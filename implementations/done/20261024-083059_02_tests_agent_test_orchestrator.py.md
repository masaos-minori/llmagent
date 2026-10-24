## Goal

Add adapter-level execute-stage-retry coverage that does not exist today, and migrate every existing
`_process_turn` call site to the split API without weakening any assertion (`REQ-007`, `AC-7`).

## Scope

- One test file only: `tests/agent/test_orchestrator.py` (existing file, new test classes + migrated
  call sites).
- The production split this file tests lives in `scripts/agent/workflow_engine_adapter.py` (Row 1);
  this document contains modification instructions for this file only.

## Assumptions

- The seven `_process_turn` call sites assert payload composition and turn boundaries, never the stage
  boundary itself, so they can be pointed at the split API unchanged (`ASSUM-04`).
- `audit_stage_completed` (now inside `_run_execute_stage`) returns early when
  `ctx.services_required.audit_logger is None`; with a `MagicMock` ctx it is a mock call, so driving
  `_run_execute_stage` directly in an existing test does not introduce a DB write.

## Design decisions

- New coverage drives the **real** engine with the shipped `config/workflows/default.json` policy
  (`max_attempts: 3`, `backoff_sec: 1`) — no test mocks the engine's retry, so the boundary is
  actually exercised (`tests` Execution policy).
- The deterministic reproduction path is leaving `ctx.turn.current_turn_id` empty, so
  `attempt_id=""` makes `LLMTurnRunner.run()` raise `RuntimeError` (`llm_turn_runner.py:73-78`) on
  every attempt — three attempts, one input — which is exactly the condition that duplicates the
  writes today.

## Alternatives considered

- Mocking the engine to invoke the execute callback twice — rejected: the Execution policy forbids
  mocking retry and requires the real `max_attempts`/`backoff_sec` to be exercised.

## Implementation

### Target file

`tests/agent/test_orchestrator.py`

### Procedure

1. Add three new test classes below (names fixed by the plan):
   `TestExecuteStageRetryRunsTurnEntryOnce`, `TestEntryWorkFailureIsNotRetried`,
   `TestEntryWorkOutsideStageTimeout`.
2. Migrate the seven `_process_turn` references at `:1167`, `:1491`, `:1529-1530`, `:1909`, `:2038`,
   `:2082`. See Migration below for the per-site mapping.
3. Run the affected test module and `check_mock_patch_targets.py`; keep every existing assertion.

### Method

#### New tests

Build the real-engine / temp-DB harness following `test_handle_turn_does_not_raise_on_real_asyncio_wait_for_timeout`
(`:360-399`): patch `db.helper.build_db_config` to a `DbConfig` pointing at `tmp_path` sqlite files,
call `create_workflow_schema()`, define a `TempStateStore(StateStore)` using a `SQLiteHelper` on the
temp path, and `monkeypatch` `agent.orchestrator.StateStore` → `TempStateStore`,
`agent.workflow_engine_adapter.WorkflowEngine` → real `WorkflowEngine`,
`agent.workflow_engine_adapter.create_task` → real `create_task`. Then `_make_orchestrator(ctx)`
gives a real engine.

- **`TestExecuteStageRetryRunsTurnEntryOnce`** (AC-1, AC-2, AC-3, AC-6): force the retry by leaving
  `ctx.turn.current_turn_id` empty so the LLM half raises `RuntimeError` on every attempt (three
  attempts, one input). Assert, after the turn halts: exactly one user message in `ctx.conv.history`;
  exactly one `kind='user'` row for that input read back through `fetch_messages()`; `stat_turns`
  advanced by exactly 1; `clear_previous_turn_ephemeral_messages()` called once; `memory.on_user_prompt`
  and `classify_and_inject_mode` each called once; the first-turn background task spawned at most
  once; and `ctx.cfg.tool.allowed_tools` observed by the LLM stage equals the mode-classified value
  and equals the configured value again after the turn. This is the witness that the boundary moved:
  before the fix the `stat_turns` delta equals the attempt count (3), after it is 1.
- **`TestEntryWorkFailureIsNotRetried`** (AC-5): make `handle_history_compression` raise
  `HistoryCompressionError` (`scripts/agent/history.py:35`) from the prepared step. Assert the task
  ends `halted` (not `failed`): a turn-entry failure is routed through the same halt handler as a
  stage failure (REQ-003), so the observable end state matches the pre-split behavior; `on_error` is
  called exactly once, at most one user row exists, and there is **no** `attempts` row for the entry
  step (entry work is outside the retry loop).
- **`TestEntryWorkOutsideStageTimeout`** (AC-4 boundary for REQ-006): with `execute.timeout_sec` set
  below the entry-work delay, the turn still completes and does not raise `WorkflowTimeoutError`; with
  the LLM stage slower than the timeout it still raises. Proves entry work left the stage timeout while
  the LLM stage stays bounded by it.

#### Migration of the seven call sites

