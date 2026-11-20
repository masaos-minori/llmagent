"""scripts/agent/tool_runner.py

Tool execution orchestration: single call dispatch, DAG/serial ordering,
result collection and history injection.

Round-level recording (serialization stats, serialization event records, DAG bucket
labels, the round execution record) lives in agent/tool_run_recorder.py.

Public entry point: execute_all_tool_calls().
"""

from __future__ import annotations

import asyncio
import logging
import time
from typing import TYPE_CHECKING, Any
from uuid import uuid4

from shared.json_utils import (
    dumps as _json_dumps,
)
from shared.tool_constants import ALL_SIDE_EFFECTING_TOOLS, RETRYABLE_TOOLS
from shared.tool_executor import ToolExecutor
from shared.tool_executor_helpers import tool_hash_key
from shared.tool_spec import ToolSpec
from shared.transport_dto import ToolCallResult

from agent.tool_audit import audit_tool_exec
from agent.tool_enums import OperationType, ToolCallStopReason
from agent.tool_exceptions import (
    IntentRecordUnavailableError,
    ToolExecutorUnavailableError,
)
from agent.tool_output import emit_tool_call, emit_tool_result
from agent.tool_policy import (
    PolicyViolationError,
    check_preflight,
    classify_operation_type,
)
from agent.tool_preparation import PreparedToolCall, prepare_tool_calls
from agent.tool_result_formatter import (
    build_execution_failure_text,
    mask_args,
    turn_limit_hint,
)
from agent.tool_round_completion import RoundState, complete_round
from agent.tool_run_recorder import (
    _log_dag_buckets,
    _record_round_exec,
    _record_round_serialization_events,
    _record_serialization_stats,
)
from agent.tool_scheduler import (
    ExecutionPlan,
    build_execution_groups,
)

if TYPE_CHECKING:
    from agent.context import AgentContext
    from agent.tool_loop_guard import ToolLoopGuard

logger = logging.getLogger(__name__)

# Display threshold: results longer than this are shown as line/char counts
_TOOL_RESULT_MAX_CHARS = 500


async def _recorded_call(
    ctx: AgentContext,
    pc: PreparedToolCall,
    guard: ToolLoopGuard,
    collected: dict[str, tuple],
    dispatched: set[str],
) -> tuple[str, str, dict, str, bool, str]:
    """Execute one call and record its result in *collected* the moment it exists.

    A call that raises during execution is converted into the same six-field
    error row the preparation phase produces
    (scripts/agent/tool_preparation.py:37), so a sibling in the same group
    still completes and the round stays total (plans/20261023-004538_plan.md).
    mcpdl001 fail-closed denials (IntentRecordUnavailableError,
    AuditUnavailableError) land in the same conversion (REQ-007, AC-5); only
    *this* call's Exception is converted — BaseException (e.g.
    asyncio.CancelledError) propagates (AC-5).

    Single writer of the agent-side tool_call_state rows (mcpdl001 REQ-003):
    keyed on the logical call id, the row walks the intent vocabulary
    pending → dispatch_starting → dispatched → response_received →
    completed/failed. A post-send failure (result dispatch_stage "sent")
    leaves the row at a dispatch-stage state for classify_stale_pending —
    never finalized here, never replayed (AC-6); a propagating BaseException
    leaves the row wherever dispatch stopped.
    """
    state_key: str | None = None
    try:
        state_key = _record_pending_state(ctx, pc)
        dispatched.add(pc.call_id)
        _finalize_state(ctx, state_key, "dispatch_starting", pc.name)
        _finalize_state(ctx, state_key, "dispatched", pc.name)
        result = await execute_one_tool_call(ctx, pc, guard, state_key=state_key)
        collected[pc.call_id] = result
        dispatched.discard(pc.call_id)
        return result
    except Exception as exc:  # noqa: BLE001 — per-call boundary; a raising call must not abort siblings; CancelledError still propagates (AC-5)
        logger.exception(
            "tool execution failed tool=%r call_id=%s", pc.name, pc.call_id
        )
        failure_text = build_execution_failure_text(exc)
        llm_text = _truncate_for_llm(
            failure_text, ctx.cfg.tool.tool_result_max_llm_chars
        )
        error_row = (pc.call_id, pc.name, pc.args, failure_text, True, llm_text)
        collected[pc.call_id] = error_row
        dispatched.discard(pc.call_id)
        try:
            _finalize_state(ctx, state_key, "failed", pc.name)
        except Exception as fin_exc:  # noqa: BLE001 — a failed finalize must not mask the error-row conversion
            logger.error(
                "tool-call state failed-finalize also failed tool=%r: %s",
                pc.name,
                fin_exc,
            )
        return error_row


