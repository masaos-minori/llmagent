## Goal

Cover the `AgentSession` contract changes: `replace_messages()` returns the boundary, `undo_last_turn()` gates at the boundary, `fetch_messages()` returns a 3-tuple, and `delete_last_turn()` is removed.

## Scope

Only `tests/agent/test_agent_session.py`. This document names exactly one target file.

## Assumptions

- The file has a `_msgs()` helper that unwraps the `(messages, session_found)` tuple from `fetch_messages()` (around line 25). This breaks once `fetch_messages()` returns a 3-tuple (row 02/03).
- Tests run against a real or mocked message repo; `session.start()` is required before `session_id` is set.

## Design decisions

- Update the `_msgs()` helper to unpack the 3-tuple so existing assertions keep working.
- Add focused tests for each changed method rather than rewriting the suite.

## Alternatives considered

- **Facade-driven vs. direct-repo tests** — this file covers the `AgentSession` facade (boundary return, DB gate, removal) to match production callers; the repo-level contract lives in row 12. Splitting keeps each file's responsibility narrow.
- **Temp on-disk DB vs. in-memory SQLite** — the suite follows the existing in-memory-SQLite pattern in `test_agent_session.py`; a temp file adds teardown without behavioral gain.

## Implementation

### Target file

`tests/agent/test_agent_session.py`

### Procedure

1. Update `_msgs()` (line ~25) to unpack the 3-tuple: `messages, _found, _floor = ...` (keep returning just `messages`).
2. Add a test that `replace_messages()` returns the boundary `int` after a rewrite and `None` when called before `start()`.
3. Add a test that `undo_last_turn()` deletes only `message_id > undo_floor_message_id` and returns `0` when the last user turn is at/before the boundary.
4. Add a test that `fetch_messages()` returns a 3-tuple whose third element is the boundary.
5. Assert `delete_last_turn()` no longer exists (no such attribute) and nothing references it.

### Method

- For the boundary-write test, drive a real `SessionMessageRepository` against a temp `session` DB (or assert on the repo the facade delegates to).
- For the gate test, seed messages spanning a boundary row ID, then assert the DELETE leaves the boundary row and earlier rows intact.
- For the removal test: `assert not hasattr(session, "delete_last_turn")` and a static `rg 'delete_last_turn'` across the repo returns nothing.

### Details

- Keep the existing `# type: ignore[arg-type]` comments where `session_id` is narrowed; the facade signature is unchanged except `fetch_messages` return type → `tuple[list[LLMMessage], bool, int]`.
- The gate test must set `sessions.undo_floor_message_id` for the session and verify `undo_last_turn()` reads it.

## Compatibility considerations

Updating `_msgs()` is required or every existing `fetch_messages` assertion breaks. Coordinate with row 12 (repo tests) which also unpacks the tuple.

## Security considerations

N/A: test-only.

## Rollback considerations

Revert the commit. Revert with rows 02/03 (contract) together.

## Validation plan

```bash
uv run pytest tests/agent/test_agent_session.py -p no.cacheprovider
```

Assert: all updated and new tests pass; `_msgs()` handles the 3-tuple; the gate, boundary-return, and removal assertions hold.

## Completion criteria

`test_agent_session.py` covers the boundary return, the DB gate (returns 0 when blocked), the 3-tuple, and `delete_last_turn()` removal; the test passes.

## Out of scope

The repo-level contract tests (row 12) and the end-to-end undo-gating tests (row 13).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 20261015-191020 | 20261015-191020 |  |
| 2 | Add or update tests per Validation plan | Completed | 20261015-191020 | 20261015-191020 | update _msgs() 2-tuple unwrap |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20261015-191020 | 20261015-191020 |  |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | N/A | — | — |  |

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
- **Related target files**: tests/agent/test_agent_session.py