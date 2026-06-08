#!/usr/bin/env python3
"""agent/note_repo.py
Note persistence repository.
"""

import logging

from db.helper import SQLiteHelper

logger = logging.getLogger(__name__)


class NoteRepository:
    """Repository for note operations."""

    def __init__(self) -> None:
        pass

    def add_note(self, content: str) -> int | None:
        """Insert a new note and return its note_id; None on failure."""
        try:
            with SQLiteHelper("session").open(write_mode=True) as db:
                cur = db.execute("INSERT INTO notes (content) VALUES (?)", (content,))
                note_id = cur.lastrowid
                db.commit()
            logger.info(f"Note added: note_id={note_id}")
            return note_id
        except Exception as e:
            logger.warning(f"add_note failed: {e}")
            return None

    def list_notes(self) -> list[dict]:
        """Return all notes ordered by note_id ascending."""
        try:
            with SQLiteHelper("session").open(row_factory=True) as db:
                rows = db.fetchall(
                    "SELECT note_id, content, created_at FROM notes ORDER BY note_id",
                )
            return [dict(r) for r in rows]
        except Exception as e:
            logger.warning(f"list_notes failed: {e}")
            return []

    def delete_note(self, note_id: int) -> bool:
        """Delete a note by ID. Returns True when found and deleted."""
        try:
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
        except Exception as e:
            logger.warning(f"delete_note failed (id={note_id}): {e}")
            return False

    def get_all_note_contents(self) -> list[str]:
        """Return all note content strings in creation order for prompt injection."""
        try:
            with SQLiteHelper("session").open(row_factory=True) as db:
                rows = db.fetchall("SELECT content FROM notes ORDER BY note_id")
            return [r["content"] for r in rows]
        except Exception as e:
            logger.warning(f"get_all_note_contents failed: {e}")
            return []