async def _run_group_calls(
    group: list[PreparedToolCall],
    serialize: bool,
    ctx: AgentContext,
    guard: ToolLoopGuard,
    collected: dict[str, tuple],
    dispatched: set[str],
) -> list[Any]:
    """Execute one group of tool calls, sequentially when serialize=True, gathered otherwise.

    A sequential group ends early once the guard's empty-result scan trips.
    """
    if serialize:
        results: list[Any] = []
        for pc in group:
            results.append(await _recorded_call(ctx, pc, guard, collected, dispatched))
            if guard.scan_empty_result_repeat():
                break
        return results
    return list(
        await asyncio.gather(
            *(_recorded_call(ctx, pc, guard, collected, dispatched) for pc in group)
        )
    )


def _logical_call_id(pc: PreparedToolCall) -> str:
    """The call's logical call id from the preparation-phase execution context.

    Sole key for the tool_call_state row and the audit idempotency_key field
    (mcpdl001 REQ-003): the same uuid7 the transport sends as
    X-Idempotency-Key. Nothing is derived — the old key derivations collided.
    """
    return pc.context.call_id if pc.context else ""


def _side_effecting(tool_name: str) -> bool:
    """True when the tool is in shared.tool_constants.ALL_SIDE_EFFECTING_TOOLS."""
    return tool_name in ALL_SIDE_EFFECTING_TOOLS


def _classify_retry_class(tool_name: str) -> str:
    """Return the retry classification for a tool using the Agent's canonical set.

    Single source of truth is shared.tool_constants.RETRYABLE_TOOLS (ADR-008):
    dispatch-capable tools are 'retryable'; every other tool — including
    unknown ones — is 'non_retryable' (fail-safe). Resolving locally (rather
    than importing shared.mcp_dedup) keeps the Agent from reading the
    dispatcher's config/mcp_dedup.toml.
    """
    return "retryable" if tool_name in RETRYABLE_TOOLS else "non_retryable"


def _record_pending_state(ctx: AgentContext, pc: PreparedToolCall) -> str | None:
    """Write the pending tool_call_state row before dispatch.

    Returns the state key (the logical call id, REQ-003), else None for
    read-only calls on any unwired/failed path.

    Fail-closed for side-effecting calls (REQ-005/REQ-007): a missing logical
    call id, unwired recorder/task, or a recorder write failure raises
    IntentRecordUnavailableError — no dispatch without the durable intent row.
    Read-only calls keep the logged best-effort path.
    """
    key = _logical_call_id(pc)
    side_effecting = _side_effecting(pc.name)
    recorder = ctx.workflow.tool_call_recorder
    task_id = ctx.workflow.current_task_id
    if not key or recorder is None or task_id is None:
        if side_effecting:
            raise IntentRecordUnavailableError(
                f"cannot record tool_call_state for side-effecting tool {pc.name!r}: "
                f"{'no logical call id' if not key else 'recorder/task context unwired'}"
            )
        return None
    try:
        recorder.record_tool_call(task_id, key, pc.name, _classify_retry_class(pc.name))
    except Exception as exc:  # noqa: BLE001 — classification decides fail-closed vs best-effort
        if side_effecting:
            raise IntentRecordUnavailableError(
                f"tool_call_state record failed for side-effecting tool {pc.name!r}"
            ) from exc
        logger.warning("tool-call state record failed tool=%r: %s", pc.name, exc)
        return None
    return key


