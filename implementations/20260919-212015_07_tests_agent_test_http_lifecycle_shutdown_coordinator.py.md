## Goal
Update the Mock-based `mock_manager` fixture and its one dependent test so they keep
verifying `ShutdownCoordinator.shutdown_all()`'s stderr-path-clearing behavior after
Step 03 of this pass changes the real call site from `manager._stderr_log_paths.clear()`
to `manager._stderr_log_manager.clear()` (`REQ-001`).

## Scope
- In scope: the `mock_manager` fixture (current lines 13-22) and
  `test_shutdown_all_clears_internal_state` (current lines 37-50) — the only test in
  this file that references `_stderr_log_paths` (confirmed via
  `rg "_stderr_log_paths" tests/agent/test_http_lifecycle_shutdown_coordinator.py`,
  three matches: lines 19, 41, 49, all inside these two locations).
- Out of scope: every other test/fixture in this file
  (`test_shutdown_all_uses_caller_supplied_terminator` and beyond) — unchanged.

## Assumptions
- Step 03 of this pass
  (`implementations/20260919-212015_03_scripts_agent_http_lifecycle_shutdown_coordinator.py.md`)
  changes `ShutdownCoordinator.shutdown_all()`'s one call site from
  `manager._stderr_log_paths.clear()` to `manager._stderr_log_manager.clear()`.
- Without this update, `test_shutdown_all_clears_internal_state`'s current assertion
  (`assert mock_manager._stderr_log_paths == {}`, line 49) would keep passing
  vacuously after Step 03 — the mock's `_stderr_log_paths` dict would simply never be
  touched by the (now-changed) real code path, so the assertion would trivially hold
  without exercising anything (this exact risk is documented in
  `plans/20260919-211529_plan.md` Risks).

## Design decisions
- Replace the fixture's `mgr._stderr_log_paths = {}` (line 19) with
  `mgr._stderr_log_manager = Mock()` — since `mock_manager` is a bare `Mock()`
  (line 15), any attribute access it hasn't been given explicitly would otherwise
  auto-vivify as a `Mock()` already; setting it explicitly here documents the
  fixture's intent and gives the test a concrete `Mock` object whose `.clear()` calls
  can be asserted.
- Replace the fixture-seeding line
  `mock_manager._stderr_log_paths["server1"] = "/tmp/server1.stderr.log"` (line 41):
  delete it entirely — there is no dict left to seed, and this test does not verify
  the log path's *value*, only that clearing happens.
  Replace the assertion `assert mock_manager._stderr_log_paths == {}` (line 49) with
  `mock_manager._stderr_log_manager.clear.assert_called_once()` — this directly
  verifies the real `ShutdownCoordinator.shutdown_all()` code path calls
  `manager._stderr_log_manager.clear()` exactly once, which is what this test's name
  (`test_shutdown_all_clears_internal_state`) means to verify.

## Alternatives considered
- Give `mock_manager._stderr_log_manager` a real (non-`Mock`) `dict`-backed fake with
  its own `.clear()` method that empties it, then assert the dict is empty afterward
  (closer to the original assertion shape): rejected — `unittest.mock.Mock.clear`
  called-once assertion is simpler, directly verifies the call happened (not just that
  *some* state ended up empty, which could pass by coincidence if the code path
  changed to not call `.clear()` at all but the dict started empty), and matches how
  this same fixture already uses plain `Mock()`/`AsyncMock()` for other collaborators
  (`_process_terminator`, line 21).

## Implementation
### Target file
tests/agent/test_http_lifecycle_shutdown_coordinator.py

### Procedure
1. Replace `mgr._stderr_log_paths = {}` (current line 19) in the `mock_manager`
   fixture.
2. Delete the fixture-seeding line (current line 41) in
   `test_shutdown_all_clears_internal_state`.
3. Replace the assertion (current line 49) in the same test.

### Method
`mock_manager` fixture (replaces current lines 14-22):
```python
@pytest.fixture
def mock_manager(self):
    mgr = Mock()
    mgr._http_procs = {}
    mgr._http_pgids = {}
    mgr._stderr_files = {}
    mgr._stderr_log_manager = Mock()
    mgr._last_health_check = {}
    mgr._process_terminator = AsyncMock()
    return mgr
```

`test_shutdown_all_clears_internal_state` (replaces current lines 37-50):
```python
async def test_shutdown_all_clears_internal_state(self, mock_manager, mock_proc, mock_stderr_fh):
    mock_manager._http_procs["server1"] = mock_proc
    mock_manager._http_pgids["server1"] = 1234
    mock_manager._stderr_files["server1"] = mock_stderr_fh
    mock_manager._last_health_check["server1"] = time.monotonic()

    coord = ShutdownCoordinator()
    await coord.shutdown_all(mock_manager)

    assert mock_manager._http_pgids == {}
    assert mock_manager._stderr_files == {}
    mock_manager._stderr_log_manager.clear.assert_called_once()
    assert mock_manager._last_health_check == {}
```

### Details
No new imports required — `Mock` is already imported (current line 4:
`from unittest.mock import AsyncMock, MagicMock, Mock`).

## Compatibility considerations
N/A: test-only file. The test still verifies the same real behavior
(`shutdown_all()` clears stderr-path tracking) — only the observation mechanism
changes from a dict-emptiness check to a call-was-made check, made necessary by the
production call site itself changing in Step 03.

## Security considerations
N/A: test file only, fully mocked collaborators.

## Rollback considerations
Revert this file's diff. Apply together with Step 03 of this pass (per
`plans/20260919-211529_plan.md` Implementation steps, Phase 2) — reverting this file
alone without reverting Step 03 would leave the test passing vacuously again (the
exact risk this step exists to close).

## Validation plan
- `uv run pytest tests/agent/test_http_lifecycle_shutdown_coordinator.py -v` — full
  file must pass, including the updated fixture and test.
- `rg "_stderr_log_paths" tests/agent/test_http_lifecycle_shutdown_coordinator.py` —
  must return no matches after this change.

## Completion criteria
- `mock_manager` fixture sets `_stderr_log_manager = Mock()` instead of
  `_stderr_log_paths = {}`.
- `test_shutdown_all_clears_internal_state` asserts
  `mock_manager._stderr_log_manager.clear.assert_called_once()` instead of dict
  emptiness.
- `uv run pytest tests/agent/test_http_lifecycle_shutdown_coordinator.py -v` passes.

## Out of scope
- `test_shutdown_all_uses_caller_supplied_terminator` and any other test in this file.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | |
| 2 | Add or update tests per Validation plan | Pending | — | — | This document's Implementation step 1 is itself the test update |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Pending | — | — | N/A: test-only file |

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
- **Requirement ID**: `REQ-001` (update the Mock-based shutdown-coordinator test to match the new call site)
- **Source issue**: issues/20260919-210241_refactor_003_deduplicate-stderr-path-tracking-and-cleanup-logic-in-http_lifecycle.py.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260919-211529_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260919-212015
- **Related target files**: tests/agent/test_http_lifecycle_shutdown_coordinator.py
