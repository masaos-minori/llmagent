## Goal
Stop the file package from importing the delete, read and write server modules so importing one file server loads only its own config (`REQ-001`).

## Scope
- Remove the three eager imports (lines 5-7); keep the module docstring and `from __future__ import annotations`.

## Assumptions
- No code uses the package-level attributes `mcp_servers.file.delete_server`, `read_server` or `write_server` without importing the submodule (repository search found no `from mcp_servers.file import ...` consumer).
- Verified by a probe: importing `mcp_servers.file.read_server` loaded all three file config files and left `delete_server` and `write_server` in `sys.modules`.

## Design decisions
- Submodules stay importable by their full path, so no lazy `__getattr__` (new) is needed here.

## Alternatives considered
- Lazy aliases as in the other packages: unnecessary, the package never exported aliases.

## Implementation
### Target file
`scripts/mcp_servers/file/__init__.py`

### Procedure
1. Delete the three `from . import ... as ...` lines.
2. Add a one-line comment explaining that sibling servers must not be imported here (config isolation).

### Method
- Leave an otherwise empty package module (docstring, future import, comment).

### Details
- Evidence: `file/__init__.py` lines 3-7; probe loaded "file_delete_mcp_server.toml", "file_read_mcp_server.toml" and "file_write_mcp_server.toml" while importing only the read server; with restrict-first the three file servers fail with `ConfigPermissionError` until this row lands.

## Compatibility considerations
- Code importing `mcp_servers.file.read_server` by full path is unaffected.

## Security considerations
- Strengthens ADR-002 config isolation: a server process can no longer read another server's configuration, including its token and policy settings, through package imports or ahead of the restriction.

## Rollback considerations
- N/A: revert the commit.

## Validation plan
- `tests/mcp_servers/test_config_isolation_import.py` (file-package test), then `uv run pytest tests/mcp_servers tests/agent tests/tools`, `uv run ruff check`, `uv run mypy`, `uv run bandit -r scripts/mcp_servers`, `uv run python tools/check_docstrings.py`, `uv run python tools/check_module_size.py`, `lint-imports`.

## Completion criteria
- Importing `mcp_servers.file.read_server` in a fresh interpreter loads only the read config and leaves the other two servers out of `sys.modules`.

## Out of Scope
- Applying `restrict_to` (launcher rows)
- Other packages

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the import removal per Implementation > Procedure | Pending | — | — | |
| 2 | Add or update tests per Validation plan (`tests/mcp_servers/test_config_isolation_import.py`, tracked in its own document) | Pending | — | — | |
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
- **Requirement ID**: `REQ-001` (file package must not import sibling servers)
- **Source issue**: issues/20261023-114103_mcpstart004_server-modules-load-config-before-isolation-and-package-init-imports-sibling-servers.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261023-115449_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261023-123945
- **Related target files**: scripts/mcp_servers/file/__init__.py
