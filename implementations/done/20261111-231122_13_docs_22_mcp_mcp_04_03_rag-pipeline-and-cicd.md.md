## Goal

Replace the audit line in `mcp_04_03` that states rag-pipeline-mcp writes no shared/dedicated audit log, so it reflects the new Layer 2 record (`REQ-006`, `AC-6`).

## Scope
**Release unit**: N/A: not part of a release unit

## Assumptions
- Line 46 currently reads: "Logs: `rag-mcp.log` in the log directory. Audit: Layer1 `tool_exec` only; no shared or dedicated audit log."
- After this change rag-pipeline-mcp emits the shared `mcp_tool_exec` record via `_audit_log()` into `rag-mcp.log` (row 01).

## Design decisions
- Change the audit clause to state that rag-pipeline-mcp writes both the agent-side Layer 1 `tool_exec` and the server-side Layer 2 `mcp_tool_exec` shared audit log.

## Alternatives considered
- Leaving "no shared or dedicated audit log": contradicts the implemented behavior. Rejected: correct it.

## Implementation
### Target file
`docs/22_mcp/mcp_04_03_rag-pipeline-and-cicd.md`

### Procedure
1. Line 46: replace "Audit: Layer1 `tool_exec` only; no shared or dedicated audit log" with "Audit: Layer1 `tool_exec` (agent-side) and Layer2 `mcp_tool_exec` shared audit log via `mcp_servers.audit._audit_log()` into `rag-mcp.log`".

### Method
- One targeted sentence edit.

### Details
- Consistent with `mcp_06_05` (row 12) Layer 2 definition.

### Companion test files
N/A.

## Compatibility considerations
- Consistent with `mcp_02_03` (row 11) and `mcp_06_05` (row 12).

## Security considerations
- Correctly attributes server-side audit coverage to rag-pipeline-mcp.

## Rollback considerations
Revert the commit.

## Validation plan
| Target | Strategy | Command | Expected |
|---|---|---|---|
| `mcp_04_03_rag-pipeline-and-cicd.md` | Structure/policy | `uv run python tools/check_docs_quality.py` | Pass |

## Completion criteria
- `mcp_04_03` line 46 no longer says rag-pipeline-mcp writes no shared audit log.

## Out of Scope
- Other `mcp_04_03` content.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Replace the audit line (line 46) | Completed | — | 20261112-051032 | line 46 rewritten to match implemented record: server_key=rag_pipeline, target=url for rag_delete_document, disabled-tool rejection writes no record |
| 2 | Run `check_docs_quality.py` (`rules/toolchain.md`) | Completed | — | 20261112-051032 |  |

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
- **Requirement ID**: `REQ-006` — `mcp_04_03` no longer says rag-pipeline-mcp writes no audit log.
- **Source issue**: issues/20261109-113023_adrrev011_mcp-audit-auth-adr.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261111-095422_adrrev011_mcp-audit-auth-adr.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261111-231122
- **Related target files**: `docs/22_mcp/mcp_04_03_rag-pipeline-and-cicd.md`