`_process_turn` no longer exists. It produced `(answer, error_kind, is_partial)` and combined entry
preparation with the LLM half. The split gives two methods: `_prepare_turn_input(line, ctx)` (returns
`None`) and `_run_execute_stage(ctx, workflow_id, session_id, task_id, turn_started_at)` (returns the
same tuple). Map each site by what it currently mocks:

**Category A — patches `_process_turn` with `AsyncMock(return_value=("ok", None, False))`**
(`:1167`, `:1909`, `:2038`, `:2082`). These mock the whole turn processor and assert a call count or a
turn-level outcome. Replace the patched name with `_run_execute_stage`:

```python
# :1167 before
with patch.object(orch._workflow_adapter, "_process_turn", new=process):
# :1167 after
with patch.object(orch._workflow_adapter, "_run_execute_stage", new=process):
```

The mock's return value still matches the `(answer, error_kind, is_partial)` contract, and
`await_count` semantics are preserved (one execute-stage invocation per turn, no retry in these
tests). **Gotcha:** `_run_execute_stage` is now only the LLM half, so the real `_prepare_turn_input`
runs for the first time in these tests. If a test's `MagicMock` ctx or harness errors on real
preparation, additionally stub it with a separate `AsyncMock()` — this does not change the
`await_count`/outcome assertion, which is on `_run_execute_stage`.

**Category B — direct call `_process_turn(line, ctx, 0.0)` to inspect the LLM payload**
(`:1491`, `:1529-1530`). The payload is built by the LLM stage *after* entry preparation injects memory
and clears ephemeral, so both halves must run in order. Replace the single call with the two calls:

```python
# :1491 before
_answer, error_kind, _is_partial = await orch._workflow_adapter._process_turn(
    "what headings are here?", ctx, 0.0
)
# :1491 after
adapter = orch._workflow_adapter
await adapter._prepare_turn_input("what headings are here?", ctx)
_answer, error_kind, _is_partial = await adapter._run_execute_stage(
    ctx, ctx.workflow.workflow_id, ctx.session.session_id,
    ctx.workflow.current_task_id, 0.0,
)
```

`:1529-1530` runs two turns in sequence — repeat the two-call block for the second turn
(`"second turn"`). The `ctx` values wired by `_wire_memory_and_mode` (`workflow_id`, `current_task_id`,
`current_turn_id`) and `_make_ctx` (`session_id`) supply the audit args; `audit_stage_completed` is a
no-op mock here. Keep the payload assertions at `:1496-1502` and the turn-boundary assertions at
`:1532-1535` intact.

### Details

- Do NOT re-introduce a `_process_turn` name anywhere (not even a thin wrapper); `AC-7` requires
  `grep -n "_process_turn" tests/` to return nothing.
- `:2038` and `:2082` live in `TestHandleWorkflowEngineStatusPreservation`, which already patches
  `_init_workflow_task`, `_deactivate_workflow`, and the `WorkflowEngine`. Apply the same
  `_run_execute_stage` replacement there; the real prepared step runs under the mock engine.
- The new test classes must keep passing `tests/agent/workflow/test_workflow_engine.py`,
  `TestHandleTurnInvokesWorkflowEngine` (`:167`, `:260-358`), `test_ephemeral_filtering_security.py`,
  and `test_history_compression_consistency.py`.

## Compatibility considerations

- No public API changes; only private adapter methods and test internals move.

## Security considerations

- N/A: test-only additions; no policy or access change.

## Rollback considerations

- Single logical change in one test file; revert the commit.

## Validation plan

- `uv run pytest tests/agent/test_orchestrator.py` — all existing classes plus the three new ones
  pass.
- `uv run python tools/check_mock_patch_targets.py` — reports no finding (`AC-7`).
- Full suite regression check: `uv run pytest` confirms the four protected modules above still pass.

## Completion criteria

- Three new classes present and passing; all seven call sites point at the split API; every original
  assertion retained; `check_mock_patch_targets.py` clean (`AC-7`).

## Out of Scope

- The production split (`scripts/agent/workflow_engine_adapter.py`) — Row 1.
- `tests/integration/test_orchestrator_integration.py` — Row 3.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 2026-10-24 | 2026-10-24 | See migration mapping above |
| 2 | Add or update tests per Validation plan | Completed | 2026-10-24 | 2026-10-24 | 3 new classes + 7 migrated sites |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 2026-10-24 | 2026-10-24 | include check_mock_patch_targets.py |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Completed | 2026-10-24 | 2026-10-24 | N/A: test-only file |

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
- **Requirement ID**: `REQ-007` (migrate the seven call sites and add adapter-level stage-retry coverage), backing `REQ-001`..`REQ-006` via the new assertions
- **Source issue**: issues/20261021-093421_turn002_execute-stage-retry-duplicates-user-messages.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261023-102728_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261024-083059
- **Related target files**: tests/agent/test_orchestrator.py
