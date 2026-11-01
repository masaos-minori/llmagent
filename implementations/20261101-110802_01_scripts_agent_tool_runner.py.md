## Goal

Make `scripts/agent/tool_runner.py` the single writer of the agent-side `tool_call_state`
table: record a row in state `pending` before each dispatch and finalize it to
`completed`/`failed` after, keyed identically to the transport dedup key, so
`workflow_engine.build_turn_control_message` (already merged, L110-128) has producer data to
classify instead of always finding `no stale tool calls`. Implements REQ-001, REQ-002,
REQ-003, REQ-004, REQ-006, REQ-007, REQ-009 of the source plan (design decisions D1, D3,
D4, D5, D6).

## Scope

- Modify `_recorded_call` (L65-95): the only place a state row is written (plan Risk 1 —
  `_execute_with_dag`/`_run_plan_batches`/`_run_group_calls` stay writer-free).
- Modify `execute_one_tool_call` (L190-234): build the key and pass key/task_id/tool to the
  recorder.
- New module-level helper `_record_pending_state(ctx, pc, key, task_id)` for the
  pre-dispatch write.
- No signature changes: `ctx` already reaches `_recorded_call`, so recorder lookup is
  `ctx.workflow.tool_call_recorder` (frozen context-flow audit row 11, `ctx.workflow`
  confirmed at `tool_runner.py` L79).

## Assumptions

- `ctx.workflow.tool_call_recorder` is set by the adapter at turn entry (row 03) and is
  `None` in unit-test contexts that do not wire it — recording is then skipped silently
  (REQ-008: recorder `None` means zero behavior change, zero rows written).
- `ctx.session.session_id` mirrors the transport uid when the adapter path is live
  (`mixin_base.py` L39 and `repl_input_loop.py` L111 set it to `str(session_id)`); fallback
  when unset mirrors the transport fallback (`uid="default"` when `session_id` is `None`,
  `None` otherwise) per design decision D3.
- `ctx.workflow.current_task_id` is set at the same turn-entry point (adapter L292);
  `None` means no task context and recording is skipped.

## Design decisions

- Record inside `_recorded_call` (committed choke point), not in the DAG planner or the
  adapter: every call already funnels through it (planner, batch, group, single), it sees
  `ctx` and the terminal outcome, and BaseException (e.g. `asyncio.CancelledError`) already
  propagates through it unchanged (L65-95 docstring), which is exactly the crash case REQ-004
  requires to leave the row `pending`.
- Key re-derived via `shared.http_transport.derive_idempotency_key("call_tool", pc.name,
  pc.args, str(uid))` — the same function the transport layer itself uses (L62); transport is
  NOT modified (plan Constraint).
- Recorder accessed through the `ToolCallRecorder` Protocol field on `WorkflowState`
  (row 02); `tool_runner` gains no new injected parameter and no direct `StateStore` import
  (import-layer contract: `agent -> shared`, no cross-agent state ownership).
- `retry_class` comes from `shared.mcp_dedup.retry_class(tool_name)`, the owner module for
  the REQ-006 classification (`config/mcp_dedup.toml [retry_class]`; unknown tools default
  `non_retryable`, fail-safe unreplayable).
- Recorder call failures are caught (`BLE001`, noqa-justified per the existing audit-callsite
  precedent at `_idempotency_key` L123) and logged at warning level — tool execution must
  not break because state recording broke (REQ-007).

## Alternatives considered

- Adapter-level wrap around the turn loop: rejected — cannot observe per-call outcomes
  inside the DAG execution, and would duplicate the call loop.
- ContextVar-injected recorder (the wiped-WIP design, plan UNK-05): rejected — the committed
  `execute_one_tool_call(ctx, pc, guard)` already receives `ctx`, so a dataclass field is
  the narrower mechanism with no implicit ambient state.
- Writing rows from `shared.http_transport` or `shared.mcp_dedup`: rejected — the agent-side
  `tool_call_state` table (workflow.sqlite) and the dispatcher-side
  `mcp_dedup_snapshot` table (mcp_dedup.sqlite) are separate stores with separate schemas
  (plan Verification Evidence); the producer belongs on the agent side.

## Implementation
### Target file

`scripts/agent/tool_runner.py`

### Procedure

1. Add TYPE_CHECKING import: `from agent.workflow.state_store import ToolCallRecorder`
   (runtime typing-only, same pattern as existing TYPE_CHECKING imports at L17).
2. Add module-level `import shared.http_transport` and `import shared.mcp_dedup` (runtime;
   both are `shared -> agent`-clean and already dependency-free of agent code).
3. Add `_state_key(ctx, name, args)` helper resolving the uid fallback (D3) and returning
   `derive_idempotency_key("call_tool", name, args, str(uid))`.
4. Add `_record_pending_state(ctx, pc, key, task_id) -> None`: resolve
   `ctx.workflow.tool_call_recorder`; if recorder or `task_id` is `None`, return; else call
   `recorder.record_tool_call(task_id, key, pc.name, retry_class(pc.name))` wrapped in
   `except Exception` → `logger.warning`.
