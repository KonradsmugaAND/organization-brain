# ClickUpAgent

**Co robi:**
- Tworzy taski w ClickUp przez API v2
- Eksportuje inbox items do ClickUp

**Power-up Skills:**
- `python-testing-patterns` (Walidacja integracji z zewnętrznym API v2)

**Pliki:**
- `app/sub_agents/clickup_agent/agent.py`
- `app/tools.py` (create_clickup_task, export_inbox_to_clickup)

**Tools:**
- `create_clickup_task(name, assignee, due_date, description)` → dict
- `export_inbox_to_clickup(item_id)` → dict

**Model:** `gemini-2.5-flash`

---

## Checklist modyfikacji ClickUpAgent

- [ ] Czy `CLICKUP_API_KEY` i `CLICKUP_DEFAULT_LIST_ID` są w `.env`?
- [ ] Czy nowe pole w tasku jest obsługiwane przez ClickUp API v2?
- [ ] Czy `export_inbox_to_clickup` aktualizuje `clickup_task_id` w SQLite?
- [ ] Czy testowałeś z realnym API (lub mock jest wystarczający)?
- [ ] Czy zaktualizowałeś ten dokument?
