## Goal
Give shell-mcp a file-backed shared `Logger` so its audit records and `call_tool` log lines reach `shell-mcp.log` (`REQ-001`).

## Scope
- Replace `logger = logging.getLogger(__name__)` (line 55) with `logger = Logger(__name__, "/opt/llm/logs/shell-mcp.log")` and add the import.
- No change to audit record contents or call sites.

## Assumptions
- The module is 10622 bytes; the change adds about 80 bytes and stays under the 16384-byte module-size gate.
- Verified by probe: with `logging.getLogger(__name__)` the logger has INFO disabled and no handler in the server process; `shared.logger.Logger` sets INFO and attaches file and stream handlers.

## Design decisions
- Use the log file name documented for this server (`shell-mcp.log`) so documentation and code agree.
- `shared.logger.Logger` redirects `/opt/llm/logs/` into `LLMAGENT_LOG_DIR` for tests, so no test hook is needed here.

## Alternatives considered
- Configure the stdlib logger by hand in `run_http()`: rejected, the project convention for entry modules is the shared `Logger`, already used by four sibling servers.

## Implementation
### Target file
`scripts/mcp_servers/shell/shell_server.py`

### Procedure
1. Add `from shared.logger import Logger` between the existing `shared.formatters` and `shared.security...` imports (alphabetical; confirm with `uv run ruff check --fix`).
2. Replace the module-level logger line 55 with `logger = Logger(__name__, "/opt/llm/logs/shell-mcp.log")`.
3. Keep `import logging`: other `logging.` references remain in the module.

### Method
- `Logger` delegates unknown attributes to the stdlib logger, so existing `logger.info`, `logger.error` and `logger.name` uses keep working.

### Details
- Evidence: `scripts/mcp_servers/shell/shell_server.py` line 55; probe output listing INFO-enabled=False and 0 handlers for this module.
- Reference only: `scripts/mcp_servers/mdq/mdq_server.py` (pattern, not edited), `scripts/shared/logger.py` (behavior: propagate off, stderr fallback when the file cannot be opened).

## Compatibility considerations
- Server startup now creates `shell-mcp.log` under the log directory; if it cannot be opened `Logger` falls back to stderr with a warning (plan UNK-01).
- Tests that read this logger through `caplog` need the propagation fixture (conftest row).

## Security considerations
- Audit and call records become durable; `Logger` redacts bearer tokens in messages (existing behavior).

## Rollback considerations
- N/A: revert the commit.

## Validation plan
- `tests/mcp_servers/test_server_logging_sinks.py` (tracked in its own document) and the server's own test directory with the propagation fixture.
- `uv run pytest tests/mcp_servers tests/agent/test_startup.py`, `uv run ruff check`, `uv run mypy`, `uv run bandit -r scripts/mcp_servers`, `uv run python tools/check_module_size.py`, `lint-imports`.

## Completion criteria
- After import the module logger has INFO enabled and at least one handler, and an audit record is written to the log file.
- Existing tests for this server pass; module-size gate passes.

## Out of Scope
- Record fields and error-type vocabulary
- A shared server-side `audit.log` (does not exist and is not needed)

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the logger change per Implementation > Procedure/Method/Details | Completed | 20261023-130926 | 20261023-130926 | implemented; tests/mcp_servers 2514 passed (conftest fixture covers caplog); full suite run at the end of the batch |
| 2 | Add or update tests per Validation plan (`tests/mcp_servers/test_server_logging_sinks.py` and the conftest fixture, tracked in their own documents) | Completed | 20261023-130926 | 20261023-130926 |  |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20261023-130926 | 20261023-130926 |  |

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
- **Requirement ID**: `REQ-001` (shared `Logger` with a file)
- **Source issue**: issues/20261023-114126_mcpstart005_server-level-audit-records-are-dropped-for-six-mcp-servers.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261023-115910_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261023-124124
- **Related target files**: scripts/mcp_servers/shell/shell_server.py