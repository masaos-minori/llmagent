## Goal

Fix Layer 2 (line 56) and the "MCP Servers without Audit Logging" section (line 65) in `mcp_06_05` so only file-read-mcp is listed as writing no audit log (`REQ-006`, `AC-6`).

## Scope
**Release unit**: N/A: not part of a release unit

## Assumptions
- Line 56 states Layer 2 ("`mcp_tool_exec` in the server's own application log") covers "all servers except file-read-mcp and rag-pipeline-mcp".
- Line 65 states "file-read-mcp and rag-pipeline-mcp write no audit logs."
- After this change rag-pipeline-mcp writes the shared record (row 01), so only file-read-mcp remains without an audit log.

## Design decisions
- Remove rag-pipeline-mcp from both the Layer 2 exception and the "without Audit Logging" section, leaving file-read-mcp as the sole no-audit-log server.

## Alternatives considered
- Editing only one location: the two statements would diverge. Rejected: fix both line 56 and line 65.

## Implementation
### Target file
`docs/22_mcp/mcp_06_05_reading-audit-logs.md`

### Procedure
1. Line 56: change "all servers except file-read-mcp and rag-pipeline-mcp" to "all servers except file-read-mcp".
2. Line 65: change "file-read-mcp and rag-pipeline-mcp write no audit logs" to "file-read-mcp writes no audit logs".

### Method
- Two targeted sentence edits; preserve the surrounding layer description and the line 49 note about cicd-mcp/git-mcp/mdq-mcp.

### Details
- rag-pipeline-mcp still writes its application log `rag-mcp.log`; the audit record lands there as Layer 2.

### Companion test files
N/A.

## Compatibility considerations
- Consistent with `mcp_02_03` (row 11) and `mcp_04_03` (row 13).

## Security considerations
- Correctly attributes server-side audit coverage to rag-pipeline-mcp.

## Rollback considerations
Revert the commit.

## Validation plan
| Target | Strategy | Command | Expected |
|---|---|---|---|
| `mcp_06_05_reading-audit-logs.md` | Structure/policy | `uv run python tools/check_docs_quality.py` | Pass |

## Completion criteria
- Only file-read-mcp is listed as writing no audit log in `mcp_06_05`.

## Out of Scope
- Other `mcp_06_05` content.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Fix Layer 2 (line 56) and the without-audit-logging section (line 65) | Completed | — | 20261112-050628 |  |
| 2 | Run `check_docs_quality.py` (`rules/toolchain.md`) | Completed | — | 20261112-050628 |  |

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
- **Requirement ID**: `REQ-006` — `mcp_06_05` no longer says rag-pipeline-mcp writes no audit log.
- **Source issue**: issues/20261109-113023_adrrev011_mcp-audit-auth-adr.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261111-095422_adrrev011_mcp-audit-auth-adr.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261111-231122
- **Related target files**: `docs/22_mcp/mcp_06_05_reading-audit-logs.md`