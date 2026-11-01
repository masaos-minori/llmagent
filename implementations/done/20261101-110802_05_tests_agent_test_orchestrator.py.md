## Goal

Add adapter-wiring tests to `tests/agent/test_orchestrator.py` proving REQ-005 end-to-end at
the adapter boundary: `WorkflowEngineAdapter` sets `ctx.workflow.tool_call_recorder` to its
own `StateStore` at turn entry (alongside `current_task_id`) and clears it in the `finally`
path, on all exit routes.

## Scope

- New test class(es) in `tests/agent/test_orchestrator.py`; no existing test modified.
- Uses the file's existing fixtures: `_make_ctx()` (MagicMock ctx), `_make_orchestrator()`,
  the autouse `_patch_workflow_loader` fixture, and the temp-DB StateStore pattern already
  used at L383/L484 ("Replace StateStore with one that uses our temp DB").

## Assumptions

- The new tests follow the L383/L484 pattern (real `StateStore` on a temp workflow DB, real
  adapter, mocked engine internals) rather than the pure-MagicMock pattern, so the recorder
  assignment exercises the real facade object.
- `ctx.workflow` is reachable as an attribute on the `_make_ctx()` MagicMock; assertions read
  `ctx.workflow.tool_call_recorder` at three points: before the turn, during the engine call
  (captured via the existing fake-engine/_patched-WorkflowEngine hook), after the turn.

## Design decisions

- Assert identity (`ctx.workflow.tool_call_recorder is adapter._state_store`) rather than
  type or duck-typing: the whole REQ-005 contract is "the adapter's own store instance", and
  identity is the strictest cheap assertion.
- Cover both normal completion and exception exit (`WorkflowHaltError` route, mirroring the
  existing `TestHandleWorkflowEngineStatusPreservation` style): the clear must happen on both
  paths because the `finally` in the turn-entry path is what guarantees no stale recorder
  leaks between turns.

## Alternatives considered

- Asserting only after-turn state (field is `None`): rejected — proves the clear but not the
  set; the failure mode this feature regresses into is a recorder that is never wired, so
  the during-turn capture is mandatory.
- New dedicated test file: rejected — the adapter turn-entry fixtures already live in this
  file and the plan's frozen target list names this file.

## Implementation
### Target file

`tests/agent/test_orchestrator.py`

### Procedure

1. Add a test (or class `TestToolCallRecorderWiring`) with a turn-entry capture hook: the
   patched fake workflow engine records `ctx.workflow.tool_call_recorder` and
   `ctx.workflow.current_task_id` when invoked.
2. `test_recorder_set_at_turn_entry_and_cleared_after`: run one turn; assert the captured
   recorder during the turn is the adapter's StateStore instance and captured
   `current_task_id` equals the task id; assert `ctx.workflow.tool_call_recorder is None`
   after the turn completes.
3. `test_recorder_cleared_on_exception_exit`: same capture, engine raises
   `WorkflowHaltError` (or another mapped error); assert during-turn set and after-turn
   cleared.
4. `test_recorder_none_before_first_turn`: assert the field is `None` on a fresh ctx before
   any turn ran (pins the default).

### Method

Append new tests after the existing turn-entry test classes
(`TestExecuteStageRetryRunsTurnEntryOnce` neighborhood, which already exercises the entry
path these tests extend).

### Details

- The capture must read the field at engine-invocation time, not after the turn: after-turn
  reads cannot prove the field was set during tool execution (the point where `tool_runner`
  looks it up).
- Reuse the temp-DB StateStore construction from the L383/L484 pattern so no production DB
  path (`/opt/llm/db/workflow.sqlite`) is touched.

## Compatibility considerations

- Existing 3851 tests under `tests/agent/` (measured 2026-11-01) unaffected: additions only.
  The autouse `_patch_workflow_loader` fixture patches `agent.orchestrator.StateStore`
  (MagicMock), `agent.orchestrator.WorkflowLoader`, and
  `agent.workflow_engine_adapter.WorkflowEngine` (fake engine) — `self._state_store` in the
  adapter is whatever `agent.orchestrator.StateStore` resolves to at construction, so use the
  L383/L484 `TempStateStore` monkeypatch pattern to make it a real temp-DB `StateStore`
  instance for the identity assertion.
- If `_make_ctx()`'s MagicMock auto-creates `ctx.workflow.tool_call_recorder`, the
  "before/after" assertions must compare against `None` explicitly (`is None`), since
  MagicMock attributes are not `None` by default — construct the test ctx with a real
  `WorkflowState()` if the mock ambiguity proves fragile.

## Security considerations

- N/A: test-only, temp DB under pytest tmp_path.

## Rollback considerations

- Deleting the added class reverts to pre-change state.

## Validation plan

- `uv run pytest tests/agent/test_orchestrator.py -x -q` then `uv run pytest tests/agent -x -q`
  (3851-test baseline + new).
- Full sequence per `rules/toolchain.md`; note mypy's primary scope is `scripts/
  tests/eventbus` — `tests/agent` is validated by execution, not by CI mypy; diff-cover
  ≥90%.
- Mutation spot-check: remove the `finally` clear locally and confirm the exception-exit test
  fails.

## Completion criteria

- REQ-005/REQ-008 acceptance criteria pass: recorder is the adapter's StateStore during the turn and
  `None` after on both normal and halt routes.
- All pre-existing tests in the file pass unmodified.

## Out of Scope

- `tool_runner` producer unit tests (row 04).
- e2e crash → pending → interrupted → replay test (toolexec001 Phase 6, plan Risk 3).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 20261101-125601 | 20261101-125601 | TestToolCallRecorderWiring (3 tests) + _temp_workflow_store helper appended after TestExecuteStageRetryRunsTurnEntryOnce; spy captures field at engine-invocation time |
| 2 | Add or update tests per Validation plan | Completed | 20261101-125601 | 20261101-125601 | This row IS the test implementation row; no separate test target |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20261101-125601 | 20261101-125601 | ruff clean; file 120 passed (117 pre-existing unmodified); mutation spot-check: removing the deactivate clear failed 2 wiring tests; full suite 10864 passed; diff-cover 100% |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Completed | 20261101-125601 | 20261101-125601 | N/A: test-only row |

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
- **Requirement ID**: REQ-005, REQ-008
- **Source issue**: issues/done/20261031-175803_toolstate001_tool-call-state-producer.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261101-105136_toolstate001_tool-call-state-producer.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261101-110802
- **Related target files**: tests/agent/test_orchestrator.py