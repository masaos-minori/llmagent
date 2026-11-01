## Goal

Wire the tool-call state recorder into the turn lifecycle in
`scripts/agent/workflow_engine_adapter.py`: set `ctx.workflow.tool_call_recorder` to the
adapter's own `StateStore` at workflow activation (beside `ctx.workflow.current_task_id`) and
clear it at deactivation, so `tool_runner` (row 01) can resolve a live recorder during every
adapter-driven turn. Implements REQ-005 (design decision D2).

> Note (2026-11-01 verification): this document was regenerated during the pre-execution
> verification pass. The original body duplicated row 02 (`context.py` content); the target
> file for this row is `scripts/agent/workflow_engine_adapter.py`, per the plan's frozen
> Target Files table.

## Scope

- Modify `_activate_workflow` (L290-295): one added line setting the recorder.
- Modify `_deactivate_workflow` (L297-302): one added line clearing the recorder.
- Nothing else in the file changes.

## Assumptions

- `self._state_store` (assigned in the constructor, L95) is a `StateStore` instance in all
  adapter-driven paths; it structurally satisfies the `ToolCallRecorder` Protocol defined by
  row 02 in `agent/context.py` (facade signatures match exactly).
- `ctx.workflow.tool_call_recorder` and the `ToolCallRecorder` Protocol exist before this row
  executes (row 02 is a hard dependency; execution order 02 → 01 → 03).
- Deactivation is guaranteed on every exit route: the Orchestrator turn bracket calls
  `self._workflow_adapter.deactivate_workflow(self._ctx)` in its nested `finally`
  (`orchestrator.py` L198), which reaches `_deactivate_workflow`; the adapter's own
  `finally` (L216-220) only handles store close/ownership. No new control flow is needed
  to guarantee the clear.

## Design decisions

- Assignment beside `ctx.workflow.current_task_id = task.task_id` (L292) and clearing beside
  `ctx.workflow.current_task_id = None` (L300) — the plan's D2 anchor points: recorder
  lifetime is exactly the per-turn task-context lifetime.
- Assign `self._state_store` directly (the adapter's own store instance): no new constructor
  parameter, no import of the Protocol at runtime (the field type comes from `agent.context`,
  already imported), no new store construction or ownership change (`_owns_state_store`
  semantics at L103/L219-220 untouched).
- Set at `_activate_workflow`, not at `activate_workflow` (L124) wrapper: the private method
  is the single activation funnel used by all turn-entry paths.

## Alternatives considered

- Setting the recorder in `Orchestrator` before calling the adapter: rejected — the recorder
  is the adapter's own store instance; wiring it outside would split ownership and leak a
  recorder into non-adapter turns.
- ContextVar ambient injection (wiped-WIP design, plan UNK-05): rejected — same rejection as
  row 02 (implicit ambient state).
- Clearing only on normal return: rejected — an exception exit (halt/timeout) must not leave
  a stale recorder on a reused ctx; the existing `finally`-driven `_deactivate_workflow`
  covers every route.

## Implementation
### Target file

`scripts/agent/workflow_engine_adapter.py`

### Procedure

1. In `_activate_workflow` (L290-295), after `ctx.workflow.current_task_id = task.task_id`
   (L292), add:
   `ctx.workflow.tool_call_recorder = self._state_store`
2. In `_deactivate_workflow` (L297-302), after `ctx.workflow.current_task_id = None` (L300),
   add: `ctx.workflow.tool_call_recorder = None`

### Method

Two single-line additive edits inside two existing methods; no signature, import, or config
changes.

### Details

- mypy verifies at the added assignment that `StateStore` structurally satisfies
  `ToolCallRecorder | None` — this only holds if row 02's Protocol mirrors the facade
  exactly (`record_tool_call(self, task_id, idempotency_key, tool, retry_class,
  snapshot_id=None)`, `finalize_tool_call(self, idempotency_key, state)`).
- The clear line must be inside `_deactivate_workflow`, not added to a separate `finally`,
  so every existing call site of `_deactivate_workflow` (normal, halt, timeout routes) gets
  the clear for free.

## Compatibility considerations

- Two added attribute assignments on `WorkflowState` (row-02 field, default `None`): existing
  tests that never activate a workflow see no change; tests that patch
  `orch._workflow_adapter.activate_workflow`/`deactivate_workflow` (e.g. L439, L538 in
  `tests/agent/test_orchestrator.py`) bypass the private methods and are unaffected.
- The autouse `_patch_workflow_loader` fixture patches
  `agent.workflow_engine_adapter.WorkflowEngine` (mock engine) and `agent.orchestrator.StateStore`
  (MagicMock) — in those tests `self._state_store` is the patched mock; the assignment is
  still type-safe and behavior-neutral.
- Consumer paths (`build_turn_control_message`, L347 `ctx.workflow.current_task_id` read)
  untouched.

## Security considerations

- N/A: attribute wiring only, no I/O in this file change.

## Rollback considerations

- Revert the single file (`git checkout -- scripts/agent/workflow_engine_adapter.py`): with
  row 02 in place the field simply stays `None` (recorder unwired → recording no-ops), so
  this row can be reverted independently. Do not remove the row-02 field before reverting
  this file (the assignments would raise `AttributeError`).

## Validation plan

- `uv run mypy --no-namespace-packages scripts/ tests/eventbus` — the assignment site is the
  structural-satisfaction check for row 02's Protocol.
- Targeted: `uv run pytest tests/agent/test_orchestrator.py -x -q` (no test changes in this
  row; wiring tests land in row 05).
- Full sequence per `rules/toolchain.md`: ruff format/check, mypy (above),
  `PYTHONPATH=scripts uv run lint-imports`, bandit `-ll`, full-suite diff-cover ≥90%.

## Completion criteria

- `ctx.workflow.tool_call_recorder` is `self._state_store` during an activated turn and
  `None` after deactivation on normal and exception routes (proven by row-05 tests).
- mypy passes with no new suppressions.
- All 3851 tests collected under `tests/agent/` (measured 2026-11-01) pass unmodified.

## Out of Scope

- The `ToolCallRecorder` Protocol and field themselves (row 02).
- Recorder usage in `tool_runner` (row 01).
- Wiring tests (row 05, `tests/agent/test_orchestrator.py`).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 20261101-125522 | 20261101-125522 | 2 single-line assignments landed in _activate_workflow/_deactivate_workflow; mypy structural check passed |
| 2 | Add or update tests per Validation plan | Completed | 20261101-125522 | 20261101-125522 | N/A for this row: wiring tests land in row 05 |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20261101-125543 | 20261101-125543 | mypy 491 files clean; tests/agent 3859 passed/3 skipped; full suite 10864 passed; diff-cover 100% |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Completed | 20261101-125543 | 20261101-125543 | N/A for this row: doc update lands in row 06 |

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
- **Requirement ID**: REQ-005
- **Source issue**: issues/done/20261031-175803_toolstate001_tool-call-state-producer.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261101-105136_toolstate001_tool-call-state-producer.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261101-110802
- **Related target files**: scripts/agent/workflow_engine_adapter.py