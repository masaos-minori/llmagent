## Goal
Stop `tests/agent/test_repository_gateway.py` from importing the removed `STRICT_PRODUCTION_OVERRIDES` constant and keep its config dict valid under the fail-closed config (REQ-001, strict toggles removed).

## Scope
**Release unit**: strict-only-startup

## Assumptions
- Lands in the same change as `tests/agent/_config_test_defaults.py` (Plan row 37), which removes `STRICT_PRODUCTION_OVERRIDES`; this document is a fallout row added by `tools/amend_plan.py` after Step 3a found the import (`tests/agent/test_repository_gateway.py:27`).
- Row 37 defines `PERMISSIVE_ALLOWED_ROOT` (new) as the shared non-empty `allowed_root`; the empty-`allowed_root` rejection (REQ-003, Phase 4) makes the config dict need it.

## Design decisions
- Remove the import and the `**STRICT_PRODUCTION_OVERRIDES,` spread; add `"allowed_root": PERMISSIVE_ALLOWED_ROOT,` to the same dict.

## Alternatives considered
N/A: test-only change

## Implementation
### Target file
`tests/agent/test_repository_gateway.py`

### Procedure
- Replace the `STRICT_PRODUCTION_OVERRIDES` entry of the `tests.agent._config_test_defaults` import (lines 23-28) with `PERMISSIVE_ALLOWED_ROOT` (new).
- In `_make_real_cfg` remove `**STRICT_PRODUCTION_OVERRIDES,` and add `"allowed_root": PERMISSIVE_ALLOWED_ROOT,` before the overrides.

### Method
- Leave `"allowed_tools": ALL_TOOL_NAMES` and the other keys unchanged.

### Details
- A failure for any other reason is a finding for a code row, not something to adjust here.

## Compatibility considerations
N/A: test-only change

## Security considerations
N/A: test-only change

## Rollback considerations
N/A: revert the commit

## Validation plan
- `uv run pytest tests/agent/test_repository_gateway.py -v`

## Completion criteria
- `STRICT_PRODUCTION_OVERRIDES` is not referenced in the file and the file passes.

## Out of Scope
- Changing the tests' assertions.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Update the import and the config dict | Done | 20261110-210000 | 20261110-210000 | Applied via `tools/swap_config_test_defaults.py`: import entry swapped (block at lines 23-28), `_make_real_cfg` (line 281) strict spread removed, `"allowed_root": PERMISSIVE_ALLOWED_ROOT` added before `**overrides` (line 306). Tests that pass their own `allowed_root="/tmp"` (lines 322/346) keep winning over the base value. |
| 2 | Run `tests/agent/test_repository_gateway.py` | Done | 20261110-210000 | 20261110-210000 | 9 passed (file was previously red at collection due to the removed constant, matching the Assumption). |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Done | 20261110-210000 | 20261110-210000 | ruff check + ruff format clean. |

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
- **Requirement ID**: `REQ-001` (strict toggles removed)
- **Source issue**: issues/20261109-112640_adrrev004_non-strict-bypass-removal.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261110-094140_adrrev004_non-strict-bypass-removal.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261110-154603
- **Related target files**: `tests/agent/test_repository_gateway.py`
