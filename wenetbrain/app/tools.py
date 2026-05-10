"""Custom tools for WenetBrain agents.

Supports both Vertex AI (enterprise) and Gemini API (AI Studio) modes.
Set GOOGLE_GENAI_USE_VERTEXAI=True in .env for Vertex AI (requires gcloud ADC).
Set GOOGLE_GENAI_USE_VERTEXAI=False and provide GOOGLE_API_KEY for quick testing.
"""

import json
import os
import sqlite3
import uuid
from datetime import UTC, datetime, timedelta
from typing import Any

import bcrypt
import requests
from dotenv import load_dotenv
from jose import JWTError, jwt
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, PointStruct, VectorParams

try:
    from google import genai
except ImportError:
    genai = None  # type: ignore[misc,assignment]

load_dotenv()

# ── Config ───────────────────────────────────────────────────────────

QDRANT_URL = os.getenv("QDRANT_URL", "http://localhost:6333")
DB_PATH = os.getenv("WENETBRAIN_DB_PATH", "wenetbrain.db")
CLICKUP_API_KEY = os.getenv("CLICKUP_API_KEY", "")
CLICKUP_DEFAULT_LIST_ID = os.getenv("CLICKUP_DEFAULT_LIST_ID", "")
EMBEDDING_SIZE = int(os.getenv("EMBEDDING_SIZE", "768"))

