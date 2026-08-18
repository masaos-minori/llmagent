#!/usr/bin/env python3
"""scripts/shared/tool_executor_helpers.py — Tool executor helper functions."""

import hashlib
from typing import Any

from shared.json_utils import dumps as _json_dumps
from shared.tool_constants import (
    CICD_WRITE_TOOLS,
    DELETE_TOOLS,
    GIT_WRITE_TOOLS,
    GITHUB_DANGEROUS_TOOLS,
    GITHUB_WRITE_TOOLS,
    MDQ_WRITE_TOOLS,
    RAG_WRITE_TOOLS,
    WRITE_TOOLS,
)
from shared.transport_dto import TransportErrorInfo

# Tools with side effects: writes, deletes, shell, or git/GitHub mutations.
# Used only as the TTL-cache-bypass check in shared/tool_executor.py — it no
# longer drives any batch-level parallel/serial execution decision.
# execute_all_tool_calls() (agent/tool_runner.py) always schedules through
# agent/tool_scheduler.py::build_execution_groups() (requires_serial barriers,
# resource-scope conflicts, and a force_serial input fed from
# ctx.cfg.tool.serial_tool_calls); the separate is_side_effect()-driven batch
# downgrade this module used to back was removed. Do not conflate
# is_side_effect() with ToolSpec.requires_serial (agent/tool_scheduler.py) when
# reasoning about tool-call concurrency.
_SIDE_EFFECT_TOOLS: frozenset[str] = (
    WRITE_TOOLS
    | DELETE_TOOLS
    | frozenset({"shell_run"})
    | GIT_WRITE_TOOLS
    | GITHUB_WRITE_TOOLS
    | GITHUB_DANGEROUS_TOOLS
    | CICD_WRITE_TOOLS
    | RAG_WRITE_TOOLS
    | MDQ_WRITE_TOOLS
)


from mutmut.mutation.trampoline import wrap_in_trampoline as _mutmut_mutated, MutantDict
mutants_x_is_side_effect__mutmut: MutantDict = {}  # type: ignore


@_mutmut_mutated(mutants_x_is_side_effect__mutmut)
def is_side_effect(tool_name: str) -> bool:
    """Return True when the tool modifies state: file write/delete, shell,
    Git write operations, or GitHub write/dangerous operations."""
    return tool_name in _SIDE_EFFECT_TOOLS


def x_is_side_effect__mutmut_orig(tool_name: str) -> bool:
    """Return True when the tool modifies state: file write/delete, shell,
    Git write operations, or GitHub write/dangerous operations."""
    return tool_name in _SIDE_EFFECT_TOOLS


def x_is_side_effect__mutmut_1(tool_name: str) -> bool:
    """Return True when the tool modifies state: file write/delete, shell,
    Git write operations, or GitHub write/dangerous operations."""
    return tool_name not in _SIDE_EFFECT_TOOLS

mutants_x_is_side_effect__mutmut['_mutmut_orig'] = x_is_side_effect__mutmut_orig # type: ignore # mutmut generated
mutants_x_is_side_effect__mutmut['x_is_side_effect__mutmut_1'] = x_is_side_effect__mutmut_1 # type: ignore # mutmut generated
mutants_x_format_transport_error__mutmut: MutantDict = {}  # type: ignore


@_mutmut_mutated(mutants_x_format_transport_error__mutmut)
def format_transport_error(
    *,
    source: str,
    phase: str,
    kind: str,
    url: str,
    status_code: int | None,
    retryable: bool,
    partial: bool,
) -> TransportErrorInfo:
    """Return TransportErrorInfo for LLM/tool transport failures; summary is one-line user-facing; detail is JSON for audit logs."""
    detail = _json_dumps(
        {
            "source": source,
            "phase": phase,
            "kind": kind,
            "status_code": status_code,
            "url": url,
            "retryable": retryable,
            "partial": partial,
        },
    )
    summary = (
        f"[{source.upper()} {kind}] {phase} failure "
        f"(status_code={status_code}, retryable={retryable}, partial={partial})"
    )
    return TransportErrorInfo(summary=summary, detail=detail)


