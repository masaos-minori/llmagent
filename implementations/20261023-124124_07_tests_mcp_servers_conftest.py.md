## Goal
Add an autouse fixture that restores propagation to the root logger for the six server loggers so `caplog` keeps capturing them (`REQ-003`).

## Scope
- New `tests/mcp_servers/conftest.py` holding one autouse fixture; no existing test module is edited.

## Assumptions
- A worktree experiment that switched the six servers to `Logger` produced 37 failures in 12 test files, all from `caplog` not seeing records because `Logger` sets `propagate = False`.
- The six loggers are named after their modules (`__name__`), so `logging.getLogger(<module name>)` reaches them without importing the modules.
- No `tests/mcp_servers/conftest.py` exists today (`tests/mcp_servers/` has only fixtures modules).

## Design decisions
- Use `monkeypatch.setattr(logging.getLogger(name), "propagate", True)` for each of the six module names, so the change is restored after every test.

## Alternatives considered
- Edit the 12 test files to attach `caplog.handler` to the server loggers: rejected, one fixture is smaller and keeps the tests' intent.

## Implementation
### Target file
`tests/mcp_servers/conftest.py` (new)

### Procedure
1. Create the file with the module docstring in the repository format and the `from __future__ import annotations` header.
2. Define the tuple of six logger names (`mcp_servers.shell.shell_server`, `mcp_servers.git.git_server`, `mcp_servers.github.github_server`, `mcp_servers.cicd.cicd_server`, `mcp_servers.rag_pipeline.rag_pipeline_server`, `mcp_servers.web_search.web_search_server`).
3. Add an autouse function-scoped fixture taking `monkeypatch` that sets `propagate = True` on each logger.

### Method
- Document in the fixture docstring why it exists (the shared `Logger` disables propagation, which hides records from `caplog`).

### Details
- Reference only: `scripts/shared/logger.py` (`propagate = False`), `tests/mcp_servers/github/test_server_common.py` (representative `caplog` use).

## Compatibility considerations
- Applies to every test under `tests/mcp_servers`; a test that imports a server module for the first time inside its body creates the logger after the fixture ran (such tests keep `propagate = False`); none are known.

## Security considerations
- No secrets.

## Rollback considerations
- N/A: revert the commit.

## Validation plan
- `uv run pytest tests/mcp_servers` (the 12 files that failed in the experiment pass), `uv run ruff check tests/mcp_servers`, `uv run mypy`.

## Completion criteria
- With the six servers on the shared `Logger`, all existing `tests/mcp_servers` tests pass.

## Out of Scope
- Changing `shared.logger.Logger`
- Per-test caplog rewrites

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the fixture per Implementation > Procedure (tests are this row's change) | Pending | — | — | |
| 2 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |

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
- **Requirement ID**: `REQ-003` (keep existing tests working with propagation restored)
- **Source issue**: issues/20261023-114126_mcpstart005_server-level-audit-records-are-dropped-for-six-mcp-servers.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261023-115910_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261023-124124
- **Related target files**: tests/mcp_servers/conftest.py