def _finalize_state(
    ctx: AgentContext, state_key: str | None, state: str, tool_name: str = ""
) -> None:
    """Move the tool_call_state row to another state in the intent vocabulary.

    No-op when no pending row was written (state_key None) or the recorder is
    unwired. BaseException paths never reach a terminal transition: the row
    stays at whatever dispatch-stage state it reached.

    Fail-closed for side-effecting calls (REQ-007): a recorder write failure
    raises IntentRecordUnavailableError instead of the old logged warning;
    read-only calls keep the best-effort warning.
    """
    if state_key is None:
        return
    recorder = ctx.workflow.tool_call_recorder
    if recorder is None:
        return
    try:
        recorder.finalize_tool_call(state_key, state)
    except Exception as exc:  # noqa: BLE001 — classification decides fail-closed vs best-effort
        if _side_effecting(tool_name):
            raise IntentRecordUnavailableError(
                f"tool_call_state {state!r} finalize failed for side-effecting tool {tool_name!r}"
            ) from exc
        logger.warning("tool-call state finalize failed key=%s: %s", state_key, exc)


def _grant_denied_result(name: str) -> ToolCallResult:
    """Deny shape for a side-effecting call that reaches execution ungranted.

    Same error_type as the gateway's grant denial so audit and retry
    classification treat both denials identically (mcpdl001 REQ-006).
    """
    return ToolCallResult(
        output=f"Grant denied: no approval grant (tool={name})",
        is_error=True,
        request_id="",
        server_key="",
        error_type="denied",
    )


async def _execute_prepared_call(
    ctx: AgentContext,
    tools: ToolExecutor,
    pc: PreparedToolCall,
) -> ToolCallResult:
    """Execute one prepared call through the gateway, or through *tools* when it is absent.

    Gateway-bypass safety justification: with gateway=None the call runs
    through *tools*; policy is not lost — every non-READ operation first needs
    the ApprovalGrant its upstream approval issued (mcpdl001 REQ-006), a
    non-READ call without a grant or logical call id is denied before the
    check_preflight fallback, and a tool name absent from the
    RuntimeToolRegistry yields a `routing` ToolCallResult from
    ToolExecutor.execute() and cannot execute. NOTE: in
    production, factory.py creates RepositoryGateway unconditionally during
    AppServices construction, so this branch should never execute.
    """
    name = pc.name
    args = pc.args
    gateway = ctx.services_required.gateway
    # Classify once before execution: non-READ (incl. UNKNOWN) sets the
    # per-attempt side-effect flag before running, so a failed side-effect
    # call also blocks retry (the adapter records attempts, not successes).
    op = classify_operation_type(name, ctx.services_required.runtime_tools)
    if op != OperationType.READ:
        ctx.turn.attempt_side_effect = True
        if pc.grant is None or pc.context is None:
            # AC-3/AC-4: an ungranted or id-less side-effecting call never
            # reaches any executor, gatewayed or not.
            logger.warning("tool_runner.grant_denied tool=%r", name)
            return _grant_denied_result(name)
    if gateway is not None:
        return await gateway.execute(ctx, name, args, grant=pc.grant)
    # Preflight check when gateway is None for non-READ operations
    try:
        check_preflight(ctx.cfg, name, args, ctx.services_required.runtime_tools)
    except PolicyViolationError as exc:
        logger.warning("tool_runner.policy_denied tool=%r reason=%s", name, exc)
        raise  # Re-raise to prevent unauthorized execution
    return await tools.execute(name, args, context=pc.context)


