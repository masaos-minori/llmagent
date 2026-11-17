# Route the docs-wave procedure archival through the sanctioned archival path

## Priority
Medium

## Summary
`tools/complete_doc_procedure.py` archives a procedure with a plain file rename after updating only the rows that read `Pending`, so it skips the unfinished-row guard and the staged `git mv` of `close-implementation`. Make its archival use the sanctioned path.

## Background
Filed as a follow-up of `plans/20261117-124614_wftool002_status-vocabulary-unify.md` (its Unknowns table, UNK-02). The archival guards it sits beside were introduced by `issues/done/20261106-123521_procarch001_archive-procedures-only-after-execution.md`, which made `close-implementation` refuse a procedure with a `Pending` row and added the archived-status check that reports a procedure archived with a `Pending`, `In Progress`, or `Blocked` row.

## Problem
After the row update, the tool calls `proc.rename` into `implementations/done/` (`Explicit in code`). Only rows whose Status is exactly `Pending` are updated, so a row that is `In Progress` or `Blocked` stays and the procedure is archived anyway; the archived-status check reports such a file only afterwards (`Explicit in code`). The archival rule of `rules/workflow-lifecycle.md` allows `git mv` only, and `close-implementation` is the sanctioned wrapper that stages the move (`Explicit in code`); it refuses only `Pending` rows, so it would not stop an `In Progress` or `Blocked` row either (`Explicit in code`). A plain rename leaves the old path as an unstaged deletion and the new path untracked until staged, while the commit workflow expects archival renames to be staged already (`Strongly implied by code`, `skills/git-commit-and-sync/workflow.md` Phase 2). The tool is in use: 90 archived procedures carry its stamp (`Operationally observed`).

## Reason for Change
- The tool reopens the failure that `procarch001` closed for the `In Progress` and `Blocked` rows, which no archival step refuses: a procedure with an unfinished row can enter `implementations/done/` and hide open work.
- A non-staged move can be committed in part, leaving an added file and a deleted file in different commits.
- The tool also removes the procedure's line from the batch memo, so the memo workflow is live and the archival should not be dropped from it. Nothing makes the change time-sensitive beyond the next batch run.

## Implementation Intent
- Archival goes through the sanctioned path (`close-implementation`, which stages a `git mv`), either by calling its function or its command.
- The tool itself stops, with a non-zero exit and no move, when any row is not terminal after its own update, because the sanctioned path refuses only `Pending` rows.
- The memo line removal and the findings table stay unchanged.

## Target Files or Areas
- `tools/complete_doc_procedure.py`
- `tests/tools/test_complete_doc_procedure.py`
- `tools/TOOL_DESCRIPTIONS.md`

## Required Changes
- Replace the plain rename with the sanctioned archival path and keep the destination-exists refusal.
- Refuse to archive when a row remains `Pending`, `In Progress`, or `Blocked` after the update, and report the rows.
- Add tests: an unfinished row blocks the move, a finished procedure is moved and staged, and a dry run moves nothing.
- Update the tool description.

## Constraints
- The memo line removal behavior and the Verification Findings insertion are unchanged.
- The archival MUST use `git mv` through the sanctioned path and no other method (`rules/workflow-lifecycle.md` Archival Move).
- Follow `routing.md` Tools, section "Adding a new tool", for every changed `tools/*.py`: ruff format and check, mypy, bandit, a smoke run against real repository data, and `tools/TOOL_DESCRIPTIONS.md` sync (`tools/check_tool_descriptions_sync.py`).
- Respect the `tools/` module-size gate (`tools/check_module_size.py --scripts-dir tools --baseline tools/check_module_size_tools_baseline.txt`): the baseline only shrinks, so a tool at or over the limit MUST NOT grow; put new logic in a new module instead.
- Follow the tool CLI conventions recorded in `tools/TOOL_DESCRIPTIONS.md`: exit codes `0` pass, `1` findings, `2` usage or environment error; `--dry-run` and atomic writes for tools that rewrite files.
- Follow the Current-Specification-Only policy: no aliases, shims, or history-style comments for removed behavior.
- Keep code comments, log text, and documentation in English; change only the Target Files and report any other needed file as a scope amendment.

## Acceptance Criteria
- A procedure with an `In Progress` or `Blocked` row is not archived, the tool exits non-zero, and the file stays in `implementations/` (test).
- A finished procedure is archived through the sanctioned path and the move is staged as a rename (test).
- `--dry-run` leaves the procedure, the memo, and `implementations/done/` unchanged (test).
- `tools/check_tool_descriptions_sync.py` passes.

## Testing Expectations
Unit tests in `tests/tools/test_complete_doc_procedure.py` with a temporary git repository fixture for the staged rename; smoke run on a copy of a real procedure; ruff, mypy, bandit. Validation sequence: `rules/toolchain.md`; after any `docs/` edit also the checkers listed in `routing.md` Tools.

## Documentation Impact
Yes. The tool's description rows in `tools/TOOL_DESCRIPTIONS.md`.

## Out of Scope
- Changing the refusal rule of the sanctioned archival tool.
- Retiring the tool.
- Rewriting already archived procedures.

## Dependencies
- `plans/20261117-124614_wftool002_status-vocabulary-unify.md` is a prerequisite: depends on its phase 1 (the test module) and phase 3 (the entry point, dry run, and function split of the same file); land this change after them.

## Unresolved Questions
- Whether `close-implementation` itself should also refuse `In Progress` and `Blocked` rows is `不明`; this issue adds the check to the docs-wave tool only.
- Whether the memo workflow should keep archiving inside this tool or hand it to a separate step is `不明` and belongs to the owner of the batch memo.
- The memo path is fixed to one default file name in the tool; whether it should be configurable is `不明`.

## AI Implementation Instruction
- If the memo-ownership question blocks the design, stop and report it instead of choosing.

## Traceability
- **Workflow phase**: issue-creator
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20261117-132202
- **Related target files**: `tools/complete_doc_procedure.py`; `tests/tools/test_complete_doc_procedure.py`; `tools/TOOL_DESCRIPTIONS.md`
