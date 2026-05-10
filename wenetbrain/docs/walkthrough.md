# WenetBrain — Walkthrough

> Kompletny przewodnik po architekturze, komponentach i flow aplikacji WenetBrain.

---

## 1. Architektura ogólna

```
┌─────────────────────────────────────────────────────────────┐
│                        Użytkownik                            │
│  ┌──────────────┐  ┌────────────────┐  ┌─────────────────┐ │
│  │ Main App     │  │ Admin Panel    │  │ Login Page      │ │
│  │ :8000        │  │ :8001          │  │ (shared)        │ │
│  └──────┬───────┘  └───────┬────────┘  └─────────────────┘ │
└─────────┼──────────────────┼────────────────────────────────┘
          │                  │
          └────────┬─────────┘
                   ▼
          ┌─────────────────┐
          │  FastAPI (:8000)│  ← A2A protocol, REST API
          │  FastAPI (:8001)│  ← Admin REST API
          └────────┬────────┘
                   │
     ┌─────────────┼─────────────┐
     ▼             ▼             ▼
┌─────────┐  ┌──────────┐  ┌──────────┐
│ SQLite  │  │ Qdrant   │  │ Vertex AI│
│ (users, │  │ (vectors)│  │ (Gemini) │
│ meetings│  │          │  │          │
│ inbox)  │  │          │  │          │
└─────────┘  └──────────┘  └──────────┘
```

---

## 2. Warstwy danych

### SQLite (`wenetbrain.db`)
| Tabela | Opis |
|--------|------|
| `users` | Konta użytkowników (id, name, role, team, company, email, password_hash) |
| `spaces` | Rejestr przestrzeni wiedzy (id, name, bank_id, space_type, company) |
| `meetings` | Metadane spotkań (id, title, type, date, participants, status) |
| `inbox` | HITL queue — itemy do zatwierdzenia (action_items, decyzje, spotkania) |
| `user_acl` | Macierz dostępu (user_id, bank_id, role) |
| `audit_log` | Log zmian (approve, reject, export) |

### Qdrant (wektorowa baza wiedzy)
- Każda przestrzeń = osobna kolekcja (bank_id)
- Punkt = chunk tekstu + payload (metadata)
- Embedding: `text-embedding-004` (768 wymiarów) lub fake embeddings (PoC)
- Odległość: cosine similarity

---

## 3. Flow użytkownika (Main App)

### 3.1 Logowanie
1. Użytkownik otwiera `http://localhost:8000`
2. Brak tokenu → przekierowanie na `/login.html`
3. Wspólna strona logowania (shared między app a adminem)
4. W prawym górnym rogu link do panelu admina
5. Po zalogowaniu JWT zapisywany w `localStorage`

### 3.2 Przestrzenie i notatki
- Sidebar ładuje przestrzenie z `/api/my/spaces` (filtrowane po ACL)
- Kliknięcie przestrzeni → ładuje notatki z Qdrant (`/api/my/spaces/{bank_id}/notes`)
- Notatki to chunki z `payload.type = 'note'`
- Można dodać własną notatkę przez modal

### 3.3 Wyszukiwanie
- Globalne wyszukiwanie na topbarze
- Wyszukuje po wszystkich bankach z ACL użytkownika
- Używa `retrieve_chunks()` → embedding + cosine search w Qdrant

### 3.4 Spotkania (Nagrywanie)
- Przycisk "Nagraj spotkanie" w topbarze
- Popup z tytułem, typem spotkania ({firma}, {zespół}, Prywatne), uczestnikami
- Źródła: tekst / upload pliku / nagranie audio (MediaRecorder)
- Po uploadzie: `/api/meetings/{id}/process` → Gemini ekstrahuje decyzje, zadania, notatki
- Wynik trafia do inboxu i do Qdrant (z pending_approval status)

### 3.5 Inbox
- Lista propozycji z spotkań (action_items, decyzje, spotkania)
- Mapowanie do użytkownika po imieniu / roli z treści
- Akcje:
  - **Zatwierdź i dodaj do ClickUp** → tworzy zadanie w ClickUp API
  - **Zatwierdź i dodaj do Outlook** → mock (zapisuje jako approved_outlook)
  - **Tylko zatwierdź** → zmienia status na approved
  - **Odrzuć** → zmienia status na rejected

### 3.6 Chat (RAG)
- Prawy panel — asystent AI
- Zapytanie → embedding → search po dozwolonych bankach → Gemini generuje odpowiedź z cytowaniem źródeł

---

## 4. Panel Admina (:8001)

### 4.1 Dashboard
- Statystyki: użytkownicy, spotkania, przestrzenie, pending inbox

### 4.2 Użytkownicy
- CRUD kont
- Tworzenie z hasłem (bcrypt)
- Podgląd ACL per użytkownik

### 4.3 Przestrzenie (drzewko)
- Hierarchiczny widok: Firmy → Zespoły → Grupy → Prywatne
- Kolory typów przestrzeni
- Tooltip z bank_id

### 4.4 Uprawnienia (ACL)
- Wybór użytkownika
- Lista przypisanych banków z rolami
- Dodawanie / usuwanie uprawnień
- Role: member, editor, manager, admin

---

## 5. Agent AI (ADK + A2A)

### RootAgent (`app/agent.py`)
- Tylko deleguje — zgodnie z guardrail "RootAgent Purity"
- Routing na podstawie intencji użytkownika

### Sub-agenci
| Agent | Rola | Plik |
|-------|------|------|
| meeting_agent | Transkrypcja audio | `sub_agents/meeting_agent/agent.py` |
| extraction_agent | Ekstrakcja decyzji/zadań | `sub_agents/extraction_agent/agent.py` |
| routing_agent | Routing do banków | `sub_agents/routing_agent/agent.py` |
| knowledge_agent | Qdrant RAG | `sub_agents/knowledge_agent/agent.py` |
| chat_agent | Odpowiedzi czat | `sub_agents/chat_agent/agent.py` |
| clickup_agent | Eksport do ClickUp | `sub_agents/clickup_agent/agent.py` |
| calendar_agent | MS365 Calendar | `sub_agents/calendar_agent/agent.py` |
| inbox_agent | HITL queue | `sub_agents/inbox_agent/agent.py` |

---

## 6. Integracje

### ClickUp
- `CLICKUP_API_KEY` + `CLICKUP_DEFAULT_LIST_ID` w `.env`
- Endpoint: `create_clickup_task()`
- Inbox: approve z action='clickup' tworzy zadanie

### Microsoft Outlook (mock)
- `MS365_ACCESS_TOKEN` w `.env` (opcjonalne)
- Endpoint: `get_calendar_events()`
- Inbox: approve z action='outlook' zapisuje event (mock)

### Vertex AI / Gemini
- `GOOGLE_GENAI_USE_VERTEXAI=True` dla GCP
- Lub `GOOGLE_API_KEY` dla Gemini API (AI Studio)
- Modele: `gemini-2.5-flash` (ekstrakcja, transkrypcja, chat)
- Embeddings: `text-embedding-004`

---

## 7. Bezpieczeństwo

- **Autentykacja**: JWT (HS256), token w localStorage
- **Autoryzacja**: ACL per użytkownik i per bank
- **Hasła**: bcrypt (bez passlib — direct bcrypt)
- **Rola wymagana**: admin dla panelu admina

---

## 8. Uruchomienie lokalne

```bash
cd wenetbrain
./start-local.sh
```

- Main app: http://localhost:8000
- Admin: http://localhost:8001
- Qdrant dashboard: http://localhost:6333/dashboard
- Default login: `admin` / `admin123`
