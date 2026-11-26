## Goal

Name the audit log types and their authoritative locations consistently in the audit document
(REQ-002, AC-1).

## Scope
**Release unit**: N/A: not part of a release unit

## Assumptions
- The Audit Log Format section is at `docs/22_mcp/mcp_02_03_audit-logging-and-errors.md:20-48`
  (re-verified 20261126).
- The per-server audit code is the authoritative source for the layer names and the servers
  that write the shared audit log; the file-write audit order is confirmed at execution time
  against `scripts/mcp_servers/file/write_service.py` after the mcpai009 audit-order change.

## Design decisions
- Each audit type is named once with its authoritative location (file and function); the
  per-server sections point to it instead of restating the field list.

## Alternatives considered

N/A: the document already owns the audit-format description; only naming consistency is added.

## Implementation
### Target file
`docs/22_mcp/mcp_02_03_audit-logging-and-errors.md`
### Procedure
- Align the audit-log-types section with the implemented layers (`tool_exec`, `mcp_tool_exec`,
  per-server dedicated layers) and name the authoritative location for each.
- Confirm the `outcome` vocabulary (`ok`/`error`/`rejected`) and the servers that write the
  shared audit log against the current code before restating them.
### Method
- Read the audit writer in `scripts/agent/tool_audit.py` and the server audit call sites; cite
  the proving test for each claim this sweep changes.
### Details
- Proving test: `tests/mcp_servers/file/test_file_server_audit_records.py`
  (`test_accepted_call_emits_one_ok_record`, `test_disabled_allowed_dirs_emits_rejected_record`).

## Compatibility considerations

N/A: no pinned counts change; the per-server documents referenced by the map are swept by the
sibling procedures of this Plan.

## Security considerations

N/A: documentation-only change describing existing audit behavior.

## Rollback considerations

N/A: revert the commit.

## Validation plan

- `uv run python tools/check_docs_quality.py`, `check_docs_structure.py`,
  `check_docs_content_policy.py`, `check_docs_consistency.py --domain mcp`
- `uv run pytest tests/mcp_servers/file/test_file_server_audit_records.py`

## Completion criteria

- Every audit type in the file is named once with its authoritative location, and the outcome
  vocabulary matches the code and the cited test.

## Out of Scope

- No audit code change; no per-server audit description outside this file.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | |
| 3 | Run the docs checkers (`rules/tool-gates.md`) and the cited proving test | Pending | — | — | |

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
- **Requirement ID**: `REQ-002` (consistent audit log types and locations)
- **Source issue**: issues/20261119-140519_mcpai012_mcp-design-docs-update.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261126-072155_mcpai012_mcp-design-docs-update.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261126-212443
- **Related target files**: `docs/22_mcp/mcp_02_03_audit-logging-and-errors.md`
