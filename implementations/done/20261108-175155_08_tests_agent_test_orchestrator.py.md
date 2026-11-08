## Goal
Add an orchestrator startup routing test: constructing `Orchestrator` must invoke `recover_stale_attempts` as a no-argument facade call and must not call `get_connection` during startup recovery.

## Scope
**Release unit**: wfaudit015-full (asserts document 03's conversion; passes only after documents 01 and 03 land).

**Plan row implemented**: `plans/20261108-084011_wfaudit015_state-store-facade-bypass.md` Implementation Target Files row 8 (`tests/agent/test_orchestrator.py`, `REQ-002`/`REQ-005`; plan step 2).

**In scope**:
- New test class `TestOrchestratorStartupRecoveryRouting` (new) with `test_startup_recovery_no_arg_facade_call` (new), appended after the existing init-related test classes.

**Out of scope**:
- Existing tests and helpers (`_patch_workflow_loader`, `_make_orchestrator`, timeout/retry suites) — unchanged. `implementations/20261108-162804_02_tests_agent_test_orchestrator.py.md` (wfaudit008) patch retargets land first; this plan only adds a new test (plan Notes reconciliation).

**Dependencies (landing order)**: `162804_02` lands first; documents 01/03 land in the same unit before this test can pass.

## Assumptions
| ID | Assumption | Validation |
|---|---|---|
| A-001 | `Orchestrator.__init__` constructs `StateStore()` and immediately calls the recovery method, so patching the class records the startup call on the class-mock instance. | Verified (`orchestrator.py` L91-92) |
| A-002 | `_patch_workflow_loader()` (L173-205) already patches `agent.orchestrator.StateStore` but yields only the loader mock; adding a second, nested `patch("agent.orchestrator.StateStore")` in the new test shadows the helper's patch and exposes the class mock without editing the helper. | Verified (helper body) |
| A-003 | `_make_orchestrator` (L211-225) is the standard construction helper for init-path tests. | Verified (helper read) |

## Design decisions
| ID | Decision | Rationale |
|---|---|---|
| D-001 | Nested extra patch instead of changing `_patch_workflow_loader` to yield the store mock. | Helper edits would touch every existing caller (and collide with `162804_02`); a local patch keeps the addition isolated. |
| D-002 | Assert `recover_stale_attempts.assert_called_once_with()` (no args) and `get_connection.assert_not_called()` on the store instance. | Pins both halves of REQ-002/REQ-005: the facade shape and the absence of the raw-connection fetch. |

## Alternatives considered
| Alternative | Reason rejected |
|---|---|
| Real-DB startup test | Heavier fixture; the contract here is the call shape at the boundary, which the class mock asserts directly (mirrors the file's existing mock discipline). |
| Extend the helper to yield all mocks | Cross-cutting edit touching dozens of tests; out of scope for an add-only row. |

## Implementation
### Target file
`tests/agent/test_orchestrator.py` (plan target row 8).

### Procedure
Step 1: append `TestOrchestratorStartupRecoveryRouting` (new) after the last init-path test class. Step 2: implement the startup call-shape assertions.

### Method
Append-only class insertion reusing existing helpers (`_patch_workflow_loader`, `_make_orchestrator`).

### Details
Step 2 — test contract:
```python
class TestOrchestratorStartupRecoveryRouting:
    """Startup recovery must be a no-argument facade call (REQ-002/REQ-005)."""

    def test_startup_recovery_no_arg_facade_call(self) -> None:
        ctx = MagicMock()
        with (
            _patch_workflow_loader(),
            patch("agent.orchestrator.StateStore") as state_store_cls,
        ):
            _make_orchestrator(ctx)
        store_instance = state_store_cls.return_value
        store_instance.recover_stale_attempts.assert_called_once_with()
        store_instance.get_connection.assert_not_called()
```
The nested `patch("agent.orchestrator.StateStore")` is applied after the helper's own patch, so the code under construction binds to this mock; call history survives the context exit.

## Compatibility considerations
- Addition-only; no existing test or helper semantics change.
- Depends on documents 01/03 landing in the same unit (the no-argument facade call).

## Security considerations
N/A (test-only change).

## Rollback considerations
Revert with the wfaudit015-full unit.

## Validation plan
Run after documents 01-08 have landed (unit gate):
| Gate | Command | Expectation |
|---|---|---|
| Orchestrator suite | `uv run pytest tests/agent/test_orchestrator.py -q` | all green incl. the new test |
| New test detail | `uv run pytest tests/agent/test_orchestrator.py -q -k startup_recovery` | 1 test passes |
| Lint | `uv run ruff check tests/agent/test_orchestrator.py` | clean |

## Completion criteria
- `recover_stale_attempts` asserted called exactly once with no arguments during `Orchestrator` construction (REQ-002/REQ-005).
- `get_connection` asserted never called during startup (REQ-003 lock on this site).

## Out of Scope
- The orchestrator production edit (document 03).
- The engine routing tests (document 07).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Append `TestOrchestratorStartupRecoveryRouting` (new) with the startup call-shape test | Completed | 20261109 | 20261109 | Deviation D-003: see below |
| 2 | Run the unit validation gates | Completed | 20261109 | 20261109 | ruff clean; 131/131 pass incl. new test |

### Deviations from Procedure Snippet
| ID | Snippet (as written) | Actual | Reason |
|---|---|---|---|
| D-003 | `with (_patch_workflow_loader(), patch("agent.orchestrator.StateStore") as state_store_cls):` | `with patch("agent.orchestrator.StateStore") as state_store_cls:` (fixture line removed) | `_patch_workflow_loader` is `@pytest.fixture(autouse=True)`; calling it directly inside the test body raises "Fixtures are not meant to be called directly." It is already active for every test in the module, so the nested `patch` alone shadows it. Test failed until the fixture line was dropped. |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| 1 | Direct call of autouse fixture `_patch_workflow_loader()` in the test body (pytest deprecation error) | Yes | 20261109 |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| — | — | — | — | — | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| — | — | — | — | — | — |

## Traceability
- **Workflow phase**: plan-to-implementation-procedure
- **Requirement ID**: `REQ-002`, `REQ-005`
- **Source issue**: `issues/20261107-203228_wfaudit015_state-store-facade-bypass.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261108-084011_wfaudit015_state-store-facade-bypass.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261108-175155
- **Related target files**: `tests/agent/test_orchestrator.py`

<!-- tools/generate_workitem.py implementation-procedure timestamp: 20261108-175155 -->
