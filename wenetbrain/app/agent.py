"""WenetBrain root agent — orchestrates all sub-agents.

This module MUST remain pure: only imports, agent definitions,
and the App factory. All business logic lives in sub-agents or tools.
Environment setup (load_dotenv, defaults) is handled in fast_api_app.py
or at application startup, NOT here.
"""

from google.adk.agents import Agent
from google.adk.apps import App

from app.sub_agents.calendar_agent.agent import calendar_agent
from app.sub_agents.chat_agent.agent import chat_agent
from app.sub_agents.clickup_agent.agent import clickup_agent
from app.sub_agents.extraction_agent.agent import extraction_agent
from app.sub_agents.inbox_agent.agent import inbox_agent
from app.sub_agents.knowledge_agent.agent import knowledge_agent
from app.sub_agents.meeting_agent.agent import meeting_agent
from app.sub_agents.routing_agent.agent import routing_agent

_instruction = """
You are WenetBrain — the organizational second brain for WeNet Group.

You coordinate a team of specialized agents:
- **meeting_agent** — transcribes audio and saves meeting metadata.
- **extraction_agent** — extracts action items, decisions, notes from transcripts.
- **routing_agent** — decides which knowledge banks the notes should go to.
- **knowledge_agent** — stores and retrieves vectors from Qdrant.
- **chat_agent** — answers questions using organizational memory (RAG).
- **clickup_agent** — exports tasks to ClickUp.
- **calendar_agent** — fetches Microsoft 365 calendar events.
- **inbox_agent** — manages human-in-the-loop approvals.

Rules:
1. When the user uploads audio or mentions a meeting, delegate to **meeting_agent** first.
2. After transcription, delegate to **extraction_agent** to get structured data.
3. Then call **routing_agent** to decide destination banks.
4. Use **knowledge_agent** to store approved chunks.
5. Use **inbox_agent** to create pending items for manager approval.
6. For questions about past meetings, delegate to **chat_agent**.
7. For task exports, delegate to **clickup_agent**.
8. For calendar sync, delegate to **calendar_agent**.

Always answer in Polish unless the user asks otherwise.
"""

root_agent = Agent(
    name="root_agent",
    model="gemini-2.5-flash",
    description="WenetBrain root orchestrator for organizational knowledge and meetings.",
    instruction=_instruction,
    sub_agents=[
        meeting_agent,
        extraction_agent,
        routing_agent,
        knowledge_agent,
        chat_agent,
        clickup_agent,
        calendar_agent,
        inbox_agent,
    ],
)

app = App(
    root_agent=root_agent,
    name="wenetbrain",
)
