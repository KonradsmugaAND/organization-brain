"""End-to-end test for the note-proposal HITL flow.

Member proposes → inbox item is created (pending_approval) and a copy lands
in the proposer's private bank. Editor+ approves → note is published to the
target bank. Member cannot approve someone else's proposal.
"""

from __future__ import annotations

import json
import sqlite3
import sys
import uuid
from pathlib import Path
from typing import Any

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

# Ensure the package is importable when pytest is run from the wenetbrain dir.
ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app import (  # noqa: E402
    api_routes,
    tools,
)
from scripts.init_db import SCHEMA  # noqa: E402

TARGET_BANK = "team_test_proposal"


@pytest.fixture
def db_path(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """Provide a temporary SQLite DB and patch tools.DB_PATH to point at it."""
    p = tmp_path / "test.db"
    conn = sqlite3.connect(p)
    conn.executescript(SCHEMA)
    # The init_db SCHEMA does not include password_hash (added by a later
    # migration in real deployments); add it here so auth works in tests.
    conn.execute("ALTER TABLE users ADD COLUMN password_hash TEXT")
    conn.commit()
    conn.close()
    monkeypatch.setattr(tools, "DB_PATH", str(p))
    return p


@pytest.fixture
def published_chunks() -> list[dict]:
    """In-memory store standing in for Qdrant during tests."""
    return []


@pytest.fixture
def patched_qdrant(
    monkeypatch: pytest.MonkeyPatch,
    published_chunks: list[dict],
) -> None:
    """Replace Qdrant-dependent helpers with in-memory stand-ins."""

    def fake_upsert(bank_id: str, chunk_id: str, chunk_text: str, payload: dict) -> str:
        published_chunks.append(
            {"bank_id": bank_id, "chunk_id": chunk_id, "chunk_text": chunk_text, "payload": payload}
        )
        return "ok"

    def fake_mark(*_args: Any, **_kwargs: Any) -> None:
        return None

    # Patch where the symbols are *used* (api_routes imported them by name).
    monkeypatch.setattr(api_routes, "upsert_chunk", fake_upsert)
    monkeypatch.setattr(api_routes, "_mark_proposal_in_private", fake_mark)


@pytest.fixture
def client(db_path: Path, patched_qdrant: None) -> TestClient:
    """FastAPI TestClient mounting only the API router."""
    app = FastAPI()
    app.include_router(api_routes.router)
    return TestClient(app)


@pytest.fixture
def users(db_path: Path) -> dict[str, dict]:
    """Seed three users + ACLs against TARGET_BANK and return a lookup."""
    member_pw = "member_pw_1"
    manager_pw = "manager_pw_1"
    other_member_pw = "other_member_pw_1"

    members = [
        ("member_1", "Member One", "member", member_pw),
        ("manager_1", "Manager One", "manager", manager_pw),
        ("member_2", "Member Two", "member", other_member_pw),
    ]
    for uid, name, _role, pw in members:
        tools.ensure_user(
            user_id=uid,
            name=name,
            role="member",
            team="test",
            company="webwave",
            email=f"{uid}@example.com",
            password_hash=tools.get_password_hash(pw),
        )

    # ACL on the target bank: member_1 = member, manager_1 = manager, member_2 = member.
    with sqlite3.connect(tools.DB_PATH) as conn:
        for uid, role in (("member_1", "member"), ("manager_1", "manager"), ("member_2", "member")):
            conn.execute(
                "INSERT OR REPLACE INTO user_acl (user_id, bank_id, role) VALUES (?, ?, ?)",
                (uid, TARGET_BANK, role),
            )
        conn.commit()

    return {
        "member_1": {"id": "member_1", "password": member_pw},
        "manager_1": {"id": "manager_1", "password": manager_pw},
        "member_2": {"id": "member_2", "password": other_member_pw},
    }


def _login(client: TestClient, user_id: str, password: str) -> str:
    resp = client.post(
        "/api/auth/login",
        data={"username": user_id, "password": password},
    )
    assert resp.status_code == 200, resp.text
    return resp.json()["access_token"]


def _auth(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def test_member_creates_proposal_not_direct_publish(
    client: TestClient,
    users: dict[str, dict],
    published_chunks: list[dict],
) -> None:
    token = _login(client, users["member_1"]["id"], users["member_1"]["password"])
    resp = client.post(
        f"/api/my/spaces/{TARGET_BANK}/notes",
        json={"title": "Idea X", "content": "let's try X"},
        headers=_auth(token),
    )
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["mode"] == "proposal"
    assert body["status"] == "pending_approval"
    assert "inbox_id" in body

    # The note must NOT have been published to the target bank yet.
    in_target = [c for c in published_chunks if c["bank_id"] == TARGET_BANK]
    assert in_target == []
    # But a private copy should exist with proposal markers.
    private = [c for c in published_chunks if c["bank_id"] == "private_member_1"]
    assert len(private) == 1
    assert private[0]["payload"]["proposal_for_bank"] == TARGET_BANK
    assert private[0]["payload"]["proposal_status"] == "pending_approval"


def test_manager_sees_proposal_in_inbox_and_can_approve(
    client: TestClient,
    users: dict[str, dict],
    published_chunks: list[dict],
) -> None:
    member_token = _login(client, users["member_1"]["id"], users["member_1"]["password"])
    create = client.post(
        f"/api/my/spaces/{TARGET_BANK}/notes",
        json={"title": "T", "content": "C"},
        headers=_auth(member_token),
    )
    inbox_id = create.json()["inbox_id"]

    manager_token = _login(client, users["manager_1"]["id"], users["manager_1"]["password"])
    inbox = client.get("/api/inbox", headers=_auth(manager_token)).json()
    matching = [i for i in inbox if i["id"] == inbox_id]
    assert matching, "Manager should see the pending proposal"
    assert matching[0]["can_approve"] is True
    assert matching[0]["is_mine"] is False

    approve = client.post(
        f"/api/inbox/{inbox_id}/approve",
        json={"action": "none"},
        headers=_auth(manager_token),
    )
    assert approve.status_code == 200, approve.text
    assert approve.json()["status"] == "approved"

    # The note is now published to the target bank.
    published = [c for c in published_chunks if c["bank_id"] == TARGET_BANK]
    assert len(published) == 1
    assert published[0]["payload"]["title"] == "T"
    assert published[0]["payload"]["approved_by"] == "manager_1"


def test_member_cannot_approve_other_proposal(
    client: TestClient,
    users: dict[str, dict],
) -> None:
    proposer = _login(client, users["member_1"]["id"], users["member_1"]["password"])
    create = client.post(
        f"/api/my/spaces/{TARGET_BANK}/notes",
        json={"title": "T2", "content": "C2"},
        headers=_auth(proposer),
    )
    inbox_id = create.json()["inbox_id"]

    intruder = _login(client, users["member_2"]["id"], users["member_2"]["password"])
    resp = client.post(
        f"/api/inbox/{inbox_id}/approve",
        json={"action": "none"},
        headers=_auth(intruder),
    )
    assert resp.status_code == 403


def test_proposer_can_cancel_own_proposal(
    client: TestClient,
    users: dict[str, dict],
) -> None:
    token = _login(client, users["member_1"]["id"], users["member_1"]["password"])
    create = client.post(
        f"/api/my/spaces/{TARGET_BANK}/notes",
        json={"title": "T3", "content": "C3"},
        headers=_auth(token),
    )
    inbox_id = create.json()["inbox_id"]

    resp = client.post(
        f"/api/inbox/{inbox_id}/reject",
        headers=_auth(token),
    )
    assert resp.status_code == 200
    assert resp.json()["status"] == "rejected"


def test_editor_path_publishes_directly(
    client: TestClient,
    users: dict[str, dict],
    published_chunks: list[dict],
    db_path: Path,
) -> None:
    # Promote member_1 to editor in the target bank.
    with sqlite3.connect(tools.DB_PATH) as conn:
        conn.execute(
            "UPDATE user_acl SET role='editor' WHERE user_id=? AND bank_id=?",
            ("member_1", TARGET_BANK),
        )
        conn.commit()

    token = _login(client, users["member_1"]["id"], users["member_1"]["password"])
    resp = client.post(
        f"/api/my/spaces/{TARGET_BANK}/notes",
        json={"title": "Direct", "content": "Editor publishes"},
        headers=_auth(token),
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["mode"] == "direct"
    assert body["status"] == "created"

    published = [c for c in published_chunks if c["bank_id"] == TARGET_BANK]
    assert len(published) == 1


def test_no_acl_returns_403(client: TestClient, users: dict[str, dict]) -> None:
    token = _login(client, users["member_1"]["id"], users["member_1"]["password"])
    resp = client.post(
        "/api/my/spaces/team_unrelated_bank/notes",
        json={"title": "X", "content": "Y"},
        headers=_auth(token),
    )
    assert resp.status_code == 403


def test_inbox_payload_roundtrip_uses_json(
    client: TestClient,
    users: dict[str, dict],
) -> None:
    token = _login(client, users["member_1"]["id"], users["member_1"]["password"])
    title = f"unique-{uuid.uuid4().hex[:8]}"
    create = client.post(
        f"/api/my/spaces/{TARGET_BANK}/notes",
        json={"title": title, "content": "body content"},
        headers=_auth(token),
    )
    inbox_id = create.json()["inbox_id"]

    with sqlite3.connect(tools.DB_PATH) as conn:
        row = conn.execute(
            "SELECT content, item_type, bank_id, status FROM inbox WHERE id = ?",
            (inbox_id,),
        ).fetchone()
    assert row is not None
    content, item_type, bank_id, status = row
    assert item_type == "note"
    assert bank_id == TARGET_BANK
    assert status == "pending_approval"
    parsed = json.loads(content)
    assert parsed["title"] == title
    assert parsed["content"] == "body content"
