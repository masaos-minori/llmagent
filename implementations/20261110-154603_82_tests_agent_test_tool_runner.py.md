## Goal
Give the `_cfg` helper in `tests/agent/test_tool_runner.py` a non-empty `allowed_tools` and `allowed_root`, since the helper's deliberately empty values now deny every tool (`REQ-002`, `REQ-003`).

## Scope
**Release unit**: N/A: not part of a release unit

## Assumptions
- Lands in the same change as, or after, the code rows it exercises (Plan rows 01-16 and 75); a test edit alone leaves the suite red until the code row lands.
- Measured: 12 tests fail under deny-on-empty. `_cfg` patches `ProductionConfigValidator` (line 83) but the empty `allowed_root` is rejected by the section builder (row 07), which the patch does not cover, so both values must change.
- `PERMISSIVE_ALLOWED_ROOT` (new) is defined by the row 37 document (`tests/agent/_config_test_defaults.py`) as `"/"`, so every absolute test path stays inside the jail; row 37 lands first.
- The tests call tools such as `write_file`, `edit_file`, `shell_run` and `github_push_files`; `ALL_TOOL_NAMES` covers all registered names.

## Design decisions
- Reuse `ALL_TOOL_NAMES` instead of a hand-maintained list so new tools do not silently become denied.
- Leave `tool_safety_tiers` and `approval_risk_rules` empty: the docstring's point (bypassing the production validator) still holds for them.

## Alternatives considered
N/A: test-only change

## Implementation
### Target file
`tests/agent/test_tool_runner.py`

### Procedure
- Import `ALL_TOOL_NAMES` and `PERMISSIVE_ALLOWED_ROOT` (new) from `tests.agent._config_test_defaults`.
- In `defaults` set `"allowed_tools": list(ALL_TOOL_NAMES)` (line 60) and `"allowed_root": PERMISSIVE_ALLOWED_ROOT` (line 69).
- Update the docstring (lines 46-52): say only `tool_safety_tiers`/`approval_risk_rules` are deliberately empty.

### Method
- Tests that need a narrower list already pass `allowed_tools=` through `**overrides`; none is expected to depend on the empty default.

### Details
- Importing `_config_test_defaults` evaluates the registry at import time; other test files already do this, so no new ordering risk.

## Compatibility considerations
N/A: test-only change

## Security considerations
N/A: test-only change

## Rollback considerations
N/A: revert the commit

## Validation plan
- `uv run pytest tests/agent/test_tool_runner.py -v`

## Completion criteria
- `_cfg` supplies non-empty `allowed_tools` and `allowed_root`.
- All tests in the file pass against the fail-closed code.

## Out of Scope
- Changing the validator patch.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Edit `tests/agent/test_tool_runner.py` per Procedure/Method/Details | Pending | — | — | |
| 2 | Run `uv run pytest tests/agent/test_tool_runner.py -v` and fix remaining fixtures in this file only | Pending | — | — | |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |

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
- **Requirement ID**: `REQ-002` (non-empty `allowed_tools`), `REQ-003` (non-empty `allowed_root`)
- **Source issue**: issues/20261109-112640_adrrev004_non-strict-bypass-removal.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261110-094140_adrrev004_non-strict-bypass-removal.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261110-154603
- **Related target files**: `tests/agent/test_tool_runner.py`
