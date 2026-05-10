"""WenetBrain — REST API routes for meetings, users, admin, chat."""

import json
import os
import shutil
import uuid
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Literal

from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, UploadFile
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pydantic import BaseModel
from qdrant_client import QdrantClient

from app.tools import (
    QDRANT_URL,
    _db,
    authenticate_user,
    create_access_token,
    create_clickup_task,
    create_inbox_item,
    create_space,
    decode_access_token,
    delete_space,
    ensure_user,
    get_inbox_items,
    get_password_hash,
    get_user_acl,
    get_user_by_id,
    list_spaces,
    retrieve_chunks,
    save_meeting_metadata,
    transcribe_audio_file,
    upsert_chunk,
)

# Roles allowed to publish notes directly to a bank (no approval needed).
APPROVER_ROLES = {"editor", "manager", "admin"}

UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(exist_ok=True)

router = APIRouter(prefix="/api")

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login", auto_error=False)


def get_current_user(token: str | None = Depends(oauth2_scheme)) -> dict | None:
    """Decode JWT token and return user dict or None."""
    if not token:
        return None
    payload = decode_access_token(token)
    if not payload:
        return None
    user_id = payload.get("sub")
    if not user_id:
        return None
    return get_user_by_id(user_id)


def require_admin(user: dict | None = Depends(get_current_user)) -> dict:
    """Require authenticated admin user."""
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    if user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    return user


# ── Models ───────────────────────────────────────────────────────────

class MeetingCreate(BaseModel):
    title: str
    meeting_type: str = "team"
    participants: list[str] = []
    transcript: str | None = None


class MeetingProcessResponse(BaseModel):
    meeting_id: str
    transcript: str
    extracted: dict[str, Any]
    destinations: list[dict]
    status: str


class UserCreate(BaseModel):
    user_id: str
    name: str
    role: str = "member"
    team: str = ""
    company: str = "webwave"
    email: str = ""
    password: str = ""


class UserACLUpdate(BaseModel):
    bank_id: str
    role: str  # member, editor, manager, admin


class ChatRequest(BaseModel):
    query: str
    user_id: str
    permitted_banks: list[str] | None = None


class ChatResponse(BaseModel):
    answer: str
    sources: list[dict]


class LoginResponse(BaseModel):
    access_token: str
    token_type: str
    user: dict


class SpaceCreate(BaseModel):
    space_id: str
    name: str
    bank_id: str
    space_type: str = "team"
    description: str = ""
    company: str = "webwave"


class SpaceUpdateACL(BaseModel):
    user_id: str
    bank_id: str
    role: str


class NoteCreate(BaseModel):
    title: str
    content: str


class InboxApprove(BaseModel):
    action: Literal["clickup", "outlook", "none"]


class SettingsUpdate(BaseModel):
    name: str | None = None
    email: str | None = None
    clickup_list_id: str | None = None
    outlook_connected: bool | None = None


class OutlookEventCreate(BaseModel):
    subject: str | None = None
    start: str | None = None
    end: str | None = None
    attendees: list[str] = []


# ── Auth ─────────────────────────────────────────────────────────────

@router.post("/auth/login")
def login(form_data: OAuth2PasswordRequestForm = Depends()) -> LoginResponse:
    """Authenticate user and return JWT token."""
    user = authenticate_user(form_data.username, form_data.password)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    token = create_access_token(data={"sub": user["id"]})
    return LoginResponse(
        access_token=token,
        token_type="bearer",
        user={k: v for k, v in user.items() if k != "password_hash"},
    )


@router.get("/auth/me")
def me(current_user: dict | None = Depends(get_current_user)) -> dict:
    """Get current authenticated user."""
    if not current_user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    return current_user


# ── Meetings ─────────────────────────────────────────────────────────

@router.get("/meetings")
def list_meetings() -> list[dict]:
    """List all meetings from SQLite."""
    with _db() as conn:
        rows = conn.execute(
            "SELECT id, title, meeting_type, date, participants, status, created_at FROM meetings ORDER BY created_at DESC"
        ).fetchall()
        return [dict(r) for r in rows]