# Auth config
SECRET_KEY = os.getenv("SECRET_KEY", "wenetbrain-dev-secret-key-change-in-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24  # 1 day

# bcrypt is used directly (passlib has compatibility issues with bcrypt 5.0+)


def migrate_db() -> None:
    """Run migrations on existing SQLite database.

    Ensures the spaces table exists and adds missing columns
    (e.g. parent_id) for backward compatibility with older DBs.
    """
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    # Ensure spaces table exists (may have been created outside init_db.py)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS spaces (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            bank_id TEXT UNIQUE NOT NULL,
            space_type TEXT DEFAULT 'team',
            description TEXT,
            company TEXT DEFAULT 'webwave',
            parent_id TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    # Add parent_id if missing
    cols = [r[1] for r in cursor.execute("PRAGMA table_info(spaces)").fetchall()]
    if "parent_id" not in cols:
        cursor.execute("ALTER TABLE spaces ADD COLUMN parent_id TEXT")
    # Add created_by to meetings if missing
    meeting_cols = [r[1] for r in cursor.execute("PRAGMA table_info(meetings)").fetchall()]
    if "created_by" not in meeting_cols:
        cursor.execute("ALTER TABLE meetings ADD COLUMN created_by TEXT")
    conn.commit()
    conn.close()


# ── Qdrant helpers ───────────────────────────────────────────────────


def _get_qdrant() -> QdrantClient:
    return QdrantClient(url=QDRANT_URL)


def _ensure_collection(bank_id: str) -> None:
    """Create Qdrant collection if it does not exist."""
    client = _get_qdrant()
    if not client.collection_exists(bank_id):
        client.create_collection(
            collection_name=bank_id,
            vectors_config=VectorParams(size=EMBEDDING_SIZE, distance=Distance.COSINE),
        )


def _fake_embedding(text: str) -> list[float]:
    """Deterministic fake embedding for PoC when no API is available."""
    import numpy as np

    rng = np.random.default_rng(abs(hash(text)) % (2**31))
    vec = rng.random(EMBEDDING_SIZE).astype(np.float32)
    vec = vec / np.linalg.norm(vec)
    return vec.tolist()


def _get_genai_client() -> genai.Client:
    """Return a google.genai.Client configured for Vertex AI or Gemini API."""
    from google import genai

    use_vertex = os.getenv("GOOGLE_GENAI_USE_VERTEXAI", "False").lower() == "true"
    if use_vertex:
        return genai.Client(
            vertexai=True,
            project=os.getenv("GOOGLE_CLOUD_PROJECT"),
            location=os.getenv("GOOGLE_CLOUD_LOCATION", "us-central1"),
        )
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        raise RuntimeError(
            "No GOOGLE_API_KEY set. Add it to .env or enable Vertex AI (GOOGLE_GENAI_USE_VERTEXAI=True + gcloud auth)."
        )
    return genai.Client(api_key=api_key)


def embed_text(text: str) -> list[float]:
    """Return embedding vector for text using Vertex AI or Gemini API."""
    try:
        client = _get_genai_client()
        result = client.models.embed_content(
            model="text-embedding-004",
            contents=text,
        )
        return result.embeddings[0].values
    except Exception as exc:
        print(f"[WARN] Embedding API failed ({exc}), falling back to fake embeddings.")
        return _fake_embedding(text)


def upsert_chunk(
    bank_id: str,
    chunk_id: str,
    chunk_text: str,
    payload: dict[str, Any],
) -> str:
    """Store a chunk with its embedding in Qdrant."""
    _ensure_collection(bank_id)
    client = _get_qdrant()
    vector = embed_text(chunk_text)
    point = PointStruct(id=chunk_id, vector=vector, payload={**payload, "chunk_text": chunk_text})
    client.upsert(collection_name=bank_id, points=[point])
    return f"upserted {chunk_id} into {bank_id}"


def retrieve_chunks(
    query: str,
    permitted_banks: list[str],
    top_k: int = 5,
) -> list[dict[str, Any]]:
    """Search Qdrant across permitted banks."""
    if not permitted_banks:
        return []
    client = _get_qdrant()
    vector = embed_text(query)
    results = []
    for bank in permitted_banks:
        _ensure_collection(bank)
        try:
            hits = client.query_points(
                collection_name=bank,
                query=vector,
                limit=top_k,
                with_payload=True,
            ).points
            for h in hits:
                results.append(
                    {
                        "bank_id": bank,
                        "score": h.score,
                        "payload": h.payload,
                    }
                )
        except Exception as exc:
            # collection may not exist yet
            print(f"Search error in {bank}: {exc}")
    # global sort by score
    results.sort(key=lambda x: x["score"], reverse=True)
    return results[:top_k]


# ── SQLite / Inbox helpers ───────────────────────────────────────────


def _db() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def create_inbox_item(
    user_id: str,
    item_type: str,
    content: str,
    meeting_id: str | None = None,
    bank_id: str | None = None,
    proposed_by: str | None = None,
) -> str:
    """Create a new inbox item for HITL approval."""
    item_id = str(uuid.uuid4())
    with _db() as conn:
        conn.execute(
            """
            INSERT INTO inbox (id, user_id, meeting_id, bank_id, item_type, content, proposed_by)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (item_id, user_id, meeting_id, bank_id, item_type, content, proposed_by),
        )
        conn.commit()
    return item_id


def get_inbox_items(user_id: str, status: str | None = None) -> list[dict[str, Any]]:
    """List inbox items for a user.

    Args:
        user_id: The user ID to filter by.
        status: Optional status filter (e.g. 'pending_approval', 'approved').

    Returns:
        List of inbox item dictionaries.
    """
    with _db() as conn:
        sql = "SELECT * FROM inbox WHERE user_id = ?"
        params: list[str | None] = [user_id]
        if status:
            sql += " AND status = ?"
            params.append(status)
        sql += " ORDER BY created_at DESC"
        rows = conn.execute(sql, params).fetchall()
        return [dict(r) for r in rows]


def approve_inbox_item(item_id: str, approved_by: str) -> dict:
    """Approve an inbox item and log audit."""
    with _db() as conn:
        row = conn.execute("SELECT * FROM inbox WHERE id = ?", (item_id,)).fetchone()
        if not row:
            return {"error": "item not found"}
        conn.execute(
            "UPDATE inbox SET status = 'approved', approved_by = ?, approved_at = ? WHERE id = ?",
            (approved_by, datetime.now(UTC).isoformat(), item_id),
        )
        conn.execute(
            "INSERT INTO audit_log (event_type, user_id, item_id, to_bank, details) VALUES (?, ?, ?, ?, ?)",
            ("approve", approved_by, item_id, row["bank_id"], json.dumps({"type": row["item_type"]})),
        )
        conn.commit()
    return {"status": "approved", "item_id": item_id}


def reject_inbox_item(item_id: str, rejected_by: str) -> dict:
    """Reject an inbox item."""
    with _db() as conn:
        conn.execute(
            "UPDATE inbox SET status = 'rejected', approved_by = ? WHERE id = ?",
            (rejected_by, item_id),
        )
        conn.commit()
    return {"status": "rejected", "item_id": item_id}


# ── ClickUp helpers ──────────────────────────────────────────────────


def create_clickup_task(name: str, assignee: str, due_date: str | None, description: str) -> dict:
    """Create a task in ClickUp. Returns mock data if no API key."""
    if not CLICKUP_API_KEY or not CLICKUP_DEFAULT_LIST_ID:
        # PoC mock
        return {
            "mock": True,
            "task_id": f"MOCK-{uuid.uuid4().hex[:8]}",
            "name": name,
            "assignee": assignee,
            "due_date": due_date,
            "description": description,
        }
    url = f"https://api.clickup.com/api/v2/list/{CLICKUP_DEFAULT_LIST_ID}/task"
    headers = {"Authorization": CLICKUP_API_KEY, "Content-Type": "application/json"}
    payload: dict[str, Any] = {
        "name": name,
        "description": description,
    }
    if due_date:
        payload["due_date"] = due_date
    resp = requests.post(url, headers=headers, json=payload, timeout=30)
    resp.raise_for_status()
    return resp.json()


def export_inbox_to_clickup(item_id: str) -> dict:
    """Export an inbox action_item to ClickUp and update status."""
    with _db() as conn:
        row = conn.execute("SELECT * FROM inbox WHERE id = ?", (item_id,)).fetchone()
        if not row:
            return {"error": "item not found"}
        data = json.loads(row["content"]) if row["content"].startswith("{") else {"description": row["content"]}
        result = create_clickup_task(
            name=data.get("description", row["content"]),
            assignee=data.get("assignee", "nieprzypisane"),
            due_date=data.get("due_date"),
            description=f"Wygenerowane przez WenetBrain: {row['content']}",
        )
        conn.execute(
            "UPDATE inbox SET status = 'exported_to_clickup', clickup_task_id = ? WHERE id = ?",
            (result.get("id", result.get("task_id")), item_id),
        )
        conn.commit()
    return {"status": "exported", "clickup": result}


# ── Calendar helpers ─────────────────────────────────────────────────


def get_calendar_events(user_email: str, days_ahead: int = 1) -> list[dict]:
    """Fetch events from MS365 Calendar. Returns mock data if no token."""
    ms_token = os.getenv("MS365_ACCESS_TOKEN", "")
    if not ms_token:
        # PoC mock
        return [
            {
                "subject": "Planning Q2 — Product + Marketing",
                "start": {"dateTime": "2026-05-09T14:00:00"},
                "end": {"dateTime": "2026-05-09T15:00:00"},
                "attendees": [
                    {"emailAddress": {"name": "Anna Kowalska"}},
                    {"emailAddress": {"name": "Marek Wójcik"}},
                ],
                "onlineMeeting": None,
            }
        ]
    url = f"https://graph.microsoft.com/v1.0/me/events?$filter=start/dateTime ge '{datetime.now(UTC).isoformat()}'&$select=subject,start,end,attendees,onlineMeeting&$top=20"
    resp = requests.get(url, headers={"Authorization": f"Bearer {ms_token}"}, timeout=30)
    resp.raise_for_status()
    return resp.json().get("value", [])


# ── Meeting / Transcription helpers ──────────────────────────────────


def transcribe_audio_file(audio_path: str) -> dict:
    """Transcribe audio using Gemini multimodal (audio-in).

    Falls back to sidecar .txt file or mock placeholder if API is unavailable.
    """
    txt_path = audio_path.rsplit(".", 1)[0] + ".txt"
    if os.path.exists(txt_path):
        with open(txt_path, encoding="utf-8") as f:
            text = f.read()
        return {"transcript": text, "source": "file", "duration_sec": 0}

    if not os.path.exists(audio_path):
        return {
            "transcript": f"[Plik audio nie istnieje: {audio_path}]",
            "source": "error",
            "duration_sec": 0,
        }

    try:
        client = _get_genai_client()
        with open(audio_path, "rb") as f:
            audio_bytes = f.read()
        import mimetypes

        mime, _ = mimetypes.guess_type(audio_path)
        mime = mime or "audio/wav"

        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=[
                "Transkrybuj to spotkanie po polsku. Zwróć tylko czystą transkrypcję.",
                {"mime_type": mime, "data": audio_bytes},
            ],
        )
        transcript = response.text or ""
        return {"transcript": transcript, "source": "gemini", "duration_sec": 0}
    except Exception as exc:
        print(f"[WARN] Transcription API failed ({exc}), returning mock.")
        return {
            "transcript": f"[Mock transcript for {audio_path} — API error: {exc}]",
            "source": "mock",
            "duration_sec": 0,
        }


def save_meeting_metadata(
    meeting_id: str,
    title: str,
    meeting_type: str,
    date: str,
    participants: list[str],
    transcript_path: str | None = None,
    audio_path: str | None = None,
) -> str:
    """Persist meeting record in SQLite."""
    with _db() as conn:
        conn.execute(
            """
            INSERT OR REPLACE INTO meetings (id, title, meeting_type, date, participants, transcript_path, audio_path)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                meeting_id,
                title,
                meeting_type,
                date,
                json.dumps(participants),
                transcript_path,
                audio_path,
            ),
        )
        conn.commit()
    return meeting_id


