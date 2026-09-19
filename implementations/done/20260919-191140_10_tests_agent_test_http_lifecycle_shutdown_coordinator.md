## Goal

Add tests for `ShutdownCoordinator.shutdown_all()` cleanup parity — verify REQ-001 before delegating.

## Scope

- **In-Scope**: Adding tests for `ShutdownCoordinator.shutdown_all()` cleanup parity
- **Out-of-Scope**: Changes to source code under `scripts/agent/`, adding tests for other lifecycle modules

## Assumptions

- `ShutdownCoordinator.shutdown_all()` will be modified to own `_http_procs` mutation (REQ-001)
- Tests must verify that the mutation happens before termination, matching `HttpServerLifecycleManager.shutdown_all()`'s current behavior

## Design decisions

- Add new tests rather than modifying existing ones — preserve existing test coverage
- Focus on verifying `_http_procs` mutation parity specifically

## Alternatives considered

- Modifying existing tests — rejected because adding new tests preserves existing coverage and makes the new requirements explicit

## Implementation

### Target file

tests/agent/test_http_lifecycle_shutdown_coordinator.py

### Procedure

Add tests for `ShutdownCoordinator.shutdown_all()` cleanup parity.

### Method

#### Step 1: Verify current test coverage

Read existing tests in `test_http_lifecycle_shutdown_coordinator.py` and identify which scenarios are already covered.

#### Step 2: Add _http_procs mutation parity test

Add a test that verifies `_http_procs` is mutated (popped) before termination when `ShutdownCoordinator.shutdown_all()` is called.

```python
def test_shutdown_all_mutates_http_procs_before_termination(self):
    """Verify _http_procs mutation occurs before termination (REQ-001)."""
    # Setup: create mock with _http_procs entries
    coordinator = ShutdownCoordinator(...)
    coordinator._http_procs = {"server1": mock_proc, "server2": mock_proc}
    
    # Call shutdown_all()
    coordinator.shutdown_all()
    
    # Assert: _http_procs is empty (mutation occurred)
    assert coordinator._http_procs == {}
```

#### Step 3: Add terminator parameter test

Add a test that verifies the `terminator` parameter works correctly as-is (REQ-002).

```python
def test_shutdown_all_uses_custom_terminator(self):
    """Verify terminator parameter works correctly (REQ-002)."""
    custom_terminator = MagicMock(spec=ProcessTerminator)
    coordinator = ShutdownCoordinator(...)
    
    coordinator.shutdown_all(terminator=custom_terminator)
    
    # Assert: custom_terminator was used instead of default
    custom_terminator.terminate.assert_called_once()
```

### Details

New tests to add:
1. `test_shutdown_all_mutates_http_procs_before_termination` — verifies REQ-001
2. `test_shutdown_all_uses_custom_terminator` — verifies REQ-002
3. `test_shutdown_all_cleanup_parity_with_http_lifecycle_manager` — verifies both methods produce same cleanup result

## Compatibility considerations

- Test-only changes — no impact on production code behavior
- New tests must work with both old and new implementations during transition

## Security considerations

- No security-relevant behavior changes — test infrastructure only

## Rollback considerations

- If test additions break further, revert and investigate root cause

## Validation plan

| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| ShutdownCoordinator.shutdown_all() | Integration: verify _http_procs mutation parity | `uv run pytest tests/agent/test_http_lifecycle_shutdown_coordinator.py -v` | All shutdown tests pass |
| Terminator parameter | Unit: verify terminator defaults correctly | Manual inspection of test | Default behavior verified |
| Full test suite | Regression — all http_lifecycle tests | `uv run pytest tests/agent/ -q --ignore=tests/integration/` | All tests pass |
| Type checking | Static analysis | `uv run mypy tests/agent/test_http_lifecycle_shutdown_coordinator.py` | Clean |
| Linting | Style check | `uv run ruff check tests/agent/test_http_lifecycle_shutdown_coordinator.py` | Clean |

## Completion criteria

- New tests added for `_http_procs` mutation parity (REQ-001)
- New tests added for terminator parameter (REQ-002)
- All tests pass after adding new assertions
- No behavioral regression — same inputs produce same outputs
- Type checker passes on modified test file
- Linter passes on modified test file

## Out of scope

- Changes to source code under `scripts/agent/`
- Adding tests for other lifecycle modules
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
- **Requirement ID**: REQ-001
- **Source issue**: issues/20260919-115306_refactor_002_consolidate_remaining_http_lifecycle_duplication_and_dead_code.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260919-120000_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260919-191140
- **Related target files**: tests/agent/test_http_lifecycle_shutdown_coordinator.py
