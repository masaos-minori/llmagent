## Goal

Split `_process_turn()` (`workflow_engine_adapter.py:323-356`) into two private methods so that
turn-entry input preparation runs exactly once per `execute_turn()` call, independent of how many
times the workflow engine retries the `execute` stage, while the execute stage keeps only
LLM/tool execution, error/partial classification, assistant persistence, and its own
`audit_stage_completed` (`REQ-001`, `REQ-002`).

## Scope

- One production file only: `scripts/agent/workflow_engine_adapter.py`.
- Add two private methods, remove `_process_turn()`, and restructure `execute_turn()` so the single
  `self._tool_override(self._allowed_tools)` scope spans both the prepared step and `engine.run()`.
- Unchanged: `_init_workflow_task()` (`:252-292`), `_activate_workflow()` (`:294-303`),
  `_handle_workflow_halt()` (`:311-321`), `_handle_turn_end()` (`:369-385`), `_tool_override()`
  (`:358-367`), the `try`/`except`/`finally` shape (`:145-204`), `plan_fn` (`:158-159`),
  `verify_fn` (`:178-183`), and every parameter/return of `execute_turn()`.

## Assumptions

- Everything entry work produces already reaches the LLM stage through `ctx` (`ctx.conv.history`
  via `llm_turn_executor.py:64`, `ctx.cfg.tool.allowed_tools` via the tool-override scope), so nothing
  needs to cross the new boundary as an argument (`ASSUM-01`, `REQ-001`).
- `ctx.turn.current_turn_id` is set before the stage runs, so `workflow_id`/`task_id`/`attempt_id`
  are non-empty and `LLMTurnRunner.run()` does not raise `RuntimeError` (`REQ-005`).
- The `finally` block (`:189-202`) produces the same task-status outcome for a prepared-step failure
  as the retry loop produces for a stage failure today (`ASSUM-03`, `REQ-003`).
- No production path relies on entry work being retried (`UNK-01`); see Validation plan.

## Design decisions

- **DR-001** Turn-entry work runs once in `execute_turn()`, after `_activate_workflow()` (`:152`) and
  before `engine.run()` (`:185`). Chosen by the user (Option A). It matches the once-per-run pattern
  the class already has (`:146-152`) and the once-per-turn semantics `ConversationStateManager`
  already encodes (`:106-119`). Consequence: a stage retry re-runs only LLM/tool execution; entry
  failures are no longer retried and leave the stage timeout (`REQ-006`).
- **DR-002** One `self._tool_override(self._allowed_tools)` scope spans both halves. It moves out of
  `_process_turn()` into `execute_turn()`, wrapping `_prepare_turn_input` (new) (new) and `engine.run`.
  `classify_and_inject_mode()` assigns `ctx.cfg.tool.allowed_tools` permanently
  (`mode_classification.py:289`), so a second, separate `with` around each half would revert it
  between the halves and silently lose the mode decision (`REQ-004`).
- **DR-003** The prepared call stays inside the existing `try`/`except`/`finally`, so
  `except (WorkflowHaltError, WorkflowTimeoutError)` (`:186-188`) and the `finally` status/deactivate/
  close path (`:189-202`) apply unchanged. A prepared-step failure marks the task `failed` and calls
  `on_error` exactly as a stage failure does today (`REQ-003`, `AC-5`).

## Alternatives considered

- Option B (self-guarding entry effects in `ConversationStateManager`) — rejected: four guards in a
  class `orchestrator` and `commands/` also call, and entry work stays inside the stage timeout
  (`plans/..._plan.md` DR-001).
- Option C (`execute.retryable: false`) — rejected: removes the protection the LLM/tool stage exists
  for and rewrites the documented contract (`docs/23_agent/agent_03_03_*:82-88`).
- An "already prepared" flag on `AgentContext` / passing prepared values into the stage callback —
  rejected: a second source of truth, and the engine calls stage callbacks with no arguments
  (`workflow_engine.py:28`).

## Implementation

### Target file

`scripts/agent/workflow_engine_adapter.py`

### Procedure

1. Add `_prepare_turn_input(self, line, ctx)` containing the five entry calls currently at
   `:332-336`, inside its own body but WITHOUT a `with self._tool_override(...)` block (the scope
   now lives in `execute_turn()` — see DR-002).
