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
- `check_adr_preservation.py` expectation (verified empirically in Step 3a, 2026-11-20): the deliberate bullet deletion reports exactly one intended ERROR — `section 'Known Deviations' text changed` — and nothing else (front matter, H2 sequence, invariants, test citations unchanged). Per `tools/_validation_gate_defs.py` and `governance_04` the gate is scenario-gated to ADRs shortened or reworded *without intending* to change decisions, and is hand-run only (not wired into pre-commit or CI); this edit is deliberate under the owner-approved Plan, so the ERROR is the expected signal, recorded in the Execution Status Notes and the Final Report. The Plan's Validation plan blanket `No ERROR` row is a wording mismatch, not a blocker.

## Completion criteria

- ADR-008 `## Known Deviations` no longer cites SHARED-001 and the sync check passes together with the ledger change (AC-4).

## Out of Scope

- The SHARED-002 bullet and every other ADR-008 section.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Remove the SHARED-001 bullet (Plan step 2) | Completed | 20261120-151320 | 20261120-151320 | Same change set as the governance_03 procedure SHARED-001 bullet removed; check_adr_preservation reports [ERROR] section Known Deviations text changed as the expected signal for this deliberate deletion (tool not wired into pre-commit or CI). |
| 2 | Run the validation sequence for this row (Validation plan) | Completed | 20261120-151320 | 20261120-151320 | All checkers in the Validation plan pass; known-deviation-sync reverse check clean because the ledger entry was removed in the same change set. |

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