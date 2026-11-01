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
- `execute_one_tool_call` (L190-234) is NOT modified (plan D1: the recorder calls live
  entirely in `_recorded_call`).
- New module-level private helpers (all new): `_state_key(ctx, pc)`,
  `_record_pending_state(ctx, pc)`, `_finalize_state(ctx, state_key, state)`.
- No public signature changes: `ctx` already reaches `_recorded_call`, so recorder lookup is
  `ctx.workflow.tool_call_recorder` (frozen context-flow audit row 11; `ctx.workflow` is
  already read in this file in `_idempotency_key`, L124-126).

## Assumptions

- `ctx.workflow.tool_call_recorder` is set by the adapter at turn entry (row 03) and is
  `None` in unit-test contexts that do not wire it — recording is then skipped silently
  (REQ-008: recorder `None` means zero behavior change, zero rows written).
- `ctx.session.session_id` equals the transport uid string on the adapter path:
  `set_session_id(str(session_id))` is called at `agent/commands/mixin_base.py` L39 and
  `agent/repl_input_loop.py` L111 (plan Verification Evidence). `session_id` is always a
  positive integer there (plan Assumption), so the recorded uid is `str(ctx.session.session_id)`
  with no fallback; the transport's `sha256(auth_token)` fallback branch (http_transport
  L194-197) is unreachable on the agent path and out of scope (plan Risk mitigation).
- `ctx.workflow.current_task_id` is set at the same turn-entry point (adapter L292);
  `None` means no task context and recording is skipped.

## Design decisions

- Record inside `_recorded_call` (committed choke point), not in the DAG planner or the
  adapter: every call already funnels through it (planner, batch, group, single), it sees
  `ctx` and the terminal outcome, and BaseException (e.g. `asyncio.CancelledError`) already
  propagates through it unchanged (L65-95 docstring), which is exactly the crash case REQ-004
  requires to leave the row `pending`.
- Key re-derived via `shared.http_transport.derive_idempotency_key("call_tool", pc.name,
  pc.args, str(ctx.session.session_id))` — the same function the transport layer itself uses
  (L62, called at L197); transport is NOT modified (plan Constraint).
- Recorder accessed through the `ToolCallRecorder` Protocol field on `WorkflowState`
  (row 02); `tool_runner` gains no new injected parameter and no direct `StateStore` import
  (import-layer contract: `agent -> shared`, no cross-agent state ownership).
- `retry_class` comes from `shared.mcp_dedup.retry_class(tool_name)`, the owner module for
  the REQ-006 classification (`config/mcp_dedup.toml [retry_class]`; unknown tools default
  `non_retryable`, fail-safe unreplayable).
- Recorder call failures are caught (`BLE001`, noqa-justified per the existing precedent at
  `_recorded_call` L83) and logged at warning level — tool execution must not break because
  state recording broke (REQ-007).

## Alternatives considered

- Adapter-level wrap around the turn loop: rejected — cannot observe per-call outcomes
  inside the DAG execution, and would duplicate the call loop.
- ContextVar-injected recorder (the wiped-WIP design, plan UNK-05): rejected — the committed
  `execute_one_tool_call(ctx, pc, guard)` already receives `ctx`, so a dataclass field is
  the narrower mechanism with no implicit ambient state.
- Writing rows from `shared.http_transport` or `shared.mcp_dedup`: rejected — the agent-side
  `tool_call_state` table (workflow.sqlite) and the dispatcher-side `tool_call_state` table
  (mcp_dedup.sqlite, `shared/mcp_dedup.py`) are separate stores with separate schemas
  (plan Verification Evidence); the producer belongs on the agent side.

## Implementation
### Target file

`scripts/agent/tool_runner.py`

### Procedure

1. Extend the existing TYPE_CHECKING import `from agent.context import AgentContext` (L56)
   with `ToolCallRecorder` (typing-only; the Protocol is defined by row 02 in
   `agent/context.py`).
