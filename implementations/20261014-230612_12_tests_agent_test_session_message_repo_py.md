## Goal

Verify the repo-level boundary behavior: `replace_messages()` writes `undo_floor_message_id` atomically with the rewrite, and `fetch_messages()` returns a 3-tuple carrying the boundary.

## Scope

Only `tests/agent/test_session_message_repo.py`. This document names exactly one target file.

## Assumptions

- Tests exercise `SessionMessageRepository` against a temp `session` DB.
- Existing tests unpack `fetch_messages()` as a 2-tuple; those break with the 3-tuple change.

## Design decisions

- Update existing 2-tuple unpacking to 3-tuple.
- Add positive tests for the boundary write and the returned boundary value.

## Alternatives considered

- **Assert atomicity via a real transaction vs. indirect observation** — a real temp `session` DB lets both messages and boundary be asserted together, proving they reflect one rewrite; asserting the SQL text alone would not prove atomicity.
- **Fake `SQLiteHelper` vs. real temp DB** — the repo talks directly to `SQLiteHelper`, so a real temp DB exercises the actual code path rather than a stub.

## Implementation

### Target file

`tests/agent/test_session_message_repo.py`

### Procedure

1. Update every `messages, found = repo.fetch_messages(sid)` to `messages, found, floor = repo.fetch_messages(sid)`.
2. Add a test: after `replace_messages(sid, msgs)`, `sessions.undo_floor_message_id == MAX(message_id)` for that session, and `fetch_messages()` returns that value as the third element.
3. Add a test: `fetch_messages()` returns `([], False, 0)` for a missing session and `([], True, 0)` for an existing session with no messages.
4. Add a test: an empty `replace_messages(sid, [])` early-returns without touching the boundary.

### Method

- Use a real temp `session` DB via `SQLiteHelper("session")` (mirror the pattern in `tests/db/test_create_schema.py` if helpful), create the session row, and assert via `PRAGMA table_info(sessions)` that `undo_floor_message_id` exists with default 0.
- Assert atomicity indirectly: after `replace_messages`, both the messages and the boundary reflect the same rewrite.

### Details

- The boundary equals the max message_id of the just-written snapshot; assert `floor == max(message_id)`.
- Preserve existing error-propagation assertions (`sqlite3.Error`).

## Compatibility considerations

All existing `fetch_messages` unpackings must become 3-tuple or the suite errors. Coordinate with row 11 (facade tests) and row 14 (restore tests).

## Security considerations

N/A: test-only.

## Rollback considerations

Revert the commit. Revert with rows 02/03 (contract) together.

## Validation plan

```bash
uv run pytest tests/agent/test_session_message_repo.py -p no.cacheprovider
```

Assert: boundary write and 3-tuple return covered; existing behavior preserved; suite passes.

## Completion criteria

`test_session_message_repo.py` covers the atomic boundary write and the 3-tuple return; existing unpacking updated; the test passes.

## Out of scope

The facade contract (row 11) and the restore conversion (row 14).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | |
| 2 | Add or update tests per Validation plan | Pending | — | — | update 2-tuple unpacking |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | N/A | — | — | |

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
- **Source issue**: N/A
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261014-214826_plan.md
- **Source implementation procedure**: N/A
- **Generated at**: 20261014-230612
- **Related target files**: tests/agent/test_session_message_repo.py
