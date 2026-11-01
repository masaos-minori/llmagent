# Let a procedure cover the test files of its code row

## Priority
Medium

## Summary
Allow one implementation procedure to carry its code row's test files as companion sections, with the one-document-per-file rule kept for everything else, so that test changes that follow a code change no longer need a separate low-information document each. The Plan's `Implementation Target Files` table still lists every file, and every row is still covered.

## Background
- `Operationally observed` (2026-10-30): the three Plans produced 59 procedure documents; 24 of them (41%) describe a test file (6 of 11 for `wftaskapi001`, 12 of 24 for `wfrecovery001`, 6 of 24 for `dbmig001`). Most of them restate what the code row's document already says: which behavior the tests assert and which commands run them.
- `Operationally observed`: for `wfrecovery001`, 12 documents (11 test files and one small code file) were generated after the code and tests were written, only so that every Plan row had a document before the move; their content records what was done.
- `Explicit in code`: `skills/plan-to-implementation-procedure/SKILL.md` Core Execution Rules state that a document "MUST NOT contain modification instructions for more than one file", and Step 4 of its workflow checks one document per row. `templates/implementation-procedure.md` already allows a "lightweight fill" for small rows, which shortens the body but not the count.
- `Explicit in code`: the Plan's table already has a `Related Tests` column per row, so the pairing of a code row with its tests is recorded in the Plan.

## Problem
The one-file-per-document rule is correct for review scope and rollback, but for test files that exist only to prove a code row it multiplies documents, status tables, and archive steps without adding independent decisions.

## Reason for Change
Test rows are about two out of five documents in a typical persisted-schema Plan. Each carries a full structure, a stale check, a status table, and an archive step, and the retroactive ones show the structure being filled for the checker rather than for the reader.

## Implementation Intent
Keep the file-level scope boundary but let it be declared per document rather than per file: a procedure for a code row may list companion test files (rows of the same Plan whose `Related Tests` or reason ties them to that code row) with their own short procedure and validation lines. The Plan's table is unchanged, the documents' `Related target files` list every covered file, and the Step 4 coverage check counts a row as covered when its file appears as a target or a companion of a document. Test files that cover more than one code row, or that need their own design decisions, keep a separate document. `code-implementation` treats companions as in scope of that document and archives the document once.

## Target Files or Areas
- `skills/plan-to-implementation-procedure/SKILL.md` and `workflow.md` (the one-file rule, Step 3c, Step 4)
- `templates/implementation-procedure.md` (a companion section)
- `skills/code-implementation/workflow.md` (scope, Step 3d, Step 7)
- `tools/generate_workitem.py` and its tests (a companion option)
- `tools/check_workitem_structure.py`, `tools/check_workitem_traceability.py`, and `tools/audit_plan_target_paths.py`, with their tests, wherever they assume one file per document

## Required Changes
- Define the companion section and the conditions under which a test file may be a companion.
- Update the coverage and uniqueness checks so a companion counts as covered and is never double-counted.
- Update the generator to scaffold a document with companions.
- State in `code-implementation` that companions are in the document's scope, are stale-checked with it, and are archived with it.
- Keep separate documents for test files that serve several rows.

## Constraints
- The one-file rule stays for source files, docs, config, and standalone test files; the exception is limited to test files of a single code row.
- No Plan table change; `Implementation Target Files` rows and Freeze rules are untouched.
- Review and rollback scope per document must remain clear: companions are listed in the document's Target file section.

## Acceptance Criteria
- A fixture Plan with a code row and two test rows produces one document that lists the code file as the target and the two test files as companions, and the coverage check passes; removing a companion makes it fail.
- A test file tied to two code rows is rejected as a companion and needs its own document.
- `tools/stale_detector.py` and the status tools handle a document with companions.
- Re-deriving the three archived Plans' document counts under the new rule is recorded (expected: the count of test documents falls to those needing their own).

## Testing Expectations
- Unit tests for the generator option, the coverage check (covered, missing, duplicate, multi-row companion), and the traceability and path-audit tools on companion documents.
- A walk-through on the archived `wftaskapi001` Plan comparing the document set before and after.
- Skill checkers and `check_tool_descriptions_sync.py`.

## Documentation Impact
Yes. The skill, workflow, and template state the exception, its conditions, and how coverage is counted. Intent and failure behavior only.

## Out of Scope
- Merging documents for source files or docs.
- Changing Plan Freeze or the table structure.
- Removing the stale check or the status table from any document.

## Dependencies
Sequencing only, in either order, with `issues/20261030-191057_flowimp002_plan-release-units.md` and `issues/20261030-191457_flowimp007_stale-sibling-new.md`: they also change `templates/implementation-procedure.md` and the two workflows; whichever lands later rebases. No other open issue or Plan targets these files (checked with `rg` over `issues/*.md` and `plans/*.md`, 2026-10-30).

## Unresolved Questions
- `不明`: which other tools or checks assume one file per document beyond the three named; the first step is a search for such assumptions.
- `不明`: whether the owner accepts the exception to the one-file rule (`skills/plan-to-implementation-procedure/SKILL.md` Core Execution Rules); this issue assumes the rule exists for review scope, not as an end in itself.
- Assumption: a test file's tie to its code row can be read from the Plan's `Related Tests` column.

## AI Implementation Instruction
Change the named skills, template, and tools only. Keep the one-file rule for non-test files and do not alter the Plan table or Freeze rules. Stop and report if a tool outside the list depends on one file per document and cannot be adapted within this issue.

## Traceability
- **Workflow phase**: issue-creator
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20261030-191615
- **Related target files**: `skills/plan-to-implementation-procedure/SKILL.md`, `skills/plan-to-implementation-procedure/workflow.md`, `templates/implementation-procedure.md`, `skills/code-implementation/workflow.md`, `tools/generate_workitem.py`, `tools/check_workitem_structure.py`, `tools/check_workitem_traceability.py`, `tools/audit_plan_target_paths.py`
