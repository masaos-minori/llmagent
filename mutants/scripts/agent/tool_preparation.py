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


from mutmut.mutation.trampoline import wrap_in_trampoline as _mutmut_mutated, MutantDict


@dataclass(frozen=True)
class PreparedToolCall:
    """A raw tool call that has passed preparation and is ready for approval/execution."""

    call_id: str
    name: str
    args: dict[str, Any]
    spec: ToolSpec
    original_call: dict
mutants_x__reject__mutmut: MutantDict = {}  # type: ignore


@_mutmut_mutated(mutants_x__reject__mutmut)
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


def x__reject__mutmut_orig(tc_id: str, name: str, args: dict, kind: str, reason: str) -> _PrepFailure:
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


def x__reject__mutmut_1(tc_id: str, name: str, args: dict, kind: str, reason: str) -> _PrepFailure:
    """Build the synthetic failure tuple for a rejected tool call.

    Mirrors `_reject_validation()`'s `ToolCallResult` construction
    (scripts/agent/tool_runner.py:92-102), but tags `error_type` with the
    specific failure `kind` (`configuration`, `unknown_tool`, `validation`,
    `schema`, `metadata`) instead of the single `"validation"` literal, and
    returns the flat 6-tuple shape `execute_one_tool_call()` produces rather
    than a `ToolCallResult`.
    """
    result = None
    logger.warning(
        "tool_preparation_rejected kind=%s tool=%r reason=%s", kind, name, reason
    )
    return tc_id, name, args, result.output, result.is_error, result.output


def x__reject__mutmut_2(tc_id: str, name: str, args: dict, kind: str, reason: str) -> _PrepFailure:
    """Build the synthetic failure tuple for a rejected tool call.

    Mirrors `_reject_validation()`'s `ToolCallResult` construction
    (scripts/agent/tool_runner.py:92-102), but tags `error_type` with the
    specific failure `kind` (`configuration`, `unknown_tool`, `validation`,
    `schema`, `metadata`) instead of the single `"validation"` literal, and
    returns the flat 6-tuple shape `execute_one_tool_call()` produces rather
    than a `ToolCallResult`.
    """
    result = ToolCallResult(
        output=None,
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


def x__reject__mutmut_3(tc_id: str, name: str, args: dict, kind: str, reason: str) -> _PrepFailure:
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
        is_error=None,
        request_id="",
        server_key="",
        source="tool_preparation",
        error_type=kind,
    )
    logger.warning(
        "tool_preparation_rejected kind=%s tool=%r reason=%s", kind, name, reason
    )
    return tc_id, name, args, result.output, result.is_error, result.output


def x__reject__mutmut_4(tc_id: str, name: str, args: dict, kind: str, reason: str) -> _PrepFailure:
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
        request_id=None,
        server_key="",
        source="tool_preparation",
        error_type=kind,
    )
    logger.warning(
        "tool_preparation_rejected kind=%s tool=%r reason=%s", kind, name, reason
    )
    return tc_id, name, args, result.output, result.is_error, result.output


def x__reject__mutmut_5(tc_id: str, name: str, args: dict, kind: str, reason: str) -> _PrepFailure:
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
        server_key=None,
        source="tool_preparation",
        error_type=kind,
    )
    logger.warning(
        "tool_preparation_rejected kind=%s tool=%r reason=%s", kind, name, reason
    )
    return tc_id, name, args, result.output, result.is_error, result.output


def x__reject__mutmut_6(tc_id: str, name: str, args: dict, kind: str, reason: str) -> _PrepFailure:
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
        source=None,
        error_type=kind,
    )
    logger.warning(
        "tool_preparation_rejected kind=%s tool=%r reason=%s", kind, name, reason
    )
    return tc_id, name, args, result.output, result.is_error, result.output


def x__reject__mutmut_7(tc_id: str, name: str, args: dict, kind: str, reason: str) -> _PrepFailure:
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
        error_type=None,
    )
    logger.warning(
        "tool_preparation_rejected kind=%s tool=%r reason=%s", kind, name, reason
    )
    return tc_id, name, args, result.output, result.is_error, result.output


def x__reject__mutmut_8(tc_id: str, name: str, args: dict, kind: str, reason: str) -> _PrepFailure:
    """Build the synthetic failure tuple for a rejected tool call.

    Mirrors `_reject_validation()`'s `ToolCallResult` construction
    (scripts/agent/tool_runner.py:92-102), but tags `error_type` with the
    specific failure `kind` (`configuration`, `unknown_tool`, `validation`,
    `schema`, `metadata`) instead of the single `"validation"` literal, and
    returns the flat 6-tuple shape `execute_one_tool_call()` produces rather
    than a `ToolCallResult`.
    """
    result = ToolCallResult(
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


def x__reject__mutmut_9(tc_id: str, name: str, args: dict, kind: str, reason: str) -> _PrepFailure:
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
        request_id="",
        server_key="",
        source="tool_preparation",
        error_type=kind,
    )
    logger.warning(
        "tool_preparation_rejected kind=%s tool=%r reason=%s", kind, name, reason
    )
    return tc_id, name, args, result.output, result.is_error, result.output


def x__reject__mutmut_10(tc_id: str, name: str, args: dict, kind: str, reason: str) -> _PrepFailure:
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
        server_key="",
        source="tool_preparation",
        error_type=kind,
    )
    logger.warning(
        "tool_preparation_rejected kind=%s tool=%r reason=%s", kind, name, reason
    )
    return tc_id, name, args, result.output, result.is_error, result.output


def x__reject__mutmut_11(tc_id: str, name: str, args: dict, kind: str, reason: str) -> _PrepFailure:
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
        source="tool_preparation",
        error_type=kind,
    )
    logger.warning(
        "tool_preparation_rejected kind=%s tool=%r reason=%s", kind, name, reason
    )
    return tc_id, name, args, result.output, result.is_error, result.output


def x__reject__mutmut_12(tc_id: str, name: str, args: dict, kind: str, reason: str) -> _PrepFailure:
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
        error_type=kind,
    )
    logger.warning(
        "tool_preparation_rejected kind=%s tool=%r reason=%s", kind, name, reason
    )
    return tc_id, name, args, result.output, result.is_error, result.output


def x__reject__mutmut_13(tc_id: str, name: str, args: dict, kind: str, reason: str) -> _PrepFailure:
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
        )
    logger.warning(
        "tool_preparation_rejected kind=%s tool=%r reason=%s", kind, name, reason
    )
    return tc_id, name, args, result.output, result.is_error, result.output


def x__reject__mutmut_14(tc_id: str, name: str, args: dict, kind: str, reason: str) -> _PrepFailure:
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
        is_error=False,
        request_id="",
        server_key="",
        source="tool_preparation",
        error_type=kind,
    )
    logger.warning(
        "tool_preparation_rejected kind=%s tool=%r reason=%s", kind, name, reason
    )
    return tc_id, name, args, result.output, result.is_error, result.output


def x__reject__mutmut_15(tc_id: str, name: str, args: dict, kind: str, reason: str) -> _PrepFailure:
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
        request_id="XXXX",
        server_key="",
        source="tool_preparation",
        error_type=kind,
    )
    logger.warning(
        "tool_preparation_rejected kind=%s tool=%r reason=%s", kind, name, reason
    )
    return tc_id, name, args, result.output, result.is_error, result.output


def x__reject__mutmut_16(tc_id: str, name: str, args: dict, kind: str, reason: str) -> _PrepFailure:
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
        server_key="XXXX",
        source="tool_preparation",
        error_type=kind,
    )
    logger.warning(
        "tool_preparation_rejected kind=%s tool=%r reason=%s", kind, name, reason
    )
    return tc_id, name, args, result.output, result.is_error, result.output


def x__reject__mutmut_17(tc_id: str, name: str, args: dict, kind: str, reason: str) -> _PrepFailure:
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
        source="XXtool_preparationXX",
        error_type=kind,
    )
    logger.warning(
        "tool_preparation_rejected kind=%s tool=%r reason=%s", kind, name, reason
    )
    return tc_id, name, args, result.output, result.is_error, result.output


def x__reject__mutmut_18(tc_id: str, name: str, args: dict, kind: str, reason: str) -> _PrepFailure:
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
        source="TOOL_PREPARATION",
        error_type=kind,
    )
    logger.warning(
        "tool_preparation_rejected kind=%s tool=%r reason=%s", kind, name, reason
    )
    return tc_id, name, args, result.output, result.is_error, result.output


def x__reject__mutmut_19(tc_id: str, name: str, args: dict, kind: str, reason: str) -> _PrepFailure:
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
        None, kind, name, reason
    )
    return tc_id, name, args, result.output, result.is_error, result.output


def x__reject__mutmut_20(tc_id: str, name: str, args: dict, kind: str, reason: str) -> _PrepFailure:
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
        "tool_preparation_rejected kind=%s tool=%r reason=%s", None, name, reason
    )
    return tc_id, name, args, result.output, result.is_error, result.output


def x__reject__mutmut_21(tc_id: str, name: str, args: dict, kind: str, reason: str) -> _PrepFailure:
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
        "tool_preparation_rejected kind=%s tool=%r reason=%s", kind, None, reason
    )
    return tc_id, name, args, result.output, result.is_error, result.output


def x__reject__mutmut_22(tc_id: str, name: str, args: dict, kind: str, reason: str) -> _PrepFailure:
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
        "tool_preparation_rejected kind=%s tool=%r reason=%s", kind, name, None
    )
    return tc_id, name, args, result.output, result.is_error, result.output


def x__reject__mutmut_23(tc_id: str, name: str, args: dict, kind: str, reason: str) -> _PrepFailure:
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
        kind, name, reason
    )
    return tc_id, name, args, result.output, result.is_error, result.output


def x__reject__mutmut_24(tc_id: str, name: str, args: dict, kind: str, reason: str) -> _PrepFailure:
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
        "tool_preparation_rejected kind=%s tool=%r reason=%s", name, reason
    )
    return tc_id, name, args, result.output, result.is_error, result.output


def x__reject__mutmut_25(tc_id: str, name: str, args: dict, kind: str, reason: str) -> _PrepFailure:
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
        "tool_preparation_rejected kind=%s tool=%r reason=%s", kind, reason
    )
    return tc_id, name, args, result.output, result.is_error, result.output


def x__reject__mutmut_26(tc_id: str, name: str, args: dict, kind: str, reason: str) -> _PrepFailure:
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
        "tool_preparation_rejected kind=%s tool=%r reason=%s", kind, name, )
    return tc_id, name, args, result.output, result.is_error, result.output


def x__reject__mutmut_27(tc_id: str, name: str, args: dict, kind: str, reason: str) -> _PrepFailure:
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
        "XXtool_preparation_rejected kind=%s tool=%r reason=%sXX", kind, name, reason
    )
    return tc_id, name, args, result.output, result.is_error, result.output


def x__reject__mutmut_28(tc_id: str, name: str, args: dict, kind: str, reason: str) -> _PrepFailure:
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
        "TOOL_PREPARATION_REJECTED KIND=%S TOOL=%R REASON=%S", kind, name, reason
    )
    return tc_id, name, args, result.output, result.is_error, result.output