@router.post("/meetings")
def create_meeting(data: MeetingCreate) -> dict:
    """Create a meeting from JSON (text transcript)."""
    meeting_id = str(uuid.uuid4())
    date = datetime.now(UTC).isoformat()
    save_meeting_metadata(
        meeting_id=meeting_id,
        title=data.title,
        meeting_type=data.meeting_type,
        date=date,
        participants=data.participants,
        transcript_path=None,
        audio_path=None,
    )
    # If transcript provided, save it as a sidecar file
    if data.transcript:
        dest = UPLOAD_DIR / f"{meeting_id}.txt"
        with open(dest, "w", encoding="utf-8") as f:
            f.write(data.transcript)
        with _db() as conn:
            conn.execute("UPDATE meetings SET transcript_path = ? WHERE id = ?", (str(dest), meeting_id))
            conn.commit()
    return {"meeting_id": meeting_id, "title": data.title, "status": "created"}


@router.post("/meetings/upload")
async def upload_meeting(
    title: str = Form(...),
    meeting_type: str = Form("team"),
    participants: str = Form(""),
    file: UploadFile | None = File(None),
    current_user: dict | None = Depends(get_current_user),
) -> dict:
    """Upload audio or txt meeting file."""
    meeting_id = str(uuid.uuid4())
    date = datetime.now(UTC).isoformat()
    participant_list = [p.strip() for p in participants.split(",") if p.strip()]

    audio_path = None
    transcript_path = None

    if file:
        ext = Path(file.filename).suffix.lower()
        dest = UPLOAD_DIR / f"{meeting_id}{ext}"
        with open(dest, "wb") as f:
            shutil.copyfileobj(file.file, f)

        if ext == ".txt":
            transcript_path = str(dest)
        else:
            audio_path = str(dest)

    save_meeting_metadata(
        meeting_id=meeting_id,
        title=title,
        meeting_type=meeting_type,
        date=date,
        participants=participant_list,
        transcript_path=transcript_path,
        audio_path=audio_path,
    )

    uploader_id = current_user["id"] if current_user else None
    if uploader_id:
        with _db() as conn:
            conn.execute("UPDATE meetings SET created_by = ? WHERE id = ?", (uploader_id, meeting_id))
            conn.commit()

    # Auto-process the meeting immediately after upload
    try:
        process_meeting(meeting_id)
    except Exception:
        pass

    return {
        "meeting_id": meeting_id,
        "title": title,
        "status": "uploaded",
        "audio_path": audio_path,
        "transcript_path": transcript_path,
    }


