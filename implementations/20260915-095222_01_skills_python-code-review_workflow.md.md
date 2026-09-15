## Goal
Add an explicit "Completed when" line to each of Phase 2 through Phase 9 in
`skills/python-code-review/workflow.md` (REQ-001 through REQ-008), tying completion to
every "Do:" checklist item having been checked against the actual diff.

## Scope
In scope: one "Completed when" line appended to each of Phase 2, 3, 4, 5, 6, 7, 8, and
9. Out of scope: Phase 1 and Phase 10 (already adequate); changing any Phase's actual
"Do:" checklist content; any other section of this file.

## Assumptions
- Adding 8 short lines will not push this file over the 400-line File Split Rule
  trigger in `skills/DESIGN.md`.
- `skills/python-code-review/SKILL.md`'s "Output Format" section (confirmed via
  Reference Files below) is still the correct cross-reference target for Phase 9's
  new line.

## Design decisions
Per `skills/python-design/SKILL.md` Core Design Rules ("Avoid implementation-reference
duplication"), each new line reuses Phase 1 and Phase 10's existing "**Completed
when**: ..." phrasing pattern rather than inventing a new format, per the Plan's own
Design section.

## Alternatives considered
- A single shared "Completed when" note referencing all 8 Phases at once (e.g. at the
  end of the Toolchain section) — rejected: the Plan's Requirements specify one line
  per Phase, since each Phase's actual completion condition differs (different tools,
  different checklist items).

## Implementation
### Target file
skills/python-code-review/workflow.md

### Procedure
1. Locate the end of each of Phase 2 (after line 51), Phase 3 (after line 60), Phase
   4 (after line 69), Phase 5 (after line 81), Phase 6 (after line 90), Phase 7 (after
   line 99), Phase 8 (after line 108), and Phase 9 (after line 116) — each
   immediately before that Phase's trailing `---` separator.
2. Insert the corresponding "Completed when" line (REQ-001 through REQ-008) at each
   location.
3. Leave Phase 1, 10, and all other content unchanged.

### Method
Use `Edit` with 8 separate `old_string`/`new_string` pairs, each anchored on the exact
final sentence of the corresponding Phase's "Do:" list (unique in the file), appending
the new "Completed when" line as a new paragraph after it, before the `---`
separator.

### Details
- Phase 2 (after "run \`ruff check\` / \`mypy\` or \`pyright\` on touched files to
  confirm type and lint findings"): add `**Completed when**: every check above has
  been applied to each changed function in the diff, and \`ruff check\`/\`mypy\`/
  \`pyright\` have been run on touched files.`
- Phase 3 (after "...without a concrete requirement"): add `**Completed when**:
  dependency direction and abstraction-introduction checks have been applied to every
  changed import/interface in the diff.`
- Phase 4 (after "...on early-return and exception paths"): add `**Completed when**:
  every changed \`async def\`/resource-acquiring code path in the diff has been
  checked for blocking calls and cleanup on both normal and exception paths.`
- Phase 5 (after "...SQL string interpolation)"): add `**Completed when**: every
  changed error-handling/config/logging code path has been checked, and \`bandit\`
  has been run where available.`
- Phase 6 (after "check CI quality gates and type-checking coverage for the touched
  paths"): add `**Completed when**: test coverage has been checked for every
  critical/edge/failure path touched by the diff, and \`pytest\` has been run to
  confirm the claimed pass/fail state.`
- Phase 7 (after "...Docs content policy — remove"): add `**Completed when**: every
  doc claim about the changed behavior has been checked against the current
  implementation, not against a prior-version recollection.`
- Phase 8 (after "a severity per \`skills/DESIGN.md\` Severity levels"): add
  `**Completed when**: every finding carried forward from Phases 2-7 has concrete
  evidence, an evidence label/confidence level, and a severity assigned.`
- Phase 9 (after "...specify the exact behavior or failure mode to verify."): add
  `**Completed when**: the report follows \`SKILL.md\`'s Output Format, findings are
  grouped by severity, and no style-only issue is over-reported.`

Do not alter any Phase's existing "Do:" checklist content, heading, or `---`
separator placement.

## Compatibility considerations
This file is referenced by 5+ other repository files (Plan Affected areas). No
public/runtime interface or code behavior is affected (this is a skill instruction
file).

## Security considerations
N/A: no secrets, credentials, or executable content involved — plain Markdown prose
addition only.

## Rollback considerations
Single-file edit adding 8 independent lines; revertable via `git checkout --
skills/python-code-review/workflow.md` (pre-commit) or a follow-up commit reverting
this file only.

## Validation plan
- `git diff skills/python-code-review/workflow.md` — confirm exactly 8 new lines
  added, one per Phase 2-9, no other line touched, "Do:" checklists unchanged.
- `uv run python tools/check_skills_references.py` — confirm no broken
  `rules/`/`skills/`/`templates/` reference was introduced.

## Completion criteria
Each of Phase 2 through 9 has an explicit "Completed when" line worded per REQ-001
through REQ-008, tying completion to the actual diff/findings, not merely to having
read the checklist; Phase 1 and 10 are unchanged; `tools/check_skills_references.py`
passes (Plan AC-1, AC-2).

## Out of scope
Phase 1 and Phase 10 of this same file; any other file; any other evaluation
criterion from the source review batch.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 20260915-105207 | 20260915-105207 | 8 insertions, one per Phase 2-9 |
| 2 | Add or update tests per Validation plan | Completed | 20260915-105207 | 20260915-105207 | N/A: no automated test for this file type — see Validation plan |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20260915-105207 | 20260915-105207 | Only `tools/check_skills_references.py` applies (Markdown, not `scripts/`) |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Completed | 20260915-105207 | 20260915-105207 | N/A: no `docs/*.md` update required |

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
- **Requirement ID**: REQ-001 through REQ-008 (add "Completed when" to Phase 2-9)
- **Source issue**: issues/20260914-115127_skillqa06_python-code-review-workflow-phase-completion-criteria.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260915-085712_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260915-095222
- **Related target files**: skills/python-code-review/workflow.md