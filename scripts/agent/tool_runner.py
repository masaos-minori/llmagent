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
from shared.tool_executor import ToolExecutor
from shared.tool_executor_helpers import tool_hash_key
from shared.tool_spec import ToolSpec
from shared.transport_dto import ToolCallResult

from agent.tool_audit import audit_tool_exec
from agent.tool_enums import OperationType, ToolCallStopReason
from agent.tool_exceptions import ToolExecutorUnavailableError
from agent.tool_output import emit_tool_call, emit_tool_result
from agent.tool_policy import (
    PolicyViolationError,
    check_preflight,
    classify_operation_type,
)
from agent.tool_preparation import PreparedToolCall, prepare_tool_calls
from agent.tool_result_formatter import (
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
) -> tuple[str, str, dict, str, bool, str]:
    """Execute one call and record its result in *collected* the moment it exists."""
    result = await execute_one_tool_call(ctx, pc, guard)
    collected[pc.call_id] = result
    return result


async def _run_group_calls(
    group: list[PreparedToolCall],
    serialize: bool,
    ctx: AgentContext,
    guard: ToolLoopGuard,
    collected: dict[str, tuple],
) -> list[Any]:
    """Execute one group of tool calls, sequentially when serialize=True, gathered otherwise.

    A sequential group ends early once the guard's empty-result scan trips.
    """
    if serialize:
        results: list[Any] = []
        for pc in group:
            results.append(await _recorded_call(ctx, pc, guard, collected))
            if guard.scan_empty_result_repeat():
                break
        return results
    return list(
        await asyncio.gather(
            *(_recorded_call(ctx, pc, guard, collected) for pc in group)
        )
    )


def _idempotency_key(ctx: AgentContext, pc: PreparedToolCall) -> str:
    """Derive a stable, retry-invariant idempotency key for this Tool Call.

    Composition: {workflow_id}:{task_id}:{turn_id}:{call_id}
    """
    workflow_id = ctx.workflow.workflow_id or ""
    task_id = ctx.workflow.current_task_id or ""
    turn_id = ctx.turn.current_turn_id or ""
    return f"{workflow_id}:{task_id}:{turn_id}:{pc.call_id}"


async def _execute_prepared_call(
    ctx: AgentContext,
    tools: ToolExecutor,
    name: str,
    args: dict[str, Any],
) -> ToolCallResult:
    """Execute one call through the gateway, or through *tools* when it is absent.

    Gateway-bypass safety justification:
    When ctx.services_required.gateway is None the call runs through *tools*
    instead of the gateway. Policy enforcement is not lost: every non-READ
    operation still passes check_preflight() before execution, and a tool name
    that is not in the RuntimeToolRegistry raises ValueError in
    ToolRouteResolver.resolve(), so an unregistered tool cannot execute.
    NOTE: In production, factory.py:652 creates RepositoryGateway unconditionally
    during AppServices construction, so this branch should never execute.
    """
    gateway = ctx.services_required.gateway
    if gateway is not None:
        return await gateway.execute(ctx, name, args)
    # Preflight check when gateway is None for non-READ operations
    # NOTE: strict_mode behavior — both strict_mode=True and strict_mode=False
    # always raise ValueError on an unresolved tool; the difference is in
    # error-message wording only. See ToolRouteResolver.__init__ docstring.
    op = classify_operation_type(name, ctx.services_required.runtime_tools)
    if op != OperationType.READ:
        try:
            check_preflight(ctx.cfg, name, args)
        except PolicyViolationError as exc:
            logger.warning("tool_runner.policy_denied tool=%r reason=%s", name, exc)
            raise  # Re-raise to prevent unauthorized execution
    return await tools.execute(name, args)


def _record_transport_failure(
    ctx: AgentContext, name: str, result: ToolCallResult
) -> None:
    """Persist a transport-level failure into diagnostics, when diagnostics are wired."""
    if (
        not result.is_error
        or result.error_type != "transport"
        or ctx.diagnostics is None
    ):
        return
    ctx.diagnostics.save_transport_failure(
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
) -> tuple[str, str, dict, str, bool, str]:
    """Execute and truncate one already-prepared tool call.

    A non-error result is recorded on *guard* here, as it is produced and before
    truncation, so empty-result counts are visible while the rest of the batch runs.

    Returns (tc_id, name, args, full_text, is_error, llm_text).
    Raises ToolExecutorUnavailableError when ctx.services_required.tools is None.
    Argument parsing and validation already happened in the preparation phase
    (agent.tool_preparation.prepare_tool_calls) before this function is ever called.
    """
    tools = ctx.services_required.tools
    if tools is None:
        raise ToolExecutorUnavailableError(
            "Tool executor is not available (ctx.services_required.tools is None)"
        )
    name = pc.name
    args = pc.args

    idempotency_key = _idempotency_key(ctx, pc)
    result = await _execute_prepared_call(ctx, tools, name, args)
    text, is_error, x_request_id = result.output, result.is_error, result.request_id
    audit_tool_exec(
        ctx,
        name,
        args,
        is_error,
        x_request_id,
        result.error_type,
        source=result.source,
        idempotency_key=idempotency_key,
    )

    _record_transport_failure(ctx, name, result)
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
                _run_group_calls(pcs, group.sequential, ctx, guard, collected)
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
    results = await _run_plan_batches(ctx, plan, pc_by_id, guard, collected)
    results.sort(key=lambda r: call_order.get(r[0], 0))

    elapsed_ms = (time.perf_counter() - t0) * 1000
    _record_round_serialization_events(ctx, serialization_events, round_id, elapsed_ms)
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
    answered when the round ends, by a real result or a synthesized row, even
    when the round raises; the exception then propagates unchanged.

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
            )
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
