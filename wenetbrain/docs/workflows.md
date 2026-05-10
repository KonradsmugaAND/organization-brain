# Development workflow

## Przed każdym PR / zmianą

### Backend / Agenci
1. Przeczytaj odpowiedni rozdział w [`agents/`](./agents/) dla zmienianego agenta
2. Wypełnij wszystkie checkboxy w checklist
3. Uruchom smoke test: `agents-cli run "..."`
4. Jeśli zmieniałeś prompt — uruchom eval: `agents-cli eval run`

### Frontend
1. Sprawdź TypeScript: `npx tsc --noEmit`
2. Sprawdź lint: `npm run lint`
3. Zbuduj dist: `npm run build`
4. Zweryfikuj czy zmiany używają tokenów CSS (`--color-*`, `--radius-*`)

## Po każdej zmianie

1. Zaktualizuj dokumentację (odpowiedni plik w [`agents/`](./agents/) lub [`design.md`](./design.md))
2. Zaktualizuj `README.md` (jeśli zmieniła się lista agentów, stack lub instrukcje setup)
3. Zaktualizuj `todo.md` (jeśli zmienił się status gotowości)

---

## Przydatne komendy

### Backend
```bash
# Start wszystkiego
./scripts/start.sh

# Stop wszystkiego
./scripts/stop.sh

# Smoke test agenta
agents-cli run "Przetestuj chat agenta"

# Playground (web UI)
agents-cli playground

# Evaluacja
agents-cli eval run

# Lint Python
make lint-py

# Test Qdrant retrieval
uv run python -c "from app.tools import retrieve_chunks; print(retrieve_chunks('Feature X', ['team_product_webwave']))"

# Test SQLite
uv run python -c "from app.tools import get_inbox_items; print(get_inbox_items('user_001'))"
```

### Frontend (główna aplikacja — port 8000)
```bash
cd wenetbrain/app/frontend
npm install
npm run dev        # dev server
npm run build      # build → dist/ (serwowane przez FastAPI)
npm run lint       # ESLint
npx tsc --noEmit   # TypeScript check
```

### Frontend (admin — port 8001)
```bash
cd wenetbrain/admin/frontend
npm install
npm run dev        # dev server
npm run build      # build → dist/
npm run lint       # ESLint
npx tsc --noEmit   # TypeScript check
```

### Makefile (z katalogu głównego brain-wenet/)
```bash
make setup         # Python deps
make setup-fe      # npm deps obu frontendów
make dev           # oba serwisy (8000 + 8001)
make stop          # zatrzymaj wszystko
make lint          # ruff + ESLint
make lint-fe       # tylko ESLint
make type-check    # ty + tsc --noEmit
make build-fe      # oba frontendy → dist/
make check         # pełny gate: lint + type-check + test + build-fe
```