def x_format_transport_error__mutmut_orig(
    *,
    source: str,
    phase: str,
    kind: str,
    url: str,
    status_code: int | None,
    retryable: bool,
    partial: bool,
) -> TransportErrorInfo:
    """Return TransportErrorInfo for LLM/tool transport failures; summary is one-line user-facing; detail is JSON for audit logs."""
    detail = _json_dumps(
        {
            "source": source,
            "phase": phase,
            "kind": kind,
            "status_code": status_code,
            "url": url,
            "retryable": retryable,
            "partial": partial,
        },
    )
    summary = (
        f"[{source.upper()} {kind}] {phase} failure "
        f"(status_code={status_code}, retryable={retryable}, partial={partial})"
    )
    return TransportErrorInfo(summary=summary, detail=detail)


def x_format_transport_error__mutmut_1(
    *,
    source: str,
    phase: str,
    kind: str,
    url: str,
    status_code: int | None,
    retryable: bool,
    partial: bool,
) -> TransportErrorInfo:
    """Return TransportErrorInfo for LLM/tool transport failures; summary is one-line user-facing; detail is JSON for audit logs."""
    detail = None
    summary = (
        f"[{source.upper()} {kind}] {phase} failure "
        f"(status_code={status_code}, retryable={retryable}, partial={partial})"
    )
    return TransportErrorInfo(summary=summary, detail=detail)


def x_format_transport_error__mutmut_2(
    *,
    source: str,
    phase: str,
    kind: str,
    url: str,
    status_code: int | None,
    retryable: bool,
    partial: bool,
) -> TransportErrorInfo:
    """Return TransportErrorInfo for LLM/tool transport failures; summary is one-line user-facing; detail is JSON for audit logs."""
    detail = _json_dumps(
        None,
    )
    summary = (
        f"[{source.upper()} {kind}] {phase} failure "
        f"(status_code={status_code}, retryable={retryable}, partial={partial})"
    )
    return TransportErrorInfo(summary=summary, detail=detail)


def x_format_transport_error__mutmut_3(
    *,
    source: str,
    phase: str,
    kind: str,
    url: str,
    status_code: int | None,
    retryable: bool,
    partial: bool,
) -> TransportErrorInfo:
    """Return TransportErrorInfo for LLM/tool transport failures; summary is one-line user-facing; detail is JSON for audit logs."""
    detail = _json_dumps(
        {
            "XXsourceXX": source,
            "phase": phase,
            "kind": kind,
            "status_code": status_code,
            "url": url,
            "retryable": retryable,
            "partial": partial,
        },
    )
    summary = (
        f"[{source.upper()} {kind}] {phase} failure "
        f"(status_code={status_code}, retryable={retryable}, partial={partial})"
    )
    return TransportErrorInfo(summary=summary, detail=detail)


def x_format_transport_error__mutmut_4(
    *,
    source: str,
    phase: str,
    kind: str,
    url: str,
    status_code: int | None,
    retryable: bool,
    partial: bool,
) -> TransportErrorInfo:
    """Return TransportErrorInfo for LLM/tool transport failures; summary is one-line user-facing; detail is JSON for audit logs."""
    detail = _json_dumps(
        {
            "SOURCE": source,
            "phase": phase,
            "kind": kind,
            "status_code": status_code,
            "url": url,
            "retryable": retryable,
            "partial": partial,
        },
    )
    summary = (
        f"[{source.upper()} {kind}] {phase} failure "
        f"(status_code={status_code}, retryable={retryable}, partial={partial})"
    )
    return TransportErrorInfo(summary=summary, detail=detail)


def x_format_transport_error__mutmut_5(
    *,
    source: str,
    phase: str,
    kind: str,
    url: str,
    status_code: int | None,
    retryable: bool,
    partial: bool,
) -> TransportErrorInfo:
    """Return TransportErrorInfo for LLM/tool transport failures; summary is one-line user-facing; detail is JSON for audit logs."""
    detail = _json_dumps(
        {
            "source": source,
            "XXphaseXX": phase,
            "kind": kind,
            "status_code": status_code,
            "url": url,
            "retryable": retryable,
            "partial": partial,
        },
    )
    summary = (
        f"[{source.upper()} {kind}] {phase} failure "
        f"(status_code={status_code}, retryable={retryable}, partial={partial})"
    )
    return TransportErrorInfo(summary=summary, detail=detail)


