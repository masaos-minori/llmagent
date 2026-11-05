## Goal
- Make the turn-status table and the adapter-write wording in the workflow-engine doc match the implemented and test-locked behavior: a turn-entry preparation failure records `halted` (written by the adapter), a failure while creating or resuming the task row writes no status, and the adapter has two status writes, not one.

## Priority
Low

## Scope
- **In-Scope**: the "The turn fails before the engine starts" row of the status table; the sentence "Cancellation is the only status write the adapter makes."; a failure-outcome statement for turn-entry preparation next to its description.
- **Out-of-Scope**: any adapter or engine code change; the halt vocabulary and the wfrecovery001 state-machine contract; the cancelled-turn attempt-row behavior; new tests.
- **Dependencies**: `N/A: none` for ordering. `plans/done/20261030-114041_wfrecovery001_workflow-recovery-state-machine.md` (consumed, rows all `Pending`, code unimplemented) lists this same doc under REQ-010 and will rewrite its state-semantics sections; when it is picked up, it must start from this corrected wording.

## Background
Adversarial review (2026-11-03) found the status table claiming a pre-engine failure leaves `pending` with "neither" as writer, and the doc stating that cancellation is the adapter's only status write.

## Problem
Verified in Step 2:
- Doc: the table row `| The turn fails before the engine starts | pending | neither | ... |` and the bullet "Cancellation is the only status write the adapter makes." in `docs/23_agent/agent_03_03_turn-processing-flow-workflow-engine.md`. The "Turn-entry preparation" note states what the step does but not how it fails.
- Code: `scripts/agent/workflow_engine_adapter.py` `execute_turn` runs `_prepare_turn_input` before `engine.run`; a non-halt exception there calls `self._state_store.update_task_status(task.task_id, "halted")` (only when the task row exists) and raises `WorkflowHaltError`, so the outcome is `halted` with `error_kind` `workflow_halted`. The second adapter write is `_record_exit_status`, which writes `halted` for `exit_reason == "cancelled"` only (`_status_for_exit`). Both are adapter writes; the engine writes `running`, `halted`, `failed`, `completed` itself.
- Test lock for the `halted` side: `TestEntryWorkFailureIsNotRetried` in `tests/agent/test_orchestrator.py` asserts a `halted` row, zero attempt rows, and an `on_error` call with `WorkflowHaltError`.

Corrections to the Issue:
- The Issue says no test asserts the `pending` outcome. One exists: `test_failure_before_engine_start_keeps_pending` ("Case H") in `tests/agent/test_orchestrator.py` makes `audit_workflow_start` raise after the row is created and asserts the status is `pending` with no status write. The optional new test is therefore not needed.
- The Issue proposes recording that preparation-`halted` and cancellation-`halted` are "distinguished by the absence of attempt rows". That is not reliable: a cancellation that arrives during turn-entry preparation also writes `halted` through `_record_exit_status` with zero attempt rows. The doc will distinguish them by how the turn ends instead: a preparation failure returns `error_kind` `workflow_halted` and reaches `on_error`, while a cancellation propagates `CancelledError`.
- Cancellation is recorded `halted` at any point after the task row exists, not only "while a stage is running"; the sentence listing adapter writes states this without altering the existing row.

## Reason for Change
The table is the reference for task lifecycle reasoning; two of its claims are false against code and tests, and the wfrecovery001 work builds on this vocabulary.

## Implementation Intent
Docs-only edit of one file, with the code and tests as the authority. Split the pre-engine row in two: (a) failure in turn-entry preparation, row exists, no stage ran: `halted`, written by the turn adapter, `error_kind` `workflow_halted`; (b) failure while creating or resuming the task row or activating it: no status write, the row keeps its created value `pending` (or does not exist). Replace the "only status write" sentence with the two adapter writes. Add one sentence under the turn-entry preparation note naming its failure outcome and pointing to the table.

## Requirements
- `REQ-001`: The status table describes both pre-engine cases with their statuses and writers, and no row claims `pending` for a preparation failure.
- `REQ-002`: The adapter-write sentence lists both adapter writes (preparation failure to `halted`; cancellation to `halted`) and no longer says cancellation is the only one.
- `REQ-003`: The turn-entry preparation note states its failure outcome and links it to the table, and distinguishes it from cancellation by turn result, not by attempt rows.
- `REQ-004`: Every added claim is backed by code or an existing test named in this Plan, and the agent-domain docs checkers pass.

