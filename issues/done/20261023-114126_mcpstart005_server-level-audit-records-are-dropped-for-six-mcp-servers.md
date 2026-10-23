# Server-level audit records are dropped for six MCP servers

## Priority
Medium

## Summary
shell-mcp, git-mcp, github-mcp, cicd-mcp, rag-pipeline-mcp and web-search-mcp emit their `mcp_tool_exec` audit records and `call_tool` log lines through a plain `logging.getLogger(__name__)` that has no handler and an effective level of WARNING in the production process. The records are discarded, although the documentation says they land in the shared audit log. Review severity: Medium after verification (a server-side audit layer is lost silently, but the Agent-side `tool_exec` layer and the dedicated audit files remain).

## Background
`scripts/mcp_servers/audit.py::_audit_log()` serializes one JSON-lines record and calls `server_logger.info(...)`. The four file/mdq servers (`file/read_server.py`, `file/write_server.py`, `file/delete_server.py`, `mdq/mdq_server.py`) create `shared.logger.Logger(__name__, "/opt/llm/logs/<name>.log")`, which attaches file and stream handlers. The six servers above create `logging.getLogger(__name__)` instead. `MCPServer.run_http()` builds `uvicorn.Config(..., log_level="info")`, which configures only the `uvicorn.*` loggers. `docs/22_mcp/mcp_06_05_reading-audit-logs.md` states that cicd, git and mdq record to `<log_dir>/audit.log`, and that layer 2 (`mcp_tool_exec` in `audit.log`) covers all servers except file-read and rag-pipeline. No MCP server module writes `audit.log`; the only path configured for it is on the Agent side (`audit_log_file` in `scripts/agent/config_dataclasses.py`).

## Problem
Confirmed by a probe (evidence label: Confirmed by execution, confidence High). After building the same `uvicorn.Config` that `run_http()` creates and importing each server module, the module `logger` of shell, git, github, cicd, rag_pipeline and web_search reported `INFO enabled = False` and zero handlers, while file-read, file-write, file-delete and mdq reported `INFO enabled = True` with two handlers. For the six affected servers every `_audit_log(logger, ...)` call and every `logger.info(fmt_kvlog("call_tool", ...))` line is silently dropped. Dedicated per-server audit files still exist for shell (`shell_audit.log`), github (`audit_log_path`) and file-delete; git, cicd, rag-pipeline and web-search have no other server-side audit record. Tool execution on git (writes, pushes), cicd (workflow triggers) and web search therefore leaves no server-side trace, and `GitConfig.audit_log_path` is documented as unused.

Verification (issue-to-plan Step 2, 2026-10-23, adversarial): the drop is confirmed, with corrections. (1) The documented shared `audit.log` has no server-side writer at all: `mcp_tool_exec` is produced only by `mcp_servers/audit.py`, which logs through each server's own logger, and the only `audit.log` writer is the Agent (`scripts/agent/factory.py`, `Logger("audit", ...)`, Agent-side `tool_exec`). Even the four servers whose logger works (file-read, file-write, file-delete, mdq) write `mcp_tool_exec` to their own application log, not to `audit.log`. So the unresolved question has an answer: there is no shared server-side sink to restore, and the documentation is wrong for every server. (2) The Agent-side Layer 1 `tool_exec` record still exists for every call, and shell, github and file-delete keep dedicated audit files, so the lost records are the Layer 2 records of git, cicd, rag-pipeline, web-search, and the Layer 2 records plus application logs of shell and github. (3) The documented application logs `shell-mcp.log`, `github-mcp.log`, `git-mcp.log`, `cicd-mcp.log` and `rag-mcp.log` are not written by any code; only five `Logger(...)` sites exist (file-read, file-write, file-delete, mdq, and the web-search service). (4) `shared.logger.Logger` falls back to a stderr stream handler when the log file cannot be opened, and the Agent captures subprocess stderr, so records are retained there; the issue's "fail startup on an unopenable sink" requirement conflicts with that existing behavior and is left as an open question. (5) `Logger` sets `propagate = False`; a worktree experiment that switched the six servers to `Logger` produced 37 failures in 12 test files that read the server loggers through `caplog`, so the tests need a propagation fixture.