def x_format_transport_error__mutmut_6(
    *,
    source: str,
    phase: str,
    kind: str,
    url: str,
    status_code: int | None,
    retryable: bool,
    partial: bool,
) -> TransportErrorInfo:
    """Return TransportErrorInfo for LLM/tool transport failures; summary is one-line user-facing; detail is JSON for audit logs."""
    detail = _json_dumps(
        {
            "source": source,
            "PHASE": phase,
            "kind": kind,
            "status_code": status_code,
            "url": url,
            "retryable": retryable,
            "partial": partial,
        },
    )
    summary = (
        f"[{source.upper()} {kind}] {phase} failure "
        f"(status_code={status_code}, retryable={retryable}, partial={partial})"
    )
    return TransportErrorInfo(summary=summary, detail=detail)


def x_format_transport_error__mutmut_7(
    *,
    source: str,
    phase: str,
    kind: str,
    url: str,
    status_code: int | None,
    retryable: bool,
    partial: bool,
) -> TransportErrorInfo:
    """Return TransportErrorInfo for LLM/tool transport failures; summary is one-line user-facing; detail is JSON for audit logs."""
    detail = _json_dumps(
        {
            "source": source,
            "phase": phase,
            "XXkindXX": kind,
            "status_code": status_code,
            "url": url,
            "retryable": retryable,
            "partial": partial,
        },
    )
    summary = (
        f"[{source.upper()} {kind}] {phase} failure "
        f"(status_code={status_code}, retryable={retryable}, partial={partial})"
    )
    return TransportErrorInfo(summary=summary, detail=detail)


def x_format_transport_error__mutmut_8(
    *,
    source: str,
    phase: str,
    kind: str,
    url: str,
    status_code: int | None,
    retryable: bool,
    partial: bool,
) -> TransportErrorInfo:
    """Return TransportErrorInfo for LLM/tool transport failures; summary is one-line user-facing; detail is JSON for audit logs."""
    detail = _json_dumps(
        {
            "source": source,
            "phase": phase,
            "KIND": kind,
            "status_code": status_code,
            "url": url,
            "retryable": retryable,
            "partial": partial,
        },
    )
    summary = (
        f"[{source.upper()} {kind}] {phase} failure "
        f"(status_code={status_code}, retryable={retryable}, partial={partial})"
    )
    return TransportErrorInfo(summary=summary, detail=detail)


def x_format_transport_error__mutmut_9(
    *,
    source: str,
    phase: str,
    kind: str,
    url: str,
    status_code: int | None,
    retryable: bool,
    partial: bool,
) -> TransportErrorInfo:
    """Return TransportErrorInfo for LLM/tool transport failures; summary is one-line user-facing; detail is JSON for audit logs."""
    detail = _json_dumps(
        {
            "source": source,
            "phase": phase,
            "kind": kind,
            "XXstatus_codeXX": status_code,
            "url": url,
            "retryable": retryable,
            "partial": partial,
        },
    )
    summary = (
        f"[{source.upper()} {kind}] {phase} failure "
        f"(status_code={status_code}, retryable={retryable}, partial={partial})"
    )
    return TransportErrorInfo(summary=summary, detail=detail)


def x_format_transport_error__mutmut_10(
    *,
    source: str,
    phase: str,
    kind: str,
    url: str,
    status_code: int | None,
    retryable: bool,
    partial: bool,
) -> TransportErrorInfo:
    """Return TransportErrorInfo for LLM/tool transport failures; summary is one-line user-facing; detail is JSON for audit logs."""
    detail = _json_dumps(
        {
            "source": source,
            "phase": phase,
            "kind": kind,
            "STATUS_CODE": status_code,
            "url": url,
            "retryable": retryable,
            "partial": partial,
        },
    )
    summary = (
        f"[{source.upper()} {kind}] {phase} failure "
        f"(status_code={status_code}, retryable={retryable}, partial={partial})"
    )
    return TransportErrorInfo(summary=summary, detail=detail)


def x_format_transport_error__mutmut_11(
    *,
    source: str,
    phase: str,
    kind: str,
    url: str,
    status_code: int | None,
    retryable: bool,
    partial: bool,
) -> TransportErrorInfo:
    """Return TransportErrorInfo for LLM/tool transport failures; summary is one-line user-facing; detail is JSON for audit logs."""
    detail = _json_dumps(
        {
            "source": source,
            "phase": phase,
            "kind": kind,
            "status_code": status_code,
            "XXurlXX": url,
            "retryable": retryable,
            "partial": partial,
        },
    )
    summary = (
        f"[{source.upper()} {kind}] {phase} failure "
        f"(status_code={status_code}, retryable={retryable}, partial={partial})"
    )
    return TransportErrorInfo(summary=summary, detail=detail)