mutants_x__reject__mutmut['_mutmut_orig'] = x__reject__mutmut_orig # type: ignore # mutmut generated
mutants_x__reject__mutmut['x__reject__mutmut_1'] = x__reject__mutmut_1 # type: ignore # mutmut generated
mutants_x__reject__mutmut['x__reject__mutmut_2'] = x__reject__mutmut_2 # type: ignore # mutmut generated
mutants_x__reject__mutmut['x__reject__mutmut_3'] = x__reject__mutmut_3 # type: ignore # mutmut generated
mutants_x__reject__mutmut['x__reject__mutmut_4'] = x__reject__mutmut_4 # type: ignore # mutmut generated
mutants_x__reject__mutmut['x__reject__mutmut_5'] = x__reject__mutmut_5 # type: ignore # mutmut generated
mutants_x__reject__mutmut['x__reject__mutmut_6'] = x__reject__mutmut_6 # type: ignore # mutmut generated
mutants_x__reject__mutmut['x__reject__mutmut_7'] = x__reject__mutmut_7 # type: ignore # mutmut generated
mutants_x__reject__mutmut['x__reject__mutmut_8'] = x__reject__mutmut_8 # type: ignore # mutmut generated
mutants_x__reject__mutmut['x__reject__mutmut_9'] = x__reject__mutmut_9 # type: ignore # mutmut generated
mutants_x__reject__mutmut['x__reject__mutmut_10'] = x__reject__mutmut_10 # type: ignore # mutmut generated
mutants_x__reject__mutmut['x__reject__mutmut_11'] = x__reject__mutmut_11 # type: ignore # mutmut generated
mutants_x__reject__mutmut['x__reject__mutmut_12'] = x__reject__mutmut_12 # type: ignore # mutmut generated
mutants_x__reject__mutmut['x__reject__mutmut_13'] = x__reject__mutmut_13 # type: ignore # mutmut generated
mutants_x__reject__mutmut['x__reject__mutmut_14'] = x__reject__mutmut_14 # type: ignore # mutmut generated
mutants_x__reject__mutmut['x__reject__mutmut_15'] = x__reject__mutmut_15 # type: ignore # mutmut generated
mutants_x__reject__mutmut['x__reject__mutmut_16'] = x__reject__mutmut_16 # type: ignore # mutmut generated
mutants_x__reject__mutmut['x__reject__mutmut_17'] = x__reject__mutmut_17 # type: ignore # mutmut generated
mutants_x__reject__mutmut['x__reject__mutmut_18'] = x__reject__mutmut_18 # type: ignore # mutmut generated
mutants_x__reject__mutmut['x__reject__mutmut_19'] = x__reject__mutmut_19 # type: ignore # mutmut generated
mutants_x__reject__mutmut['x__reject__mutmut_20'] = x__reject__mutmut_20 # type: ignore # mutmut generated
mutants_x__reject__mutmut['x__reject__mutmut_21'] = x__reject__mutmut_21 # type: ignore # mutmut generated
mutants_x__reject__mutmut['x__reject__mutmut_22'] = x__reject__mutmut_22 # type: ignore # mutmut generated
mutants_x__reject__mutmut['x__reject__mutmut_23'] = x__reject__mutmut_23 # type: ignore # mutmut generated
mutants_x__reject__mutmut['x__reject__mutmut_24'] = x__reject__mutmut_24 # type: ignore # mutmut generated
mutants_x__reject__mutmut['x__reject__mutmut_25'] = x__reject__mutmut_25 # type: ignore # mutmut generated
mutants_x__reject__mutmut['x__reject__mutmut_26'] = x__reject__mutmut_26 # type: ignore # mutmut generated
mutants_x__reject__mutmut['x__reject__mutmut_27'] = x__reject__mutmut_27 # type: ignore # mutmut generated
mutants_x__reject__mutmut['x__reject__mutmut_28'] = x__reject__mutmut_28 # type: ignore # mutmut generated
mutants_x__prepare_one__mutmut: MutantDict = {}  # type: ignore


@_mutmut_mutated(mutants_x__prepare_one__mutmut)
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


def x__prepare_one__mutmut_orig(ctx: AgentContext, tc: dict) -> PreparedToolCall | _PrepFailure:
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


def x__prepare_one__mutmut_1(ctx: AgentContext, tc: dict) -> PreparedToolCall | _PrepFailure:
    """Prepare one raw tool call, returning either a `PreparedToolCall` or a failure tuple."""
    tc_id = None
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


def x__prepare_one__mutmut_2(ctx: AgentContext, tc: dict) -> PreparedToolCall | _PrepFailure:
    """Prepare one raw tool call, returning either a `PreparedToolCall` or a failure tuple."""
    tc_id = tc.get(None)
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


def x__prepare_one__mutmut_3(ctx: AgentContext, tc: dict) -> PreparedToolCall | _PrepFailure:
    """Prepare one raw tool call, returning either a `PreparedToolCall` or a failure tuple."""
    tc_id = tc.get("XXidXX")
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


def x__prepare_one__mutmut_4(ctx: AgentContext, tc: dict) -> PreparedToolCall | _PrepFailure:
    """Prepare one raw tool call, returning either a `PreparedToolCall` or a failure tuple."""
    tc_id = tc.get("ID")
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


def x__prepare_one__mutmut_5(ctx: AgentContext, tc: dict) -> PreparedToolCall | _PrepFailure:
    """Prepare one raw tool call, returning either a `PreparedToolCall` or a failure tuple."""
    tc_id = tc.get("id")
    func = None
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


def x__prepare_one__mutmut_6(ctx: AgentContext, tc: dict) -> PreparedToolCall | _PrepFailure:
    """Prepare one raw tool call, returning either a `PreparedToolCall` or a failure tuple."""
    tc_id = tc.get("id")
    func = tc.get("function") and {}
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


def x__prepare_one__mutmut_7(ctx: AgentContext, tc: dict) -> PreparedToolCall | _PrepFailure:
    """Prepare one raw tool call, returning either a `PreparedToolCall` or a failure tuple."""
    tc_id = tc.get("id")
    func = tc.get(None) or {}
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


def x__prepare_one__mutmut_8(ctx: AgentContext, tc: dict) -> PreparedToolCall | _PrepFailure:
    """Prepare one raw tool call, returning either a `PreparedToolCall` or a failure tuple."""
    tc_id = tc.get("id")
    func = tc.get("XXfunctionXX") or {}
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


def x__prepare_one__mutmut_9(ctx: AgentContext, tc: dict) -> PreparedToolCall | _PrepFailure:
    """Prepare one raw tool call, returning either a `PreparedToolCall` or a failure tuple."""
    tc_id = tc.get("id")
    func = tc.get("FUNCTION") or {}
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


def x__prepare_one__mutmut_10(ctx: AgentContext, tc: dict) -> PreparedToolCall | _PrepFailure:
    """Prepare one raw tool call, returning either a `PreparedToolCall` or a failure tuple."""
    tc_id = tc.get("id")
    func = tc.get("function") or {}
    name = None

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


def x__prepare_one__mutmut_11(ctx: AgentContext, tc: dict) -> PreparedToolCall | _PrepFailure:
    """Prepare one raw tool call, returning either a `PreparedToolCall` or a failure tuple."""
    tc_id = tc.get("id")
    func = tc.get("function") or {}
    name = func.get(None)

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


def x__prepare_one__mutmut_12(ctx: AgentContext, tc: dict) -> PreparedToolCall | _PrepFailure:
    """Prepare one raw tool call, returning either a `PreparedToolCall` or a failure tuple."""
    tc_id = tc.get("id")
    func = tc.get("function") or {}
    name = func.get("XXnameXX")

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


def x__prepare_one__mutmut_13(ctx: AgentContext, tc: dict) -> PreparedToolCall | _PrepFailure:
    """Prepare one raw tool call, returning either a `PreparedToolCall` or a failure tuple."""
    tc_id = tc.get("id")
    func = tc.get("function") or {}
    name = func.get("NAME")

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


def x__prepare_one__mutmut_14(ctx: AgentContext, tc: dict) -> PreparedToolCall | _PrepFailure:
    """Prepare one raw tool call, returning either a `PreparedToolCall` or a failure tuple."""
    tc_id = tc.get("id")
    func = tc.get("function") or {}
    name = func.get("name")

    if tc_id:
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


