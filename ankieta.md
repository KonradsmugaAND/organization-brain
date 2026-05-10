# Ankieta konkursowa — WenetBrain

---

## Na czym polega problem?

W codziennej pracy zespołów produktowych i projektowych spotkania generują ogromną ilość wiedzy — ustalenia, decyzje, zadania — która natychmiast po wyjściu z call'a zaczyna zanikać. Szacujemy, że każdy pracownik uczestniczy średnio w 4–6 spotkaniach tygodniowo (ok. 20 miesięcznie). Sporządzenie rzetelnych notatek po jednym spotkaniu zajmuje 20–40 minut, co przy 10-osobowym zespole daje **ok. 70–130 godzin miesięcznie** poświęconych wyłącznie na dokumentowanie — zanim ktokolwiek zdąży faktycznie wykonać to, co ustalono.

Bieżące podejście (prowadzenie "second brain" w Notion) działa, ale wymaga wysokiej dyscypliny i jest wyłącznie manualne — nie każdy pracownik jest skłonny konsekwentnie je prowadzić. Oczywiście mało kto robi taką dokumentację na co dzień, co bezpośrednio prowadzi do utraty wiedzy i konieczności ponownych konsultacji. Efekt: wiedza jest niekompletna, trudna do przeszukania i niewidoczna między zespołami.

Równolegle funkcjonują komercyjne narzędzia do transkrypcji spotkań (np. Fireflies.ai). Licencja dla 50 pracowników webwave kosztowałaby szacunkowo **800–2 000 USD miesięcznie** — i nadal nie rozwiązuje problemu przeszukiwania wiedzy ani integracji z obiegiem zadań.

Konkretne skutki braku rozwiązania:
- Ustalenia ze spotkań umykają lub są powielane na kolejnych spotkaniach
- Action items nie trafiają do systemów zadaniowych (ClickUp) — wykonanie zależy od pamięci uczestników
- Nowy pracownik lub osoba nieobecna na spotkaniu nie ma szybkiego dostępu do kontekstu decyzji
- Wiedza firmowa jest rozproszona: część w Notion, część w mailach, część tylko w głowach

---

## Jak będzie wyglądał sukces?

Rozwiązanie uznamy za sukces, gdy:

- **Czas sporządzania notatek ze spotkania skróci się z ~30 minut do ~2 minut** — pracownik nagrywa spotkanie, system automatycznie generuje transkrypt, wyodrębnia action items, decyzje i notatki
- **100% action items ze spotkań trafia automatycznie do ClickUp** (z możliwością akceptacji przez managera przed wysłaniem), eliminując przypadki, w których zadanie „znika" po rozmowie
- **Czas potrzebny na znalezienie konkretnej decyzji lub ustalenia z przeszłości skróci się z kilkudziesięciu minut (przeszukiwanie Notion, maili, Teams) do poniżej 30 sekund** — przez czat AI zadający pytanie w języku naturalnym
- Nowy pracownik będzie mógł samodzielnie zrozumieć kontekst projektu przez rozmowę z bazą wiedzy zespołu — bez godzin onboardingu z innymi osobami
- Koszt narzędzia dla całej organizacji będzie **co najmniej 5× niższy** niż ekwiwalentne rozwiązania SaaS (self-hosted, brak opłat per-seat) — a sama wiedza firmowa pozostaje wyłącznie w naszej infrastrukturze, nie na serwerach zewnętrznych dostawców. Mamy też pełną kontrolę nad rozwojem narzędzia: możemy dowolnie rozszerzać funkcjonalności, integrować z własnymi systemami i nie jesteśmy uzależnieni od roadmapy ani decyzji biznesowych zewnętrznego dostawcy

---

## Jak działa rozwiązanie od strony technicznej?

WenetBrain to działający prototyp lokalnie hostowanego "second brain" dla organizacji. Architektura opiera się na kilku warstwach:

**Model / platforma AI:**
- **Google Gemini 2.5 Flash** (przez Vertex AI / AI Studio) — główny model LLM do ekstrakcji wiedzy, odpowiedzi w chacie RAG i orkiestracji agentów
- **Google ADK (Agent Development Kit) 1.33+** — framework do budowy agentów AI; system działa jako hierarchia 8 wyspecjalizowanych sub-agentów (MeetingAgent, ExtractionAgent, RoutingAgent, KnowledgeAgent, ChatAgent, ClickUpAgent, CalendarAgent, InboxAgent)
- **Transkrypcja audio** — AI Speech-to-Text po przesłaniu nagrania spotkania

