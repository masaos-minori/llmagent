## Goal
Remove the `SecurityProfile` fixture plumbing from `tests/agent/test_startup_mcp_lifecycle.py` so it matches an `MCPConfig` without `security_profile` (`REQ-001`, `REQ-007`).

## Scope
**Release unit**: strict-only-startup


## Assumptions
- `rg` shows no strict-key use in this file; its 21 hits are all `SecurityProfile`/`security_profile` (`_make_startup` parameter line 33 and assignment line 38, about 14 `security_profile=SecurityProfile.PRODUCTION` kwargs, and `ctx.cfg.mcp.security_profile = ...` at lines 381 and 395). Plan wording gap (no extra file): this row's Plan text says "strict toggles" and cites REQ-001, but the file also uses `security_profile`/`SecurityProfile`, which `AC-07` requires to be absent from `tests/`; the same edit removes them. No additional target file is involved.

## Design decisions
- Delete the parameter, the assignments and the kwargs; the `MagicMock` ctx needs no replacement attribute.

## Alternatives considered
N/A: the attribute is gone from the dataclass.

## Implementation
### Target file
`tests/agent/test_startup_mcp_lifecycle.py`

### Procedure
- Remove `SecurityProfile` from the import block (line 23) and the `security_profile` parameter and assignment in `_make_startup()` (lines 33, 38).
- Delete every `security_profile=SecurityProfile.PRODUCTION` argument (lines 96-416 per `rg -n security_profile`) and the two `ctx.cfg.mcp.security_profile = ...` lines (381, 395); collapse call formatting that becomes single-line.

### Method
- `uv run ruff format` after the edit to normalize wrapping.

### Details
- No assertion depends on the removed attribute; behavior under test (`_start_servers()`, `_verify_mcp_health()`) is unchanged.

## Compatibility considerations
Test-only; passes only after `MCPConfig`/dataclass changes land (release unit), but is also valid before because MagicMock accepts any attribute.

## Security considerations
N/A: fixture cleanup, no check removed.

## Rollback considerations
N/A: revert the commit

## Validation plan
- `uv run pytest tests/agent/test_startup_mcp_lifecycle.py -v`
- `uv run ruff format` and `uv run ruff check` on the file
- `uv run mypy --no-namespace-packages scripts/ tests/eventbus tools`

## Completion criteria
- `rg -n 'security_profile|SecurityProfile' tests/agent/test_startup_mcp_lifecycle.py` returns nothing and the file passes (`AC-07`).

## Out of Scope
- Source edits.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Remove the `SecurityProfile` import, the helper parameter and all kwargs/assignments | Pending | — | — | |
| 2 | Run the file's tests and the validation sequence (`rules/toolchain.md`) | Pending | — | — | |

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
- **Requirement ID**: `REQ-001` (and `REQ-007`: the fixtures use `SecurityProfile`)
- **Source issue**: issues/20261109-112640_adrrev004_non-strict-bypass-removal.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261110-094140_adrrev004_non-strict-bypass-removal.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261110-154603
- **Related target files**: `tests/agent/test_startup_mcp_lifecycle.py`
