## Goal
Make `_make_cfg` in `tests/agent/test_tool_approval_risk.py` valid under fail-closed config: no strict overrides, a non-empty `allowed_root`, and the existing non-empty `allowed_tools`.

## Scope
**Release unit**: N/A: not part of a release unit

## Assumptions
- Lands in the same change as, or after, the code rows it exercises (Plan rows 01-16 and 75); a test edit alone leaves the suite red until the code row lands.
- `_make_cfg` already sets `"allowed_tools": ALL_TOOL_NAMES` (64 registered tools), so only `allowed_root` and the removed strict spread need to change.
- `PERMISSIVE_ALLOWED_ROOT` (new) is defined by the row 37 document (`tests/agent/_config_test_defaults.py`) as `"/"`, so every absolute test path stays inside the jail; row 37 lands first.
- Phase 4 (fail-closed safety lists); the import of `STRICT_PRODUCTION_OVERRIDES` goes away with row 37.
- Measured: 2 tests fail under deny-on-empty (empty default `allowed_root`).

## Design decisions
- Set the root once in the shared `_make_cfg` base dict (before `**overrides`) so a test that passes its own `allowed_root` still wins.

## Alternatives considered
N/A: test-only change

## Implementation
### Target file
`tests/agent/test_tool_approval_risk.py`

### Procedure
- Import `PERMISSIVE_ALLOWED_ROOT` (new) from `tests.agent._config_test_defaults` and drop the `STRICT_PRODUCTION_OVERRIDES` import (import block near lines 18-25).
- In the `build_agent_config({...})` dict of `_make_cfg` remove `**STRICT_PRODUCTION_OVERRIDES,` and add `"allowed_root": PERMISSIVE_ALLOWED_ROOT,` ahead of `**overrides`.

### Method
- Keep the rest of the dict identical (embed_url, `_dummy` server, tiers, risk rules).

### Details
- If a test fails for a reason other than the root or the strict spread, treat it as a finding for the code row, not something to paper over here.

## Compatibility considerations
N/A: test-only change

## Security considerations
N/A: test-only change

## Rollback considerations
N/A: revert the commit

## Validation plan
- `uv run pytest tests/agent/test_tool_approval_risk.py -v`

## Completion criteria
- `STRICT_PRODUCTION_OVERRIDES` is not referenced.
- `_make_cfg` supplies a non-empty `allowed_root`.
- The file passes against the fail-closed code (measured failing under deny-on-empty before this change).

## Out of Scope
- Changing `ALL_TOOL_NAMES`.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Edit `tests/agent/test_tool_approval_risk.py` per Procedure/Method/Details | Pending | — | — | |
| 2 | Run `uv run pytest tests/agent/test_tool_approval_risk.py -v` and fix remaining fixtures in this file only | Pending | — | — | |
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
- **Requirement ID**: `REQ-002` (non-empty `allowed_tools`), `REQ-003` (non-empty `allowed_root`); the strict-key spread is also removed (`REQ-001`)
- **Source issue**: issues/20261109-112640_adrrev004_non-strict-bypass-removal.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261110-094140_adrrev004_non-strict-bypass-removal.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261110-154603
- **Related target files**: `tests/agent/test_tool_approval_risk.py`
