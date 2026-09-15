## Goal
Replace `skills/python-refactoring/report-template.md`'s Completion Gate closing
sentence (line 108) with one that routes to this file's own `Blocked` status
vocabulary (REQ-002).

## Scope
In scope: line 108's sentence only. Out of scope: the 9 existing Completion Gate pass
conditions (lines 92-107, unchanged); any other section of this file;
`validation.md` (a separate target-file row in this same Plan).

## Assumptions
- Replacing 1 sentence will not push this file over the 400-line File Split Rule
  trigger in `skills/DESIGN.md`.
- This file's `Blocked` status vocabulary (used at lines 27, 71, 84, and 101,
  confirmed present during this document's own Step 3a verification) remains the
  correct existing term to reuse.

## Design decisions
Per `skills/python-design/SKILL.md` Core Design Rules ("Avoid implementation-reference
duplication"), the replacement reuses the exact `Blocked` term already established
elsewhere in this same file, rather than introducing a new status word, per the
Plan's own Design section.

## Alternatives considered
- Appending a new sentence after line 108 rather than replacing it — rejected: the
  Plan's REQ-002 specifies "replace line 108's ... with ...", not an addition; leaving
  the old bare sentence in place alongside a new one would create redundant,
  potentially conflicting guidance.

## Implementation
### Target file
skills/python-refactoring/report-template.md

### Procedure
1. Locate line 108 ("If any item is not satisfied, do not report the task as
   complete.").
2. Replace it with the `Blocked`-routing sentence.
3. Leave the 9 preceding pass conditions (lines 92-107) and all other content
   unchanged.

### Method
Use `Edit` with an `old_string`/`new_string` pair covering line 108's exact sentence
(unique in the file), replacing it in place.

### Details
Change:
`If any item is not satisfied, do not report the task as complete.`
to:
`If any required item above cannot be satisfied: report \`Blocked\` (per this file's
existing \`Blocked\` status vocabulary) rather than a partial pass — a Completion Gate
item is not conditional/optional like the validation items covered by \`Not run\`/
\`Blocked\` status elsewhere in this template.`

Do not alter the 9 pass conditions (lines 92-107) or the Path C paragraph immediately
above line 108.

## Compatibility considerations
This file is referenced by 3+ other repository files (Plan Affected areas). No
public/runtime interface or code behavior is affected — this replaces one exit-
condition sentence with a more precise one using the file's own existing vocabulary,
without weakening the gate.

## Security considerations
N/A: no secrets, credentials, or executable content involved — plain Markdown prose
replacement only.

## Rollback considerations
Single-file, single-sentence-replacement edit; revertable independently of the
companion `validation.md` document via `git checkout --
skills/python-refactoring/report-template.md` (pre-commit) or a follow-up commit
reverting this file only.

## Validation plan
- `git diff skills/python-refactoring/report-template.md` — confirm only line 108
  changed, the 9 pass conditions and Path C paragraph unchanged.
- `uv run python tools/check_skills_references.py` — confirm no broken
  `rules/`/`skills/`/`templates/` reference was introduced.

## Completion criteria
The Completion Gate states an explicit exit condition using the `Blocked` status
vocabulary for any unsatisfied required item; the 9 pass conditions are unchanged;
`tools/check_skills_references.py` passes (Plan AC-2).

## Out of scope
The 9 existing Completion Gate pass conditions; `validation.md` (a separate
target-file row in this Plan); any other section of `report-template.md`; any other
file; any other evaluation criterion from the source review batch.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 20260915-110247 | 20260915-110247 |  |
| 2 | Add or update tests per Validation plan | Completed | 20260915-110247 | 20260915-110247 | N/A: no automated test for this file type — see Validation plan |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20260915-110247 | 20260915-110247 | Only `tools/check_skills_references.py` applies (Markdown, not `scripts/`) |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Completed | 20260915-110247 | 20260915-110247 | N/A: no `docs/*.md` update required |

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
- **Requirement ID**: REQ-002 (route Completion Gate exit condition to Blocked vocabulary)
- **Source issue**: issues/20260914-115550_skillqa12_python-refactoring-tool-order-and-completion-gate-exit.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260915-090513_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260915-095918
- **Related target files**: skills/python-refactoring/report-template.md