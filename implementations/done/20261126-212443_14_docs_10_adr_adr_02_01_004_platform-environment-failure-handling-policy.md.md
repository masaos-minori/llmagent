## Goal

Align ADR-004's ownership and failure-contract descriptions with the implementation, referencing
the open governance items and pending AAL entries without resolving them (REQ-003, REQ-004,
REQ-008, AC-2, AC-3).

## Scope
**Release unit**: N/A: not part of a release unit

## Assumptions
- The ADR is 36992 B, which equals its `SIZE_EXCEPTIONS` ceiling in
  `tools/check_docs_structure.py` (re-verified 20261126), so every edit must be size-neutral.
- Pending entries are AAL-003 (line 352) and AAL-019 (line 353); AAL-002 is already recorded as
  approved (line 350), so the Issue's "pending ledger entries" claim is stale for AAL-002.
- MCP-001, MCP-002, NC-001, NC-002 are open in
  `docs/00_governance/governance_03_issue-and-uncertainty-management.md` and are referenced as
  open, not resolved.

## Design decisions
- Edits are replacement-style: a description is rewritten in place, no text is appended, so the
  file size stays at the ceiling.
- Only unresolved behavior is listed as a limitation (AC-3); the pending AAL entries are cited by
  ID as awaiting maintainer approval.

## Alternatives considered

N/A: the ADR already owns the failure-handling decision; only the ownership wording and the
open-item references are aligned.

## Implementation
### Target file
`docs/10_adr/adr_02_01_004_platform-environment-failure-handling-policy.md`
### Procedure
- Rewrite the ownership descriptions to the Plan's vocabulary (Agent owns intent, approval,
  workflow state, retry orchestration; MCP owns final pre-handler enforcement, owner lease,
  terminal evidence).
- Reference MCP-001, MCP-002, NC-001, NC-002 and pending AAL-003/AAL-019 as open items; write no
  approval text.
### Method
- Measure the file before and after each replacement; the size must be unchanged. If a required
  addition cannot be size-neutral, re-record the ceiling in `tools/check_docs_structure.py` per
  its recorded convention and report it.
### Details
- The exception rows that name a pending rationale must point to the governance item by ID rather
  than state an outcome.

## Compatibility considerations

N/A: the ADR is governance-consumed; the governance file is referenced, not edited.

## Security considerations

N/A: no control is changed; the fail-closed behavior is described as implemented.

## Rollback considerations

N/A: revert the commit.

## Validation plan

- `uv run python tools/check_adr_structure.py`, `check_docs_quality.py`,
  `check_docs_structure.py`, `check_docs_content_policy.py`, `check_docs_consistency.py --domain mcp`
- Size check: the file stays at or below 36992 B.

## Completion criteria

- No ADR statement contradicts the implementation, the open items and pending AAL entries are
  referenced as open, no approval text is written, and the file is within its recorded ceiling.

## Out of Scope

- No resolution of MCP-001, MCP-002, NC-001, NC-002; no approval for AAL-003 or AAL-019.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 20261126-234310 | 20261126-234310 | Size-neutral rewrites of the two dedup exception rows to the Plan ownership vocabulary (MCP layer: final pre-handler enforcement, owner lease, terminal evidence; Agent: retry orchestration). Stale citation corrected: scripts/shared/mcp_dedup.py has no _write(); the warning-only write path is dispatch.py _store_op(). NC-002 added to the Group 2 item 7 PENDING marker (was ID-less). MCP-001/MCP-002/NC-001/AAL-003/AAL-019 already referenced as open; AAL-002 confirmed approved (issue claim stale). File size unchanged at 36992 B. |
| 3 | Run the ADR and docs checkers (`rules/tool-gates.md`) | Completed | 20261126-234310 | 20261126-234310 | check_adr_structure + docs checkers pass; size 36992 B (at ceiling, unchanged) |

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
- **Requirement ID**: `REQ-004` (ADR-004 ownership and failure-contract alignment)
- **Source issue**: issues/20261119-140519_mcpai012_mcp-design-docs-update.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261126-072155_mcpai012_mcp-design-docs-update.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261126-212443
- **Related target files**: `docs/10_adr/adr_02_01_004_platform-environment-failure-handling-policy.md`