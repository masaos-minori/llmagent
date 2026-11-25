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

import hashlib
import json
import logging
import secrets
import time
import uuid
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

import orjson
from shared.tool_spec import ToolSpec
from shared.transport_dto import ToolCallResult, ToolExecutionContext

from agent.tool_arg_validator import validate_tool_arguments

if TYPE_CHECKING:
    from agent.context import AgentContext
    from agent.shared.models import ApprovalGrant

logger = logging.getLogger(__name__)


@dataclass
class ReplayDirective:
    """One-time Agent-managed replay directive for a reissued tool call.

    Built at turn entry from a persisted `interrupted` replayable `tool_call_state`
    row (see `agent.workflow.tool_call_state_ops.reconstruct_replay_directives`) and
    held on `TurnState.replay_directives`, so the LLM never sees the id it carries
    (REQ-002). `original_call_id` is the logical call id of the interrupted call;
    after the mcpdl001 id unification it is also the row's `idempotency_key`.

    `consumed` records one-time consumption within the turn. The dataclass is not
    frozen: `consumed` is the field the matching helper sets, and a frozen dataclass
    cannot carry one-time consumption without a second holder object.
    """

    original_call_id: str
    task_id: str
    tool: str
    args_hash: str
    consumed: bool = False


# Matches execute_one_tool_call()'s return shape: (tc_id, name, args, full_text,
# is_error, llm_text). A prepare-phase failure has no separate "full" vs
# "truncated" text, so both text fields carry the same rejection reason.
_PrepFailure = tuple[str, str, dict, str, bool, str]


_MAX_TOOL_CALL_ID_LEN = 256  # LLM-supplied tool-call ids are short opaque tokens


@dataclass(frozen=True)
class PreparedToolCall:
    """A raw tool call that has passed preparation and is ready for approval/execution."""

    call_id: str
    name: str
    args: dict[str, Any]
    spec: ToolSpec
    original_call: dict
    # Logical-call identity generated once here; None only in legacy fixtures —
    # execution and the gateway deny side-effecting calls without it.
    context: ToolExecutionContext | None = None
    # Approval grant issued by run_approval_checks (mcpdl001 REQ-006): set via
    # dataclasses.replace on every approved non-READ call; None for READ calls
    # and for calls that never reach execution.
    grant: ApprovalGrant | None = None


def _malformed_id_reason(tc_id: str) -> str:
    """Return a rejection reason when an LLM-supplied tool-call id is malformed, else "".

    Rejects over-long ids and ids carrying whitespace or control characters: the
    id keys correlation and audit rows, and REQ-001 requires format validation
    at the preparation boundary.
    """
    if len(tc_id) > _MAX_TOOL_CALL_ID_LEN:
        return f"tool call id exceeds {_MAX_TOOL_CALL_ID_LEN} characters: {tc_id[:64]!r}..."
    if any(ch.isspace() or ord(ch) < 0x20 or ord(ch) == 0x7F for ch in tc_id):
        return f"tool call id contains whitespace or control characters: {tc_id[:64]!r}"
    return ""


