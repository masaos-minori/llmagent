## Goal
- Add tests, driving the real `StartupValidationPipeline`, that the config-only stage reports a strict routing drift and a safety-tier failure as FATAL, shows a non-strict drift as a WARNING, runs all four checks together, and passes cleanly for a valid configuration, and that the runtime stage no longer runs the config-only checks (`REQ-005`: new tests fail on the pre-change code and pass after it; `REQ-006`: the file's harness is limited to the runtime stage).

## Scope
**Release unit**: N/A: not part of a release unit

- New test code in `tests/agent/test_startup_validation.py`. The existing tests and helper behavior stay as they are; no production code.

## Assumptions
- Execution order: this procedure depends on no existing name other than the new method `check_config` (new), which the tests call on a real pipeline, so the executor SHOULD run it first (Plan Phase 1) to record the new tests failing on the pre-change code, then run the release-unit procedures.
- `check_config` (new) is a synchronous method of `StartupValidationPipeline` returning a `StartupValidationResult`; it reads `ctx.cfg.mcp.mcp_servers`, `ctx.cfg.tool.routing_drift_strict`, and the module-level `check_routing_drift`, `check_routing_safety_tiers`, and `_check_component_mandatoriness` of `agent.startup_validation`, which the tests patch (checked in Step 3a).
- The file's `_make_ctx()` leaves `ctx.cfg.mcp.mcp_servers` a `MagicMock` (iterating it yields nothing) and does not set `routing_drift_strict`; each new test sets what it needs.
- The existing helper `_run_check_services(rag_service, *, wait_for_side_effect=None)` drives the runtime stage with the config-only checks patched to a clean pass; it stays valid after the split because the patched names remain importable.
- Step 2 start conditions held: the Plan is not gated and has no blocking Unknown; the overlap with the disabled-auth Plan is a recorded sequencing dependency.

## Design decisions
- Test `check_config` directly (no orchestrator) with a small helper `_run_check_config` (new) that builds the pipeline on a context and patches the three module-level names with clean defaults overridable per test.
- One regression test pins the runtime stage: with the clean helper `_run_check_services`, the patched `check_routing_drift` is never called and no `mcp_auth` outcome exists.

## Alternatives considered
N/A: the cases are fixed by the Plan's Tests section.

## Implementation
### Target file
`tests/agent/test_startup_validation.py`

### Procedure
1. Append the helper `_run_check_config` (new) after the existing helpers.
2. Append a class `TestCheckConfigStage` (new) with the tests below.
3. Add the one runtime-stage regression test to the same class.

### Method
- Helper `_run_check_config(ctx, **overrides)` (new): patch `agent.startup_validation.check_routing_drift`, `check_routing_safety_tiers` (each a `MagicMock(return_value=[])` by default) and `_check_component_mandatoriness` (a `MagicMock()` by default) with `overrides` replacing any of them by name; return `StartupValidationPipeline(ctx, MagicMock()).check_config()`.
- `test_strict_drift_is_fatal` (new): `ctx.cfg.tool.routing_drift_strict = True`, `check_routing_drift` raising `RuntimeError("Strict mode: routing drift detected")`; the result has a FATAL outcome with source `routing_drift`.
- `test_safety_tier_failure_is_fatal` (new): `check_routing_safety_tiers` raising `RuntimeError("tier missing")`; FATAL with source `routing_safety_tiers`.
- `test_non_strict_drift_is_warning` (new): `routing_drift_strict = False`, `check_routing_drift` returning one message; one WARNING outcome with source `routing_drift`, and `has_fatal` is false.
- `test_valid_config_passes_cleanly` (new): real or `MagicMock` servers with tokens and clean mocks; no FATAL, no WARNING, and an OK `mcp_auth` outcome.
- `test_config_checks_report_together_without_short_circuit` (new): an enabled token-less `MagicMock(auth_token="", is_disabled=False)` server and a failing `check_routing_drift`; both a FATAL `mcp_auth` and a FATAL `routing_drift` outcome are present.
- `test_runtime_stage_no_longer_runs_config_checks` (new): with `_run_check_services` and `check_routing_drift` replaced by a recording mock, the mock is not called and no outcome has source `mcp_auth` or `routing_drift`. This test needs a way to see the mock: build the mock in the test and patch `agent.startup_validation.check_routing_drift` around the call, as the helper does, instead of passing it through the helper.

### Details
- Do not edit `TestRagConsistencyTimeout`, the posture-gate test, or the existing helpers.
- Use no real token or environment value; server keys are synthetic.

## Compatibility considerations
N/A: test-only change.

## Security considerations
N/A: synthetic servers and empty or placeholder tokens only.

## Rollback considerations
N/A: revert the commit.

## Validation plan
- Before the production procedures run: `uv run pytest tests/agent/test_startup_validation.py -k TestCheckConfigStage -q` shows the tests failing (`check_config` is missing, and the runtime-stage test sees the checks still called); record the output in the Failure Log.
- After them: the same command passes with six tests collected, and `uv run pytest tests/agent/test_startup_validation.py -q` passes in full.
- `uv run ruff format --check`, `uv run ruff check`, `uv run python tools/check_mock_patch_targets.py`, and `uv run python tools/check_suppression_justification.py` report no findings.

## Completion criteria
- The six tests exist and pass after the production change, and were seen failing on the pre-change code (`AC-2`, `AC-3`, `AC-5`).
- The existing tests of the file still pass.

## Out of Scope
- Production code, the orchestrator call-order tests, and the other test files (separate procedures).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Write the helper and the tests as described in Implementation > Procedure/Method | Completed | 20261104-183306 | 20261104-183306 | — |
| 2 | Run the new tests before the production change and record the failures, then run them after | Completed | 20261104-183306 | 20261104-183306 | — |
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
- **Requirement ID**: `REQ-005` (new stage tests), `REQ-006` (harness limited to the runtime stage)
- **Source issue**: `issues/20261031-135634_validorder001_config-validation-after-spawn.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261104-095930_validorder001_config-validation-after-spawn.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261104-142300
- **Related target files**: `tests/agent/test_startup_validation.py`