async def _record_transport_failure(
    ctx: AgentContext, name: str, result: ToolCallResult
) -> None:
    """Persist a transport-level failure to diagnostics off the loop, when wired."""
    if (
        not result.is_error
        or result.error_type != "transport"
        or ctx.diagnostics is None
    ):
        return
    await asyncio.to_thread(
        ctx.diagnostics.save_transport_failure,
        session_id=getattr(ctx.session, "session_id", None),
        tool_name=name,
        server_key=result.server_key or "",
        error_msg=result.output[:500],
    )


def _truncate_for_llm(text: str, limit: int) -> str:
    """Cap a tool result at *limit* chars for the copy handed back to the LLM."""
    if len(text) <= limit:
        return text
    return text[:limit] + "\n... (truncated)"


async def execute_one_tool_call(
    ctx: AgentContext,
    pc: PreparedToolCall,
    guard: ToolLoopGuard,
    *,
    state_key: str | None = None,
) -> tuple[str, str, dict, str, bool, str]:
    """Execute and truncate one already-prepared tool call.

    A non-error result is recorded on *guard* when produced, before
    truncation, so empty-result counts stay visible while the batch runs.

    When *state_key* is given (the key from _record_pending_state), also
    writes the result-driven intent transitions: `response_received` on a
    response-bearing result, then the terminal `completed`/`failed`. A
    post-send failure (dispatch_stage "sent" with an error result) leaves the
    row at `dispatched` for classify_stale_pending — never finalized here
    (AC-6).

    Returns (tc_id, name, args, full_text, is_error, llm_text).
    Raises ToolExecutorUnavailableError when ctx.services_required.tools is None.
    Argument parsing and validation already happened in prepare_tool_calls().
    """
    tools = ctx.services_required.tools
    if tools is None:
        raise ToolExecutorUnavailableError(
            "Tool executor is not available (ctx.services_required.tools is None)"
        )
    name = pc.name
    args = pc.args

    result = await _execute_prepared_call(ctx, tools, pc)
    text, is_error, x_request_id = result.output, result.is_error, result.request_id
    audit_tool_exec(
        ctx,
        name,
        args,
        is_error,
        x_request_id,
        result.error_type,
        source=result.source,
        idempotency_key=_logical_call_id(pc),
    )
    if state_key is not None:
        if result.dispatch_stage == "response":
            _finalize_state(ctx, state_key, "response_received", name)
        if not (result.dispatch_stage == "sent" and is_error):
            _finalize_state(ctx, state_key, "failed" if is_error else "completed", name)

    await _record_transport_failure(ctx, name, result)
    guard.observe_availability(result)
    if not is_error:
        guard.record_tool_result(name, text)

    llm_text = _truncate_for_llm(text, ctx.cfg.tool.tool_result_max_llm_chars)

    return pc.call_id, name, args, text, is_error, llm_text


async def _collect_tool_result_msgs(
    ctx: AgentContext,
    results: list[tuple[str, str, dict, str, bool, str]],
    turn: int,
    out_failed_keys: set[str] | None,
) -> list[tuple[str, str | None, list[dict] | None, str | None]]:
    """Log, display, persist, and append tool results to history.

    Returns tool_msgs for session.save_many(). Applies per-turn char limit.
    Raises sqlite3.Error when tool result persistence fails.
    """
    tool_msgs: list[tuple[str, str | None, list[dict] | None, str | None]] = []
    turn_chars = 0
    for tc_id, name, args, text, is_error, llm_text in results:
        _update_stats_for_result(ctx, name, args, is_error, out_failed_keys)
        masked = mask_args(args, ctx.cfg.tool.masked_fields)
        _log_and_emit_tool_call(turn + 1, name, masked)
        _emit_tool_result(text, name)

        llm_text = _apply_turn_char_limit(
            llm_text,
            turn_chars,
            limit=ctx.cfg.tool.tool_results_turn_max_chars,
        )
        turn_chars += len(llm_text)
        await ctx.conv.append_message(
            {"role": "tool", "tool_call_id": tc_id, "content": llm_text}
        )
        tool_msgs.append(("tool", llm_text, None, tc_id))
    return tool_msgs


