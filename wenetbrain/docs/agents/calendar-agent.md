# CalendarAgent

**Co robi:**
- Pobiera eventy z MS365 Calendar (Graph API)
- Sugeruje typ spotkania na podstawie listy uczestników

**Power-up Skills:**
- `python-testing-patterns` (Weryfikacja heurystyki sugestii typów spotkań)

**Pliki:**
- `app/sub_agents/calendar_agent/agent.py`
- `app/tools.py` (get_calendar_events, suggest_meeting_type)

**Tools:**
- `get_calendar_events(user_email, days_ahead)` → list[dict]
- `suggest_meeting_type(attendees)` → str

**Model:** `gemini-2.5-flash`

---

## Checklist modyfikacji CalendarAgent

- [ ] Czy `MS365_ACCESS_TOKEN` jest ważny (OAuth2 refresh)?
- [ ] Czy nowe pola z Graph API są obsługiwane?
- [ ] Czy heurystyka `suggest_meeting_type` jest zgodna z RoutingAgent?
- [ ] Czy zaktualizowałeś ten dokument?