# ── ACL helpers ──────────────────────────────────────────────────────


def get_user_acl(user_id: str) -> list[dict]:
    """Return list of {bank_id, role} for user."""
    with _db() as conn:
        rows = conn.execute("SELECT bank_id, role FROM user_acl WHERE user_id = ?", (user_id,)).fetchall()
        return [dict(r) for r in rows]


def ensure_user(
    user_id: str,
    name: str,
    role: str = "member",
    team: str = "",
    company: str = "webwave",
    email: str = "",
    password_hash: str | None = None,
) -> None:
    """Create user and default ACLs if not exists."""
    with _db() as conn:
        conn.execute(
            """
            INSERT OR IGNORE INTO users (id, name, role, team, company, email, password_hash)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (user_id, name, role, team, company, email, password_hash),
        )
        # default ACLs — support both raw names and full bank_ids
        company_bank = company if company.startswith("company_") else f"company_{company}"
        team_bank = team if team.startswith("team_") else f"team_{team}" if team else ""
        defaults = [
            ("group", "member"),
            (company_bank, "member"),
            (f"private_{user_id}", "admin"),
        ]
        if team_bank:
            defaults.append((team_bank, "member"))
        for bank, r in defaults:
            conn.execute(
                "INSERT OR IGNORE INTO user_acl (user_id, bank_id, role) VALUES (?, ?, ?)",
                (user_id, bank, r),
            )
        # ensure private space record exists in spaces table
        private_bank_id = f"private_{user_id}"
        conn.execute(
            """
            INSERT OR IGNORE INTO spaces (id, name, bank_id, space_type, description, company)
            VALUES (?, ?, ?, 'private', '', ?)
            """,
            (private_bank_id, "Prywatne", private_bank_id, company),
        )
        conn.commit()


# ── Auth helpers ─────────────────────────────────────────────────────


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash."""
    if not hashed_password:
        return False
    return bcrypt.checkpw(plain_password.encode("utf-8"), hashed_password.encode("utf-8"))


def get_password_hash(password: str) -> str:
    """Hash a password."""
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def create_access_token(data: dict, expires_delta: timedelta | None = None) -> str:
    """Create a JWT access token."""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(UTC) + expires_delta
    else:
        expire = datetime.now(UTC) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def decode_access_token(token: str) -> dict | None:
    """Decode and validate a JWT access token."""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError:
        return None


def authenticate_user(user_id: str, password: str) -> dict | None:
    """Authenticate a user by user_id and password."""
    with _db() as conn:
        row = conn.execute(
            "SELECT id, name, role, team, company, email, password_hash FROM users WHERE id = ?",
            (user_id,),
        ).fetchone()
        if not row:
            return None
        user = dict(row)
        if not user.get("password_hash"):
            return None
        if not verify_password(password, user["password_hash"]):
            return None
        return user


def get_user_by_id(user_id: str) -> dict | None:
    """Get user by ID."""
    with _db() as conn:
        row = conn.execute(
            "SELECT id, name, role, team, company, email FROM users WHERE id = ?",
            (user_id,),
        ).fetchone()
        return dict(row) if row else None


def list_spaces() -> list[dict[str, Any]]:
    """List all spaces.

    Returns:
        List of space dictionaries ordered by creation date (newest first).
    """
    with _db() as conn:
        rows = conn.execute("SELECT * FROM spaces ORDER BY created_at DESC").fetchall()
        return [dict(r) for r in rows]


def create_space(
    space_id: str,
    name: str,
    bank_id: str,
    space_type: str = "team",
    description: str = "",
    company: str = "webwave",
    parent_id: str | None = None,
) -> dict[str, Any]:
    """Create a new space.

    Args:
        space_id: Unique identifier for the space.
        name: Human-readable name.
        bank_id: Qdrant collection / knowledge bank identifier.
        space_type: Type of space ('weall', 'company', 'team', 'group', 'private').
        description: Optional description.
        company: Company identifier.
        parent_id: Optional parent space ID for hierarchical spaces.

    Returns:
        Dictionary with created space metadata.
    """
    with _db() as conn:
        conn.execute(
            """
            INSERT INTO spaces (id, name, bank_id, space_type, description, company, parent_id)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (space_id, name, bank_id, space_type, description, company, parent_id),
        )
        conn.commit()
    return {"id": space_id, "name": name, "bank_id": bank_id, "parent_id": parent_id}


def update_space(
    space_id: str,
    name: str | None = None,
    bank_id: str | None = None,
    description: str | None = None,
) -> dict[str, str]:
    """Update an existing space.

    Args:
        space_id: The space to update.
        name: New name, or None to keep current.
        bank_id: New bank_id, or None to keep current.
        description: New description, or None to keep current.

    Returns:
        Status dictionary indicating update result.
    """
    fields: list[str] = []
    values: list[str | None] = []
    if name is not None:
        fields.append("name = ?")
        values.append(name)
    if bank_id is not None:
        fields.append("bank_id = ?")
        values.append(bank_id)
    if description is not None:
        fields.append("description = ?")
        values.append(description)
    if not fields:
        return {"status": "no_change", "id": space_id}
    values.append(space_id)
    with _db() as conn:
        conn.execute(f"UPDATE spaces SET {', '.join(fields)} WHERE id = ?", values)
        conn.commit()
    return {"status": "updated", "id": space_id}


def delete_space(space_id: str) -> dict[str, str]:
    """Delete a space by ID.

    Args:
        space_id: The space to delete.

    Returns:
        Status dictionary confirming deletion.
    """
    with _db() as conn:
        conn.execute("DELETE FROM spaces WHERE id = ?", (space_id,))
        conn.commit()
    return {"status": "deleted", "id": space_id}
