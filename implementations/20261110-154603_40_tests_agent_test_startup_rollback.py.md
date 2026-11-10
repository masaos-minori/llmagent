## Goal
Remove the `SecurityProfile` import and the `security_profile` assignment from `tests/agent/test_startup_rollback.py`.

## Scope
**Release unit**: strict-only-startup

## Assumptions
- Lands in the same change as, or after, the code rows it exercises (Plan rows 01-16 and 75); a test edit alone leaves the suite red until the code row lands.
- `SecurityProfile` is deleted from `scripts/shared/mcp_config.py` (row 10) and `AgentConfig.security_profile` from `config_dataclasses.py` (row 06). `ctx` is a `MagicMock`, so the assignment is dead once the field is gone.
- The Plan's Phase 1 step does not cite this file's path, so the release-unit default is kept (the Plan's `### Release units` entry names the phase, not each file).

## Design decisions
- Delete only the import name and the assignment; the other names in the `from shared.mcp_config import (...)` block stay.

## Alternatives considered
N/A: test-only change

## Implementation
### Target file
`tests/agent/test_startup_rollback.py`

### Procedure
- Remove `SecurityProfile,` from the import block (line 18).
- Delete `ctx.cfg.mcp.security_profile = SecurityProfile.PRODUCTION` in `test_rollback_on_partial_multi_server_failure` (line 199).

### Method
- Run `uv run ruff check` to catch any now-unused import.

### Details
- Confirm with `rg -n "SecurityProfile|security_profile" tests/agent/test_startup_rollback.py`.

## Compatibility considerations
N/A: test-only change

## Security considerations
N/A: test-only change

## Rollback considerations
N/A: revert the commit

## Validation plan
- `uv run pytest tests/agent/test_startup_rollback.py -v`

## Completion criteria
- No `SecurityProfile`/`security_profile` reference remains.
- The file's tests pass.

## Out of Scope
- Other tests in the file.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Edit `tests/agent/test_startup_rollback.py` per Procedure/Method/Details | Pending | — | — | |
| 2 | Run `uv run pytest tests/agent/test_startup_rollback.py -v` and fix remaining fixtures in this file only | Pending | — | — | |
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
- **Requirement ID**: `REQ-001` (per the Plan row); the change removes `SecurityProfile` (`REQ-007`)
- **Source issue**: issues/20261109-112640_adrrev004_non-strict-bypass-removal.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261110-094140_adrrev004_non-strict-bypass-removal.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261110-154603
- **Related target files**: `tests/agent/test_startup_rollback.py`
