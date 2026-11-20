## Goal

- Register the pending EventBus producer and consumer item as one new Needs Confirmation entry with a unique identifier (`REQ-001`), close SHARED-001 by removing its ledger entry (`REQ-005`), and replace the line numbers in the SHARED-002 entry with section names (`REQ-006`).

## Scope
**Release unit**: N/A: not part of a release unit

- Plan steps 1 and 2. Execute this document together with the ADR-006 and ADR-013 procedures (step 1: they cite the new identifier) and the ADR-008 procedure (step 2: it removes the SHARED-001 bullet in the same change set, because the sync check reports a dangling reference otherwise).

## Assumptions

- The new identifier is the next free number after NC-002 (expected NC-003); read Part 2 at edit time. `NC-` is the only inventory prefix, so the number is unique across Part 2.
- The entry records the question only: `Assigned To` is the maintainer, no decision and no approval text is written (Plan Assumption A3).
- SHARED-001 is closed on this evidence: `test_run_integrity_check_keeps_rollback_journal_mode` passes and the classification path opens the database read-only (`scripts/db/recovery.py`, `_run_integrity_check(..., read_only=True)`); if the test fails when re-run, stop and report (Plan Assumption A4).
- For SHARED-002 only the line numbers are replaced: verified against current source (Step 3a, 2026-11-20) — the ADR-008 `System of record` row no longer lists `memories_vec` and the `Derived or rebuildable data` row lists `memories_fts, memories_vec (from memories)`; AAL-027 records the pending approval. The ledger `Current Description` is therefore restated in the past tense (the mismatch as first found) with row names instead of line numbers; do not change the entry's status or substance, and report the staleness (Plan UNK-03).

## Design decisions

- Resolved items are removed from the ledger, not kept with a closed status (Part 1 Status Values), so SHARED-001 is deleted.
- The new item goes into Part 2 (a pending maintainer decision), not Part 1 (Plan D1).

## Alternatives considered

N/A: a text edit; the Plan fixes the change.

## Implementation
### Target file
`docs/00_governance/governance_03_issue-and-uncertainty-management.md`
### Procedure
1. Run `uv run pytest tests/db/test_db_recovery.py -k keeps_rollback_journal_mode -q`; continue only when it passes.
2. Append a new entry after `#### NC-002` in Part 2 `### Active Items` with the fifteen fields listed in Details.
3. Delete the `#### SHARED-001` entry, from its heading to the line before `#### SHARED-002`.
4. In the `#### SHARED-002` entry's `Current Description`, replace the line-number citation with matrix row names in the past tense (the mismatch as first found): `Line 92 lists ... and line 93 lists ...` becomes `The System of record row listed ... and the Derived or rebuildable data row listed ...` naming the same values; change nothing else in the entry.
### Method
- Direct text edits; keep the existing field order and bullet shape of NC-001 and NC-002.
### Details
- `Source File`: `adr_02_04_006_eventbus-sqlite-persistence-and-sse-delivery.md`; `Section`: Decision > item 14 (EventBus producers and consumers); `Line Number`: the current line of that sentence, read at edit time.
- `Question`: which component defines the EventBus producers and consumers, and when is the integration planned. `Evidence`: ADR-006 Decision item 14 and the ADR-013 Caller model status both say the model is not yet defined and no producer or consumer is named.
- `Impact`: until resolved no producer or consumer is named, and the first publisher or consumer client activates ADR-013 `Review Triggers` item 1. `Required Action`: the maintainer decides the defining component and timing; the implementer does not write it.
- `Status`: open; `Assigned To`: maintainer; `Last Reviewed`: the date of the edit; `Priority`: pick from the Part 2 Priority Values (Medium expected); `Related NC`: None; `Resolution Target`: the decision recorded in ADR-006 Decision item 14; `Blocking`: None.

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

- Part 2 holds the new entry with all fifteen fields and a unique identifier (AC-1).
- `grep -n "#### SHARED-001"` returns nothing in this file and the sync check passes once the ADR-008 bullet is removed (AC-4).
- The SHARED-002 entry contains no line number (AC-5).

## Out of Scope

- Approval text, the SHARED-002 decision, and any change to deviation substance.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Register the new entry in Part 2 (Plan step 1) | Completed | 20261120-151320 | 20261120-151320 | NC-003 registered after NC-002 with the 15 Part 2 fields. |
| 2 | Remove SHARED-001 and fix the SHARED-002 line numbers (Plan step 2) | Completed | 20261120-151320 | 20261120-151320 | Same change set as the ADR-008 procedure SHARED-001 entry removed; SHARED-002 Current Description restated with row names instead of line numbers. |
| 3 | Run the validation sequence for this row (Validation plan) | Completed | 20261120-151320 | 20261120-151320 | All checkers in the Validation plan pass. |

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
- **Requirement ID**: `REQ-001` (new inventory entry), `REQ-005` (close SHARED-001), `REQ-006` (SHARED-002 line numbers)
- **Source issue**: issues/20261117-123012_adrchk012_traceability-id-uniqueness.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261120-124329_adrchk012_traceability-id-uniqueness.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261120-125111
- **Related target files**: `docs/00_governance/governance_03_issue-and-uncertainty-management.md`