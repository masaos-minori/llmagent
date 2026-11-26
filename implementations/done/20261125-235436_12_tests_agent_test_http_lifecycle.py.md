## Goal

Add restart-refusal and port-conflict-prevention tests, PGID-failure retention tests, and record-ownership tests (REQ-001, REQ-004, REQ-005, REQ-011).

## Scope
**Release unit**: N/A: not part of a release unit (Phase 1 tests are outside R3-ownership)

## Assumptions
- This file is also targeted by cliplc006's pending procedure (`implementations/20261125-223712_10_tests_agent_test_http_lifecycle.py.md`, launch-spec scope); add this row's tests on top of that procedure, not in parallel (UNK-04).
- Phase 1 tests are expected to fail until Phases 3-4 land.

## Design decisions
- N/A: test row, no design decision of its own.

## Alternatives considered
- N/A.

## Implementation
### Target file
`tests/agent/test_http_lifecycle.py`

### Procedure
Add tests: restart over a live process raises `RestartBlockedError` (new) and starts no second process; PGID-failure retention keeps the record; record ownership releases only on confirmed exit.

### Method
Extend the existing manager test module; imports already cover the manager, launcher, and `TerminationOutcome` (`:14-19`).

### Details
- The port-conflict test asserts no `start()` call after an unconfirmed outcome (AC-2).

## Compatibility considerations
- N/A: test-only.

## Security considerations
- N/A.

## Rollback considerations
- N/A: revert the commit.

## Validation plan
- `uv run pytest tests/agent/test_http_lifecycle.py` — green after Phases 2-4 (AC-1, AC-2).

## Completion criteria
- The three defect-pinning groups are green and stay green as regression coverage.

## Out of Scope
- The implementation changes (rows 02, 03, 05).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 20261126-152500 | 20261126-153500 | Tests first, expected to fail until Phases 3-4 Changed files: tests/agent/test_http_lifecycle.py. Retargeted all private-dict sites to _records/ManagedProcessRecord (_make_record helper); TestGetPgidFailureTracking unconfirmed test renamed+rewritten to record retention (pgid None, EXIT_UNCONFIRMED state/outcome); TestRestartRefusal added: unconfirmed exit raises RestartBlockedError with start() never awaited (AC-2 port-conflict prevention) and record retained; confirmed-exit release path pinned. cliplc006 row-10 prerequisite confirmed already implemented and archived (done/) |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20261126-153600 | 20261126-133051 | Test row: validation is the pytest run pytest tests/agent/test_http_lifecycle.py: 15 passed. ruff/format clean. Full-suite run at end of batch End-of-batch full-suite run: 15103 passed, 5 skipped; coverage xml + diff-cover --compare-branch=master --fail-under=90: 93% (99 new lines, 6 missing). Allowed-red set fully retired |

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
- **Requirement ID**: REQ-001, REQ-004, REQ-005, REQ-011 (defect-pinning tests first)
- **Source issue**: issues/20261119-145305_cliplc007_mcp-process-ownership.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261125-232847_cliplc007_mcp-process-ownership.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261125-235436
- **Related target files**: `tests/agent/test_http_lifecycle.py`