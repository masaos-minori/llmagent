## Goal

Make routing drift always FATAL in `startup_validation.py` by removing the `routing_drift_strict` read, the non-strict WARNING path and the `strict` argument of `_record_drift_check_failure` (REQ-001 strict-only startup); update the two startup-validation test files in the same change.

## Scope
**Release unit**: strict-only-startup

Edit `scripts/agent/startup_validation.py` and its companion tests `tests/agent/shared/test_startup_validation_pipeline.py` and `tests/agent/test_startup_validation.py`. `check_routing_drift` itself (`scripts/agent/services/routing_drift.py`) is not a Plan target.

## Assumptions

- Sequencing: the Plan's Phases 1-4 can land in any order within this file; the strict-key removal (Phase 1) ships in the `strict-only-startup` release unit, the `security_profile` removal is Phase 3 and the `allowed_root` rejection is Phase 4.
- `scripts/agent/services/routing_drift.py::check_routing_drift(ctx, *, strict=False)` and `scripts/agent/services/tool_validation.py::_check_tool_definitions(ctx, strict=False)` keep their `strict` parameter: they have their own tests (`tests/agent/test_startup_mcp_starter.py`, `tests/agent/test_repl_health.py`) and the REPL runtime check `check_tool_definitions_runtime` calls it with `strict=False`. Startup passes `strict=True`. Removing those parameters would be a Plan amendment (not a target here); recorded as a follow-up observation, not a blocker.
- The companion tests also contain `SecurityProfile`/`security_profile` references (`test_startup_validation.py` lines 23 and 31; `test_startup_validation_pipeline.py` lines 19, 71, 163, 262); those are removed in this document's test pass because AC-07 requires none in `tests/`. The `Mock` attribute assignment `ctx.cfg.mcp.security_profile = ...` is harmless before Phase 3 but must go before the `MCPConfig` field is removed.
- A hidden-ordering hazard: `check_config()` currently starts `drift_strict = True` so a failure while reading the setting fails closed; with no setting to read, that guard disappears and the call becomes unconditional `strict=True`.

## Design decisions

- `check_config()` calls `check_routing_drift(ctx, strict=True)`; a `RuntimeError` becomes `pipeline.add_fatal("routing_drift", str(exc))` as today, and any other exception becomes FATAL through `_record_drift_check_failure(pipeline, exc)`.
- The `for msg in check_routing_drift(...)` loop that adds WARNINGs stays: with `strict=True` it still logs/returns warnings only when there is no drift to raise on.

## Alternatives considered

Keeping `drift_strict = True` as a local constant was rejected: it keeps a dead variable and the `strict` keyword on the helper. Passing `strict=True` through a module constant was rejected as optionality without a user.

## Implementation
### Target file
`scripts/agent/startup_validation.py`

### Procedure
1. Change `_record_drift_check_failure` (line 56) to `(pipeline, exc)`: remove the `strict` keyword and the WARNING branch; always `pipeline.add_fatal("routing_drift", message)`. Rewrite its docstring to say the failure is always FATAL (an unknown result is not a clean result).
2. In `StartupValidator.check_config` (section `# 5. Routing drift (static)`, lines 144-157) delete the `drift_strict` variable and its comment, call `check_routing_drift(ctx, strict=True)`, and call `_record_drift_check_failure(pipeline, exc)`.
3. Rewrite the `except Exception` justification comment (line 156) so it no longer names `routing_drift_strict`; keep the `# noqa: BLE001 — ...` form that `tools/check_suppression_justification.py` requires.

### Method
- Edit by symbol; keep the `except RuntimeError` branch before `except Exception`.
- `rg -n "routing_drift_strict|drift_strict" scripts/agent/startup_validation.py` must return nothing afterwards.

### Details
- No new imports. `StartupValidationResult.add_warning` remains used elsewhere in the module.
- Behavior change to state in the docstring: before, an unexpected exception in the drift check was a WARNING when `routing_drift_strict` was false; now it is always FATAL.

### Companion test files
- `tests/agent/shared/test_startup_validation_pipeline.py`
  - Procedure: Delete `test_routing_drift_strict_false_warns_only` (line 114) and the strict-setting assignments (`tool_definitions_strict` and `routing_drift_strict` at lines 72, 104, 115, 164, 242, 263-264); rename `test_routing_drift_strict_true_raises_fatal` (line 103) to drop the strict wording from its name; remove the `SecurityProfile` import (line 19) and `security_profile` assignments (lines 71, 163, 262).
  - Validation: `uv run pytest tests/agent/shared/test_startup_validation_pipeline.py -v`
- `tests/agent/test_startup_validation.py`
  - Procedure: Delete `test_non_strict_drift_is_warning` (line 151) and rename `test_strict_drift_is_fatal` (line 121) to `test_routing_drift_is_fatal` (new); drop the strict assignments (lines 33, 125, 154) and the `SecurityProfile` import and assignment (lines 23, 31); add a case where the drift check raises a non-`RuntimeError` and assert a FATAL `routing_drift` result.
  - Validation: `uv run pytest tests/agent/test_startup_validation.py -v`

## Compatibility considerations

Behavior change: a routing drift or an unexpected drift-check failure aborts startup unconditionally. The shipped `config/agent.toml` already set `routing_drift_strict = true`, so deployed behavior is unchanged.

## Security considerations

Removes a path that downgraded a safety finding to WARNING (ADR-003 routing authority). Strictly tightens startup; nothing is relaxed.

## Rollback considerations

`git revert`; the config key removal ships in the same release unit, so revert both together.

## Validation plan

- `uv run pytest tests/agent/test_startup_validation.py tests/agent/shared/test_startup_validation_pipeline.py tests/agent/test_startup_severity_classification.py -v` (the severity file has its own Plan row).
- `uv run ruff format` and `uv run ruff check` on the three files; `uv run mypy --no-namespace-packages scripts/`.
- `uv run python tools/check_suppression_justification.py`.

## Completion criteria

- No `routing_drift_strict` or `drift_strict` text remains in the source file.
- `_record_drift_check_failure` always records FATAL.
- Both companion tests assert FATAL only and contain no `SecurityProfile` or strict-setting references.

## Out of Scope

- `routing_drift.py` and `tool_validation.py` signatures (see Assumptions).
- Other startup test files (own Plan rows: `test_startup.py`, `test_startup_severity_classification.py`, `test_startup_mcp_lifecycle.py`, and others).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Simplify `_record_drift_check_failure` and the `check_config` drift section | Pending | — | — | REQ-001 |
| 2 | Update the companion tests (pipeline and validation): remove non-strict cases and `SecurityProfile` references; add the non-`RuntimeError` FATAL case | Pending | — | — | REQ-001, REQ-007 |
| 3 | Run ruff, mypy, suppression check and the three startup test files | Pending | — | — |  |

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
- **Requirement ID**: `REQ-001`
- **Source issue**: issues/20261109-112640_adrrev004_non-strict-bypass-removal.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261110-094140_adrrev004_non-strict-bypass-removal.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261110-154603
- **Related target files**: `scripts/agent/startup_validation.py`, `tests/agent/shared/test_startup_validation_pipeline.py`, `tests/agent/test_startup_validation.py`
