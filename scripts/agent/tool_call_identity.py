"""scripts/agent/tool_call_identity.py — call identity, side-effect flag, and retry-class classification.

The decisions that name a call and classify it live here so tool_runner keeps execution
orchestration only (ADR-018 draft, python-refactoring Path C). Private helpers with no
callers outside tool_runner.
"""

from __future__ import annotations

from shared.runtime_tool_registry import RuntimeToolRegistry
from shared.tool_constants import ALL_SIDE_EFFECTING_TOOLS
from shared.tool_metadata import retry_policy_is_retryable

from agent.tool_preparation import PreparedToolCall


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


def _classify_retry_class(tool_name: str, registry: RuntimeToolRegistry | None) -> str:
    """Declared retry_policy decides the dedup retry class; fail-safe non_retryable."""
    try:
        declared = registry.get(tool_name).retry_policy if registry else None
    except KeyError:
        declared = None
    return "retryable" if retry_policy_is_retryable(declared) else "non_retryable"