def x__prepare_one__mutmut_15(ctx: AgentContext, tc: dict) -> PreparedToolCall | _PrepFailure:
    """Prepare one raw tool call, returning either a `PreparedToolCall` or a failure tuple."""
    tc_id = tc.get("id")
    func = tc.get("function") or {}
    name = func.get("name")

    if not tc_id:
        return _reject(
            None, name or "", {}, "configuration", "tool call is missing an id"
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


def x__prepare_one__mutmut_16(ctx: AgentContext, tc: dict) -> PreparedToolCall | _PrepFailure:
    """Prepare one raw tool call, returning either a `PreparedToolCall` or a failure tuple."""
    tc_id = tc.get("id")
    func = tc.get("function") or {}
    name = func.get("name")

    if not tc_id:
        return _reject(
            tc_id or "", None, {}, "configuration", "tool call is missing an id"
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


def x__prepare_one__mutmut_17(ctx: AgentContext, tc: dict) -> PreparedToolCall | _PrepFailure:
    """Prepare one raw tool call, returning either a `PreparedToolCall` or a failure tuple."""
    tc_id = tc.get("id")
    func = tc.get("function") or {}
    name = func.get("name")

    if not tc_id:
        return _reject(
            tc_id or "", name or "", None, "configuration", "tool call is missing an id"
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


def x__prepare_one__mutmut_18(ctx: AgentContext, tc: dict) -> PreparedToolCall | _PrepFailure:
    """Prepare one raw tool call, returning either a `PreparedToolCall` or a failure tuple."""
    tc_id = tc.get("id")
    func = tc.get("function") or {}
    name = func.get("name")

    if not tc_id:
        return _reject(
            tc_id or "", name or "", {}, None, "tool call is missing an id"
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


def x__prepare_one__mutmut_19(ctx: AgentContext, tc: dict) -> PreparedToolCall | _PrepFailure:
    """Prepare one raw tool call, returning either a `PreparedToolCall` or a failure tuple."""
    tc_id = tc.get("id")
    func = tc.get("function") or {}
    name = func.get("name")

    if not tc_id:
        return _reject(
            tc_id or "", name or "", {}, "configuration", None
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


def x__prepare_one__mutmut_20(ctx: AgentContext, tc: dict) -> PreparedToolCall | _PrepFailure:
    """Prepare one raw tool call, returning either a `PreparedToolCall` or a failure tuple."""
    tc_id = tc.get("id")
    func = tc.get("function") or {}
    name = func.get("name")

    if not tc_id:
        return _reject(
            name or "", {}, "configuration", "tool call is missing an id"
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


def x__prepare_one__mutmut_21(ctx: AgentContext, tc: dict) -> PreparedToolCall | _PrepFailure:
    """Prepare one raw tool call, returning either a `PreparedToolCall` or a failure tuple."""
    tc_id = tc.get("id")
    func = tc.get("function") or {}
    name = func.get("name")

    if not tc_id:
        return _reject(
            tc_id or "", {}, "configuration", "tool call is missing an id"
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


def x__prepare_one__mutmut_22(ctx: AgentContext, tc: dict) -> PreparedToolCall | _PrepFailure:
    """Prepare one raw tool call, returning either a `PreparedToolCall` or a failure tuple."""
    tc_id = tc.get("id")
    func = tc.get("function") or {}
    name = func.get("name")

    if not tc_id:
        return _reject(
            tc_id or "", name or "", "configuration", "tool call is missing an id"
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


def x__prepare_one__mutmut_23(ctx: AgentContext, tc: dict) -> PreparedToolCall | _PrepFailure:
    """Prepare one raw tool call, returning either a `PreparedToolCall` or a failure tuple."""
    tc_id = tc.get("id")
    func = tc.get("function") or {}
    name = func.get("name")

    if not tc_id:
        return _reject(
            tc_id or "", name or "", {}, "tool call is missing an id"
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


def x__prepare_one__mutmut_24(ctx: AgentContext, tc: dict) -> PreparedToolCall | _PrepFailure:
    """Prepare one raw tool call, returning either a `PreparedToolCall` or a failure tuple."""
    tc_id = tc.get("id")
    func = tc.get("function") or {}
    name = func.get("name")

    if not tc_id:
        return _reject(
            tc_id or "", name or "", {}, "configuration", )
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


def x__prepare_one__mutmut_25(ctx: AgentContext, tc: dict) -> PreparedToolCall | _PrepFailure:
    """Prepare one raw tool call, returning either a `PreparedToolCall` or a failure tuple."""
    tc_id = tc.get("id")
    func = tc.get("function") or {}
    name = func.get("name")

    if not tc_id:
        return _reject(
            tc_id and "", name or "", {}, "configuration", "tool call is missing an id"
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


def x__prepare_one__mutmut_26(ctx: AgentContext, tc: dict) -> PreparedToolCall | _PrepFailure:
    """Prepare one raw tool call, returning either a `PreparedToolCall` or a failure tuple."""
    tc_id = tc.get("id")
    func = tc.get("function") or {}
    name = func.get("name")

    if not tc_id:
        return _reject(
            tc_id or "XXXX", name or "", {}, "configuration", "tool call is missing an id"
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


def x__prepare_one__mutmut_27(ctx: AgentContext, tc: dict) -> PreparedToolCall | _PrepFailure:
    """Prepare one raw tool call, returning either a `PreparedToolCall` or a failure tuple."""
    tc_id = tc.get("id")
    func = tc.get("function") or {}
    name = func.get("name")

    if not tc_id:
        return _reject(
            tc_id or "", name and "", {}, "configuration", "tool call is missing an id"
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


def x__prepare_one__mutmut_28(ctx: AgentContext, tc: dict) -> PreparedToolCall | _PrepFailure:
    """Prepare one raw tool call, returning either a `PreparedToolCall` or a failure tuple."""
    tc_id = tc.get("id")
    func = tc.get("function") or {}
    name = func.get("name")

    if not tc_id:
        return _reject(
            tc_id or "", name or "XXXX", {}, "configuration", "tool call is missing an id"
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


def x__prepare_one__mutmut_29(ctx: AgentContext, tc: dict) -> PreparedToolCall | _PrepFailure:
    """Prepare one raw tool call, returning either a `PreparedToolCall` or a failure tuple."""
    tc_id = tc.get("id")
    func = tc.get("function") or {}
    name = func.get("name")

    if not tc_id:
        return _reject(
            tc_id or "", name or "", {}, "XXconfigurationXX", "tool call is missing an id"
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


def x__prepare_one__mutmut_30(ctx: AgentContext, tc: dict) -> PreparedToolCall | _PrepFailure:
    """Prepare one raw tool call, returning either a `PreparedToolCall` or a failure tuple."""
    tc_id = tc.get("id")
    func = tc.get("function") or {}
    name = func.get("name")

    if not tc_id:
        return _reject(
            tc_id or "", name or "", {}, "CONFIGURATION", "tool call is missing an id"
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


def x__prepare_one__mutmut_31(ctx: AgentContext, tc: dict) -> PreparedToolCall | _PrepFailure:
    """Prepare one raw tool call, returning either a `PreparedToolCall` or a failure tuple."""
    tc_id = tc.get("id")
    func = tc.get("function") or {}
    name = func.get("name")

    if not tc_id:
        return _reject(
            tc_id or "", name or "", {}, "configuration", "XXtool call is missing an idXX"
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


def x__prepare_one__mutmut_32(ctx: AgentContext, tc: dict) -> PreparedToolCall | _PrepFailure:
    """Prepare one raw tool call, returning either a `PreparedToolCall` or a failure tuple."""
    tc_id = tc.get("id")
    func = tc.get("function") or {}
    name = func.get("name")

    if not tc_id:
        return _reject(
            tc_id or "", name or "", {}, "configuration", "TOOL CALL IS MISSING AN ID"
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


def x__prepare_one__mutmut_33(ctx: AgentContext, tc: dict) -> PreparedToolCall | _PrepFailure:
    """Prepare one raw tool call, returning either a `PreparedToolCall` or a failure tuple."""
    tc_id = tc.get("id")
    func = tc.get("function") or {}
    name = func.get("name")

    if not tc_id:
        return _reject(
            tc_id or "", name or "", {}, "configuration", "tool call is missing an id"
        )
    if name:
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


def x__prepare_one__mutmut_34(ctx: AgentContext, tc: dict) -> PreparedToolCall | _PrepFailure:
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
            None, "", {}, "validation", "tool call is missing a function name"
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


def x__prepare_one__mutmut_35(ctx: AgentContext, tc: dict) -> PreparedToolCall | _PrepFailure:
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
            tc_id, None, {}, "validation", "tool call is missing a function name"
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


def x__prepare_one__mutmut_36(ctx: AgentContext, tc: dict) -> PreparedToolCall | _PrepFailure:
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
            tc_id, "", None, "validation", "tool call is missing a function name"
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


def x__prepare_one__mutmut_37(ctx: AgentContext, tc: dict) -> PreparedToolCall | _PrepFailure:
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
            tc_id, "", {}, None, "tool call is missing a function name"
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


def x__prepare_one__mutmut_38(ctx: AgentContext, tc: dict) -> PreparedToolCall | _PrepFailure:
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
            tc_id, "", {}, "validation", None
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


def x__prepare_one__mutmut_39(ctx: AgentContext, tc: dict) -> PreparedToolCall | _PrepFailure:
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
            "", {}, "validation", "tool call is missing a function name"
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


def x__prepare_one__mutmut_40(ctx: AgentContext, tc: dict) -> PreparedToolCall | _PrepFailure:
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
            tc_id, {}, "validation", "tool call is missing a function name"
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


def x__prepare_one__mutmut_41(ctx: AgentContext, tc: dict) -> PreparedToolCall | _PrepFailure:
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
            tc_id, "", "validation", "tool call is missing a function name"
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


def x__prepare_one__mutmut_42(ctx: AgentContext, tc: dict) -> PreparedToolCall | _PrepFailure:
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
            tc_id, "", {}, "tool call is missing a function name"
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


def x__prepare_one__mutmut_43(ctx: AgentContext, tc: dict) -> PreparedToolCall | _PrepFailure:
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
            tc_id, "", {}, "validation", )

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


def x__prepare_one__mutmut_44(ctx: AgentContext, tc: dict) -> PreparedToolCall | _PrepFailure:
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
            tc_id, "XXXX", {}, "validation", "tool call is missing a function name"
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


def x__prepare_one__mutmut_45(ctx: AgentContext, tc: dict) -> PreparedToolCall | _PrepFailure:
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
            tc_id, "", {}, "XXvalidationXX", "tool call is missing a function name"
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


def x__prepare_one__mutmut_46(ctx: AgentContext, tc: dict) -> PreparedToolCall | _PrepFailure:
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
            tc_id, "", {}, "VALIDATION", "tool call is missing a function name"
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


def x__prepare_one__mutmut_47(ctx: AgentContext, tc: dict) -> PreparedToolCall | _PrepFailure:
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
            tc_id, "", {}, "validation", "XXtool call is missing a function nameXX"
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


def x__prepare_one__mutmut_48(ctx: AgentContext, tc: dict) -> PreparedToolCall | _PrepFailure:
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
            tc_id, "", {}, "validation", "TOOL CALL IS MISSING A FUNCTION NAME"
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


def x__prepare_one__mutmut_49(ctx: AgentContext, tc: dict) -> PreparedToolCall | _PrepFailure:
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

    args_str = None
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


def x__prepare_one__mutmut_50(ctx: AgentContext, tc: dict) -> PreparedToolCall | _PrepFailure:
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

    args_str = func.get(None, "{}")
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


def x__prepare_one__mutmut_51(ctx: AgentContext, tc: dict) -> PreparedToolCall | _PrepFailure:
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

    args_str = func.get("arguments", None)
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


def x__prepare_one__mutmut_52(ctx: AgentContext, tc: dict) -> PreparedToolCall | _PrepFailure:
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

    args_str = func.get("{}")
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


def x__prepare_one__mutmut_53(ctx: AgentContext, tc: dict) -> PreparedToolCall | _PrepFailure:
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

    args_str = func.get("arguments", )
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


def x__prepare_one__mutmut_54(ctx: AgentContext, tc: dict) -> PreparedToolCall | _PrepFailure:
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

    args_str = func.get("XXargumentsXX", "{}")
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


def x__prepare_one__mutmut_55(ctx: AgentContext, tc: dict) -> PreparedToolCall | _PrepFailure:
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

    args_str = func.get("ARGUMENTS", "{}")
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


def x__prepare_one__mutmut_56(ctx: AgentContext, tc: dict) -> PreparedToolCall | _PrepFailure:
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

    args_str = func.get("arguments", "XX{}XX")
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


def x__prepare_one__mutmut_57(ctx: AgentContext, tc: dict) -> PreparedToolCall | _PrepFailure:
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
        args = None
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


def x__prepare_one__mutmut_58(ctx: AgentContext, tc: dict) -> PreparedToolCall | _PrepFailure:
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
        args = orjson.loads(None)
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


def x__prepare_one__mutmut_59(ctx: AgentContext, tc: dict) -> PreparedToolCall | _PrepFailure:
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
            None,
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


def x__prepare_one__mutmut_60(ctx: AgentContext, tc: dict) -> PreparedToolCall | _PrepFailure:
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
            None,
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


def x__prepare_one__mutmut_61(ctx: AgentContext, tc: dict) -> PreparedToolCall | _PrepFailure:
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
            None,
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


def x__prepare_one__mutmut_62(ctx: AgentContext, tc: dict) -> PreparedToolCall | _PrepFailure:
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
            None,
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


def x__prepare_one__mutmut_63(ctx: AgentContext, tc: dict) -> PreparedToolCall | _PrepFailure:
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
            None,
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


def x__prepare_one__mutmut_64(ctx: AgentContext, tc: dict) -> PreparedToolCall | _PrepFailure:
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


def x__prepare_one__mutmut_65(ctx: AgentContext, tc: dict) -> PreparedToolCall | _PrepFailure:
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


def x__prepare_one__mutmut_66(ctx: AgentContext, tc: dict) -> PreparedToolCall | _PrepFailure:
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


def x__prepare_one__mutmut_67(ctx: AgentContext, tc: dict) -> PreparedToolCall | _PrepFailure:
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


def x__prepare_one__mutmut_68(ctx: AgentContext, tc: dict) -> PreparedToolCall | _PrepFailure:
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


def x__prepare_one__mutmut_69(ctx: AgentContext, tc: dict) -> PreparedToolCall | _PrepFailure:
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
            "XXvalidationXX",
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


def x__prepare_one__mutmut_70(ctx: AgentContext, tc: dict) -> PreparedToolCall | _PrepFailure:
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
            "VALIDATION",
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


def x__prepare_one__mutmut_71(ctx: AgentContext, tc: dict) -> PreparedToolCall | _PrepFailure:
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

    if isinstance(args, dict):
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


def x__prepare_one__mutmut_72(ctx: AgentContext, tc: dict) -> PreparedToolCall | _PrepFailure:
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
            None,
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


def x__prepare_one__mutmut_73(ctx: AgentContext, tc: dict) -> PreparedToolCall | _PrepFailure:
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
            None,
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


def x__prepare_one__mutmut_74(ctx: AgentContext, tc: dict) -> PreparedToolCall | _PrepFailure:
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
            None,
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


def x__prepare_one__mutmut_75(ctx: AgentContext, tc: dict) -> PreparedToolCall | _PrepFailure:
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
            None,
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


def x__prepare_one__mutmut_76(ctx: AgentContext, tc: dict) -> PreparedToolCall | _PrepFailure:
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
            None,
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


def x__prepare_one__mutmut_77(ctx: AgentContext, tc: dict) -> PreparedToolCall | _PrepFailure:
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


def x__prepare_one__mutmut_78(ctx: AgentContext, tc: dict) -> PreparedToolCall | _PrepFailure:
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


def x__prepare_one__mutmut_79(ctx: AgentContext, tc: dict) -> PreparedToolCall | _PrepFailure:
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


def x__prepare_one__mutmut_80(ctx: AgentContext, tc: dict) -> PreparedToolCall | _PrepFailure:
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


def x__prepare_one__mutmut_81(ctx: AgentContext, tc: dict) -> PreparedToolCall | _PrepFailure:
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


def x__prepare_one__mutmut_82(ctx: AgentContext, tc: dict) -> PreparedToolCall | _PrepFailure:
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
            "XXvalidationXX",
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


def x__prepare_one__mutmut_83(ctx: AgentContext, tc: dict) -> PreparedToolCall | _PrepFailure:
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
            "VALIDATION",
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


def x__prepare_one__mutmut_84(ctx: AgentContext, tc: dict) -> PreparedToolCall | _PrepFailure:
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
            "XXarguments must decode to a JSON objectXX",
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


def x__prepare_one__mutmut_85(ctx: AgentContext, tc: dict) -> PreparedToolCall | _PrepFailure:
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
            "arguments must decode to a json object",
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


def x__prepare_one__mutmut_86(ctx: AgentContext, tc: dict) -> PreparedToolCall | _PrepFailure:
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
            "ARGUMENTS MUST DECODE TO A JSON OBJECT",
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


def x__prepare_one__mutmut_87(ctx: AgentContext, tc: dict) -> PreparedToolCall | _PrepFailure:
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

    registry = None
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


def x__prepare_one__mutmut_88(ctx: AgentContext, tc: dict) -> PreparedToolCall | _PrepFailure:
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
    if registry is not None:
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


def x__prepare_one__mutmut_89(ctx: AgentContext, tc: dict) -> PreparedToolCall | _PrepFailure:
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
            None,
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


def x__prepare_one__mutmut_90(ctx: AgentContext, tc: dict) -> PreparedToolCall | _PrepFailure:
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
            None,
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


def x__prepare_one__mutmut_91(ctx: AgentContext, tc: dict) -> PreparedToolCall | _PrepFailure:
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
            None,
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


def x__prepare_one__mutmut_92(ctx: AgentContext, tc: dict) -> PreparedToolCall | _PrepFailure:
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
            None,
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


def x__prepare_one__mutmut_93(ctx: AgentContext, tc: dict) -> PreparedToolCall | _PrepFailure:
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
            None,
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


def x__prepare_one__mutmut_94(ctx: AgentContext, tc: dict) -> PreparedToolCall | _PrepFailure:
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


def x__prepare_one__mutmut_95(ctx: AgentContext, tc: dict) -> PreparedToolCall | _PrepFailure:
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


def x__prepare_one__mutmut_96(ctx: AgentContext, tc: dict) -> PreparedToolCall | _PrepFailure:
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


def x__prepare_one__mutmut_97(ctx: AgentContext, tc: dict) -> PreparedToolCall | _PrepFailure:
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


def x__prepare_one__mutmut_98(ctx: AgentContext, tc: dict) -> PreparedToolCall | _PrepFailure:
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


def x__prepare_one__mutmut_99(ctx: AgentContext, tc: dict) -> PreparedToolCall | _PrepFailure:
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
            "XXconfigurationXX",
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


def x__prepare_one__mutmut_100(ctx: AgentContext, tc: dict) -> PreparedToolCall | _PrepFailure:
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
            "CONFIGURATION",
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


def x__prepare_one__mutmut_101(ctx: AgentContext, tc: dict) -> PreparedToolCall | _PrepFailure:
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
            "XXRuntimeToolRegistry is not available (ctx.services_required.runtime_tools is None)XX",
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


def x__prepare_one__mutmut_102(ctx: AgentContext, tc: dict) -> PreparedToolCall | _PrepFailure:
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
            "runtimetoolregistry is not available (ctx.services_required.runtime_tools is none)",
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


def x__prepare_one__mutmut_103(ctx: AgentContext, tc: dict) -> PreparedToolCall | _PrepFailure:
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
            "RUNTIMETOOLREGISTRY IS NOT AVAILABLE (CTX.SERVICES_REQUIRED.RUNTIME_TOOLS IS NONE)",
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


def x__prepare_one__mutmut_104(ctx: AgentContext, tc: dict) -> PreparedToolCall | _PrepFailure:
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
        runtime_tool = None
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


def x__prepare_one__mutmut_105(ctx: AgentContext, tc: dict) -> PreparedToolCall | _PrepFailure:
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
        runtime_tool = registry.get(None)
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


def x__prepare_one__mutmut_106(ctx: AgentContext, tc: dict) -> PreparedToolCall | _PrepFailure:
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
            None, name, args, "unknown_tool", f"unregistered tool: {name!r}"
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


def x__prepare_one__mutmut_107(ctx: AgentContext, tc: dict) -> PreparedToolCall | _PrepFailure:
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
            tc_id, None, args, "unknown_tool", f"unregistered tool: {name!r}"
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


def x__prepare_one__mutmut_108(ctx: AgentContext, tc: dict) -> PreparedToolCall | _PrepFailure:
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
            tc_id, name, None, "unknown_tool", f"unregistered tool: {name!r}"
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


def x__prepare_one__mutmut_109(ctx: AgentContext, tc: dict) -> PreparedToolCall | _PrepFailure:
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
            tc_id, name, args, None, f"unregistered tool: {name!r}"
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


def x__prepare_one__mutmut_110(ctx: AgentContext, tc: dict) -> PreparedToolCall | _PrepFailure:
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
            tc_id, name, args, "unknown_tool", None
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


def x__prepare_one__mutmut_111(ctx: AgentContext, tc: dict) -> PreparedToolCall | _PrepFailure:
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
            name, args, "unknown_tool", f"unregistered tool: {name!r}"
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


def x__prepare_one__mutmut_112(ctx: AgentContext, tc: dict) -> PreparedToolCall | _PrepFailure:
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
            tc_id, args, "unknown_tool", f"unregistered tool: {name!r}"
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


def x__prepare_one__mutmut_113(ctx: AgentContext, tc: dict) -> PreparedToolCall | _PrepFailure:
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
            tc_id, name, "unknown_tool", f"unregistered tool: {name!r}"
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


def x__prepare_one__mutmut_114(ctx: AgentContext, tc: dict) -> PreparedToolCall | _PrepFailure:
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
            tc_id, name, args, f"unregistered tool: {name!r}"
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


def x__prepare_one__mutmut_115(ctx: AgentContext, tc: dict) -> PreparedToolCall | _PrepFailure:
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
            tc_id, name, args, "unknown_tool", )

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


def x__prepare_one__mutmut_116(ctx: AgentContext, tc: dict) -> PreparedToolCall | _PrepFailure:
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
            tc_id, name, args, "XXunknown_toolXX", f"unregistered tool: {name!r}"
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


def x__prepare_one__mutmut_117(ctx: AgentContext, tc: dict) -> PreparedToolCall | _PrepFailure:
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
            tc_id, name, args, "UNKNOWN_TOOL", f"unregistered tool: {name!r}"
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


def x__prepare_one__mutmut_118(ctx: AgentContext, tc: dict) -> PreparedToolCall | _PrepFailure:
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

    validation = None
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


def x__prepare_one__mutmut_119(ctx: AgentContext, tc: dict) -> PreparedToolCall | _PrepFailure:
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
        tool_name=None,
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


def x__prepare_one__mutmut_120(ctx: AgentContext, tc: dict) -> PreparedToolCall | _PrepFailure:
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
        args=None,
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


def x__prepare_one__mutmut_121(ctx: AgentContext, tc: dict) -> PreparedToolCall | _PrepFailure:
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
        input_schema=None,
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


def x__prepare_one__mutmut_122(ctx: AgentContext, tc: dict) -> PreparedToolCall | _PrepFailure:
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
        allow_extra_fields=None,
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


def x__prepare_one__mutmut_123(ctx: AgentContext, tc: dict) -> PreparedToolCall | _PrepFailure:
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


def x__prepare_one__mutmut_124(ctx: AgentContext, tc: dict) -> PreparedToolCall | _PrepFailure:
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


def x__prepare_one__mutmut_125(ctx: AgentContext, tc: dict) -> PreparedToolCall | _PrepFailure:
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


def x__prepare_one__mutmut_126(ctx: AgentContext, tc: dict) -> PreparedToolCall | _PrepFailure:
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


def x__prepare_one__mutmut_127(ctx: AgentContext, tc: dict) -> PreparedToolCall | _PrepFailure:
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
    if validation.success:
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


def x__prepare_one__mutmut_128(ctx: AgentContext, tc: dict) -> PreparedToolCall | _PrepFailure:
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
        return _reject(None, name, args, "schema", validation.reason)

    try:
        spec = registry.tool_spec_for_call(tc_id, name, args)
    except KeyError:
        return _reject(
            tc_id, name, args, "metadata", f"failed to build tool metadata for {name!r}"
        )

    return PreparedToolCall(
        call_id=tc_id, name=name, args=args, spec=spec, original_call=tc
    )


def x__prepare_one__mutmut_129(ctx: AgentContext, tc: dict) -> PreparedToolCall | _PrepFailure:
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
        return _reject(tc_id, None, args, "schema", validation.reason)

    try:
        spec = registry.tool_spec_for_call(tc_id, name, args)
    except KeyError:
        return _reject(
            tc_id, name, args, "metadata", f"failed to build tool metadata for {name!r}"
        )

    return PreparedToolCall(
        call_id=tc_id, name=name, args=args, spec=spec, original_call=tc
    )


def x__prepare_one__mutmut_130(ctx: AgentContext, tc: dict) -> PreparedToolCall | _PrepFailure:
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
        return _reject(tc_id, name, None, "schema", validation.reason)

    try:
        spec = registry.tool_spec_for_call(tc_id, name, args)
    except KeyError:
        return _reject(
            tc_id, name, args, "metadata", f"failed to build tool metadata for {name!r}"
        )

    return PreparedToolCall(
        call_id=tc_id, name=name, args=args, spec=spec, original_call=tc
    )


def x__prepare_one__mutmut_131(ctx: AgentContext, tc: dict) -> PreparedToolCall | _PrepFailure:
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
        return _reject(tc_id, name, args, None, validation.reason)

    try:
        spec = registry.tool_spec_for_call(tc_id, name, args)
    except KeyError:
        return _reject(
            tc_id, name, args, "metadata", f"failed to build tool metadata for {name!r}"
        )

    return PreparedToolCall(
        call_id=tc_id, name=name, args=args, spec=spec, original_call=tc
    )


def x__prepare_one__mutmut_132(ctx: AgentContext, tc: dict) -> PreparedToolCall | _PrepFailure:
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
        return _reject(tc_id, name, args, "schema", None)

    try:
        spec = registry.tool_spec_for_call(tc_id, name, args)
    except KeyError:
        return _reject(
            tc_id, name, args, "metadata", f"failed to build tool metadata for {name!r}"
        )

    return PreparedToolCall(
        call_id=tc_id, name=name, args=args, spec=spec, original_call=tc
    )


def x__prepare_one__mutmut_133(ctx: AgentContext, tc: dict) -> PreparedToolCall | _PrepFailure:
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
        return _reject(name, args, "schema", validation.reason)

    try:
        spec = registry.tool_spec_for_call(tc_id, name, args)
    except KeyError:
        return _reject(
            tc_id, name, args, "metadata", f"failed to build tool metadata for {name!r}"
        )

    return PreparedToolCall(
        call_id=tc_id, name=name, args=args, spec=spec, original_call=tc
    )


def x__prepare_one__mutmut_134(ctx: AgentContext, tc: dict) -> PreparedToolCall | _PrepFailure:
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
        return _reject(tc_id, args, "schema", validation.reason)

    try:
        spec = registry.tool_spec_for_call(tc_id, name, args)
    except KeyError:
        return _reject(
            tc_id, name, args, "metadata", f"failed to build tool metadata for {name!r}"
        )

    return PreparedToolCall(
        call_id=tc_id, name=name, args=args, spec=spec, original_call=tc
    )


def x__prepare_one__mutmut_135(ctx: AgentContext, tc: dict) -> PreparedToolCall | _PrepFailure:
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
        return _reject(tc_id, name, "schema", validation.reason)

    try:
        spec = registry.tool_spec_for_call(tc_id, name, args)
    except KeyError:
        return _reject(
            tc_id, name, args, "metadata", f"failed to build tool metadata for {name!r}"
        )

    return PreparedToolCall(
        call_id=tc_id, name=name, args=args, spec=spec, original_call=tc
    )


def x__prepare_one__mutmut_136(ctx: AgentContext, tc: dict) -> PreparedToolCall | _PrepFailure:
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
        return _reject(tc_id, name, args, validation.reason)

    try:
        spec = registry.tool_spec_for_call(tc_id, name, args)
    except KeyError:
        return _reject(
            tc_id, name, args, "metadata", f"failed to build tool metadata for {name!r}"
        )

    return PreparedToolCall(
        call_id=tc_id, name=name, args=args, spec=spec, original_call=tc
    )


def x__prepare_one__mutmut_137(ctx: AgentContext, tc: dict) -> PreparedToolCall | _PrepFailure:
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
        return _reject(tc_id, name, args, "schema", )

    try:
        spec = registry.tool_spec_for_call(tc_id, name, args)
    except KeyError:
        return _reject(
            tc_id, name, args, "metadata", f"failed to build tool metadata for {name!r}"
        )

    return PreparedToolCall(
        call_id=tc_id, name=name, args=args, spec=spec, original_call=tc
    )


def x__prepare_one__mutmut_138(ctx: AgentContext, tc: dict) -> PreparedToolCall | _PrepFailure:
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
        return _reject(tc_id, name, args, "XXschemaXX", validation.reason)

    try:
        spec = registry.tool_spec_for_call(tc_id, name, args)
    except KeyError:
        return _reject(
            tc_id, name, args, "metadata", f"failed to build tool metadata for {name!r}"
        )

    return PreparedToolCall(
        call_id=tc_id, name=name, args=args, spec=spec, original_call=tc
    )


def x__prepare_one__mutmut_139(ctx: AgentContext, tc: dict) -> PreparedToolCall | _PrepFailure:
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
        return _reject(tc_id, name, args, "SCHEMA", validation.reason)

    try:
        spec = registry.tool_spec_for_call(tc_id, name, args)
    except KeyError:
        return _reject(
            tc_id, name, args, "metadata", f"failed to build tool metadata for {name!r}"
        )

    return PreparedToolCall(
        call_id=tc_id, name=name, args=args, spec=spec, original_call=tc
    )


def x__prepare_one__mutmut_140(ctx: AgentContext, tc: dict) -> PreparedToolCall | _PrepFailure:
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
        spec = None
    except KeyError:
        return _reject(
            tc_id, name, args, "metadata", f"failed to build tool metadata for {name!r}"
        )

    return PreparedToolCall(
        call_id=tc_id, name=name, args=args, spec=spec, original_call=tc
    )


def x__prepare_one__mutmut_141(ctx: AgentContext, tc: dict) -> PreparedToolCall | _PrepFailure:
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
        spec = registry.tool_spec_for_call(None, name, args)
    except KeyError:
        return _reject(
            tc_id, name, args, "metadata", f"failed to build tool metadata for {name!r}"
        )

    return PreparedToolCall(
        call_id=tc_id, name=name, args=args, spec=spec, original_call=tc
    )


def x__prepare_one__mutmut_142(ctx: AgentContext, tc: dict) -> PreparedToolCall | _PrepFailure:
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
        spec = registry.tool_spec_for_call(tc_id, None, args)
    except KeyError:
        return _reject(
            tc_id, name, args, "metadata", f"failed to build tool metadata for {name!r}"
        )

    return PreparedToolCall(
        call_id=tc_id, name=name, args=args, spec=spec, original_call=tc
    )


def x__prepare_one__mutmut_143(ctx: AgentContext, tc: dict) -> PreparedToolCall | _PrepFailure:
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
        spec = registry.tool_spec_for_call(tc_id, name, None)
    except KeyError:
        return _reject(
            tc_id, name, args, "metadata", f"failed to build tool metadata for {name!r}"
        )

    return PreparedToolCall(
        call_id=tc_id, name=name, args=args, spec=spec, original_call=tc
    )


def x__prepare_one__mutmut_144(ctx: AgentContext, tc: dict) -> PreparedToolCall | _PrepFailure:
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
        spec = registry.tool_spec_for_call(name, args)
    except KeyError:
        return _reject(
            tc_id, name, args, "metadata", f"failed to build tool metadata for {name!r}"
        )

    return PreparedToolCall(
        call_id=tc_id, name=name, args=args, spec=spec, original_call=tc
    )


def x__prepare_one__mutmut_145(ctx: AgentContext, tc: dict) -> PreparedToolCall | _PrepFailure:
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
        spec = registry.tool_spec_for_call(tc_id, args)
    except KeyError:
        return _reject(
            tc_id, name, args, "metadata", f"failed to build tool metadata for {name!r}"
        )

    return PreparedToolCall(
        call_id=tc_id, name=name, args=args, spec=spec, original_call=tc
    )


def x__prepare_one__mutmut_146(ctx: AgentContext, tc: dict) -> PreparedToolCall | _PrepFailure:
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
        spec = registry.tool_spec_for_call(tc_id, name, )
    except KeyError:
        return _reject(
            tc_id, name, args, "metadata", f"failed to build tool metadata for {name!r}"
        )

    return PreparedToolCall(
        call_id=tc_id, name=name, args=args, spec=spec, original_call=tc
    )


def x__prepare_one__mutmut_147(ctx: AgentContext, tc: dict) -> PreparedToolCall | _PrepFailure:
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
            None, name, args, "metadata", f"failed to build tool metadata for {name!r}"
        )

    return PreparedToolCall(
        call_id=tc_id, name=name, args=args, spec=spec, original_call=tc
    )


def x__prepare_one__mutmut_148(ctx: AgentContext, tc: dict) -> PreparedToolCall | _PrepFailure:
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
            tc_id, None, args, "metadata", f"failed to build tool metadata for {name!r}"
        )

    return PreparedToolCall(
        call_id=tc_id, name=name, args=args, spec=spec, original_call=tc
    )


def x__prepare_one__mutmut_149(ctx: AgentContext, tc: dict) -> PreparedToolCall | _PrepFailure:
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
            tc_id, name, None, "metadata", f"failed to build tool metadata for {name!r}"
        )

    return PreparedToolCall(
        call_id=tc_id, name=name, args=args, spec=spec, original_call=tc
    )


def x__prepare_one__mutmut_150(ctx: AgentContext, tc: dict) -> PreparedToolCall | _PrepFailure:
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
            tc_id, name, args, None, f"failed to build tool metadata for {name!r}"
        )

    return PreparedToolCall(
        call_id=tc_id, name=name, args=args, spec=spec, original_call=tc
    )


def x__prepare_one__mutmut_151(ctx: AgentContext, tc: dict) -> PreparedToolCall | _PrepFailure:
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
            tc_id, name, args, "metadata", None
        )

    return PreparedToolCall(
        call_id=tc_id, name=name, args=args, spec=spec, original_call=tc
    )


def x__prepare_one__mutmut_152(ctx: AgentContext, tc: dict) -> PreparedToolCall | _PrepFailure:
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
            name, args, "metadata", f"failed to build tool metadata for {name!r}"
        )

    return PreparedToolCall(
        call_id=tc_id, name=name, args=args, spec=spec, original_call=tc
    )


def x__prepare_one__mutmut_153(ctx: AgentContext, tc: dict) -> PreparedToolCall | _PrepFailure:
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
            tc_id, args, "metadata", f"failed to build tool metadata for {name!r}"
        )

    return PreparedToolCall(
        call_id=tc_id, name=name, args=args, spec=spec, original_call=tc
    )


def x__prepare_one__mutmut_154(ctx: AgentContext, tc: dict) -> PreparedToolCall | _PrepFailure:
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
            tc_id, name, "metadata", f"failed to build tool metadata for {name!r}"
        )

    return PreparedToolCall(
        call_id=tc_id, name=name, args=args, spec=spec, original_call=tc
    )


def x__prepare_one__mutmut_155(ctx: AgentContext, tc: dict) -> PreparedToolCall | _PrepFailure:
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
            tc_id, name, args, f"failed to build tool metadata for {name!r}"
        )

    return PreparedToolCall(
        call_id=tc_id, name=name, args=args, spec=spec, original_call=tc
    )


def x__prepare_one__mutmut_156(ctx: AgentContext, tc: dict) -> PreparedToolCall | _PrepFailure:
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
            tc_id, name, args, "metadata", )

    return PreparedToolCall(
        call_id=tc_id, name=name, args=args, spec=spec, original_call=tc
    )


def x__prepare_one__mutmut_157(ctx: AgentContext, tc: dict) -> PreparedToolCall | _PrepFailure:
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
            tc_id, name, args, "XXmetadataXX", f"failed to build tool metadata for {name!r}"
        )

    return PreparedToolCall(
        call_id=tc_id, name=name, args=args, spec=spec, original_call=tc
    )


def x__prepare_one__mutmut_158(ctx: AgentContext, tc: dict) -> PreparedToolCall | _PrepFailure:
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
            tc_id, name, args, "METADATA", f"failed to build tool metadata for {name!r}"
        )

    return PreparedToolCall(
        call_id=tc_id, name=name, args=args, spec=spec, original_call=tc
    )


def x__prepare_one__mutmut_159(ctx: AgentContext, tc: dict) -> PreparedToolCall | _PrepFailure:
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
        call_id=None, name=name, args=args, spec=spec, original_call=tc
    )


def x__prepare_one__mutmut_160(ctx: AgentContext, tc: dict) -> PreparedToolCall | _PrepFailure:
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
        call_id=tc_id, name=None, args=args, spec=spec, original_call=tc
    )


def x__prepare_one__mutmut_161(ctx: AgentContext, tc: dict) -> PreparedToolCall | _PrepFailure:
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
        call_id=tc_id, name=name, args=None, spec=spec, original_call=tc
    )


