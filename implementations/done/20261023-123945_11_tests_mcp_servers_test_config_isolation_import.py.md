## Goal
Prove each server module loads only its own config file, the file package no longer imports sibling servers, lazy aliases still resolve, a server module executes once under `python -m`, and the `ENTRIES` table matches the server classes (`REQ-005`).

## Scope
- New test module only.

## Assumptions
- Fresh interpreters are needed because server modules cache config and `sys.modules`; token variables come from the test process environment (all ten set by `tests/conftest.py`), and `LLMAGENT_LOG_DIR` points at `tmp_path`.
- The shell case is skipped when `firejail` is not installed.

## Design decisions
- One parametrized subprocess helper that restricts to the server's own config, records `ConfigLoader.load` arguments and imports the module, printing the recorded names as JSON.

## Alternatives considered
- In-process checks: rejected, other tests already imported these modules in the same process.

## Implementation
### Target file
`tests/mcp_servers/test_config_isolation_import.py` (new)

### Procedure
1. Parametrized test over the ten (module, config file) pairs: in a subprocess call `ConfigLoader.restrict_to(<own>)` first, import the module, and assert exit 0 and that the recorded loads equal the set containing only the own config file.
2. File-package test: importing `mcp_servers.file.read_server` leaves `mcp_servers.file.delete_server` and `mcp_servers.file.write_server` out of `sys.modules`.
3. Alias test: `from mcp_servers.git import server`, `from mcp_servers.mdq import models, server, service, tools` and the other packages' aliases resolve to the expected submodules; an unknown attribute raises `AttributeError`.
4. Single-execution test: in a subprocess run `runpy.run_module("mcp_servers.git.git_server", run_name="__main__")` with `MCPServer.run_http` patched to a no-op and count `ConfigLoader.load("git_mcp_server.toml")` calls; assert one.
5. `ENTRIES` test: parse the `ENTRIES` rows of `deploy/build_binaries.sh`, import each class and assert the config field equals the class `own_config_file`; assert the launcher template text places `restrict_to` before the server import.

### Method
- Use `subprocess.run([sys.executable, "-c", script], env=..., capture_output=True)` with `PYTHONPATH` set to `scripts`.

### Details
- Reference only: `tests/mcp_servers/test_config_isolation_fail_closed.py`, `tests/conftest.py` (token and firejail setup).

## Compatibility considerations
- Test-only.

## Security considerations
- Fake token values only.

## Rollback considerations
- N/A: revert the commit.

## Validation plan
- `uv run pytest tests/mcp_servers/test_config_isolation_import.py`, `uv run ruff check tests/mcp_servers`, `uv run mypy`.

## Completion criteria
- All cases pass on the implemented change; the file-package and single-execution cases fail on the pre-change code.

## Out of Scope
- Changes to existing test modules

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the test module per Implementation > Procedure (tests are this row's change) | Completed | 20261023-130633 | 20261023-130633 | implemented; tests/mcp_servers + startup + tools: 3631 passed; full suite run at the end of the batch; Nuitka rebuild not run (plan Phase 5) |
| 2 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20261023-130633 | 20261023-130633 |  |

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
- **Requirement ID**: `REQ-005` (isolation tests), covering `REQ-001`, `REQ-002`, `REQ-003`
- **Source issue**: issues/20261023-114103_mcpstart004_server-modules-load-config-before-isolation-and-package-init-imports-sibling-servers.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261023-115449_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261023-123945
- **Related target files**: tests/mcp_servers/test_config_isolation_import.py