@router.post("/meetings/{meeting_id}/process")
def process_meeting(meeting_id: str) -> MeetingProcessResponse:
    """Transcribe, extract, route and store meeting chunks."""
    with _db() as conn:
        row = conn.execute("SELECT * FROM meetings WHERE id = ?", (meeting_id,)).fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Meeting not found")
        meeting = dict(row)

    # 1. Transcription
    audio_path = meeting.get("audio_path")
    transcript_path = meeting.get("transcript_path")
    transcript = ""

    if transcript_path and os.path.exists(transcript_path):
        with open(transcript_path, encoding="utf-8") as f:
            transcript = f.read()
    elif audio_path and os.path.exists(audio_path):
        result = transcribe_audio_file(audio_path)
        transcript = result.get("transcript", "")
    else:
        transcript = meeting.get("transcript", "") or ""

    # 2. Extraction via Gemini
    from google import genai

    use_vertex = os.getenv("GOOGLE_GENAI_USE_VERTEXAI", "False").lower() == "true"
    if use_vertex:
        client = genai.Client(
            vertexai=True,
            project=os.getenv("GOOGLE_CLOUD_PROJECT"),
            location=os.getenv("GOOGLE_CLOUD_LOCATION", "us-central1"),
        )
    else:
        api_key = os.getenv("GOOGLE_API_KEY")
        if not api_key:
            raise HTTPException(status_code=500, detail="No GOOGLE_API_KEY configured")
        client = genai.Client(api_key=api_key)

    prompt = f"""Przeanalizuj transkrypcję spotkania. Wyciągnij:
1. Decyzje (decisions)
2. Zadania (action_items) — kto, co, do kiedy
3. Notatki (notes)

Zwróć JSON:
{{
  "decisions": ["..."],
  "action_items": [{{"task": "...", "assignee": "...", "due_date": "..."}}],
  "notes": ["..."]
}}

Transkrypcja:
{transcript}
"""
    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=prompt,
    )
    extracted_text = response.text or "{}"
    # Strip markdown code block if present
    extracted_text = extracted_text.strip().removeprefix("```json").removeprefix("```").removesuffix("```").strip()
    try:
        extracted = json.loads(extracted_text)
    except json.JSONDecodeError:
        extracted = {"decisions": [], "action_items": [], "notes": [], "raw": extracted_text}

    # 3. Routing (based on meeting_type)
    mt = meeting.get("meeting_type", "team").lower()
    company_id = "webwave"
    participants = json.loads(meeting.get("participants", "[]"))
    created_by = meeting.get("created_by")
    destinations = []

    if mt == "private":
        if created_by:
            destinations.append({"bank_id": f"private_{created_by}", "status": "approved"})
        for p in participants:
            if p != created_by:
                destinations.append({"bank_id": f"private_{p}", "status": "approved"})
    elif mt == "team":
        destinations.append({"bank_id": f"team_product_{company_id}", "status": "pending_approval"})
        for p in participants:
            destinations.append({"bank_id": f"private_{p}", "status": "approved"})
        if created_by and created_by not in participants:
            destinations.append({"bank_id": f"private_{created_by}", "status": "approved"})
    elif mt == "company":
        destinations.append({"bank_id": f"company_{company_id}", "status": "pending_approval"})
        for p in participants:
            destinations.append({"bank_id": f"private_{p}", "status": "approved"})
        if created_by and created_by not in participants:
            destinations.append({"bank_id": f"private_{created_by}", "status": "approved"})
    elif mt == "cross":
        destinations.append({"bank_id": f"company_{company_id}", "status": "pending_approval"})
        destinations.append({"bank_id": f"team_product_{company_id}", "status": "pending_approval"})
        for p in participants:
            destinations.append({"bank_id": f"private_{p}", "status": "approved"})
    elif mt == "oneonone":
        for p in participants:
            destinations.append({"bank_id": f"private_{p}", "status": "approved"})
        if created_by and created_by not in participants:
            destinations.append({"bank_id": f"private_{created_by}", "status": "approved"})
    elif mt == "allhands":
        destinations.append({"bank_id": "group", "status": "pending_approval"})
        destinations.append({"bank_id": f"company_{company_id}", "status": "pending_approval"})
        for p in participants:
            destinations.append({"bank_id": f"private_{p}", "status": "approved"})

    # 4. Store chunks in Qdrant
    all_chunks = []
    for decision in extracted.get("decisions", []):
        all_chunks.append({"type": "decision", "text": decision})
    for note in extracted.get("notes", []):
        all_chunks.append({"type": "note", "text": note})
    for item in extracted.get("action_items", []):
        text = item.get("task", "")
        if item.get("assignee"):
            text += f" (przypisane do: {item['assignee']}"
            if item.get("due_date"):
                text += f", do: {item['due_date']}"
            text += ")"
        all_chunks.append({"type": "action_item", "text": text})

    for _i, chunk in enumerate(all_chunks):
        for dest in destinations:
            bank_id = dest["bank_id"]
            chunk_id = str(uuid.uuid4())
            upsert_chunk(
                bank_id=bank_id,
                chunk_id=chunk_id,
                chunk_text=chunk["text"],
                payload={
                    "meeting_id": meeting_id,
                    "meeting_title": meeting.get("title", ""),
                    "meeting_date": meeting.get("date", ""),
                    "meeting_type": mt,
                    "chunk_type": chunk["type"],
                    "status": dest["status"],
                },
            )

    return MeetingProcessResponse(
        meeting_id=meeting_id,
        transcript=transcript,
        extracted=extracted,
        destinations=destinations,
        status="processed",
    )


# ── Users & ACL ──────────────────────────────────────────────────────

@router.get("/users")
def list_users(current_user: dict | None = Depends(get_current_user)) -> list[dict]:
    """List all users. Requires authentication."""
    if not current_user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    with _db() as conn:
        rows = conn.execute(
            "SELECT id, name, role, team, company, email, created_at FROM users ORDER BY created_at DESC"
        ).fetchall()
        return [dict(r) for r in rows]


@router.post("/users")
def create_user(data: UserCreate) -> dict:
    """Create a new user with default ACLs."""
    password_hash = get_password_hash(data.password) if data.password else None
    ensure_user(
        user_id=data.user_id,
        name=data.name,
        role=data.role,
        team=data.team,
        company=data.company,
        email=data.email,
        password_hash=password_hash,
    )
    return {"status": "created", "user_id": data.user_id}


@router.get("/users/{user_id}/acl")
def user_acl(user_id: str) -> list[dict]:
    """Get user ACL."""
    return get_user_acl(user_id)


