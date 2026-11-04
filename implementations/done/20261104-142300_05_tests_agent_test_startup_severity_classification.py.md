## Goal
- Re-point the tests of `tests/agent/test_startup_severity_classification.py` that assert the moved config-only checks (`mcp_auth`, `routing_drift`, `routing_safety_tiers`) to the new config stage, and keep the runtime-stage tests on `_check_services` (`REQ-006`: tests whose harness drives the moved checks drive the new stage).

## Scope
**Release unit**: config-stage-split

- The harness helper and twelve tests of `TestCheckServicesSeverityClassification` in `tests/agent/test_startup_severity_classification.py`. The assertions are unchanged.

## Assumptions
- Execution order: this procedure runs after the production procedures of this Plan (earlier `seq`), and after the disabled-auth Plan's procedure for this file, which sets `is_disabled=False` on its token-less mocks; re-pointing does not touch those mock arguments.
- The module-level helper `_run_check_services(ctx, *, embedding_dims=None, **overrides)` builds a real orchestrator and validation pipeline, patches names in `agent.startup_validation` from a `mocks` dict plus `overrides`, patches `StartupValidationResult` so the created result is captured, and calls `startup._check_services()` (checked in Step 3a).
- After the production procedures, `StartupOrchestrator._check_config` (new) exists, is synchronous, and raises `RuntimeError("Startup validation failed: ...")` on a FATAL, like `_check_services`.
- The twelve config-only tests are `test_mcp_auth_fatal_when_any_server_missing_token`, `test_mcp_auth_ok_when_all_servers_have_token`, `test_mcp_auth_fatal_lists_all_offending_servers`, `test_routing_drift_warning_on_messages`, `test_routing_drift_emits_no_outcome_when_clean`, `test_routing_drift_unexpected_failure_is_fatal_when_strict`, `test_routing_drift_unexpected_failure_is_warning_when_not_strict`, `test_routing_drift_runtime_error_is_fatal_regardless_of_strict`, `test_routing_drift_unreadable_strictness_is_fatal`, `test_routing_safety_tiers_warning_on_messages`, `test_routing_safety_tiers_emits_no_outcome_when_clean`, and `test_routing_safety_tiers_unexpected_failure_is_fatal`. The `test_routing_drift_live_*` tests exercise tool discovery and stay on the runtime stage.
- Until this procedure runs, these twelve tests fail against the split: an allowed red state of the release unit.
- Step 2 start conditions held: the Plan is not gated and has no blocking Unknown; the overlap with the disabled-auth Plan is a recorded sequencing dependency.

## Design decisions
- Add a keyword `stage` to the existing helper and a thin wrapper `_run_check_config` (new), instead of copying the helper: the patch list is shared, and the tests change by one name each.
- The `stage == "config"` branch calls `startup._check_config()` synchronously inside the same `try`, so the captured exception and result behave like the runtime branch.

## Alternatives considered
N/A: the re-pointing approach is fixed by the Plan (Decision 1 and `REQ-006`).

## Implementation
### Target file
`tests/agent/test_startup_severity_classification.py`

### Procedure
1. Add the `stage` keyword to `_run_check_services` and branch the final call.
2. Add the wrapper `_run_check_config` (new) after the helper.
3. In the twelve tests above, replace the call `_run_check_services(` with `_run_check_config(`; leave every argument and assertion.

### Method
Signature, Before:

```python
async def _run_check_services(
    ctx: MagicMock,
    *,
    embedding_dims: int | None = None,
    **overrides: object,
) -> tuple[StartupValidationResult, Exception | None]:
```

After:

```python
async def _run_check_services(
    ctx: MagicMock,
    *,
    embedding_dims: int | None = None,
    stage: str = "services",
    **overrides: object,
) -> tuple[StartupValidationResult, Exception | None]:
```

Final call, Before:

```python
        try:
            await startup._check_services()
        except Exception as e:  # noqa: BLE001 — capturing for assertion, not swallowing silently
            exc = e
```

After:

```python
        try:
            if stage == "config":
                startup._check_config()
            else:
                await startup._check_services()
        except Exception as e:  # noqa: BLE001 — capturing for assertion, not swallowing silently
            exc = e
```

Wrapper (new), placed right after the helper:

```python
async def _run_check_config(
    ctx: MagicMock, **overrides: object
) -> tuple[StartupValidationResult, Exception | None]:
    """Run StartupOrchestrator._check_config() and return (captured result, exception or None)."""
    return await _run_check_services(ctx, stage="config", **overrides)
```

### Details
- Add one line to the helper's docstring: `stage` selects the config-only stage (`"config"`) or the runtime stage (`"services"`).
- Do not change the `mocks` dict, the patches, or any readiness, discovery, or RAG test.

## Compatibility considerations
N/A: test-only change.

## Security considerations
N/A: synthetic servers and placeholder tokens only.

## Rollback considerations
Revert the commit; this file is part of the release unit, so reverting only it leaves its twelve tests asserting the moved checks against the runtime stage.

## Validation plan
- `uv run pytest tests/agent/test_startup_severity_classification.py -q` passes in full (collected the file's tests).
- `uv run ruff format --check`, `uv run ruff check`, `uv run mypy --no-namespace-packages scripts/ tests/eventbus`, and `uv run python tools/check_suppression_justification.py` report no findings.

## Completion criteria
- The twelve tests assert the same outcomes through `_run_check_config`, and the runtime-stage tests still use `_run_check_services` (`AC-5`).
- The whole file passes.

## Out of Scope
- Production code, the twin tests in `tests/agent/test_startup.py`, and the new stage tests (separate procedures).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Edit the helper and re-point the tests as described in Implementation > Procedure/Method | Completed | 20261104-183306 | 20261104-183306 | — |
| 2 | Run the whole file and confirm it passes | Completed | 20261104-183306 | 20261104-183306 | — |
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
- **Requirement ID**: `REQ-006` (tests drive the new config stage)
- **Source issue**: `issues/20261031-135634_validorder001_config-validation-after-spawn.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261104-095930_validorder001_config-validation-after-spawn.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261104-142300
- **Related target files**: `tests/agent/test_startup_severity_classification.py`
