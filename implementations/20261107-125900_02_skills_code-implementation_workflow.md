# Implementation Procedure: archive-order rule in code-implementation workflow

## Goal

State, in `skills/code-implementation/workflow.md`, that a procedure is moved to
`implementations/done/` only by the archival move, and never by any earlier step. This
closes the gap behind `REQ-001`: the archive-order rule must be stated in the workflow that
actually performs procedure archival. (`REQ-001`: the archive-order rule is stated in the
two workflow files.)

## Scope
**Release unit**: N/A: not part of a release unit

## Assumptions
- The archival move is Step 7 ("Move the Completed Implementation Procedure File"); the
  Step 1 all-steps-completed resume move is the same archival operation applied to an
  already-complete procedure, so it is in scope for the same rule.
- The statement complements (does not contradict) the sibling
  `plan-to-implementation-procedure` statement generated for the same `REQ-001`.

## Design decisions
- State the rule as a guard sentence on the existing Step 7 / Allowed file operations move
  rather than a new section: the move already exists and is well anchored, so a sentence is
  reviewable in one hunk and changes no behavior.

## Alternatives considered
- Adding the rule to a new section: rejected; the Step 7 anchor already describes the move,
  so a guard sentence reads more naturally than a new navigational destination.

## Implementation
### Target file
`skills/code-implementation/workflow.md`

### Procedure
1. In "Allowed file operations", extend the bullet "Move the processed implementation
   procedure file to `implementations/done/` after validation passes (Step 7)" with a
   clause stating that NO earlier step (implement, test, or document) moves a procedure;
   the move happens only at Step 7 (or the Step 1 all-steps-completed resume for an
   already-complete procedure).
2. In Step 7, add a one-line note that moving a procedure before its Execution Status rows
   are `Completed` is the mistake this rule prevents.

### Method
- Insert the clause into existing prose; no new section, heading, or table.
- Mirror the `plan-to-implementation-procedure` wording so the two files read as one rule.

### Details
- Anchor the clause on the existing Step 7 bullet so the guard sits next to the operation it
  constrains.
- Do not describe the `detect-unexecuted-archive` detector here beyond the fact that
  `implementations/done/` holds executed procedures; the detector has its own row.

## Compatibility considerations
N/A: documentation-only; no runtime or API impact.

## Security considerations
N/A: no code path or permission change.

## Rollback considerations
N/A: revert the commit.

## Validation plan
- Read the Allowed file operations and Step 7 sections and confirm the guard names only
  Step 7 (and the Step 1 resume) as moving a procedure to `implementations/done/`.
- Run `uv run python tools/check_skills_references.py` if any backtick reference was added.

## Completion criteria
`skills/code-implementation/workflow.md` states that a procedure reaches
`implementations/done/` only via the Step 7 archival move (or the Step 1 all-steps-completed
resume), never via an implement/test/document step.

## Out of Scope
- Editing `skills/plan-to-implementation-procedure/workflow.md` here (its own row covers it).
- Editing `routing.md` here (its own row covers it).
- Any code change.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Add the archive-order guard to Allowed file operations and Step 7 | Pending | — | — | |
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
- **Requirement ID**: `REQ-001` — state the archive-order rule in the code-implementation workflow
- **Source issue**: `issues/20261106-123521_procarch001_archive-procedures-only-after-execution.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261107-121954_procarch001_archive-procedures-only-after-execution.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261107-125900
- **Related target files**: `skills/code-implementation/workflow.md`
