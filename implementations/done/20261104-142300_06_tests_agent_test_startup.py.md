## Goal
- Re-point the tests of `tests/agent/test_startup.py` that assert the moved config-only checks to the new config stage, and keep the runtime-stage tests on `_check_services` (`REQ-006`: tests whose harness drives the moved checks drive the new stage).

## Scope
**Release unit**: config-stage-split

- The duplicated harness helper and nine tests in `tests/agent/test_startup.py` (seven in `TestCheckServicesSeverityClassification`, two in `TestCheckServicesFatalErrorMessageWithRemediation`). The assertions are unchanged.

## Assumptions
- Execution order: this procedure runs after the production procedures of this Plan (earlier `seq`), and after the disabled-auth Plan's procedure for this file, which sets `is_disabled=False` on token-less mocks; re-pointing does not touch those mock arguments.
- The helper `_run_check_services(ctx, *, embedding_dims=None, **overrides)` in this file is a duplicate of the one in `tests/agent/test_startup_severity_classification.py`: same patches, same final `await startup._check_services()` call (checked in Step 3a).
- The nine tests are `test_mcp_auth_fatal_when_any_server_missing_token`, `test_mcp_auth_ok_when_all_servers_have_token`, `test_mcp_auth_fatal_lists_all_offending_servers`, `test_routing_drift_warning_on_messages`, `test_routing_drift_emits_no_outcome_when_clean`, `test_routing_safety_tiers_warning_on_messages`, `test_routing_safety_tiers_emits_no_outcome_when_clean`, `test_fatal_error_message_includes_remediation`, and `test_fatal_error_message_format_with_multiple_outcomes`; the last two assert a FATAL that comes from `mcp_auth`, so they follow it into the config stage. The `test_routing_drift_live_*`, readiness, discovery, and RAG tests stay on the runtime stage.
- Until this procedure runs, these nine tests fail against the split: an allowed red state of the release unit.
- Step 2 start conditions held: the Plan is not gated and has no blocking Unknown; the overlap with the disabled-auth Plan is a recorded sequencing dependency.

## Design decisions
- Apply the same helper change as the twin file (a `stage` keyword plus a thin wrapper `_run_check_config` (new)), so the two duplicated harnesses stay consistent.

## Alternatives considered
N/A: fixed by the Plan (`REQ-006`); deduplicating the two harnesses is out of scope.

## Implementation
### Target file
`tests/agent/test_startup.py`

### Procedure
1. Add the `stage` keyword to `_run_check_services` and branch the final call.
2. Add the wrapper `_run_check_config` (new) after the helper.
3. In the nine tests above, replace the call `_run_check_services(` with `_run_check_config(`; leave every argument and assertion.

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
- Add one line to the helper's docstring that `stage` selects the config-only stage (`"config"`) or the runtime stage (`"services"`).
- Leave the remediation text assertion in `test_fatal_error_message_includes_remediation` as it is; the message comes from the same helper.

## Compatibility considerations
N/A: test-only change.

## Security considerations
N/A: synthetic servers and placeholder tokens only.

## Rollback considerations
Revert the commit; this file is part of the release unit, so reverting only it leaves its nine tests asserting the moved checks against the runtime stage.

## Validation plan
- `uv run pytest tests/agent/test_startup.py -q` passes in full (collected the file's tests).
- `uv run ruff format --check`, `uv run ruff check`, `uv run mypy --no-namespace-packages scripts/ tests/eventbus`, and `uv run python tools/check_suppression_justification.py` report no findings.

## Completion criteria
- The nine tests assert the same outcomes and messages through `_run_check_config`, and the runtime-stage tests still use `_run_check_services` (`AC-5`).
- The whole file passes.

## Out of Scope
- Production code, the twin tests in `tests/agent/test_startup_severity_classification.py`, and the new stage tests (separate procedures).

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
- **Related target files**: `tests/agent/test_startup.py`
