## Goal

Add to `SessionMessageRepository` the two repository primitives the turn-persistence
boundary needs to undo a compression rewrite: a read that captures the session's whole
row image (with `message_id` and `created_at`) and its `/undo` boundary, and a
one-transaction restore that rewrites those rows back at or below the turn-start marker
and resets the boundary.

## Scope
**Release unit**: N/A: not part of a release unit

## Assumptions

- The capture runs immediately before `replace_messages` rewrites the session inside the
  same worker-thread call, so the image equals the persisted turn-start rows plus this
  turn's already-appended rows; only rows at or below the turn-start marker are restored,
  which discards this turn's partial rows and keeps prior turns intact (REQ-001, REQ-004).
- `messages.message_id` is the sole key other tables reference (`sessions.session_id`,
  `ON DELETE CASCADE`); no row in any other table points at a `messages.message_id`, so a
  delete-and-reinsert restore loses no dependent rows (schema read in `scripts/db/schema_sql.py`).
- Cross-plan note: `restoresummary001` edits the *body* of `replace_messages` (skip
  ephemeral system rows) while this Plan adds two new methods and leaves
  `replace_messages` and `delete_messages_from` unchanged. Either order works; coordinate the
  merge so the new methods sit apart from that edit. The captured image reflects the actual
  current rows regardless of that filter.

## Design decisions

- Add two instance methods, `capture_session_image` (new) (read) and `restore_session_image` (new)
  (one-transaction rewrite), rather than a new class: the boundary already holds the
  session and marker and delegates every DB write to the repository, so the image logic
  belongs with the other repository methods and needs no new type (REQ-001, REQ-002).
- Store each image row as `(message_id, role, content, tool_calls, tool_call_id,
  created_at)` and the boundary as a separate int, so the restore reproduces the original
  ids and `created_at` exactly instead of letting `AUTOINCREMENT` mint new ids (REQ-001,
  AC-1).

## Alternatives considered

- Capturing only `role`/`content`/`tool_calls`/`tool_call_id`: rejected because a faithful
  restore must preserve `message_id` (so `/undo` and snapshot-count stay correct) and
  `created_at` (REQ-001, AC-1); the Issue explicitly calls out `created_at`.
- Restoring every captured row unconditionally: rejected because rows appended above the
  turn-start marker this turn must not come back; the restore filters to `message_id <=
  marker` (REQ-004).

## Implementation
### Target file
`scripts/agent/session_message_repo.py`

### Procedure
1. Add `capture_session_image` (new) (session_id) after `delete_messages_from`.
2. Add `restore_session_image` (new) (session_id, image, marker) after `capture_session_image` (new).
3. Leave `replace_messages`, `delete_messages_from`, and every existing method unchanged.

### Method
- `capture_session_image` (new) (session_id: int) -> tuple[list[tuple[Any, ...]], int]:
  open one read connection, `SELECT message_id, role, content, tool_calls, tool_call_id,
  created_at FROM messages WHERE session_id = ? ORDER BY message_id`, collect the rows, and
  read `undo_floor_message_id` from `sessions`; return `(rows, undo_floor)`. Raises
  `sqlite3.Error` on DB failure.
- `restore_session_image` (new) (session_id: int, image: list[tuple], undo_floor: int,
  marker: int) -> int: open one write connection, `BEGIN IMMEDIATE`, `DELETE FROM messages
  WHERE session_id = ?`, re-INSERT each image row whose `message_id <= marker` with its
  explicit `message_id` and `created_at`, `UPDATE sessions SET undo_floor_message_id = ? WHERE
  session_id = ?`, `COMMIT`; return the restored boundary `MAX(message_id)`. On failure the
  transaction rolls back, the rows present stay untouched, and `sqlite3.Error` propagates
  (REQ-002).