@router.post("/users/{user_id}/acl")
def update_user_acl(
    user_id: str,
    data: UserACLUpdate,
    admin: dict = Depends(require_admin),
) -> dict:
    """Update or add ACL entry for user."""
    with _db() as conn:
        conn.execute(
            "INSERT OR REPLACE INTO user_acl (user_id, bank_id, role) VALUES (?, ?, ?)",
            (user_id, data.bank_id, data.role),
        )
        conn.commit()
    return {"status": "updated", "user_id": user_id, "bank_id": data.bank_id, "role": data.role}


# ── Inbox ────────────────────────────────────────────────────────────

@router.get("/inbox")
def inbox_items(current_user: dict | None = Depends(get_current_user)) -> list[dict]:
    """List inbox items for the authenticated user.

    Returns:
        - items where the user is the recipient (user_id == me), and
        - pending note proposals targeting any bank where the user is Editor+.
    Each item has `is_mine` and `can_approve` flags for the frontend.
    """
    if not current_user:
        raise HTTPException(status_code=401, detail="Not authenticated")

    user_id = current_user["id"]
    acl = get_user_acl(user_id)
    approver_banks = {a["bank_id"] for a in acl if a["role"] in APPROVER_ROLES}

    by_id: dict[str, dict] = {}
    for item in get_inbox_items(user_id):
        item["is_mine"] = True
        item["can_approve"] = (
            item.get("status") == "pending_approval"
            and item.get("bank_id") in approver_banks
            and item.get("proposed_by") != user_id
        )
        by_id[item["id"]] = item

    if approver_banks:
        placeholders = ",".join("?" for _ in approver_banks)
        with _db() as conn:
            rows = conn.execute(
                f"""
                SELECT * FROM inbox
                WHERE item_type = 'note'
                  AND status = 'pending_approval'
                  AND bank_id IN ({placeholders})
                ORDER BY created_at DESC
                """,
                list(approver_banks),
            ).fetchall()
        for row in rows:
            item = dict(row)
            if item["id"] in by_id:
                continue
            item["is_mine"] = item.get("proposed_by") == user_id
            item["can_approve"] = item.get("proposed_by") != user_id
            by_id[item["id"]] = item

    items = list(by_id.values())
    items.sort(key=lambda i: i.get("created_at") or "", reverse=True)
    return items


# ── Chat (RAG) ───────────────────────────────────────────────────────

@router.post("/chat")
def chat(req: ChatRequest) -> ChatResponse:
    """Chat with organizational memory (RAG)."""
    banks = req.permitted_banks or ["group", "company_webwave", "team_product_webwave"]
    chunks = retrieve_chunks(req.query, banks, top_k=5)

    context_parts = []
    sources = []
    for c in chunks:
        payload = c.get("payload", {})
        text = payload.get("chunk_text", "")
        context_parts.append(text)
        sources.append(
            {
                "bank_id": c["bank_id"],
                "score": c["score"],
                "meeting_title": payload.get("meeting_title", "?"),
                "meeting_date": payload.get("meeting_date", "?"),
            }
        )

    if not context_parts:
        return ChatResponse(
            answer="Nie znalazłem żadnych informacji w pamięci organizacyjnej na ten temat.",
            sources=[],
        )

    from google import genai

    use_vertex = os.getenv("GOOGLE_GENAI_USE_VERTEXAI", "False").lower() == "true"
    if use_vertex:
        client = genai.Client(
            vertexai=True,
            project=os.getenv("GOOGLE_CLOUD_PROJECT"),
            location=os.getenv("GOOGLE_CLOUD_LOCATION", "us-central1"),
        )
    else:
        api_key = os.getenv("GOOGLE_API_KEY")
        if not api_key:
            raise HTTPException(status_code=500, detail="No GOOGLE_API_KEY configured")
        client = genai.Client(api_key=api_key)

    context = "\n- ".join(context_parts)
    prompt = f"""Odpowiedz na pytanie użytkownika na podstawie poniższego kontekstu z spotkań.

Kontekst:
- {context}

Pytanie: {req.query}

Odpowiedz po polsku, zwięźle i konkretnie. Jeśli kontekst nie zawiera odpowiedzi, powiedz o tym wprost.
"""
    try:
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt,
        )
        answer = response.text or ""
    except Exception as exc:
        raise HTTPException(status_code=503, detail=f"LLM API error: {exc}")
    return ChatResponse(answer=answer, sources=sources)


# ── Admin stats ──────────────────────────────────────────────────────