def _canonical_args_hash(args: dict[str, Any]) -> str:
    """Hex sha256 over canonical-JSON args (sorted keys, compact separators).

    Same computation as the approval grant's hash, so the gateway can compare
    the grant and the context at the authorization boundary.
    """
    canonical = json.dumps(args, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def _resolve_replay_call_id(
    ctx: AgentContext, tc_id: str, tool: str, args: dict, args_hash: str
) -> str | _PrepFailure:
    """The logical call id for a prepared call: the directive's, or a fresh one.

    Matching is tool name plus canonical argument hash, scoped to the current task
    (REQ-002). A match is consumed here, so one directive serves exactly one call
    (REQ-001). Several matches is fail closed: the helper returns the `ambiguity`
    rejection tuple — a new `kind` value in `_reject`'s free-string vocabulary —
    listing the matching ids, so an ambiguous call never reaches dispatch (REQ-003).
    Keeping the decision here is what limits `_prepare_one` to one added branch.
    """
    matches = [
        d
        for d in ctx.turn.replay_directives
        if d.task_id == ctx.workflow.current_task_id
        and d.tool == tool
        and d.args_hash == args_hash
        and not d.consumed
    ]
    if len(matches) > 1:
        ids = ", ".join(d.original_call_id for d in matches)
        return _reject(
            tc_id,
            tool,
            args,
            "ambiguity",
            f"{len(matches)} replay directives match tool {tool!r} "
            f"(args hash {args_hash}): {ids}",
        )
    if not matches:
        return _logical_call_id()
    directive = matches[0]
    directive.consumed = True
    return directive.original_call_id


def _logical_call_id() -> str:
    """Return the opaque UUIDv7 logical call id for one prepared call.

    ``uuid.uuid7()`` covers both project venvs (3.14); the fallback composes the
    same RFC 9562 layout (48-bit ms timestamp, version 7, 74 random bits) on the
    3.13 floor declared by ``requires-python``, which CI runs.
    """
    uuid7 = getattr(uuid, "uuid7", None)
    if callable(uuid7):
        return str(uuid7())
    value = (
        (time.time_ns() // 1_000_000 & 0xFFFF_FFFF_FFFF) << 80
        | 0x7 << 76
        | secrets.randbits(12) << 64
        | 0b10 << 62
        | secrets.randbits(62)
    )
    return str(uuid.UUID(int=value))


def _reject(tc_id: str, name: str, args: dict, kind: str, reason: str) -> _PrepFailure:
    """Build the synthetic failure tuple for a rejected tool call.

    Mirrors `_reject_validation()`'s `ToolCallResult` construction
    (scripts/agent/tool_runner.py:92-102), but tags `error_type` with the
    specific failure `kind` (`configuration`, `unknown_tool`, `validation`,
    `schema`, `metadata`, `duplicate_id`) instead of the single `"validation"`
    literal, and returns the flat 6-tuple shape `execute_one_tool_call()`
    produces rather than a `ToolCallResult`.
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
    if not isinstance(tc_id, str):
        return _reject(
            str(tc_id), name or "", {}, "validation", "tool call id must be a string"
        )
    malformed = _malformed_id_reason(tc_id)
    if malformed:
        return _reject(tc_id, name or "", {}, "validation", malformed)
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

    args_hash = _canonical_args_hash(args)
    resolved = _resolve_replay_call_id(ctx, tc_id, name, args, args_hash)
    if isinstance(resolved, tuple):
        return resolved

    return PreparedToolCall(
        call_id=tc_id,
        name=name,
        args=args,
        spec=spec,
        original_call=tc,
        context=ToolExecutionContext(
            call_id=resolved,
            tool=name,
            args_hash=args_hash,
            operation="call_tool",
        ),
    )


def _move_duplicate_ids(
    prepared: list[PreparedToolCall],
) -> tuple[list[PreparedToolCall], list[_PrepFailure]]:
    """Move every prepared call whose `call_id` occurs more than once in the batch
    out of `prepared`, as a `duplicate_id` rejection (AC-001, AC-002).

    Batch-level post-pass over the `_prepare_one` results. Counting sees only
    `prepared` entries: the misexecution hazard is two same-id calls surviving
    preparation together, where the id-keyed `call_specs`/`pc_by_id` dicts in
    `tool_runner._execute_with_dag()` silently resolve both to the last
    occurrence (the second call's arguments execute twice, the first's never).
    A call already rejected for another reason never reached `prepared` and is
    not re-rejected here. Survivors and rejections keep their relative order;
    `complete_round`'s `_merge_in_declared_order` re-establishes declared batch
    order for the persisted rows.
    """
    counts: dict[str, int] = {}
    for pc in prepared:
        counts[pc.call_id] = counts.get(pc.call_id, 0) + 1
    kept: list[PreparedToolCall] = []
    failures: list[_PrepFailure] = []
    for pc in prepared:
        if counts[pc.call_id] > 1:
            failures.append(
                _reject(
                    pc.call_id,
                    pc.name,
                    pc.args,
                    "duplicate_id",
                    f"duplicate tool call id {pc.call_id!r} appears "
                    f"{counts[pc.call_id]} times in this round",
                )
            )
        else:
            kept.append(pc)
    return kept, failures


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

    Duplicate call ids are rejected after the per-call loop by
    `_move_duplicate_ids()`; those rejections are appended after the per-call
    ones, and `_merge_in_declared_order()` (agent.tool_round_completion)
    re-establishes declared batch order downstream.
    """
    prepared: list[PreparedToolCall] = []
    failures: list[_PrepFailure] = []
    for tc in tool_calls:
        outcome = _prepare_one(ctx, tc)
        if isinstance(outcome, PreparedToolCall):
            prepared.append(outcome)
        else:
            failures.append(outcome)
    prepared, dup_failures = _move_duplicate_ids(prepared)
    failures.extend(dup_failures)
    return prepared, failures
