## Goal
Remove ADR-008's Amendment section, rewrite the `removed by compatrm001` Review Trigger as the current trigger, and remove the Amendment Approval Mapping bullet (`REQ-001` / `AC-1`).

## Scope
**Release unit**: N/A: not part of a release unit

## Assumptions
- Line numbers have drifted from the Plan (other Plans edited these files); locate each passage by its quoted text.
- UNK-03 checked in Step 3a: the Amendment's current rule (every database matches the current canonical schema via the shared fingerprint; mismatched files are archived and recreated) is already stated in Context > Constraints (the `rag.sqlite and session.sqlite are recreated ... current-only policy` bullet), so the Amendment can be removed outright.
- `adrrev009` (landed) edited Decision Detail #7 and Known Deviations only; the three passages here are untouched.
- `check_adr_preservation.py` reports the removed Approval-section bullet as an ERROR; that is the intended change and is explained, not suppressed.
- The ADR is over its size ceiling (36197 of 34206, pre-existing); this edit shrinks it, which helps the ceiling re-record chore.
- Overlap with other open Plans is judged compatible in the Plan's Assumptions; touch only the history passages named here.

## Design decisions
- Delete the section `### Amendment (dbmig001, 2026-10-30)` whole; rewrite the trigger as `A migration mechanism is proposed (for example forward-only migrations for workflow.sqlite or eventbus.sqlite) or replicated storage is introduced`.

## Alternatives considered
N/A: the Plan fixes the approach for this row.

## Implementation
### Target file
`docs/10_adr/adr_02_05_008_db-sqlite-4db-separation.md`

### Procedure
1. Compare the Amendment's rule with Context > Constraints and the Recovery text (UNK-03).
2. Delete the Amendment section.
3. Rewrite the Review Trigger bullet that cites compatrm001.
4. Delete the `Amendment Approval Mapping` bullet in the Approval Record.

### Method
- Keep every Decision Detail, invariant, and the current approval bullets unchanged.
- Confirm no other `dbmig001` or `compatrm001` mention remains in the ADR (`rg -n 'dbmig001|compatrm001'`).

### Details
- Removing history is a wording edit, not a decision change (`governance_05`), so no approval record is added; any decision hidden in the passage is first confirmed present in the current sections (UNK-03).
- Report the preservation ERROR in the final report as the maintainer-decided removal of amendment history.

## Compatibility considerations
N/A: documentation-only change; no code, config, or schema impact.

## Security considerations
N/A: no authorization, secret, or trust-boundary change.

## Rollback considerations
N/A: revert the commit.

## Validation plan
- `uv run python tools/check_adr_structure.py`, `check_adr_invariant_matrix.py`, `check_adr_authority.py`, `check_adr_preservation.py`, `generate_adr_authority.py --check` — pass; preservation reports only the removed Amendment text.
- `uv run python tools/check_docs_quality.py`, `check_docs_structure.py`, `check_docs_content_policy.py --strict`, `check_docs_japanese.py` — pass.
- `uv run python tools/check_known_deviation_sync.py`, `check_needs_confirmation_inventory.py` — pass (UNK-05).

## Completion criteria
- No Amendment section, plan ID, or amendment date remains; the Review Trigger is current-tense; the Approval Mapping bullet is gone; only intended preservation findings remain.

## Out of Scope
- Known Deviations, Decision Detail #7 (adrrev009); adding approval records.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | |
| 2 | Run the documentation checkers per Validation plan | Pending | — | — | |

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
- **Requirement ID**: `REQ-001` — remove ADR-008 amendment history, keep current policy
- **Source issue**: issues/20261109-113318_adrrev017_docs-history-wording.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261111-110144_adrrev017_docs-history-wording.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261112-123928
- **Related target files**: `docs/10_adr/adr_02_05_008_db-sqlite-4db-separation.md`
