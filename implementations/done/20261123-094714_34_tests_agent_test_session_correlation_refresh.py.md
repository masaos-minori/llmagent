## Goal

Update the correlation-refresh tests to the new contracts: `clear_conversation` is async and `restore_session` only builds state, so the correlation refresh happens at the transition commit.

## Scope
**Release unit**: N/A: not part of a release unit

In scope: `TestFlowRefresh` (`test_restore_flow_refreshes_correlation`, `test_clear_flow_refreshes_correlation`) and the imports. The helper-guard tests stay unchanged.

## Assumptions

- Verified: the restore-flow test expects `restore_session` to call `set_session_id`; after procedure 04 it no longer mutates the context, and the refresh is done by `SessionTransitionService` at commit.
- Verified: the clear-flow test calls `clear_conversation(ctx, new_session=True)` synchronously; after procedure 06 it is a coroutine.
- The consumer scan in the Plan missed this test; found by the full-suite run, recorded as a fallout row.

## Design decisions

- Restore flow: drive the load through `SessionTransitionService` (or assert the builder never calls `set_session_id` and the commit does); keep the invariant that correlation is refreshed exactly once with the new id.

## Alternatives considered

Rejected: dropping the restore-flow test (it guards the correlation-refresh invariant that this suite exists for).

## Implementation
### Target file
`tests/agent/test_session_correlation_refresh.py`

### Procedure
1. Make the clear-flow test `async` and `await clear_conversation(...)`.
2. Rewrite the restore-flow test to assert the builder leaves the correlation untouched and that the transition commit refreshes it once with the new id.

### Method
Follow the mock setup of `tests/agent/services/test_session_transition.py` (the new service tests) for a ctx the service accepts.

### Details
- Keep the MagicMock ctx with a real `ConversationState`; no DB, network, or config.

## Compatibility considerations

N/A: tests only.

## Security considerations

N/A: tests only.

## Rollback considerations

N/A: revert the commit.

## Validation plan

- `uv run pytest tests/agent/test_session_correlation_refresh.py tests/agent/services/test_session_transition.py`

## Completion criteria

- Both flow tests pass against the new contracts and still prove the correlation is refreshed once.

## Out of Scope

Production code.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | — | 20261123-122903 | Changed: tests/agent/test_session_correlation_refresh.py |
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
- **Requirement ID**: `REQ-002` (atomic /clear new and /session load through the transition service)
- **Source issue**: issues/20261119-145300_cliplc002_session-transition-generation.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261122-232757_cliplc002_session-transition-generation.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261123-094714
- **Related target files**: `tests/agent/test_session_correlation_refresh.py`