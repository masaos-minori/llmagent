## Goal
Remove the dead `_cfg` helper (its defaults carry `security_profile`, an empty `allowed_tools` and an empty `allowed_root`) from `tests/integration/test_agent_integration.py`.

## Scope
**Release unit**: strict-only-startup

## Assumptions
- Lands in the same change as, or after, the code rows it exercises (Plan rows 01-16 and 75); a test edit alone leaves the suite red until the code row lands.
- `rg -n "_cfg\(" tests/integration/test_agent_integration.py` finds only the definition (line 19): the helper has no caller, and its `"security_profile": "development"` value would already fail `SecurityProfile(...)` today.
- After rows 05-07 the helper's defaults (`security_profile`, `allowed_tools: []`, `allowed_root: ""`) would each be rejected, so fixing them in place would keep dead code alive.

## Design decisions
- Delete the helper rather than repair it; remove imports that only it used.

## Alternatives considered
Repairing the defaults (non-empty `allowed_tools`, root `"/"`, no `security_profile`): rejected because nothing calls the helper.

## Implementation
### Target file
`tests/integration/test_agent_integration.py`

### Procedure
- Delete `_cfg` (starts at line 19, ends before `class TestMemoryScoringWithRealDB`).
- Remove `build_agent_config` and `AgentConfig` imports (lines 12-13) if `uv run ruff check` reports them unused.

### Method
- Delete the function in full; do not touch `TestMemoryScoringWithRealDB` and the other tests.

### Details
- If a later search finds a caller outside the file (none expected: the helper is module-private), stop and report instead of deleting.

## Compatibility considerations
N/A: test-only change

## Security considerations
N/A: test-only change

## Rollback considerations
N/A: revert the commit

## Validation plan
- `uv run pytest tests/integration/test_agent_integration.py -v`
- `uv run ruff check tests/integration/test_agent_integration.py`

## Completion criteria
- `security_profile` no longer appears in the file.
- No unused import remains.
- The file's tests pass.

## Out of Scope
- Rewriting the other integration tests.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Edit `tests/integration/test_agent_integration.py` per Procedure/Method/Details | Pending | — | — | |
| 2 | Run `uv run pytest tests/integration/test_agent_integration.py -v` and fix remaining fixtures in this file only | Pending | — | — | |
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
- **Requirement ID**: `REQ-001` (per the Plan row); the change removes `security_profile` and the empty-list defaults (`REQ-007`, `REQ-002`, `REQ-003`)
- **Source issue**: issues/20261109-112640_adrrev004_non-strict-bypass-removal.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261110-094140_adrrev004_non-strict-bypass-removal.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261110-154603
- **Related target files**: `tests/integration/test_agent_integration.py`
