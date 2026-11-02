## Goal
- Add a note to `templates/implementation-procedure.md` that a name another procedure of the same Plan creates, declared `(new)` by an earlier sibling, is resolved and reported by `tools/stale_detector.py` and needs no manual Assumptions note (`REQ-004`: template states tool-resolved sibling declarations).

## Scope
- Modify only the "Marking what the procedure creates" note in "Notes on filling sections". Documentation-only; Medium blast radius (every procedure follows the template, and `tools/generate_workitem.py` copies its fenced block, which this edit does not touch).

## Assumptions
- A1: Step 3a: the note currently covers a name or import the document itself creates and says an absent unmarked name "is reported as stale and aborts the cycle" (verified by Read, 2026-11-02). The change adds one sentence after it and does not edit the fenced structure block.
- A2: The detector's sibling resolution is created by the `seq` 01 procedure, so it exists when this text lands.
- A3: Overlap judgment (Step 2, `check_plan_target_overlaps.py`, 2026-11-02): this file is targeted by flowimp002, flowimp007, and flowimp009. Judged compatible: flowimp002 edits the `## Scope` block, flowimp009 adds the companion section and adjusts the one-file statements; this Plan edits only the `(new)` marking note (Plan A6, A8). No sequencing dependency.
- A4: `check_workitem_structure.py` checks `## ` headings of generated documents against the fenced block; since the block is untouched, the check is expected to pass unchanged.

## Design decisions
- Add to the marking note: the marker is needed only for names the document itself creates; a name that an earlier-`seq` procedure of the same Plan marks `(new)` is resolved by the detector, which prints a `resolved from sibling` line, so no Assumptions note is needed.

## Alternatives considered
- N/A: wording fixed by the Plan (REQ-004).

## Implementation
### Target file
`templates/implementation-procedure.md`

### Procedure
1. Locate the bullet starting `**Marking what the procedure creates**` at execution time (by text).
2. Append one sentence to that bullet; do not touch the fenced template block or other notes.

### Method
- Use Edit anchored on the final sentence `so a sentence that merely mentions an import is not.` of that bullet.

### Details
- The sentence also states the default order rule (earlier `seq` only) and the two detector options in a clause, so the template stays consistent with `tools/TOOL_DESCRIPTIONS.md`.

## Compatibility considerations
- N/A: additive note; the generated-document structure is unchanged.

## Security considerations
- N/A: documentation only.

## Rollback considerations
- N/A: revert the commit.

## Validation plan
- `uv run python tools/check_workitem_structure.py --file {a generated procedure of this Plan}`: no findings (fixture check from the Plan).
- `uv run python tools/check_skills_references.py`: no findings.

## Completion criteria
- The template note states the sibling resolution (AC-5); the fenced block is byte-identical; the checkers pass.

## Out of Scope
- The fenced block, the lightweight-fill rules, the `## Scope` text (flowimp002), and the companion section (flowimp009).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Append the sibling-resolution sentence to the `(new)` marking note in `templates/implementation-procedure.md` | Pending | — | — | |
| 2 | Run `check_workitem_structure.py` on a generated procedure and `check_skills_references.py` | Pending | — | — | |

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
- **Related target files**: `templates/implementation-procedure.md`
