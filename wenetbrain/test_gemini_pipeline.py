"""Test pipeline: Gemini API / Vertex AI connectivity for WenetBrain.

Run this after filling in GOOGLE_API_KEY (or gcloud ADC) in .env:
    uv run python test_gemini_pipeline.py
"""

import os

from dotenv import load_dotenv

load_dotenv()


def check_env() -> bool:
    """Verify required env vars are set."""
    use_vertex = os.getenv("GOOGLE_GENAI_USE_VERTEXAI", "False").lower() == "true"
    print(f"GOOGLE_GENAI_USE_VERTEXAI = {use_vertex}")

    if use_vertex:
        project = os.getenv("GOOGLE_CLOUD_PROJECT")
        if not project or project == "wenetbrain-local":
            print("❌ GOOGLE_CLOUD_PROJECT not set correctly in .env")
            return False
        print(f"✅ Vertex AI mode | project={project} | location={os.getenv('GOOGLE_CLOUD_LOCATION')}")
        print("   (Make sure you ran: gcloud auth login --update-adc)")
    else:
        key = os.getenv("GOOGLE_API_KEY")
        if not key or key == "your-ai-studio-key-here":
            print("❌ GOOGLE_API_KEY not set in .env")
            print("   Get one at: https://ai.google.dev > 'Get API key'")
            return False
        masked = key[:8] + "..." + key[-4:]
        print(f"✅ Gemini API mode | key={masked}")

    return True


def test_embedding() -> bool:
    """Test text-embedding-004."""
    print("\n🧪 Test 1: Embedding (text-embedding-004)")
    try:
        from app.tools import embed_text

        vec = embed_text("Test spotkania projektowego w WenetBrain")
        print(f"   Vector length: {len(vec)}")
        print(f"   First 5 dims: {vec[:5]}")
        if len(vec) == 768:
            print("✅ Embedding OK (768 dims)")
            return True
        print(f"⚠️ Unexpected dimension: {len(vec)} (expected 768)")
        return False
    except Exception as exc:
        print(f"❌ Embedding failed: {exc}")
        return False


def test_gemini_chat() -> bool:
    """Test basic Gemini chat completion."""
    print("\n🧪 Test 2: Gemini chat (gemini-2.5-flash)")
    try:
        from app.tools import _get_genai_client

        client = _get_genai_client()
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents="Powiedz po polsku jednym zdaniem: czym jest WenetBrain?",
        )
        text = response.text or ""
        print(f"   Response: {text[:200]}")
        if "WenetBrain" in text or "organizacyjny" in text or "mózg" in text:
            print("✅ Gemini chat OK")
            return True
        print("⚠️ Response received but content unexpected")
        return False
    except Exception as exc:
        print(f"❌ Gemini chat failed: {exc}")
        return False


def test_transcription_mock() -> bool:
    """Test transcription fallback (no audio file)."""
    print("\n🧪 Test 3: Transcription fallback (mock)")
    try:
        from app.tools import transcribe_audio_file

        result = transcribe_audio_file("/tmp/nonexistent_meeting.wav")
        print(f"   Result: {result}")
        print("✅ Transcription fallback OK")
        return True
    except Exception as exc:
        print(f"❌ Transcription failed: {exc}")
        return False


def main():
    print("=" * 60)
    print("WenetBrain — Gemini / Vertex AI Pipeline Test")
    print("=" * 60)

    if not check_env():
        print("\n⛔ Fix .env first, then rerun.")
        return 1

    results = []
    results.append(("Embedding", test_embedding()))
    results.append(("Gemini chat", test_gemini_chat()))
    results.append(("Transcription", test_transcription_mock()))

    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    for name, ok in results:
        icon = "✅" if ok else "❌"
        print(f"   {icon} {name}")

    all_ok = all(r[1] for r in results)
    if all_ok:
        print("\n🚀 All tests passed! You can now run the full app.")
    else:
        print("\n⚠️ Some tests failed. Check errors above.")
    return 0 if all_ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
