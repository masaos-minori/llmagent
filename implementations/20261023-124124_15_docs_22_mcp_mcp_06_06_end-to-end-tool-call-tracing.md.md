## Goal
Correct the audit and application-log statements so they match the implementation after the six servers write their own logs (`REQ-005`).

## Scope
- Edit lines 17 and 21: keep the Agent-side `mcp_request_id` query on `audit.log` and point the server `request_id` query at the server's own application log `<log_dir>/<server>-mcp.log`.

## Assumptions
- The document has 4 commits in 30 days; keep the edit to the audit sentences and rebase before committing.
- After the server rows land, every server writes `mcp_tool_exec` records to its own application log `<log_dir>/<server>-mcp.log`; `audit.log` is written only by the Agent.

## Design decisions
- State destinations per server in prose, without duplicating record fields (`skills/DESIGN.md` Avoid implementation-reference duplication).

## Alternatives considered
- N/A: documentation-only row.

## Implementation
### Target file
`docs/22_mcp/mcp_06_06_end-to-end-tool-call-tracing.md`

### Procedure
1. Apply the correction at lines 17 and 21: keep the Agent-side `mcp_request_id` query on `audit.log` and point the server `request_id` query at the server's own application log `<log_dir>/<server>-mcp.log`.

### Method
- Edit existing text; no new section, table or code block.

### Details
- English only; keep the three-layer vocabulary (Agent `tool_exec`, server `mcp_tool_exec`, dedicated audit file) and only correct the destination of the server layer.

## Compatibility considerations
- N/A: documentation-only.

## Security considerations
- N/A: describes existing records.

## Rollback considerations
- N/A: revert the commit.

## Validation plan
- `uv run python tools/check_docs_quality.py`, `check_docs_structure.py`, `check_docs_content_policy.py`, `check_docs_consistency.py --domain mcp`, `check_docs_japanese.py`.

## Completion criteria
- No sentence claims a shared server-side `audit.log`; the destinations match the code; checkers pass.

## Out of Scope
- Other MCP documents
- Agent-side audit documentation

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the documentation edit per Implementation > Procedure | Pending | — | — | |
| 2 | Run the documentation checkers named in `routing.md` Tools "When to run which tool" | Pending | — | — | |

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
- **Requirement ID**: `REQ-005` (documentation states where audit and application logs are written)
- **Source issue**: issues/20261023-114126_mcpstart005_server-level-audit-records-are-dropped-for-six-mcp-servers.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261023-115910_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261023-124124
- **Related target files**: docs/22_mcp/mcp_06_06_end-to-end-tool-call-tracing.md
