# Implementation Procedure: archive-order rule in plan-to-implementation-procedure workflow

## Goal

State, in `skills/plan-to-implementation-procedure/workflow.md`, that this workflow archives
the Plan only (`plans/done/`) and never moves an implementation procedure to
`implementations/done/`; only `code-implementation` Step 7 moves a procedure. This closes
the gap behind `REQ-001`: an unexecuted procedure can be archived because no file states
which phase owns procedure archival. (`REQ-001`: the archive-order rule is stated in the
two workflow files.)

## Scope
**Release unit**: N/A: not part of a release unit

## Assumptions
- The archive-order rule belongs in this workflow's own prose (Allowed file operations and
  Step 4), not in `code-implementation`'s file, which owns procedure archival.
- The existing Step 4 ("Move the Completed Plan File") is the correct anchor; the Plan's
  repository-evidence cell naming it "Step 7" was a copy error and is corrected separately
  in this cycle.

## Design decisions
- State the rule as a short explicit sentence rather than renumbering steps: renaming
  Step 4 would ripple through every cross-reference, while a sentence is reviewable in one
  hunk and changes no behavior.

## Alternatives considered
- Adding the rule to a new section instead of the existing Allowed file operations / Step 4
  anchors: rejected; the anchors already describe the move, so the rule reads as a guard on
  existing text rather than a new navigational destination.
- Covering procedure archival here too: rejected; this workflow never touches
  `implementations/`, so stating it there would duplicate `code-implementation`'s Step 7.

## Implementation
### Target file
`skills/plan-to-implementation-procedure/workflow.md`

### Procedure
1. Open the "Allowed file operations" section and add one sentence after the bullet that
   allows moving the processed plan file to `plans/done/`: this workflow archives the Plan
   only and never moves an implementation procedure to `implementations/done/`; that move
   belongs to `code-implementation` Step 7.
2. In Step 4 ("Move the Completed Plan File"), add a one-line note restating that the move
   is the Plan file only and that no procedure under `implementations/` is moved by this
   workflow.

### Method
- Insert the sentence into existing prose; no new section, heading, or table.
- Keep the wording identical in spirit to the `code-implementation` statement so the two
  files read as one rule (see the companion procedure for `code-implementation`).

### Details
- Place the Allowed file operations sentence immediately after the existing
  "Move the processed plan file to `plans/done/` once Step 3's validation passes" bullet so
  the guard sits next to the operation it constrains.
- Do not reference `implementations/done/` contents here beyond the one guard sentence; the
  detector and `routing.md` cover that directory.

## Compatibility considerations
N/A: documentation-only; no runtime or API impact.

## Security considerations
N/A: no code path or permission change.

## Rollback considerations
N/A: revert the commit.

## Validation plan
- Read both workflow files and confirm the archive-order sentence is present and names
  `plans/done/` (this file) and `implementations/done/` (`code-implementation`).
- Run `uv run python tools/check_skills_references.py` if any backtick reference was added.

## Completion criteria
The "Allowed file operations" and Step 4 of `skills/plan-to-implementation-procedure/workflow.md`
both state that this workflow archives the Plan only and never moves a procedure, with no
mention of moving anything under `implementations/`.

## Out of Scope
- Editing `skills/code-implementation/workflow.md` here (its own row covers it).
- Editing `routing.md` here (its own row covers it).
- Any code change.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Add the archive-order rule to the Allowed file operations and Step 4 | Pending | — | — | |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | docs-only; structure checkers only |
| 4 | Update documentation, if in scope | Pending | — | — | N/A: skill workflow file, not a docs/ task-scope row |

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
- **Requirement ID**: `REQ-001` — state the archive-order rule in the plan-to-implementation-procedure workflow
- **Source issue**: `issues/20261106-123521_procarch001_archive-procedures-only-after-execution.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261107-121954_procarch001_archive-procedures-only-after-execution.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261107-125900
- **Related target files**: `skills/plan-to-implementation-procedure/workflow.md`
