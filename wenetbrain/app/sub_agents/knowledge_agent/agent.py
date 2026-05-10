"""KnowledgeAgent — manages vector embeddings and retrieval in Qdrant."""

from google.adk.agents import Agent

from app.tools import embed_text, retrieve_chunks, upsert_chunk

_instruction = """
You are KnowledgeAgent — WenetBrain's memory manager.

Your job:
1. Store chunks in Qdrant via `upsert_chunk`.
2. Retrieve relevant chunks via `retrieve_chunks` using the user's query and permitted banks.
3. Always filter by permitted_banks (ACL).

When storing, include full metadata: bank_id, meeting_id, meeting_type, speaker_id, chunk_type, status.
"""

knowledge_agent = Agent(
    name="knowledge_agent",
    model="gemini-2.5-flash",
    description="Manages embeddings and retrieval in Qdrant.",
    instruction=_instruction,
    tools=[upsert_chunk, retrieve_chunks, embed_text],
)
