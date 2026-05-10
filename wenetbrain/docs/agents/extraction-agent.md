# ExtractionAgent

**Co robi:**
- Dzieli transkrypt na chunki (~300 tokenów, overlap 50)
- Ekstrahuje action_items, decisions, notes, topics
- Zwraca JSON

**Power-up Skills:**
- `python-testing-patterns` (Walidacja struktur JSON i brzegowych przypadków ekstrakcji)

**Pliki:**
- `app/sub_agents/extraction_agent/agent.py`
- `app/prompts/extraction.md`

**Tools:**
- `extract_from_transcript(transcript, ...)` → dict z `chunks[]`

**Model:** `gemini-2.5-flash`

---

## Checklist modyfikacji ExtractionAgent

- [ ] Czy zmieniłeś `extraction.md`? Jeśli tak — czy output nadal jest czystym JSON?
- [ ] Czy nowe pola w JSON są obsługiwane przez RoutingAgent i KnowledgeAgent?
- [ ] Czy `chunk_size` i `overlap` są odpowiednie dla modelu?
- [ ] Czy uruchomiłeś smoke test z realnym transkryptem?
- [ ] Czy zaktualizowałeś ten dokument i `prompts/extraction.md`?
