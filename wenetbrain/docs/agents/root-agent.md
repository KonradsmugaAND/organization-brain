# RootAgent (Orchestrator)

**Co robi:**
- Odbiera pytanie użytkownika
- Decyduje, który sub-agent powinien je obsłużyć
- Deleguje i zwraca odpowiedź

**Power-up Skills:**
- `vercel-composition-patterns` (Orkiestracja przepływów)

**Pliki:**
- `app/agent.py`

**Model:** `gemini-2.5-flash`

**Sub-agenci:**
- meeting_agent, extraction_agent, routing_agent, knowledge_agent, chat_agent, clickup_agent, calendar_agent, inbox_agent

---

## Checklist modyfikacji RootAgent

- [ ] Czy nowy sub-agent jest zaimportowany i dodany do `sub_agents`?
- [ ] Czy `instruction` zawiera regułę delegacji dla nowego agenta?
- [ ] Czy nie usunąłeś istniejących reguł delegacji?
- [ ] Czy uruchomiłeś `agents-cli run "Przetestuj orchestrator"`?
- [ ] Czy zaktualizowałeś dokumentację (dodałeś opis nowego agenta w [`agents/index.md`](./index.md))?
- [ ] Czy zaktualizowałeś `README.md` (lista agentów)?
