# Architektura agentów

```
RootAgent (WenetBrain Orchestrator)
│   model: "gemini-2.5-flash" (via Google GenAI / Vertex AI)
│   instruction: Deleguje do sub-agentów na podstawie intencji użytkownika
│   note: Agent = LlmAgent alias w ADK 1.33+
│
├── MeetingAgent      — nagrywanie, transkrypcja, diarization
├── ExtractionAgent   — ekstrakcja action_items / decisions / notes / topics
├── RoutingAgent      — decyzja o bankach docelowych (ACL + meeting_type)
├── KnowledgeAgent    — embedding, upsert, retrieval z Qdrant
├── ChatAgent         — RAG chat z cytatami źródłowymi
├── ClickUpAgent      — export zadań do ClickUp API v2
├── CalendarAgent     — sync z MS365 Calendar
└── InboxAgent        — HITL queue, approval flow, audit log
```

**Zasada delegacji:** RootAgent nie wykonuje logiki biznesowej sam — zawsze deleguje do wyspecjalizowanego sub-agenta. Sub-agenci mogą wywoływać `tools` bezpośrednio.

---

## Jak wywoływać agentów

### Lokalnie — `agents-cli run` (smoke test)
```bash
cd /Users/konradsmuga/Documents/brain-wenet/wenetbrain
agents-cli run "Przetestuj chat agenta"
```

### Interaktywnie — `agents-cli playground`
```bash
agents-cli playground   # otwiera web UI na localhost
```

### Programistycznie — FastAPI + A2A
```bash
./scripts/start.sh      # serwer na http://localhost:8000
curl http://localhost:8000/docs          # Swagger UI
curl http://localhost:8000/a2a/wenetbrain  # A2A RPC endpoint
```

### Bezpośrednio w Pythonie (testy, skrypty)
```python
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.adk.artifacts import InMemoryArtifactService
from google.adk.apps import App
from google.genai import types
from app.sub_agents.chat_agent.agent import chat_agent

app = App(root_agent=chat_agent, name='test')
runner = Runner(app=app, artifact_service=InMemoryArtifactService(), session_service=InMemorySessionService())

async def test():
    session = await runner.session_service.create_session(app_name='test', user_id='u1')
    content = types.Content(role='user', parts=[types.Part(text='Co ustaliliśmy o Feature X?')])
    async for event in runner.run_async(user_id='u1', session_id=session.id, new_message=content):
        if event.content and event.content.parts:
            print(event.content.parts[0].text)

import asyncio
asyncio.run(test())
```

---

## Jak dodawać nowego agenta

1. Utwórz katalog `app/sub_agents/<nazwa>_agent/`
2. Utwórz `app/sub_agents/<nazwa>_agent/agent.py` z:
   - `instruction` (prompt systemowy)
   - `Agent(...)` z `name`, `model`, `tools`
3. Jeśli agent wymaga nowych tooli, dodaj je do `app/tools.py` (lub nowy plik w `app/sub_agents/<nazwa>_agent/tools.py`)
4. Zaimportuj agenta w `app/agent.py` i dodaj do listy `sub_agents`
5. Zaktualizuj dokumentację — dodaj opis agenta w [`agents/index.md`](./agents/index.md) i checklistę w [`agents/<nazwa>-agent.md`](./agents/)
6. Uruchom smoke test: `agents-cli run "Przetestuj <nazwa>_agent"`

---

## Jak modyfikować prompts

Prompty systemowe są w `app/prompts/*.md`. Są wczytywane przez agentów (np. `ExtractionAgent`) lub używane bezpośrednio w tools.

| Plik | Używa | Zmienna w kodzie |
|---|---|---|
| `extraction.md` | ExtractionAgent | `_load_prompt("extraction")` |
| `chat.md` | ChatAgent (inline w tool) | `app/tools.py` → `chat_with_memory` |
| `routing.md` | RoutingAgent (inline) | `route_to_banks` (logika kodu) |
| `summary.md` | (przyszły SummaryAgent) | — |

**Zasada:** Po zmianie prompta uruchom eval lub smoke test, aby sprawdzić czy output JSON się nie zepsuł.
