## Goal

Extend the Identity Fields table to the single id-definition table with the workflow, session,
request, and call ids (REQ-001, AC-1).

## Scope
**Release unit**: N/A: not part of a release unit

## Assumptions
- The Identity Fields table is at `docs/22_mcp/mcp_06_06_end-to-end-tool-call-tracing.md:60-65`
  and already carries `idempotency_key`, `turn_id`, `task_id`, and `task_linkage`
  (re-verified 20261126, Step 3a — the Step 2 claim that the table lacks the idempotency key is
  stale). The remaining gap is the workflow, session, request, and call ids.
- This table is the single definition of the ids for the MCP area; `docs/22_mcp/mcp_03_01_dispatch-and-routing.md`
  (procedure 02) points to it instead of restating it.

## Design decisions
- The table is extended in place rather than replaced, so the existing rows and the compatibility
  note stay.
- Each id row states where it is generated and where it is observed, matching
  `scripts/agent/tool_call_identity.py`.

## Alternatives considered

N/A: the tracing document already owns the identity-field definition; no alternative location.

## Implementation
### Target file
`docs/22_mcp/mcp_06_06_end-to-end-tool-call-tracing.md`
### Procedure
- Add the workflow, session, request, and call id rows to the Identity Fields table so it is the
  single id-definition table for the area.
- State that replay identity is Agent-managed, consistent with procedure 02's routing document.
### Method
- Verify each id against `scripts/agent/tool_call_identity.py` and the audit record fields in
  `scripts/agent/tool_audit.py` before writing it.
### Details
- Proving test: `tests/mcp_servers/test_execution_context.py`
  (`test_fields_and_stripped_key`, `test_agreeing_header_is_accepted`).

## Compatibility considerations

N/A: the table is additive; readers that treat absent keys as empty strings are unaffected.

## Security considerations

N/A: documentation-only change describing existing identity fields.

## Rollback considerations

N/A: revert the commit.

## Validation plan

- `uv run python tools/check_docs_quality.py`, `check_docs_structure.py`,
  `check_docs_content_policy.py`, `check_docs_consistency.py --domain mcp`
- `uv run pytest tests/mcp_servers/test_execution_context.py`

## Completion criteria

- The file holds one id-definition table covering workflow, task, turn, call, session, request
  ids and the idempotency key, and the changed claims cite a proving test that passes.

## Out of Scope

- No change to the audit record format or to the identity generation code.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 20261126-234310 | 20261126-234310 | Added call_id, workflow_id, session_id, request_id rows and the Agent-managed replay statement. Step 3b finding: the cross-layer correlation claim was stale — github_audit.log carries session/request/call via build_write_audit_fields (scripts/shared/write_outcome.py), so the claim now covers only shell_audit.log and delete_audit.log. |
| 3 | Run the docs checkers (`rules/tool-gates.md`) and the cited proving test | Completed | 20261126-234310 | 20261126-234310 | docs checkers pass; 81 passed (execution_context, write_outcome, github_write_outcomes, tool_preparation) |

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
- **Requirement ID**: `REQ-001` (single id-definition table)
- **Source issue**: issues/20261119-140519_mcpai012_mcp-design-docs-update.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261126-072155_mcpai012_mcp-design-docs-update.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261126-212443
- **Related target files**: `docs/22_mcp/mcp_06_06_end-to-end-tool-call-tracing.md`