@router.get("/admin/stats")
def admin_stats(current_user: dict | None = Depends(get_current_user)) -> dict:
    """Dashboard statistics."""
    with _db() as conn:
        users = conn.execute("SELECT COUNT(*) as count FROM users").fetchone()["count"]
        meetings = conn.execute("SELECT COUNT(*) as count FROM meetings").fetchone()["count"]
        inbox_pending = conn.execute(
            "SELECT COUNT(*) as count FROM inbox WHERE status = 'pending_approval'"
        ).fetchone()["count"]
        inbox_total = conn.execute("SELECT COUNT(*) as count FROM inbox").fetchone()["count"]
    return {
        "users": users,
        "meetings": meetings,
        "inbox_pending": inbox_pending,
        "inbox_total": inbox_total,
    }


# ── Spaces ───────────────────────────────────────────────────────────

@router.get("/spaces")
def list_all_spaces(current_user: dict | None = Depends(get_current_user)) -> list[dict]:
    """List all spaces."""
    if not current_user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    return list_spaces()


@router.post("/spaces")
def create_new_space(
    data: SpaceCreate,
    current_user: dict | None = Depends(get_current_user),
) -> dict:
    """Create a new space."""
    if not current_user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    return create_space(
        space_id=data.space_id,
        name=data.name,
        bank_id=data.bank_id,
        space_type=data.space_type,
        description=data.description,
        company=data.company,
    )


@router.delete("/spaces/{space_id}")
def remove_space(
    space_id: str,
    current_user: dict | None = Depends(get_current_user),
) -> dict:
    """Delete a space."""
    if not current_user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    return delete_space(space_id)


# ── My Spaces ────────────────────────────────────────────────────────

@router.get("/my/spaces")
def my_spaces(current_user: dict | None = Depends(get_current_user)) -> list[dict]:
    """Return spaces the current user has ACL access to."""
    if not current_user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    user_id = current_user["id"]
    with _db() as conn:
        # ensure private space exists for existing users created before this fix
        private_bank_id = f"private_{user_id}"
        conn.execute(
            """
            INSERT OR IGNORE INTO spaces (id, name, bank_id, space_type, description, company)
            VALUES (?, 'Prywatne', ?, 'private', '', 'webwave')
            """,
            (private_bank_id, private_bank_id),
        )
        conn.execute(
            "INSERT OR IGNORE INTO user_acl (user_id, bank_id, role) VALUES (?, ?, 'admin')",
            (user_id, private_bank_id),
        )
        # sync ACLs based on users.team / users.company for users created via admin panel
        user_row = conn.execute(
            "SELECT team, company FROM users WHERE id = ?", (user_id,)
        ).fetchone()
        if user_row:
            team_val, company_val = user_row["team"] or "", user_row["company"] or ""
            # resolve bank_ids (support both raw names and full bank_ids)
            company_bank = company_val if company_val.startswith("company_") else f"company_{company_val}" if company_val else ""
            team_bank = team_val if team_val.startswith("team_") else f"team_{team_val}" if team_val else ""
            for bank_id in [company_bank, team_bank]:
                if bank_id:
                    space = conn.execute(
                        "SELECT 1 FROM spaces WHERE bank_id = ?", (bank_id,)
                    ).fetchone()
                    if space:
                        conn.execute(
                            "INSERT OR IGNORE INTO user_acl (user_id, bank_id, role) VALUES (?, ?, 'member')",
                            (user_id, bank_id),
                        )
        conn.commit()
        rows = conn.execute(
            """
            SELECT s.id, s.name, s.bank_id, s.space_type, a.role
            FROM spaces s
            JOIN user_acl a ON s.bank_id = a.bank_id
            WHERE a.user_id = ?
            ORDER BY s.created_at DESC
            """,
            (user_id,),
        ).fetchall()
        return [dict(r) for r in rows]