5. In `execute_one_tool_call`: after the approval block and before `executor(...)` dispatch
   (around L228-231 where `key = tool_hash_key(args)` is already computed), compute
   `state_key = _state_key(ctx, pc.name, pc.args)` and `state_task_id =
   ctx.workflow.current_task_id`, call `_record_pending_state`, then pass
   `state_key`/`state_task_id` into `_recorded_call`.
6. In `_recorded_call`: accept `state_key: str | None`, `state_task_id: str | None` keyword
   arguments; after `result = await execute_one_tool_call(...)` completes (both the success
   and the captured-`Exception` branches, before returning the row), call
   `recorder.finalize_tool_call(state_task_id, state_key, "completed" or "failed")`
   guarded the same way as step 5; BaseException must skip finalize (propagates as today).

### Method

Inline edits to two functions plus two new module-level private helpers; no new class, no
signature changes to public functions, no config changes.

### Details

- Recorder lookup happens once per call inside `_recorded_call` (`recorder =
  ctx.workflow.tool_call_recorder`); a `None` recorder is a no-op, which keeps all existing
  unit tests passing without rewiring (they do not set the field).
- The pending write must happen before dispatch, not before approval: a denied call has no
  dispatch to dedup against and stays unrecorded (matches consumer semantics — only executed
  calls matter to `build_turn_control_message`).
- `finalize_tool_call` maps captured execution failures to `failed` and normal returns to
  `completed`; `recorder.mark_tool_call_interrupted` is NOT called here (the consumer's
  `classify_stale_pending` owns the `interrupted` transition).
- The existing `_idempotency_key` (L123) audit hash and its `snapshot_id` argument to
  `audit_tool_exec` remain exactly as-is: audit and state keys are separate concerns
  (plan Verification Evidence).
- Vulture baseline for this file is 0 findings; bandit baseline 0 high/medium; keep the two
  new `except Exception` handlers noqa-BLE001-justified with a one-line comment citing
  REQ-007 (recording failure must not break execution).

## Compatibility considerations

- Existing callers unchanged: `_recorded_call` is called only from `tool_runner.py` L82 and
  the keyword additions are internal; `execute_all_tool_calls` (L400-407), `ToolLoopGuard`,
  `ToolCallStopReason`, `PreparedToolCall` untouched.
- `tests/agent/test_tool_runner.py` and `tests/agent/test_tool_approval_preflight.py` call
  `execute_one_tool_call`/`execute_all_tool_calls` directly with un-wired `ctx.workflow`
  (`tool_call_recorder=None`): behavior unchanged (silent skip), 321-agent-test baseline
  preserved.
- Consumer side already merged (`build_turn_control_message`, `classify_stale_pending` call
  at `workflow_engine.py` L128): no consumer edits in scope.

## Security considerations

- Keys are derived from a salted SHA-256 of name + canonical-JSON args + session id
  (`derive_idempotency_key`, `DEFAULT_IDEMPOTENCY_SALT`): no tool arguments or session ids
  are written into the table, only the hash.
- Recorder failure logging must log the exception type/message only, never tool arguments
  (the args may contain sensitive content).

## Rollback considerations

- Revert the single file (`git checkout -- scripts/agent/tool_runner.py`): with no recorder
  wired (rows 02/03 not yet merged), the helper short-circuits, so the change is inert by
  itself; rollback safe in any merge order because the recorder field defaults to `None`.

## Validation plan

- Targeted: `uv run pytest tests/agent/test_tool_runner.py tests/agent/test_tool_approval_preflight.py -x -q`.
- New tests land in row 04 (`tests/agent/test_tool_runner.py`): pending-before-dispatch,
  completed/failed finalize, exception-in-recorder non-fatal, BaseException leaves pending,
  un-wired-recorder no-op.
- Full sequence per `rules/toolchain.md`: `ruff check`, `ruff format --check`,
  `uv run mypy scripts/`, `bandit -ll`, `radon cc -nc`, `vulture`, `make test`; diff-cover
  gate ≥90% on the new lines.
- E2E (toolexec001 Phase 6 completion): crash mid-call → row stays `pending` → next turn
  `build_turn_control_message` reports it → replay path consumes the key.

## Completion criteria

- All REQ-001..REQ-004, REQ-006, REQ-007, REQ-009 acceptance criteria listed in the plan row 1 pass.
- Lint/type/security gates clean with no new suppressions beyond the two justified BLE001
  noqa comments.
- Existing 321 agent tests still pass unmodified.

## Out of Scope

- Recorder injection (row 03) and the `ToolCallRecorder` Protocol (row 02).
- `scripts/shared/http_transport.py`, `scripts/shared/mcp_dedup.py`,
  `scripts/agent/workflow/tool_call_state_ops.py`, `scripts/agent/workflow/state_store.py`
  (must not change — plan Constraint).
- `tool_http_transport.py` (does not exist on master; plan UNK-05).
- Interrupt classification (owned by `classify_stale_pending` / consumer).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | |
| 2 | Add or update tests per Validation plan | Pending | — | — | |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Pending | — | — | |

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
- **Requirement ID**: REQ-001, REQ-002, REQ-003, REQ-004, REQ-006, REQ-007, REQ-009
- **Source issue**: issues/done/20261031-175803_toolstate001_tool-call-state-producer.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261101-105136_toolstate001_tool-call-state-producer.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261101-110802
- **Related target files**: scripts/agent/tool_runner.py