## Implementation Target Files
**Freeze status**: Frozen

This table is the canonical, frozen source of implementation scope for this Plan. Once
`Frozen`, `Implementation steps`, `Acceptance criteria`, and every downstream
`plan-to-implementation-procedure` document MUST reference file paths only from this
table — no other file may be treated as a modification target.

| File Path | Change Responsibility | Reason for Modification | Related Requirement / Acceptance Criterion | Repository Evidence | Related Tests | Validation Status |
|---|---|---|---|---|---|---|
| `docs/23_agent/agent_03_03_turn-processing-flow-workflow-engine.md` | Turn processing and workflow engine doc | Correct the status table row, the adapter-write bullet, and add the preparation failure outcome | REQ-001, REQ-002, REQ-003, REQ-004 / AC-1, AC-2, AC-3, AC-4 | Table row and bullet in the "Task Status Transitions" section; `_prepare_turn_input` failure path writes `halted` in `workflow_engine_adapter.py` (checked in Step 2) | `tools/check_docs_consistency.py --domain agent`; `tests/agent/test_orchestrator.py` as the behavior lock | Verified |

## Reference Files
| File Path | Why It Must Be Read | Related Target File or Requirement |
|---|---|---|
| `scripts/agent/workflow_engine_adapter.py` | Authoritative adapter status writes and `_status_for_exit` | REQ-001, REQ-002 |
| `scripts/agent/workflow/workflow_engine.py` | Engine status writes (`running`, `halted`, `failed`, `completed`) | REQ-001 |
| `tests/agent/test_orchestrator.py` | `TestEntryWorkFailureIsNotRetried` and the Case H test lock the documented behavior | REQ-004 |

## Acceptance Criteria
- AC-1 (REQ-001): the table has separate rows for a preparation failure (`halted`, turn adapter) and a task-row creation or resume failure (no write; `pending` if the row was created); no `pending`-for-preparation claim remains (`rg` over the doc).
- AC-2 (REQ-002): the doc no longer contains "Cancellation is the only status write the adapter makes" and names both adapter writes.
- AC-3 (REQ-003): the turn-entry preparation note states the failure outcome and a link to the table; it contains no "distinguished by the absence of attempt rows" claim.
- AC-4 (REQ-004): `uv run python tools/check_docs_consistency.py --domain agent`, `check_docs_quality.py`, `check_docs_structure.py`, `check_docs_content_policy.py --strict`, and `check_docs_japanese.py` pass; `uv run pytest tests/agent/test_orchestrator.py` still passes (no code changed).

## Tests
- `REQ-001`..`REQ-004`: no new tests. The behavior lock is `TestEntryWorkFailureIsNotRetried` (`halted` side) and `test_failure_before_engine_start_keeps_pending` (`pending` side), both in `tests/agent/test_orchestrator.py`; the docs checkers cover the doc.

## Documentation Impact
The one target document above (resolved through `docs/00_index.md` "Document References by Task", agent domain); drives REQ-001 to REQ-003. No other doc states these status writes (`rg "only status write"` over `docs/` finds only this file).

## Assumptions
- Code and tests are authoritative; the Issue's constraint not to change adapter behavior stands.
- Overlap on the same doc with `plans/20261105-085821_wfreview003_workflow-loader-bare-int-coercion.md` judged compatible: that Plan edits "Workflow Loader Validation Rules"; this Plan edits "Task Status Transitions" and the turn-entry preparation note; the sections are disjoint (Step 8b).
- `docs/` content policy: the added text describes behavior and cites no line numbers or test names, so it stays inside `skills/DESIGN.md` Docs content policy.

## Unknowns
| ID | Unknown Description | Evidence Missing | Resolution Path | Blocking? (True/False) |
|---|---|---|---|---|
| UNK-01 | Whether wfrecovery001 (consumed Plan, unimplemented) will reword this table again | Its Execution Status rows are all `Pending` | Implementer of that Plan re-reads the corrected wording first | False |

## Affected areas
| File | Change | Blast Radius | Churn (30d) | Bus Factor | deploy.sh Impact |
|---|---|---|---|---|---|
| `docs/23_agent/agent_03_03_turn-processing-flow-workflow-engine.md` | Modify | Low: one table row and two short passages | N/A | N/A | None (docs are not deployed) |

