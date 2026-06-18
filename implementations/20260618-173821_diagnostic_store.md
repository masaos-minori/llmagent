# Implementation: Create `DiagnosticStore` module

## Goal

Create a new `DiagnosticStore` class that owns the `session_diagnostics` table and provides `save()`, `fetch()`, and `fetch_all()` methods, independent of `SessionMessageRepository`.

## Scope

- New file: `scripts/agent/diagnostic_store.py`
- Update `scripts/agent/__init__.py` if applicable

**Out of scope:** Schema migration (separate doc), caller changes (separate docs).

## Assumptions

1. Diagnostic data volume is low — single call per session from `orchestrator.py`.
2. Existing diagnostic data in `messages` table (role='diagnostic') stays in place; new data goes to `session_diagnostics`.

## Implementation

### Target file

`scripts/agent/diagnostic_store.py`

### Procedure

1. Create `DiagnosticStore` class.
2. Add `save(session_id, kind, content) → None` method.
3. Add `fetch(session_id) → list[dict]` method.
4. Add `fetch_all(limit=50) → list[dict]` method.

### Method

New file following existing repository patterns (`SessionMessageRepository`, `NoteRepository`).

### Details

```python
"""agent/diagnostic_store.py
DiagnosticStore — dedicated storage for runtime diagnostics.
Diagnostic data is stored in the session_diagnostics table,
separate from normal conversation messages.
"""

from __future__ import annotations

import json
import logging
from typing import Any

from db.helper import SQLiteHelper

logger = logging.getLogger(__name__)


class DiagnosticStore:
    """Dedicated store for diagnostic messages, separate from conversation history."""

    def __init__(self, session_id: int | None = None) -> None:
        self.session_id = session_id

    def save(self, session_id: int | None, kind: str, content: str) -> None:
        """Persist one diagnostic entry."""
        with SQLiteHelper("session").open(write_mode=True) as db:
            db.execute(
                "INSERT INTO session_diagnostics (session_id, kind, content)"
                " VALUES (?, ?, ?)",
                (session_id, kind, content),
            )
            db.commit()

    def fetch(self, session_id: int) -> list[dict[str, Any]]:
        """Return all diagnostics for a session, newest first."""
        with SQLiteHelper("session").open(row_factory=True) as db:
            rows = db.fetchall(
                "SELECT id, session_id, kind, content, created_at"
                " FROM session_diagnostics WHERE session_id = ?"
                " ORDER BY created_at DESC",
                (session_id,),
            )
        return [dict(r) for r in rows]

    def fetch_all(self, limit: int = 50) -> list[dict[str, Any]]:
        """Return most recent diagnostics across all sessions."""
        with SQLiteHelper("session").open(row_factory=True) as db:
            rows = db.fetchall(
                "SELECT id, session_id, kind, content, created_at"
                " FROM session_diagnostics"
                " ORDER BY created_at DESC LIMIT ?",
                (limit,),
            )
        return [dict(r) for r in rows]
```

## Validation Plan

| Check | Tool | Criterion |
|---|---|---|
| Import | `python -c "from agent.diagnostic_store import DiagnosticStore"` | No ImportError |
| Lint | `ruff check scripts/agent/diagnostic_store.py` | 0 errors |
| Type | `mypy scripts/agent/diagnostic_store.py` | No new errors |
| Architecture | `lint-imports` | 0 violations |
