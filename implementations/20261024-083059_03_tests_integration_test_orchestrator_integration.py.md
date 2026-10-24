## Goal

Migrate the two remaining `_process_turn` call sites in the integration suite to the split API, and
add one characterization test proving that a resumed (`existing_task_id`) task also performs entry
preparation exactly once (`REQ-007`, `AC-7`).

## Scope

- One test file only: `tests/integration/test_orchestrator_integration.py` (existing file, migrated
  call sites + one extended resume test).
- The production split this file tests lives in `scripts/agent/workflow_engine_adapter.py` (Row 1);
  this document contains modification instructions for this file only.

## Assumptions

- The two call sites inspect the LLM payload after entry preparation, so both halves must run in order
  (same reasoning as `tests/agent/test_orchestrator.py` Category B).
- The resume cases at `:718-782` exercise `_init_workflow_task` (task creation/resumption), not
  `_process_turn`; they keep passing unchanged.

## Design decisions

- Drive a real `execute_turn` for the resumed-task test so the once-per-turn prepared step is actually
  on the path; assert the prepared step ran once rather than assuming it.

## Alternatives considered

- Asserting only that `_init_workflow_task` resumes correctly — rejected: that covers task lookup, not
  the entry-preparation boundary this Plan moved.

## Implementation

### Target file

`tests/integration/test_orchestrator_integration.py`

### Procedure

1. Migrate the two direct `_process_turn` calls (Category B): `:665`
   (`test_tool_call_ephemeral_and_memory_injected_in_same_payload`) and `:706-707`
   (`test_tool_call_ephemeral_not_duplicated_across_turns`).
2. Add `TestResumedTaskPreparesOnce` to `TestWorkflowResumeWithRealDB` (the class at `:715`), which
   already contains the `existing_task_id` resume cases that must keep passing unchanged.

### Method

#### Migration (`:665`, `:706-707`)

Both are direct calls that inspect the payload built by the LLM stage after entry preparation. Replace
each `_process_turn(line, ctx, 0.0)` with the two-call sequence (prepare, then run the stage):

```python
# :665 before
_answer, error_kind, _is_partial = await orch._workflow_adapter._process_turn(
    "what headings are here?", ctx, 0.0
)
# :665 after
adapter = orch._workflow_adapter
await adapter._prepare_turn_input("what headings are here?", ctx)
_answer, error_kind, _is_partial = await adapter._run_execute_stage(
    ctx, ctx.workflow.workflow_id, ctx.session.session_id,
    ctx.workflow.current_task_id, 0.0,
)
```

`:706-707` runs two turns — repeat the two-call block for `"first turn"` then `"second turn"`. Keep
the payload assertions at `:669-676` and `:709-712` intact. `audit_stage_completed` inside
`_run_execute_stage` is a no-op mock under the `MagicMock` ctx.

#### New test: `TestResumedTaskPreparesOnce`

Follow the resume harness already in `TestWorkflowResumeWithRealDB` (`:718-792`): patch
`agent.workflow_engine_adapter.get_task_by_id` to an `existing_task`, patch `create_task` (assert it
is not called), patch `agent.orchestrator.StateStore` and `audit_workflow_start`, build
`Orchestrator(ctx)`, set `orch._workflow_def = MagicMock(version="test-v1")`, then drive a real
`execute_turn(line, turn_started_at, session_id, existing_task_id=<id>)` with a mocked
`ctx.services_required.llm.stream`.

- Assert `_prepare_turn_input` (equivalently `append_user_message`) is called exactly once for the
  resumed run — the reused task does not re-run entry preparation.
- Strengthen with a forced retry: leave `ctx.turn.current_turn_id` empty so the LLM half raises on
  every attempt, and still assert the prepared step ran once despite multiple attempts.
- Keep the existing halted-task rejection (`test_resume_rejects_halted_task`, `:769-792`) untouched;
  do not move or rewrite those methods.

### Details

- Do NOT introduce a `_process_turn` name anywhere in this file (`AC-7`).
- The new test belongs inside `TestWorkflowResumeWithRealDB` so the resume characterization sits next
  to the cases it extends.

## Compatibility considerations

- N/A: test-only additions; no public API change.

## Security considerations

- N/A: test-only.

## Rollback considerations

- Single logical change in one test file; revert the commit.

## Validation plan

- `uv run pytest tests/integration/test_orchestrator_integration.py` — all existing resume cases plus
  the migrated sites and the new `TestResumedTaskPreparesOnce` pass.
- `uv run python tools/check_mock_patch_targets.py` — reports no finding (`AC-7`).

## Completion criteria

- Both call sites point at the split API; `TestResumedTaskPreparesOnce` present and passing; existing
  resume outcomes unchanged (`AC-7`).

## Out of Scope

- The production split (`scripts/agent/workflow_engine_adapter.py`) — Row 1.
- `tests/agent/test_orchestrator.py` — Row 2.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | migrate :665, :706-707 |
| 2 | Add or update tests per Validation plan | Pending | — | — | add TestResumedTaskPreparesOnce |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | include check_mock_patch_targets.py |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Pending | — | — | N/A: test-only file |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| — | — | — | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| — | — | — | — | — | — |

## Traceability
- **Workflow phase**: plan-to-implementation-procedure
- **Requirement ID**: `REQ-007` (migrate the integration call sites; characterize once-per-turn prep on the resumed-task path)
- **Source issue**: issues/20261021-093421_turn002_execute-stage-retry-duplicates-user-messages.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261023-102728_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261024-083059
- **Related target files**: tests/integration/test_orchestrator_integration.py
