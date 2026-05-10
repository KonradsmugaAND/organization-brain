# WenetBrain — Przewodnik projektu (Claude Code)

WenetBrain to lokalnie uruchamiany **organizacyjny second brain**: nagrywa spotkania, ekstrahuje wiedzę (action items, decyzje, notatki), zapisuje ją w Qdrant z ACL, udostępnia czat RAG, eksportuje zadania do ClickUp przez HITL i synchronizuje MS365 Calendar.

Stack: **Google ADK + A2A** (backend Python), **FastAPI**, **React 19 + Vite + shadcn/ui + Tailwind v4** (frontend), **Qdrant** (vector DB), **SQLite** (metadata PoC), `uv` (Python), `npm` (frontend).

---

## Układ repozytorium

```
brain-wenet/               ← git root (ten plik tu leży)
  CLAUDE.md
  README.md
  todo.md
  Makefile                 ← zadania deweloperskie (make help)
  graphify-out/            ← interaktywny graf wiedzy (NIE edytuj ręcznie)
  .github/workflows/       ← CI/CD (GitHub Actions)
  wenetbrain/              ← Python project root (stąd uruchamiaj uv)
    pyproject.toml
    docker-compose.yml     ← Qdrant
    .env                   ← NIE commituj; kopiuj z .env.example
    app/
      agent.py             ← RootAgent (TYLKO deleguje, zero logiki)
      fast_api_app.py      ← FastAPI + A2A (port 8000)
      api_routes.py        ← REST router
      tools.py             ← WSZYSTKIE shared tools (Qdrant, SQLite, ClickUp, Calendar, auth)
      prompts/             ← system prompty jako pliki .md
      sub_agents/          ← 8 sub-agentów, każdy w katalogu z agent.py
        meeting_agent/
        extraction_agent/
        routing_agent/
        knowledge_agent/
        chat_agent/
        clickup_agent/
        calendar_agent/
        inbox_agent/
      frontend/            ← główna aplikacja React (Vite, port 8000)
        src/
        dist/              ← build (commitowany, serwowany przez FastAPI)
    admin/
      admin_app.py         ← FastAPI admin (port 8001)
      admin_routes.py
      frontend/            ← panel administracyjny React
        src/
        dist/
    scripts/
      start.sh             ← uruchamia Qdrant + init + główną aplikację
      stop.sh
      init_qdrant.py
      init_db.py
    start-local.sh         ← uruchamia obie aplikacje (8000 + 8001)
    docs/
      README.md            ← indeks dokumentacji developerskiej
      architecture.md      ← hierarchia agentów, jak dodawać agentów
      acl.md               ← macierz ACL (źródło prawdy)
      design.md            ← design system frontendu
      workflows.md         ← workflow deweloperski
      agents/              ← checklisty per-agent
```

---

## Architektura agentów

```
RootAgent  (app/agent.py)
  model: Gemini 2.5 Flash | LiteLLM/Ollama (local PoC)
  zasada: WYŁĄCZNIE orkiestruje — zero logiki biznesowej
  ├── MeetingAgent     — upload audio, transkrypcja, metadane spotkania
  ├── ExtractionAgent  — action items / decyzje / notatki z transkryptu
  ├── RoutingAgent     — wybór docelowych knowledge banks (ACL + meeting_type)
  ├── KnowledgeAgent   — embeddingi, upsert i retrieval w Qdrant
  ├── ChatAgent        — czat RAG z cytatami źródeł
  ├── ClickUpAgent     — eksport zadań do ClickUp API v2
  ├── CalendarAgent    — pobieranie/sync MS365 Calendar
  └── InboxAgent       — kolejka HITL: propozycje czekają na akceptację managera
```

---

## Komendy

