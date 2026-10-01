## Goal
- Add the new governance document to the governance document guide's navigation tables (REQ-005).

## Scope
- In: the changes listed under Implementation > Details in `docs/00_governance/governance_00_document-guide.md`.
- Out: every other file and every unlisted part of `docs/00_governance/governance_00_document-guide.md`.

## Assumptions
- `## Reading Order` and `## AI Query Routing` tables list governance_01 to governance_04 only (re-verified 2026-10-01).
- Execution order across this Plan's procedures follows Plan Implementation steps: Step 1 baseline -> Step 2 (seq 01 Part A) -> Step 3 (seq 02) -> Step 4 (seq 06, 07, 08) -> Step 5 (seq 01 Part B) -> Step 6 (seq 03) -> Step 7 (seq 04, 05) -> Step 8 verification.

## Design decisions
- Append one row to each table after the governance_04 row; keep table formatting.

## Alternatives considered
- N/A: two table rows.

## Implementation
### Target file
- `docs/00_governance/governance_00_document-guide.md`

### Procedure
1. Confirm the prerequisite procedures named in Assumptions are Completed.
2. Apply the changes in Details, in the listed order.
3. Run the Validation plan and compare with the Plan Design baseline.
4. Record results in Execution Status Notes.

### Method
- Targeted edits only; confirm with `git diff docs/00_governance/governance_00_document-guide.md` that nothing outside Details changed.

### Details
- `## Reading Order`: add a row with Category `Change Impact and Dependency Graphs` and File `governance_05_change-impact-and-dependency-graphs.md` (file name in backticks, as in the existing rows).
- `## AI Query Routing`: add a row with Question `Change impact, RACI model, dependency graphs` and Rule `governance_05` (in backticks, as in the existing rows).

## Compatibility considerations
- Navigation only.

## Security considerations
- N/A: documentation/tool path change only; no secrets, network access, or runtime behavior beyond which file the checker reads.

## Rollback considerations
- Revert with `git checkout -- docs/00_governance/governance_00_document-guide.md` (or delete the file if newly created). Revert seq 01 Part B before seq 02/06 to keep the graph checker passing.

## Validation plan
- `uv run python tools/check_docs_structure.py docs/00_governance/governance_00_document-guide.md` — no new finding.
- `uv run python tools/check_docs_quality.py` — no new line for this file.

## Completion criteria
- Both tables contain the new document; no other change.

## Out of scope
- Rule wording changes; stale-path cleanup (`govpath001`); `## Area Canonical Maps` (`canon001`); ADR quotes (`langdoc001`); the external-behavior matrix discrepancy (`issues/20261001-112149_unknowns.md`).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Confirm seq 02 Completed | Completed | 20261001-155700 | 20261001-155715 | seq 02 Completed and archived |
| 2 | Add the two table rows | Completed | 20261001-155700 | 20261001-155715 | Added one row to each of the two tables |
| 3 | Run Validation plan | Completed | 20261001-155700 | 20261001-155715 | Structure check passed, quality findings unchanged |

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
- **Requirement ID**: REQ-005 (governance navigation) — Plan Implementation steps Step 7
- **Source issue**: issues/20261001-104656_docsize001_reduce-documentation-policy-below-structure-size-limit.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261001-112149_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261001-121155
- **Related target files**: docs/00_governance/governance_00_document-guide.md