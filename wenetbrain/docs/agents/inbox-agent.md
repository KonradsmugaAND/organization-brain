# InboxAgent

**Co robi:**
- Tworzy propozycje w inboxie (pending_approval)
- Zatwierdza / odrzuca propozycje (z audit log)
- Zarządza exportem do ClickUp

**Power-up Skills:**
- `ui-ux-pro-max` (Projektowanie przepływu HITL w interfejsie)
- `python-testing-patterns` (Testowanie spójności audit log i stanów zatwierdzeń)

**Pliki:**
- `app/sub_agents/inbox_agent/agent.py`
- `app/tools.py` (create_inbox_item, get_inbox_items, approve_inbox_item, reject_inbox_item)

**Tools:**
- `create_inbox_item(user_id, item_type, content, ...)` → item_id
- `get_inbox_items(user_id, status)` → list[dict]
- `approve_inbox_item(item_id, approved_by)` → dict
- `reject_inbox_item(item_id, rejected_by)` → dict

**Model:** `gemini-2.5-flash`

---

## Checklist modyfikacji InboxAgent

- [ ] Czy nowy `item_type` jest obsługiwany przez UI / frontend?
- [ ] Czy `approve_inbox_item` wywołuje `KnowledgeAgent.upsert_chunk` (jeśli ma)?
- [ ] Czy `audit_log` zapisuje wszystkie wymagane pola?
- [ ] Czy sprawdziłeś uprawnienia (czy approver ma rolę editor/manager/admin dla danego banku)?
- [ ] Czy zaktualizowałeś ten dokument?
