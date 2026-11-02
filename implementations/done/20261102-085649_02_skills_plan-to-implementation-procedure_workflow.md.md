## Goal
- Update `skills/plan-to-implementation-procedure/workflow.md` so Step 3c lets a code row's document carry its test rows as companions and Step 4's coverage and uniqueness checklist counts a companion as covering its row without double-counting it (`REQ-001`: companion conditions in the workflow; `REQ-002`: coverage and uniqueness counting).

## Scope
- Modify only `skills/plan-to-implementation-procedure/workflow.md`: the Workflow position `seq` note, Step 3c (one-document bullets, the `Already implemented` classification, the `Not implemented` document bullet, the stale-detector bullet), the Step 4 pre-move checklist, and the Step 4 Execution Status mapping sentence. Documentation-only; Medium blast radius.

## Assumptions
- A1: Step 3a: Step 3c states "one target file = one implementation procedure document", "each row maps to exactly one document - no merging is needed", and "modification instructions for exactly this row's `File Path` - no other file"; Step 4 requires "rows equal rows covered", "at most one per row", "every document ... maps back to exactly one row" and "no procedure document modifies more than one file (its `Implementation > Target file` names exactly one path)" (verified by Read, 2026-11-02). The edits are located by those phrases, not line numbers.
- A2: Step 3a: no tool checks row coverage today (Plan Background). The coverage command is created by the `seq` 05 procedure as an opt-in mode of `tools/check_workitem_traceability.py` (the flag is named `--plan-coverage` there); this procedure cites it by that name, so it exists when this text lands.
- A3: Step 3a: a companion row keeps its table position, so `seq` numbering of the other rows is unchanged and a skipped `seq` is expected (the existing rule already fixes `seq` by row position, not by generation order).
- A4: Overlap judgment (Step 2, `check_plan_target_overlaps.py`, 2026-11-02, Plan A7 to A11): this file is also targeted by flowimp008, flowimp011 and (already procedured) flowimp002, flowimp003, flowimp007. Judged compatible by content, a sequencing dependency by file: edits are anchored by text, not line number; whichever Plan lands later rebases. Specific ranges: flowimp002 and flowimp003 text (units, gated marker) lies in Step 2 and Step 4 prose outside the lines edited here; flowimp007 edits Step 3c item (2) of the stale-detector bullet, and this procedure edits the same bullet by adding a companion sentence after it (sequencing dependency, Plan A8, A9); flowimp008 edits the Step 4 `Work Items Created` paragraph; flowimp011 rewrites the Step 3c additional-target-file bullet.
- A5: Step 3c's `Partially implemented` rule is not changed; a companion that an existing document lists counts as covered by that document for classification.

## Design decisions
- Keep the one-file rule as the default sentence and add the companion exception directly under it, with the four conditions stated once by reference to `SKILL.md` Core Execution Rules (no restatement).
- Step 3c: classify a companion row as covered when its eligibility holds and the code row's document lists it; it gets no document and no `seq` file. A test file failing a condition keeps its own document as before.
- Step 4: replace the three counting bullets with companion-aware wording and add one bullet: run the coverage command on the Plan and require no finding.

## Alternatives considered
- Add companion handling to the `Already implemented` classification only: rejected; the generation path (`Not implemented`) is where companions are decided.

## Implementation
### Target file
`skills/plan-to-implementation-procedure/workflow.md`

### Procedure
1. Workflow position: add a sentence that a companion row has no file of its own, so its `seq` is skipped.
2. Step 3c: after the "one target file = one implementation procedure document" lead-in, add the companion exception and its pointer to `SKILL.md`; adjust the duplicate-`File Path` bullet ("each row maps to exactly one document") to "each row is covered by exactly one document, as its target or as a companion".
3. Step 3c `Already implemented`: add that a document whose `Related target files` lists the row's path after the primary target (as a companion) covers the row.
4. Step 3c `Not implemented`: change "exactly this row's `File Path` - no other file" to allow the companion section for an eligible test row; the document then lists target first and companions in `### Companion test files`.
5. Step 3c stale-detector bullet: add that a companion's `(new)` marks and line citations are checked against the companion by the tool.
6. Step 4 checklist: edit the three counting bullets and the "no procedure document modifies more than one file" bullet for companions, and add the coverage-command bullet.
7. Step 4 mapping paragraph: "A procedure document carries out the modification of one file" becomes one file plus its companions; a step citing a companion's `File Path` is mapped to the same document.

### Method
- Edit with text anchors per item; keep every existing clause that is not named above.
- Cite `SKILL.md` by its rule title only, not as `SKILL.md` Core Execution Rules: that section already links to Step 3c, so a one-line section reference closes a heading cycle (found in Step 3e, corrected here).
- The coverage bullet reads: run `uv run python tools/check_workitem_traceability.py --plan-coverage {plan_path}` and require exit 0 before the move.

### Details
- Rows counted: each Plan row is covered once, whether by a document of its own (target), by a document listing it as companion, or by `Already implemented`; documents generated this cycle number at most one per code or standalone row, and no companion is also a target or companion of another document.
- A companion discovered to need a design decision of its own, or tied to two code rows, is classified `Not implemented` and gets its own document; it is not a Plan Gap.

## Compatibility considerations
- Plan Freeze and the table structure are untouched; a Plan with no companions follows the unchanged counts.

## Security considerations
- N/A: documentation only.

## Rollback considerations
- N/A: revert the commit.

## Validation plan
- `uv run python tools/check_skills_references.py`: no findings.
- `uv run python tools/check_skills_heading_cycles.py`: no findings.

## Completion criteria
- Step 3c and the Step 4 checklist state the companion exception, the coverage count, and the coverage command; the one-file rule remains for every other file (AC-1, AC-2); both checkers pass.

## Out of Scope
- The other Plans' paragraphs named in A4, the template and `SKILL.md` text, and any change to Plan Freeze.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Edit Workflow position and Step 3c for companions | Completed | 20261102-133644 | 20261102-133644 | Workflow position and Step 3c edited; stale check clean; Method corrected (SKILL.md cited by rule title to avoid heading cycle); full suite deferred to plan end |
| 2 | Edit the Step 4 checklist and mapping text, add the coverage-command bullet | Completed | 20261102-133644 | 20261102-133644 | Step 4 checklist, mapping text, coverage bullet edited |
| 3 | Run `check_skills_references.py` and `check_skills_heading_cycles.py` | Completed | 20261102-133644 | 20261102-133644 | check_skills_references and check_skills_heading_cycles: no issues |

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
- **Requirement ID**: REQ-001 (companion conditions in Step 3c), REQ-002 (Step 4 coverage and uniqueness checklist)
- **Source issue**: issues/20261030-191615_flowimp009_test-row-grouping.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261102-080828_flowimp009_test-row-grouping.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261102-085649
- **Related target files**: `skills/plan-to-implementation-procedure/workflow.md`
