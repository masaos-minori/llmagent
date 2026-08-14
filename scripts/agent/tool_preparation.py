"""scripts/agent/tool_preparation.py

Fail-closed tool-call preparation phase, run before `_run_approval_gate()` in
`execute_all_tool_calls()` (scripts/agent/tool_runner.py).

For every raw LLM tool call, `prepare_tool_calls()` parses `id`/`function.name`,
decodes `arguments` JSON exactly once, requires the decoded value to be a
`dict`, resolves the tool through `RuntimeToolRegistry` only (no
`ctx.cfg.tool.tool_definitions` fallback), validates the args against the live
`RuntimeTool.input_schema`, and builds a `PreparedToolCall` carrying a per-call
`ToolSpec`. Any failure at any step becomes a synthetic tool-error result
tuple, never a `PreparedToolCall` — closing the silent-acceptance gap where a
tool name absent from the registry but present in a stale
`ctx.cfg.tool.tool_definitions` entry could previously reach execution.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

import orjson
from shared.tool_spec import ToolSpec
from shared.transport_dto import ToolCallResult

from agent.tool_arg_validator import validate_tool_arguments

if TYPE_CHECKING:
    from agent.context import AgentContext

logger = logging.getLogger(__name__)

# Matches execute_one_tool_call()'s return shape: (tc_id, name, args, full_text,
# is_error, llm_text). A prepare-phase failure has no separate "full" vs
# "truncated" text, so both text fields carry the same rejection reason.
_PrepFailure = tuple[str, str, dict, str, bool, str]


@dataclass(frozen=True)
class PreparedToolCall:
    """A raw tool call that has passed preparation and is ready for approval/execution."""

    call_id: str
    name: str
    args: dict[str, Any]
    spec: ToolSpec
    original_call: dict


def _reject(tc_id: str, name: str, args: dict, kind: str, reason: str) -> _PrepFailure:
    """Build the synthetic failure tuple for a rejected tool call.

    Mirrors `_reject_validation()`'s `ToolCallResult` construction
    (scripts/agent/tool_runner.py:92-102), but tags `error_type` with the
    specific failure `kind` (`configuration`, `unknown_tool`, `validation`,
    `schema`, `metadata`) instead of the single `"validation"` literal, and
    returns the flat 6-tuple shape `execute_one_tool_call()` produces rather
    than a `ToolCallResult`.
    """
    result = ToolCallResult(
        output=reason,
        is_error=True,
        request_id="",
        server_key="",
        source="tool_preparation",
        error_type=kind,
    )
    logger.warning(
        "tool_preparation_rejected kind=%s tool=%r reason=%s", kind, name, reason
    )
    return tc_id, name, args, result.output, result.is_error, result.output


def _prepare_one(ctx: AgentContext, tc: dict) -> PreparedToolCall | _PrepFailure:
    """Prepare one raw tool call, returning either a `PreparedToolCall` or a failure tuple."""
    tc_id = tc.get("id")
    func = tc.get("function") or {}
    name = func.get("name")

    if not tc_id:
        return _reject(
            tc_id or "", name or "", {}, "configuration", "tool call is missing an id"
        )
    if not name:
        return _reject(
            tc_id, "", {}, "validation", "tool call is missing a function name"
        )

    args_str = func.get("arguments", "{}")
    try:
        args = orjson.loads(args_str)
    except orjson.JSONDecodeError:
        return _reject(
            tc_id,
            name,
            {},
            "validation",
            f"Invalid JSON in tool arguments for {name!r}: {args_str!r}",
        )

    if not isinstance(args, dict):
        return _reject(
            tc_id,
            name,
            {},
            "validation",
            "arguments must decode to a JSON object",
        )

    registry = ctx.services_required.runtime_tools
    if registry is None:
        return _reject(
            tc_id,
            name,
            args,
            "configuration",
            "RuntimeToolRegistry is not available (ctx.services_required.runtime_tools is None)",
        )

    try:
        runtime_tool = registry.get(name)
    except KeyError:
        return _reject(
            tc_id, name, args, "unknown_tool", f"unregistered tool: {name!r}"
        )

    validation = validate_tool_arguments(
        tool_name=name,
        args=args,
        input_schema=runtime_tool.input_schema,
        allow_extra_fields=runtime_tool.allow_extra_fields,
    )
    if not validation.success:
        return _reject(tc_id, name, args, "schema", validation.reason)

    try:
        spec = registry.tool_spec_for_call(tc_id, name, args)
    except KeyError:
        return _reject(
            tc_id, name, args, "metadata", f"failed to build tool metadata for {name!r}"
        )

    return PreparedToolCall(
        call_id=tc_id, name=name, args=args, spec=spec, original_call=tc
    )


def prepare_tool_calls(
    ctx: AgentContext, tool_calls: list[dict]
) -> tuple[list[PreparedToolCall], list[_PrepFailure]]:
    """Prepare a batch of raw tool calls, in order.

    Returns `(prepared, failures)`: `prepared` holds one `PreparedToolCall` per
    call that passed every preparation step, in original relative order;
    `failures` holds one synthetic failure tuple per call that was rejected at
    any step, also in original relative order. Each failure tuple carries its
    own `tc_id`, so the caller can reinsert it at its original batch index
    without this function tracking indices itself.
    """
    prepared: list[PreparedToolCall] = []
    failures: list[_PrepFailure] = []
    for tc in tool_calls:
        outcome = _prepare_one(ctx, tc)
        if isinstance(outcome, PreparedToolCall):
            prepared.append(outcome)
        else:
            failures.append(outcome)
    return prepared, failures
