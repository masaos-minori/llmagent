## Goal
Give the `_cfg` helper in `tests/agent/test_tool_loop_guard.py` a non-empty `allowed_root`, since the approval section builder now rejects an empty one (`REQ-003`, fallout row added at the end-of-batch gate).

## Scope
**Release unit**: N/A: not part of a release unit

## Assumptions
- Lands after row 07 (`scripts/agent/config_section_builders.py` rejects an empty or absent `allowed_root`); measured: 46 tests in this file fail at the 20261110 end-of-batch `pytest tests/` gate, all with `ConfigReloadValidationError: allowed_root is empty or absent` from the `defaults` dict (line 49 `"allowed_root": ""`).
- `ToolLoopGuard` logic (dedup, cycle detection, error budgets) does not consult `allowed_tools`/`allowed_root`; the failures are purely build-time, so a permissive root preserves every test's intent.
- `_cfg` patches `ProductionConfigValidator`; the section-builder rejection is not covered by that patch, matching the row 82 finding.

## Design decisions
- Replace only `"allowed_root": ""` with `PERMISSIVE_ALLOWED_ROOT` from `tests.agent._config_test_defaults` (the shared non-empty root, `"/"`), same fixture pattern as rows 46/47/80/81/92/93.

## Alternatives considered
Swapping in `ALL_TOOL_NAMES` was rejected: no failure in this file comes from `allowed_tools`. Tests that need specific loop-guard config already use `**overrides`.

## Implementation
### Target file
`tests/agent/test_tool_loop_guard.py`

### Procedure
- Add `from tests.agent._config_test_defaults import PERMISSIVE_ALLOWED_ROOT` to the import block.
- In the `defaults` dict of `_cfg`, replace `"allowed_root": "",` (line 49) with `"allowed_root": PERMISSIVE_ALLOWED_ROOT,`.

### Method
- Run the file; if any test still fails for a non-build reason, record it as a finding for the owning code row rather than loosening the assertion.

### Details
- Line 372's comment about `build_agent_config` mapping loop-guard keys is unrelated to this change.
- Importing `_config_test_defaults` evaluates the registry at import time; other test files already do this.

## Compatibility considerations
N/A: test-only change

## Security considerations
N/A: test-only change

## Rollback considerations
N/A: revert the commit

## Validation plan
- `uv run pytest tests/agent/test_tool_loop_guard.py -v` (expect all 57 tests green)
- `uv run ruff check tests/agent/test_tool_loop_guard.py && uv run ruff format tests/agent/test_tool_loop_guard.py`

## Completion criteria
- No build-time `ConfigReloadValidationError` remains in this file.
- The file passes against the fail-closed code.

## Out of Scope
- Changing `tool_loop_guard.py` or the section builder.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Edit `tests/agent/test_tool_loop_guard.py` per Procedure/Method/Details | Done | 20261110-214000 | 20261110-214100 | Import `PERMISSIVE_ALLOWED_ROOT` added after the `shared.transport_dto` import block (isort placement); `"allowed_root": ""` (line 49) replaced with `PERMISSIVE_ALLOWED_ROOT`. |
| 2 | Run `uv run pytest tests/agent/test_tool_loop_guard.py -v` and fix remaining fixtures in this file only | Done | 20261110-214100 | 20261110-214100 | 57 passed (was 46 failed + 11 passed pre-change). No `allowed_tools` change needed, matching the Assumption. |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Done | 20261110-214100 | 20261110-214100 | ruff check (isort fixed) + ruff format clean. |

### Verification Findings
| Item | Finding | Action taken |
|------|---------|--------------|
| VF-1 | Anchor confirmed: `"allowed_root": ""` at line 49 inside `_cfg` `defaults` | Applied as written |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| — | — | — | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| — | — | — | — | — | — |

## Traceability
- **Workflow phase**: plan-to-implementation-procedure (post-freeze fallout amendment, `tools/amend_plan.py`)
- **Requirement ID**: `REQ-003` (empty or absent `allowed_root` fails closed in test fixtures too)
- **Source issue**: issues/20261109-112640_adrrev004_non-strict-bypass-removal.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261110-094140_adrrev004_non-strict-bypass-removal.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261110-154603
- **Related target files**: `tests/agent/test_tool_loop_guard.py`
