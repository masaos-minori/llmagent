## Goal

Align the fail-open/fail-closed and risk-tier statements with the implemented contracts, and
reference the open exceptions without resolving them (REQ-002, REQ-004, AC-1, AC-2).

## Scope
**Release unit**: N/A: not part of a release unit

## Assumptions
- The Fail-Open vs Fail-Closed Summary table is at
  `docs/22_mcp/mcp_05_03_fail-open-fail-closed-and-risk-tiers.md:20-32` (re-verified 20261126).
- `path_denylist` is recorded there as a registered ADR-004 exception whose rationale is
  pending; per the owner decision of 20261126 the exception is referenced as open
  (MCP-001, MCP-002 in `docs/00_governance/governance_03_issue-and-uncertainty-management.md`),
  not resolved.
- The store_error overlay path is documented in `docs/22_mcp/mcp_03_03_transport-and-health.md`;
  this row cites it rather than restating it (`skills/DESIGN.md`, no implementation-reference
  duplication).

## Design decisions
- Risk-tier statements use the ownership vocabulary: Agent owns intent, approval, workflow
  state, and retry orchestration; MCP owns final pre-handler enforcement, owner lease, and
  terminal evidence.
- Only unresolved limitations are listed in the Known Issues wording (AC-3).

## Alternatives considered

N/A: the summary table already owns the fail-open/fail-closed description; only the open-exception
references and the ownership wording are aligned.

## Implementation
### Target file
`docs/22_mcp/mcp_05_03_fail-open-fail-closed-and-risk-tiers.md`
### Procedure
- Check each control row against the implementation and correct any policy statement that
  contradicts the code.
- Add the open-exception references (MCP-001, MCP-002) to the fail-open row, and the
  store_error overlay path reference to the dedup failure behavior.
### Method
- Verify each control with `rg` against the server's guard code before writing it.
### Details
- Proving test: `tests/mcp_servers/test_mcp_dispatch.py`
  (`test_store_error_retryable_proceeds_non_retryable_fails_closed`).

## Compatibility considerations

N/A: documentation-only change; the governance file is referenced, not edited.

## Security considerations

N/A: no control is changed; the policies are described as implemented.

## Rollback considerations

N/A: revert the commit.

## Validation plan

- `uv run python tools/check_docs_quality.py`, `check_docs_structure.py`,
  `check_docs_content_policy.py`, `check_docs_consistency.py --domain mcp`
- `uv run pytest tests/mcp_servers/test_mcp_dispatch.py`

## Completion criteria

- Every control row matches the implementation, the open exceptions are referenced as open, and
  the changed claims cite a proving test that passes.

## Out of Scope

- No approval text; MCP-001, MCP-002, NC-001, NC-002 are not resolved.

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
- **Requirement ID**: `REQ-002` (risk-tier statements), `REQ-004` (ownership alignment)
- **Source issue**: issues/20261119-140519_mcpai012_mcp-design-docs-update.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261126-072155_mcpai012_mcp-design-docs-update.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261126-212443
- **Related target files**: `docs/22_mcp/mcp_05_03_fail-open-fail-closed-and-risk-tiers.md`
