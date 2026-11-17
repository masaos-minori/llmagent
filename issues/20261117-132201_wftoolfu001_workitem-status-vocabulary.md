# Define the Execution Status vocabulary once and validate it for active work items

## Priority
Medium

## Summary
The Status column of a work item's Execution Status table accepts any text, and the vocabulary itself disagrees with the batch-close tool about `N/A`. Decide the allowed set once and make the structure checker report values outside it for active work items.

## Background
Filed as a follow-up of `plans/20261117-124614_wftool002_status-vocabulary-unify.md` (its Unknowns table, UNK-01). That Plan fixes one writer of the value `Done`; this issue covers the validation gap that let about six hundred other non-vocabulary rows through. Distinct from `issues/done/20261107-203218_wfaudit005_unvalidated-status-writes.md`, which covers the status columns of the workflow database tables, not the Markdown work item tables.

## Problem
The vocabulary is Pending, In Progress, Blocked, Completed, and Superseded in `tools/_workitem_status_table.py` and `templates/execution-status.md` (`Explicit in code`). `tools/close_procedures_batch.py` treats `Completed` and `N/A` as terminal, so `N/A` is accepted by one consumer and absent from the vocabulary (`Explicit in code`). No check validates the Status column (`Explicit in code`). Measured with the shared parser (`Operationally observed`): among archived procedures that have a status table, 631 hold a value outside the vocabulary, led by `Done` (732 rows), `N/A` and its prose variants (more than 400 rows), `Complete` (149 rows), and `Skipped` (118 rows); 3 of the 4 active procedures hold `N/A` rows; the active plans hold none; 10 archived plans hold `Complete`, `Done`, `Obsolete`, or `Reverted (partial)`. The newest archived procedures with `Done` came from a batch archived today.

## Reason for Change
- Consumers classify by exact value: `sync_plan_workitem_status.py` reconciles a Plan row only when every row is `Completed` or `Superseded`, `close_procedures_batch.py` accepts only `Completed` and `N/A` as terminal, and the archived-status check treats only Pending, In Progress, and Blocked as unfinished. A non-vocabulary value is therefore read as finished by one consumer and as unreconciled by another, silently.
- Hand-written rows are the main source (about three quarters of the `Done` rows carry no stamp of the tool), so fixing one writer cannot close the gap.
- The rows keep arriving: the newest archived batch still holds `Done` rows. Nothing makes the change urgent beyond that continued drift.

## Implementation Intent
- One decision fixes the status of `N/A` (a terminal status of the vocabulary, or a value the consumers stop accepting), applied to the vocabulary source, the template, and every consumer.
- The structure checker reports a Status value outside the vocabulary in an active work item (top-level `plans/` and `implementations/`), with the file and the value, and grandfathers the archived files through a baseline in the manner of the archived-status rule.
- The vocabulary stays defined in one place that both the template and the checker read.

## Target Files or Areas
- `tools/check_workitem_structure.py`
- `tools/_workitem_status_table.py`
- `templates/execution-status.md`
- tools/close_procedures_batch.py (only if `N/A` is removed from its terminal set)
- A baseline file for archived non-vocabulary values (new, beside `tools/check_archived_status_baseline.txt`)
- `tests/tools/test_check_workitem_structure.py`
- `tools/TOOL_DESCRIPTIONS.md`

## Required Changes
- Decide the status of `N/A` and apply it to the vocabulary, the template, and the batch-close tool.
- Decide whether common variants (`Complete`, `Skipped`, `Deferred`) are aliases that the writers normalize or values the checker rejects.
- Add the Status value check to the structure checker for active work items, with a baseline for archived files.
- Add tests: an unknown value in an active procedure and in an active plan, an accepted value, an archived file in the baseline, and the live active set.
- Update the tool description and the checker row of `routing.md` if its trigger text changes.

## Constraints
- Do not rewrite Status values in archived work items; the baseline records them.
- Do not change the vocabulary beyond the `N/A` decision; extending it is a separate decision.
- Follow `routing.md` Tools, section "Adding a new tool", for every changed `tools/*.py`: ruff format and check, mypy, bandit, a smoke run against real repository data, and `tools/TOOL_DESCRIPTIONS.md` sync (`tools/check_tool_descriptions_sync.py`).
- Respect the `tools/` module-size gate (`tools/check_module_size.py --scripts-dir tools --baseline tools/check_module_size_tools_baseline.txt`): the baseline only shrinks, so a tool at or over the limit MUST NOT grow; put new logic in a new module instead.
- Follow the tool CLI conventions recorded in `tools/TOOL_DESCRIPTIONS.md`: exit codes `0` pass, `1` findings, `2` usage or environment error; `--dry-run` and atomic writes for tools that rewrite files.
- Follow the Current-Specification-Only policy: no aliases, shims, or history-style comments for removed behavior.
- Keep code comments, log text, and documentation in English; change only the Target Files and report any other needed file as a scope amendment.

## Acceptance Criteria
- A procedure or plan under the active directories with a Status value outside the vocabulary makes the checker exit `1` and name the file and the value (test).
- `N/A` is accepted or rejected the same way by the vocabulary, `templates/execution-status.md`, `tools/close_procedures_batch.py`, and the checker (tests).
- The checker passes on the live active work items, and archived files in the baseline are not reported.
- `tools/check_tool_descriptions_sync.py` passes.

## Testing Expectations
Unit tests under `tests/tools/test_check_workitem_structure.py` and `tests/tools/test_close_procedures_batch.py` for the `N/A` decision; a smoke run over the live active work items; ruff, mypy, bandit. Validation sequence: `rules/toolchain.md`; after any `docs/` edit also the checkers listed in `routing.md` Tools.

## Documentation Impact
Yes. `templates/execution-status.md`, the checker's description, and the `routing.md` row if its text changes; no `docs/` file.

## Out of Scope
- Rewriting archived rows.
- The workflow database status columns (`wfaudit005`).
- Adding statuses to the vocabulary.

## Dependencies
- `plans/20261117-124614_wftool002_status-vocabulary-unify.md` is a prerequisite: depends on its phase 2, which adds the shared completed-status constant to `tools/_workitem_status_table.py`; land this change after that phase.
- `plans/20261117-124139_wftool001_gate-workitem-structure.md` also edits `tools/check_workitem_structure.py`: follows its phase 1 so the two changes do not collide.

## Unresolved Questions
- Whether `N/A` is a status or a different marker is `不明` and needs a maintainer decision.
- Whether variants such as `Complete` are normalized by writers or rejected is `不明`.
- The baseline file's name and format are `不明`.

## AI Implementation Instruction
- Present the `N/A` options with their consumers and stop before changing any consumer.
- Do not rewrite archived rows.

## Traceability
- **Workflow phase**: issue-creator
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20261117-132201
- **Related target files**: `tools/check_workitem_structure.py`; `tools/_workitem_status_table.py`; `templates/execution-status.md`; tools/close_procedures_batch.py (only if `N/A` is removed from its terminal set); A baseline file for archived non-vocabulary values (new, beside `tools/check_archived_status_baseline.txt`); `tests/tools/test_check_workitem_structure.py`; `tools/TOOL_DESCRIPTIONS.md`