## Design
Path A (1 file, no code, interface, or schema change). Single-owner decision: the code and tests win over the stale table. The edit is limited to the three passages in Implementation Intent; the surrounding claims that already hold (cancellation to `halted`, engine writes `failed` once, a failing status write propagates) are left untouched, and the new wording is checked against them by `check_docs_consistency.py`. Consumer scan not required: no symbol or constant changes.

## Implementation steps
1. **Phase 1: Docs correction**
   - [ ] Rewrite the status table row and the adapter-write bullet (REQ-001, REQ-002; `docs/23_agent/agent_03_03_turn-processing-flow-workflow-engine.md`)
   - [ ] Add the preparation failure outcome to the turn-entry preparation note (REQ-003; `docs/23_agent/agent_03_03_turn-processing-flow-workflow-engine.md`)
2. **Phase 2: Verification**
   - [ ] Run the docs checkers and the orchestrator tests (REQ-004; `docs/23_agent/agent_03_03_turn-processing-flow-workflow-engine.md`). No deploy step: nothing under `scripts/` or `config/` changes.

### Release units
N/A: no release unit

## Validation plan
| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| `docs/23_agent/agent_03_03_turn-processing-flow-workflow-engine.md` | Docs checkers | `uv run python tools/check_docs_quality.py`, `check_docs_structure.py`, `check_docs_content_policy.py --strict`, `check_docs_consistency.py --domain agent`, `check_docs_japanese.py` | Pass |
| same | Behavior lock (unchanged code) | `uv run pytest tests/agent/test_orchestrator.py -k "EntryWorkFailure or before_engine_start"` | Pass |

Validation quality baseline: `N/A: no Python target`.

## Risks
- **Risk**: The new wording over-generalizes cancellation (any point after the row exists) beyond what a test locks → **Mitigation**: the statement follows `_status_for_exit` and the `finally` in `execute_turn` (read in Step 2); it is stated as the adapter's rule, not as a new guarantee.
- **Risk**: wfrecovery001 rewrites the same table later and reintroduces the old claim → **Mitigation**: recorded in Scope Dependencies and UNK-01.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Correct the table, the adapter-write bullet, and the preparation note | In Progress | — | — |  |
| 2 | Run docs checkers and orchestrator tests | Pending | — | — |  |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| — | — | — | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| implementations/20261105-093123_01_docs_23_agent_agent_03_03_turn-processing-flow-workflow-engine.md.md | 1 | Procedure | Pending | — | — |

## Traceability
- **Workflow phase**: issue-to-plan
- **Source issue**: issues/20261103-134148_wfreview007_docs-turn-status-table-vs-adapter-halt-write.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: this document is the generated plan
- **Source implementation procedure**: N/A: not applicable in this phase
- **Generated at**: 20261105-090353
- **Related target files**: `docs/23_agent/agent_03_03_turn-processing-flow-workflow-engine.md`

### Requirement Traceability
| Requirement ID | Source Issue section or evidence | Target file | Implementation step | Acceptance criterion | Test or validation item | Status |
|---|---|---|---|---|---|---|
| REQ-001 | Issue Required Changes 1; adapter `_prepare_turn_input` failure path | `docs/23_agent/agent_03_03_turn-processing-flow-workflow-engine.md` | Phase 1 | AC-1 | docs checkers; `rg` | Confirmed by repository evidence |
| REQ-002 | Issue Required Changes 2; `_status_for_exit` | `docs/23_agent/agent_03_03_turn-processing-flow-workflow-engine.md` | Phase 1 | AC-2 | `rg` | Confirmed by repository evidence |
| REQ-003 | Issue Required Changes 3, Documentation Impact (corrected: distinguish by turn result) | `docs/23_agent/agent_03_03_turn-processing-flow-workflow-engine.md` | Phase 1 | AC-3 | docs checkers | Derived from confirmed evidence |
| REQ-004 | Issue Acceptance Criteria 2-3 | `docs/23_agent/agent_03_03_turn-processing-flow-workflow-engine.md` | Phase 2 | AC-4 | checker commands in Validation plan | Explicit in issue |

<!-- tools/generate_workitem.py implementation-procedure-pass timestamp: 20261105-093123 -->