def x__prepare_one__mutmut_162(ctx: AgentContext, tc: dict) -> PreparedToolCall | _PrepFailure:
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
        call_id=tc_id, name=name, args=args, spec=None, original_call=tc
    )


def x__prepare_one__mutmut_163(ctx: AgentContext, tc: dict) -> PreparedToolCall | _PrepFailure:
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
        call_id=tc_id, name=name, args=args, spec=spec, original_call=None
    )


def x__prepare_one__mutmut_164(ctx: AgentContext, tc: dict) -> PreparedToolCall | _PrepFailure:
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
        name=name, args=args, spec=spec, original_call=tc
    )


def x__prepare_one__mutmut_165(ctx: AgentContext, tc: dict) -> PreparedToolCall | _PrepFailure:
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
        call_id=tc_id, args=args, spec=spec, original_call=tc
    )


def x__prepare_one__mutmut_166(ctx: AgentContext, tc: dict) -> PreparedToolCall | _PrepFailure:
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
        call_id=tc_id, name=name, spec=spec, original_call=tc
    )


def x__prepare_one__mutmut_167(ctx: AgentContext, tc: dict) -> PreparedToolCall | _PrepFailure:
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
        call_id=tc_id, name=name, args=args, original_call=tc
    )


def x__prepare_one__mutmut_168(ctx: AgentContext, tc: dict) -> PreparedToolCall | _PrepFailure:
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
        call_id=tc_id, name=name, args=args, spec=spec, )

