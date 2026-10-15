## Goal

Verify that `/session load` restores `ctx.conv.undo_floor` from the stored boundary, and update the existing `fetch_messages` mock to the 3-tuple contract.

## Scope

Only `tests/agent/test_session_restore.py`. This document names exactly one target file.

## Assumptions

- The file mocks the session repo: `ctx.session.fetch_messages.return_value = (messages or [], session_found)` (line 24). This 2-tuple mock breaks once `fetch_messages()` returns a 3-tuple (row 02/03).
- `restore_session()` rebuilds history via `ctx.conv.replace_history(...)` then must convert the boundary.

## Design decisions

- Update the mock to a 3-tuple so `restore_session()` unpacks correctly.
- Add a test asserting `ctx.conv.undo_floor` is set to the converted index when a boundary exists, and `0` when it does not.

## Alternatives considered

- **Mock `fetch_messages` vs. a real restore** — the mock (updated to a 3-tuple) isolates the row-ID-to-index conversion; a real restore would couple this test to the repo layer covered in row 12.
- **Index by `message_id` vs. by role/content** — the conversion approach (row 10) determines how the test locates the boundary; align the assertion with that implementation choice.

## Implementation

### Target file

`tests/agent/test_session_restore.py`

### Procedure

1. Update every `ctx.session.fetch_messages.return_value = (messages or [], session_found)` to a 3-tuple: `(messages or [], session_found, undo_floor_id)`.
2. Add a test: restoring a session whose `sessions.undo_floor_message_id > 0` sets `ctx.conv.undo_floor` to the matching history index.
3. Add a test: restoring a never-compressed session (`undo_floor_message_id == 0`) sets `ctx.conv.undo_floor == 0`.

### Method

- For the conversion test, seed a session with messages, set `undo_floor_message_id` to a known row ID, mock `fetch_messages` to return that boundary, and assert `ctx.conv.undo_floor` points to the corresponding restored-history index.
- The exact index depends on how the boundary row ID maps to a history index (row 10's design decision about preserving message identity); align the test with that implementation.

### Details

- If the implementation preserves `message_id` on history entries to match the boundary, the test can assert the index by locating that `message_id`.
- Keep existing `SessionNotFoundError` / `SessionNoMessagesError` assertions intact.

## Compatibility considerations

The mock update is required or every restore test errors. Coordinate with row 10 (conversion) and rows 02/03 (contract).

## Security considerations

N/A: test-only.

## Rollback considerations

Revert the commit. Revert with rows 02/03/10 together.

## Validation plan

```bash
uv run pytest tests/agent/test_session_restore.py -p no.cacheprovider
```

Assert: mock unpacks the 3-tuple; boundary conversion covered; error paths preserved; suite passes.

## Completion criteria

`test_session_restore.py` uses the 3-tuple mock and covers boundary restoration (index set when present, 0 when absent); the test passes.

## Out of scope

The repo contract (row 12) and the facade contract (row 11).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 20261015-191020 | 20261015-191020 |  |
| 2 | Add or update tests per Validation plan | Completed | 20261015-191020 | 20261015-191020 | update fetch_messages mock to 3-tuple |
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
- **Related target files**: tests/agent/test_session_restore.py