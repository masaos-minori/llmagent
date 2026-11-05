# Turn-status docs contradict the adapter's tested halted-write for turn-entry preparation failures

## Priority
Low

## Summary
`docs/23_agent/agent_03_03_turn-processing-flow-workflow-engine.md` states that a turn failing before the engine starts leaves `tasks.status='pending'` and that "cancellation is the only status write the adapter makes". The adapter actually writes `halted` when turn-entry preparation (which runs before `engine.run`) fails, and this behavior is deliberate and test-locked. Update the status-transition table and the adapter-write wording to match the implemented, tested contract.

## Background
Adversarial code review of `scripts/agent/workflow/` and its integration points (2026-11-03). Evidence:

- Confirmed: `docs/23_agent/agent_03_03_turn-processing-flow-workflow-engine.md:88` — table row "The turn fails before the engine starts | `pending` | neither | the row keeps the value it was created with, because no stage ever ran"; and `:93` — "Cancellation is the only status write the adapter makes."
- Confirmed: `scripts/agent/workflow_engine_adapter.py:225-234` — a `_prepare_turn_input` failure writes `self._state_store.update_task_status(task.task_id, "halted")` and re-raises as `WorkflowHaltError`; the in-code comment states the intent: "mark the task halted and route it through the existing halt handler ... identical end state to a stage halt (REQ-003)". `_prepare_turn_input` runs before `engine.run` (`:222` vs `:235`), so this is a "turn fails before the engine starts" case that leaves `halted`, not `pending`.
- Confirmed tested: `tests/agent/test_orchestrator.py:806-897` — `TestEntryWorkFailureIsNotRetried` ("A turn-entry failure halts immediately: no retries, no attempts row (AC-5)") asserts `status == "halted"` after a history-compression failure in the prepared step. The code side is a contract with regression coverage; the docs are the stale side.
- Confirmed: the docs describe turn-entry preparation itself (`agent_03_03...md:108-111`) but never state its failure outcome, so the only table row that covers "fails before the engine starts" is the contradicting `pending` row.
- Confirmed test gap for the doc's remaining claim: a failure before the task row exists (e.g. `_init_workflow_task` raising `RuntimeError` at `workflow_engine_adapter.py:317,319-321`) genuinely writes no status, but no test asserts the row stays `pending` for that exit — the `pending` row of the table is only true for that narrower case.

## Problem
The status-transition table is the reference for anyone reasoning about workflow task lifecycle (including `issue-to-plan` work on recovery semantics). Two of its claims are false against current code: a pre-engine turn-entry failure writes `halted` (not `pending`), and the adapter performs a second status write besides cancellation. A reader using the table would misclassify halted tasks as never-started tasks.

## Reason for Change
The docs file was regenerated during the `20261101-163219` wfrecovery001 procedure batch (`implementations/done/20261101-163219_15_docs_23_agent_agent_03_03_turn-processing-flow-workflow-engine.md.md`) yet still carries the contradicting rows; leaving it stale directly undermines the wfrecovery001 state-machine work that builds on this vocabulary.

## Implementation Intent
Docs correction (code is intentional and test-locked):
- Split the "fails before the engine starts" row into the two real cases: (a) failure while the task row exists but before any stage ran — including turn-entry preparation — records `halted`, written by the adapter; (b) failure before/without a task row (task creation or lookup failure) — no status write happens, and the row semantics are `pending` only if the row was created.
- Fix the "cancellation is the only status write the adapter makes" sentence to enumerate the adapter's actual writes (cancelled → `halted`; turn-entry preparation failure → `halted`).

## Target Files or Areas
- `docs/23_agent/agent_03_03_turn-processing-flow-workflow-engine.md`
- `tests/agent/test_orchestrator.py` (only if the plan adds a `pending`-preservation test for the task-creation-failure case)

## Required Changes
- Update the status table row at `agent_03_03...md:88` to describe both pre-engine cases and their writers.
- Update the sentence at `:93` to list all adapter status writes.
- Ensure the section around `:108-111` (turn-entry preparation) states its failure outcome and links it to the table.
- Optional (plan decides): add a small test that a task-lookup failure (`RuntimeError` from `_init_workflow_task`) leaves no status write (row absent or `pending`).

## Constraints
- Do not change adapter code behavior: the `halted` write is an AC-5/REQ-003 contract with passing regression tests (`TestEntryWorkFailureIsNotRetried`).
- Doc wording must keep consistency with the adjacent claims that already hold: cancellation → `halted` (`:87,91-93`), engine-writes-`failed`-exactly-once (`:85`), and `tools/check_docs_consistency.py --domain agent`.

## Acceptance Criteria
- The status table no longer claims `pending` for turn-entry preparation failures, and no longer claims cancellation is the adapter's only status write.
- `uv run python tools/check_docs_consistency.py --domain agent` passes.
- `TestEntryWorkFailureIsNotRetried` and the rest of the orchestrator tests pass unchanged.

## Testing Expectations
- Docs consistency checker (`tools/check_docs_consistency.py --domain agent`).
- Existing orchestrator tests as behavior lock; optional new test only for the task-creation-failure case.

## Documentation Impact
This is a documentation-accuracy fix: correct the task-status transition table, the adapter-write sentence, and add the turn-entry preparation failure outcome (intent + failure behavior). Record in the same doc that `halted`-from-preparation and `halted`-from-cancellation are distinguished by the absence of attempt rows (see `:96-98`).

## Out of Scope
- Changing the adapter's status writes or the halt vocabulary (owned by the wfrecovery001 state-machine contract).
- The cancelled-turn attempt-row behavior (`workflow_engine.py` leaving the attempt `running` on cancellation) — verified as documented intent at `agent_03_03...md:96-98` and not treated as a defect here.

## Dependencies
- `issues/20261030-105639_wfrecovery001_workflow-recovery-state-machine.md` (open, High): its plan will extend this same status vocabulary; if it lands first, re-check this issue's wording against the new table before editing.

## Unresolved Questions
- 不明: whether the plan wants the optional `pending`-preservation test now or folded into the wfrecovery001 wave.

## AI Implementation Instruction
Docs-only correction unless the plan explicitly adds the optional test. Cite the tested behavior (`TestEntryWorkFailureIsNotRetried`) when choosing which side is authoritative; do not "fix" the code to match the old table.

## Traceability
- **Workflow phase**: `python-code-review` (adversarial review of `scripts/agent/workflow/` and integration points), filed via `issue-creator`
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20261103-134148
- **Related target files**: `docs/23_agent/agent_03_03_turn-processing-flow-workflow-engine.md`, `tests/agent/test_orchestrator.py`
