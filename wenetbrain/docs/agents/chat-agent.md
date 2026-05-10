# ChatAgent

**Co robi:**
- Odbiera pytanie użytkownika
- Wyszukuje relevant chunki (RAG) z permitted banks
- Formułuje odpowiedź z cytatami źródłowymi

**Power-up Skills:**
- `ui-ux-pro-max` (Projektowanie formatu odpowiedzi dla lepszej czytelności w UI)
- `python-testing-patterns` (Testy regresyjne odpowiedzi RAG)

**Pliki:**
- `app/sub_agents/chat_agent/agent.py`
- `app/prompts/chat.md`

**Tools:**
- `chat_with_memory(query, user_id, permitted_banks, chat_history)` → dict z `answer` i `sources`

**Model:** `gemini-2.5-flash`

---

## Checklist modyfikacji ChatAgent

- [ ] Czy `chat.md` prompt zawiera instrukcję cytowania źródeł?
- [ ] Czy `top_k` w retrieve_chunks jest odpowiedni (nie za duży kontekst)?
- [ ] Czy historia rozmowy nie przekracza limitu tokenów?
- [ ] Czy nowy format odpowiedzi jest obsługiwany przez frontend (jeśli istnieje)?
- [ ] Czy zaktualizowałeś ten dokument i `prompts/chat.md`?
