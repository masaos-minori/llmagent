## Goal
- `REQ-005`, `REQ-006`: point ADR-008's `mdq.sqlite` derived-store bullet at the document that records the migration responsibility, without changing any Decision.

## Scope
- `docs/10_adr/adr_02_008_sqlite-4db-separation.md` only: one added sentence in the existing `mdq.sqlite` bullet under "Derived Stores Outside the Four Domains". The Deployment chapter is the other row's document.

## Assumptions
- `db_03_architecture_and_schema-migration-and-scaling.md` section 8d records that the MDQ service runs legacy-schema detection every time it starts, and it is already listed in this ADR's front matter `related:`.
- The ADR's Decision, Invariants, Known Deviations, and Verification text must stay as they are.

## Design decisions
- Append the sentence to the end of the existing `mdq.sqlite` bullet instead of adding a bullet or a section.
- State only where the migration responsibility is documented, not a new rule.

## Alternatives considered
N/A: a new ADR section or a Decision change was rejected as out of scope.

## Implementation
### Target file
`docs/10_adr/adr_02_008_sqlite-4db-separation.md`

### Procedure
- In "Derived Stores Outside the Four Domains" (heading at line 131), at the end of the `mdq.sqlite` bullet (line 133), add one sentence: the schema of `mdq.sqlite` is created and checked for a legacy shape by the MDQ service whenever it starts, as described in `db_03` section 8d, and that service owns this migration responsibility.

### Method
- Use the same inline-reference style as the surrounding bullet; refer to `db_03` section 8d by document name without adding a source-file citation (this keeps the ADR source-reference check unaffected).
- Do not touch the Decision, Invariants, Known Deviations, Verification, or the line-42 summary sentence.

### Details
- Keep the sentence factual and in English; keep the bullet's existing parenthetical evidence unchanged.

## Compatibility considerations
N/A: one added sentence; no Decision or Invariant changes.

## Security considerations
N/A: documentation only.

## Rollback considerations
N/A: revert the commit.

## Validation plan
- `uv run python tools/check_adr_preservation.py` (expect no ERROR), `uv run python tools/check_adr_structure.py`, `uv run python tools/check_adr_reference.py`, `uv run python tools/check_adr_invariant_matrix.py`
- `uv run python tools/check_docs_quality.py`, `uv run python tools/check_docs_structure.py docs/10_adr/adr_02_008_sqlite-4db-separation.md`, `uv run python tools/check_docs_japanese.py`

## Completion criteria
- The bullet carries the cross-reference sentence and nothing else in the ADR changed.
- The ADR and docs checkers above report no ERROR or new finding.

## Out of scope
- Any Decision, Invariant, Verification, or Known Deviations change, the Deployment chapter, `db_03`, and `db_08`.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Add the one-line cross-reference to the `mdq.sqlite` bullet | Completed | 20261016-131948 | 20261016-132027 | changed: docs/10_adr/adr_02_008_sqlite-4db-separation.md (one sentence appended to the mdq.sqlite bullet) |
| 2 | Run the ADR and docs checkers | Completed | 20261016-132027 | 20261016-132027 | check_adr_structure/reference/invariant_matrix, docs quality/structure/content_policy --strict/japanese, check_db_separation, generate_reference_table --check: clean. check_adr_preservation: exit 0, 1 WARNING (Decision section text changed; the added sentence only points to db_03 section 8d, no ERROR; mapping recorded in the report) |

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
- **Requirement ID**: REQ-005 (ADR-008 cross-reference), REQ-006 (consistency and checkers)
- **Source issue**: issues/20261016-125807_dep001_add-mdq.sqlite-to-the-deployment-db-inventory.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261016-130739_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261016-131326
- **Related target files**: docs/10_adr/adr_02_008_sqlite-4db-separation.md