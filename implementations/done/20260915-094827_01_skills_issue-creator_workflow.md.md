## Goal
Add an explicit "Completed when" line to each of Phase 3 through Phase 8 in
`skills/issue-creator/workflow.md` (REQ-001 through REQ-006), matching the style
already used in Phase 1 and Phase 2.

## Scope
In scope: one "Completed when" line appended to each of Phase 3, 4, 5, 6, 7, and 8.
Out of scope: Phase 1, 2, 9, 10 (already adequate); adding any "Stop and ask"/Blocked
condition to Phase 3-8; Phase 10's own separate scaffold-tool change (tracked in a
different Plan/document, `skillqa14`); any other section of this file.

## Assumptions
- Adding 6 short lines will not push this file (currently 241 lines) over the
  400-line File Split Rule trigger in `skills/DESIGN.md`.
- A separate Plan (`skillqa14`) targets this same file's Phase 10 — confirmed
  non-overlapping with this document's Phase 3-8 scope by re-reading both Plans'
  Scope sections; no conflict.

## Design decisions
Per `skills/python-design/SKILL.md` Core Design Rules ("Avoid implementation-reference
duplication"), each new line reuses Phase 1 (line 27) and Phase 2 (line 55)'s exact
"**Completed when**: ..." phrasing pattern rather than inventing a new format, per the
Plan's own Design section.

## Alternatives considered
- Adding a "Stop and ask" condition alongside each "Completed when" line — rejected
  per the Plan's own Scope Out-of-Scope: none of Phase 3-8 was found to need one.

## Implementation
### Target file
skills/issue-creator/workflow.md

### Procedure
1. Locate the end of each of Phase 3 (after line 78), Phase 4 (after line 96), Phase
   5 (after line 107), Phase 6 (after line 127), Phase 7 (after line 148), and Phase 8
   (after line 157) — each immediately before that Phase's trailing `---` separator.
2. Insert the corresponding "Completed when" line (REQ-001 through REQ-006) at each
   location.
3. Leave Phase 1, 2, 9, 10, and all other content unchanged.

### Method
Use `Edit` with 6 separate `old_string`/`new_string` pairs, each anchored on the exact
final sentence of the corresponding Phase (unique in the file), appending the new
"Completed when" line as a new paragraph after it, before the `---` separator.

### Details
- Phase 3 (after "...otherwise describe the responsibility, not the location."):
  add `**Completed when**: Background, Problem, Reason for Change, and Implementation
  Intent are each filled or explicitly marked \`N/A\` with a stated reason.`
- Phase 4 (after "...Use \`N/A: none\` if there are none."): add `**Completed when**:
  Target Files or Areas, Required Changes, Constraints, Out of Scope, and Dependencies
  are each filled or explicitly marked \`N/A\`/\`Unknown\` per the template's
  convention.`
- Phase 5 (after "...clearly does not affect behavior."): add `**Completed when**:
  every Acceptance Criteria item is independently testable by review, test execution,
  or documentation inspection, and Testing Expectations is filled or marked \`Not
  required\` only for a documentation-only/no-behavior-change task.`
- Phase 6 (after "...move to Needs Confirmation."): add `**Completed when**:
  Documentation Impact states explicitly whether documentation must be updated, and if
  so, names the kind of information affected.`
- Phase 7 (after "...non-blocking consistency improvements."): add `**Completed
  when**: exactly one of High/Medium/Low is assigned, matching the criteria stated
  above for that tier.`
- Phase 8 (after "...do not implement out-of-scope items."): add `**Completed when**:
  the AI Implementation Instruction states concrete constraints (not a generic
  restatement of Phase 4's Out of Scope) an implementer must follow.`

Do not alter any Phase's existing content, heading, or `---` separator placement.

## Compatibility considerations
This file is referenced by 7+ other repository files (Plan Affected areas). No
public/runtime interface or code behavior is affected (this is a skill instruction
file). A separate Plan (`skillqa14`) also edits this file's Phase 10 — this document's
6 insertions are confined to Phase 3-8 and do not touch Phase 10, so the two Plans'
edits do not conflict when both are applied.

## Security considerations
N/A: no secrets, credentials, or executable content involved — plain Markdown prose
addition only.

## Rollback considerations
Single-file edit adding 6 independent lines; revertable via `git checkout --
skills/issue-creator/workflow.md` (pre-commit) or a follow-up commit reverting this
file only. If `skillqa14`'s Phase 10 edit has already landed in the same file by the
time of a revert, verify the revert does not also remove that unrelated change.

## Validation plan
- `git diff skills/issue-creator/workflow.md` — confirm exactly 6 new lines added, one
  per Phase 3-8, no other line touched.
- `uv run python tools/check_skills_references.py` — confirm no broken
  `rules/`/`skills/`/`templates/` reference was introduced.

## Completion criteria
Each of Phase 3 through 8 has an explicit "Completed when" line worded per REQ-001
through REQ-006; no Phase gained a "Stop and ask"/Blocked condition; Phase 1, 2, 9, 10
are unchanged; `tools/check_skills_references.py` passes (Plan AC-1, AC-2, AC-3).

## Out of scope
Phase 1, 2, 9, 10 of this same file (Phase 10 tracked separately by `skillqa14`); any
other file; any other evaluation criterion from the source review batch.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 20260915-103622 | 20260915-103622 | 6 insertions, one per Phase 3-8 |
| 2 | Add or update tests per Validation plan | Completed | 20260915-103622 | 20260915-103622 | N/A: no automated test for this file type — see Validation plan |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20260915-103622 | 20260915-103622 | Only `tools/check_skills_references.py` applies (Markdown, not `scripts/`) |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Completed | 20260915-103622 | 20260915-103622 | N/A: no `docs/*.md` update required |

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
- **Requirement ID**: REQ-001 through REQ-006 (add "Completed when" to Phase 3-8)
- **Source issue**: issues/20260914-114926_skillqa03_issue-creator-workflow-add-phase-completion-criteria.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260915-085343_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260915-094827
- **Related target files**: skills/issue-creator/workflow.md