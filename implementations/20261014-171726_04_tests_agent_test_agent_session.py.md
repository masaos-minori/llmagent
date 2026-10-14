# Implementation Procedure

## Goal

Add a unit test asserting `message_count` in `list_sessions()` results (`REQ-001` / `AC-1`).

## Scope

Add one or more test methods to the existing `TestListSessions` class in `tests/agent/test_agent_session.py` (class starts at line 360). Test-only change.

## Assumptions

- The `session` fixture wires `AgentSession` to a fresh in-memory SQLite DB with `sessions` + `messages` tables (schema lines 33-47); session_id `1` is pre-inserted with zero messages.
- `session.start()` inserts a new session row (autoincrement id `2`) and sets `self.session_id`; `session.save(role, content)` / `session.save_many(rows)` adds `messages` rows to the current session.
- `list_sessions()` now returns `message_count` (sibling procedure for `scripts/agent/session.py`).

## Design decisions

- Seed via the public API (`start()`/`save()`) rather than raw SQL, reusing the existing pattern in `test_saves_multiple_messages` (line 230) and `test_updates_title` (line 343, which calls `list_sessions()`).
- Assert both branches: the just-started session has a non-zero count, and the pre-existing session_id `1` reports `0` (verifies the `LEFT JOIN` does not drop zero-message sessions).

## Alternatives considered

- Inserting messages via raw `conn.execute(...)`: rejected — using `save()` exercises the real code path and matches the suite's convention.

## Implementation

### Target file

`tests/agent/test_agent_session.py`

### Procedure

Add a method to `TestListSessions`, e.g. `test_message_count_counts_messages_per_session`:

1. `session.start()` then `session.save("user", "a")` and `session.save("user", "b")` (2 messages on the new session).
2. `rows = {r["session_id"]: r for r in session.list_sessions()}`.
3. `assert rows[session.session_id]["message_count"] == 2`.
4. `assert rows[1]["message_count"] == 0`.

### Method

Place the method inside `class TestListSessions` as its last method, immediately after `test_marks_current_session` (lines 384-387), before the class closes at line 388. Keep the existing `self, session` signature. Do not modify other tests.

### Details

- `list_sessions()` defaults to `limit=20`, so both sessions (id `1` and the new id `2`) are returned; the dict comprehension keys by `session_id`.
- The `reset_fake_helper` autouse fixture gives each test an isolated in-memory DB, so ids are deterministic.

## Compatibility considerations

Test-only; additive method. Does not alter existing tests or the module under test.

## Security considerations

N/A: test-only.

## Rollback considerations

Remove the added test method.

## Validation plan

| Target/Module | Strategy | Command | Expected |
|---|---|---|---|
| `tests/agent/test_agent_session.py` | Unit — assert counts incl. zero case | `uv run pytest tests/agent/test_agent_session.py` | New test passes; full `TestListSessions` still passes |

## Completion criteria

The new test asserts `message_count` matches `messages` rows and that a zero-message session reports `0`.

## Out of scope

Source query change (`scripts/agent/session.py`) is a separate row.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | N/A | — | — | test-only row |
| 2 | Add or update tests per Validation plan | Pending | — | — | unit test for `message_count` |
| 3 | Run validation sequence (`rules/toolchain.md`) | Pending | — | — | — |
| 4 | Update documentation | N/A | — | — | not in scope for this row |

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
- **Requirement ID**: `REQ-001` — add per-session message count to `/session list`
- **Source issue**: `issues/20261014-150311_sess001_finalize-session-list-command.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261014-160933_plan.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261014-171726
- **Related target files**: `tests/agent/test_agent_session.py`
