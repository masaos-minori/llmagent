## Goal

Align ADR-008's ownership descriptions with the implemented dedup contracts and reference pending
AAL-028 as open (REQ-003, REQ-004, REQ-008, AC-2, AC-3).

## Scope
**Release unit**: N/A: not part of a release unit

## Assumptions
- The ADR is 54865 B, which equals its `SIZE_EXCEPTIONS` ceiling in
  `tools/check_docs_structure.py` (re-verified 20261126), so every edit must be size-neutral.
- AAL-024, AAL-025, AAL-039 are already recorded as approved in the Approval Record; only
  AAL-028 (line 416) is pending, so the Issue's "pending ledger entries" claim is stale for the
  approved entries.
- The lease state machine and the warning-only store-write path are implemented in
  `scripts/shared/mcp_dedup.py`; the warning-only path is described as an open exception, not
  resolved.

## Design decisions
- Edits are replacement-style so the file stays at its ceiling.
- Ownership is stated in the Plan's vocabulary: the shared MCP dispatcher owns the store, the
  owner lease, and terminal evidence; the Agent owns intent, approval, and retry orchestration.

## Alternatives considered

N/A: the ADR already owns the store-separation decision; only the ownership wording and the
open-item reference are aligned.

## Implementation
### Target file
`docs/10_adr/adr_02_05_008_db-six-sqlite-store-separation.md`
### Procedure
- Rewrite the dedup-store ownership descriptions to match the implemented lease and store-write
  behavior in `scripts/shared/mcp_dedup.py`.
- Reference pending AAL-028 as open; write no approval text.
### Method
- Measure the file before and after each replacement; the size must be unchanged. If a required
  addition cannot be size-neutral, re-record the ceiling in `tools/check_docs_structure.py` per
  its recorded convention and report it.
### Details
- Proving tests for the changed claims: `tests/shared/test_mcp_dedup.py`
  (`test_acquire_creates_owned_pending_row`, `test_owner_finalizes_completed_and_replay`).

## Compatibility considerations

N/A: the ADR is governance-consumed; the governance file is referenced, not edited.

## Security considerations

N/A: no control is changed; the fail-closed behavior after store loss is described as implemented.

## Rollback considerations

N/A: revert the commit.

## Validation plan

- `uv run python tools/check_adr_structure.py`, `check_docs_quality.py`,
  `check_docs_structure.py`, `check_docs_content_policy.py`, `check_docs_consistency.py --domain mcp`
- `uv run pytest tests/shared/test_mcp_dedup.py`
- Size check: the file stays at or below 54865 B.

## Completion criteria

- The ownership description matches the implemented dedup contracts, AAL-028 is referenced as
  open, no approval text is written, and the file is within its recorded ceiling.

## Out of Scope

- No dedup behavior change; no approval for AAL-028.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 20261126-234310 | 20261126-234310 | Ownership paragraph rewritten to the Plan vocabulary (dispatcher: store, schema creation, canonical-shape validation, owner lease, terminal evidence; Agent: intent, approval, workflow state, retry orchestration) with the two proving tests. Stale claim corrected: tools/check_db_separation.py covers five stores (mcp_dedup registered for ownership and path), not four; mdq.sqlite still uncovered. AAL-028 confirmed already referenced as pending (no approval text written); AAL-024/025/039 confirmed approved. Warning-only store-write path stays described as open exception MCP-002 in ADR-004, not restated here (size ceiling). |
| 3 | Run the ADR and docs checkers (`rules/tool-gates.md`) and the cited proving test | Completed | 20261126-234310 | 20261126-234310 | check_adr_structure + docs checkers pass; size 54845 B (within 54865 B ceiling); 100 passed (tests/shared/test_mcp_dedup.py) |

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
- **Requirement ID**: `REQ-004` (ADR-008 dedup ownership alignment)
- **Source issue**: issues/20261119-140519_mcpai012_mcp-design-docs-update.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261126-072155_mcpai012_mcp-design-docs-update.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261126-212443
- **Related target files**: `docs/10_adr/adr_02_05_008_db-six-sqlite-store-separation.md`