## Reason for Change
Audit records exist to reconstruct who did what through write-capable tools. The current gap is invisible: tests pass, the documentation claims a shared audit log, and no error is raised.

## Implementation Intent
Give every server one explicit, shared logging setup that attaches a handler for the audit stream before serving, and make a failure to attach it a startup error rather than a silent loss. Decide, and document, the single destination of the shared audit records.

## Target Files or Areas
- `scripts/mcp_servers/audit.py`
- `scripts/mcp_servers/server.py` (common start path)
- `scripts/mcp_servers/{shell,git,github,cicd,rag_pipeline,web_search}/*_server.py` (logger creation)
- `scripts/shared/logger.py` (`Logger`, `LLMAGENT_LOG_DIR`)
- `docs/22_mcp/mcp_06_05_reading-audit-logs.md`, `docs/22_mcp/mcp_04_05_git.md`
- `tests/mcp_servers/`

## Required Changes
- Create the audit and application loggers of the six servers through the shared `Logger` (or an equivalent shared helper) so records reach a file.
- Define the shared audit destination and make the documentation match the implementation.
- Fail startup, or report a degraded health state, when the audit sink cannot be opened.
- Remove or implement the unused `GitConfig.audit_log_path` so configuration matches behavior.

## Constraints
- Records must not contain secrets; the existing redaction in `shared.logger` applies.
- Log files must stay under the configured log directory, including the `LLMAGENT_LOG_DIR` test override.
- Do not change the audit record schema.

## Acceptance Criteria
- A tool call on each of the ten servers produces exactly one `mcp_tool_exec` record at the documented destination.
- INFO is enabled and a handler is attached for the audit logger of every server after startup.
- The documentation lists, per server, where the audit records are written, matching the code.

## Testing Expectations
- Parametrized test over all ten server modules asserting the audit logger has a handler and INFO enabled after import under the `run_http()` logging configuration.
- Integration test per affected server: a `call_tool` request writes one audit record to a temporary log directory.
- Regression test that a failure to open the sink is reported rather than ignored.
- Run `ruff`, `mypy`, `bandit`, and `pytest tests/mcp_servers tests/shared`.

## Documentation Impact
Update `mcp_06_05_reading-audit-logs.md` and `mcp_04_05_git.md` so the audit destinations and layers match the implementation (operational notes, failure behavior). Run the documentation checkers named in `routing.md` for any edited `docs/` file.

## Out of Scope
- Agent-side `tool_exec` auditing.
- Log rotation and retention policy.
- Changing the audit record fields or error-type vocabulary.

## Dependencies
- Related: `mcpstart002` changes the common start path; the logging setup can live there once it exists, or be added per module first.
- No open issue under `issues/` covers these files.

## Unresolved Questions
- Resolved by verification: no shared server-side sink exists; each server should write `mcp_tool_exec` to its own application log and the documentation should say so.
- Should an unopenable log file fail startup, given `shared.logger.Logger` deliberately falls back to stderr?

## AI Implementation Instruction
Limit changes to logger creation and sink handling for the six servers plus the matching documentation. Do not change record contents. Use temporary directories in tests, never `/opt/llm/logs`. Stop and report if the intended audit destination cannot be determined from the documentation.

## Traceability
- **Workflow phase**: python-code-review (adversarial review of MCP server startup), converted by issue-creator
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20261023-114126
- **Related target files**: `scripts/mcp_servers/audit.py`, `scripts/mcp_servers/server.py`, `scripts/mcp_servers/git/git_server.py`, `scripts/mcp_servers/shell/shell_server.py`, `docs/22_mcp/mcp_06_05_reading-audit-logs.md`
