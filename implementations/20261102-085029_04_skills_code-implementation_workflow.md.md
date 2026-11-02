## Goal
- State in `skills/code-implementation/workflow.md` Step 2 stale-detection result handling that names declared `(new)` by earlier siblings are resolved and reported as informational lines, not as mismatches (`REQ-004`: skill text states tool-resolved sibling declarations).

## Scope
- Modify only the "Stale detection result handling" subsection (part of Step 2). Documentation-only; High blast radius (executes every procedure), so the edit is one added paragraph.

## Assumptions
- A1: Step 3a: the subsection currently explains the `(new)` marker for names and imports, then for target files, then the abort rules for "any mismatch" (verified by Read, 2026-11-02); it does not mention informational lines. The Plan's phrase "Pre-execution stale detection (part of Step 2)" names the parent section.
- A2: The detector's informational output, options, and order rule are created by the `seq` 01 procedure, so they exist when this text lands.
- A3: Overlap judgment (Step 2, `check_plan_target_overlaps.py`, 2026-11-02): this file is targeted by six Frozen Plans (flowimp002, 003, 007, 008, 009, 011). Judged compatible: this Plan edits the stale-detection result handling in Step 2; flowimp003 edits Step 1 and Multi-file processing text, flowimp002 Step 4, flowimp008 the Toolchain table and Step 7, flowimp011 the scope rules (new stop rule), flowimp009 Step 2 target-file text, Step 3d, and Step 7. flowimp009 may touch the same Step 2 area (companions are stale-checked), so whichever lands later rebases (Plan A8).
- A4: The abort rule stays: only remaining mismatches abort; a resolved sibling declaration is not a mismatch.

## Design decisions
- Add a paragraph after the target-file `(new)` paragraph: a name or import marked `(new)` by an earlier-`seq` sibling procedure of the same `Source plan` is resolved by the detector and printed as `resolved from sibling`; it is not a mismatch and does not abort; the reader may confirm the declaring document named in the line.
- Mention that a name declared only by a later sibling remains a mismatch, with the reason in its detail.

## Alternatives considered
- N/A: wording fixed by the Plan (REQ-004).

## Implementation
### Target file
`skills/code-implementation/workflow.md`

### Procedure
1. Re-read the "Stale detection result handling" subsection at execution time; locate it by heading.
2. Insert the new paragraph before the `If the stale detector reports any mismatch:` list; do not change the list.

### Method
- Use Edit anchored on the `An unmarked target that does not exist is still a mismatch and aborts the procedure.` sentence (unique), appending the paragraph after it.

### Details
- Do not weaken the abort rule: the paragraph says informational lines do not abort and that every remaining mismatch still aborts.

## Compatibility considerations
- N/A: additive wording; abort behavior for unmarked names is unchanged.

## Security considerations
- N/A: documentation only.

## Rollback considerations
- N/A: revert the commit.

## Validation plan
- `uv run python tools/check_skills_references.py` and `uv run python tools/check_skills_heading_cycles.py`: no findings.

## Completion criteria
- Step 2 result handling states that sibling-declared names are resolved and reported by the tool and are not mismatches (AC-5); both checkers pass.

## Out of Scope
- Other steps of this workflow, the abort rules, and the edits of other Plans to this file.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Add the sibling-resolution paragraph to Step 2 result handling in `skills/code-implementation/workflow.md` | Pending | — | — | |
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
- **Related target files**: `skills/code-implementation/workflow.md`
