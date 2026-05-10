"""Admin API routes for user, space and ACL management."""

from datetime import UTC

from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pydantic import BaseModel

from app.tools import (
    QDRANT_URL,
    _db,
    authenticate_user,
    create_access_token,
    create_space,
    decode_access_token,
    delete_space,
    get_password_hash,
    get_user_by_id,
    list_spaces,
    update_space,
    upsert_chunk,
)

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

class LoginResponse(BaseModel):
    access_token: str
    token_type: str
    user: dict


class UserCreate(BaseModel):
    user_id: str
    name: str
    role: str = "member"
    team: str = ""
    company: str = "webwave"
    email: str = ""
    password: str = ""


class UserUpdate(BaseModel):
    name: str | None = None
    role: str | None = None
    team: str | None = None
    company: str | None = None
    email: str | None = None
    password: str | None = None


class SpaceCreate(BaseModel):
    space_id: str
    name: str
    bank_id: str
    space_type: str = "team"
    description: str = ""
    company: str = "webwave"
    parent_id: str | None = None


class SpaceUpdate(BaseModel):
    name: str | None = None
    bank_id: str | None = None
    description: str | None = None


class ACLUpdate(BaseModel):
    user_id: str
    bank_id: str
    role: str


class AdminNoteCreate(BaseModel):
    title: str
    content: str


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
def me(current_user: dict = Depends(require_admin)) -> dict:
    """Get current authenticated admin user."""
    return current_user


# ── Users ────────────────────────────────────────────────────────────

@router.get("/users")
def list_users(admin: dict = Depends(require_admin)) -> list[dict]:
    """List all users."""
    with _db() as conn:
        rows = conn.execute(
            "SELECT id, name, role, team, company, email, created_at FROM users ORDER BY created_at DESC"
        ).fetchall()
        return [dict(r) for r in rows]


