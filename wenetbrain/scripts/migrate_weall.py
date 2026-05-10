#!/usr/bin/env python3
"""Migrate existing SQLite database to support 'weall' space_type."""

import os
import sqlite3

DB_PATH = os.getenv("WENETBRAIN_DB_PATH", "wenetbrain.db")


def migrate():
    if not os.path.exists(DB_PATH):
        print(f"Database not found at {DB_PATH}, nothing to migrate.")
        return

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Check current schema
    cursor.execute("PRAGMA table_info(spaces)")
    cols = cursor.fetchall()
    space_type_col = next((c for c in cols if c[1] == "space_type"), None)
    if not space_type_col:
        print("spaces table missing space_type column")
        return

    # Check if 'weall' is already in the CHECK constraint by attempting an insert
    cursor.execute("BEGIN")
    try:
        cursor.execute(
            "INSERT INTO spaces (id, name, bank_id, space_type) VALUES (?, ?, ?, ?)",
            ("__migration_test__", "Test", "__test__", "weall"),
        )
        cursor.execute("DELETE FROM spaces WHERE id = ?", ("__migration_test__",))
        conn.commit()
        print("Migration not needed — 'weall' space_type is already supported.")
        return
    except sqlite3.IntegrityError as e:
        conn.rollback()
        if "CHECK" in str(e):
            print("CHECK constraint blocks 'weall'. Rebuilding spaces table...")
        else:
            raise

    # Rebuild spaces table with updated CHECK constraint
    conn.execute("PRAGMA foreign_keys=OFF")
    conn.execute("BEGIN")

    conn.execute("""
        CREATE TABLE spaces_new (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            bank_id TEXT UNIQUE NOT NULL,
            space_type TEXT DEFAULT 'team' CHECK(space_type IN ('weall','company','team','group','private')),
            description TEXT,
            company TEXT DEFAULT 'webwave',
            parent_id TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (parent_id) REFERENCES spaces_new(id)
        )
    """)

    conn.execute("""
        INSERT INTO spaces_new (id, name, bank_id, space_type, description, company, parent_id, created_at)
        SELECT id, name, bank_id, space_type, description, company, parent_id, created_at FROM spaces
    """)

    conn.execute("DROP TABLE spaces")
    conn.execute("ALTER TABLE spaces_new RENAME TO spaces")

    conn.execute("PRAGMA foreign_keys=ON")
    conn.commit()
    print("Migration complete. 'weall' space_type is now supported.")


if __name__ == "__main__":
    migrate()
