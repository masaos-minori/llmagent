# Implementation Procedure: docs/10_adr/adr_02_05_008_db-sqlite-4db-separation.md

## Goal
Rewrite the four migration-policy surfaces of ADR-02/05/008 to the current-only policy: migration
contract text, dbmig001 amendment supersession note, schema-repair vocabulary, and the
re-evaluation trigger.

## Scope
- Target file: `docs/10_adr/adr_02_05_008_db-sqlite-4db-separation.md` (MODIFY).
- Release unit: `policy-finalization`.
- Related requirement / acceptance criteria: REQ-005, REQ-006 / AC-004 (frozen target row 9).

## Assumptions
- Anchors grep-verified: line 60 (migration contract), lines 73-75 (dbmig001 Amendment), line 137
  (schema-repair vocabulary), line 363 (re-evaluation trigger).
- compatrm001's plan owns the schema-startup narrative; this document edit is the terminology and
  trigger rewrite only — no section restructure.

## Verification findings (adversarial re-verification 2026-11-07, HEAD `be4d74463`)

- Four surfaces edited, matching the measured flag sites (lines 60, 75, 363 at execution time):
  Constraints bullet rewritten to the current-only policy (startup gate refuses legacy marker
  tables; archive-and-recreate; "Migration design beyond these two domains" removed); the
  `### Amendment (dbmig001, 2026-10-30)` subsection prefixed with a supersession paragraph
  (mechanism removed by plan `plans/done/20261107-061846_plan.md` compatrm001, paragraph retained
  as historical record); the schema-repair vocabulary entry rewritten to archive-and-recreate as
  the only repair path; the Review Trigger "A migration mechanism is introduced..." rewritten to
  reintroduction-requires-re-evaluation wording.

## Design decisions
- Amendment blocks are history: line 73-75 gains a supersession note (`Superseded 2026-11-07:
  the migration machinery described here was removed; schema must match the code exactly`) instead
  of deletion.
- Line 60 contract becomes: schema created only by the canonical creation path; mismatch is a
  startup failure, not a migration event.
- Line 137 vocabulary: schema-repair guidance re-anchored to the archive-and-recreate runbook
  (doc 10 owns the runbook text).
- Line 363 re-evaluation trigger keeps its decision hook but states that introducing any
  migration path would require a new ADR — historical marker on the retired mechanism name.

## Alternatives considered
- Deleting the amendment section: rejected — ADR immutability convention.
- Moving all migration text to db_03 docs: rejected — the ADR is the policy authority; docs 11-13
  describe implementation, not policy.

## Implementation

### Target file
- `docs/10_adr/adr_02_05_008_db-sqlite-4db-separation.md` (MODIFY).

### Procedure
1. Line 60: replace migration-contract sentence with current-only startup contract wording.
2. Lines 73-75: append the supersession note to the dbmig001 Amendment block.
3. Line 137: rewrite the schema-repair vocabulary entry to reference archive-and-recreate.
4. Line 363: rewrite the re-evaluation trigger sentence with historical markers on retired names.
5. Whole-file sweep for present-tense migration claims (the five doc-claim phrases); mark or
   remove.

### Method
- Section-anchored text edits; checker doc-claim pass afterwards.

### Details
- Every retired mechanism mention keeps a marker word (`superseded`, `removed`, `historical`,
  `was:`) on or above the line (10-line window rule).
- `user_version` (EventBus stamp) stays described as live — it is not a retired mechanism.

## Compatibility considerations
- Governance-docs-consistency CI and `tools/check_adr_invariant_matrix.py` must stay green.

## Security considerations
- None.

## Rollback considerations
- Single-file revert.

## Validation plan
- Checker blocking run exit 0; ADR invariant matrix CI; docs structure/consistency CI.

## Completion criteria
- Four anchors rewritten per Design decisions; zero unmarked migration claims; CI green.

## Out of Scope
- Other ADR files; db docs (docs 11-13).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Line 60 contract | Completed | 20261107-184026 | 20261107-184026 |  |
| 2 | Lines 73-75 supersession | Completed | 20261107-184026 | 20261107-184026 |  |
| 3 | Line 137 vocabulary | Completed | 20261107-184026 | 20261107-184026 |  |
| 4 | Line 363 trigger | Completed | 20261107-184026 | 20261107-184026 |  |
| 5 | Phrase sweep | Completed | 20261107-184026 | 20261107-184026 |  |
### Blocker Log
- None.

### Work Items Created
- None.

## Traceability
- **Workflow phase**: plan-to-implementation-procedure
- **Requirement ID**: REQ-005, REQ-006 / AC-004
- **Source issue**: issues/20261106-125145_compatrm004_finalize-no-compatibility-policy-across-ci-tests-docs.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261107-064415_compatrm004_finalize-no-compatibility-policy-across-ci-tests-docs.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261107-103000
- **Related target files**: `docs/10_adr/adr_02_05_008_db-sqlite-4db-separation.md`