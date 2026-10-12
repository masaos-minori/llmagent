## Goal
- Tell procedure authors to mark symbols and imports the procedure creates, so the stale detector does not report them (`REQ-004`).

## Scope
- Only the section Notes on filling sections of `templates/implementation-procedure.md`: one new bullet. The fenced template and every other note are untouched.

## Assumptions
- Procedures generated from this template are the detector's input, so the convention belongs here; the existing practice for new files already uses a backticked path followed by (new).

## Design decisions
- One bullet that states the rule, the effect, and the limit: unmarked names that do not exist are still reported.

## Alternatives considered
N/A: the Plan Design section already fixed the approach for this row.

## Implementation
### Target file
`templates/implementation-procedure.md`

### Procedure
1. Locate the section with `grep -n "Notes on filling sections" templates/implementation-procedure.md`.
2. Append one bullet at the end of the list in that section, written in English. Its content: when a procedure names a symbol or an import statement that it will create, write the name in backticks and follow it with the word (new) in parentheses; `tools/stale_detector.py` skips the existence check for such a name, while a name that is absent and not marked is reported as stale. Also say that only an import statement at the start of a line is checked as an import, so a sentence that merely mentions an import is not.
3. Leave the fenced template and all other notes untouched.

### Method
- Add the bullet in the same style as its neighbours (a bold lead-in phrase, then the explanation); keep the template's fenced block unchanged because `tools/check_workitem_structure.py` reads its headings.

### Details
- Do not use a concrete symbol in backticks inside the bullet, because a sample name would itself be looked up; describe the pattern in words.
- Apply together with procedures 03 and 05 so the three descriptions agree.

## Compatibility considerations
N/A: documentation-only change; existing procedures are unaffected.

## Security considerations
N/A: no input handling, credentials, or trust boundary is touched.

## Rollback considerations
N/A: revert the commit.

## Validation plan
- `uv run python tools/check_workitem_structure.py --file implementations/<any procedure>.md` still reports no findings (the fenced template is unchanged); `uv run python tools/check_skills_references.py` passes.
- Execution order for the whole plan: procedure 02 (tests) first, then 01 (code), then 03, 04 and 05 (documentation); the new-policy tests must be seen failing before the code is edited.

## Completion criteria
- The notes contain the new bullet; the fenced template is unchanged; the checkers pass.

## Out of scope
- The structure of the template, the lightweight-fill note, and any other file.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Add the marker convention bullet to the notes | Completed | 20261012-171422 | 20261012-171434 | stale_detector clean changed: templates/implementation-procedure.md (one bullet in Notes on filling sections; fenced template unchanged, 14 headings) |
| 2 | Run the structure and reference checkers | Completed | 20261012-171434 | 20261012-171434 | check_workitem_structure and check_skills_references pass |

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
- **Requirement ID**: `REQ-004` (authoring guidance for the marker)
- **Source issue**: issues/20261012-132457_stale001_fix-stale-detector-false-positives.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261012-132739_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261012-170854
- **Related target files**: templates/implementation-procedure.md