**Narzędzia i aplikacje:**
- **FastAPI** (Python) — backend REST API + obsługa protokołu A2A
- **React 19 + TypeScript + Vite + shadcn/ui** — interfejs użytkownika (aplikacja główna + panel administracyjny)
- **ClickUp API v2** — integracja eksportu zadań z HITL (manager zatwierdza przed wysłaniem)
- **Microsoft 365 Calendar** — synchronizacja spotkań

**Zasoby techniczne:**
- **Qdrant** (wektorowa baza danych, Docker) — przechowuje embeddingi notatek i transkryptów; umożliwia semantyczne wyszukiwanie (RAG)
- **SQLite** — metadane użytkowników, przestrzenie, ACL, audit log (docelowo PostgreSQL)
- **JWT + OAuth2 + bcrypt** — autentykacja; cztery poziomy dostępu do wiedzy: prywatny, zespołowy, firmowy, grupowy (cała organizacja)
- Uruchamiane lokalnie / na własnym serwerze — brak zewnętrznych subskrypcji per-seat

Przepływ: pracownik nagrywa spotkanie → przesyła do aplikacji → MeetingAgent transkrybuje → ExtractionAgent wyodrębnia action items / decyzje / notatki → RoutingAgent kieruje wiedzę do właściwych przestrzeni (wg ACL) → KnowledgeAgent zapisuje embeddingi w Qdrant → InboxAgent czeka na akceptację managera → ClickUpAgent tworzy zadania w ClickUp. Każdy pracownik może w dowolnym momencie zapytać ChatAgent o dowolną wiedzę z bazy.

---

## Co się stanie, jeśli tego nie zrobimy?

Bez WenetBrain organizacja będzie dalej funkcjonować w trybie, który skaluje się źle:

- Wraz ze wzrostem liczby spotkań i zespołów rośnie liniowo czas tracony na ręczne dokumentowanie — każde 5 nowych osób to kolejne ~30–60 godzin dokumentacji miesięcznie
- Ryzyko błędów operacyjnych: ustalenia nieudokumentowane na czas są zapominane lub realizowane niezgodnie z intencją — koszty poprawek i nieporozumień trudno zmierzyć, ale są realne
- Jeśli zdecydujemy się na zakup komercyjnego narzędzia (Fireflies, Otter, Notion AI), koszt dla 50 osób to **10 000–25 000 USD rocznie**, bez gwarancji że wiedza pozostanie w granicach organizacji (dane na zewnętrznych serwerach)
- Brak centralnej, przeszukiwalnej bazy wiedzy coraz bardziej spowalnia onboarding nowych pracowników i utrudnia podejmowanie decyzji w oparciu o historię projektu

---

## Kto jest odpowiedzialny za wyniki Twojego obszaru?

*(Uzupełnij: imię i nazwisko managera / osoby odpowiedzialnej za wyniki zespołu)*

---

## Pokaż nam, jak to działa (link do wideo)

*(Uzupełnij: nagraj krótkie demo — uruchom aplikację, nagraj spotkanie lub prześlij plik audio, pokaż wyekstrahowane action items, przejdź przez czat AI z pytaniem np. "Co mam zrobić w tym tygodniu?")*

---

## Mam już działający prototyp (PoC)?

**TAK** — działający prototyp jest dostępny lokalnie. Obejmuje:
- Upload i transkrypcję spotkań
- Automatyczną ekstrakcję action items, decyzji i notatek
- Wektorową bazę wiedzy z podziałem na przestrzenie (prywatna / zespół / firma / grupa)
- Czat AI (RAG) z cytowaniem źródeł
- Eksport zadań do ClickUp z akceptacją managera (HITL)
- Panel administracyjny do zarządzania użytkownikami i przestrzeniami
- Synchronizację z MS365 Calendar

---

*Projekt: WenetBrain | Stack: Google ADK + Gemini 2.5 Flash + Qdrant + FastAPI + React 19*
