## Goal
- Simplify Step 3c item (2) so a name declared `(new)` by an earlier-`seq` sibling no longer needs a manual Assumptions note, because the detector resolves and reports it (`REQ-004`: skill text states tool-resolved sibling declarations).

## Scope
- Modify only the stale-detector bullet of Step 3c in `skills/plan-to-implementation-procedure/workflow.md` (item (2) of the three-item mismatch list). Documentation-only; Medium blast radius (the workflow runs every generation).

## Assumptions
- A1: Step 3a: Step 3c currently says item (2): a name that only an earlier-`seq` row's procedure in this Plan creates is acceptable and is noted in the document's Assumptions (verified by Read, 2026-11-02); the wording is located by the text "earlier-`seq` row's procedure", not by line number.
- A2: The detector behavior (informational line, default earlier-only rule, `--sibling-order any`, `--no-siblings`) is created by the `seq` 01 procedure of this Plan, so it exists when this text lands.
- A3: Overlap judgment (Step 2, `check_plan_target_overlaps.py`, 2026-11-02): this file is targeted by six Frozen Plans (flowimp002, 003, 007, 008, 009, 011). Judged compatible: this Plan edits Step 3c item (2) only; flowimp008 edits the Step 4 `Work Items Created` paragraph, flowimp011 the additional-target-file paragraph in Step 3c, flowimp009 the one-file rules, Step 3c, and the Step 4 checklist, flowimp002 and flowimp003 other steps and markers. Item (2) sits in the same bullet as the stale-detector run that flowimp009 may touch, so whichever lands later rebases (Plan A8).
- A4: Scripts that consume the wording: none; `tools/check_skills_references.py` and `tools/check_skills_heading_cycles.py` check references only.

## Design decisions
- Keep the three-way classification but state that item (2) is resolved by the tool: the detector prints a `resolved from sibling` line naming the declaring document, so the author adds no Assumptions note; the note is needed only when the tool is run with `--no-siblings` or the document has no `Source plan`.
- Keep item (1) and item (3) unchanged; state the default order rule (earlier `seq`) in one clause.

## Alternatives considered
- N/A: wording fixed by the Plan (REQ-004).

## Implementation
### Target file
`skills/plan-to-implementation-procedure/workflow.md`

### Procedure
1. Re-read Step 3c's `stale_detector.py` bullet at execution time and locate item (2) by its text.
2. Replace item (2) with the simplified wording; leave items (1) and (3) and the rest of the bullet as they are.

### Method
- Use Edit with the full item (2) clause as the unique anchor.

### Details
- New item (2) states: a name that only an earlier-`seq` sibling procedure of this Plan marks `(new)` is resolved and reported by the tool as an informational line, and needs no Assumptions note; a name declared only by a later-`seq` sibling stays a mismatch and is corrected here.

## Compatibility considerations
- N/A: wording only; existing procedures that already carry the note stay valid.

## Security considerations
- N/A: documentation only.

## Rollback considerations
- N/A: revert the commit.

## Validation plan
- `uv run python tools/check_skills_references.py` and `uv run python tools/check_skills_heading_cycles.py`: no findings.

## Completion criteria
- Step 3c item (2) states that sibling declarations are resolved and reported by the tool and need no manual note (AC-5); both checkers pass.

## Out of Scope
- Other steps of this workflow, the Step 2 start conditions, the Step 4 text, and the edits of other Plans to this file.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Rewrite Step 3c item (2) in `skills/plan-to-implementation-procedure/workflow.md` | Pending | — | — | |
| 2 | Run `check_skills_references.py` and `check_skills_heading_cycles.py` | Pending | — | — | |

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
- **Requirement ID**: REQ-004
- **Source issue**: issues/20261030-191457_flowimp007_stale-sibling-new.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261102-080513_flowimp007_stale-sibling-new.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261102-085029
- **Related target files**: `skills/plan-to-implementation-procedure/workflow.md`
