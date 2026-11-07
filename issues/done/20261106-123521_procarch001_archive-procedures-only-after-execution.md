# Archive implementation procedures only after they are executed

## Priority
Medium

## Summary
Nine implementation procedures were moved to `implementations/done/` without being executed, and nothing in the repository detected it until the code was found missing.

## Background
Commit `f0dff11a8` ("Adversarially verify & archive 9 toolcli001/tracecompanion001 procedure docs") moved the procedures of the `toolcli001` and `tracecompanion001` Plans to `implementations/done/` while every Execution Status row was still `Pending` and the code did not exist (no `tests/tools/test_tool_cli_convention.py`, no `_procedures_of_plan`). `routing.md` defines `implementations/done/` as procedures consumed by `prompts/03_implementation.md`. `tools/plan_dependency_order.py` treats an archived Plan as complete, so dependent Plans were reported `ready`. `tools/manage_workitem_stage.py close-implementation` checks only that no row is `Pending` and that the destination is free on `origin/master`. Many older procedures under `implementations/done/` also keep stale `Pending` rows, so row status alone cannot show whether a procedure ran.

## Problem
An unexecuted procedure can be archived without any check, and the archive then hides open work from `plan_dependency_order.py`, the dependency order, and reviewers.

## Reason for Change
The mistake cost a restore, a re-verification, and an out-of-order execution of nine procedures, and it can recur on any batch archive.

## Implementation Intent
State the rule that only `code-implementation` Step 7 moves a procedure to `implementations/done/` (plan-to-implementation-procedure archives the Plan only), and add a cheap detector for a recently archived procedure whose rows are still `Pending`.

## Target Files or Areas
`skills/plan-to-implementation-procedure/workflow.md`, `skills/code-implementation/workflow.md`, `routing.md` (Document workflow directories), `tools/manage_workitem_stage.py`, `tools/plan_dependency_order.py`, `tools/check_workitem_traceability.py`.

## Required Changes
- Add the rule to the workflow files that archive procedures and to the `routing.md` directory table.
- Add a check that warns when a procedure archived within the last N days (by its first commit into `implementations/done/`) still has a `Pending`, `In Progress`, or `Blocked` row; older files are not reported.
- Decide whether `plan_dependency_order.py` should also report a Plan whose procedures are not all archived and completed as not finished.

## Constraints
The detector MUST NOT report the historical `done/` files that already carry stale rows; the window must be explicit. No change to the archive tools' refusal conditions beyond what the rule needs.

## Acceptance Criteria
- A procedure archived by mistake is reported by the check within its window.
- The rule is stated once in the workflow files and referenced from `routing.md`.
- The historical `done/` files produce no finding.

## Testing Expectations
Tests for the detector with a temporary repository (recent archive with Pending rows, recent archive completed, old archive with Pending rows); `uv run python tools/check_tool_descriptions_sync.py` and the checkers `routing.md` names for the edited skill files.

## Documentation Impact
Yes: the workflow files and `routing.md` directory table (intent: who archives procedures and when); `tools/TOOL_DESCRIPTIONS.md` for the detector.

## Out of Scope
Rewriting history, changing the status of the historical `done/` files, and the policy questions filed separately.

## Dependencies
N/A: none

## Unresolved Questions
- Window length N and whether the detector belongs in `check_workitem_traceability.py` or `manage_workitem_stage.py` (`detect-stale`-like).

## AI Implementation Instruction
Keep the detector read-only and report-only; do not move or edit work items. Follow `rules/coding.md` and the `tools/` validation steps of `routing.md` "Adding a new tool".

## Traceability
- **Workflow phase**: issue-creator
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20261106-123521
- **Related target files**: `skills/plan-to-implementation-procedure/workflow.md`, `skills/code-implementation/workflow.md`, `routing.md`, `tools/manage_workitem_stage.py`, `tools/check_workitem_traceability.py`

## Adversarial Validation

Validated against current source and git history on 2026-11-07.

- Commit `f0dff11a8` ("Adversarially verify & archive 9 toolcli001/tracecompanion001 procedure docs") exists; its body states nothing was executed, every step stayed `Pending`, and all 9 docs were archived to `implementations/done/`. — Evidence: `Operationally observed` (git) — Confidence: High
- `plan_dependency_order.py` loads an archived Plan (`plans/done/`) as a node; `manage_workitem_stage.py close-implementation` refuses when any Execution Status row is `Pending`. — Evidence: `Explicit in code` — Confidence: High
- No factual conflict found. The Unresolved Questions (window length N, detector ownership) remain appropriately open.

Verdict: accepted as filed.

## Content Analysis

- Type: tooling/policy fix (read-only detector plus a workflow and `routing.md` rule).
- Pipeline path: issue -> plan -> implementation procedure -> code. Owner: engineer.
- Scope: `tools/manage_workitem_stage.py`, `tools/plan_dependency_order.py`, `tools/check_workitem_traceability.py`, two workflow files, `routing.md`.
- Dependency: none declared. Independent of the other three batch issues.
- Open item before planning: window length N and which tool owns the detector (both under Unresolved Questions).