@router.get("/my/spaces/{bank_id}/notes")
def list_notes(
    bank_id: str,
    current_user: dict | None = Depends(get_current_user),
) -> list[dict]:
    """List notes in a space from Qdrant."""
    if not current_user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    # Validate bank_id against user's ACL
    acl = get_user_acl(current_user["id"])
    permitted_banks = {a["bank_id"] for a in acl}
    if bank_id not in permitted_banks:
        raise HTTPException(status_code=403, detail="Access denied to this space")
    client = QdrantClient(url=QDRANT_URL)
    try:
        from qdrant_client.models import FieldCondition, Filter, MatchValue

        filter_cond = Filter(
            should=[
                FieldCondition(key="chunk_type", match=MatchValue(value="note")),
                FieldCondition(key="type", match=MatchValue(value="note")),
            ]
        )
        results: list[dict] = []
        offset = None
        while True:
            points, next_offset = client.scroll(
                collection_name=bank_id,
                scroll_filter=filter_cond,
                limit=100,
                offset=offset,
                with_payload=True,
            )
            for p in points:
                payload = p.payload or {}
                results.append(
                    {
                        "chunk_id": p.id,
                        "text": payload.get("chunk_text", ""),
                        "payload": payload,
                        "created_at": payload.get("created_at"),
                    }
                )
            offset = next_offset
            if offset is None:
                break
        return results
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@router.post("/my/spaces/{bank_id}/notes")
def create_note(
    bank_id: str,
    data: NoteCreate,
    current_user: dict | None = Depends(get_current_user),
) -> dict:
    """Create a note in a space.

    - Editor / Manager / Admin → publish directly to the target bank.
    - Member → save a copy to private bank and queue an inbox proposal
      that any Editor+ in the target bank can approve.
    - No ACL → 403.
    """
    if not current_user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    acl = get_user_acl(current_user["id"])
    role_in_bank = next((a["role"] for a in acl if a["bank_id"] == bank_id), None)
    if role_in_bank is None:
        raise HTTPException(status_code=403, detail="Access denied to this space")

    created_at = datetime.now(UTC).isoformat()
    chunk_text = f"{data.title}\n\n{data.content}"

    if role_in_bank in APPROVER_ROLES:
        chunk_id = str(uuid.uuid4())
        upsert_chunk(
            bank_id=bank_id,
            chunk_id=chunk_id,
            chunk_text=chunk_text,
            payload={
                "type": "note",
                "user_id": current_user["id"],
                "title": data.title,
                "created_at": created_at,
            },
        )
        return {"status": "created", "mode": "direct", "chunk_id": chunk_id}

    # Member path → private copy + proposal in inbox.
    private_bank = f"private_{current_user['id']}"
    private_chunk_id = str(uuid.uuid4())
    upsert_chunk(
        bank_id=private_bank,
        chunk_id=private_chunk_id,
        chunk_text=chunk_text,
        payload={
            "type": "note",
            "user_id": current_user["id"],
            "title": data.title,
            "created_at": created_at,
            "proposal_for_bank": bank_id,
            "proposal_status": "pending_approval",
        },
    )
    inbox_id = create_inbox_item(
        user_id=current_user["id"],
        item_type="note",
        content=json.dumps({"title": data.title, "content": data.content}),
        bank_id=bank_id,
        proposed_by=current_user["id"],
    )
    return {
        "status": "pending_approval",
        "mode": "proposal",
        "inbox_id": inbox_id,
        "private_chunk_id": private_chunk_id,
    }


@router.delete("/my/spaces/{bank_id}/notes/{chunk_id}")
def delete_note(
    bank_id: str,
    chunk_id: str,
    current_user: dict | None = Depends(get_current_user),
) -> dict:
    """Delete a note from a space. Owner can delete from their private space; Editor+ can delete from any space they manage."""
    if not current_user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    acl = get_user_acl(current_user["id"])
    role_in_bank = next((a["role"] for a in acl if a["bank_id"] == bank_id), None)
    if role_in_bank is None:
        raise HTTPException(status_code=403, detail="Access denied to this space")
    private_bank = f"private_{current_user['id']}"
    if bank_id != private_bank and role_in_bank not in APPROVER_ROLES:
        raise HTTPException(status_code=403, detail="Only editors and above can delete notes from shared spaces")
    client = QdrantClient(url=QDRANT_URL)
    try:
        from qdrant_client.models import PointIdsList
        client.delete(collection_name=bank_id, points_selector=PointIdsList(points=[chunk_id]))
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))
    return {"status": "deleted", "chunk_id": chunk_id}


# ── Search ───────────────────────────────────────────────────────────

@router.get("/search")
def search(
    q: str = Query(..., description="Search query"),
    current_user: dict | None = Depends(get_current_user),
) -> list[dict]:
    """Search across all banks the user has ACL access to."""
    if not current_user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    acl = get_user_acl(current_user["id"])
    permitted_banks = [a["bank_id"] for a in acl]
    if not permitted_banks:
        return []
    return retrieve_chunks(q, permitted_banks, top_k=20)


# ── Inbox Actions ────────────────────────────────────────────────────