def x_format_transport_error__mutmut_12(
    *,
    source: str,
    phase: str,
    kind: str,
    url: str,
    status_code: int | None,
    retryable: bool,
    partial: bool,
) -> TransportErrorInfo:
    """Return TransportErrorInfo for LLM/tool transport failures; summary is one-line user-facing; detail is JSON for audit logs."""
    detail = _json_dumps(
        {
            "source": source,
            "phase": phase,
            "kind": kind,
            "status_code": status_code,
            "URL": url,
            "retryable": retryable,
            "partial": partial,
        },
    )
    summary = (
        f"[{source.upper()} {kind}] {phase} failure "
        f"(status_code={status_code}, retryable={retryable}, partial={partial})"
    )
    return TransportErrorInfo(summary=summary, detail=detail)


def x_format_transport_error__mutmut_13(
    *,
    source: str,
    phase: str,
    kind: str,
    url: str,
    status_code: int | None,
    retryable: bool,
    partial: bool,
) -> TransportErrorInfo:
    """Return TransportErrorInfo for LLM/tool transport failures; summary is one-line user-facing; detail is JSON for audit logs."""
    detail = _json_dumps(
        {
            "source": source,
            "phase": phase,
            "kind": kind,
            "status_code": status_code,
            "url": url,
            "XXretryableXX": retryable,
            "partial": partial,
        },
    )
    summary = (
        f"[{source.upper()} {kind}] {phase} failure "
        f"(status_code={status_code}, retryable={retryable}, partial={partial})"
    )
    return TransportErrorInfo(summary=summary, detail=detail)


def x_format_transport_error__mutmut_14(
    *,
    source: str,
    phase: str,
    kind: str,
    url: str,
    status_code: int | None,
    retryable: bool,
    partial: bool,
) -> TransportErrorInfo:
    """Return TransportErrorInfo for LLM/tool transport failures; summary is one-line user-facing; detail is JSON for audit logs."""
    detail = _json_dumps(
        {
            "source": source,
            "phase": phase,
            "kind": kind,
            "status_code": status_code,
            "url": url,
            "RETRYABLE": retryable,
            "partial": partial,
        },
    )
    summary = (
        f"[{source.upper()} {kind}] {phase} failure "
        f"(status_code={status_code}, retryable={retryable}, partial={partial})"
    )
    return TransportErrorInfo(summary=summary, detail=detail)


def x_format_transport_error__mutmut_15(
    *,
    source: str,
    phase: str,
    kind: str,
    url: str,
    status_code: int | None,
    retryable: bool,
    partial: bool,
) -> TransportErrorInfo:
    """Return TransportErrorInfo for LLM/tool transport failures; summary is one-line user-facing; detail is JSON for audit logs."""
    detail = _json_dumps(
        {
            "source": source,
            "phase": phase,
            "kind": kind,
            "status_code": status_code,
            "url": url,
            "retryable": retryable,
            "XXpartialXX": partial,
        },
    )
    summary = (
        f"[{source.upper()} {kind}] {phase} failure "
        f"(status_code={status_code}, retryable={retryable}, partial={partial})"
    )
    return TransportErrorInfo(summary=summary, detail=detail)


def x_format_transport_error__mutmut_16(
    *,
    source: str,
    phase: str,
    kind: str,
    url: str,
    status_code: int | None,
    retryable: bool,
    partial: bool,
) -> TransportErrorInfo:
    """Return TransportErrorInfo for LLM/tool transport failures; summary is one-line user-facing; detail is JSON for audit logs."""
    detail = _json_dumps(
        {
            "source": source,
            "phase": phase,
            "kind": kind,
            "status_code": status_code,
            "url": url,
            "retryable": retryable,
            "PARTIAL": partial,
        },
    )
    summary = (
        f"[{source.upper()} {kind}] {phase} failure "
        f"(status_code={status_code}, retryable={retryable}, partial={partial})"
    )
    return TransportErrorInfo(summary=summary, detail=detail)


