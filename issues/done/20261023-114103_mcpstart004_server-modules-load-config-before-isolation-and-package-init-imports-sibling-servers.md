# Server modules load config before isolation and package init imports sibling servers

## Priority
Medium

## Summary
Config isolation (`ConfigLoader.restrict_to`) is applied inside `MCPServer.run_http()`, after the server module has already been imported and its configuration, service and posture have been built. In addition, `scripts/mcp_servers/file/__init__.py` imports all three file servers eagerly, so starting only file-read-mcp loads and validates the file-write and file-delete configurations too. Review severity: Medium after verification (an ADR-002 isolation invariant is violated for the file servers, but the impact is defense in depth, not a reachable exposure).

## Background
ADR-002 (platform config isolation) requires each server process to read only its own config file; `run_http()` enforces this with `ConfigLoader.restrict_to(self.own_config_file)`. Every `*_server.py` loads its config at module level (for example `_cfg = ...load()`), builds its service, and computes its posture at import time. The production binary launchers import the server module first and then call `run_http()`. Package `__init__.py` files of cicd, git, mdq, rag_pipeline, shell and web_search import their own server module; `file/__init__.py` imports `delete_server`, `read_server` and `write_server`.

## Problem
Confirmed by a probe (evidence label: Confirmed by execution, confidence High). Importing only `mcp_servers.file.read_server` with the three file tokens set loaded `file_delete_mcp_server.toml`, `file_read_mcp_server.toml` and `file_write_mcp_server.toml`, left `mcp_servers.file.delete_server` and `mcp_servers.file.write_server` in `sys.modules`, and found `ConfigLoader._allowed_files` still `None` (isolation not yet active). Consequences:

- The file-read process reads and validates the delete and write server configs, so isolation does not hold during the load window.
- file-read-mcp cannot start unless `MCP_FILE_DELETE_AUTH_TOKEN` and `MCP_FILE_WRITE_AUTH_TOKEN` are also valid; a delete-server configuration error takes the read server down. With only the delete token empty, importing the read server failed with the delete server's "auth_token is empty" error.
- Each file server process builds the other two services (including their audit log handlers) without serving them.
- Under `python -m mcp_servers.git.git_server`, Python warns that the module is already in `sys.modules` after the package import and executes it a second time as `__main__`; a probe counted two loads of `git_mcp_server.toml`. The posture gate then evaluates the `__main__` copy while the app that uvicorn serves comes from the other copy.

Verification (issue-to-plan Step 2, 2026-10-23, adversarial): the findings are confirmed, with corrections. (1) The cross-server import is specific to `file/__init__.py`; the other six packages import only their own server module (and own models, service and tools). (2) The startup-coupling claim holds for a standalone start, but in an Agent-managed start every `MCP_*_AUTH_TOKEN` is passed to every subprocess (see the shell environment issue), so a file-read outage caused by a missing delete token does not occur in production today; the isolation breach itself does. (3) The double execution only happens under `python -m <server module>` (a development path); the production binaries import the module once. (4) `ConfigLoader.restrict_to` accepts one file set per process and the test suite imports many servers in one process, so calling it at the top of each server module would break tests; the call has to move to the process entry point (binary launcher, `mcp_launcher.py`), not into the modules. (5) The binary launchers use a static `from <module> import <Class>` so Nuitka can see the dependency; a dynamic import in the launcher would risk breaking the onefile build. (6) Existing tests import `from mcp_servers.git import server`, so any lazy package `__init__` must keep the `server` alias. (7) `mcp_launcher.py` has no tests today.

## Reason for Change
The isolation rule is the stated defense against one compromised or misconfigured server reading another server's secrets and settings, and the file servers differ sharply in privilege (read versus delete). Startup coupling also turns a delete-server misconfiguration into a read outage, and double execution makes startup state harder to reason about.

## Implementation Intent
Apply isolation before any server module reads configuration, and make package imports side-effect free so importing one server never executes another. Keep one place that decides the allowed config file for a process.

## Target Files or Areas
- `scripts/mcp_servers/server.py` (`run_http`, `restrict_to` placement)
- `scripts/mcp_servers/file/__init__.py` and the other package `__init__.py` files that import their server module
- Each `*_server.py` module-level config load
- `scripts/mcp_launcher.py` (`discover_servers` imports every server module in one process)
- `tests/mcp_servers/`

## Required Changes
- Remove eager server imports from the package `__init__.py` files (the file package first), or make them lazy.
- Apply `restrict_to` for the server's own config file before its module-level config load, for example at the top of each server module or in a shared helper called first.
- Decide how `mcp_launcher.py` discovery should import several servers without breaking isolation (isolation applies per process).
- Keep each server importable in tests without loading sibling configs.

## Constraints
- `ConfigLoader.restrict_to` allows only one file set per process; discovery of all servers in one process cannot use it.
- Do not change which keys each server reads from its own config file.
- Anything importing `mcp_servers.<pkg>` for models or tools must keep working.

## Acceptance Criteria
- Importing `mcp_servers.file.read_server` loads only `file_read_mcp_server.toml` and does not import the other file servers.
- Starting file-read-mcp succeeds when the delete and write tokens are absent.
- A server module attempting to load a config file outside its own set fails before any value is read.
- `python -m <server module>` executes the module once.

## Testing Expectations
- Regression test that records `ConfigLoader.load` calls while importing each server module and asserts the set equals the server's own config file.
- Regression test that importing one file server does not place the other two in `sys.modules`.
- Test that the isolation restriction is active before the module-level config load.
- Run `ruff`, `mypy`, `bandit`, `lint-imports`, and `pytest tests/mcp_servers tests/shared`.

## Documentation Impact
Update the MCP configuration documentation to state when isolation takes effect and that servers never import each other (boundaries, failure behavior). Run the documentation checkers named in `routing.md` for any edited `docs/` file.

## Out of Scope
- Changing the config file layout or the ADR itself.
- Per-server token distribution by the Agent.
- The posture gate bypass (`mcpstart002`) and the empty-token rule (`mcpstart003`).

## Dependencies
- Related: `mcpstart002` and `mcpstart003` edit the same server modules; coordinate to avoid conflicting edits, in any order.
- No open issue under `issues/` covers these files.

## Unresolved Questions
- How should `mcp_launcher.py --list` discover servers without importing every module in one process? A static registry or per-server subprocess are options.

## AI Implementation Instruction
Keep changes to import structure and the placement of the isolation call. Do not rewrite service logic. Confirm with a config-load recording test before and after. Stop and report if removing a package-level import breaks an external importer outside `scripts/mcp_servers`.

## Traceability
- **Workflow phase**: python-code-review (adversarial review of MCP server startup), converted by issue-creator
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20261023-114103
- **Related target files**: `scripts/mcp_servers/server.py`, `scripts/mcp_servers/file/__init__.py`, `scripts/mcp_servers/file/read_server.py`, `scripts/mcp_launcher.py`
