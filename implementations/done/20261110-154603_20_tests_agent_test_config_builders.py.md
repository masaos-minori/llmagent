## Goal
Update `tests/agent/test_config_builders.py` for builders without the strict keys, without `security_profile`, and with an `allowed_root` that must be non-empty (`REQ-001`, `REQ-007`, `REQ-003` consequence).

## Scope
**Release unit**: strict-only-startup


## Assumptions
- Builder documents make `_build_approval_config()` raise `ValueError` for an empty or absent `allowed_root` (message names the key) and `build_agent_config()` stop computing `security_profile_val`; this document asserts with `pytest.raises(ValueError, match="allowed_root")`, which fits either exception subclass the builder document picks.
- `_MIN_CFG` (line 37) lacks `allowed_root`; every `build_agent_config({**_MIN_CFG, ...})` and `_build_approval_config(cfg)` call would fail the new rejection, so `_MIN_CFG` gets `"allowed_root": "/opt/llm"`.
- Plan wording gap (no extra file): this row's Plan text says "strict toggles" and cites REQ-001, but the file also uses `security_profile`/`SecurityProfile`, which `AC-07` requires to be absent from `tests/`; the same edit removes them. No additional target file is involved.

## Design decisions
- Keep builder behavior cases; remove cases only about removed keys; make the defaults test pass an explicit `allowed_root` and add separate rejection tests.

## Alternatives considered
Making the builder default `allowed_root` to a path was rejected: the Plan requires the empty value to fail at load.

## Implementation
### Target file
`tests/agent/test_config_builders.py`

### Procedure
- Remove the `from shared.mcp_config import SecurityProfile` import (line 32) and `"tool_definitions_strict"`/`"routing_drift_strict"` from `_TOOL_DEFAULTS` (lines 148-149) and the override test (186-187).
- Remove the two keys from every `build_agent_config` dict (about lines 409-420, 450-451, 468-469, 478-479, 488-489, 499-500, 744-745, 772-773).
- Rename `test_system_prompt_tool_and_security_profile_propagate` (line 444) to `test_system_prompt_tool_propagates` (new) and drop the `security_profile` key and the `SecurityProfile.PRODUCTION` assertion (line 456); drop the `security_profile` key from `test_production_validation_passes_without_exit_when_strict_flags_set` (line 460-470, rename without "strict_flags") and from `test_production_validation_errors_raises` (line 508-511) with their comments; reword the docstring at line 551 that mentions `security_profile_val`.
- Add `"allowed_root": "/opt/llm"` to `_MIN_CFG`; change `TestBuildApprovalConfig` defaults test (line 275) to `_build_approval_config({"allowed_root": "/opt/llm"})` and its assertion at line 328 to `/opt/llm`; add `allowed_root` to the dict at line 334.
- Add `test_empty_allowed_root_rejected` (new) and `test_absent_allowed_root_rejected` (new) on `_build_approval_config`, and `test_removed_keys_rejected_by_build_agent_config` (new) parametrized over `tool_definitions_strict`, `routing_drift_strict`, `security_profile` expecting `ConfigReloadValidationError` (unknown key via the validator).

### Method
- The `test_production_validation_errors_raises` case patches `ProductionConfigValidator.validate`; keep the patch, only the config dict changes.

### Details
- `TestEmptyStringFallbackIdioms` (line ~760) passes `_MIN_CFG`; it keeps working once `_MIN_CFG` has `allowed_root`.

## Compatibility considerations
Test-only; depends on the builder, dataclass, validator and registry documents (release unit).

## Security considerations
Adds coverage that an empty `allowed_root` fails at load; removes no coverage of enforced checks.

## Rollback considerations
N/A: revert the commit

## Validation plan
- `uv run pytest tests/agent/test_config_builders.py -v`
- `uv run ruff format` and `uv run ruff check` on the file
- `uv run mypy --no-namespace-packages scripts/ tests/eventbus tools`
- `uv run pytest tests/agent tests/shared tests/integration -v` (full Phase 5 pass once every document is implemented)

## Completion criteria
- No strict key or profile reference remains outside the removed-key rejection test; empty and absent `allowed_root` are covered as rejected; the file passes (`AC-01`, `AC-03`, `AC-07`).

## Out of Scope
- `tests/agent/_config_test_defaults.py` and `tests/agent/services/test_config_reload.py` (own documents).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Remove the `SecurityProfile` import, strict keys and profile assertions; add `allowed_root` to `_MIN_CFG` and the approval-builder inputs | Done | 20261110-172551 | 20261110-172551 | bulk conversion via one-off script |
| 2 | Add the empty/absent `allowed_root` and removed-key rejection tests | Done | 20261110-172551 | 20261110-172551 | `TestBuildApprovalConfig.test_empty/absent_allowed_root_rejected`, `TestBuildAgentConfig.test_removed_keys_rejected_by_build_agent_config` (parametrized, matches "Unknown config keys") |
| 3 | Run the validation sequence (`rules/toolchain.md`) | In Progress | 20261110-172551 | — | file-level ruff+pytest green (69 passed); mypy/full-suite deferred to the code-batch end gate |

### Verification Findings
- (confirmed) `_build_approval_config` raises `ValueError("allowed_root is empty or absent; an empty value would disable the path jail")` (config_section_builders.py line 298-301); `build_agent_config` routes validator "Unknown config keys" errors into `ConfigReloadValidationError`.
- (addition) the Procedure's dict-fix list covered the risk-level test at line 334; without `allowed_root` the empty-root ValueError fires first, so that test was given `allowed_root` alongside the invalid rules.

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
- **Requirement ID**: `REQ-001`, `REQ-007` (plus the `REQ-003` fixture consequence for `allowed_root`)
- **Source issue**: issues/20261109-112640_adrrev004_non-strict-bypass-removal.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261110-094140_adrrev004_non-strict-bypass-removal.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261110-154603
- **Related target files**: `tests/agent/test_config_builders.py`