def x_format_transport_error__mutmut_17(
    *,
    source: str,
    phase: str,
    kind: str,
    url: str,
    status_code: int | None,
    retryable: bool,
    partial: bool,
) -> TransportErrorInfo:
    """Return TransportErrorInfo for LLM/tool transport failures; summary is one-line user-facing; detail is JSON for audit logs."""
    detail = _json_dumps(
        {
            "source": source,
            "phase": phase,
            "kind": kind,
            "status_code": status_code,
            "url": url,
            "retryable": retryable,
            "partial": partial,
        },
    )
    summary = None
    return TransportErrorInfo(summary=summary, detail=detail)


def x_format_transport_error__mutmut_18(
    *,
    source: str,
    phase: str,
    kind: str,
    url: str,
    status_code: int | None,
    retryable: bool,
    partial: bool,
) -> TransportErrorInfo:
    """Return TransportErrorInfo for LLM/tool transport failures; summary is one-line user-facing; detail is JSON for audit logs."""
    detail = _json_dumps(
        {
            "source": source,
            "phase": phase,
            "kind": kind,
            "status_code": status_code,
            "url": url,
            "retryable": retryable,
            "partial": partial,
        },
    )
    summary = (
        f"[{source.lower()} {kind}] {phase} failure "
        f"(status_code={status_code}, retryable={retryable}, partial={partial})"
    )
    return TransportErrorInfo(summary=summary, detail=detail)


def x_format_transport_error__mutmut_19(
    *,
    source: str,
    phase: str,
    kind: str,
    url: str,
    status_code: int | None,
    retryable: bool,
    partial: bool,
) -> TransportErrorInfo:
    """Return TransportErrorInfo for LLM/tool transport failures; summary is one-line user-facing; detail is JSON for audit logs."""
    detail = _json_dumps(
        {
            "source": source,
            "phase": phase,
            "kind": kind,
            "status_code": status_code,
            "url": url,
            "retryable": retryable,
            "partial": partial,
        },
    )
    summary = (
        f"[{source.upper()} {kind}] {phase} failure "
        f"(status_code={status_code}, retryable={retryable}, partial={partial})"
    )
    return TransportErrorInfo(summary=None, detail=detail)


def x_format_transport_error__mutmut_20(
    *,
    source: str,
    phase: str,
    kind: str,
    url: str,
    status_code: int | None,
    retryable: bool,
    partial: bool,
) -> TransportErrorInfo:
    """Return TransportErrorInfo for LLM/tool transport failures; summary is one-line user-facing; detail is JSON for audit logs."""
    detail = _json_dumps(
        {
            "source": source,
            "phase": phase,
            "kind": kind,
            "status_code": status_code,
            "url": url,
            "retryable": retryable,
            "partial": partial,
        },
    )
    summary = (
        f"[{source.upper()} {kind}] {phase} failure "
        f"(status_code={status_code}, retryable={retryable}, partial={partial})"
    )
    return TransportErrorInfo(summary=summary, detail=None)


def x_format_transport_error__mutmut_21(
    *,
    source: str,
    phase: str,
    kind: str,
    url: str,
    status_code: int | None,
    retryable: bool,
    partial: bool,
) -> TransportErrorInfo:
    """Return TransportErrorInfo for LLM/tool transport failures; summary is one-line user-facing; detail is JSON for audit logs."""
    detail = _json_dumps(
        {
            "source": source,
            "phase": phase,
            "kind": kind,
            "status_code": status_code,
            "url": url,
            "retryable": retryable,
            "partial": partial,
        },
    )
    summary = (
        f"[{source.upper()} {kind}] {phase} failure "
        f"(status_code={status_code}, retryable={retryable}, partial={partial})"
    )
    return TransportErrorInfo(detail=detail)


def x_format_transport_error__mutmut_22(
    *,
    source: str,
    phase: str,
    kind: str,
    url: str,
    status_code: int | None,
    retryable: bool,
    partial: bool,
) -> TransportErrorInfo:
    """Return TransportErrorInfo for LLM/tool transport failures; summary is one-line user-facing; detail is JSON for audit logs."""
    detail = _json_dumps(
        {
            "source": source,
            "phase": phase,
            "kind": kind,
            "status_code": status_code,
            "url": url,
            "retryable": retryable,
            "partial": partial,
        },
    )
    summary = (
        f"[{source.upper()} {kind}] {phase} failure "
        f"(status_code={status_code}, retryable={retryable}, partial={partial})"
    )
    return TransportErrorInfo(summary=summary, )

