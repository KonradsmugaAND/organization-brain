# RoutingAgent

**Co robi:**
- Na podstawie `meeting_type` i `participants` decyduje, do których banków trafią chunki
- Zwraca listę `{bank_id, status}`

**Power-up Skills:**
- `python-testing-patterns` (Testowanie macierzy ACL i reguł routingu)

**Pliki:**
- `app/sub_agents/routing_agent/agent.py`

**Tools:**
- `route_to_banks(meeting_type, participants, company_id)` → dict

**Model:** `gemini-2.5-flash`

## Reguły routing (źródło prawdy)

| Typ | Banki docelowe | Status |
|-----|----------------|--------|
| team | team_{id} + private_{each} | pending_approval / approved |
| cross | company_{id} + team_{each} + private_{each} | pending_approval / approved |
| oneonone | private_{each} ONLY | approved |
| allhands | group + company_{id} + private_{each} | pending_approval / approved |

---

## Checklist modyfikacji RoutingAgent

- [ ] Czy nowa reguła routing jest zgodna z macierzą ACL ([`acl.md`](../acl.md))?
- [ ] Czy nowy `bank_id` istnieje w Qdrant (lub jest tworzony dynamicznie)?
- [ ] Czy `InboxAgent` wie, kto powinien zatwierdzić nowy bank?
- [ ] Czy zaktualizowałeś `routing.md` (jeśli zmieniłeś prompt)?
- [ ] Czy zaktualizowałeś ten dokument i macierz ACL?
