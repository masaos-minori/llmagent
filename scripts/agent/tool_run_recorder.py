"""scripts/agent/tool_run_recorder.py — round-level serialization and execution recording.

Recording layer for the single DAG execution path in agent/tool_runner.py. This module
owns:
  _serialization_stats counters and get_serialization_stats() (read by commands/cmd_mcp.py)
  _dag_bucket_label / _log_dag_buckets: debug-only scheduling bucket labels
  _record_serialization_stats: folds one round's events into the counters
  _record_round_serialization_events: ctx.stats entries plus the diagnostics write
  _scheduling_mode and _record_round_exec: the round record /mcp stats reads back

Extracted from tool_runner.py so tool_runner keeps single call dispatch, DAG/serial
ordering, and result collection only. No scheduling decision is made here: every value
recorded here is produced by agent/tool_scheduler.py's ExecutionPlan.

Dependency direction: tool_run_recorder -> tool_audit, tool_preparation, tool_scheduler
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any

from shared.json_utils import now_iso_raw
from shared.tool_spec import ToolSpec

from agent.tool_audit import write_round_exec
from agent.tool_preparation import PreparedToolCall
from agent.tool_scheduler import ScheduledBatch, SerializationEvent

if TYPE_CHECKING:
    from agent.context import AgentContext

logger = logging.getLogger(__name__)


_serialization_stats: dict[str, int] = {
    "total_events": 0,
    "total_tools_affected": 0,
    "tools_affected_last_round": 0,
}


def get_serialization_stats() -> dict[str, int]:
    """Return current serialization statistics."""
    return dict(_serialization_stats)


def _record_serialization_stats(
    serialization_events: tuple[SerializationEvent, ...],
) -> None:
    """Fold one round's serialization events into the module-level counters."""
    if not serialization_events:
        _serialization_stats["tools_affected_last_round"] = 0
        return
    total_affected = sum(e.tools_count for e in serialization_events)
    _serialization_stats["total_events"] += len(serialization_events)
    _serialization_stats["total_tools_affected"] += total_affected
    _serialization_stats["tools_affected_last_round"] = total_affected
    logger.info(
        "Serialization impact: %d tools grouped serially (normally would run in parallel)",
        total_affected,
    )


def _dag_bucket_label(spec: ToolSpec) -> str:
    """Name the scheduling bucket a call's ToolSpec places it in (debug output only)."""
    if spec.requires_serial:
        return "serial_barrier"
    if spec.resource_scopes or spec.is_write:
        scopes = spec.resource_scopes or ("global:write",)
        return f"resource_scope:{','.join(scopes)}"
    return "parallel"


def _log_dag_buckets(approved_calls: list[PreparedToolCall]) -> None:
    """Label every approved call's scheduling bucket when DEBUG logging is enabled."""
    if not logger.isEnabledFor(logging.DEBUG):
        return
    for pc in approved_calls:
        logger.debug("DAG_BUCKET: %s → %s", pc.name, _dag_bucket_label(pc.spec))


def _record_round_serialization_events(
    ctx: AgentContext,
    serialization_events: tuple[SerializationEvent, ...],
    round_id: str,
    elapsed_ms: float,
) -> None:
    """Append one stats entry per serialization event and mirror it into diagnostics."""
    ts = now_iso_raw()
    for se in serialization_events:
        round_event: dict[str, Any] = {
            "trigger_tool": se.trigger_tool,
            "affected_tools": [],
            "affected_count": se.tools_count,
            "mode": "serial",
            "serial_reason": se.reason,
            "resource_scopes": list(se.resource_scopes),
            "is_write": se.is_write,
            "requires_serial": se.requires_serial,
            "scheduling_decision": se.scheduling_decision,
            "elapsed_ms": round(elapsed_ms, 1),
            "timestamp": ts,
        }
        ctx.stats.stat_serialization_events.append(round_event)
        ctx.stats.stat_serialization_total_overhead_ms += elapsed_ms
        if ctx.diagnostics is not None:
            ctx.diagnostics.save_serialization_event(
                session_id=ctx.session.session_id,
                round_id=round_id,
                trigger_tool=se.trigger_tool,
                affected_count=se.tools_count,
                mode="serial",
                elapsed_ms=elapsed_ms,
                reason=se.reason,
            )


def _scheduling_mode(batches: tuple[ScheduledBatch, ...]) -> str:
    """Return the round's mode label: concurrent when any batch holds several groups."""
    if any(len(batch.groups) > 1 for batch in batches):
        return "dag_concurrent"
    return "dag_sequential"


def _record_round_exec(
    ctx: AgentContext,
    approved_calls: list[PreparedToolCall],
    serialization_events: tuple[SerializationEvent, ...],
    round_id: str,
    elapsed_ms: float,
    batches: tuple[ScheduledBatch, ...],
) -> None:
    """Write the round-level execution record that /mcp stats reads back."""
    first_event = next(iter(serialization_events), None)
    write_round_exec(
        ctx,
        round_id=round_id,
        tool_count=len(approved_calls),
        mode="parallel",
        has_side_effect=first_event is not None,
        trigger_tool=first_event.trigger_tool if first_event else None,
        elapsed_ms=elapsed_ms,
        affected_tools=[pc.name for pc in approved_calls],
        serial_reason=first_event.reason if first_event else None,
        scheduling_mode=_scheduling_mode(batches),
    )
