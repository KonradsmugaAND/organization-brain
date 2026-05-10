"""End-to-end WenetBrain pipeline test with real Gemini + Vertex AI.

Tests:
  1. Embedding + Qdrant upsert/retrieve
  2. Gemini extraction from a sample meeting transcript
  3. Full RAG query over stored chunks

Run:
    uv run python test_e2e_wenetbrain.py
"""

import os
import uuid

from dotenv import load_dotenv

load_dotenv()

SAMPLE_TRANSCRIPT = """
Anna Kowalska: Dzień dobry, zaczynamy sprint planning. Mamy do zrobienia trzy zadania: naprawić bug w autoryzacji, zaktualizować landing page i przygotować raport Q2.
Marek Wójcik: Bug w autoryzacji jest krytyczny. Proponuję przypisać go do Piotra, deadline na piątek.
Anna Kowalska: Zgoda. Landing page może poczekać do przyszłego tygodnia.
Piotr Nowak: Dobra, biorę buga. Potrzebuję dostęp do stagingu.
Anna Kowalska: Decyzja: przepuszczamy landing page w tym sprincie. Focus na bug i raport.
Marek Wójcik: Raport przygotuję do środy. Potrzebuję danych z Google Analytics.
Anna Kowalska: Wszyscy zgadzają się z planem? Tak, zamykamy temat.
""".strip()


def test_qdrant_pipeline() -> bool:
    """Test embedding + Qdrant upsert + retrieve."""
    print("\n🧪 Test 1: Qdrant pipeline (embedding → upsert → retrieve)")
    try:
        from app.tools import retrieve_chunks, upsert_chunk

        bank_id = "test_team_product_webwave"
        meeting_id = str(uuid.uuid4())
        chunk_text = "Decyzja: przepuszczamy landing page w tym sprincie. Focus na bug i raport."

        # Upsert
        upsert_chunk(
            bank_id=bank_id,
            chunk_id=str(uuid.uuid4()),
            chunk_text=chunk_text,
            payload={
                "meeting_id": meeting_id,
                "meeting_title": "Sprint Planning Q2",
                "meeting_date": "2026-05-10",
                "chunk_type": "decision",
                "speaker": "Anna Kowalska",
            },
        )
        print(f"   ✅ Upserted chunk into {bank_id}")

        # Retrieve
        results = retrieve_chunks(
            query="co z landing page",
            permitted_banks=[bank_id],
            top_k=3,
        )
        if results:
            top = results[0]
            print(f"   ✅ Retrieved {len(results)} chunks")
            print(f"   Top score: {top['score']:.3f}")
            print(f"   Text: {top['payload']['chunk_text'][:100]}...")
            return True
        print("   ❌ No results retrieved")
        return False
    except Exception as exc:
        print(f"   ❌ Qdrant pipeline failed: {exc}")
        return False


def test_gemini_extraction() -> bool:
    """Test Gemini extraction from a real transcript."""
    print("\n🧪 Test 2: Gemini extraction (transcript → action items / decisions)")
    try:
        from google import genai

        client = genai.Client(
            vertexai=True,
            project=os.getenv("GOOGLE_CLOUD_PROJECT"),
            location=os.getenv("GOOGLE_CLOUD_LOCATION", "us-central1"),
        )

        prompt = f"""Przeanalizuj poniższą transkrypcję spotkania.
Wyciągnij:
1. Decyzje (decisions)
2. Zadania do wykonania (action_items) — kto, co, do kiedy
3. Notatki (notes)

Zwróć wynik w formacie JSON:
{{
  "decisions": ["..."],
  "action_items": [{{"task": "...", "assignee": "...", "due_date": "..."}}],
  "notes": ["..."]
}}

Transkrypcja:
{SAMPLE_TRANSCRIPT}
"""

        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt,
        )
        text = response.text or ""
        print(f"   ✅ Gemini responded ({len(text)} chars)")
        # Show first 500 chars
        preview = text.replace("\n", " ")[:500]
        print(f"   Preview: {preview}...")
        return True
    except Exception as exc:
        print(f"   ❌ Gemini extraction failed: {exc}")
        return False


def test_rag_chat() -> bool:
    """Test RAG chat by querying stored knowledge."""
    print("\n🧪 Test 3: RAG chat (query → retrieve → Gemini answer)")
    try:
        from google import genai

        from app.tools import retrieve_chunks

        bank_id = "test_team_product_webwave"
        query = "kto ma naprawić buga w autoryzacji?"

        chunks = retrieve_chunks(query, permitted_banks=[bank_id], top_k=3)
        context = "\n".join(
            f"- {c['payload'].get('chunk_text', '')}" for c in chunks
        )

        client = genai.Client(
            vertexai=True,
            project=os.getenv("GOOGLE_CLOUD_PROJECT"),
            location=os.getenv("GOOGLE_CLOUD_LOCATION", "us-central1"),
        )

        prompt = f"""Odpowiedz na pytanie użytkownika na podstawie poniższego kontekstu z spotkania.

Kontekst:
{context}

Pytanie: {query}
"""
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt,
        )
        answer = response.text or ""
        print(f"   ✅ RAG answer ({len(answer)} chars)")
        print(f"   Answer: {answer[:300]}...")
        return True
    except Exception as exc:
        print(f"   ❌ RAG chat failed: {exc}")
        return False


def main():
    print("=" * 60)
    print("WenetBrain — End-to-End Pipeline Test (Real AI)")
    print("=" * 60)

    results = []
    results.append(("Qdrant pipeline", test_qdrant_pipeline()))
    results.append(("Gemini extraction", test_gemini_extraction()))
    results.append(("RAG chat", test_rag_chat()))

    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    for name, ok in results:
        icon = "✅" if ok else "❌"
        print(f"   {icon} {name}")

    all_ok = all(r[1] for r in results)
    if all_ok:
        print("\n🚀 Full pipeline works! WenetBrain is now AI-powered.")
    else:
        print("\n⚠️ Some tests failed. Check errors above.")
    return 0 if all_ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