```bash
# ── Konfiguracja (jednorazowo, z wenetbrain/) ──────────────────────────
cp wenetbrain/.env.example wenetbrain/.env   # wypełnij kredentiale
cd wenetbrain && uv sync                     # zależności Python
cd wenetbrain && uv sync --extra lint        # + ruff, ty, codespell

cd wenetbrain/app/frontend && npm install    # frontend główny
cd wenetbrain/admin/frontend && npm install  # frontend admin

# LUB przez Makefile (z katalogu brain-wenet/):
make setup      # Python deps
make setup-fe   # npm deps obu frontendów

# ── Uruchamianie serwisów ─────────────────────────────────────────────
make dev        # oba serwisy (8000 + 8001)
make stop       # zatrzymaj wszystko
# lub ręcznie:
cd wenetbrain && ./start-local.sh

# ── Lint i formatowanie ───────────────────────────────────────────────
make lint       # ruff + ESLint (oba frontendy)
make lint-py    # tylko ruff
make lint-fe    # tylko ESLint
make format     # ruff format (Python)

# ── Sprawdzanie typów ─────────────────────────────────────────────────
make type-check # ty (Python, advisory) + tsc --noEmit (TypeScript)

# ── Testy ─────────────────────────────────────────────────────────────
make test       # pytest tests/ (wymaga działającego Qdrant)
# lub ręcznie:
cd wenetbrain && uv run pytest tests/ -v

# ── Build frontendu ───────────────────────────────────────────────────
make build-fe   # oba frontendy → dist/

# ── Pełny gate przed PR ───────────────────────────────────────────────
make check      # lint + type-check + test + build-fe

# ── ADK tools ─────────────────────────────────────────────────────────
cd wenetbrain
agents-cli run "Przetestuj chat agenta"   # smoke test
agents-cli playground                      # UI do interaktywnych testów
agents-cli eval run                        # ADK evaluation

# ── Ręczne testy funkcjonalne (z wenetbrain/) ─────────────────────────
uv run python -c "from app.tools import retrieve_chunks; print(retrieve_chunks('Feature X', ['team_product_webwave']))"
uv run python -c "from app.tools import get_inbox_items; print(get_inbox_items('user_001'))"

# ── E2E (wymaga GCP credentials) ──────────────────────────────────────
uv run python test_gemini_pipeline.py
uv run python test_e2e_wenetbrain.py
```

---

## URL serwisów (local dev)

| Serwis | URL |
|--------|-----|
| Główna aplikacja (API + frontend) | http://localhost:8000 |
| Swagger UI | http://localhost:8000/docs |
| A2A RPC | http://localhost:8000/a2a/wenetbrain |
| Agent card | http://localhost:8000/a2a/wenetbrain/.well-known/agent.json |
| Panel administracyjny | http://localhost:8001 |
| Qdrant dashboard | http://localhost:6333/dashboard |
| Domyślny login dev | admin / admin123 |

---

## Guardrails deweloperskie

1. **RootAgent Purity** — `app/agent.py` (RootAgent) WYŁĄCZNIE deleguje. Zero logiki biznesowej w orkiestratorze. Cała logika żyje w plikach `sub_agents/*/agent.py` lub `app/tools.py`.

2. **ACL Truth** — Każda zmiana routingu musi pasować do macierzy ACL w `wenetbrain/docs/acl.md`. Implementacja: `get_user_acl()` i `ensure_user()` w `app/tools.py`.

3. **Tooling Standard** — Każda funkcja w `app/tools.py` musi mieć pełne Python type hints i docstring. Bez wyjątków.

4. **Definition of Done** — Zadanie jest ukończone dopiero gdy checklista w `wenetbrain/docs/agents/index.md` jest wypełniona i smoke test przechodzi: `agents-cli run "..."`.

5. **Graphify Sync** — Po zmianach strukturalnych zaktualizuj graf wiedzy (`/graphify` w sesji Claude Code).

---

## Kiedy aktualizować graf wiedzy (`/graphify`)

**Wymagane** po:
- Nowym/usuniętym agencie w `app/agent.py` lub `app/sub_agents/`
- Nowym/usuniętym toolu w `app/tools.py`
- Zmianie routingu lub ACL
- Zmianie kontraktów API (FastAPI routes, modele Pydantic)
- Zmianie schematu bazy (SQLite tabele lub kolekcje Qdrant)
- Refaktoryzacji dotykającej więcej niż 2 moduły

**Nie wymagane** dla: formatowania, komentarzy, zmiennych lokalnych, testów jednostkowych.

```bash
/graphify                    # pełna regeneracja
/graphify wenetbrain/app     # tylko katalog app/ (szybciej)
```

---

## Jak dodać nowego sub-agenta

