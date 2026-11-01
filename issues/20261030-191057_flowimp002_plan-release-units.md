# Declare release units in Plans and run them as one batch

## Priority
High

## Summary
Let a Plan declare which phases must land together (a release unit), and give `code-implementation` a batch mode for such a unit: cycles run in Plan phase order, the full test suite runs once at the end of the unit, and all members are archived together after it passes. Ordinary Plans keep the per-cycle gate.

## Background
- `Operationally observed` (2026-10-30, plan `wfrecovery001`): the Plan listed Phase 2 (workflow schema) and Phase 3 (attempt write path) as separate phases. The schema row adds `attempts.attempt_number NOT NULL` with a unique index, which breaks every existing attempt insert, so neither phase could pass the suite alone. The work was finished only after the executor proposed, and the user approved, a single batch with one full-suite run at the end.
- `Operationally observed`: plan `wftaskapi001` states the same coupling in prose only (its Phase 3 title says "one release unit"); no field or check carries it.
- `Explicit in code`: `skills/code-implementation/workflow.md` Step 4 requires the full suite "exactly once per cycle" and Step 3c/Multi-file processing stop the batch on a cross-file conflict; there is no provision for cycles that are red by design until a later cycle lands. `templates/plan.md` has no release-unit field.
- `Operationally observed`: the session ran the full suite about eight times (427 to 493 seconds each); several runs existed only to satisfy the per-cycle rule.

## Problem
Plans describe phases as independent, while some phases can only be validated together. The executor must either break the per-cycle rule without a sanctioned procedure or split a coupled change into states that cannot be tested, and the Plan's phase status cannot express a group.

## Reason for Change
Persisted-schema changes always couple the schema row to its write path, so the situation recurs with every such Plan (`toolexec001`, `wflease001`, `dlqbox001` are queued). An explicit unit makes the exception reviewable, bounded, and cheaper than repeated full runs.

## Implementation Intent
Make the coupling a declared, checkable fact rather than an ad hoc decision. The Plan names the unit and states why its members cannot be green alone. Procedure documents carry the unit name. Batch mode keeps every safeguard that matters: cycles still run in Plan phase order, static validators (format, lint, types, import contracts) and impact-selected tests still run per cycle, a failure not attributable to a later member of the unit still stops the cycle, the Attempt Limit and Failure Log still apply, and the full suite and coverage gate run once at the end. Archival and Plan status updates happen for the whole unit after it passes.

## Target Files or Areas
- `templates/plan.md` and `templates/implementation-procedure.md` (the declaration and its carry-over)
- `skills/issue-to-plan/workflow.md` (where phases are written)
- `skills/plan-to-implementation-procedure/workflow.md` (copying the unit into each procedure)
- `skills/code-implementation/workflow.md` (batch mode and its explicit exception)
- `tools/check_workitem_structure.py` and its tests (format validation)
- `tools/manage_workitem_stage.py` and its tests (group display in `list` and `show`)

## Required Changes
- Add a release-unit declaration to the Plan template: unit name, member phases, and the stated reason the members cannot be validated alone.
- Carry the unit name into each generated procedure document.
- Add a batch mode to `code-implementation` with an explicit, referenced exception to the "exactly once per cycle" rule, the allowed red states, and the end-of-unit validation and archival.
- Validate the declaration format in `check_workitem_structure.py`.
- Show the unit grouping in `manage_workitem_stage.py list` and `show`.

## Constraints
- The per-cycle gate stays the default; a unit needs a stated, evidence-backed coupling.
- Safety rules stay in force: no parallel cycles, no bulk destructive commands, rollback limited to files recorded for the unit.
- `rules/ai-execution.md` Instruction Precedence applies: the exception must be stated in the narrower file and reference the rule it overrides.

## Acceptance Criteria
- `templates/plan.md` and `templates/implementation-procedure.md` carry the field, and a fixture Plan with a valid declaration passes `check_workitem_structure.py` while a malformed one fails.
- `skills/code-implementation/workflow.md` describes batch mode, names the rule it excepts, and keeps the per-cycle gate for Plans without a unit.
- `manage_workitem_stage.py list` groups procedures by unit.
- `check_skills_references.py` and `check_skills_heading_cycles.py` pass.

## Testing Expectations
- Unit tests for the declaration checker and the grouped display, including a Plan without a unit.
- A walk-through on the archived `wfrecovery001` Plan: with the declaration added to a copy, the described batch mode reproduces the run that was done by hand.
- Skill and docs checkers named in `routing.md` for the changed `skills/*.md` files.

## Documentation Impact
Yes. The skills and templates state the declaration, the batch mode, and the safeguards (intent, boundaries, failure behavior). No code-level detail in docs.

## Out of Scope
- Removing the per-cycle gate for ordinary Plans.
- Changing what the full suite is, the coverage threshold, or the Attempt Limit.
- Dependency ordering between Plans (a separate issue) and consumer discovery (`issues/20261030-191006_flowimp001_consumer-impact-scan.md`).

## Dependencies
N/A: none. No open issue or Plan targets these files (checked with `rg` over `issues/*.md` and `plans/*.md`, 2026-10-30). Related: `issues/20261030-191006_flowimp001_consumer-impact-scan.md` (reduces mid-unit discoveries).

## Unresolved Questions
- `不明`: whether a failure "attributable to a later member of the unit" can be decided mechanically or only by the executor's judgment; the first version may leave it to the executor and record the judgment in the Failure Log.
- `不明`: whether the Plan's own phase status should become per-unit or stay per-phase with a unit marker.
- Assumption: one unit per set of phases is enough; nested or overlapping units are not needed.

## AI Implementation Instruction
Change only the templates, skill workflows, and the two tools listed. Keep the per-cycle gate as the default and state the exception in the narrower file with a reference to the rule it overrides. Do not weaken the Attempt Limit, rollback, or the single end-of-unit full-suite and coverage run. Stop and report if the exception conflicts with `rules/workflow-lifecycle.md`.

## Traceability
- **Workflow phase**: issue-creator
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20261030-191057
- **Related target files**: `templates/plan.md`, `templates/implementation-procedure.md`, `skills/issue-to-plan/workflow.md`, `skills/plan-to-implementation-procedure/workflow.md`, `skills/code-implementation/workflow.md`, `tools/check_workitem_structure.py`, `tools/manage_workitem_stage.py`
