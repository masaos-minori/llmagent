## Goal
Add unmocked tests of `_check_component_mandatoriness()` in `tests/agent/test_startup_validation.py` so ADR-004 INV-14 (Deployment-Blocking) has a test that fails if the startup abort path regresses (`REQ-005` / `AC-5`).

## Scope
**Release unit**: N/A: not part of a release unit

## Assumptions
- Every existing test patches `_check_component_mandatoriness` with a `MagicMock` (`_run_check_config` default and the `check_services` helpers), so the abort path is untested (checked against current source).
- `check_config()` runs the check against `ctx.cfg.mcp.mcp_servers`; a minimal `MagicMock` context is enough (UNK-06 resolved by the existing `_make_ctx()` / `_run_check_config` pattern); if that proves infeasible, stop and amend the Plan to move the test beside `tests/agent/test_startup.py`.
- Overlap: `plans/20261112-120011_rmcompat003_rag-corpus-identity-decision.md` edits the `identity-unverified` assertions (about lines 245-281) of the same file; this document only appends a new test class — compatible, any order.

## Design decisions
- Call the real `_check_component_mandatoriness` through `StartupValidationPipeline(ctx, MagicMock()).check_config()` with only `load_component_mandatoriness` patched, so the fatal source label and message are asserted end to end.
- Assert the source label (`component_mandatoriness`) and message fragment only, never the registry file content (avoids brittleness).

## Alternatives considered
N/A: the Plan fixes the approach for this row.

## Implementation
### Target file
`tests/agent/test_startup_validation.py`

### Procedure
1. Run `uv run python tools/check_adr_invariant_matrix.py` and record the baseline (UNK-05).
2. Add `class TestComponentMandatorinessAbort` with unmocked cases: unknown configured server, registry load failure (`ComponentMandatorinessError` and `FileNotFoundError`), consistent registry.
3. Write the tests first, show them failing against a deliberately broken check (comment out the `add_fatal` call locally), restore, then show them passing.

### Method
- Helper: reuse `_run_check_config` with `_check_component_mandatoriness` removed from the mocks (pass the override as the real function: `_check_component_mandatoriness=<imported real function>`), and patch `agent.startup_validation.load_component_mandatoriness`.
- Unknown server: registry from registry fixtures of `tests/shared/test_component_mandatoriness.py` without the configured key; servers `{"ghost": MagicMock(required=True)}`; expect one fatal under `component_mandatoriness`.
- Load failure: `side_effect=ComponentMandatorinessError("bad")` then `FileNotFoundError("missing")`; expect a fatal containing `Undeterminable component mandatoriness`.
- Consistent registry: server key present with the registered `required` value; expect no `component_mandatoriness` fatal.

### Details
- Source behavior: `scripts/agent/startup_validation.py` `_check_component_mandatoriness` adds the fatals above; `ProductionConfigValidator.validate_against_registry` (`scripts/agent/production_config_validator.py`) returns the conflict and unknown-server messages.
- Patch target is the import site `agent.startup_validation.load_component_mandatoriness`, per `tools/check_mock_patch_targets.py`.
- Existing tests, including `tests/shared/test_mcp_config.py::TestRequiredDefault`, run unchanged.

## Compatibility considerations
N/A: test-only addition; no existing test behavior changes.

## Security considerations
N/A: asserts an existing fail-fast gate; no new authorization.

## Rollback considerations
N/A: revert the commit.

## Validation plan
- `uv run pytest tests/agent/test_startup_validation.py tests/shared/test_component_mandatoriness.py tests/shared/test_mcp_config.py tests/eventbus -v` — pass.
- `uv run ruff format`, `uv run ruff check`, `uv run mypy` on the file; `uv run python tools/check_mock_patch_targets.py` — pass.

## Completion criteria
- A test fails if `_check_component_mandatoriness()` stops adding a fatal for an unknown server or a missing/invalid registry.
- A consistent registry adds no fatal; all existing tests still pass.

## Out of Scope
- Changing `scripts/agent/startup_validation.py`; editing the ADR text (rows 04 to 08 of this Plan's procedures).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Write the unmocked tests first and show them failing against a deliberately broken check | Pending | — | — | |
| 2 | Make the tests pass; run `uv run pytest tests/agent/test_startup_validation.py tests/shared/test_component_mandatoriness.py tests/shared/test_mcp_config.py -v` | Pending | — | — | |
| 3 | Run the validation sequence (`rules/toolchain.md`): ruff format/check, mypy, `tools/check_mock_patch_targets.py` | Pending | — | — | |

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
- **Requirement ID**: `REQ-005` — prove that startup aborts for an undefined component mandatoriness (ADR-004 INV-14)
- **Source issue**: issues/20261109-113220_adrrev015_adr-index-matrix.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261111-104147_adrrev015_adr-index-matrix.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261112-123307
- **Related target files**: `tests/agent/test_startup_validation.py`
