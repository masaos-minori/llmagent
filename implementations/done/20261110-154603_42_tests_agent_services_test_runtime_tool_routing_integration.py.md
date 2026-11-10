## Goal
Remove the `SecurityProfile` import and the `security_profile` assignment from `tests/agent/services/test_runtime_tool_routing_integration.py`.

## Scope
**Release unit**: strict-only-startup

## Assumptions
- Lands in the same change as, or after, the code rows it exercises (Plan rows 01-16 and 75); a test edit alone leaves the suite red until the code row lands.
- `ctx` is a `MagicMock`; once `AgentConfig.security_profile` and the enum are deleted the assignment has no meaning.
- The Plan's Phase 1 step does not cite this file's path, so the release-unit default is kept (the Plan's `### Release units` entry names the phase, not each file).

## Design decisions
- Delete only the import name and the assignment.

## Alternatives considered
N/A: test-only change

## Implementation
### Target file
`tests/agent/services/test_runtime_tool_routing_integration.py`

### Procedure
- Remove `SecurityProfile,` from the `shared.mcp_config` import block (line 20).
- Delete `ctx.cfg.mcp.security_profile = SecurityProfile.PRODUCTION` (line 342).

### Method
- Check unused imports with `uv run ruff check`.

### Details
- `rg -n "SecurityProfile|security_profile" tests/agent/services/test_runtime_tool_routing_integration.py` returns nothing.

## Compatibility considerations
N/A: test-only change

## Security considerations
N/A: test-only change

## Rollback considerations
N/A: revert the commit

## Validation plan
- `uv run pytest tests/agent/services/test_runtime_tool_routing_integration.py -v`

## Completion criteria
- No `SecurityProfile`/`security_profile` reference remains.
- The tests pass.

## Out of Scope
- Other tests.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Edit `tests/agent/services/test_runtime_tool_routing_integration.py` per Procedure/Method/Details | Done | 20261110-185500 | 20261110-190000 | `SecurityProfile,` removed from the import block (line 20); `ctx.cfg.mcp.security_profile = SecurityProfile.PRODUCTION` deleted (line 342). |
| 2 | Run `uv run pytest tests/agent/services/test_runtime_tool_routing_integration.py -v` and fix remaining fixtures in this file only | Done | 20261110-190000 | 20261110-190000 | 13 passed (file was a collection-error file before the row landed). |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Done | 20261110-190000 | 20261110-190000 | ruff clean; final grep shows no `SecurityProfile`/`security_profile` hits. |

### Verification Findings
| Item | Finding | Action taken |
|------|---------|--------------|
| VF-1 | Anchors confirmed against the current file: import name at line 20 (block starts line 18), assignment at line 342 | Applied as written; other import names kept |

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
- **Requirement ID**: `REQ-001` (per the Plan row); the change removes `SecurityProfile` (`REQ-007`)
- **Source issue**: issues/20261109-112640_adrrev004_non-strict-bypass-removal.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261110-094140_adrrev004_non-strict-bypass-removal.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261110-154603
- **Related target files**: `tests/agent/services/test_runtime_tool_routing_integration.py`