@router.post("/inbox/{item_id}/approve")
def approve_inbox(
    item_id: str,
    data: InboxApprove,
    current_user: dict | None = Depends(get_current_user),
) -> dict:
    """Approve an inbox item with optional export action.

    For note proposals: requires Editor+ in the target bank, publishes the note
    to that bank, and marks the proposer's private copy as approved.
    """
    if not current_user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    with _db() as conn:
        row = conn.execute("SELECT * FROM inbox WHERE id = ?", (item_id,)).fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Item not found")
        item = dict(row)

        if item.get("item_type") == "note":
            target_bank = item.get("bank_id")
            if not target_bank:
                raise HTTPException(status_code=400, detail="Note proposal missing bank_id")
            acl = get_user_acl(current_user["id"])
            role_in_bank = next((a["role"] for a in acl if a["bank_id"] == target_bank), None)
            if role_in_bank not in APPROVER_ROLES:
                raise HTTPException(status_code=403, detail="Editor+ required to approve")
            if item.get("status") != "pending_approval":
                raise HTTPException(status_code=409, detail=f"Already {item.get('status')}")

            try:
                payload = json.loads(item.get("content") or "{}")
            except json.JSONDecodeError:
                payload = {}
            title = payload.get("title", "")
            content = payload.get("content", item.get("content", ""))
            chunk_text = f"{title}\n\n{content}".strip()
            chunk_id = str(uuid.uuid4())
            created_at = datetime.now(UTC).isoformat()
            upsert_chunk(
                bank_id=target_bank,
                chunk_id=chunk_id,
                chunk_text=chunk_text,
                payload={
                    "type": "note",
                    "user_id": item.get("proposed_by"),
                    "title": title,
                    "created_at": created_at,
                    "approved_by": current_user["id"],
                    "from_inbox_id": item_id,
                },
            )
            conn.execute(
                "UPDATE inbox SET status = ?, approved_by = ?, approved_at = ? WHERE id = ?",
                ("approved", current_user["id"], created_at, item_id),
            )
            conn.execute(
                "INSERT INTO audit_log (event_type, user_id, item_id, to_bank, details) VALUES (?, ?, ?, ?, ?)",
                (
                    "approve_note_proposal",
                    current_user["id"],
                    item_id,
                    target_bank,
                    json.dumps(
                        {
                            "proposed_by": item.get("proposed_by"),
                            "chunk_id": chunk_id,
                        }
                    ),
                ),
            )
            conn.commit()

            # Reflect approval on the proposer's private copy if it exists.
            try:
                _mark_proposal_in_private(item.get("proposed_by"), target_bank, "approved")
            except Exception as exc:
                print(f"[WARN] Could not update private copy: {exc}")

            return {
                "status": "approved",
                "item_id": item_id,
                "chunk_id": chunk_id,
                "bank_id": target_bank,
            }

        # Non-note items keep the legacy behaviour.
        status = "approved"
        if data.action == "clickup":
            content = item.get("content", "")
            try:
                parsed = json.loads(content) if content.startswith("{") else {}
            except json.JSONDecodeError:
                parsed = {}
            name = parsed.get("description", content) or "Inbox item"
            assignee = parsed.get("assignee", "nieprzypisane")
            due_date = parsed.get("due_date")
            description = f"Wygenerowane przez WenetBrain: {content}"
            create_clickup_task(name, assignee, due_date, description)
            status = "approved_clickup"
        elif data.action == "outlook":
            status = "approved_outlook"
        else:
            status = "approved"
        conn.execute(
            "UPDATE inbox SET status = ?, approved_by = ?, approved_at = ? WHERE id = ?",
            (status, current_user["id"], datetime.now(UTC).isoformat(), item_id),
        )
        conn.commit()
    return {"status": status, "item_id": item_id}


@router.post("/inbox/{item_id}/reject")
def reject_inbox(
    item_id: str,
    current_user: dict | None = Depends(get_current_user),
) -> dict:
    """Reject an inbox item.

    Note proposals can be rejected by an Editor+ in the target bank
    or by the original proposer (cancel-my-own-proposal).
    """
    if not current_user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    with _db() as conn:
        row = conn.execute("SELECT * FROM inbox WHERE id = ?", (item_id,)).fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Item not found")
        item = dict(row)

        if item.get("item_type") == "note":
            target_bank = item.get("bank_id")
            acl = get_user_acl(current_user["id"])
            role_in_bank = next((a["role"] for a in acl if a["bank_id"] == target_bank), None)
            is_proposer = item.get("proposed_by") == current_user["id"]
            if not is_proposer and role_in_bank not in APPROVER_ROLES:
                raise HTTPException(status_code=403, detail="Editor+ or proposer required to reject")
            try:
                _mark_proposal_in_private(item.get("proposed_by"), target_bank, "rejected")
            except Exception as exc:
                print(f"[WARN] Could not update private copy: {exc}")

        conn.execute(
            "UPDATE inbox SET status = 'rejected', approved_by = ? WHERE id = ?",
            (current_user["id"], item_id),
        )
        conn.commit()
    return {"status": "rejected", "item_id": item_id}