mutants_x_format_transport_error__mutmut['_mutmut_orig'] = x_format_transport_error__mutmut_orig # type: ignore # mutmut generated
mutants_x_format_transport_error__mutmut['x_format_transport_error__mutmut_1'] = x_format_transport_error__mutmut_1 # type: ignore # mutmut generated
mutants_x_format_transport_error__mutmut['x_format_transport_error__mutmut_2'] = x_format_transport_error__mutmut_2 # type: ignore # mutmut generated
mutants_x_format_transport_error__mutmut['x_format_transport_error__mutmut_3'] = x_format_transport_error__mutmut_3 # type: ignore # mutmut generated
mutants_x_format_transport_error__mutmut['x_format_transport_error__mutmut_4'] = x_format_transport_error__mutmut_4 # type: ignore # mutmut generated
mutants_x_format_transport_error__mutmut['x_format_transport_error__mutmut_5'] = x_format_transport_error__mutmut_5 # type: ignore # mutmut generated
mutants_x_format_transport_error__mutmut['x_format_transport_error__mutmut_6'] = x_format_transport_error__mutmut_6 # type: ignore # mutmut generated
mutants_x_format_transport_error__mutmut['x_format_transport_error__mutmut_7'] = x_format_transport_error__mutmut_7 # type: ignore # mutmut generated
mutants_x_format_transport_error__mutmut['x_format_transport_error__mutmut_8'] = x_format_transport_error__mutmut_8 # type: ignore # mutmut generated
mutants_x_format_transport_error__mutmut['x_format_transport_error__mutmut_9'] = x_format_transport_error__mutmut_9 # type: ignore # mutmut generated
mutants_x_format_transport_error__mutmut['x_format_transport_error__mutmut_10'] = x_format_transport_error__mutmut_10 # type: ignore # mutmut generated
mutants_x_format_transport_error__mutmut['x_format_transport_error__mutmut_11'] = x_format_transport_error__mutmut_11 # type: ignore # mutmut generated
mutants_x_format_transport_error__mutmut['x_format_transport_error__mutmut_12'] = x_format_transport_error__mutmut_12 # type: ignore # mutmut generated
mutants_x_format_transport_error__mutmut['x_format_transport_error__mutmut_13'] = x_format_transport_error__mutmut_13 # type: ignore # mutmut generated
mutants_x_format_transport_error__mutmut['x_format_transport_error__mutmut_14'] = x_format_transport_error__mutmut_14 # type: ignore # mutmut generated
mutants_x_format_transport_error__mutmut['x_format_transport_error__mutmut_15'] = x_format_transport_error__mutmut_15 # type: ignore # mutmut generated
mutants_x_format_transport_error__mutmut['x_format_transport_error__mutmut_16'] = x_format_transport_error__mutmut_16 # type: ignore # mutmut generated
mutants_x_format_transport_error__mutmut['x_format_transport_error__mutmut_17'] = x_format_transport_error__mutmut_17 # type: ignore # mutmut generated
mutants_x_format_transport_error__mutmut['x_format_transport_error__mutmut_18'] = x_format_transport_error__mutmut_18 # type: ignore # mutmut generated
mutants_x_format_transport_error__mutmut['x_format_transport_error__mutmut_19'] = x_format_transport_error__mutmut_19 # type: ignore # mutmut generated
mutants_x_format_transport_error__mutmut['x_format_transport_error__mutmut_20'] = x_format_transport_error__mutmut_20 # type: ignore # mutmut generated
mutants_x_format_transport_error__mutmut['x_format_transport_error__mutmut_21'] = x_format_transport_error__mutmut_21 # type: ignore # mutmut generated
mutants_x_format_transport_error__mutmut['x_format_transport_error__mutmut_22'] = x_format_transport_error__mutmut_22 # type: ignore # mutmut generated
mutants_x_tool_hash_key__mutmut: MutantDict = {}  # type: ignore


@_mutmut_mutated(mutants_x_tool_hash_key__mutmut)
def tool_hash_key(name: str, args: dict[str, Any]) -> str:
    """Return a stable MD5 hash for a (tool name, args) pair; used for failed-call tracking (NOT for cache keys). Cache keys use plain string concatenation: f'{name}:{json_dumps(args)}'."""
    return hashlib.md5(  # nosec B324 — non-security hash for dedup key identity
        f"{name}:{_json_dumps(args)}".encode(),
        usedforsecurity=False,
    ).hexdigest()


