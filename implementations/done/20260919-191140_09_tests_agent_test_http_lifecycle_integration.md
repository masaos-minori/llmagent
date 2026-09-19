## Goal

Update integration tests for delegation-order change implied by REQ-003 — ensure shutdown tests observe correct cleanup order after `HttpServerLifecycleManager.shutdown_all()` delegates to `ShutdownCoordinator.shutdown_all()`.

## Scope

- **In-Scope**: Updating integration tests to reflect delegation-order change
- **Out-of-Scope**: Adding new unit tests for extracted functions (REQ-010), changes to source code under `scripts/agent/`

## Assumptions

- The delegation-order change means `_http_procs` mutation now occurs in `ShutdownCoordinator.shutdown_all()` instead of `HttpServerLifecycleManager.shutdown_all()`
- Tests that previously verified `_http_procs` mutation in `HttpServerLifecycleManager.shutdown_all()` need to be updated to verify it in `ShutdownCoordinator.shutdown_all()`

## Design decisions

- Update existing assertions rather than adding new ones — minimize test surface area
- Keep test names unchanged where possible to maintain traceability

## Alternatives considered

- Adding entirely new tests instead of updating existing ones — rejected because it increases maintenance burden without adding value

## Implementation

### Target file

tests/agent/test_http_lifecycle_integration.py

### Procedure

Update integration tests to reflect delegation-order change implied by REQ-003.

### Method

#### Step 1: Identify affected tests

Search for tests that verify `_http_procs` mutation or shutdown cleanup order. These are the tests that need updating.

#### Step 2: Update affected tests

For each affected test:
- Move assertions about `_http_procs` mutation from `HttpServerLifecycleManager.shutdown_all()` to `ShutdownCoordinator.shutdown_all()`
- Ensure the test still verifies the same behavioral contract (cleanup parity)

### Details

Affected tests likely include:
- Tests that assert `_http_procs` is empty after shutdown
- Tests that verify shutdown cleanup order
- Tests that verify SIGTERM→SIGKILL process iteration

Example update pattern:
```python
# Before: assertion on HttpServerLifecycleManager
assert mgr._http_procs == {}

# After: assertion on ShutdownCoordinator
assert mgr._shutdown_coordinator._http_procs == {}
```

## Compatibility considerations

- Test-only changes — no impact on production code behavior
- Test assertions must match the new delegation path

## Security considerations

- No security-relevant behavior changes — test infrastructure only

## Rollback considerations

- If test updates break further, revert to original assertions and investigate root cause

## Validation plan

| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| Integration tests | Regression — all http_lifecycle integration tests | `uv run pytest tests/agent/test_http_lifecycle_integration.py -v` | All tests pass |
| Full test suite | Regression — all http_lifecycle tests | `uv run pytest tests/agent/ -q --ignore=tests/integration/` | All tests pass |
| Type checking | Static analysis | `uv run mypy tests/agent/test_http_lifecycle_integration.py` | Clean |
| Linting | Style check | `uv run ruff check tests/agent/test_http_lifecycle_integration.py` | Clean |

## Completion criteria

- All integration tests pass after updating for delegation-order change
- Assertions correctly reference `ShutdownCoordinator` for `_http_procs` mutation
- No behavioral regression — same inputs produce same outputs
- Type checker passes on modified test file
- Linter passes on modified test file

## Out of scope

- Adding new unit tests for extracted functions (REQ-010)
- Changes to source code under `scripts/agent/`
- Deciding whether `ProcessSnapshotProvider` should be wired up (separate issue)

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | |
| 2 | Add or update tests per Validation plan | Pending | — | — | |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Pending | — | — | |

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
- **Requirement ID**: REQ-009
- **Source issue**: issues/20260919-115306_refactor_002_consolidate_remaining_http_lifecycle_duplication_and_dead_code.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260919-120000_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260919-191140
- **Related target files**: tests/agent/test_http_lifecycle_integration.py