mutants_x__prepare_one__mutmut['_mutmut_orig'] = x__prepare_one__mutmut_orig # type: ignore # mutmut generated
mutants_x__prepare_one__mutmut['x__prepare_one__mutmut_1'] = x__prepare_one__mutmut_1 # type: ignore # mutmut generated
mutants_x__prepare_one__mutmut['x__prepare_one__mutmut_2'] = x__prepare_one__mutmut_2 # type: ignore # mutmut generated
mutants_x__prepare_one__mutmut['x__prepare_one__mutmut_3'] = x__prepare_one__mutmut_3 # type: ignore # mutmut generated
mutants_x__prepare_one__mutmut['x__prepare_one__mutmut_4'] = x__prepare_one__mutmut_4 # type: ignore # mutmut generated
mutants_x__prepare_one__mutmut['x__prepare_one__mutmut_5'] = x__prepare_one__mutmut_5 # type: ignore # mutmut generated
mutants_x__prepare_one__mutmut['x__prepare_one__mutmut_6'] = x__prepare_one__mutmut_6 # type: ignore # mutmut generated
mutants_x__prepare_one__mutmut['x__prepare_one__mutmut_7'] = x__prepare_one__mutmut_7 # type: ignore # mutmut generated
mutants_x__prepare_one__mutmut['x__prepare_one__mutmut_8'] = x__prepare_one__mutmut_8 # type: ignore # mutmut generated
mutants_x__prepare_one__mutmut['x__prepare_one__mutmut_9'] = x__prepare_one__mutmut_9 # type: ignore # mutmut generated
mutants_x__prepare_one__mutmut['x__prepare_one__mutmut_10'] = x__prepare_one__mutmut_10 # type: ignore # mutmut generated
mutants_x__prepare_one__mutmut['x__prepare_one__mutmut_11'] = x__prepare_one__mutmut_11 # type: ignore # mutmut generated
mutants_x__prepare_one__mutmut['x__prepare_one__mutmut_12'] = x__prepare_one__mutmut_12 # type: ignore # mutmut generated
mutants_x__prepare_one__mutmut['x__prepare_one__mutmut_13'] = x__prepare_one__mutmut_13 # type: ignore # mutmut generated
mutants_x__prepare_one__mutmut['x__prepare_one__mutmut_14'] = x__prepare_one__mutmut_14 # type: ignore # mutmut generated
mutants_x__prepare_one__mutmut['x__prepare_one__mutmut_15'] = x__prepare_one__mutmut_15 # type: ignore # mutmut generated
mutants_x__prepare_one__mutmut['x__prepare_one__mutmut_16'] = x__prepare_one__mutmut_16 # type: ignore # mutmut generated
mutants_x__prepare_one__mutmut['x__prepare_one__mutmut_17'] = x__prepare_one__mutmut_17 # type: ignore # mutmut generated
mutants_x__prepare_one__mutmut['x__prepare_one__mutmut_18'] = x__prepare_one__mutmut_18 # type: ignore # mutmut generated
mutants_x__prepare_one__mutmut['x__prepare_one__mutmut_19'] = x__prepare_one__mutmut_19 # type: ignore # mutmut generated
mutants_x__prepare_one__mutmut['x__prepare_one__mutmut_20'] = x__prepare_one__mutmut_20 # type: ignore # mutmut generated
mutants_x__prepare_one__mutmut['x__prepare_one__mutmut_21'] = x__prepare_one__mutmut_21 # type: ignore # mutmut generated
mutants_x__prepare_one__mutmut['x__prepare_one__mutmut_22'] = x__prepare_one__mutmut_22 # type: ignore # mutmut generated
mutants_x__prepare_one__mutmut['x__prepare_one__mutmut_23'] = x__prepare_one__mutmut_23 # type: ignore # mutmut generated
mutants_x__prepare_one__mutmut['x__prepare_one__mutmut_24'] = x__prepare_one__mutmut_24 # type: ignore # mutmut generated
mutants_x__prepare_one__mutmut['x__prepare_one__mutmut_25'] = x__prepare_one__mutmut_25 # type: ignore # mutmut generated
mutants_x__prepare_one__mutmut['x__prepare_one__mutmut_26'] = x__prepare_one__mutmut_26 # type: ignore # mutmut generated
mutants_x__prepare_one__mutmut['x__prepare_one__mutmut_27'] = x__prepare_one__mutmut_27 # type: ignore # mutmut generated
mutants_x__prepare_one__mutmut['x__prepare_one__mutmut_28'] = x__prepare_one__mutmut_28 # type: ignore # mutmut generated
mutants_x__prepare_one__mutmut['x__prepare_one__mutmut_29'] = x__prepare_one__mutmut_29 # type: ignore # mutmut generated
mutants_x__prepare_one__mutmut['x__prepare_one__mutmut_30'] = x__prepare_one__mutmut_30 # type: ignore # mutmut generated
mutants_x__prepare_one__mutmut['x__prepare_one__mutmut_31'] = x__prepare_one__mutmut_31 # type: ignore # mutmut generated
mutants_x__prepare_one__mutmut['x__prepare_one__mutmut_32'] = x__prepare_one__mutmut_32 # type: ignore # mutmut generated
mutants_x__prepare_one__mutmut['x__prepare_one__mutmut_33'] = x__prepare_one__mutmut_33 # type: ignore # mutmut generated
mutants_x__prepare_one__mutmut['x__prepare_one__mutmut_34'] = x__prepare_one__mutmut_34 # type: ignore # mutmut generated
mutants_x__prepare_one__mutmut['x__prepare_one__mutmut_35'] = x__prepare_one__mutmut_35 # type: ignore # mutmut generated
mutants_x__prepare_one__mutmut['x__prepare_one__mutmut_36'] = x__prepare_one__mutmut_36 # type: ignore # mutmut generated
mutants_x__prepare_one__mutmut['x__prepare_one__mutmut_37'] = x__prepare_one__mutmut_37 # type: ignore # mutmut generated
mutants_x__prepare_one__mutmut['x__prepare_one__mutmut_38'] = x__prepare_one__mutmut_38 # type: ignore # mutmut generated
mutants_x__prepare_one__mutmut['x__prepare_one__mutmut_39'] = x__prepare_one__mutmut_39 # type: ignore # mutmut generated
mutants_x__prepare_one__mutmut['x__prepare_one__mutmut_40'] = x__prepare_one__mutmut_40 # type: ignore # mutmut generated
mutants_x__prepare_one__mutmut['x__prepare_one__mutmut_41'] = x__prepare_one__mutmut_41 # type: ignore # mutmut generated
mutants_x__prepare_one__mutmut['x__prepare_one__mutmut_42'] = x__prepare_one__mutmut_42 # type: ignore # mutmut generated
mutants_x__prepare_one__mutmut['x__prepare_one__mutmut_43'] = x__prepare_one__mutmut_43 # type: ignore # mutmut generated
mutants_x__prepare_one__mutmut['x__prepare_one__mutmut_44'] = x__prepare_one__mutmut_44 # type: ignore # mutmut generated
mutants_x__prepare_one__mutmut['x__prepare_one__mutmut_45'] = x__prepare_one__mutmut_45 # type: ignore # mutmut generated
mutants_x__prepare_one__mutmut['x__prepare_one__mutmut_46'] = x__prepare_one__mutmut_46 # type: ignore # mutmut generated
mutants_x__prepare_one__mutmut['x__prepare_one__mutmut_47'] = x__prepare_one__mutmut_47 # type: ignore # mutmut generated
mutants_x__prepare_one__mutmut['x__prepare_one__mutmut_48'] = x__prepare_one__mutmut_48 # type: ignore # mutmut generated
mutants_x__prepare_one__mutmut['x__prepare_one__mutmut_49'] = x__prepare_one__mutmut_49 # type: ignore # mutmut generated
mutants_x__prepare_one__mutmut['x__prepare_one__mutmut_50'] = x__prepare_one__mutmut_50 # type: ignore # mutmut generated
mutants_x__prepare_one__mutmut['x__prepare_one__mutmut_51'] = x__prepare_one__mutmut_51 # type: ignore # mutmut generated
mutants_x__prepare_one__mutmut['x__prepare_one__mutmut_52'] = x__prepare_one__mutmut_52 # type: ignore # mutmut generated
mutants_x__prepare_one__mutmut['x__prepare_one__mutmut_53'] = x__prepare_one__mutmut_53 # type: ignore # mutmut generated
mutants_x__prepare_one__mutmut['x__prepare_one__mutmut_54'] = x__prepare_one__mutmut_54 # type: ignore # mutmut generated
mutants_x__prepare_one__mutmut['x__prepare_one__mutmut_55'] = x__prepare_one__mutmut_55 # type: ignore # mutmut generated
mutants_x__prepare_one__mutmut['x__prepare_one__mutmut_56'] = x__prepare_one__mutmut_56 # type: ignore # mutmut generated
mutants_x__prepare_one__mutmut['x__prepare_one__mutmut_57'] = x__prepare_one__mutmut_57 # type: ignore # mutmut generated
mutants_x__prepare_one__mutmut['x__prepare_one__mutmut_58'] = x__prepare_one__mutmut_58 # type: ignore # mutmut generated
mutants_x__prepare_one__mutmut['x__prepare_one__mutmut_59'] = x__prepare_one__mutmut_59 # type: ignore # mutmut generated
mutants_x__prepare_one__mutmut['x__prepare_one__mutmut_60'] = x__prepare_one__mutmut_60 # type: ignore # mutmut generated
mutants_x__prepare_one__mutmut['x__prepare_one__mutmut_61'] = x__prepare_one__mutmut_61 # type: ignore # mutmut generated
mutants_x__prepare_one__mutmut['x__prepare_one__mutmut_62'] = x__prepare_one__mutmut_62 # type: ignore # mutmut generated
mutants_x__prepare_one__mutmut['x__prepare_one__mutmut_63'] = x__prepare_one__mutmut_63 # type: ignore # mutmut generated
mutants_x__prepare_one__mutmut['x__prepare_one__mutmut_64'] = x__prepare_one__mutmut_64 # type: ignore # mutmut generated
mutants_x__prepare_one__mutmut['x__prepare_one__mutmut_65'] = x__prepare_one__mutmut_65 # type: ignore # mutmut generated
mutants_x__prepare_one__mutmut['x__prepare_one__mutmut_66'] = x__prepare_one__mutmut_66 # type: ignore # mutmut generated
mutants_x__prepare_one__mutmut['x__prepare_one__mutmut_67'] = x__prepare_one__mutmut_67 # type: ignore # mutmut generated
mutants_x__prepare_one__mutmut['x__prepare_one__mutmut_68'] = x__prepare_one__mutmut_68 # type: ignore # mutmut generated
mutants_x__prepare_one__mutmut['x__prepare_one__mutmut_69'] = x__prepare_one__mutmut_69 # type: ignore # mutmut generated
mutants_x__prepare_one__mutmut['x__prepare_one__mutmut_70'] = x__prepare_one__mutmut_70 # type: ignore # mutmut generated
mutants_x__prepare_one__mutmut['x__prepare_one__mutmut_71'] = x__prepare_one__mutmut_71 # type: ignore # mutmut generated
mutants_x__prepare_one__mutmut['x__prepare_one__mutmut_72'] = x__prepare_one__mutmut_72 # type: ignore # mutmut generated
mutants_x__prepare_one__mutmut['x__prepare_one__mutmut_73'] = x__prepare_one__mutmut_73 # type: ignore # mutmut generated
mutants_x__prepare_one__mutmut['x__prepare_one__mutmut_74'] = x__prepare_one__mutmut_74 # type: ignore # mutmut generated
mutants_x__prepare_one__mutmut['x__prepare_one__mutmut_75'] = x__prepare_one__mutmut_75 # type: ignore # mutmut generated
mutants_x__prepare_one__mutmut['x__prepare_one__mutmut_76'] = x__prepare_one__mutmut_76 # type: ignore # mutmut generated
mutants_x__prepare_one__mutmut['x__prepare_one__mutmut_77'] = x__prepare_one__mutmut_77 # type: ignore # mutmut generated
mutants_x__prepare_one__mutmut['x__prepare_one__mutmut_78'] = x__prepare_one__mutmut_78 # type: ignore # mutmut generated
mutants_x__prepare_one__mutmut['x__prepare_one__mutmut_79'] = x__prepare_one__mutmut_79 # type: ignore # mutmut generated
mutants_x__prepare_one__mutmut['x__prepare_one__mutmut_80'] = x__prepare_one__mutmut_80 # type: ignore # mutmut generated
mutants_x__prepare_one__mutmut['x__prepare_one__mutmut_81'] = x__prepare_one__mutmut_81 # type: ignore # mutmut generated
mutants_x__prepare_one__mutmut['x__prepare_one__mutmut_82'] = x__prepare_one__mutmut_82 # type: ignore # mutmut generated
mutants_x__prepare_one__mutmut['x__prepare_one__mutmut_83'] = x__prepare_one__mutmut_83 # type: ignore # mutmut generated
mutants_x__prepare_one__mutmut['x__prepare_one__mutmut_84'] = x__prepare_one__mutmut_84 # type: ignore # mutmut generated
mutants_x__prepare_one__mutmut['x__prepare_one__mutmut_85'] = x__prepare_one__mutmut_85 # type: ignore # mutmut generated
mutants_x__prepare_one__mutmut['x__prepare_one__mutmut_86'] = x__prepare_one__mutmut_86 # type: ignore # mutmut generated
mutants_x__prepare_one__mutmut['x__prepare_one__mutmut_87'] = x__prepare_one__mutmut_87 # type: ignore # mutmut generated
mutants_x__prepare_one__mutmut['x__prepare_one__mutmut_88'] = x__prepare_one__mutmut_88 # type: ignore # mutmut generated
mutants_x__prepare_one__mutmut['x__prepare_one__mutmut_89'] = x__prepare_one__mutmut_89 # type: ignore # mutmut generated
mutants_x__prepare_one__mutmut['x__prepare_one__mutmut_90'] = x__prepare_one__mutmut_90 # type: ignore # mutmut generated
mutants_x__prepare_one__mutmut['x__prepare_one__mutmut_91'] = x__prepare_one__mutmut_91 # type: ignore # mutmut generated
mutants_x__prepare_one__mutmut['x__prepare_one__mutmut_92'] = x__prepare_one__mutmut_92 # type: ignore # mutmut generated
mutants_x__prepare_one__mutmut['x__prepare_one__mutmut_93'] = x__prepare_one__mutmut_93 # type: ignore # mutmut generated
mutants_x__prepare_one__mutmut['x__prepare_one__mutmut_94'] = x__prepare_one__mutmut_94 # type: ignore # mutmut generated
mutants_x__prepare_one__mutmut['x__prepare_one__mutmut_95'] = x__prepare_one__mutmut_95 # type: ignore # mutmut generated
mutants_x__prepare_one__mutmut['x__prepare_one__mutmut_96'] = x__prepare_one__mutmut_96 # type: ignore # mutmut generated
mutants_x__prepare_one__mutmut['x__prepare_one__mutmut_97'] = x__prepare_one__mutmut_97 # type: ignore # mutmut generated
mutants_x__prepare_one__mutmut['x__prepare_one__mutmut_98'] = x__prepare_one__mutmut_98 # type: ignore # mutmut generated
mutants_x__prepare_one__mutmut['x__prepare_one__mutmut_99'] = x__prepare_one__mutmut_99 # type: ignore # mutmut generated
mutants_x__prepare_one__mutmut['x__prepare_one__mutmut_100'] = x__prepare_one__mutmut_100 # type: ignore # mutmut generated
mutants_x__prepare_one__mutmut['x__prepare_one__mutmut_101'] = x__prepare_one__mutmut_101 # type: ignore # mutmut generated
mutants_x__prepare_one__mutmut['x__prepare_one__mutmut_102'] = x__prepare_one__mutmut_102 # type: ignore # mutmut generated
mutants_x__prepare_one__mutmut['x__prepare_one__mutmut_103'] = x__prepare_one__mutmut_103 # type: ignore # mutmut generated
mutants_x__prepare_one__mutmut['x__prepare_one__mutmut_104'] = x__prepare_one__mutmut_104 # type: ignore # mutmut generated
mutants_x__prepare_one__mutmut['x__prepare_one__mutmut_105'] = x__prepare_one__mutmut_105 # type: ignore # mutmut generated
mutants_x__prepare_one__mutmut['x__prepare_one__mutmut_106'] = x__prepare_one__mutmut_106 # type: ignore # mutmut generated
mutants_x__prepare_one__mutmut['x__prepare_one__mutmut_107'] = x__prepare_one__mutmut_107 # type: ignore # mutmut generated
mutants_x__prepare_one__mutmut['x__prepare_one__mutmut_108'] = x__prepare_one__mutmut_108 # type: ignore # mutmut generated
mutants_x__prepare_one__mutmut['x__prepare_one__mutmut_109'] = x__prepare_one__mutmut_109 # type: ignore # mutmut generated
mutants_x__prepare_one__mutmut['x__prepare_one__mutmut_110'] = x__prepare_one__mutmut_110 # type: ignore # mutmut generated
mutants_x__prepare_one__mutmut['x__prepare_one__mutmut_111'] = x__prepare_one__mutmut_111 # type: ignore # mutmut generated
mutants_x__prepare_one__mutmut['x__prepare_one__mutmut_112'] = x__prepare_one__mutmut_112 # type: ignore # mutmut generated
mutants_x__prepare_one__mutmut['x__prepare_one__mutmut_113'] = x__prepare_one__mutmut_113 # type: ignore # mutmut generated
mutants_x__prepare_one__mutmut['x__prepare_one__mutmut_114'] = x__prepare_one__mutmut_114 # type: ignore # mutmut generated
mutants_x__prepare_one__mutmut['x__prepare_one__mutmut_115'] = x__prepare_one__mutmut_115 # type: ignore # mutmut generated
mutants_x__prepare_one__mutmut['x__prepare_one__mutmut_116'] = x__prepare_one__mutmut_116 # type: ignore # mutmut generated
mutants_x__prepare_one__mutmut['x__prepare_one__mutmut_117'] = x__prepare_one__mutmut_117 # type: ignore # mutmut generated
mutants_x__prepare_one__mutmut['x__prepare_one__mutmut_118'] = x__prepare_one__mutmut_118 # type: ignore # mutmut generated
mutants_x__prepare_one__mutmut['x__prepare_one__mutmut_119'] = x__prepare_one__mutmut_119 # type: ignore # mutmut generated
mutants_x__prepare_one__mutmut['x__prepare_one__mutmut_120'] = x__prepare_one__mutmut_120 # type: ignore # mutmut generated
mutants_x__prepare_one__mutmut['x__prepare_one__mutmut_121'] = x__prepare_one__mutmut_121 # type: ignore # mutmut generated
mutants_x__prepare_one__mutmut['x__prepare_one__mutmut_122'] = x__prepare_one__mutmut_122 # type: ignore # mutmut generated
mutants_x__prepare_one__mutmut['x__prepare_one__mutmut_123'] = x__prepare_one__mutmut_123 # type: ignore # mutmut generated
mutants_x__prepare_one__mutmut['x__prepare_one__mutmut_124'] = x__prepare_one__mutmut_124 # type: ignore # mutmut generated
mutants_x__prepare_one__mutmut['x__prepare_one__mutmut_125'] = x__prepare_one__mutmut_125 # type: ignore # mutmut generated
mutants_x__prepare_one__mutmut['x__prepare_one__mutmut_126'] = x__prepare_one__mutmut_126 # type: ignore # mutmut generated
mutants_x__prepare_one__mutmut['x__prepare_one__mutmut_127'] = x__prepare_one__mutmut_127 # type: ignore # mutmut generated
mutants_x__prepare_one__mutmut['x__prepare_one__mutmut_128'] = x__prepare_one__mutmut_128 # type: ignore # mutmut generated
mutants_x__prepare_one__mutmut['x__prepare_one__mutmut_129'] = x__prepare_one__mutmut_129 # type: ignore # mutmut generated
mutants_x__prepare_one__mutmut['x__prepare_one__mutmut_130'] = x__prepare_one__mutmut_130 # type: ignore # mutmut generated
mutants_x__prepare_one__mutmut['x__prepare_one__mutmut_131'] = x__prepare_one__mutmut_131 # type: ignore # mutmut generated
mutants_x__prepare_one__mutmut['x__prepare_one__mutmut_132'] = x__prepare_one__mutmut_132 # type: ignore # mutmut generated
mutants_x__prepare_one__mutmut['x__prepare_one__mutmut_133'] = x__prepare_one__mutmut_133 # type: ignore # mutmut generated
mutants_x__prepare_one__mutmut['x__prepare_one__mutmut_134'] = x__prepare_one__mutmut_134 # type: ignore # mutmut generated
mutants_x__prepare_one__mutmut['x__prepare_one__mutmut_135'] = x__prepare_one__mutmut_135 # type: ignore # mutmut generated
mutants_x__prepare_one__mutmut['x__prepare_one__mutmut_136'] = x__prepare_one__mutmut_136 # type: ignore # mutmut generated
mutants_x__prepare_one__mutmut['x__prepare_one__mutmut_137'] = x__prepare_one__mutmut_137 # type: ignore # mutmut generated
mutants_x__prepare_one__mutmut['x__prepare_one__mutmut_138'] = x__prepare_one__mutmut_138 # type: ignore # mutmut generated
mutants_x__prepare_one__mutmut['x__prepare_one__mutmut_139'] = x__prepare_one__mutmut_139 # type: ignore # mutmut generated
mutants_x__prepare_one__mutmut['x__prepare_one__mutmut_140'] = x__prepare_one__mutmut_140 # type: ignore # mutmut generated
mutants_x__prepare_one__mutmut['x__prepare_one__mutmut_141'] = x__prepare_one__mutmut_141 # type: ignore # mutmut generated
mutants_x__prepare_one__mutmut['x__prepare_one__mutmut_142'] = x__prepare_one__mutmut_142 # type: ignore # mutmut generated
mutants_x__prepare_one__mutmut['x__prepare_one__mutmut_143'] = x__prepare_one__mutmut_143 # type: ignore # mutmut generated
mutants_x__prepare_one__mutmut['x__prepare_one__mutmut_144'] = x__prepare_one__mutmut_144 # type: ignore # mutmut generated
mutants_x__prepare_one__mutmut['x__prepare_one__mutmut_145'] = x__prepare_one__mutmut_145 # type: ignore # mutmut generated
mutants_x__prepare_one__mutmut['x__prepare_one__mutmut_146'] = x__prepare_one__mutmut_146 # type: ignore # mutmut generated
mutants_x__prepare_one__mutmut['x__prepare_one__mutmut_147'] = x__prepare_one__mutmut_147 # type: ignore # mutmut generated
mutants_x__prepare_one__mutmut['x__prepare_one__mutmut_148'] = x__prepare_one__mutmut_148 # type: ignore # mutmut generated
mutants_x__prepare_one__mutmut['x__prepare_one__mutmut_149'] = x__prepare_one__mutmut_149 # type: ignore # mutmut generated
mutants_x__prepare_one__mutmut['x__prepare_one__mutmut_150'] = x__prepare_one__mutmut_150 # type: ignore # mutmut generated
mutants_x__prepare_one__mutmut['x__prepare_one__mutmut_151'] = x__prepare_one__mutmut_151 # type: ignore # mutmut generated
mutants_x__prepare_one__mutmut['x__prepare_one__mutmut_152'] = x__prepare_one__mutmut_152 # type: ignore # mutmut generated
mutants_x__prepare_one__mutmut['x__prepare_one__mutmut_153'] = x__prepare_one__mutmut_153 # type: ignore # mutmut generated
mutants_x__prepare_one__mutmut['x__prepare_one__mutmut_154'] = x__prepare_one__mutmut_154 # type: ignore # mutmut generated
mutants_x__prepare_one__mutmut['x__prepare_one__mutmut_155'] = x__prepare_one__mutmut_155 # type: ignore # mutmut generated
mutants_x__prepare_one__mutmut['x__prepare_one__mutmut_156'] = x__prepare_one__mutmut_156 # type: ignore # mutmut generated
mutants_x__prepare_one__mutmut['x__prepare_one__mutmut_157'] = x__prepare_one__mutmut_157 # type: ignore # mutmut generated
mutants_x__prepare_one__mutmut['x__prepare_one__mutmut_158'] = x__prepare_one__mutmut_158 # type: ignore # mutmut generated
mutants_x__prepare_one__mutmut['x__prepare_one__mutmut_159'] = x__prepare_one__mutmut_159 # type: ignore # mutmut generated
mutants_x__prepare_one__mutmut['x__prepare_one__mutmut_160'] = x__prepare_one__mutmut_160 # type: ignore # mutmut generated
mutants_x__prepare_one__mutmut['x__prepare_one__mutmut_161'] = x__prepare_one__mutmut_161 # type: ignore # mutmut generated
mutants_x__prepare_one__mutmut['x__prepare_one__mutmut_162'] = x__prepare_one__mutmut_162 # type: ignore # mutmut generated
mutants_x__prepare_one__mutmut['x__prepare_one__mutmut_163'] = x__prepare_one__mutmut_163 # type: ignore # mutmut generated
mutants_x__prepare_one__mutmut['x__prepare_one__mutmut_164'] = x__prepare_one__mutmut_164 # type: ignore # mutmut generated
mutants_x__prepare_one__mutmut['x__prepare_one__mutmut_165'] = x__prepare_one__mutmut_165 # type: ignore # mutmut generated
mutants_x__prepare_one__mutmut['x__prepare_one__mutmut_166'] = x__prepare_one__mutmut_166 # type: ignore # mutmut generated
mutants_x__prepare_one__mutmut['x__prepare_one__mutmut_167'] = x__prepare_one__mutmut_167 # type: ignore # mutmut generated
mutants_x__prepare_one__mutmut['x__prepare_one__mutmut_168'] = x__prepare_one__mutmut_168 # type: ignore # mutmut generated
mutants_x_prepare_tool_calls__mutmut: MutantDict = {}  # type: ignore


