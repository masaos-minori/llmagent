## Goal

- Remove the SHARED-001 bullet from `## Known Deviations`, because SHARED-001 is fixed in code and its ledger entry is removed (`REQ-005`).

## Scope
**Release unit**: N/A: not part of a release unit

- Plan step 2. Execute in the same change set as the `governance_03` procedure: removing the ledger entry alone leaves a dangling reference here, and removing this bullet alone leaves an uncited open entry.

## Assumptions

- The Issue's claim that this section reads `Not applicable` does not hold: the section lists the SHARED-001 and SHARED-002 bullets (checked in the plan-to-implementation-procedure cycle).
- The SHARED-002 bullet stays unchanged (its status is open until the AAL-027 approval is recorded).

## Design decisions

- Remove only the bullet; do not rewrite the section or add a resolution note (Current-Specification-Only policy).

## Alternatives considered

N/A: a text edit; the Plan fixes the change.

## Implementation
### Target file
`docs/10_adr/adr_02_05_008_db-sqlite-4db-separation.md`
### Procedure
1. In `## Known Deviations`, delete the bullet that starts `- **Known Issue:** SHARED-001`.
2. Leave the SHARED-002 bullet and the section heading as they are.
### Method
- Direct bullet deletion.
### Details
- Do not add `Not applicable`; the section still holds the SHARED-002 bullet.

## Compatibility considerations

N/A: documentation row; no decision text changes.

## Security considerations

N/A: documentation row.

## Rollback considerations

N/A: revert the commit.

## Validation plan

- `uv run python tools/check_docs_quality.py`, `uv run python tools/check_docs_structure.py`, `uv run python tools/check_docs_content_policy.py`, `uv run python tools/check_docs_japanese.py`.
- `uv run python tools/check_known_deviation_sync.py`, `uv run python tools/check_needs_confirmation_inventory.py`, `uv run python tools/check_adr_structure.py`, `uv run python tools/check_adr_preservation.py`.

## Completion criteria

- ADR-008 `## Known Deviations` no longer cites SHARED-001 and the sync check passes together with the ledger change (AC-4).

## Out of Scope

- The SHARED-002 bullet and every other ADR-008 section.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Remove the SHARED-001 bullet (Plan step 2) | Pending | — | — | Same change set as the governance_03 procedure |
| 2 | Run the validation sequence for this row (Validation plan) | Pending | — | — | |

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
- **Requirement ID**: `REQ-005` (close SHARED-001)
- **Source issue**: issues/20261117-123012_adrchk012_traceability-id-uniqueness.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261120-124329_adrchk012_traceability-id-uniqueness.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261120-125111
- **Related target files**: `docs/10_adr/adr_02_05_008_db-sqlite-4db-separation.md`