2. Add `_run_execute_stage(...)` (new) containing the per-attempt half: `handle_llm_turn` (`:338-344`),
   the `result.action` / `is_partial` / `persist_as_assistant` logic (`:345-354`), and the
   `audit_stage_completed` block moved from `execute_fn` (`:167-175`). Returns
   `(answer, error_kind, is_partial)`.
3. Remove `_process_turn()` entirely (`:323-356`). No surviving method is named `_process_turn`
   (`REQ-002`, `AC-7`).
4. In `execute_turn()`: replace the `execute_fn` body so it awaits `_run_execute_stage(...)` (new) instead
   of `_process_turn(...)`, and move the `with self._tool_override(self._allowed_tools):` block from
   inside the old `_process_turn()` up to wrap `await self._prepare_turn_input(...)` and
   `await engine.run(...)` as one scope.
5. Confirm no other production caller of `_process_turn()` exists (`rg -n '_process_turn' scripts/`
   must return nothing; the only caller was `execute_fn`).

### Method

Current `execute_fn` (`:161-176`):

```python
async def execute_fn() -> str | None:
    """Process the user turn via process_turn and log stage completion."""
    nonlocal answer, error_kind, is_partial
    answer, error_kind, is_partial = await self._process_turn(
        line, self._ctx, turn_started_at
    )
    elapsed_ms = round((time.perf_counter() - turn_started_at) * 1000, 1)
    audit_stage_completed(
        self._ctx,
        task.task_id,
        "execute",
        elapsed_ms,
        workflow_id=workflow_id,
        session_id=session_id,
    )
    return None
```

New `execute_fn` — the audit block leaves `execute_fn` and enters `_run_execute_stage` (new); only the
`nonlocal` assignment and the call remain:

```python
async def execute_fn() -> str | None:
    """Run one execute-stage attempt and return its result."""
    nonlocal answer, error_kind, is_partial
    answer, error_kind, is_partial = await self._run_execute_stage(
        self._ctx, workflow_id, session_id, task.task_id, turn_started_at
    )
    return None
```

The tool-override + engine block in `execute_turn()` (`:185`), which today has no explicit `with`
(the scope lived inside `_process_turn()`):

```python
            await engine.run(task, plan_fn, execute_fn, verify_fn)
```

becomes one scope that prepares once and then runs the engine (`DR-002`):

```python
            with self._tool_override(self._allowed_tools):
                await self._prepare_turn_input(line, self._ctx)
                await engine.run(task, plan_fn, execute_fn, verify_fn)
```

New `_prepare_turn_input(self, line, ctx)` — the five entry calls (`:332-336`) only, no tool
override, no return value:

```python
    async def _prepare_turn_input(self, line: str, ctx: AgentContext) -> None:
        """Run turn-entry input preparation once, before the engine runs.

        Clears the previous turn's ephemeral messages, injects memory, classifies
        the turn mode, appends the user message, and compresses history. Runs once
        per execute_turn() regardless of execute-stage retries (REQ-001). Called
        from execute_turn() inside the single self._tool_override scope that also
        wraps engine.run(), so the mode-classified allowed_tools is in force for
        the LLM stage (REQ-004).
        """
        self._conversation_manager.clear_previous_turn_ephemeral_messages()
        await self._conversation_manager.handle_memory_injection(line)
        await classify_and_inject_mode(line, ctx)
        await self._conversation_manager.append_user_message(line)
        await self._conversation_manager.handle_history_compression()
```

New `_run_execute_stage(self, ctx, workflow_id, session_id, task_id, turn_started_at)` — the
per-attempt half plus the moved audit block. `line` is NOT an argument: the LLM half reads the
context from `ctx` and never used `line`; `turn_started_at` (previously unused in the old
`_process_turn`, see `UNK-03`) is now consumed here for `elapsed_ms`:

```python
    async def _run_execute_stage(
        self,
        ctx: AgentContext,
        workflow_id: str,
        session_id: str,
        task_id: str,
        turn_started_at: float,
    ) -> tuple[str, str | None, bool]:
        """Perform one execute-stage attempt: LLM/tool execution, error and
        partial-answer classification, assistant persistence, and
        audit_stage_completed. Per-attempt only; turn-entry preparation lives in
        _prepare_turn_input (REQ-002). Returns (answer, error_kind, is_partial)
        with the same contract as the removed _process_turn().
        """
        result = await self._llm_executor.handle_llm_turn(
            ctx.conv.llm_url,
            workflow_id=ctx.workflow.workflow_id or "",
            task_id=ctx.workflow.current_task_id or "",
            stage_id="execute",
            attempt_id=ctx.turn.current_turn_id or "",
        )
        answer = result.answer
        error_kind: str | None = None
        is_partial = False
        if result.action != "continue":
            error_kind = result.error_kind or result.reason or result.action
            if (
                isinstance(result.exception, LLMTransportError)
                and result.exception.partial_text
            ):
                is_partial = True
        elif result.persist_as_assistant:
            ctx.session.save("assistant", answer)

        elapsed_ms = round((time.perf_counter() - turn_started_at) * 1000, 1)
        audit_stage_completed(
            ctx,
            task_id,
            "execute",
            elapsed_ms,
            workflow_id=workflow_id,
            session_id=session_id,
        )
        return answer, error_kind, is_partial
```

Notes that keep this behavior-preserving:

- `answer = result.answer` is assigned before the `if`, exactly as today, so the returned answer is
  identical for every `result.action`.
- Neither new method contains its own `with self._tool_override(...)`. The ONLY tool-override scope
  is the one in `execute_turn()` above. Adding a `with` to either helper would restore
  `allowed_tools` between the two halves and break `REQ-004`.
- `audit_stage_completed` reads `task_id`/`workflow_id`/`session_id` from the arguments
  `execute_turn` passes, so the audit event carries the same values as today.

### Details

- Signature choice: the stage half takes `workflow_id`, `session_id`, `task_id`, `turn_started_at`
  because those are the locals `execute_turn` already has for `audit_stage_completed`; the engine's
  zero-argument `StageCallback` (`workflow_engine.py:28`) forces `execute_fn` to be a zero-arg
  closure, so it captures none of them — it passes them explicitly. `ctx` supplies everything the
  LLM half reads (`conv.llm_url`, `workflow.workflow_id`, `workflow.current_task_id`,
  `turn.current_turn_id`).
- `UNK-03` resolves itself: the old `turn_started_at` parameter was unused in `:325-356`; it is now
  used by `_run_execute_stage` (new).
- Module size (`UNK-04`): the split adds two methods and removes one; measure with
  `check_module_size.py` after the change (gate 16384 B, current 14798 B, no baseline entry). If it
  fails, move the preparation method to a small private helper module under `scripts/agent/` — a
  design consequence inside this Plan, not a new work item.

## Compatibility considerations

- No public signature changes: `execute_turn()` keeps its signature and `(answer, error_kind,
  is_partial)` return; stage callbacks keep `Callable[[], Awaitable[str | None]]`.
- `plan_fn` and `verify_fn` now run inside the widened tool-override scope. `plan_fn` returns `None`
  and `_handle_turn_end` reads no tool configuration (`:234-242`, `:369-385`), so nothing observable
  changes today; `AC-6` asserts the equivalence rather than assuming it.

## Security considerations

- The tool-override still scopes `ctx.cfg.tool.allowed_tools` to the instance list for the whole
  turn, including the prepared step, so `classify_and_inject_mode()`'s permanent assignment is
  restored after the turn exactly as before (`REQ-004`, `:358-367`).

## Rollback considerations

- Single logical change in one file; revert the commit. The split introduces no new import, schema,
  config, or service, so reverting restores the pre-change state cleanly.

## Validation plan

Behavior (drive the real engine with the shipped `config/workflows/default.json` policy — never
mock the retry):

- New `TestExecuteStageRetryRunsTurnEntryOnce` (new): forced failing first attempt, second succeeds;
  assert exactly one user message in `ctx.conv.history`, exactly one `kind='user'` row via
  `fetch_messages()`, `stat_turns` +1, memory injection / `classify_and_inject_mode` called once,
  `allowed_tools` correct during the stage and restored after (`AC-1`..`AC-3`, `AC-6`). Real-engine
  temp-DB harness at `tests/agent/test_orchestrator.py:360-399`.
- New `TestEntryWorkFailureIsNotRetried` (new): `HistoryCompressionError` → task `failed`, `on_error` once,
  one user row at most, no `attempts` row for the entry step (`AC-5`).
- New `TestEntryWorkOutsideStageTimeout` (new): `execute.timeout_sec` below the entry delay still
  completes without `WorkflowTimeoutError`; a slower LLM stage still raises (`AC-4` boundary for
  `REQ-006`).
