# Close executed procedures and update Plan status with one verified command

## Priority
Medium

## Summary
Make the closing of executed implementation procedures discoverable and complete: point `code-implementation` at the existing row and archive tools, and add one verified batch command that completes the rows, archives the procedures with the renames staged, maps the Plan's Execution Status steps, and updates the Plan's `Work Items Created` table, without the all-rows-`Completed` shortcut that `close-batch` takes.

## Background
- `Operationally observed` (2026-10-30): closing 41 procedure documents in the three Plans took repeated `set-step-status` calls per row, a custom Python loop, and hand edits of each Plan's `Work Items Created` table and step statuses. The executor did not use `tools/set_execution_status.py` or `tools/close_procedure.sh` because nothing in the workflow named them.
- `Explicit in code`: `tools/TOOL_DESCRIPTIONS.md` lists `set_execution_status.py` (marks selected rows of one document) and `close_procedure.sh` (marks every row `Completed` for a date and archives it). A search of `skills/`, `routing.md`, and `rules/` finds no reference to either; `skills/code-implementation/workflow.md` Toolchain names only `set-step-status` and `close-implementation`.
- `Explicit in code`: `skills/code-implementation/workflow.md` Step 7 forbids `close-batch` because it sets every row of every procedure and of the Plan to `Completed` and overwrites timestamps; it describes the Plan update (map steps that modify the target file, require all files of a step to be archived) as manual `set-step-status plan` calls. `skills/plan-to-implementation-procedure/workflow.md` Step 4 states that the `Work Items Created` table has no tool and is edited directly.
- Related closed work: `issues/done/20261023-173429_workitem001_single-command-to-close-an-executed-implementation-batch-and-its-plan-status.md` produced `close-batch`, whose behavior the workflow then ruled out for this use.

## Problem
The closing sequence is a fixed series of operations repeated for every batch, an existing tool pair covers half of it, the skill text does not point to it, and the half that remains (Plan step mapping, Work Items table) is manual and error-prone.

## Reason for Change
Each release batch closes dozens of documents. Manual closing is slow and, because the batch command that exists would overwrite true statuses, the safe path is the most laborious one. `AGENTS.md` Global Rule 7 asks for a tool once an operation repeats three or more times.

## Implementation Intent
First, make the existing tools discoverable from the skill. Then add one batch command that verifies before it changes anything: every named procedure has only `Completed` or explicitly `N/A` rows (rows are completed only when the caller passes an explicit option and a note, never implicitly), the archive destination is free, and the Plan can be found. It then archives the procedures with the renames staged, sets each Plan step to `Completed` only when every file the step cites has its procedure archived (the rule already written in Step 7), and updates the matching `Work Items Created` rows. A dry-run mode prints the plan of changes. No status is invented: rows the command did not verify stay as they are.

## Target Files or Areas
- `tools/manage_workitem_stage.py` and its tests (a new subcommand), or a new sibling tool if the file's size makes that preferable
- `tools/set_execution_status.py` and `tools/close_procedure.sh` (referenced, possibly folded into the new command)
- `skills/code-implementation/workflow.md` (Toolchain and Step 7)
- `skills/plan-to-implementation-procedure/workflow.md` (the `Work Items Created` note)
- `tools/TOOL_DESCRIPTIONS.md`

## Required Changes
- Reference `set_execution_status.py` and `close_procedure.sh` in the `code-implementation` Toolchain table.
- Add the verified batch command with a dry-run mode, explicit row completion, Plan step mapping, and Work Items updates.
- Replace the manual Step 7 Plan-update text with a call to the command, keeping the mapping rule as the command's documented behavior.
- Update the `Work Items Created` statement in the other skill.

## Constraints
- The command must not set a row `Completed` without an explicit option and a note; it must never touch rows it did not verify.
- A failed archive of one document must not stop the others (the existing per-file rule), and must be reported.
- It stages renames only (`--stage-only` behavior); it never commits.
- It must keep working on Plans that have no `Work Items Created` rows for a document.

## Acceptance Criteria
- On fixture Plans and procedures, a dry run prints the intended row changes, archives, step mappings, and Work Items updates and changes nothing; a real run applies exactly those.
- A procedure with a `Pending` or `Blocked` row is refused with the row named, without changing any file.
- A Plan step is marked `Completed` only when all cited files have archived procedures; otherwise it is left unchanged and reported.
- `code-implementation` and `plan-to-implementation-procedure` texts reference the command, and `check_skills_references.py` and `check_skills_heading_cycles.py` pass.

## Testing Expectations
- Unit tests for each refusal and mapping case, including a Plan whose step cites two files with only one archived.
- A dry-run on the live repository's `plans/` with the three Plans of 2026-10-30, reviewed against the manual result.
- `ruff`, `mypy <tool path>`, and `bandit` on the changed or new tool; `check_tool_descriptions_sync.py`.

## Documentation Impact
Yes. The two skills state the command, its verification, and that rows are never completed implicitly. Intent and failure behavior only.

## Out of Scope
- Changing `close-batch`'s own behavior beyond what the new command needs.
- Generating procedure documents or deciding execution order.
- Committing the result (`git-commit-and-sync`).

## Dependencies
Sequencing only, in either order, with `issues/20261030-191057_flowimp002_plan-release-units.md` and `issues/20261030-191144_flowimp003_plan-dependency-gate.md`: all three change `tools/manage_workitem_stage.py` and `skills/code-implementation/workflow.md`; whichever lands later rebases. No other open issue or Plan targets these files (checked with `rg` over `issues/*.md` and `plans/*.md`, 2026-10-30).

## Unresolved Questions
- `不明`: whether the command belongs in `manage_workitem_stage.py` or in a sibling tool, given the file's current size (not measured here).
- `不明`: whether `close_procedure.sh`'s all-rows behavior is still wanted once an explicit-row option exists.
- Assumption: a Plan step's cited files can be read reliably from its checkbox lines.

## AI Implementation Instruction
Add the command and the skill references only. Never complete a row implicitly and never touch a document the command did not verify. Keep the existing tools working. Stop and report if the Plan step mapping cannot be derived from the step text.

## Traceability
- **Workflow phase**: issue-creator
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20261030-191530
- **Related target files**: `tools/manage_workitem_stage.py`, `tools/set_execution_status.py`, `tools/close_procedure.sh`, `skills/code-implementation/workflow.md`, `skills/plan-to-implementation-procedure/workflow.md`, `tools/TOOL_DESCRIPTIONS.md`
