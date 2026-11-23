## Goal

Update the compress-persist-restore round-trip test to the builder contract of `restore_session`.

## Scope
**Release unit**: N/A: not part of a release unit

In scope: `test_compress_persist_restore_keeps_summary_drops_ephemeral` only (the tail that reads `ctx.conv.history` and `ctx.conv.undo_floor` after `restore_session`).

## Assumptions

- Verified: the test calls `await restore_session(ctx, session_id=1)` and then asserts on `ctx.conv.history` and `ctx.conv.undo_floor`; the builder now returns a state object and leaves `ctx` untouched.
- The consumer scan missed this test; found by the full-suite run, recorded as a fallout row.

## Design decisions

- Assert on the returned state's history and undo floor with the same expectations (prompt, one canonical summary, no forged or ephemeral rows, floor 3).

## Alternatives considered

N/A: the assertions keep their meaning; only their source changes.

## Implementation
### Target file
`tests/agent/test_history_compression_consistency.py`

### Procedure
1. Bind `state = await restore_session(...)`, then read the history and undo floor from `state` instead of `ctx.conv`.

### Method
Edit the final block of the test; keep the seeded `ctx` (it still supplies `system_prompt_content`).

### Details
- Use the field names defined in `session_restore.py` for the returned state.

## Compatibility considerations

N/A: tests only.

## Security considerations

N/A: tests only.

## Rollback considerations

N/A: revert the commit.

## Validation plan

- `uv run pytest tests/agent/test_history_compression_consistency.py`

## Completion criteria

- The test passes with the same behavioral assertions on the returned state.

## Out of Scope

Production code and other tests in the file.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | — | 20261123-122904 | Changed: tests/agent/test_history_compression_consistency.py |
| 2 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20261123-122904 | 20261123-123431 | awaiting end-of-batch run End-of-batch run passed: 13519 passed, 5 skipped; mypy 608 files clean; lint-imports 6 kept; diff-cover 98% |

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
- **Requirement ID**: `REQ-002` (atomic /clear new and /session load through the transition service), `REQ-009` (separate restore counts)
- **Source issue**: issues/20261119-145300_cliplc002_session-transition-generation.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261122-232757_cliplc002_session-transition-generation.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261123-094714
- **Related target files**: `tests/agent/test_history_compression_consistency.py`