def _update_stats_for_result(
    ctx: AgentContext,
    name: str,
    args: dict,
    is_error: bool,
    out_failed_keys: set[str] | None,
) -> None:
    """Update stats and failed keys for a single tool result."""
    ctx.stats.stat_tool_calls += 1
    if is_error:
        ctx.stats.stat_tool_errors += 1
        if out_failed_keys is not None:
            out_failed_keys.add(tool_hash_key(name, args))


def _log_and_emit_tool_call(turn: int, name: str, masked: dict) -> None:
    """Log and emit a tool call event."""
    logger.info("Tool call (turn %s): %s(%s)", turn, name, masked)
    emit_tool_call(name, _json_dumps(masked))


def _emit_tool_result(text: str, name: str) -> None:
    """Emit tool result with truncation display if needed."""
    if len(text) > _TOOL_RESULT_MAX_CHARS:
        n_lines = len(text.splitlines())
        logger.info("Tool result %s (full): %s", name, text)
        emit_tool_result(name, f"{n_lines} lines / {len(text)} chars (truncated)")
    else:
        emit_tool_result(name, text)


def _apply_turn_char_limit(
    llm_text: str,
    turn_chars: int,
    limit: int,
) -> str:
    """Apply per-turn char limit; return hint if exceeded."""
    if limit > 0 and (turn_chars + len(llm_text)) > limit:
        omitted_chars = len(llm_text)
        omitted_lines = len(llm_text.splitlines())
        logger.info(
            "Per-turn tool result limit reached: %s chars > %s; result replaced with hint",
            turn_chars + omitted_chars,
            limit,
        )
        return turn_limit_hint(omitted_chars, omitted_lines, limit)
    return llm_text


async def _run_plan_batches(
    ctx: AgentContext,
    plan: ExecutionPlan,
    pc_by_id: dict[str, PreparedToolCall],
    guard: ToolLoopGuard,
    collected: dict[str, tuple],
    dispatched: set[str],
) -> list[Any]:
    """Run every batch of the plan, flattening group results into one list.

    No further batch is dispatched once the guard's empty-result scan trips.
    """
    results: list[Any] = []
    for batch in plan.batches:
        is_concurrent = len(batch.groups) > 1
        logger.debug(
            "ROUND_EXEC: running %d group(s) %s",
            len(batch.groups),
            "concurrently" if is_concurrent else "sequentially",
        )
        pc_groups = [
            [pc_by_id[spec.call_id] for spec in group.calls] for group in batch.groups
        ]
        batch_results = await asyncio.gather(
            *(
                _run_group_calls(
                    pcs, group.sequential, ctx, guard, collected, dispatched
                )
                for pcs, group in zip(pc_groups, batch.groups)
            )
        )
        results.extend(r for group_res in batch_results for r in group_res)
        if guard.scan_empty_result_repeat():
            break
    return results


async def _execute_with_dag(
    ctx: AgentContext,
    approved_calls: list[PreparedToolCall],
    guard: ToolLoopGuard,
    collected: dict[str, tuple],
    force_serial: bool = False,
    dispatched: set[str] | None = None,
) -> list[Any]:
    """Run approved calls through the single DAG execution plan.

    Delegates to build_execution_groups(), the sole scheduling engine — passing
    force_serial through as a planner input (rather than selecting between two
    execution engines) is what lets ctx.cfg.tool.serial_tool_calls still force
    fully serial execution without a second code path. Scheduling metadata
    comes entirely from each PreparedToolCall.spec (already resolved via
    RuntimeToolRegistry.tool_spec_for_call() during the preparation phase) —
    this function performs no registry lookups of its own.
    """
    call_specs: dict[str, ToolSpec] = {pc.call_id: pc.spec for pc in approved_calls}
    pc_by_id: dict[str, PreparedToolCall] = {pc.call_id: pc for pc in approved_calls}
    if dispatched is None:
        dispatched = set()

    round_id = str(uuid4())
    t0 = time.perf_counter()
    plan: ExecutionPlan = build_execution_groups(
        [pc.original_call for pc in approved_calls],
        call_specs,
        force_serial=force_serial,
    )
    _log_dag_buckets(approved_calls)
    serialization_events = plan.serialization_events
    _record_serialization_stats(serialization_events)

    call_order = {pc.call_id: i for i, pc in enumerate(approved_calls)}
    results = await _run_plan_batches(ctx, plan, pc_by_id, guard, collected, dispatched)
    results.sort(key=lambda r: call_order.get(r[0], 0))

    elapsed_ms = (time.perf_counter() - t0) * 1000
    await _record_round_serialization_events(
        ctx, serialization_events, round_id, elapsed_ms
    )
    _record_round_exec(
        ctx,
        approved_calls,
        serialization_events,
        round_id,
        elapsed_ms,
        plan.batches,
    )
    return results