1. Utwórz `app/sub_agents/<name>_agent/agent.py` z `instruction`, `Agent(...)`, `name`, `model`, `tools`
2. Jeśli potrzebne nowe tools — dodaj do `app/tools.py` z pełnymi type hints i docstringiem
3. Zaimportuj i dodaj do `sub_agents=[...]` w `app/agent.py`
4. Dodaj dokumentację w `wenetbrain/docs/agents/<name>-agent.md` (opis + checklista)
5. Uruchom: `agents-cli run "Przetestuj <name>_agent"`
6. Uruchom: `/graphify`

---

## Jak modyfikować prompty

Pliki promptów: `app/prompts/extraction.md`, `chat.md`, `routing.md`, `summary.md`.

Po każdej zmianie promptu uruchom eval lub smoke test i sprawdź czy struktura JSON odpowiedzi jest zachowana.

---

## Stack technologiczny

| Warstwa | Technologia |
|---------|-------------|
| Framework agentów | Google ADK 1.27+ + A2A protocol |
| LLM (cloud) | Gemini 2.5 Flash (Vertex AI / AI Studio) |
| LLM (local PoC) | Ollama (llama3.2) |
| Baza wektorowa | Qdrant (Docker) |
| Baza relacyjna | SQLite (PoC → docelowo PostgreSQL) |
| Backend API | FastAPI |
| Autentykacja | OAuth2 + JWT (HS256) + bcrypt |
| Frontend | React 19 + TypeScript + Vite |
| UI Framework | shadcn/ui + Tailwind CSS v4 |
| Package manager | `uv` (backend), `npm` (frontend) |
| Infra lokalna | Docker Compose |

---

## Subagenci Claude Code

Projekt ma 5 dedykowanych subagentów w `.claude/agents/`. Claude automatycznie deleguje do nich odpowiednie zadania — możesz też wywołać ich bezpośrednio przez `@agent-<name>`.

| Agent | Kolor | Skille | Kiedy używać |
|-------|-------|--------|-------------|
| `frontend-designer` | niebieski | `tailwind-v4-shadcn`, `react-dev`, `figma-use` | Komponenty React, UI, shadcn/ui, Tailwind v4, design system, build dist/ |
| `adk-developer` | fioletowy | `google-agents-cli-adk-code`, `google-agents-cli-eval` | Sub-agenty ADK, instrukcje agentów, prompty systemowe, A2A |
| `backend-developer` | zielony | `fastapi-python` | FastAPI routes, tools.py, Qdrant, SQLite, auth, ACL |
| `code-reviewer` | żółty | — | Review kodu po zmianach — guardrails ADK, bezpieczeństwo, jakość |
| `eval-runner` | pomarańczowy | `google-agents-cli-eval` | pytest, smoke testy, ADK eval, lint, type check, pre-PR gate |

### Podział odpowiedzialności (co kto dotyka)

```
app/agent.py                → adk-developer (tylko sub_agents=[])
app/sub_agents/**/agent.py  → adk-developer
app/prompts/*.md            → adk-developer
app/tools.py                → backend-developer
app/api_routes.py           → backend-developer
app/fast_api_app.py         → backend-developer
admin/admin_routes.py       → backend-developer
admin/admin_app.py          → backend-developer
app/frontend/src/**         → frontend-designer
admin/frontend/src/**       → frontend-designer
dist/                       → frontend-designer (przez npm run build)
tests/                      → eval-runner (uruchomienie), backend-developer (pisanie)
docs/agents/**              → adk-developer
docs/acl.md                 → backend-developer
docs/design.md              → frontend-designer
docs/architecture.md        → adk-developer
```

### Kiedy uruchomić `/graphify`

Każdy z agentów ma w swojej checkliście informację kiedy `/graphify` jest wymagane. Zasada ogólna — **wymagane** po zmianach strukturalnych:
- Nowy/usunięty sub-agent lub tool → `/graphify wenetbrain/app`
- Nowe/usunięte API routes lub schemat bazy → `/graphify wenetbrain/app`
- Refaktoryzacja >2 modułów → `/graphify`

**Nie wymagane** dla: formatowania, stylów CSS, zmiennych lokalnych, drobnych poprawek.

---

## Znane ograniczenia PoC

- SQLite (nie PostgreSQL) — brak horizontal scaling
- Brak szyfrowania danych w Qdrant i SQLite
- Brak SSO/SAML — tylko lokalne konta JWT
- Brak speaker diarization — manualne przypisywanie mówców
- Brak Slack notifications
- Single-process (brak GKE/Agent Runtime deployment)
