# KnowledgeAgent

**Co robi:**
- Tworzy embeddingi tekstu (fake w PoC, docelowo Vertex AI)
- Zapisuje (upsert) chunki w Qdrant z metadanymi
- Wyszukuje (retrieve) relevant chunki z filtrem ACL

**Power-up Skills:**
- `python-testing-patterns` (Weryfikacja precyzji retrievalu i izolacji banków)

**Pliki:**
- `app/sub_agents/knowledge_agent/agent.py`
- `app/tools.py` (embed_text, upsert_chunk, retrieve_chunks)

**Tools:**
- `embed_text(text)` → list[float]
- `upsert_chunk(bank_id, chunk_id, chunk_text, payload)` → str
- `retrieve_chunks(query, permitted_banks, top_k)` → list[dict]

**Model:** `gemini-2.5-flash`

---

## Checklist modyfikacji KnowledgeAgent

- [ ] Czy `EMBEDDING_SIZE` w `.env` zgadza się z rozmiarem kolekcji w Qdrant?
- [ ] Czy nowe pole w `payload` jest obsługiwane przez Qdrant (typ, rozmiar)?
- [ ] Czy `retrieve_chunks` filtruje po `permitted_banks` (bezpieczeństwo ACL)?
- [ ] Czy po zmianie embedding model trzeba przeindeksować Qdrant?
- [ ] Czy zaktualizowałeś ten dokument?
