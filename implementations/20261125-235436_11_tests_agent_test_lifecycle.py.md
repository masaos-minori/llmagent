## Goal

Add new-state transition-table tests, invalid-transition no-mutation tests, and shutdown-suppression typed-error tests (REQ-006, REQ-007, REQ-008, REQ-011).

## Scope
**Release unit**: N/A: not part of a release unit (Phase 1 tests are outside R3-ownership)

## Assumptions
- Phase 1 tests are written first and are expected to fail until Phases 2-4 land (Plan Phase 1, release unit R3-ownership note).

## Design decisions
- Keep the pinned invalid pairs (`:685-696`, `FAILED -> RUNNING` and `STOPPED -> RUNNING`) green while adding the new-state tests.

## Alternatives considered
- N/A: test row, no design decision of its own.

## Implementation
### Target file
`tests/agent/test_lifecycle.py`

### Procedure
Add tests for the three new states and their transitions, for `_set_state` rejection without mutation, and for `EnsureSuppressedError`/`RestartSuppressedError` raises during shutdown.

### Method
Extend the existing transition-table test class and the router test class; imports already cover `LifecycleState`, `assert_valid_transition`, and the router (`:29-30`).

### Details
- The no-mutation test asserts the state is unchanged after an invalid transition (AC-3); the suppression tests assert typed raises (AC-4).

## Compatibility considerations
- N/A: test-only.

## Security considerations
- N/A.

## Rollback considerations
- N/A: revert the commit.

## Validation plan
- `uv run pytest tests/agent/test_lifecycle.py` — new tests green after Phases 2-4; pinned pairs still rejected.

## Completion criteria
- AC-3 and AC-4 are pinned by green tests; the pinned invalid pairs remain green.

## Out of Scope
- The implementation changes (rows 01, 06, 08).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | Tests first, expected to fail until Phases 2-4 |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | Test row: validation is the pytest run |

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
- **Requirement ID**: REQ-006, REQ-007, REQ-008, REQ-011 (defect-pinning tests first)
- **Source issue**: issues/20261119-145305_cliplc007_mcp-process-ownership.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261125-232847_cliplc007_mcp-process-ownership.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261125-235436
- **Related target files**: `tests/agent/test_lifecycle.py`
