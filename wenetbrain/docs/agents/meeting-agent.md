# MeetingAgent

**Co robi:**
- Transkrybuje plik audio (mock w PoC, docelowo Whisper / Gemini native audio)
- Zapisuje metadane spotkania do SQLite

**Power-up Skills:**
- `python-testing-patterns` (Weryfikacja poprawności transkrypcji i metadanych)

**Pliki:**
- `app/sub_agents/meeting_agent/agent.py`

**Tools:**
- `transcribe_audio_file(audio_path)` → dict z `transcript`
- `save_meeting_metadata(...)` → zapis do SQLite

**Model:** `gemini-2.5-flash`

---

## Checklist modyfikacji MeetingAgent

- [ ] Czy nowy tool ma poprawny docstring z type hints?
- [ ] Czy `instruction` opisuje nowy flow (np. nowy sposób nagrywania)?
- [ ] Czy testowałeś `transcribe_audio_file` bezpośrednio w Pythonie?
- [ ] Czy `save_meeting_metadata` zapisuje wszystkie wymagane pola?
- [ ] Czy zaktualizowałeś ten dokument?
- [ ] Czy dodałeś test do `tests/` lub eval case?