2. Add runtime imports `from shared.http_transport import derive_idempotency_key` and
   `from shared.mcp_dedup import retry_class` (agent→shared, allowed by `.importlinter`;
   matches the file's existing `from shared... import ...` style).
3. Add `_state_key(ctx, pc) -> str` (new): return
   `derive_idempotency_key("call_tool", pc.name, pc.args, str(ctx.session.session_id))`
   (plan D3; no uid fallback needed on the agent path — see Assumptions).
4. Add `_record_pending_state(ctx, pc) -> str | None` (new): resolve
   `recorder = ctx.workflow.tool_call_recorder` and `task_id = ctx.workflow.current_task_id`;
   if either is `None`, return `None`; else compute `key = _state_key(ctx, pc)`, call
   `recorder.record_tool_call(task_id, key, pc.name, retry_class(pc.name))` wrapped in
   `except Exception` (noqa BLE001) → `logger.warning`, and return `key` (or `None` if the
   record failed).
5. Add `_finalize_state(ctx, state_key: str | None, state: str) -> None` (new): if
   `state_key` is `None`, return; resolve the recorder; call
   `recorder.finalize_tool_call(state_key, state)` (real facade signature: no `task_id`
   parameter) wrapped in the same guarded `except Exception` → `logger.warning`.
6. In `_recorded_call` (no signature change): before `result = await
   execute_one_tool_call(...)`, call `state_key = _record_pending_state(ctx, pc)` (pending
   written before dispatch, plan D1); in the captured `except Exception` branch call
   `_finalize_state(ctx, state_key, "failed")` before returning the error row; after the
   normal return path call `_finalize_state(ctx, state_key, "completed")`. BaseException
   must skip finalize entirely (propagates as today, leaving the row `pending`, REQ-004).
   `execute_one_tool_call` itself is not touched.

### Method

Inline edits to one function (`_recorded_call`) plus three new module-level private helpers;
no new class, no signature changes to public functions, no config changes.

### Details

- Recorder lookup happens inside the new helpers (`ctx.workflow.tool_call_recorder`); a
  `None` recorder is a no-op, which keeps all existing unit tests passing without rewiring
  (they do not set the field).
- The pending write must happen before dispatch, not before approval: a denied call has no
  dispatch to dedup against and stays unrecorded (matches consumer semantics — only executed
  calls matter to `build_turn_control_message`).
- `_finalize_state` maps captured execution failures to `failed` and normal result rows
  (including `is_error=True` rows — the call executed and produced its result) to
  `completed` (plan D1); the real `StateStore` facade exposes no `mark_tool_call_interrupted`
  method, and the consumer's `classify_stale_pending` owns the `interrupted` transition.
- The existing `_idempotency_key` (L123) — the audit-only composite key
  `{workflow_id}:{task_id}:{turn_id}:{call_id}` passed to `audit_tool_exec` as
  `idempotency_key=` — remains exactly as-is (REQ-009): audit key and state-row key are
  separate concerns (plan UNK-01).
- Vulture baseline for this file is 0 findings; bandit baseline 0 high/medium; keep the two
  new `except Exception` handlers noqa-BLE001-justified with a one-line comment citing
  REQ-007 (recording failure must not break execution).

## Compatibility considerations

- Existing callers unchanged: `_recorded_call` is called only from `tool_runner.py` L112 and
  L118 (and the DAG batch paths that funnel through them); `execute_one_tool_call` (L190),
  `execute_all_tool_calls` (L400), `ToolLoopGuard`, `ToolCallStopReason`, `PreparedToolCall`
  untouched.
- `tests/agent/test_tool_runner.py` and `tests/agent/test_tool_approval_preflight.py` call
  `execute_one_tool_call`/`execute_all_tool_calls` directly with un-wired `ctx.workflow`
  (`tool_call_recorder=None`): behavior unchanged (silent skip), 3851-test `tests/agent`
  baseline (measured 2026-11-01) preserved.
- Consumer side already merged (`build_turn_control_message`, `classify_stale_pending` call
  at `workflow_engine.py` L128): no consumer edits in scope.

## Security considerations

- Keys are plain (unsalted) SHA-256 over `method \n tool_name \n canonical-JSON(args) \n uid`
  (`derive_idempotency_key`, `shared/http_transport.py` L62): no tool arguments or session ids
  are written into the table, only the hash.
- Recorder failure logging must log the exception type/message only, never tool arguments
  (the args may contain sensitive content).

## Rollback considerations

- Revert the single file (`git checkout -- scripts/agent/tool_runner.py`) is safe at any
  time: with the row-02 field present but unwired, the helpers short-circuit. The reverse
  order is not safe: row 01 reads `ctx.workflow.tool_call_recorder`, so row 02 must be
  implemented BEFORE row 01 (AttributeError otherwise); row 03 wires the value. Execution
  order for this batch: 02 → 01 → 03.

## Validation plan

- Targeted: `uv run pytest tests/agent/test_tool_runner.py tests/agent/test_tool_approval_preflight.py -x -q`.
- New tests land in row 04 (`tests/agent/test_tool_runner.py`): pending-before-dispatch,
  completed/failed finalize, exception-in-recorder non-fatal, BaseException leaves pending,
  un-wired-recorder no-op.
- Full sequence per `rules/toolchain.md`: `uv run ruff format scripts/`, `uv run ruff check
  scripts/`, `uv run mypy --no-namespace-packages scripts/ tests/eventbus`,
  `PYTHONPATH=scripts uv run lint-imports`, `uv run bandit -r scripts/ -c pyproject.toml
  -ll`, full suite `uv run coverage run -m pytest tests/` + `uv run coverage xml` +
  `uv run diff-cover coverage.xml --compare-branch=master --fail-under=90`; diff-cover
  gate ≥90% on the new lines.
- E2E (toolexec001 Phase 6 completion): crash mid-call → row stays `pending` → next turn
  `build_turn_control_message` reports it → replay path consumes the key.

## Completion criteria

- All REQ-001..REQ-004, REQ-006, REQ-007, REQ-009 acceptance criteria listed in the plan row 1 pass.
- Lint/type/security gates clean with no new suppressions beyond the two justified BLE001
  noqa comments.
- All 3851 tests collected under `tests/agent/` (measured 2026-11-01) still pass unmodified.

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
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 20261101-121424 | 20261101-121424 | 3 helpers + _recorded_call wiring; TYPE_CHECKING Protocol import omitted (not needed with future-annotations, avoids F401) |
| 2 | Add or update tests per Validation plan | Completed | — | — | N/A for this row: new tests land in row 04 |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20261101-125522 | 20261101-125522 | Full suite 10864 passed/8 skipped; diff-cover 100% (initial 75% run predated row-04 tests covering helper failure branches) |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Completed | 20261101-125522 | 20261101-125522 | N/A for this row: doc update lands in row 06 |

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