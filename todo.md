# WenetBrain — Lista zadań do wykonania

> Aktualna checklista następnych kroków.  
> Źródło: `wenetbrain/SUMMARY.md` (sekcje TODO i wymagane akcje).

---

## Priorytet: Krytyczne (blokuje pełną funkcjonalność)

- [ ] Założyć projekt GCP i włączyć billing
- [ ] Włączyć Vertex AI API, Speech-to-Text API w GCP
- [ ] Dodać `GOOGLE_CLOUD_PROJECT` i `GOOGLE_CLOUD_LOCATION` do `.env`
- [ ] Wykonać `gcloud auth login --update-adc`
- [ ] Wykonać `agents-cli login --interactive`
- [x] Przełączyć na `Gemini(model="gemini-2.5-flash")` z fallbackiem na `GOOGLE_API_KEY`
- [x] Ustawić `GOOGLE_GENAI_USE_VERTEXAI` konfigurowalne przez `.env`
- [ ] Przetestować end-to-end: audio → transkrypcja (Gemini) → ekstrakcja → Qdrant

## Priorytet: Wysoki (integracje zewnętrzne)

- [x] Wygenerować ClickUp API key i wpisać do `.env` (`CLICKUP_API_KEY`)
- [x] Wygenerować `CLICKUP_DEFAULT_LIST_ID` i wpisać do `.env`
- [ ] Zarejestrować aplikację w Azure AD (MS365 Calendar)
- [ ] Dodać `MS365_CLIENT_ID` i `MS365_CLIENT_SECRET` do `.env`
- [x] Skonfigurować `user_acl` — przypisać role (member/editor/manager/admin) w `wenetbrain.db`

## Priorytet: Średni (frontend i UX)

- [x] Zbudować UI w React 19 + Vite (zamiast Next.js) z shadcn/ui + Tailwind v4
- [x] Ekran przestrzeni (spaces): sidebar + lista notatek + czat
- [x] Ekran inbox: zatwierdzanie / eksport do ClickUp
- [x] Modal nagrywania: wybór typu spotkania + upload audio/txt
- [x] Integracja frontend ↔ FastAPI przez `fetch` (api.ts)

## Priorytet: Niski (opcjonalne / przyszłość)

- [ ] Zainstalować Ollama + `llama3.2` jako fallback 100% lokalny
- [ ] Diarization: zintegrować `pyannote.audio` i voice profiles
- [ ] Nagranie próbek głosu użytkowników (`~/.wenetbrain/voice_profile/`)
- [ ] Integracja Slack (powiadomienia o inboxie)
- [ ] SSO / SAML (SaaS multi-tenant)

## Architektura i rozwój

- [ ] Dodać `SummaryAgent` (podsumowanie całego spotkania)
- [ ] Rozważyć migrację SQLite → PostgreSQL (Cloud SQL w produkcji)
- [ ] Rozważyć migrację Qdrant lokalny → Qdrant Cloud / Vertex AI Vector Search
- [ ] Dodać szyfrowanie at-rest dla Qdrant (produkcja)
- [ ] Przygotować deployment target: `agents-cli scaffold enhance . --deployment-target agent_runtime`

## Dokumentacja

- [x] Utworzyć katalog `docs/` na dokumentację projektową
- [x] Przenieść `design.md` do `docs/design.md`
- [ ] Dodać dokumentację API (OpenAPI / Swagger opis dla zewnętrznych integracji)
- [ ] Uzupełnić docs/agents/*-agent.md o aktualne modele i kontrakty
- [ ] Dodać docs/api.md z opisem endpointów REST
- [ ] Dodać docs/database.md ze schematem SQLite i kolekcjami Qdrant
