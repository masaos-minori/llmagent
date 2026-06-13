#!/usr/bin/env python3
"""agent/note_repo.py
Note persistence repository.
"""

import logging

from db.helper import SQLiteHelper

logger = logging.getLogger(__name__)


class NoteRepository:
    """Repository for note operations."""

    def add_note(self, content: str) -> int:
        """Insert a new note and return its note_id; raises sqlite3.Error on failure."""
        with SQLiteHelper("session").open(write_mode=True) as db:
            cur = db.execute("INSERT INTO notes (content) VALUES (?)", (content,))
            note_id = cur.lastrowid
            db.commit()
        if note_id is None:
            raise RuntimeError("SQLite did not set lastrowid after INSERT into notes")
        logger.info(f"Note added: note_id={note_id}")
        return note_id

    def list_notes(self) -> list[dict]:
        """Return all notes ordered by note_id ascending; raises sqlite3.Error on failure."""
        with SQLiteHelper("session").open(row_factory=True) as db:
            rows = db.fetchall(
                "SELECT note_id, content, pinned, created_at FROM notes ORDER BY note_id",
            )
        return [dict(r) for r in rows]

    def delete_note(self, note_id: int) -> bool:
        """Delete a note by ID. Returns True when found and deleted; raises sqlite3.Error on DB failure."""
        with SQLiteHelper("session").open(write_mode=True) as db:
            row = db.execute(
                "SELECT note_id FROM notes WHERE note_id = ?",
                (note_id,),
            ).fetchone()
            if row is None:
                return False
            db.execute("DELETE FROM notes WHERE note_id = ?", (note_id,))
            db.commit()
        logger.info(f"Note deleted: note_id={note_id}")
        return True

    def pin_note(self, note_id: int) -> bool:
        """Set pinned=1. Returns False when note not found."""
        with SQLiteHelper("session").open(write_mode=True) as db:
            row = db.execute(
                "SELECT note_id FROM notes WHERE note_id = ?", (note_id,)
            ).fetchone()
            if row is None:
                return False
            db.execute("UPDATE notes SET pinned=1 WHERE note_id=?", (note_id,))
            db.commit()
        logger.info(f"Note pinned: note_id={note_id}")
        return True

    def unpin_note(self, note_id: int) -> bool:
        """Set pinned=0. Returns False when note not found."""
        with SQLiteHelper("session").open(write_mode=True) as db:
            row = db.execute(
                "SELECT note_id FROM notes WHERE note_id = ?", (note_id,)
            ).fetchone()
            if row is None:
                return False
            db.execute("UPDATE notes SET pinned=0 WHERE note_id=?", (note_id,))
            db.commit()
        logger.info(f"Note unpinned: note_id={note_id}")
        return True

    def get_pinned_notes(self) -> list[dict]:
        """Return all pinned notes ordered by note_id."""
        with SQLiteHelper("session").open(row_factory=True) as db:
            rows = db.fetchall(
                "SELECT note_id, content, pinned, created_at FROM notes "
                "WHERE pinned=1 ORDER BY note_id",
            )
        return [dict(r) for r in rows]

    def search_notes(self, query: str, limit: int = 5) -> list[dict]:
        """Return notes matching query via LIKE search, ordered by note_id.

        Escapes LIKE metacharacters (%, _, \\) to prevent unintended wildcard matches.
        """
        escaped = query.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
        with SQLiteHelper("session").open(row_factory=True) as db:
            rows = db.fetchall(
                "SELECT note_id, content, pinned, created_at FROM notes "
                "WHERE content LIKE ? ESCAPE '\\' ORDER BY note_id LIMIT ?",
                (f"%{escaped}%", limit),
            )
        return [dict(r) for r in rows]

    def get_all_note_contents(self) -> list[str]:
        """Return all note content strings in creation order; raises sqlite3.Error on failure."""
        with SQLiteHelper("session").open(row_factory=True) as db:
            rows = db.fetchall("SELECT content FROM notes ORDER BY note_id")
        return [r["content"] for r in rows]