@_mutmut_mutated(mutants_x_prepare_tool_calls__mutmut)
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


def x_prepare_tool_calls__mutmut_orig(
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


def x_prepare_tool_calls__mutmut_1(
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
    prepared: list[PreparedToolCall] = None
    failures: list[_PrepFailure] = []
    for tc in tool_calls:
        outcome = _prepare_one(ctx, tc)
        if isinstance(outcome, PreparedToolCall):
            prepared.append(outcome)
        else:
            failures.append(outcome)
    return prepared, failures


def x_prepare_tool_calls__mutmut_2(
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
    failures: list[_PrepFailure] = None
    for tc in tool_calls:
        outcome = _prepare_one(ctx, tc)
        if isinstance(outcome, PreparedToolCall):
            prepared.append(outcome)
        else:
            failures.append(outcome)
    return prepared, failures


def x_prepare_tool_calls__mutmut_3(
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
        outcome = None
        if isinstance(outcome, PreparedToolCall):
            prepared.append(outcome)
        else:
            failures.append(outcome)
    return prepared, failures


def x_prepare_tool_calls__mutmut_4(
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
        outcome = _prepare_one(None, tc)
        if isinstance(outcome, PreparedToolCall):
            prepared.append(outcome)
        else:
            failures.append(outcome)
    return prepared, failures


def x_prepare_tool_calls__mutmut_5(
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
        outcome = _prepare_one(ctx, None)
        if isinstance(outcome, PreparedToolCall):
            prepared.append(outcome)
        else:
            failures.append(outcome)
    return prepared, failures


def x_prepare_tool_calls__mutmut_6(
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
        outcome = _prepare_one(tc)
        if isinstance(outcome, PreparedToolCall):
            prepared.append(outcome)
        else:
            failures.append(outcome)
    return prepared, failures


def x_prepare_tool_calls__mutmut_7(
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
        outcome = _prepare_one(ctx, )
        if isinstance(outcome, PreparedToolCall):
            prepared.append(outcome)
        else:
            failures.append(outcome)
    return prepared, failures


def x_prepare_tool_calls__mutmut_8(
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
            prepared.append(None)
        else:
            failures.append(outcome)
    return prepared, failures


def x_prepare_tool_calls__mutmut_9(
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
            failures.append(None)
    return prepared, failures

mutants_x_prepare_tool_calls__mutmut['_mutmut_orig'] = x_prepare_tool_calls__mutmut_orig # type: ignore # mutmut generated
mutants_x_prepare_tool_calls__mutmut['x_prepare_tool_calls__mutmut_1'] = x_prepare_tool_calls__mutmut_1 # type: ignore # mutmut generated
mutants_x_prepare_tool_calls__mutmut['x_prepare_tool_calls__mutmut_2'] = x_prepare_tool_calls__mutmut_2 # type: ignore # mutmut generated
mutants_x_prepare_tool_calls__mutmut['x_prepare_tool_calls__mutmut_3'] = x_prepare_tool_calls__mutmut_3 # type: ignore # mutmut generated
mutants_x_prepare_tool_calls__mutmut['x_prepare_tool_calls__mutmut_4'] = x_prepare_tool_calls__mutmut_4 # type: ignore # mutmut generated
mutants_x_prepare_tool_calls__mutmut['x_prepare_tool_calls__mutmut_5'] = x_prepare_tool_calls__mutmut_5 # type: ignore # mutmut generated
mutants_x_prepare_tool_calls__mutmut['x_prepare_tool_calls__mutmut_6'] = x_prepare_tool_calls__mutmut_6 # type: ignore # mutmut generated
mutants_x_prepare_tool_calls__mutmut['x_prepare_tool_calls__mutmut_7'] = x_prepare_tool_calls__mutmut_7 # type: ignore # mutmut generated
mutants_x_prepare_tool_calls__mutmut['x_prepare_tool_calls__mutmut_8'] = x_prepare_tool_calls__mutmut_8 # type: ignore # mutmut generated
mutants_x_prepare_tool_calls__mutmut['x_prepare_tool_calls__mutmut_9'] = x_prepare_tool_calls__mutmut_9 # type: ignore # mutmut generated
