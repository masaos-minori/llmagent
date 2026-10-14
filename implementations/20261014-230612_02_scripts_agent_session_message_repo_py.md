## Goal

Persist the `/undo` compression boundary atomically with the snapshot rewrite, and expose the stored boundary on restore so it can be converted into a history index.

## Scope

Only `scripts/agent/session_message_repo.py`: `replace_messages()` and `fetch_messages()`. This document names exactly one target file.

## Assumptions

- `replace_messages()` runs in a single transaction (DELETE + INSERT) and early-returns on empty input (lines 146-162).
- `fetch_messages()` currently returns `(messages, session_found)` (lines 168-218) and is called by `AgentSession.fetch_messages()` (facade, `scripts/agent/session.py:110`) and `session_restore.restore_session()` (`scripts/agent/services/session_restore.py:32`).
- Changing the return signature ripples to those callers; update them in the same step.

## Design decisions

- Write the boundary in the SAME transaction as the rewrite so it is atomic with the snapshot (never persisted without the snapshot, never without its boundary).
- Set the boundary to the post-rewrite `MAX(message_id)` for the session.
- Extend `fetch_messages()` to return a 3-tuple `(messages, session_found, undo_floor_message_id)` so restore reads the boundary in the same query round-trip.

## Alternatives considered

- **Separate `UPDATE` call outside the rewrite transaction** — rejected: non-atomic, leaves a window where the snapshot and boundary disagree.
- **Return the boundary via a separate method/query on restore** — rejected: an extra DB round-trip and a second code path; the plan specifies surfacing it through `fetch_messages()`.

## Implementation

### Target file

`scripts/agent/session_message_repo.py`

### Procedure

1. In `replace_messages()`, extend the transaction (lines 158-162) to set the boundary.
2. In `fetch_messages()`, also select `undo_floor_message_id` and return it.

### Method

**`replace_messages()`** — inside the `with SQLiteHelper("session").open(write_mode=True) as db:` block (after `db.commit()` is NOT yet called; add before commit):

```python
db.execute(
    "UPDATE sessions SET undo_floor_message_id = "
    "(SELECT MAX(message_id) FROM messages WHERE session_id = ?) "
    "WHERE session_id = ?",
    (session_id,),
)
```

Place this `UPDATE` after the `executemany` INSERT and before `db.commit()` so the snapshot rewrite and boundary update are atomic. Keep the existing early returns (empty `messages`, empty `rows`).

**`fetch_messages()`** — add `undo_floor_message_id` to the session lookup and return it:

- In the `session_found` check, also read the boundary. Query `undo_floor_message_id` from `sessions` for the session.
- Return `(messages, session_found, undo_floor_message_id)`. For the `not session_found` branch return `([], False, 0)`; for the "exists but no messages" branch return `([], True, 0)`.

### Details

- The boundary equals the max message_id of the just-written snapshot. Using a correlated subquery in the `UPDATE` keeps it to one statement.
- Preserve all existing error propagation (`sqlite3.Error` propagates to caller).
- Update BOTH callers in the same step (see rows 03 and 10):
  - `AgentSession.fetch_messages()` facade (`scripts/agent/session.py:110`) must unpack the 3-tuple and return it.
  - `restore_session()` (`scripts/agent/services/session_restore.py:32`) must unpack the 3-tuple and convert the stored boundary row ID into a history index.
- Existing tests that unpack `fetch_messages()` as a 2-tuple will break (e.g. `tests/agent/test_regression_undo_artifact.py`). That file is not an Implementation Target Files row — see Plan Gap note below.

## Compatibility considerations

Changing `fetch_messages()` to a 3-tuple is a breaking contract change. Every caller must be updated in the same step: `AgentSession.fetch_messages()` (facade) and `restore_session()`. Callers not updated will raise "too many values to unpack".

## Security considerations

N/A: no new attack surface. The boundary is an internal integrity marker, not user input.

## Rollback considerations

Revert the commit. The column addition (row 01) must be reverted together; reverting this row alone against the new column would leave `fetch_messages()` referencing a non-existent column.

## Validation plan

```bash
uv run pytest tests/agent/test_session_message_repo.py -p no.cacheprovider
```

Assert: after `replace_messages()`, `sessions.undo_floor_message_id == MAX(message_id)` for the session; `fetch_messages()` returns a 3-tuple whose third element is the boundary; the boundary is `0` for a session with no messages.

## Completion criteria

`replace_messages()` writes `undo_floor_message_id` atomically with the rewrite; `fetch_messages()` returns `(messages, session_found, undo_floor_message_id)`; affected callers updated; `tests/agent/test_session_message_repo.py` passes.

## Out of scope

The in-memory `ctx.conv.undo_floor` field (row 04), the restore conversion logic (row 10), and the `/undo` gating (rows 05/07).

## Plan gap

`fetch_messages()` changes from a 2-tuple to a 3-tuple. Existing tests that unpack it as a 2-tuple will break, e.g. `tests/agent/test_regression_undo_artifact.py` (uses `_msgs()` = `messages, found = fetch_messages(...)`). That file is NOT an Implementation Target Files row, so updating it is an additional target-file discovery: report it as `Blocked` / Needs confirmation and add a dedicated row (or get explicit authorization) rather than editing it silently here. Other `_msgs()` callers in `test_agent_session.py` (row 11), `test_session_message_repo.py` (this row), and `test_history_compression_consistency.py` (row 13) are covered by their rows.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | |
| 2 | Add or update tests per Validation plan | Pending | — | — | |
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
- **Related target files**: scripts/agent/session_message_repo.py
