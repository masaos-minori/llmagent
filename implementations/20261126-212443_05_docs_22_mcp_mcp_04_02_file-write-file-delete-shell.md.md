## Goal

Correct the file-write and file-delete statements and record dry-run parity and the audit order
(REQ-002, AC-1).

## Scope
**Release unit**: N/A: not part of a release unit

## Assumptions
- The guard and postcondition section is at `docs/22_mcp/mcp_04_02_file-write-file-delete-shell.md:28-33`
  (re-verified 20261126).
- The delete side already states that the root guard runs before the `dry_run` branch (line 51);
  the write side does not state dry-run parity, so that is the gap this row fills.
- The audit-order facts come from the mcpai009 implementation, which has landed; the procedure
  states them as implemented behavior.

## Design decisions
- Dry-run parity is stated as one sentence per server: the guard path is shared by dry-run and
  real execution, so a dry-run call is rejected by the same guard as a real call.
- Audit order is stated as where the record is written relative to the postcondition check.

## Alternatives considered

N/A: the section already owns the guard and postcondition description.

## Implementation
### Target file
`docs/22_mcp/mcp_04_02_file-write-file-delete-shell.md`
### Procedure
- Add the write-side dry-run parity statement to the guard section, matching the delete-side
  wording already present at line 51.
- State the audit order for `write_file`: the service-level audit record is written after the
  postcondition check (`scripts/mcp_servers/file/write_service.py`, `_write_audit_log`), so a
  postcondition failure produces no service-level record while the dispatch-level
  `mcp_tool_exec` record still reports `outcome="error"`.
### Method
- Confirm the order against `write_service.py` (`write_file`, `_verify_written_size`,
  `_write_audit_log`) before writing.
### Details
- Proving test: `tests/mcp_servers/file/test_delete_service.py`
  (`test_write_audit_log_creates_file_and_appends`), and
  `tests/mcp_servers/file/test_file_server_audit_records.py` for the dispatch-level record.

## Compatibility considerations

N/A: documentation-only change; the file is shared with mcpai009, judged compatible (that plan
wrote the facts it established; this row sweeps them).

## Security considerations

N/A: no control is changed; the guard behavior is described as implemented.

## Rollback considerations

N/A: revert the commit.

## Validation plan

- `uv run python tools/check_docs_quality.py`, `check_docs_structure.py`,
  `check_docs_content_policy.py`, `check_docs_consistency.py --domain mcp`
- `uv run pytest tests/mcp_servers/file/test_delete_service.py tests/mcp_servers/file/test_file_server_audit_records.py`

## Completion criteria

- Both servers state dry-run parity and the audit order, and each claim cites a proving test
  that exists and passes.

## Out of Scope

- No shell-server change; no change to the write or delete implementation.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | |
| 3 | Run the docs checkers (`rules/tool-gates.md`) and the cited proving tests | Pending | — | — | |

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
- **Requirement ID**: `REQ-002` (file-write and file-delete statements)
- **Source issue**: issues/20261119-140519_mcpai012_mcp-design-docs-update.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261126-072155_mcpai012_mcp-design-docs-update.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261126-212443
- **Related target files**: `docs/22_mcp/mcp_04_02_file-write-file-delete-shell.md`
