# Implementation: agent/note_repo.py + agent/session.py — pin/unpin/search methods

## Goal

Add `pin_note()`, `unpin_note()`, `get_pinned_notes()`, `search_notes()` to `NoteRepository`; update `list_notes()` to SELECT `pinned`; add matching delegation methods to `AgentSession`; update `tests/test_note_repo.py`.

## Scope

- `scripts/agent/note_repo.py` — 4 new methods + `list_notes()` SELECT update
- `scripts/agent/session.py` — 4 delegation methods
- `tests/test_note_repo.py` — `_SCHEMA_SQL` pinned field; `test_returns_correct_keys` update; 4 new test classes

## Assumptions

- `db/create_schema.py` already has `pinned INTEGER NOT NULL DEFAULT 0` in notes DDL
- `NoteRepository` uses `SQLiteHelper("session")` for all DB access
- `test_note_repo.py` uses `_FakeSQLiteHelper` with in-memory SQLite — `_SCHEMA_SQL` must match production DDL
- LIKE search: `%{escaped}%` with metachar escaping (`%`, `_`, `\`)
- `search_notes()` default limit=5 matching plan design
- Existing `add_note()`, `delete_note()`, `get_all_note_contents()` are unchanged

## Implementation

### Target file

- `scripts/agent/note_repo.py`
- `scripts/agent/session.py`
- `tests/test_note_repo.py`

### Procedure

1. Update `list_notes()` in `note_repo.py` — add `pinned` to SELECT
2. Add `pin_note()`, `unpin_note()`, `get_pinned_notes()`, `search_notes()` to `NoteRepository`
3. Add 4 delegation methods to `AgentSession` in `session.py`
4. Update `_SCHEMA_SQL` in `test_note_repo.py`
5. Update `TestListNotes.test_returns_correct_keys` assertion
6. Add `TestPinNote`, `TestUnpinNote`, `TestGetPinnedNotes`, `TestSearchNotes` test classes

### Method

- Edit tool for each file
- Use existing `add_note/delete_note` as implementation pattern

### Details

**`note_repo.py` — list_notes() SELECT update:**
```python
def list_notes(self) -> list[dict]:
    with SQLiteHelper("session").open(row_factory=True) as db:
        rows = db.fetchall(
            "SELECT note_id, content, pinned, created_at FROM notes ORDER BY note_id",
        )
    return [dict(r) for r in rows]
```

**`note_repo.py` — pin_note():**
```python
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
```

**`note_repo.py` — unpin_note():**
```python
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
```

**`note_repo.py` — get_pinned_notes():**
```python
def get_pinned_notes(self) -> list[dict]:
    """Return all pinned notes ordered by note_id."""
    with SQLiteHelper("session").open(row_factory=True) as db:
        rows = db.fetchall(
            "SELECT note_id, content, pinned, created_at FROM notes "
            "WHERE pinned=1 ORDER BY note_id",
        )
    return [dict(r) for r in rows]
```

**`note_repo.py` — search_notes():**
```python
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
```

**`session.py` — 4 delegation methods (add after existing delete_note delegation):**
```python
def pin_note(self, note_id: int) -> bool:
    """Pin a note by ID."""
    return self._note_repo.pin_note(note_id)

def unpin_note(self, note_id: int) -> bool:
    """Unpin a note by ID."""
    return self._note_repo.unpin_note(note_id)

def get_pinned_notes(self) -> list[dict]:
    """Return all pinned notes."""
    return self._note_repo.get_pinned_notes()

def search_notes(self, query: str, limit: int = 5) -> list[dict]:
    """Search notes by content LIKE query."""
    return self._note_repo.search_notes(query, limit)
```

**`test_note_repo.py` — _SCHEMA_SQL:**
```python
_SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS notes (
    note_id    INTEGER PRIMARY KEY AUTOINCREMENT,
    content    TEXT    NOT NULL,
    pinned     INTEGER NOT NULL DEFAULT 0,
    created_at TEXT    NOT NULL DEFAULT (datetime('now'))
);
"""
```

**`test_note_repo.py` — test_returns_correct_keys:**
```python
assert set(notes[0].keys()) == {"note_id", "content", "pinned", "created_at"}
```

## Validation plan

- `uv run pytest tests/test_note_repo.py -v` — all pass
- `uv run mypy scripts/agent/note_repo.py scripts/agent/session.py` — 0 new errors
- `uv run ruff check scripts/agent/note_repo.py` — 0 errors
