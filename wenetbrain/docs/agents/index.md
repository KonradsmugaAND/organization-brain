# Opis agentów + checklista modyfikacji

Dla każdego agenta poniżej znajduje się:
- **Co robi** — zakres odpowiedzialności
- **Pliki** — gdzie mieszka kod
- **Tools** — jakie funkcje wywołuje
- **Model** — jaki LLM używa
- **Checklist** — kroki do wykonania PRZED i PO każdej zmianie

---

## Lista agentów

| Agent | Rola | Plik |
|-------|------|------|
| [RootAgent](./root-agent.md) | Orkiestrator delegujący do sub-agentów | `app/agent.py` |
| [MeetingAgent](./meeting-agent.md) | Transkrypcja audio, metadane spotkań | `app/sub_agents/meeting_agent/agent.py` |
| [ExtractionAgent](./extraction-agent.md) | Ekstrakcja action_items / decyzji / notatek | `app/sub_agents/extraction_agent/agent.py` |
| [RoutingAgent](./routing-agent.md) | Routing do banków wiedzy (ACL + typ spotkania) | `app/sub_agents/routing_agent/agent.py` |
| [KnowledgeAgent](./knowledge-agent.md) | Embedding + retrieval w Qdrant | `app/sub_agents/knowledge_agent/agent.py` |
| [ChatAgent](./chat-agent.md) | RAG chat z cytatami źródłowymi | `app/sub_agents/chat_agent/agent.py` |
| [ClickUpAgent](./clickup-agent.md) | Eksport zadań do ClickUp API v2 | `app/sub_agents/clickup_agent/agent.py` |
| [CalendarAgent](./calendar-agent.md) | Sync z MS365 Calendar | `app/sub_agents/calendar_agent/agent.py` |
| [InboxAgent](./inbox-agent.md) | HITL queue, approval flow, audit log | `app/sub_agents/inbox_agent/agent.py` |

---

## Ostatni przegląd architektury

**Data:** 2026-05-10

**Wykonane zmiany:**
- RootAgent: usunięta logika inicjalizacyjna (`load_dotenv`, `os.environ`), przeniesiona do `fast_api_app.py`
- Wszystkie sub-agenty: `Gemini(model=...)` zastąpione stringiem `"gemini-2.5-flash"` (ADK 1.33+ best practice)
- ExtractionAgent: `extract_from_transcript` teraz używa prawdziwego LLM (Gemini) z promptem `extraction.md`
- ChatAgent: `chat_with_memory` teraz używa prawdziwego LLM (Gemini) z promptem `chat.md`
- Dokumentacja: zaktualizowano model we wszystkich plikach `.md` z `LiteLlm` na `gemini-2.5-flash`
- Usunięto nieużywane importy `Gemini` z agentów
