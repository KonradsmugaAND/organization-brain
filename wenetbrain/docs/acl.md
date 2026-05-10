# Macierz ACL (źródło prawdy)

| Akcja | Member | Editor | Manager | Admin |
|-------|--------|--------|---------|-------|
| Czytaj bank | Tak | Tak | Tak | Tak |
| Dodaj notatkę prywatną | Tak | Tak | Tak | Tak |
| Zaproponuj notatkę do banku | Tak | Tak | Tak | Tak |
| Zatwierdź propozycję membera | Nie | Tak | Tak | Tak |
| Zaproponuj awans do banku wyżej | Nie | Nie | Tak | Tak |
| Zatwierdź awans z dołu | Nie | Nie | Nie | Tak |
| Zarządzaj rolami | Nie | Nie | Nie | Tak |
| Konfiguruj integracje | Nie | Nie | Nie | Tak |

## Gdzie zmieniać

- Logika ACL jest w `app/tools.py` → `get_user_acl()` i `ensure_user()`
- W przyszłości: dodać middleware w `app/fast_api_app.py` lub w samym InboxAgent

## Flow „Dodaj notatkę do przestrzeni"

Implementacja: `app/api_routes.py` — `POST /api/my/spaces/{bank_id}/notes`,
`GET /api/inbox`, `POST /api/inbox/{id}/approve|reject`. Stała ról
publikujących bezpośrednio: `APPROVER_ROLES = {"editor","manager","admin"}`.

1. **Brak ACL do przestrzeni** → `403`. Notatka nie powstaje.
2. **Editor / Manager / Admin** → bezpośredni `upsert_chunk` do banku
   docelowego. Response: `{status:"created", mode:"direct", chunk_id}`.
3. **Member** →
   - kopia notatki ląduje w `private_<user_id>` z payloadem
     `proposal_for_bank=<docelowy>`, `proposal_status="pending_approval"`
     (autor od razu widzi notatkę u siebie),
   - `create_inbox_item(item_type="note", bank_id=<docelowy>,
     user_id=<autor>, proposed_by=<autor>, content=JSON({title, content}))`,
   - response: `{status:"pending_approval", mode:"proposal", inbox_id,
     private_chunk_id}`.

`GET /api/inbox` zwraca dla każdego użytkownika:
- własne itemy (`user_id=me`),
- pending note proposals targetujące banki, w których user ma rolę z
  `APPROVER_ROLES`. Każdy item ma flagi `is_mine` i `can_approve`.

`POST /api/inbox/{id}/approve` dla `item_type='note'`:
- wymaga, aby zatwierdzający miał Editor+ w `bank_id` propozycji,
- parsuje JSON `content`, robi `upsert_chunk` do banku docelowego z payloadem
  `{type:"note", user_id=proposed_by, title, approved_by, from_inbox_id}`,
- aktualizuje `inbox.status="approved"`, dodaje wpis w `audit_log`
  (`event_type="approve_note_proposal"`),
- znaczy prywatną kopię autora `proposal_status="approved"`.

`POST /api/inbox/{id}/reject` dla `item_type='note'`:
- dozwolone dla Editor+ w `bank_id` **lub** dla `proposed_by==me` (autor
  może anulować swoją propozycję),
- znaczy prywatną kopię `proposal_status="rejected"`.

## Panel admina (port 8001)

Endpoint `POST /admin/api/spaces/{bank_id}/notes` (`admin/admin_routes.py`)
**pomija ACL** — admin może opublikować notatkę w dowolnej przestrzeni.
UI: `admin/frontend/src/components/AdminNoteModal.tsx` (osadzony w
`SpacesView.tsx`).