@router.post("/users")
def create_new_user(data: UserCreate, admin: dict = Depends(require_admin)) -> dict:
    """Create a new user with optional password."""
    password_hash = get_password_hash(data.password) if data.password else None
    with _db() as conn:
        conn.execute(
            """
            INSERT OR IGNORE INTO users (id, name, role, team, company, email, password_hash)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (data.user_id, data.name, data.role, data.team, data.company, data.email, password_hash),
        )
        # default ACLs — team/company bank_ids passed directly as bank_ids
        defaults = [
            ("group", "member"),
            ("weall", "member"),
            (f"private_{data.user_id}", "admin"),
        ]
        # data.team and data.company are already bank_ids when sent from SpacesView
        if data.team:
            defaults.append((data.team, data.role or "member"))
        if data.company:
            defaults.append((data.company, "member"))
        for bank, r in defaults:
            conn.execute(
                "INSERT OR IGNORE INTO user_acl (user_id, bank_id, role) VALUES (?, ?, ?)",
                (data.user_id, bank, r),
            )
        conn.commit()
    return {"status": "created", "user_id": data.user_id}


@router.get("/users/{user_id}")
def get_user(user_id: str, admin: dict = Depends(require_admin)) -> dict:
    """Get user details."""
    with _db() as conn:
        row = conn.execute(
            "SELECT id, name, role, team, company, email, created_at FROM users WHERE id = ?",
            (user_id,),
        ).fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="User not found")
        return dict(row)


@router.patch("/users/{user_id}")
def update_user(user_id: str, data: UserUpdate, admin: dict = Depends(require_admin)) -> dict:
    """Update user fields."""
    fields = []
    values = []
    if data.name is not None:
        fields.append("name = ?")
        values.append(data.name)
    if data.role is not None:
        fields.append("role = ?")
        values.append(data.role)
    if data.team is not None:
        fields.append("team = ?")
        values.append(data.team)
    if data.company is not None:
        fields.append("company = ?")
        values.append(data.company)
    if data.email is not None:
        fields.append("email = ?")
        values.append(data.email)
    if data.password is not None:
        fields.append("password_hash = ?")
        values.append(get_password_hash(data.password))
    if not fields:
        return {"status": "no_change", "user_id": user_id}
    values.append(user_id)
    with _db() as conn:
        conn.execute(f"UPDATE users SET {', '.join(fields)} WHERE id = ?", values)
        conn.commit()
    return {"status": "updated", "user_id": user_id}


@router.delete("/users/{user_id}")
def remove_user(user_id: str, admin: dict = Depends(require_admin)) -> dict:
    """Delete a user and their ACLs."""
    with _db() as conn:
        conn.execute("DELETE FROM user_acl WHERE user_id = ?", (user_id,))
        conn.execute("DELETE FROM users WHERE id = ?", (user_id,))
        conn.commit()
    return {"status": "deleted", "user_id": user_id}


@router.get("/users/{user_id}/acl")
def user_acl(user_id: str, admin: dict = Depends(require_admin)) -> list[dict]:
    """Get user ACL."""
    with _db() as conn:
        rows = conn.execute(
            "SELECT bank_id, role FROM user_acl WHERE user_id = ?", (user_id,)
        ).fetchall()
        return [dict(r) for r in rows]


@router.post("/users/{user_id}/acl")
def update_user_acl(user_id: str, data: ACLUpdate, admin: dict = Depends(require_admin)) -> dict:
    """Update or add ACL entry for user."""
    with _db() as conn:
        conn.execute(
            "INSERT OR REPLACE INTO user_acl (user_id, bank_id, role) VALUES (?, ?, ?)",
            (user_id, data.bank_id, data.role),
        )
        conn.commit()
    return {"status": "updated", "user_id": user_id, "bank_id": data.bank_id, "role": data.role}


@router.delete("/users/{user_id}/acl/{bank_id}")
def delete_user_acl(user_id: str, bank_id: str, admin: dict = Depends(require_admin)) -> dict:
    """Remove ACL entry for user."""
    with _db() as conn:
        conn.execute(
            "DELETE FROM user_acl WHERE user_id = ? AND bank_id = ?",
            (user_id, bank_id),
        )
        conn.commit()
    return {"status": "deleted", "user_id": user_id, "bank_id": bank_id}


# ── Spaces ───────────────────────────────────────────────────────────

@router.get("/spaces")
def list_all_spaces(admin: dict = Depends(require_admin)) -> list[dict]:
    """List all spaces as a flat list with parent_id."""
    return list_spaces()


@router.post("/spaces")
def create_new_space(data: SpaceCreate, admin: dict = Depends(require_admin)) -> dict:
    """Create a new space."""
    return create_space(
        space_id=data.space_id,
        name=data.name,
        bank_id=data.bank_id,
        space_type=data.space_type,
        description=data.description,
        company=data.company,
        parent_id=data.parent_id,
    )


@router.patch("/spaces/{space_id}")
def update_existing_space(space_id: str, data: SpaceUpdate, admin: dict = Depends(require_admin)) -> dict:
    """Update a space."""
    return update_space(
        space_id=space_id,
        name=data.name,
        bank_id=data.bank_id,
        description=data.description,
    )


@router.delete("/spaces/{space_id}")
def remove_space(space_id: str, admin: dict = Depends(require_admin)) -> dict:
    """Delete a space."""
    return delete_space(space_id)


@router.get("/spaces/{bank_id}/users")
def space_users(bank_id: str, admin: dict = Depends(require_admin)) -> list[dict]:
    """List users with ACL for a given space."""
    with _db() as conn:
        rows = conn.execute(
            """
            SELECT u.id, u.name, u.email, u.role as user_role, a.role as acl_role
            FROM users u
            JOIN user_acl a ON u.id = a.user_id
            WHERE a.bank_id = ?
            ORDER BY u.name
            """,
            (bank_id,),
        ).fetchall()
        return [dict(r) for r in rows]


@router.get("/spaces/{bank_id}/notes")
def space_notes(bank_id: str, admin: dict = Depends(require_admin)) -> list[dict]:
    """List notes in a space from Qdrant."""
    from qdrant_client import QdrantClient
    from qdrant_client.models import FieldCondition, Filter, MatchValue

    client = QdrantClient(url=QDRANT_URL)
    try:
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
                        "title": payload.get("title", ""),
                        "user_id": payload.get("user_id", ""),
                        "created_at": payload.get("created_at"),
                    }
                )
            offset = next_offset
            if offset is None:
                break
        return results
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@router.post("/spaces/{bank_id}/notes")
def create_space_note(bank_id: str, data: AdminNoteCreate, admin: dict = Depends(require_admin)) -> dict:
    """Create a note in a space as admin."""
    import uuid
    from datetime import datetime

    chunk_id = str(uuid.uuid4())
    created_at = datetime.now(UTC).isoformat()
    chunk_text = f"{data.title}\n\n{data.content}"
    upsert_chunk(
        bank_id=bank_id,
        chunk_id=chunk_id,
        chunk_text=chunk_text,
        payload={
            "type": "note",
            "user_id": admin["id"],
            "title": data.title,
            "created_at": created_at,
        },
    )
    return {"status": "created", "chunk_id": chunk_id}


@router.delete("/spaces/{bank_id}/notes/{chunk_id}")
def delete_space_note(bank_id: str, chunk_id: str, admin: dict = Depends(require_admin)) -> dict:
    """Delete a note from a space."""
    from qdrant_client import QdrantClient
    from qdrant_client.models import PointIdsList
    client = QdrantClient(url=QDRANT_URL)
    try:
        client.delete(collection_name=bank_id, points_selector=PointIdsList(points=[chunk_id]))
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))
    return {"status": "deleted", "chunk_id": chunk_id}


# ── Stats ────────────────────────────────────────────────────────────

@router.get("/admin/stats")
def admin_stats(admin: dict = Depends(require_admin)) -> dict:
    """Dashboard statistics."""
    with _db() as conn:
        users = conn.execute("SELECT COUNT(*) as count FROM users").fetchone()["count"]
        meetings = conn.execute("SELECT COUNT(*) as count FROM meetings").fetchone()["count"]
        spaces = conn.execute("SELECT COUNT(*) as count FROM spaces").fetchone()["count"]
        inbox_pending = conn.execute(
            "SELECT COUNT(*) as count FROM inbox WHERE status = 'pending_approval'"
        ).fetchone()["count"]
        inbox_total = conn.execute("SELECT COUNT(*) as count FROM inbox").fetchone()["count"]
    return {
        "users": users,
        "meetings": meetings,
        "spaces": spaces,
        "inbox_pending": inbox_pending,
        "inbox_total": inbox_total,
    }
