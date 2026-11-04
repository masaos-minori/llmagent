## Goal
- Add `run()`-level tests that the config stage runs before `_start_servers` and that a config FATAL aborts before any subprocess start without a rollback, and stub the new stage in the file's autouse fixture so the existing `run()` tests keep isolating the step they test (`REQ-005`: call-order and abort-before-spawn tests that fail on the pre-change code; `REQ-006`: `run()` tests stub the new stage).

## Scope
**Release unit**: N/A: not part of a release unit

- `tests/agent/test_startup_rollback.py` only: one fixture edit and a new test class. No production code; the existing tests are unchanged.

## Assumptions
- Execution order: the new tests assign `_check_config` as an instance attribute and the fixture stub uses `create=True`, so this procedure works before and after the production procedures; the executor SHOULD run it first (Plan Phase 1) to record the new tests failing on the pre-change code.
- The file's `_make_rollback_startup()` builds an orchestrator on `ctx = MagicMock()` with an `AsyncMock` lifecycle whose `shutdown_all` returns `[]`; existing tests replace `_start_servers`, `_check_services`, and `_setup_prompt` per instance and leave `_verify_mcp_health` real, which passes on the empty mock server dict (checked in Step 3a).
- Its autouse fixture `_stub_component_init` patches `ComponentInitializer.initialize` with `patch.object(...)` in a `with` block; the new stage stub is added to the same `with` block.
- After the production procedures, `run()` calls `self._check_config()` once before `_start_servers`; without the stub, the existing tests would execute the real stage on a `MagicMock` context.
- Step 2 start conditions held: the Plan is not gated and has no blocking Unknown; no cross-plan overlap names this file.

## Design decisions
- Stub with `patch.object(StartupOrchestrator, "_check_config", new=MagicMock(), create=True)`: `create=True` keeps the fixture valid before the method exists; the new order test asserts the stage is called once, so a renamed method is still caught.
- Record call order with a shared list appended by `side_effect` functions, so the order assertion does not rely on mock internals.

## Alternatives considered
N/A: the fixture seam is the one the Plan names; a per-test stub in every existing test would be a larger diff.

## Implementation
### Target file
`tests/agent/test_startup_rollback.py`

### Procedure
1. Extend the `with patch.object(ComponentInitializer, "initialize", ...)` block of `_stub_component_init` with the `_check_config` stub, and update its docstring sentence to name both seams.
2. Append a class `TestConfigStageOrdering` (new) with two async tests, using the file's `_make_rollback_startup()` and its autouse fixture.

### Method
Fixture, Before:

```python
        with patch.object(
            ComponentInitializer,
            "initialize",
            new=AsyncMock(return_value=(MagicMock(), MagicMock())),
        ):
            yield
```

After:

```python
        with (
            patch.object(
                ComponentInitializer,
                "initialize",
                new=AsyncMock(return_value=(MagicMock(), MagicMock())),
            ),
            patch.object(
                StartupOrchestrator, "_check_config", new=MagicMock(), create=True
            ),
        ):
            yield
```

New tests (names are new):
- `test_config_stage_runs_before_start_servers` (new): build the orchestrator with `_make_rollback_startup()`; set `orch._check_config`, `orch._start_servers`, `orch._verify_mcp_health`, `orch._check_services`, and `orch._setup_prompt` to mocks whose `side_effect` appends a label to a shared list; `await orch.run()`; the list equals the labels in the order config, start, verify, services, prompt.
- `test_config_failure_aborts_before_start_without_rollback` (new): set `orch._check_config = MagicMock(side_effect=RuntimeError("Startup validation failed: routing drift"))` and `orch._start_servers = AsyncMock()`; `pytest.raises(RuntimeError, match="Startup validation failed")` around `await orch.run()`; `orch._start_servers.assert_not_called()` and `mock_lifecycle.shutdown_all.assert_not_awaited()`.

### Details
- Import `MagicMock` is already present in the file; keep the existing tests, the helper, and the file docstring unchanged except the fixture docstring sentence.
- Do not assert on state the test assigned to a mock beyond the call order and the raised error.

## Compatibility considerations
N/A: test-only change.

## Security considerations
N/A: no credential, network, or process; everything is mocked.

## Rollback considerations
N/A: revert the commit.

## Validation plan
- Before the production procedures run: `uv run pytest tests/agent/test_startup_rollback.py -k TestConfigStageOrdering -q` shows both tests failing (the stage is never called, so the order list lacks the config label and no abort happens); record the output in the Failure Log.
- After them: the same command passes, and `uv run pytest tests/agent/test_startup_rollback.py -q` passes in full.
- `uv run ruff format --check`, `uv run ruff check`, and `uv run python tools/check_mock_patch_targets.py` report no findings.

## Completion criteria
- The order test shows config, start, verify, services, prompt for a valid run, and the abort test shows no `_start_servers` call and no `shutdown_all` await after a config FATAL (`AC-1`, `AC-2`, `AC-5`).
- Every existing `run()` test passes with the new stage stubbed.

## Out of Scope
- Production code and the other test files (separate procedures).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Edit the fixture and add the tests as described in Implementation > Procedure/Method | Completed | 20261104-183306 | 20261104-183306 | — |
| 2 | Run the new tests before the production change and record the failures, then run the whole file after | Completed | 20261104-183306 | 20261104-183306 | — |
| 3 | Run the validation sequence (`rules/toolchain.md`) and the Validation plan | Completed | 20261104-183306 | 20261104-183306 | release-unit end-of-unit suite+coverage+diff-cover green; ruff/mypy/bandit/lint-imports/check_module_size/check_mock_patch_targets/check_suppression_justification clean |

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
- **Requirement ID**: `REQ-005` (call-order and abort tests), `REQ-006` (`run()` tests stub the new stage)
- **Source issue**: `issues/20261031-135634_validorder001_config-validation-after-spawn.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261104-095930_validorder001_config-validation-after-spawn.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261104-142300
- **Related target files**: `tests/agent/test_startup_rollback.py`
