## Goal
- Document the MCP server shutdown behavior (concurrent termination, one overall bound, and exit detection) in the lifecycle document (`REQ-006` (document the shutdown behavior)).

## Scope
- In scope: `docs/22_mcp/mcp_03_04_tool-call-tracing-and-lifecycle.md` only.
- Out of scope: every other file (each has its own procedure document); the second mapped document `agent_02_runtime-architecture.md` is checked for conflicts only and not modified.

## Assumptions
- The code procedures for the terminator and the coordinator are applied first, so the text describes implemented behavior.

## Design decisions
- Add a short "Implementation Note" subsection next to the existing "Double SIGINT Guard" note, stating behavior and intent (concurrent termination, one bound, SIGTERM then SIGKILL, exit detection) and pointing to the source for detail, per `skills/DESIGN.md` Avoid implementation-reference duplication.

## Alternatives considered
- N/A: documentation-only row.

## Implementation

### Target file

`docs/22_mcp/mcp_03_04_tool-call-tracing-and-lifecycle.md`

### Procedure
1. After the "Implementation Note (Double SIGINT Guard)" subsection, add an "Implementation Note (Shutdown Termination)" subsection of a few sentences: all HTTP subprocess servers receive SIGTERM at the start of shutdown and are awaited together, so total time is bounded by one termination timeout (30 seconds) rather than the sum; a server that exits on SIGTERM is detected as exited immediately, and only a server that ignores SIGTERM is escalated to SIGKILL; a termination failure keeps that server's tracking entry for manual cleanup.
2. Keep the existing "Double SIGINT Guard" text unchanged; do not copy constants beyond the timeout value and do not list file names beyond a reference to `agent/http_lifecycle_shutdown_coordinator.py`.
### Method
- English prose, matching the surrounding subsections' style; mark the claims as `(Explicit in code)` like the neighboring note.
### Details
- Check `docs/23_agent/agent_02_runtime-architecture.md` for a conflicting shutdown statement; it describes only the SIGTERM flag handling of the REPL, so no edit is expected.

## Compatibility considerations
- N/A: documentation-only change.

## Security considerations
- N/A: no security impact.

## Rollback considerations
- N/A: revert the commit.

## Validation plan
- `uv run python tools/check_docs_quality.py`, `uv run python tools/check_docs_structure.py`, and `uv run python tools/check_docs_content_policy.py --strict`.
- `uv run python tools/check_docs_consistency.py --domain mcp` and `uv run python tools/check_docs_japanese.py`.

## Completion criteria
- The document states the shutdown behavior and the checkers above pass.

## Out of Scope
- Modifying any file other than the target file; changing code; `issues/done/`, `plans/done/`, `implementations/done/`.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Add the shutdown termination note to the lifecycle document | Pending | — | — | |
| 2 | Run the documentation checkers named in Validation plan | Pending | — | — | |

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
- **Requirement ID**: `REQ-006` (document the shutdown behavior)
- **Source issue**: issues/done/20261019-215906_mcpshut001_make-mcp-server-shutdown-bounded-and-complete.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261019-220318_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261019-220632
- **Related target files**: docs/22_mcp/mcp_03_04_tool-call-tracing-and-lifecycle.md
