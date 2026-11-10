## Goal
Remove the removed `tool_definitions_strict` toggle from `_make_ctx` in `tests/agent/services/test_mcp_tool_discovery_posture_gate.py`.

## Scope
**Release unit**: strict-only-startup

## Assumptions
- Lands in the same change as, or after, the code rows it exercises (Plan rows 01-16 and 75); a test edit alone leaves the suite red until the code row lands.
- After row 03, tool-definition mismatch is always FATAL and `_is_strict` is gone; `ctx.cfg` is a `MagicMock`, so the assignment is dead.
- Tests that relied on the non-strict (WARNING) result of a mismatch, if any, show up as failures when the file runs against the new code; the implementer then converts them to FATAL expectations per the Plan's REQ-001 (the posture-gate cases themselves do not depend on strictness).
- The Plan's Phase 1 step does not cite this file's path, so the release-unit default is kept (the Plan's `### Release units` entry names the phase, not each file).

## Design decisions
- Delete the fixture line first, run the file, and only then adjust any test that fails for strictness reasons.

## Alternatives considered
N/A: test-only change

## Implementation
### Target file
`tests/agent/services/test_mcp_tool_discovery_posture_gate.py`

### Procedure
- Delete `ctx.cfg.tool.tool_definitions_strict = False` in `_make_ctx` (line 81).

### Method
- Single-line deletion.

### Details
- `rg -n tool_definitions_strict tests/agent/services/test_mcp_tool_discovery_posture_gate.py` returns nothing.

## Compatibility considerations
N/A: test-only change

## Security considerations
N/A: test-only change

## Rollback considerations
N/A: revert the commit

## Validation plan
- `uv run pytest tests/agent/services/test_mcp_tool_discovery_posture_gate.py -v`

## Completion criteria
- The toggle is gone.
- The file's tests pass against the strict-only code.

## Out of Scope
- Cases in `tests/agent/services/test_mcp_tool_discovery.py` (row 21, companion of row 03).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Edit `tests/agent/services/test_mcp_tool_discovery_posture_gate.py` per Procedure/Method/Details | Done | 20261110-191500 | 20261110-192000 | `ctx.cfg.tool.tool_definitions_strict = False` deleted from `_make_ctx` (line 81). |
| 2 | Run `uv run pytest tests/agent/services/test_mcp_tool_discovery_posture_gate.py -v` and fix remaining fixtures in this file only | Done | 20261110-192000 | 20261110-192500 | `test_a_required_tool_of_a_posture_rejected_server_is_a_fatal_finding` converted to strict-only semantics per the Assumption: filter narrowed to the required-tool finding, plus a new FATAL assertion for the tool-definition-mismatch finding. 11 passed. |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Done | 20261110-192500 | 20261110-192500 | ruff clean; `rg tool_definitions_strict` returns only a reworded comment (final comment avoids the literal name; no code hits). |

### Verification Findings
| Item | Finding | Action taken |
|------|---------|--------------|
| VF-1 | Anchor confirmed: fixture line at 81 in `_make_ctx` | Deleted as specified |
| VF-2 | One test depended on the old WARNING-vs-FATAL split: the posture-rejected `git` server declares `git_push`, which is absent from `tools_definitions`, so the strict-only check adds a second FATAL finding (`extra_on_servers=['git_push']`) besides the required-tool finding | Converted per Assumption line 10: `missing` filter now matches `required tool`; added explicit FATAL assertion for the mismatch finding (this was the file's one pre-existing allowed red) |

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
- **Requirement ID**: `REQ-001` (strict toggle removed)
- **Source issue**: issues/20261109-112640_adrrev004_non-strict-bypass-removal.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261110-094140_adrrev004_non-strict-bypass-removal.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261110-154603
- **Related target files**: `tests/agent/services/test_mcp_tool_discovery_posture_gate.py`
