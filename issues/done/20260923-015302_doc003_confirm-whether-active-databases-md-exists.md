# Confirm Whether docs/databases/active_databases.md Should Exist

## Priority
Medium

## Summary
Determine whether `docs/databases/active_databases.md` should remain in the repository. The file has no Front Matter, no H1 heading, and appears to be orphaned. It was flagged during DOC-002 analysis but cannot be processed until its existence is confirmed.

## Background
During the `issue-to-plan` workflow for DOC-002 (Fix Front Matter inconsistencies across docs/), this file was identified as having no Front Matter and no H1 heading. However, adding Front Matter to a file that should not exist would be incorrect. The original issue (DOC-002) noted this as an unresolved question.

## Problem
`docs/databases/active_databases.md` lacks all required Front Matter fields (`title`, `area`, `tags`, `related`) and has zero H1 headings. Unlike other violations where we can infer defaults, this file may be intentionally orphaned or deleted. Adding metadata to a file that should not exist would compound the problem.

## Reason for Change
Without confirmation of whether this file should exist, we cannot safely add Front Matter or H1 headings. This is a prerequisite decision that blocks progress on DOC-002's implementation for this specific file.

## Implementation Intent
Review the file's content and history to determine if it serves any purpose. Check git history for deletion intent. If the file is obsolete, delete it. If it is needed, add proper Front Matter and structure.

## Target Files or Areas
- `docs/databases/active_databases.md`

## Required Changes
- Review file content and git history
- Decide whether to keep or delete the file
- If keeping: add Front Matter and H1 heading per DOC-002 requirements
- If deleting: remove the file

## Constraints
- Do not modify any other files outside of this decision
- Preserve git history if the file is kept

## Acceptance Criteria
- Decision documented: keep or delete
- If kept: Front Matter added per schema validation
- If deleted: file removed from repository

## Testing Expectations
- Run `uv run python tools/check_docs_structure.py "docs/**/*.md"` after changes to confirm zero errors

## Documentation Impact
If the file is deleted, no documentation update needed. If kept, Front Matter must conform to `schemas/doc_front_matter.json`.

## Out of Scope
- Fixing broken references in other files that point to this file
- Restructuring the databases/ directory

## Dependencies
- DOC-002 (this decision gates progress on that plan)

## Unresolved Questions
- What was the original purpose of this file?
- Was it intentionally left without Front Matter as a signal to review its fate?

## AI Implementation Instruction
1. Read `docs/databases/active_databases.md` content
2. Run `git log --all -- docs/databases/active_databases.md` to check history
3. Based on findings, decide: keep (add Front Matter/H1) or delete
4. Execute the decision
5. Re-run `uv run python tools/check_docs_structure.py "docs/**/*.md"` to confirm zero errors

## Traceability
- **Workflow phase**: issue-to-plan
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260923-014359_plan.md
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20260923-015302
- **Related target files**: docs/databases/active_databases.md
