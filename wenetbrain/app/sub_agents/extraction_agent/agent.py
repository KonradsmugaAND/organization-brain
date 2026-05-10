"""ExtractionAgent — extracts action items, decisions, notes from transcripts."""

import json
import os

from google.adk.agents import Agent

from app.tools import _get_genai_client

PROMPT_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "prompts")


def _load_prompt(name: str) -> str:
    """Load a prompt template from the prompts directory."""
    path = os.path.join(PROMPT_DIR, f"{name}.md")
    if os.path.exists(path):
        with open(path, encoding="utf-8") as f:
            return f.read()
    return ""


def _split_transcript_into_chunks(transcript: str, chunk_size: int = 200, overlap: int = 30) -> list[str]:
    """Split transcript into overlapping word chunks.

    Args:
        transcript: Full meeting transcript text.
        chunk_size: Number of words per chunk.
        overlap: Number of overlapping words between chunks.

    Returns:
        List of chunk strings.
    """
    words = transcript.split()
    chunks = []
    step = max(1, chunk_size - overlap)
    for i in range(0, len(words), step):
        chunk_text = " ".join(words[i : i + chunk_size])
        chunks.append(chunk_text)
    return chunks


def extract_from_transcript(
    transcript: str,
    user_name: str = "Użytkownik",
    user_role: str = "",
    user_team: str = "",
    meeting_type: str = "team",
    participants_list: str = "",
    meeting_date: str = "",
) -> dict:
    """Extract structured data from a meeting transcript using LLM.

    Args:
        transcript: Full meeting transcript text.
        user_name: Name of the requesting user.
        user_role: Role of the user.
        user_team: Team name.
        meeting_type: Type of meeting (team, cross, oneonone, allhands).
        participants_list: Comma-separated list of participants.
        meeting_date: ISO date string.

    Returns:
        JSON with chunks[] containing action_items, decisions, notes, topics.
    """
    prompt_template = _load_prompt("extraction")
    if not prompt_template:
        # Fallback if prompt file is missing
        prompt_template = (
            "Przeanalizuj transkrypt spotkania. "
            "Wyciągnij action_items, decisions, notes, topics. "
            "Zwróć TYLKO JSON.\n\nTranskrypt:\n{chunk_text}"
        )

    chunks = _split_transcript_into_chunks(transcript, chunk_size=300, overlap=50)
    extracted_chunks = []

    client = _get_genai_client()

    for idx, chunk_text in enumerate(chunks):
        # Escape braces in chunk_text to prevent .format() KeyError
        safe_chunk = chunk_text.replace("{", "{{").replace("}", "}}")
        prompt = prompt_template.format(
            user_name=user_name,
            user_role=user_role,
            user_team=user_team,
            meeting_type=meeting_type,
            participants_list=participants_list,
            meeting_date=meeting_date,
            chunk_text=safe_chunk,
        )
        try:
            response = client.models.generate_content(
                model="gemini-2.5-flash",
                contents=prompt,
            )
            text = response.text or "{}"
            # Strip markdown code fences
            text = text.strip().removeprefix("```json").removeprefix("```").removesuffix("```").strip()
            parsed = json.loads(text)
        except Exception as exc:
            # Fallback for API errors — return empty structure for this chunk
            parsed = {
                "action_items": [],
                "decisions": [],
                "notes": [f"[Błąd ekstrakcji chunk {idx}: {exc}]"],
                "topics": [],
            }

        extracted_chunks.append(
            {
                "chunk_index": idx,
                "action_items": parsed.get("action_items", []),
                "decisions": parsed.get("decisions", []),
                "notes": parsed.get("notes", []),
                "topics": parsed.get("topics", []),
            }
        )

    return {
        "chunks": extracted_chunks,
        "summary": f"Extracted {len(extracted_chunks)} chunks from transcript of {len(transcript.split())} words.",
    }


_instruction = """
You are ExtractionAgent — WenetBrain's knowledge extraction specialist.

Your job:
1. Receive a meeting transcript and metadata.
2. Call `extract_from_transcript` to get structured data (action items, decisions, notes, topics).
3. Return the structured JSON.

Be concise. Return only the extracted data.
"""

extraction_agent = Agent(
    name="extraction_agent",
    model="gemini-2.5-flash",
    description="Extracts action items, decisions, and notes from meeting transcripts.",
    instruction=_instruction,
    tools=[extract_from_transcript],
)
