# Implementation Procedure: Add the `/undo` memory/DB parity regression module

## Goal

Add a new regression module that proves `/undo` restores memory/DB parity after injected divergence (T-001, REQ-007), validates the row-list return and boundary gate (T-002, REQ-001), exercises the ambiguous-match reload fallback with warning log (T-003, REQ-003), and confirms memory-only artifact trimming (T-004, REQ-002). (`REQ-002`, `REQ-003`, `REQ-004`, `REQ-007`)

## Scope

One new file, `tests/agent/test_undo_db_memory_parity.py`. Four test functions/classes covering T-001..T-004. No other file touched.

## Assumptions

- No existing test constructs diverged memory/DB state before undo (Plan evidence: grep over tests/). File name is new; verify no collision with `ls tests/agent`.
- Tests drive `undo_service.undo_last_turn(ctx)` through a minimal `AgentContext` whose `session` is an `AgentSession` backed by a patched in-memory SQLite DB (same `_FakeSQLiteHelper`/`patch("agent.session.SQLiteHelper")` pattern as `tests/agent/test_agent_session.py` L638-705 and `tests/agent/test_regression_undo_artifact.py` L51-116).
- `ctx.conv.history` is a list of message dicts; `ctx.conv.undo_floor` is an index; `ctx.stats.stat_turns` an int.
- `DeletedRow` (new) is importable from `agent.services.models` for asserting returned identity.
- A warning is emitted on the reload-fallback path; capture it with `caplog` / `pytest.warns` / a logger hook to assert the decision was logged (REQ-004).

## Design decisions

- Build a small context factory fixture: given a list of `(role, content, tool_call_id)` turns plus an optional orphan DB row, seed the DB via `session.save_many`, set `conv.history`/`conv.undo_floor`, and return a context wired to `undo_service`.
- Parity assertion compares memory history to `fetch_messages` output on role/content/tool_call_id after undo (T-001).
- The divergence fixtures inject exactly one extra tool row into the DB tail (via a direct DB insert through the patched connection) that is absent from memory, so the identity tail-match fails and the reload fallback fires (T-003).

## Alternatives considered

- Reusing `test_regression_undo_artifact.py` for parity — rejected: that module asserts counts and never injects divergence; a dedicated module is required (Plan evidence) and is its own target row.

## Implementation

### Target file
`tests/agent/test_undo_db_memory_parity.py` (new)

### Procedure
1. Create the module with the shared schema SQL, a `_FakeSQLiteHelper`-style fake (copy the pattern from `test_regression_undo_artifact.py`), and a `session` fixture.
2. Add a context-builder helper producing a minimal `AgentContext`-like object with `conv` (history, undo_floor), `session`, and `stats`.
3. Implement T-001..T-004 as described below.
4. Assert the reload-fallback warning is logged (T-003).

### Method
New module. Fixture + context builder + four test cases.

### Details
- **T-001** (REQ-007): seed two turns (user/assistant), inject an extra orphan `tool` row into the DB tail only, set memory history to the two turns, call undo, assert memory history equals `fetch_messages` (same roles/contents/ids order) — parity restored.
- **T-002** (REQ-001): healthy session → undo returns a non-empty `list[DeletedRow]` whose `message_id`s are ascending and equal the deleted set; boundary-blocked session (last user at/before `undo_floor_message_id`) → returns `[]`.
- **T-003** (REQ-003): divergence where the DB tail contains a row absent from memory AND the memory tail cannot match contiguously → after undo, `conv.history` equals the DB remaining rows (reload) and a warning logging the deleted ids was emitted.
- **T-004** (REQ-002): a memory-only `_memory_injected` block before the last user turn is trimmed along with that turn on the primary (matched) path.
- Keep the module focused: these four cases are the acceptance surface (AC-001..AC-005). Do not add broad coverage.

## Compatibility considerations

- New file; does not affect existing modules. Import `undo_service` and `agent.session.AgentSession` only.

## Security considerations

- N/A: test-only, in-memory DB.

## Rollback considerations

- Single logical commit adding this file; rollback is `git revert`.

## Validation plan

- `uv run pytest tests/agent/test_undo_db_memory_parity.py -q` — T-001..T-004 pass.
- Static: `uv run ruff check tests/agent/test_undo_db_memory_parity.py` and `uv run mypy --no-namespace-packages tests/agent/test_undo_db_memory_parity.py` — clean.
- Full suite: `uv run pytest tests/` green.

## Completion criteria

- All four parity cases pass; the reload-fallback warning is asserted; mypy/ruff clean.

## Out of Scope

- Production changes (rows 01-04).
- Return-type updates to existing tests (rows 05/06).
- Doc update (row 08).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Add the parity module with T-001..T-004 (new) | Pending | — | — | |
| 2 | Run the validation sequence (pytest + static) | Pending | — | — | |

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
- **Requirement ID**: `REQ-002`, `REQ-003`, `REQ-004`, `REQ-007`
- **Source issue**: issues/20261026-224959_undo002_undo-db-memory-set-consistency.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261027-074657_undo002_undo-db-memory-set-consistency.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261027-214625
- **Related target files**: tests/agent/test_undo_db_memory_parity.py