- Migrated call sites keep every existing assertion (`AC-7`).

Static / architectural (recorded baselines, `AC-8`):

- `uv run ruff check scripts/ tests/`
- `uv run mypy --no-namespace-packages scripts/` (baseline: Success, 437 files)
- `PYTHONPATH=scripts uv run lint-imports` (baseline: 6 kept, 0 broken)
- `uv run python tools/check_module_size.py` (no new violation, no new baseline entry)
- `uv run radon cc -s -n C scripts/agent/workflow_engine_adapter.py scripts/agent/conversation_state_manager.py` (baseline: empty)
- `uv run vulture scripts/agent/workflow_engine_adapter.py scripts/agent/conversation_state_manager.py --min-confidence 80` (baseline: empty)
- `uv run bandit -c pyproject.toml -ll scripts/agent/workflow_engine_adapter.py` (baseline: exit 0)
- `uv run python tools/check_mock_patch_targets.py` (migrated test patches; `AC-7`)

Regression set that must keep passing unchanged: `tests/agent/workflow/test_workflow_engine.py`,
`tests/agent/test_orchestrator.py::TestHandleTurnInvokesWorkflowEngine` (`:167`, `:260-358`),
`tests/agent/test_ephemeral_filtering_security.py`, `tests/agent/test_history_compression_consistency.py`.

Before leaving the retry path, read the history-compression fallback contract at
`docs/03_testing/testing_01_quality-roadmap-testing-quality-and-debug-retrospective.md:158` and
confirm `handle_history_compression` handles its own failure (`UNK-01`); if a production path depends
on retried entry work, stop and reopen `REQ-006` before Phase 2.

## Completion criteria

- Exactly one user message per retried turn (`AC-1`); memory injection and mode classification each
  called once (`AC-2`); `stat_turns` +1, ephemeral clear once, first-turn task at most once
  (`AC-3`).
- Retry semantics unchanged: attempts recorded, exhaustion raises `WorkflowHaltError`,
  `WorkflowTimeoutError` not retried, non-retryable stages run once (`AC-4`).
- A prepared-step failure is not retried and creates no `attempts` row for the entry step
  (`AC-5`).
- `allowed_tools` observed by the LLM stage equals the mode-classified value and is restored after
  the turn (`AC-6`).
- No `_process_turn` reference remains anywhere in `tests/` (`AC-7`); static/architectural checks
  pass against their baselines (`AC-8`).

## Out of Scope

- `scripts/agent/conversation_state_manager.py`, `scripts/agent/mode_classification.py`,
  `scripts/agent/llm_turn_executor.py`, `scripts/agent/llm_turn_runner.py`, `scripts/agent/workflow/`,
  `config/workflows/default.json` — unchanged by this Plan.
- Documentation updates — handled by the docs rows of this Plan (`agent_03_03`, `agent_03_01`), not
  this file.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the split of `_process_turn` into `_prepare_turn_input` (new) + `_run_execute_stage` (new); restructure `execute_turn` so one tool-override scope spans both halves | Completed | 2026-10-24 | 2026-10-24 | DR-001/DR-002/DR-003; see Implementation > Method |
| 2 | Add `TestExecuteStageRetryRunsTurnEntryOnce` (new), `TestEntryWorkFailureIsNotRetried` (new), `TestEntryWorkOutsideStageTimeout` (new); migrate the 7 test call sites | Completed | 2026-10-24 | 2026-10-24 | Row 2 covers the test file |
| 3 | Run the validation sequence (`rules/toolchain.md`) + `check_mock_patch_targets.py` | Completed | 2026-10-24 | 2026-10-24 | Baselines in Validation plan |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Completed | 2026-10-24 | 2026-10-24 | Doc rows handle agent_03_03/agent_03_01 |

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
- **Requirement ID**: `REQ-001`, `REQ-002`, `REQ-003`, `REQ-004`, `REQ-005`, `REQ-006` (split the once-per-turn boundary out of the retryable execute stage; keep externally observable failure behavior and the tool-override equivalence)
- **Source issue**: issues/20261021-093421_turn002_execute-stage-retry-duplicates-user-messages.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261023-102728_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261024-083059
- **Related target files**: scripts/agent/workflow_engine_adapter.py
