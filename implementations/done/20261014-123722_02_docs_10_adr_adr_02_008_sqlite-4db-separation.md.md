## Goal

SQLite 4-DB ADR: Remove approvals from Decision 3 (line 112), INV-03 (line 338), the Domain table (line 88), the Recovery Policy Matrix (line 100), and Implementation References (line 527) (REQ-001: record the owner decision and apply the ADR changes).

## Scope

- Remove approvals from Decision 3 (line 112), INV-03 (line 338), the Domain table (line 88), the Recovery Policy Matrix (line 100), and Implementation References (line 527); add a Decision Change line of 140 bytes or less (141 including its newline, because the edits leave 141 bytes of budget)

## Assumptions

- Plan `plans/20261014-114443_plan.md` is `Frozen`; this file is one of its `Implementation Target Files` rows.
- Apply only after the repository owner's decision (Plan Step 1) is recorded, together with every other procedure of this plan (Steps 2-11) as one commit unit.
- Line numbers come from the Plan and may shift; locate edits by symbol, test name, or section.

## Design decisions

- This edit changes an Accepted ADR decision: the owner's recorded decision (Plan Step 1) is a precondition and the same change must update every affected document and verification.
- Use unregistered wording only; do not renumber invariants.

## Alternatives considered

N/A: the docs follow the code removal

## Implementation

### Target file

`docs/10_adr/adr_02_008_sqlite-4db-separation.md`

### Procedure

Remove approvals from Decision 3 (line 112), INV-03 (line 338), the Domain table (line 88), the Recovery Policy Matrix (line 100), and Implementation References (line 527); add a Decision Change line of 140 bytes or less (141 including its newline, because the edits leave 141 bytes of budget).

### Method

Evidence recorded in the Plan: `adr_02_008_sqlite-4db-separation.md` lines 88, 100, 527. Locate the places with a case-sensitive search for the removed names in this file, edit by symbol or section, then format the file.

### Details

- Remove the word Approvals from Decision 3 and INV-03 (workflow.sqlite is the canonical store for Tasks, Attempts, Artifacts, and processed Events), remove approvals from the Domain table cell, remove the clause that pending approvals are recovered at Agent startup from the Recovery Policy Matrix cell (keep none automated, manual operator handling), and remove approvals from the Implementation References entry.
- Size budget: the file is 33636 bytes and tools/check_docs_structure.py allows 33647; the five removals save 130 bytes, so the new Decision Change line may be at most 140 bytes plus its newline. A fitting line: - **Decision Change (YYYY-MM-DD)**: Task-level approval decision (repository owner); approvals removed from Decision #3 and INV-03. Measure with wc -c before saving.
- Do not touch the operator approval requirement rows; they concern operator restore.

## Compatibility considerations

Docs-only change.

## Security considerations

N/A: docs-only change

## Rollback considerations

N/A: revert the commit; the whole plan lands as one commit unit.

## Validation plan

- `uv run python tools/check_adr_invariant_matrix.py`, `check_adr_reference.py`, `check_adr_structure.py`, `check_docs_structure.py`, and `check_compat_shims.py` pass.
- `wc -c` of the file is at most 33647 and `uv run python tools/check_docs_structure.py` passes.

## Completion criteria

- Every mention named in the Procedure is removed or reworded and the document stays well-formed (headings, tables, links, front matter).

## Out of scope

- Tool-level approval (the keep list), the MDQ and eventbus areas, and any file outside this Plan's target table.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Confirm the owner decision is recorded, then apply the edit | Completed | 20261014-142001 | 20261014-142001 |  |
| 2 | Run the ADR and docs checkers | Completed | 20261014-142001 | 20261014-142001 |  |

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
- **Requirement ID**: REQ-001
- **Source issue**: issues/20261014-112913_appr001_remove-the-post-execution-approval-gate.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261014-114443_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261014-123722
- **Related target files**: docs/10_adr/adr_02_008_sqlite-4db-separation.md