# Single command to close an executed implementation batch and its plan status

## Priority
Medium

## Summary
Provide one repeatable entry point that, after a plan's implementation procedures have been executed, archives every procedure of that batch, marks the matching plan rows `Completed`, and leaves the result ready for a single `chore:` commit. The goal is to replace a multi-command manual sequence that recent history shows being repeated by hand.

## Background
`git log --grep='archive the executed'` returns 9 commits with the same shape (examples: `46078e90f`, `c50dc24d9`). Each commit moves a whole batch of `implementations/*.md` files into `implementations/done/`, edits their Execution Status tables, and rewrites the matching rows of one `plans/done/*_plan.md` Execution Status table (for example `In Progress` to `Completed` with `Started`, `Completed`, and `Notes` filled in).

Repository tools already cover the individual operations (`Explicit in code`, per `tools/manage_workitem_stage.py` module docstring and `tools/TOOL_DESCRIPTIONS.md`):

- `manage_workitem_stage.py close-implementation` archives one file at a time and refuses while a row is `Pending`.
- `manage_workitem_stage.py set-status` and `set-step-status` update a plan's or procedure's Execution Status table.
- `set_execution_status.py` marks selected rows `Completed` and stamps the timestamps.

`skills/code-implementation/workflow.md` already tells the implementer to prefer `close-implementation` per target file. No tool or documented step runs the whole batch plus the plan-status update as one operation (`Needs confirmation`: this was judged from `tools/TOOL_DESCRIPTIONS.md` and the workflow text only, not from reading every tool body).

## Problem
Closing one batch means one `close-implementation` call per procedure file (7 to 9 files in the two latest commits), then a plan-table update, then a commit. `AGENTS.md` Global Rule 7 says an operation performed three or more times is to be extracted into a script under `tools/`; this sequence has been performed at least 9 times as a whole but exists only as individual tool calls. The manual form invites omissions, such as a plan row left `In Progress` or one procedure left unarchived.

## Reason for Change
The repetition is already established by history, and the building blocks exist, so the remaining cost is orchestration only. A single entry point lowers the chance of a half-closed batch and shortens the end of every implementation cycle.

## Implementation Intent
Add a thin orchestration layer on top of the existing tools, not a second implementation of archival or table editing. It should take the plan path (or the shared procedure timestamp prefix) as input, discover that batch's procedure files, and call the existing logic for each. It must keep the existing refusal behavior, including the `Pending` row check and the `--force --reason` requirement. Whether the layer is a new subcommand of `manage_workitem_stage.py` or a separate small tool is a design decision for the plan stage. Committing stays with `skills/git-commit-and-sync`; the layer should stage only (`--stage-only` semantics) so the commit message remains a human or agent decision.

## Target Files or Areas
- `tools/manage_workitem_stage.py` (or a new `tools/` script, to be decided)
- `tools/set_execution_status.py`
- `tools/TOOL_DESCRIPTIONS.md`
- `skills/code-implementation/workflow.md` (final archival step)
- `tests/` for the chosen tool (location Unknown; mirror existing `tools/` test layout)

## Required Changes
- Decide between extending `manage_workitem_stage.py` and adding a new tool; record the reason in the plan.
- Implement batch discovery from a plan path or timestamp prefix, in a deterministic order.
- For each discovered procedure: mark its Execution Status `Completed` and archive it through the existing code path.
- Update the matching plan Execution Status rows (`Completed`, timestamps, optional note) through the existing code path.
- Support a dry-run mode that prints the intended moves and edits without changing files.
- Register the tool in `tools/TOOL_DESCRIPTIONS.md` and update the archival step of `skills/code-implementation/workflow.md` to reference it.

## Constraints
- Must not bypass the `Pending` refusal or the `--force --reason` rule of `close-implementation`.
- Archival moves must stay `git mv` renames, as in the current tool.
- Must not touch `implementations/superseded/` handling or the `done/` directory structure (`rules/ai-execution.md` Global Safety Restrictions).
- Tool changes follow the lighter validation in `routing.md` "Adding a new tool" (ruff, mypy with explicit path, bandit, a smoke run on live data, `check_tool_descriptions_sync.py`).

## Acceptance Criteria
- One invocation archives all procedure files of a batch and updates the plan rows; a second invocation on the same batch is a no-op or a clear refusal, not a partial re-run.
- A batch containing a `Pending` row is refused with no file moved.
- Dry-run changes no file and lists every planned move and edit.
- The resulting working-tree diff for a past batch is equivalent in shape to the diff of `46078e90f` (verified on a copy or a scratch branch, not by rewriting history).
- `uv run python tools/check_tool_descriptions_sync.py` and `uv run python tools/check_workitem_structure.py` pass after the change.

## Testing Expectations
- Unit tests for batch discovery, refusal on `Pending`, idempotency, and dry-run.
- An integration-style test using a temporary git repository fixture.
- `uv run ruff`, `uv run mypy tools/<file>.py`, and `uv run bandit tools/<file>.py` clean.
- Smoke run against current `implementations/` and `plans/` content, recorded as evidence.

## Documentation Impact
`tools/TOOL_DESCRIPTIONS.md` must gain or update a row. `skills/code-implementation/workflow.md` needs its archival step to name the new entry point. Content to document: intent, the refusal conditions retained, and operational notes about `--stage-only`. No `docs/` change is expected.

## Out of Scope
- Generating the commit message or running `git commit`.
- Changing the Execution Status table format or `templates/execution-status.md`.
- Archiving issues (`close-issue`) or plans (`close-plan`); only procedures plus the plan status rows are covered.
- Changing the other workflow stages.

## Dependencies
Sibling-issue check: the open issues under `issues/` (`turn006` and `eventbus001` to `eventbus008`) touch none of these files; `N/A: none` overlap. Depends on the existing `manage_workitem_stage.py` and `set_execution_status.py` behavior staying stable.

## Unresolved Questions
- Assumption: the repeated chore commits are produced by hand or by an agent following the workflow text, not by an undocumented script. Not verified.
- Should the plan-status update live in the same tool, or remain a separate step because the plan may stay `In Progress` when only part of its batches are done?
- Is a batch always identifiable by a shared timestamp prefix, or only through the plan's `Implementation Target Files` table?

## AI Implementation Instruction
Reuse the existing tool functions; do not copy their logic. Keep the change minimal and limited to the target files. Do not modify unrelated tools or skills. Stop and report if the batch-identification question cannot be answered from repository evidence. Do not run the tool against real `implementations/` content except as a dry run until tests pass.

## Traceability
- **Workflow phase**: `issue-creator`
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20261023-173429
- **Related target files**: `tools/manage_workitem_stage.py`, `tools/set_execution_status.py`, `tools/TOOL_DESCRIPTIONS.md`, `skills/code-implementation/workflow.md`
