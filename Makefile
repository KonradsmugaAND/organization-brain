SHELL := /bin/bash
.DEFAULT_GOAL := help

WENETBRAIN := wenetbrain
APP_FE      := wenetbrain/app/frontend
ADMIN_FE    := wenetbrain/admin/frontend

.PHONY: help dev dev-main stop setup setup-fe \
        lint lint-py lint-fe format \
        type-check test build-fe check

help:
	@grep -E '^[a-zA-Z_-]+:.*##' $(MAKEFILE_LIST) | \
	  awk 'BEGIN {FS = ":.*##"}; {printf "  \033[36m%-18s\033[0m %s\n", $$1, $$2}'

# ── Serwisy ─────────────────────────────────────────────────────────────

dev:             ## Uruchom oba serwisy (main :8000 + admin :8001)
	cd $(WENETBRAIN) && ./start-local.sh

dev-main:        ## Uruchom tylko główną aplikację + Qdrant (:8000)
	cd $(WENETBRAIN) && ./scripts/start.sh

stop:            ## Zatrzymaj wszystkie serwisy
	cd $(WENETBRAIN) && ./scripts/stop.sh

# ── Konfiguracja ─────────────────────────────────────────────────────────

setup:           ## Zainstaluj wszystkie zależności Python (dev + lint)
	cd $(WENETBRAIN) && uv sync && uv sync --extra lint

setup-fe:        ## Zainstaluj zależności npm obu frontendów
	cd $(APP_FE) && npm install
	cd $(ADMIN_FE) && npm install

# ── Lint ──────────────────────────────────────────────────────────────────

lint:            ## Uruchom wszystkie lintery (Python + oba frontendy)
	$(MAKE) lint-py
	$(MAKE) lint-fe

lint-py:         ## ruff lint — kod Python
	cd $(WENETBRAIN) && uv run ruff check .

lint-fe:         ## ESLint — oba frontendy
	cd $(APP_FE) && npm run lint
	cd $(ADMIN_FE) && npm run lint

# ── Formatowanie ──────────────────────────────────────────────────────────

format:          ## Auto-formatuj kod Python (ruff format)
	cd $(WENETBRAIN) && uv run ruff format .

# ── Sprawdzanie typów ─────────────────────────────────────────────────────

type-check:      ## ty (Python, advisory) + tsc --noEmit (TypeScript, oba frontendy)
	cd $(WENETBRAIN) && uv run ty check . || true
	cd $(APP_FE) && npx tsc -b --noEmit
	cd $(ADMIN_FE) && npx tsc -b --noEmit

# ── Testy ─────────────────────────────────────────────────────────────────

test:            ## pytest tests/ (wymaga działającego Qdrant)
	cd $(WENETBRAIN) && uv run pytest tests/ -v

# ── Build ─────────────────────────────────────────────────────────────────

build-fe:        ## Zbuduj oba frontendy do dist/
	cd $(APP_FE) && npm run build
	cd $(ADMIN_FE) && npm run build

# ── Gate przed PR ─────────────────────────────────────────────────────────

check:           ## Pełny gate: lint + type-check + test + build-fe
	$(MAKE) lint
	$(MAKE) type-check
	$(MAKE) test
	$(MAKE) build-fe
	@echo ""
	@echo "Wszystkie sprawdzenia przeszły. Gotowe do PR."
