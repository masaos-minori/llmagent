## Goal
Make `_make_cfg` in `tests/agent/test_tool_approval_preflight.py` valid under fail-closed config: no strict overrides, a non-empty `allowed_root`, and the existing non-empty `allowed_tools`.

## Scope
**Release unit**: N/A: not part of a release unit

## Assumptions
- Lands in the same change as, or after, the code rows it exercises (Plan rows 01-16 and 75); a test edit alone leaves the suite red until the code row lands.
- `_make_cfg` already sets `"allowed_tools": ALL_TOOL_NAMES` (64 registered tools), so only `allowed_root` and the removed strict spread need to change.
- `PERMISSIVE_ALLOWED_ROOT` (new) is defined by the row 37 document (`tests/agent/_config_test_defaults.py`) as `"/"`, so every absolute test path stays inside the jail; row 37 lands first.
- Phase 4 (fail-closed safety lists); the import of `STRICT_PRODUCTION_OVERRIDES` goes away with row 37.
- Measured: 21 tests in this file fail under deny-on-empty because `allowed_root` is empty.

## Design decisions
- Set the root once in the shared `_make_cfg` base dict (before `**overrides`) so a test that passes its own `allowed_root` still wins.

## Alternatives considered
N/A: test-only change

## Implementation
### Target file
`tests/agent/test_tool_approval_preflight.py`

### Procedure
- Import `PERMISSIVE_ALLOWED_ROOT` (new) from `tests.agent._config_test_defaults` and drop the `STRICT_PRODUCTION_OVERRIDES` import (import block near lines 18-25).
- In the `build_agent_config({...})` dict of `_make_cfg` remove `**STRICT_PRODUCTION_OVERRIDES,` and add `"allowed_root": PERMISSIVE_ALLOWED_ROOT,` ahead of `**overrides`.

### Method
- Keep the rest of the dict identical (embed_url, `_dummy` server, tiers, risk rules).
- Tests that set their own root (for example `allowed_root="/tmp"` near line 1070) are unchanged.
- `test_approval_flow_preflight_gate_fires` (line 1051) keeps `allowed_tools=["read_only_tool"]`; it is non-empty and still denies `write_file`.

### Details
- If a test fails for a reason other than the root or the strict spread, treat it as a finding for the code row, not something to paper over here.

## Compatibility considerations
N/A: test-only change

## Security considerations
N/A: test-only change

## Rollback considerations
N/A: revert the commit

## Validation plan
- `uv run pytest tests/agent/test_tool_approval_preflight.py -v`

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
| 1 | Edit `tests/agent/test_tool_approval_preflight.py` per Procedure/Method/Details | Done | 20261110-193000 | 20261110-193500 | Import block: `STRICT_PRODUCTION_OVERRIDES` → `PERMISSIVE_ALLOWED_ROOT`. `_make_cfg` base dict: dropped the strict spread, added `"allowed_root": PERMISSIVE_ALLOWED_ROOT` ahead of `**overrides`; dict otherwise identical. |
| 2 | Run `uv run pytest tests/agent/test_tool_approval_preflight.py -v` and fix remaining fixtures in this file only | Done | 20261110-193500 | 20261110-194000 | Re-measured after the environment reorg: 79 passed (78 baseline + 1 new test). Also converted 3 residual in-file `allowed_root=""` overrides (github repo-allowlist fixtures, lines 1083/1140/1148) to `PERMISSIVE_ALLOWED_ROOT`: path gating is irrelevant to their repo-allowlist assertions and they named the strict value inline. |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Done | 20261110-193500 | 20261110-194000 | ruff check + ruff format clean; no `STRICT_PRODUCTION_OVERRIDES` reference remains. |

### Verification Findings
| Item | Finding | Action taken |
|------|---------|--------------|
| VF-1 | Anchors confirmed: import block lines 18-24 (with the old name at line 23 after the reorg), `_make_cfg` at line 42, `**STRICT_PRODUCTION_OVERRIDES` at line 47; the doc's "near lines 18-25" holds | Applied as written |
| VF-2 | `test_approval_flow_preflight_gate_fires` (line 1053) uses `allowed_tools=["read_only_tool"]` with `plan_blocked_tools=["write_file"]` — the doc's cited `["read_file", "write_file"]` does not match the current file (fixture evolution since the doc was generated). The checkpoint's intent (preflight gates a non-allowed tool) still holds | Left unchanged |
| VF-3 | `test_empty_allowed_tools_denies_every_tool` was absent at baseline as the doc predicted; added as written | Added |

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
- **Related target files**: `tests/agent/test_tool_approval_preflight.py`