async def execute_all_tool_calls(
    ctx: AgentContext,
    tool_calls: list[dict],
    turn: int,
    out_failed_keys: set[str] | None = None,
    *,
    guard: ToolLoopGuard,
) -> None:
    """Execute all tool calls then append results in original order.

    *guard* is the per-turn ToolLoopGuard; each executed call records its own
    result on it (see execute_one_tool_call). Every declared tool_call id is
    answered when the round ends, by a real result (success or a captured
    execution-failure row) or a synthesized "not executed" row for a call that
    never ran. A call that raises during execution is converted into that error
    row rather than aborting its siblings; only a BaseException (e.g.
    asyncio.CancelledError) propagates unchanged.

    Always DAG-scheduled via _execute_with_dag() — the single execution path.
    ctx.cfg.tool.serial_tool_calls feeds force_serial into the planner (one
    sequential phase per call) rather than selecting a separate execution
    engine. Every raw tool call is prepared (parsed, resolved against
    RuntimeToolRegistry, and argument-validated) before approval — a call
    that fails preparation never reaches the approval gate, DAG planning, or
    execution. Approval checks are enforced before execution — denied tool
    calls are returned as tool messages with a denial reason.
    """
    if not tool_calls:
        ctx.session.save_many([])
        return

    state = RoundState([tc["id"] for tc in tool_calls if tc.get("id")])

    async def finish(reason: ToolCallStopReason) -> None:
        await complete_round(
            ctx,
            state,
            tool_calls,
            turn,
            out_failed_keys,
            reason,
            _collect_tool_result_msgs,
        )

    try:
        # Fail-closed preparation phase: parse/resolve/validate before approval.
        prepared, state.prep_failures = prepare_tool_calls(ctx, tool_calls)
        approved_calls, state.denied_ids = await _run_approval_gate(ctx, prepared)
        if approved_calls:
            await _execute_with_dag(
                ctx,
                approved_calls,
                guard,
                state.collected,
                force_serial=ctx.cfg.tool.serial_tool_calls,
                dispatched=state.dispatched_ids,
            )
    except asyncio.CancelledError:
        raise
    except BaseException:
        try:
            await finish(ToolCallStopReason.ROUND_NOT_COMPLETED)
        except Exception:  # noqa: BLE001 — completion must never replace the round's own exception
            logger.exception("tool round completion failed")
        raise
    await finish(ToolCallStopReason.GUARD_STOP)


async def _run_approval_gate(
    ctx: AgentContext,
    prepared: list[PreparedToolCall],
) -> tuple[list[PreparedToolCall], list[str]]:
    """Run approval checks and return (approved_calls, denied_ids).

    This is the sole per-tool-call approval gate for the batch: every prepared
    tool call in `prepared` is checked here, exactly once, before any of it
    reaches execution. Calls that pass (`approved_calls`) proceed straight
    to execution — including through `RepositoryGateway` for write/delete/
    API-write tools — without any further approval check performed anywhere
    downstream.
    """
    from agent.tool_approval import run_approval_checks

    return await run_approval_checks(ctx, prepared)