def x_tool_hash_key__mutmut_orig(name: str, args: dict[str, Any]) -> str:
    """Return a stable MD5 hash for a (tool name, args) pair; used for failed-call tracking (NOT for cache keys). Cache keys use plain string concatenation: f'{name}:{json_dumps(args)}'."""
    return hashlib.md5(  # nosec B324 — non-security hash for dedup key identity
        f"{name}:{_json_dumps(args)}".encode(),
        usedforsecurity=False,
    ).hexdigest()


def x_tool_hash_key__mutmut_1(name: str, args: dict[str, Any]) -> str:
    """Return a stable MD5 hash for a (tool name, args) pair; used for failed-call tracking (NOT for cache keys). Cache keys use plain string concatenation: f'{name}:{json_dumps(args)}'."""
    return hashlib.md5(  # nosec B324 — non-security hash for dedup key identity
        None,
        usedforsecurity=False,
    ).hexdigest()


def x_tool_hash_key__mutmut_2(name: str, args: dict[str, Any]) -> str:
    """Return a stable MD5 hash for a (tool name, args) pair; used for failed-call tracking (NOT for cache keys). Cache keys use plain string concatenation: f'{name}:{json_dumps(args)}'."""
    return hashlib.md5(  # nosec B324 — non-security hash for dedup key identity
        f"{name}:{_json_dumps(args)}".encode(),
        usedforsecurity=None,
    ).hexdigest()


def x_tool_hash_key__mutmut_3(name: str, args: dict[str, Any]) -> str:
    """Return a stable MD5 hash for a (tool name, args) pair; used for failed-call tracking (NOT for cache keys). Cache keys use plain string concatenation: f'{name}:{json_dumps(args)}'."""
    return hashlib.md5(  # nosec B324 — non-security hash for dedup key identity
        usedforsecurity=False,
    ).hexdigest()


def x_tool_hash_key__mutmut_4(name: str, args: dict[str, Any]) -> str:
    """Return a stable MD5 hash for a (tool name, args) pair; used for failed-call tracking (NOT for cache keys). Cache keys use plain string concatenation: f'{name}:{json_dumps(args)}'."""
    return hashlib.md5(  # nosec B324 — non-security hash for dedup key identity
        f"{name}:{_json_dumps(args)}".encode(),
        ).hexdigest()


def x_tool_hash_key__mutmut_5(name: str, args: dict[str, Any]) -> str:
    """Return a stable MD5 hash for a (tool name, args) pair; used for failed-call tracking (NOT for cache keys). Cache keys use plain string concatenation: f'{name}:{json_dumps(args)}'."""
    return hashlib.md5(  # nosec B324 — non-security hash for dedup key identity
        f"{name}:{_json_dumps(None)}".encode(),
        usedforsecurity=False,
    ).hexdigest()


def x_tool_hash_key__mutmut_6(name: str, args: dict[str, Any]) -> str:
    """Return a stable MD5 hash for a (tool name, args) pair; used for failed-call tracking (NOT for cache keys). Cache keys use plain string concatenation: f'{name}:{json_dumps(args)}'."""
    return hashlib.md5(  # nosec B324 — non-security hash for dedup key identity
        f"{name}:{_json_dumps(args)}".encode(),
        usedforsecurity=True,
    ).hexdigest()

mutants_x_tool_hash_key__mutmut['_mutmut_orig'] = x_tool_hash_key__mutmut_orig # type: ignore # mutmut generated
mutants_x_tool_hash_key__mutmut['x_tool_hash_key__mutmut_1'] = x_tool_hash_key__mutmut_1 # type: ignore # mutmut generated
mutants_x_tool_hash_key__mutmut['x_tool_hash_key__mutmut_2'] = x_tool_hash_key__mutmut_2 # type: ignore # mutmut generated
mutants_x_tool_hash_key__mutmut['x_tool_hash_key__mutmut_3'] = x_tool_hash_key__mutmut_3 # type: ignore # mutmut generated
mutants_x_tool_hash_key__mutmut['x_tool_hash_key__mutmut_4'] = x_tool_hash_key__mutmut_4 # type: ignore # mutmut generated
mutants_x_tool_hash_key__mutmut['x_tool_hash_key__mutmut_5'] = x_tool_hash_key__mutmut_5 # type: ignore # mutmut generated
mutants_x_tool_hash_key__mutmut['x_tool_hash_key__mutmut_6'] = x_tool_hash_key__mutmut_6 # type: ignore # mutmut generated
