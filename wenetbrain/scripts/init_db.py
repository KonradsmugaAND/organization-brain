#!/usr/bin/env python3
"""Initialize SQLite database for WenetBrain metadata, inbox and audit log."""

import os
import sqlite3

DB_PATH = os.getenv("WENETBRAIN_DB_PATH", "wenetbrain.db")

SCHEMA = """
CREATE TABLE IF NOT EXISTS users (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    role TEXT,
    team TEXT,
    company TEXT,
    email TEXT UNIQUE,
    voice_profile_path TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS meetings (
    id TEXT PRIMARY KEY,
    title TEXT,
    meeting_type TEXT CHECK(meeting_type IN ('team','cross','oneonone','allhands')),
    date TEXT,
    participants TEXT,
    transcript_path TEXT,
    audio_path TEXT,
    status TEXT DEFAULT 'pending',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS inbox (
    id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL,
    meeting_id TEXT,
    bank_id TEXT,
    item_type TEXT CHECK(item_type IN ('note','action_item','decision','task_clickup')),
    content TEXT,
    status TEXT DEFAULT 'pending_approval' CHECK(status IN ('pending_approval','approved','rejected','exported_to_clickup')),
    proposed_by TEXT,
    approved_by TEXT,
    approved_at TIMESTAMP,
    clickup_task_id TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id),
    FOREIGN KEY (meeting_id) REFERENCES meetings(id)
);

CREATE TABLE IF NOT EXISTS audit_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    event_type TEXT NOT NULL,
    user_id TEXT,
    item_id TEXT,
    from_bank TEXT,
    to_bank TEXT,
    details TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS spaces (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    bank_id TEXT UNIQUE NOT NULL,
    space_type TEXT DEFAULT 'team' CHECK(space_type IN ('weall','company','team','group','private')),
    description TEXT,
    company TEXT DEFAULT 'webwave',
    parent_id TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (parent_id) REFERENCES spaces(id)
);

CREATE TABLE IF NOT EXISTS user_acl (
    user_id TEXT NOT NULL,
    bank_id TEXT NOT NULL,
    role TEXT DEFAULT 'member' CHECK(role IN ('member','editor','manager','admin')),
    PRIMARY KEY (user_id, bank_id)
);
"""


def init_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.executescript(SCHEMA)
    conn.commit()
    conn.close()
    print(f"Database initialized at {DB_PATH}")


if __name__ == "__main__":
    init_db()
