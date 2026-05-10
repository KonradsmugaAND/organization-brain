# WenetBrain — Organizational Second Brain (ADK + A2A PoC)

Lokalnie uruchamiany asystent organizacyjny zbudowany na **Google ADK** z protokołem **A2A** (Agent-to-Agent).

## Co potrafi

- **MeetingAgent** — nagrywanie i transkrypcja spotkań (Gemini multimodal z fallbackiem do pliku .txt)
- **ExtractionAgent** — ekstrakcja action items, decyzji i notatek z transkryptów (chunking + LLM)
- **RoutingAgent** — routing wiedzy do banków (group / company / team / private) z ACL
- **KnowledgeAgent** — embeddingi (text-embedding-004) i retrieval w **Qdrant**
- **ChatAgent** — czat RAG z pamięcią organizacyjną (cytaty źródłowe z banków)
- **ClickUpAgent** — eksport zadań do ClickUp API v2
- **CalendarAgent** — synchronizacja z Microsoft 365 Calendar
- **InboxAgent** — HITL queue (human-in-the-loop) z audit logiem

## Architektura

```
RootAgent (WenetBrain Orchestrator)
├── MeetingAgent
├── ExtractionAgent
├── RoutingAgent
├── KnowledgeAgent
├── ChatAgent
├── ClickUpAgent
├── CalendarAgent
└── InboxAgent
```

## Wymagania

- macOS 13+ lub Ubuntu 22+
- Docker
- [uv](https://docs.astral.sh/uv/getting-started/installation/)
- Ollama (lokalne modele) lub konto Google Cloud (Gemini API)

## Instalacja

```bash
# 1. Wejdź do katalogu projektu
cd wenetbrain

# 2. Zainstaluj zależności
uv tool install google-agents-cli
agents-cli setup --skip-auth

# 3. Skonfiguruj środowisko
cp .env.example .env
# Edytuj .env — podaj GOOGLE_CLOUD_PROJECT lub zostaw puste dla trybu Ollama

# 4. Zainstaluj paczki projektu
uv sync
```

## Uruchomienie

```bash
# Pełny stack (Qdrant + backend + admin)
cd wenetbrain
./start-local.sh

# Lub przez Makefile (z katalogu głównego)
make dev       # uruchamia oba serwisy (8000 + 8001)
make stop      # zatrzymuje wszystko
```

Serwisy:
- **API + frontend:** http://localhost:8000
- **Docs (Swagger):** http://localhost:8000/docs
- **A2A RPC:** http://localhost:8000/a2a/wenetbrain
- **Agent Card:** http://localhost:8000/a2a/wenetbrain/.well-known/agent.json
- **Panel admina:** http://localhost:8001
- **Qdrant Dashboard:** http://localhost:6333/dashboard
- **Login dev:** admin / admin123

## Testowanie

```bash
cd wenetbrain

# Szybki smoke test
agents-cli run "Przetestuj chat agenta"

# Interaktywny playground
agents-cli playground

# Testy pytest
uv run pytest tests/ -v

# Ręczne testy funkcjonalne
uv run python -c "from app.tools import retrieve_chunks; print(retrieve_chunks('Feature X', ['team_product_webwave']))"
```

## Struktura projektu

```
wenetbrain/
  app/
    agent.py                    # Root orchestrator
    fast_api_app.py             # FastAPI + A2A
    tools.py                    # Custom tools (Qdrant, SQLite, ClickUp, Calendar)
    prompts/                    # System prompts
      extraction.md
      chat.md
      summary.md
      routing.md
    sub_agents/                 # ADK sub-agents
      meeting_agent/
      extraction_agent/
      routing_agent/
      knowledge_agent/
      chat_agent/
      clickup_agent/
      calendar_agent/
      inbox_agent/
    frontend/                   # React app (Vite + shadcn/ui)
      src/
        App.tsx
        components/
        api.ts
      dist/                     # Production build
  admin/
    admin_app.py                # FastAPI admin panel
    admin_routes.py             # Admin API routes
    frontend/                   # React admin (Vite + shadcn/ui)
      src/
        App.tsx
        components/
        api.ts
      dist/                     # Production build
  scripts/
    start.sh
    stop.sh
    init_qdrant.py
    init_db.py
  docker-compose.yml            # Qdrant
  pyproject.toml
  .env.example
```

## Stack technologiczny

| Warstwa | Technologia |
|---|---|
| Framework agentów | Google ADK + A2A protocol |
| LLM (cloud) | Gemini 2.5 Flash (Vertex AI / Gemini API) |
| LLM (local PoC fallback) | Ollama (llama3.2) via LiteLLM |
| Embedding | text-embedding-004 (fallback: deterministic fake) |
| Baza wektorowa | Qdrant |
| Baza relacyjna | SQLite (PoC) |
| Backend API | FastAPI + A2A |
| Auth | OAuth2 + JWT HS256 + bcrypt |
| Frontend | React 19 + TypeScript + Vite + shadcn/ui + Tailwind CSS v4 |
| Infra lokalna | Docker Compose |

## Guardrails / Limity PoC

- Auth: lokalne konta JWT (brak SSO/SAML)
- Diarization: brak — ręczne przypisywanie uczestników
- ClickUp / MS365: wymagają konfiguracji API keys w `.env` (mock w PoC)
- Brak szyfrowania at-rest w Qdrant i SQLite
- Single-process (brak GKE/Agent Runtime deployment)
- Embedding: Vertex AI / Gemini API z deterministic fallback

## Licencja

Apache 2.0 (scaffold z Google ADK)