def _mark_proposal_in_private(
    proposer_id: str | None,
    target_bank: str | None,
    new_status: str,
) -> None:
    """Update the proposer's private-bank copy to reflect approval/rejection."""
    if not proposer_id or not target_bank:
        return
    private_bank = f"private_{proposer_id}"
    client = QdrantClient(url=QDRANT_URL)
    if not client.collection_exists(private_bank):
        return
    from qdrant_client.models import FieldCondition, Filter, MatchValue

    flt = Filter(
        must=[
            FieldCondition(key="proposal_for_bank", match=MatchValue(value=target_bank)),
            FieldCondition(key="proposal_status", match=MatchValue(value="pending_approval")),
        ]
    )
    points, _ = client.scroll(
        collection_name=private_bank,
        scroll_filter=flt,
        limit=50,
        with_payload=True,
    )
    for p in points:
        client.set_payload(
            collection_name=private_bank,
            payload={"proposal_status": new_status},
            points=[p.id],
        )


# ── Settings ─────────────────────────────────────────────────────────

@router.get("/settings")
def get_settings(current_user: dict | None = Depends(get_current_user)) -> dict:
    """Return current user settings."""
    if not current_user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    user_id = current_user["id"]
    with _db() as conn:
        cursor = conn.execute("PRAGMA table_info(users)")
        columns = {c["name"] for c in cursor.fetchall()}
        allowed_cols = {"id", "name", "email", "role", "clickup_list_id", "outlook_connected"}
        select_cols = [c for c in allowed_cols if c in columns]
        row = conn.execute(
            f"SELECT {', '.join(select_cols)} FROM users WHERE id = ?",
            (user_id,),
        ).fetchone()
        user = dict(row) if row else {}
    return {
        "user_id": user.get("id"),
        "name": user.get("name"),
        "email": user.get("email"),
        "role": user.get("role"),
        "clickup_list_id": user.get("clickup_list_id"),
        "outlook_connected": user.get("outlook_connected", False),
    }


@router.patch("/settings")
def update_settings(
    data: SettingsUpdate,
    current_user: dict | None = Depends(get_current_user),
) -> dict:
    """Update current user settings."""
    if not current_user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    user_id = current_user["id"]
    updates: dict[str, Any] = {}
    if data.name is not None:
        updates["name"] = data.name
    if data.email is not None:
        updates["email"] = data.email
    if data.clickup_list_id is not None:
        updates["clickup_list_id"] = data.clickup_list_id
    if data.outlook_connected is not None:
        updates["outlook_connected"] = data.outlook_connected
    if not updates:
        raise HTTPException(status_code=400, detail="No fields to update")
    with _db() as conn:
        cursor = conn.execute("PRAGMA table_info(users)")
        columns = {c["name"] for c in cursor.fetchall()}
        allowed_cols = {"name", "email", "role", "clickup_list_id", "outlook_connected"}
        valid_updates = {k: v for k, v in updates.items() if k in columns and k in allowed_cols}
        if valid_updates:
            set_clause = ", ".join(f"{k} = ?" for k in valid_updates)
            values = list(valid_updates.values()) + [user_id]
            conn.execute(f"UPDATE users SET {set_clause} WHERE id = ?", values)
            conn.commit()
    return {"status": "updated", "user_id": user_id}


# ── Integrations ─────────────────────────────────────────────────────

@router.get("/integrations/clickup/lists")
def clickup_lists(current_user: dict | None = Depends(get_current_user)) -> list[dict]:
    """Mock: return available ClickUp lists."""
    if not current_user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    return [{"id": "123", "name": "Personal List"}]


@router.post("/integrations/outlook/events")
def create_outlook_event(
    data: OutlookEventCreate,
    current_user: dict | None = Depends(get_current_user),
) -> dict:
    """Mock: create an Outlook event."""
    if not current_user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    event_id = "mock-" + str(uuid.uuid4())
    return {"status": "created", "event_id": event_id}
