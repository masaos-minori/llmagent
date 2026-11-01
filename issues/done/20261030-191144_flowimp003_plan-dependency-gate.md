# Gate procedures on Plan dependencies and show the execution order

## Priority
High

## Summary
Make Plan-to-Plan dependencies machine-readable, add a read-only tool that computes the order and the ready or gated state of open Plans and their procedures, and make `plan-to-implementation-procedure` and `code-implementation` use it, so that procedures that cannot run yet are marked and listed as gated instead of being discovered when execution starts.

## Background
- `Operationally observed` (2026-10-30): the wfrecovery001 and wftaskapi001 procedure documents for the schema-dependent rows were generated while the dbmig001 Plan they depended on had no procedure documents at all. Seven of them sat blocked (`Pending` with a prose "Gated" note) until dbmig001 was implemented; the block was found only when execution began. The executor asked the user about the execution order three times.
- `Explicit in code`: `skills/plan-to-implementation-procedure/workflow.md` Step 2 ("Plan-level start conditions") says that a Dependency on another open Plan must be reported with a question and that the order must not be decided there. The rule is prose; nothing evaluates it and nothing is recorded on the generated documents.
- `Explicit in code`: `tools/check_plan_target_overlaps.py` lists Plans that share a target file and gives candidates only; `tools/manage_workitem_stage.py list` filters by kind and status and has no order view. Procedure filenames sort by the table position `seq`, while execution follows the Plan's phases; each generated procedure repeats "execution order follows the phases, not seq" in prose.
- Related closed work: `issues/done/20261023-173429_workitem001_single-command-to-close-an-executed-implementation-batch-and-its-plan-status.md` (closing a finished batch).

## Problem
A dependency between Plans exists only as prose. The executor learns that a procedure cannot run when it tries to run it, the generated documents do not say whether they are runnable, and the real execution order is reconstructed by hand for every batch.

## Reason for Change
Persisted-state work is ordered by design (migration framework, then key rename, then recovery state machine, then lease and retry), and more such Plans are open. Every unrecorded dependency costs a blocked cycle and a question.

## Implementation Intent
Record the dependency in a structured line in the Plan, compute order and readiness with a tool, and let the skills consume the result. The tool recommends; it never decides: the existing rule that the order is the owner's decision stays, and the tool only makes the question answerable (what depends on what, what is ready, what is gated and by which open item). Procedures whose Plan is gated are generated with an explicit gated marker and reason and are listed separately; an execution-order view shows procedures in Plan phase order.

## Target Files or Areas
- `tools/plan_dependency_order.py` (new) and `tests/tools/test_plan_dependency_order.py` (new)
- `tools/manage_workitem_stage.py` and its tests (order view)
- `templates/plan.md` (the structured dependency line) and `templates/execution-status.md` (gated marker vocabulary)
- `skills/plan-to-implementation-procedure/workflow.md` (Step 2 start conditions)
- `skills/code-implementation/workflow.md` (Step 1 target selection)
- `tools/TOOL_DESCRIPTIONS.md` and `routing.md`

## Required Changes
- Define the structured dependency line (the depended-on Plan or Issue path, the phase, and the reason) in the Plan template, and keep reading the existing prose form as a fallback with a warning.
- Add the tool: build the graph from the dependency lines and from shared target files (reusing the overlap tool's data), detect cycles, print a recommended order, and report each open Plan as ready or gated with the blocking item.
- Mark procedures of a gated Plan as gated with the reason, using a vocabulary entry in `templates/execution-status.md`.
- Add an order view to `manage_workitem_stage.py list` (Plan phase order, grouped by Plan).
- Update the two skills to call the tool and report, not decide.

## Constraints
- Read-only tool; no network.
- The owner still decides order; the tool and skills must not reorder or skip work silently (`skills/plan-to-implementation-procedure/workflow.md` Step 2).
- Existing Plans without the structured line must keep working.
- The marker vocabulary change must stay within `templates/execution-status.md`'s rules.

## Acceptance Criteria
- On fixture Plans, the tool prints the expected order, reports cycles, and marks a Plan whose dependency is open as gated with the blocking path.
- `manage_workitem_stage.py list` has an order view that lists procedures in Plan phase order for a given Plan.
- A procedure generated for a gated Plan carries the marker and reason, and `code-implementation` Step 1 reports gated procedures instead of starting them.
- The skills and template checkers (`check_skills_references.py`, `check_skills_heading_cycles.py`, `check_workitem_structure.py`) pass, and the tool is registered (`check_tool_descriptions_sync.py`).

## Testing Expectations
- Unit tests for graph building, cycle detection, readiness, the prose fallback, and the order view.
- A smoke run on the live `plans/` directory that completes without error and whose output is reviewed against the known order (dbmig001, wftaskapi001, wfrecovery001, then the others).
- `ruff`, `mypy <tool path>`, and `bandit <tool path>` per "Adding a new tool".

## Documentation Impact
Yes. The two skills, the Plan template, and the status vocabulary state the structured dependency, the gated state, and that the owner decides the order. Intent and failure behavior only.

## Out of Scope
- Deciding or changing the real order of any open Plan.
- Release-unit batching within a Plan (`issues/20261030-191057_flowimp002_plan-release-units.md`).
- Consumer discovery (`issues/20261030-191006_flowimp001_consumer-impact-scan.md`).

## Dependencies
Sequencing only, in either order, with `issues/20261030-191057_flowimp002_plan-release-units.md`: both change `templates/plan.md`, `skills/plan-to-implementation-procedure/workflow.md`, `skills/code-implementation/workflow.md`, and `tools/manage_workitem_stage.py`; whichever lands second rebases onto the other. No other open issue or Plan targets these files (checked with `rg` over `issues/*.md` and `plans/*.md`, 2026-10-30).

## Unresolved Questions
- `不明`: whether the prose dependency statements of the open Plans can be converted mechanically or need a one-time manual pass.
- `不明`: whether `Gated` should be a new status or a `Blocked`/`Pending` note with a fixed prefix.
- Assumption: a Plan's dependency can always be expressed as a Plan or Issue path plus a phase.

## AI Implementation Instruction
Implement the tool, the template lines, and the skill steps only. Keep the tool read-only and advisory. Do not reorder, regenerate, or edit any existing Plan or procedure as part of this issue. Stop and report if the status vocabulary change conflicts with `templates/execution-status.md`.

## Traceability
- **Workflow phase**: issue-creator
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20261030-191144
- **Related target files**: `tools/plan_dependency_order.py`, `tests/tools/test_plan_dependency_order.py`, `tools/manage_workitem_stage.py`, `templates/plan.md`, `templates/execution-status.md`, `skills/plan-to-implementation-procedure/workflow.md`, `skills/code-implementation/workflow.md`, `tools/TOOL_DESCRIPTIONS.md`, `routing.md`
