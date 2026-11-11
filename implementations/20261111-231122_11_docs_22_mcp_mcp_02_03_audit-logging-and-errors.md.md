## Goal

Add rag-pipeline-mcp to the audit-writing server list and fix the Note in `mcp_02_03` so only file-read-mcp is listed as writing no audit log (`REQ-006`, `AC-6`).

## Scope
**Release unit**: N/A: not part of a release unit

## Assumptions
- Line 22 lists the audit-writing servers and states "file-read-mcp and rag-pipeline-mcp write no audit log".
- Line 44's Note states "file-read-mcp and rag-pipeline-mcp do not write audit logs".
- After this change rag-pipeline-mcp writes the shared `mcp_tool_exec` record (row 01), so only file-read-mcp remains without an audit log.

## Design decisions
- Insert `rag-pipeline-mcp` into the server list on line 22 and change the trailing clause to name only file-read-mcp as the no-audit-log server.
- Update the Note on line 44 to drop rag-pipeline-mcp from the no-audit-log pair.

## Alternatives considered
- Editing only one of the two locations: the two statements would diverge. Rejected: fix both line 22 and line 44.

## Implementation
### Target file
`docs/22_mcp/mcp_02_03_audit-logging-and-errors.md`

### Procedure
1. Line 22: add `rag-pipeline-mcp` to the list of audit-writing servers; change "file-read-mcp and rag-pipeline-mcp write no audit log" to "file-read-mcp writes no audit log".
2. Line 44: change "file-read-mcp and rag-pipeline-mcp do not write audit logs" to "file-read-mcp does not write audit logs".

### Method
- Two targeted sentence edits; preserve the surrounding table and other server names.

### Details
- The `target` field row (line 33) notes rag-pipeline-mcp records the truncated URL; consistent with rag-pipeline-mcp now writing the shared log.

### Companion test files
N/A.

## Compatibility considerations
- Consistent with `mcp_06_05` (row 12) and `mcp_04_03` (row 13), which make the same correction.

## Security considerations
- Correctly attributes server-side audit coverage to rag-pipeline-mcp.

## Rollback considerations
Revert the commit.

## Validation plan
| Target | Strategy | Command | Expected |
|---|---|---|---|
| `mcp_02_03_audit-logging-and-errors.md` | Structure/policy | `uv run python tools/check_docs_quality.py` | Pass |

## Completion criteria
- `mcp_02_03` lists rag-pipeline-mcp as an audit-writing server and names only file-read-mcp as writing no audit log.

## Out of Scope
- Other `mcp_02_03` content.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Add rag-pipeline-mcp to the list (line 22) and fix the Note (line 44) | Pending | — | — | |
| 2 | Run `check_docs_quality.py` (`rules/toolchain.md`) | Pending | — | — | |

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
- **Requirement ID**: `REQ-006` — `mcp_02_03` no longer says rag-pipeline-mcp writes no audit log.
- **Source issue**: issues/20261109-113023_adrrev011_mcp-audit-auth-adr.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261111-095422_adrrev011_mcp-audit-auth-adr.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261111-231122
- **Related target files**: `docs/22_mcp/mcp_02_03_audit-logging-and-errors.md`
