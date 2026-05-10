"""ChatAgent — RAG chat with organizational memory."""

import os

from google.adk.agents import Agent

from app.tools import _get_genai_client, retrieve_chunks

PROMPT_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "prompts")


def _load_prompt(name: str) -> str:
    """Load a prompt template from the prompts directory."""
    path = os.path.join(PROMPT_DIR, f"{name}.md")
    if os.path.exists(path):
        with open(path, encoding="utf-8") as f:
            return f.read()
    return ""


def chat_with_memory(
    query: str,
    user_id: str,
    permitted_banks: list[str],
    user_name: str = "Użytkownik",
    chat_history: list[dict] | None = None,
) -> dict:
    """Answer a question using RAG over permitted knowledge banks.

    Args:
        query: User question.
        user_id: Identifier of the user.
        permitted_banks: List of bank_ids the user can access.
        user_name: Name of the user for personalization.
        chat_history: Previous messages.

    Returns:
        Dict with answer and sources.
    """
    chunks = retrieve_chunks(query, permitted_banks, top_k=5)
    if not chunks:
        return {
            "answer": "Nie znalazłem żadnych informacji w pamięci organizacyjnej na ten temat.",
            "sources": [],
        }

    # Build context from retrieved chunks
    context_parts = []
    sources = []
    for c in chunks:
        payload = c.get("payload", {})
        text = payload.get("chunk_text", "")
        context_parts.append(text)
        sources.append(
            {
                "bank_id": c["bank_id"],
                "score": c["score"],
                "meeting_title": payload.get("meeting_title", "?"),
                "meeting_date": payload.get("meeting_date", "?"),
            }
        )

    # Load prompt template and format with retrieved context
    prompt_template = _load_prompt("chat")
    if not prompt_template:
        # Fallback if prompt file is missing
        answer = (
            "Oto co znalazłem w pamięci organizacyjnej:\n\n"
            + "\n".join(f"- {s}" for s in context_parts)
            + "\n\n[Źródła: "
            + ", ".join(f"{s['meeting_title']} ({s['meeting_date']})" for s in sources)
            + "]"
        )
        return {"answer": answer, "sources": sources}

    # Build banks description for the prompt
    bank_descriptions = []
    for bank_id in permitted_banks:
        bank_descriptions.append(f"- {bank_id}")
    available_banks_description = "\n".join(bank_descriptions) if bank_descriptions else "brak"

    # Format chat history
    history_text = ""
    if chat_history:
        for msg in chat_history[-6:]:  # Keep last 6 messages to avoid token overflow
            role = msg.get("role", "user")
            text = msg.get("text", "")
            history_text += f"{role}: {text}\n"

    # Format retrieved chunks for prompt
    retrieved_chunks_text = "\n\n".join(
        f"[Chunk z {s['meeting_title']} ({s['meeting_date']}, bank: {s['bank_id']}, score: {s['score']:.3f})]\n{text}"
        for text, s in zip(context_parts, sources, strict=False)
    )
    # Escape braces to prevent .format() KeyError from user content
    safe_chunks = retrieved_chunks_text.replace("{", "{{").replace("}", "}}")
    safe_history = (history_text or "brak").replace("{", "{{").replace("}", "}}")

    prompt = prompt_template.format(
        user_name=user_name,
        available_banks_description=available_banks_description,
        retrieved_chunks=safe_chunks,
        chat_history=safe_history,
    )

    # Generate answer with LLM
    client = _get_genai_client()

    try:
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt,
        )
        answer = response.text or "Przepraszam, nie udało się wygenerować odpowiedzi."
    except Exception as exc:
        answer = f"Błąd podczas generowania odpowiedzi: {exc}"

    return {"answer": answer, "sources": sources}


_instruction = """
You are ChatAgent — WenetBrain's conversational memory interface.

Your job:
1. Receive a user question and permitted banks.
2. Call `chat_with_memory` to retrieve relevant chunks and formulate an answer.
3. Return the answer with source citations.

Always answer in Polish. Be concise. If no data is found, say so clearly.
"""

chat_agent = Agent(
    name="chat_agent",
    model="gemini-2.5-flash",
    description="Chat with organizational memory via RAG.",
    instruction=_instruction,
    tools=[chat_with_memory],
)
