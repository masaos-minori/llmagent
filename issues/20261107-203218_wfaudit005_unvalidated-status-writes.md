# Validate and constrain workflow status writes

## Priority
Medium

## Summary
Status columns in the workflow tables accept arbitrary strings: `update_task_status`, `finish_attempt`, and `finalize_tool_call` pass caller-supplied status values straight into SQL, and `tasks.status` / `attempts.status` have no CHECK constraint. Define the allowed status vocabulary per table and enforce it.

## Background
Code review evidence (Verified):
- `tool_call_state.state` carries a SQL CHECK constraint; `tasks.status` and `attempts.status` do not.
- The engine writes bare string literals (e.g. an exit-status literal for failed attempts) and the adapter writes halt/completion statuses; none of the status-writing helpers validate the value.
- Status values form an implicit state machine (`running`, `completed`, `failed`, `halted`, `interrupted`) that is nowhere declared in one place; each writer hardcodes its own literals.
Related archived work: `issues/done/20261103-134148_wfreview007_docs-turn-status-table-vs-adapter-halt-write.md` (docs vs halt-write mismatch, resolved) and `issues/done/20261021-093421_turn003_task-status-overwritten-after-failure.md` (resolved) show status semantics have repeatedly drifted.

## Problem
A typo or a new writer can insert any string into a status column, silently creating states no reader recognizes. Diagnostics and recovery queries already have to guess which values exist. Adding a CHECK later then fails on rows the unconstrained writes created.

## Reason for Change
The workflow status vocabulary is shared by recovery, halt handling, and diagnostics; making it a declared, enforced contract is cheap now and increasingly expensive once more writers appear. This is a maintainability/type-safety fix with data-integrity payoff.

## Implementation Intent
Declare the allowed status sets once (a shared constant or enum near the workflow persistence boundary), accept only those values in the status-writing helpers, and mirror them in the DDL CHECK constraints for `tasks.status` and `attempts.status` (the `tool_call_state.state` pattern already shows the intended shape). Replace scattered literals in the engine/adapter with the declared values.

## Target Files or Areas
- scripts/agent/workflow/state_store.py (status-writing facade methods)
- scripts/agent/workflow/task_ops.py, scripts/agent/workflow/attempt_ops.py
- scripts/agent/workflow/workflow_engine.py (status literals)
- scripts/db/schema_sql.py (CHECK constraints)

## Required Changes
- Define the allowed status vocabulary per table in one place.
- Validate status arguments in the facade/ops writers; raise on unknown values.
- Add CHECK constraints to `tasks.status` and `attempts.status` matching the vocabulary.
- Replace bare status literals in engine/adapter call sites with the declared values.

## Constraints
- Existing databases contain only currently-written values; a CHECK must not newly reject a database the current code wrote. Confirm the live value set before fixing the constraint (a probe query on the production copy counts as evidence).
- workflow.sqlite has no migration path: if a CHECK must be added to existing tables, use the archive-and-recreate procedure, coordinated with the schema-gate issue so the gate matches the new shape.
- Public method signatures stay compatible.

## Acceptance Criteria
- Writing an unknown status raises a clear error instead of persisting it.
- The DDL enforces the same vocabulary the code declares.
- A single declaration of the status vocabulary exists and all writers reference it.

## Testing Expectations
- Unit tests: unknown status rejected per table; all known statuses accepted.
- Schema tests confirm the CHECK constraints exist and accept every value the code writes.
- Full workflow test package remains green.

## Documentation Impact
The workflow state machine (which statuses exist per table and legal transitions if any are defined) belongs in the agent state/persistence documentation as a boundary statement. Keep it declarative; no per-caller enumeration.

## Out of Scope
- Reconciling task rows after recovery (separate issue).
- Changing halt or retry semantics.
- Session or eventbus status columns.

## Dependencies
- Coordinate DDL changes with `issues/20261107-203216_wfaudit003_schema-gate-table-gap.md` (gate must match the constrained shape).
- Semantically related: `issues/20261107-203220_wfaudit007_task-status-never-reconciled.md` (the vocabulary declaration should land before or with that reconciliation work).

## Unresolved Questions
- Is `tasks.status` still needed at all if no production code consumes it (see the task-status reconciliation issue)? Decide vocabulary after that decision.

## AI Implementation Instruction
Keep the vocabulary declaration single-sourced; do not sprinkle validation conditionals across call sites. Run a probe query against the deployed workflow database before writing the CHECK constraint, and record the observed value set in the PR text.

## Traceability
- **Workflow phase**: python-code-review
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20261107-203218
- **Related target files**: scripts/agent/workflow/state_store.py, scripts/agent/workflow/task_ops.py, scripts/agent/workflow/attempt_ops.py, scripts/agent/workflow/workflow_engine.py, scripts/db/schema_sql.py
