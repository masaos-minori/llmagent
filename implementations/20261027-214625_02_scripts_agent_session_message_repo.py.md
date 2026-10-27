# Implementation Procedure: Add a row-level undo method to `SessionMessageRepository`

## Goal

Give the DB undo step a repo-level home that reads the `/undo` boundary, finds the last user row, selects the deleted rows' identity, deletes them, and returns them as `list[DeletedRow]` in ascending `message_id` order — so the service side trims memory by row identity. (`REQ-001`, `REQ-006`)

## Scope

One production file, `scripts/agent/session_message_repo.py`. One new method on `SessionMessageRepository`. No change to existing methods.

## Assumptions

- The method lives on `SessionMessageRepository`, consistent with `replace_messages` (L140-174), `delete_messages_from` (L193-213), and `fetch_messages` (L269-326) all owning session-message persistence here.
- The repo already imports `SQLiteHelper` from `db.helper` (L10) and `LLMMessage` from `shared.types` (L12); it will import `DeletedRow` (new) from `agent.services.models` (row 01). If that import cycle (repo → services) errors, the dataclass stays in `models.py` and the repo builds plain tuples — but the return type contract (`list[DeletedRow]`) is owned by the caller/repo agreement; implement procedure confirms.
- Existing pattern: each method opens exactly one `SQLiteHelper("session")` connection; writes use `open(write_mode=True)`, commits, and let `sqlite3.Error` propagate.
- `fetch_messages` (L281-325) shows how to read `undo_floor_message_id` from `sessions` and messages ordered by `message_id` using `row_factory=True`.

## Design decisions

- Mirror `session.undo_last_turn`'s current SQL (session.py L224-269) but return rows instead of a count: read `undo_floor_message_id`, scan rows DESC for the last `role == "user"`, gate on `last_user_id > undo_floor`, then `SELECT ... ORDER BY message_id` + `DELETE ... WHERE message_id >= last_user_id` in one transaction, returning the selected rows.
- Build `DeletedRow` (new) per row from the SELECT columns. `content`/`tool_call_id` may be NULL → `None`.
- Return `[]` when blocked (no user row, or at/before the boundary) or when the session has no rows / `session_id is None`.

## Alternatives considered

- Keeping the SQL in `session.py` and having the repo expose a thin wrapper — rejected: the Plan requires a repo-level home consistent with other session-message ops (row 02 evidence), and the return-type change must move with the SQL.
- Returning `(rows, count)` — rejected: `n_removed` is derived from `len(rows)` by the caller; the Plan's `UndoResult` carries `deleted_rows` (new) and `n_removed` separately (row 01), so the repo returns just the rows.

## Implementation

### Target file
`scripts/agent/session_message_repo.py`

### Procedure
1. Import `DeletedRow` (new) from `agent.services.models` at the top (next to the `shared.types` import). Guard against a cycle: if `agent.services.models` imports the repo, use a local import inside the method instead of a module-level one.
2. Add `undo_deleted_rows(self, session_id: int | None) -> list[DeletedRow]` to `SessionMessageRepository`, next to `delete_messages_from`.

### Method
One new method. Read floor → find last user row → gate → SELECT+DELETE in one write connection → build `DeletedRow` (new) list. No change to existing methods.

### Details
- New method (new):
  ```python
  def undo_deleted_rows(self, session_id: int | None) -> list[DeletedRow]:
      """Return the rows deleted by a /undo, ascending message_id (REQ-001).

      One transaction: read the /undo boundary, find the last user row, gate on
      `last_user_id > undo_floor`, then SELECT and DELETE every row at/after it.
      Returns [] when there is no session, no user row, or the last user turn is
      at/before the boundary (nothing undoable). Raises sqlite3.Error on DB failure.
      """
      if session_id is None:
          return []
      from agent.services.models import DeletedRow (new)  # local import avoids repo->services cycle
      with SQLiteHelper("session").open(write_mode=True) as db:
        floor_row = db.execute(
            "SELECT undo_floor_message_id FROM sessions WHERE session_id = ?",
            (session_id,),
        ).fetchone()
        undo_floor = floor_row[0] if floor_row else 0
        rows = db.fetchall(
            "SELECT message_id, role, content, tool_calls, tool_call_id "
            "FROM messages WHERE session_id = ? ORDER BY message_id DESC",
            (session_id,),
        )
        last_user_id = None
        for r in rows:
            if r["role"] == "user":
                last_user_id = r["message_id"]
                break
        if last_user_id is None or last_user_id <= undo_floor:
            return []  # nothing undoable: at/before the boundary
        deleted_rows = db.fetchall(
            "SELECT message_id, role, content, tool_call_id "
            "FROM messages WHERE session_id = ? AND message_id >= ? "
            "ORDER BY message_id",
            (session_id, last_user_id),
        )
        db.execute(
            "DELETE FROM messages WHERE session_id = ? AND message_id >= ?",
            (session_id, last_user_id),
        )
        db.commit()
      return [
          DeletedRow(
              message_id=r["message_id"],
              role=r["role"],
              content=r["content"],
              tool_call_id=r["tool_call_id"],
          )
          for r in deleted_rows
      ]
  ```
- Note: `fetch_messages` uses `row_factory=True` to get dict-like rows; this method relies on the same `SQLiteHelper(...).open()` returning row-factory rows (the repo's other readers do). Confirm the default `open()` here yields keyed access; if not, open with `row_factory=True` as `fetch_messages` does.

## Compatibility considerations

- Purely additive method; no existing method signature changes, so `session.py`'s current callers of other repo methods are unaffected. `session.py`'s own `undo_last_turn` is rewritten in row 03 to call this.
- `DeletedRow` (new) is imported lazily to avoid any import-order surprise.

## Security considerations

- Read/delete are scoped by `session_id` + `message_id >= last_user_id`; same authorization surface as `delete_messages_from`. No injection surface beyond the parameterized queries already used throughout the repo.

## Rollback considerations

- Single logical commit touching this file, `models.py` (row 01), `session.py` (row 03), their tests; rollback is `git revert`. No schema/migration.

## Validation plan

- Unit: `uv run pytest tests/agent/test_agent_session.py -q -k "undo"` — updated cases assert the returned row lists (row 05).
- Static: `uv run ruff check scripts/agent/session_message_repo.py` and `uv run mypy --no-namespace-packages scripts/agent/session_message_repo.py` — clean.
- Full suite: `uv run pytest tests/` green.

## Completion criteria

- `undo_deleted_rows` (new) returns `list[DeletedRow]` in ascending `message_id` order, gated by `undo_floor_message_id`, `[]` when blocked.
- One transaction; `sqlite3.Error` propagates. mypy/ruff clean.

## Out of Scope

- Trimming memory (row 04).
- Re-pointing `session.undo_last_turn` (row 03).
- Any caller beyond `session.py` (only caller; REQ-005 atomic update).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Add `undo_deleted_rows` (new) returning `list[DeletedRow]` (new), gated by boundary | Pending | — | — | |
| 2 | Run the validation sequence (static + undo test cases) | Pending | — | — | |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| — | — | — | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| — | — | — | — | — | — |

## Traceability
- **Workflow phase**: plan-to-implementation-procedure
- **Requirement ID**: `REQ-001`, `REQ-006`
- **Source issue**: issues/20261026-224959_undo002_undo-db-memory-set-consistency.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261027-074657_undo002_undo-db-memory-set-consistency.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261027-214625
- **Related target files**: scripts/agent/session_message_repo.py
