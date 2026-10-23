## Goal
Prove that for all ten server modules the audit logger has INFO enabled and a handler and that an audit record is written to a file (`REQ-004`).

## Scope
- New test module only.

## Assumptions
- `tests/conftest.py` sets `LLMAGENT_LOG_DIR` (line 163) before the server modules import, so each `Logger` writes under the test log directory.
- All ten server modules import in the test process (tokens and firejail are handled in `tests/conftest.py`).

## Design decisions
- Parametrize over the ten (module, logger attribute) pairs; for the record test call `mcp_servers.audit._audit_log(module.logger, ...)` and read the log file path from the logger's `FileHandler`.

## Alternatives considered
- Subprocess per server: rejected, the in-process import is sufficient because the logger is created at import.

## Implementation
### Target file
`tests/mcp_servers/test_server_logging_sinks.py` (new)

### Procedure
1. Test that `module.logger` has `isEnabledFor(logging.INFO)` true and at least one handler for each of the ten server modules.
2. Test that a call to `_audit_log` with fixed arguments writes exactly one JSON line with `event == "mcp_tool_exec"` to the logger's file handler path, then flush and read it.
3. Note in a comment that web_search keeps its separate service logger on the same file.

### Method
- Locate the `FileHandler` among `logger.handlers` (the shared `Logger` delegates `handlers` to the stdlib logger) and use its `baseFilename`.

### Details
- Reference only: `mcp_servers/audit.py` (`_audit_log`), `scripts/shared/logger.py` (handlers).

## Compatibility considerations
- Test-only.

## Security considerations
- Fixed fake session and request ids; no secrets.

## Rollback considerations
- N/A: revert the commit.

## Validation plan
- `uv run pytest tests/mcp_servers/test_server_logging_sinks.py`, `uv run ruff check tests/mcp_servers`, `uv run mypy`.

## Completion criteria
- All ten parametrized cases pass on the implemented change; the six cases for the changed servers fail on the pre-change code.

## Out of Scope
- Record field assertions beyond `event`
- Log rotation

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the test module per Implementation > Procedure (tests are this row's change) | Pending | — | — | |
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
- **Requirement ID**: `REQ-004` (sink and record tests for all ten servers), covering `REQ-001`
- **Source issue**: issues/20261023-114126_mcpstart005_server-level-audit-records-are-dropped-for-six-mcp-servers.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261023-115910_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261023-124124
- **Related target files**: tests/mcp_servers/test_server_logging_sinks.py