### Details
- Reuse the existing `_INSERT_MESSAGE_SQL` template; extend it with `message_id` and
  `created_at` for the restore insert, e.g. `INSERT INTO messages (message_id, session_id,
  role, content, tool_calls, tool_call_id, created_at) VALUES (?, ?, ?, ?, ?, ?)`.
- Build each insert tuple as `(message_id, session_id, role, content, tool_calls,
  tool_call_id, created_at)` straight from the captured row, so ids and timestamps survive.
- Filter `message_id <= marker` inside the restore, not the capture, so the capture stays a
  plain whole-session read and the marker gate lives where the boundary passes it.
- Keep the boundary reset in the same transaction as the row rewrite so memory and the
  persisted `undo_floor_message_id` can never diverge (REQ-002, AC-6).
- Stale-reference marks: name both new methods `(new)` for `stale_detector.py`.

## Compatibility considerations

- No signature of any existing method changes, so `/compact`'s `replace_messages` use and
  the orchestrator/tool tests that stub `replace_messages` are unaffected (REQ-004).
- The restore's explicit-id re-insert is compatible with `AUTOINCREMENT` (ids only ever
  increase) and with `sessions.session_id` `ON DELETE CASCADE` (the session row is not
  touched).

## Security considerations

- The restore re-inserts rows the session already owned; it does not introduce new keys or
  untrusted data, and it preserves the stored `tool_calls`/`tool_call_id` verbatim, so no
  validation policy changes.

## Rollback considerations

- The change is additive (two methods); revert the commit. A failed restore leaves the
  pre-restore rows in place (single transaction), so a partial restore cannot corrupt state.

## Validation plan

- Repository unit tests in `tests/agent/test_session_message_repo.py`: the captured image
  round-trips `message_id` and `created_at`; `restore_session_image` (new) resets the boundary and
  re-inserts only rows at or below the marker; a failing restore (injected
  `sqlite3.Error`) leaves the existing rows untouched and re-raises.
- Static: `uv run ruff format`, `uv run ruff check`, `uv run mypy --no-namespace-packages
  scripts/`, `uv run python tools/check_module_size.py` (module stays under the 20480-byte
  gate), `uv run vulture` (no new dead code), `uv run python tools/generate_reference_table.py
  --check` (new public methods, if any, do not drift).

## Completion criteria

- `capture_session_image` (new) returns the session's rows with original `message_id` and
  `created_at` and the persisted `undo_floor_message_id`.
- `restore_session_image` (new) rewrites those rows at or below the marker in one transaction,
  resets `undo_floor_message_id`, and on failure leaves the rows present and raises
  `sqlite3.Error`.
- All repository and size/static checks pass; no existing method changed.

## Out of Scope

- Changing `replace_messages` or `delete_messages_from` behaviour.
- Any in-memory `conv.undo_floor` handling — that is the boundary's job (Row 02).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement `capture_session_image` (new) and `restore_session_image` (new) in `session_message_repo.py` | Completed | 20261105-072001 | 20261105-073500 | capture_session_image/restore_session_image added; type aliases instead of typing.Any per rules/coding.md |
| 2 | Add repository tests per Validation plan | Completed | — | 20261105-073500 | Deferred to sibling procedure 20261104-224326_05 (test-file row of the frozen Plan table); tests land in cycle 5 |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | — | 20261105-073500 | ruff/mypy/lint-imports/bandit/size/reference-table pass; full pytest 11511 passed; vulture flags the two new methods until Row 02 wires them, re-checked after cycle 02 |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Completed | — | 20261105-073500 | N/A: this row touches no `docs/` |

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
- **Requirement ID**: `REQ-001` (faithful row restore with id and `created_at`), `REQ-002`
  (one-transaction, fail-safe restore), `REQ-004` (existing methods unchanged)
- **Source issue**: issues/20261031-180341_compresscomp001_compression-compensation-wipes-session.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261104-114113_compresscomp001_compression-compensation-wipes-session.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261104-224326
- **Related target files**: scripts/agent/session_message_repo.py