"""scripts/shared/token_counter.py

Accurate token counting via llamacpp /tokenize endpoint.

Priority:
  1. LLM usage.prompt_tokens (passed as last_input_tokens) — exact
  2. POST /tokenize endpoint   (llamacpp standard API)      — exact
  3. Category-aware estimate                               — estimated

When exact token counts are unavailable (sources 1 and 2), the fallback uses
category-aware estimation with different character-to-token ratios per content
type:

  - Natural language text (user/assistant/tool):   4.0 chars/token
  - Structured JSON (assistant tool_calls):        2.5 chars/token
  - System messages (mixed format):                3.5 chars/token

This is more accurate than a simple ``chars // 4`` heuristic, especially for
multilingual text and structured tool payloads.  The count is marked
``is_exact=False`` to distinguish it from LLM-provided or /tokenize-derived
counts.
"""

import logging

import httpx

from shared.json_utils import (
    dumps as _json_dumps,
)
from shared.json_utils import (
    parse_http_json,
    tool_call_serialized_length,
)
from shared.token_estimation import estimate_tokens
from shared.types import LLMMessage

logger = logging.getLogger(__name__)


from mutmut.mutation.trampoline import wrap_in_trampoline as _mutmut_mutated, MutantDict
mutants_xǁ_WarnOnceǁ__init____mutmut: MutantDict = {}  # type: ignore
mutants_xǁ_WarnOnceǁlog__mutmut: MutantDict = {}  # type: ignore
mutants_xǁ_WarnOnceǁreset__mutmut: MutantDict = {}  # type: ignore


class _WarnOnce:
    """Module-level warn-once helper that suppresses repeated messages per session."""

    @_mutmut_mutated(mutants_xǁ_WarnOnceǁ__init____mutmut)
    def __init__(self) -> None:
        """Initialize with no warnings emitted yet."""
        self._warned: bool = False

    def xǁ_WarnOnceǁ__init____mutmut_orig(self) -> None:
        """Initialize with no warnings emitted yet."""
        self._warned: bool = False

    def xǁ_WarnOnceǁ__init____mutmut_1(self) -> None:
        """Initialize with no warnings emitted yet."""
        self._warned: bool = None

    def xǁ_WarnOnceǁ__init____mutmut_2(self) -> None:
        """Initialize with no warnings emitted yet."""
        self._warned: bool = True

    @_mutmut_mutated(mutants_xǁ_WarnOnceǁlog__mutmut)
    def log(self, msg: str, *args: object) -> None:
        """Emit a warning message only once per session instance."""
        if not self._warned:
            logger.warning(msg, *args)
            self._warned = True

    def xǁ_WarnOnceǁlog__mutmut_orig(self, msg: str, *args: object) -> None:
        """Emit a warning message only once per session instance."""
        if not self._warned:
            logger.warning(msg, *args)
            self._warned = True

    def xǁ_WarnOnceǁlog__mutmut_1(self, msg: str, *args: object) -> None:
        """Emit a warning message only once per session instance."""
        if self._warned:
            logger.warning(msg, *args)
            self._warned = True

    def xǁ_WarnOnceǁlog__mutmut_2(self, msg: str, *args: object) -> None:
        """Emit a warning message only once per session instance."""
        if not self._warned:
            logger.warning(None, *args)
            self._warned = True

    def xǁ_WarnOnceǁlog__mutmut_3(self, msg: str, *args: object) -> None:
        """Emit a warning message only once per session instance."""
        if not self._warned:
            logger.warning(*args)
            self._warned = True

    def xǁ_WarnOnceǁlog__mutmut_4(self, msg: str, *args: object) -> None:
        """Emit a warning message only once per session instance."""
        if not self._warned:
            logger.warning(msg, )
            self._warned = True

    def xǁ_WarnOnceǁlog__mutmut_5(self, msg: str, *args: object) -> None:
        """Emit a warning message only once per session instance."""
        if not self._warned:
            logger.warning(msg, *args)
            self._warned = None

    def xǁ_WarnOnceǁlog__mutmut_6(self, msg: str, *args: object) -> None:
        """Emit a warning message only once per session instance."""
        if not self._warned:
            logger.warning(msg, *args)
            self._warned = False

    @_mutmut_mutated(mutants_xǁ_WarnOnceǁreset__mutmut)
    def reset(self) -> None:
        """Reset the warn-once flag after a successful call."""
        self._warned = False

    def xǁ_WarnOnceǁreset__mutmut_orig(self) -> None:
        """Reset the warn-once flag after a successful call."""
        self._warned = False

    def xǁ_WarnOnceǁreset__mutmut_1(self) -> None:
        """Reset the warn-once flag after a successful call."""
        self._warned = None

    def xǁ_WarnOnceǁreset__mutmut_2(self) -> None:
        """Reset the warn-once flag after a successful call."""
        self._warned = True

mutants_xǁ_WarnOnceǁ__init____mutmut['_mutmut_orig'] = _WarnOnce.xǁ_WarnOnceǁ__init____mutmut_orig # type: ignore # mutmut generated
mutants_xǁ_WarnOnceǁ__init____mutmut['xǁ_WarnOnceǁ__init____mutmut_1'] = _WarnOnce.xǁ_WarnOnceǁ__init____mutmut_1 # type: ignore # mutmut generated
mutants_xǁ_WarnOnceǁ__init____mutmut['xǁ_WarnOnceǁ__init____mutmut_2'] = _WarnOnce.xǁ_WarnOnceǁ__init____mutmut_2 # type: ignore # mutmut generated

mutants_xǁ_WarnOnceǁlog__mutmut['_mutmut_orig'] = _WarnOnce.xǁ_WarnOnceǁlog__mutmut_orig # type: ignore # mutmut generated
mutants_xǁ_WarnOnceǁlog__mutmut['xǁ_WarnOnceǁlog__mutmut_1'] = _WarnOnce.xǁ_WarnOnceǁlog__mutmut_1 # type: ignore # mutmut generated
mutants_xǁ_WarnOnceǁlog__mutmut['xǁ_WarnOnceǁlog__mutmut_2'] = _WarnOnce.xǁ_WarnOnceǁlog__mutmut_2 # type: ignore # mutmut generated
mutants_xǁ_WarnOnceǁlog__mutmut['xǁ_WarnOnceǁlog__mutmut_3'] = _WarnOnce.xǁ_WarnOnceǁlog__mutmut_3 # type: ignore # mutmut generated
mutants_xǁ_WarnOnceǁlog__mutmut['xǁ_WarnOnceǁlog__mutmut_4'] = _WarnOnce.xǁ_WarnOnceǁlog__mutmut_4 # type: ignore # mutmut generated
mutants_xǁ_WarnOnceǁlog__mutmut['xǁ_WarnOnceǁlog__mutmut_5'] = _WarnOnce.xǁ_WarnOnceǁlog__mutmut_5 # type: ignore # mutmut generated
mutants_xǁ_WarnOnceǁlog__mutmut['xǁ_WarnOnceǁlog__mutmut_6'] = _WarnOnce.xǁ_WarnOnceǁlog__mutmut_6 # type: ignore # mutmut generated

mutants_xǁ_WarnOnceǁreset__mutmut['_mutmut_orig'] = _WarnOnce.xǁ_WarnOnceǁreset__mutmut_orig # type: ignore # mutmut generated
mutants_xǁ_WarnOnceǁreset__mutmut['xǁ_WarnOnceǁreset__mutmut_1'] = _WarnOnce.xǁ_WarnOnceǁreset__mutmut_1 # type: ignore # mutmut generated
mutants_xǁ_WarnOnceǁreset__mutmut['xǁ_WarnOnceǁreset__mutmut_2'] = _WarnOnce.xǁ_WarnOnceǁreset__mutmut_2 # type: ignore # mutmut generated
mutants_x__estimate_chars__mutmut: MutantDict = {}  # type: ignore


@_mutmut_mutated(mutants_x__estimate_chars__mutmut)
def _estimate_chars(history: list[LLMMessage]) -> int:
    """Count total characters across all messages (content + serialised tool_calls)."""
    total = 0
    for msg in history:
        content = msg.get("content")
        total += len(content) if isinstance(content, str) else 0
        total += sum(
            tool_call_serialized_length(tc) for tc in msg.get("tool_calls") or []
        )
    return total


def x__estimate_chars__mutmut_orig(history: list[LLMMessage]) -> int:
    """Count total characters across all messages (content + serialised tool_calls)."""
    total = 0
    for msg in history:
        content = msg.get("content")
        total += len(content) if isinstance(content, str) else 0
        total += sum(
            tool_call_serialized_length(tc) for tc in msg.get("tool_calls") or []
        )
    return total


def x__estimate_chars__mutmut_1(history: list[LLMMessage]) -> int:
    """Count total characters across all messages (content + serialised tool_calls)."""
    total = None
    for msg in history:
        content = msg.get("content")
        total += len(content) if isinstance(content, str) else 0
        total += sum(
            tool_call_serialized_length(tc) for tc in msg.get("tool_calls") or []
        )
    return total


def x__estimate_chars__mutmut_2(history: list[LLMMessage]) -> int:
    """Count total characters across all messages (content + serialised tool_calls)."""
    total = 1
    for msg in history:
        content = msg.get("content")
        total += len(content) if isinstance(content, str) else 0
        total += sum(
            tool_call_serialized_length(tc) for tc in msg.get("tool_calls") or []
        )
    return total


def x__estimate_chars__mutmut_3(history: list[LLMMessage]) -> int:
    """Count total characters across all messages (content + serialised tool_calls)."""
    total = 0
    for msg in history:
        content = None
        total += len(content) if isinstance(content, str) else 0
        total += sum(
            tool_call_serialized_length(tc) for tc in msg.get("tool_calls") or []
        )
    return total


def x__estimate_chars__mutmut_4(history: list[LLMMessage]) -> int:
    """Count total characters across all messages (content + serialised tool_calls)."""
    total = 0
    for msg in history:
        content = msg.get(None)
        total += len(content) if isinstance(content, str) else 0
        total += sum(
            tool_call_serialized_length(tc) for tc in msg.get("tool_calls") or []
        )
    return total


def x__estimate_chars__mutmut_5(history: list[LLMMessage]) -> int:
    """Count total characters across all messages (content + serialised tool_calls)."""
    total = 0
    for msg in history:
        content = msg.get("XXcontentXX")
        total += len(content) if isinstance(content, str) else 0
        total += sum(
            tool_call_serialized_length(tc) for tc in msg.get("tool_calls") or []
        )
    return total


def x__estimate_chars__mutmut_6(history: list[LLMMessage]) -> int:
    """Count total characters across all messages (content + serialised tool_calls)."""
    total = 0
    for msg in history:
        content = msg.get("CONTENT")
        total += len(content) if isinstance(content, str) else 0
        total += sum(
            tool_call_serialized_length(tc) for tc in msg.get("tool_calls") or []
        )
    return total


def x__estimate_chars__mutmut_7(history: list[LLMMessage]) -> int:
    """Count total characters across all messages (content + serialised tool_calls)."""
    total = 0
    for msg in history:
        content = msg.get("content")
        total = len(content) if isinstance(content, str) else 0
        total += sum(
            tool_call_serialized_length(tc) for tc in msg.get("tool_calls") or []
        )
    return total


def x__estimate_chars__mutmut_8(history: list[LLMMessage]) -> int:
    """Count total characters across all messages (content + serialised tool_calls)."""
    total = 0
    for msg in history:
        content = msg.get("content")
        total -= len(content) if isinstance(content, str) else 0
        total += sum(
            tool_call_serialized_length(tc) for tc in msg.get("tool_calls") or []
        )
    return total


def x__estimate_chars__mutmut_9(history: list[LLMMessage]) -> int:
    """Count total characters across all messages (content + serialised tool_calls)."""
    total = 0
    for msg in history:
        content = msg.get("content")
        total += len(content) if isinstance(content, str) else 1
        total += sum(
            tool_call_serialized_length(tc) for tc in msg.get("tool_calls") or []
        )
    return total


def x__estimate_chars__mutmut_10(history: list[LLMMessage]) -> int:
    """Count total characters across all messages (content + serialised tool_calls)."""
    total = 0
    for msg in history:
        content = msg.get("content")
        total += len(content) if isinstance(content, str) else 0
        total = sum(
            tool_call_serialized_length(tc) for tc in msg.get("tool_calls") or []
        )
    return total


def x__estimate_chars__mutmut_11(history: list[LLMMessage]) -> int:
    """Count total characters across all messages (content + serialised tool_calls)."""
    total = 0
    for msg in history:
        content = msg.get("content")
        total += len(content) if isinstance(content, str) else 0
        total -= sum(
            tool_call_serialized_length(tc) for tc in msg.get("tool_calls") or []
        )
    return total


def x__estimate_chars__mutmut_12(history: list[LLMMessage]) -> int:
    """Count total characters across all messages (content + serialised tool_calls)."""
    total = 0
    for msg in history:
        content = msg.get("content")
        total += len(content) if isinstance(content, str) else 0
        total += sum(
            None
        )
    return total


def x__estimate_chars__mutmut_13(history: list[LLMMessage]) -> int:
    """Count total characters across all messages (content + serialised tool_calls)."""
    total = 0
    for msg in history:
        content = msg.get("content")
        total += len(content) if isinstance(content, str) else 0
        total += sum(
            tool_call_serialized_length(None) for tc in msg.get("tool_calls") or []
        )
    return total


def x__estimate_chars__mutmut_14(history: list[LLMMessage]) -> int:
    """Count total characters across all messages (content + serialised tool_calls)."""
    total = 0
    for msg in history:
        content = msg.get("content")
        total += len(content) if isinstance(content, str) else 0
        total += sum(
            tool_call_serialized_length(tc) for tc in msg.get("tool_calls") and []
        )
    return total


def x__estimate_chars__mutmut_15(history: list[LLMMessage]) -> int:
    """Count total characters across all messages (content + serialised tool_calls)."""
    total = 0
    for msg in history:
        content = msg.get("content")
        total += len(content) if isinstance(content, str) else 0
        total += sum(
            tool_call_serialized_length(tc) for tc in msg.get(None) or []
        )
    return total


def x__estimate_chars__mutmut_16(history: list[LLMMessage]) -> int:
    """Count total characters across all messages (content + serialised tool_calls)."""
    total = 0
    for msg in history:
        content = msg.get("content")
        total += len(content) if isinstance(content, str) else 0
        total += sum(
            tool_call_serialized_length(tc) for tc in msg.get("XXtool_callsXX") or []
        )
    return total


def x__estimate_chars__mutmut_17(history: list[LLMMessage]) -> int:
    """Count total characters across all messages (content + serialised tool_calls)."""
    total = 0
    for msg in history:
        content = msg.get("content")
        total += len(content) if isinstance(content, str) else 0
        total += sum(
            tool_call_serialized_length(tc) for tc in msg.get("TOOL_CALLS") or []
        )
    return total

mutants_x__estimate_chars__mutmut['_mutmut_orig'] = x__estimate_chars__mutmut_orig # type: ignore # mutmut generated
mutants_x__estimate_chars__mutmut['x__estimate_chars__mutmut_1'] = x__estimate_chars__mutmut_1 # type: ignore # mutmut generated
mutants_x__estimate_chars__mutmut['x__estimate_chars__mutmut_2'] = x__estimate_chars__mutmut_2 # type: ignore # mutmut generated
mutants_x__estimate_chars__mutmut['x__estimate_chars__mutmut_3'] = x__estimate_chars__mutmut_3 # type: ignore # mutmut generated
mutants_x__estimate_chars__mutmut['x__estimate_chars__mutmut_4'] = x__estimate_chars__mutmut_4 # type: ignore # mutmut generated
mutants_x__estimate_chars__mutmut['x__estimate_chars__mutmut_5'] = x__estimate_chars__mutmut_5 # type: ignore # mutmut generated
mutants_x__estimate_chars__mutmut['x__estimate_chars__mutmut_6'] = x__estimate_chars__mutmut_6 # type: ignore # mutmut generated
mutants_x__estimate_chars__mutmut['x__estimate_chars__mutmut_7'] = x__estimate_chars__mutmut_7 # type: ignore # mutmut generated
mutants_x__estimate_chars__mutmut['x__estimate_chars__mutmut_8'] = x__estimate_chars__mutmut_8 # type: ignore # mutmut generated
mutants_x__estimate_chars__mutmut['x__estimate_chars__mutmut_9'] = x__estimate_chars__mutmut_9 # type: ignore # mutmut generated
mutants_x__estimate_chars__mutmut['x__estimate_chars__mutmut_10'] = x__estimate_chars__mutmut_10 # type: ignore # mutmut generated
mutants_x__estimate_chars__mutmut['x__estimate_chars__mutmut_11'] = x__estimate_chars__mutmut_11 # type: ignore # mutmut generated
mutants_x__estimate_chars__mutmut['x__estimate_chars__mutmut_12'] = x__estimate_chars__mutmut_12 # type: ignore # mutmut generated
mutants_x__estimate_chars__mutmut['x__estimate_chars__mutmut_13'] = x__estimate_chars__mutmut_13 # type: ignore # mutmut generated
mutants_x__estimate_chars__mutmut['x__estimate_chars__mutmut_14'] = x__estimate_chars__mutmut_14 # type: ignore # mutmut generated
mutants_x__estimate_chars__mutmut['x__estimate_chars__mutmut_15'] = x__estimate_chars__mutmut_15 # type: ignore # mutmut generated
mutants_x__estimate_chars__mutmut['x__estimate_chars__mutmut_16'] = x__estimate_chars__mutmut_16 # type: ignore # mutmut generated
mutants_x__estimate_chars__mutmut['x__estimate_chars__mutmut_17'] = x__estimate_chars__mutmut_17 # type: ignore # mutmut generated
mutants_x__serialise_for_tokenize__mutmut: MutantDict = {}  # type: ignore


@_mutmut_mutated(mutants_x__serialise_for_tokenize__mutmut)
def _serialise_for_tokenize(history: list[LLMMessage]) -> str:
    """Flatten history to a single string for the /tokenize endpoint."""
    parts: list[str] = []
    for msg in history:
        role = msg.get("role", "")
        content_raw = msg.get("content")
        content = content_raw if isinstance(content_raw, str) else ""
        if content:
            parts.append(f"{role}: {content}")
        for tc in msg.get("tool_calls") or []:
            parts.append(_json_dumps(tc))
    return "\n".join(parts)


def x__serialise_for_tokenize__mutmut_orig(history: list[LLMMessage]) -> str:
    """Flatten history to a single string for the /tokenize endpoint."""
    parts: list[str] = []
    for msg in history:
        role = msg.get("role", "")
        content_raw = msg.get("content")
        content = content_raw if isinstance(content_raw, str) else ""
        if content:
            parts.append(f"{role}: {content}")
        for tc in msg.get("tool_calls") or []:
            parts.append(_json_dumps(tc))
    return "\n".join(parts)


def x__serialise_for_tokenize__mutmut_1(history: list[LLMMessage]) -> str:
    """Flatten history to a single string for the /tokenize endpoint."""
    parts: list[str] = None
    for msg in history:
        role = msg.get("role", "")
        content_raw = msg.get("content")
        content = content_raw if isinstance(content_raw, str) else ""
        if content:
            parts.append(f"{role}: {content}")
        for tc in msg.get("tool_calls") or []:
            parts.append(_json_dumps(tc))
    return "\n".join(parts)


def x__serialise_for_tokenize__mutmut_2(history: list[LLMMessage]) -> str:
    """Flatten history to a single string for the /tokenize endpoint."""
    parts: list[str] = []
    for msg in history:
        role = None
        content_raw = msg.get("content")
        content = content_raw if isinstance(content_raw, str) else ""
        if content:
            parts.append(f"{role}: {content}")
        for tc in msg.get("tool_calls") or []:
            parts.append(_json_dumps(tc))
    return "\n".join(parts)


def x__serialise_for_tokenize__mutmut_3(history: list[LLMMessage]) -> str:
    """Flatten history to a single string for the /tokenize endpoint."""
    parts: list[str] = []
    for msg in history:
        role = msg.get(None, "")
        content_raw = msg.get("content")
        content = content_raw if isinstance(content_raw, str) else ""
        if content:
            parts.append(f"{role}: {content}")
        for tc in msg.get("tool_calls") or []:
            parts.append(_json_dumps(tc))
    return "\n".join(parts)


def x__serialise_for_tokenize__mutmut_4(history: list[LLMMessage]) -> str:
    """Flatten history to a single string for the /tokenize endpoint."""
    parts: list[str] = []
    for msg in history:
        role = msg.get("role", None)
        content_raw = msg.get("content")
        content = content_raw if isinstance(content_raw, str) else ""
        if content:
            parts.append(f"{role}: {content}")
        for tc in msg.get("tool_calls") or []:
            parts.append(_json_dumps(tc))
    return "\n".join(parts)


def x__serialise_for_tokenize__mutmut_5(history: list[LLMMessage]) -> str:
    """Flatten history to a single string for the /tokenize endpoint."""
    parts: list[str] = []
    for msg in history:
        role = msg.get("")
        content_raw = msg.get("content")
        content = content_raw if isinstance(content_raw, str) else ""
        if content:
            parts.append(f"{role}: {content}")
        for tc in msg.get("tool_calls") or []:
            parts.append(_json_dumps(tc))
    return "\n".join(parts)


def x__serialise_for_tokenize__mutmut_6(history: list[LLMMessage]) -> str:
    """Flatten history to a single string for the /tokenize endpoint."""
    parts: list[str] = []
    for msg in history:
        role = msg.get("role", )
        content_raw = msg.get("content")
        content = content_raw if isinstance(content_raw, str) else ""
        if content:
            parts.append(f"{role}: {content}")
        for tc in msg.get("tool_calls") or []:
            parts.append(_json_dumps(tc))
    return "\n".join(parts)


def x__serialise_for_tokenize__mutmut_7(history: list[LLMMessage]) -> str:
    """Flatten history to a single string for the /tokenize endpoint."""
    parts: list[str] = []
    for msg in history:
        role = msg.get("XXroleXX", "")
        content_raw = msg.get("content")
        content = content_raw if isinstance(content_raw, str) else ""
        if content:
            parts.append(f"{role}: {content}")
        for tc in msg.get("tool_calls") or []:
            parts.append(_json_dumps(tc))
    return "\n".join(parts)


def x__serialise_for_tokenize__mutmut_8(history: list[LLMMessage]) -> str:
    """Flatten history to a single string for the /tokenize endpoint."""
    parts: list[str] = []
    for msg in history:
        role = msg.get("ROLE", "")
        content_raw = msg.get("content")
        content = content_raw if isinstance(content_raw, str) else ""
        if content:
            parts.append(f"{role}: {content}")
        for tc in msg.get("tool_calls") or []:
            parts.append(_json_dumps(tc))
    return "\n".join(parts)


def x__serialise_for_tokenize__mutmut_9(history: list[LLMMessage]) -> str:
    """Flatten history to a single string for the /tokenize endpoint."""
    parts: list[str] = []
    for msg in history:
        role = msg.get("role", "XXXX")
        content_raw = msg.get("content")
        content = content_raw if isinstance(content_raw, str) else ""
        if content:
            parts.append(f"{role}: {content}")
        for tc in msg.get("tool_calls") or []:
            parts.append(_json_dumps(tc))
    return "\n".join(parts)


def x__serialise_for_tokenize__mutmut_10(history: list[LLMMessage]) -> str:
    """Flatten history to a single string for the /tokenize endpoint."""
    parts: list[str] = []
    for msg in history:
        role = msg.get("role", "")
        content_raw = None
        content = content_raw if isinstance(content_raw, str) else ""
        if content:
            parts.append(f"{role}: {content}")
        for tc in msg.get("tool_calls") or []:
            parts.append(_json_dumps(tc))
    return "\n".join(parts)


def x__serialise_for_tokenize__mutmut_11(history: list[LLMMessage]) -> str:
    """Flatten history to a single string for the /tokenize endpoint."""
    parts: list[str] = []
    for msg in history:
        role = msg.get("role", "")
        content_raw = msg.get(None)
        content = content_raw if isinstance(content_raw, str) else ""
        if content:
            parts.append(f"{role}: {content}")
        for tc in msg.get("tool_calls") or []:
            parts.append(_json_dumps(tc))
    return "\n".join(parts)


def x__serialise_for_tokenize__mutmut_12(history: list[LLMMessage]) -> str:
    """Flatten history to a single string for the /tokenize endpoint."""
    parts: list[str] = []
    for msg in history:
        role = msg.get("role", "")
        content_raw = msg.get("XXcontentXX")
        content = content_raw if isinstance(content_raw, str) else ""
        if content:
            parts.append(f"{role}: {content}")
        for tc in msg.get("tool_calls") or []:
            parts.append(_json_dumps(tc))
    return "\n".join(parts)


def x__serialise_for_tokenize__mutmut_13(history: list[LLMMessage]) -> str:
    """Flatten history to a single string for the /tokenize endpoint."""
    parts: list[str] = []
    for msg in history:
        role = msg.get("role", "")
        content_raw = msg.get("CONTENT")
        content = content_raw if isinstance(content_raw, str) else ""
        if content:
            parts.append(f"{role}: {content}")
        for tc in msg.get("tool_calls") or []:
            parts.append(_json_dumps(tc))
    return "\n".join(parts)


def x__serialise_for_tokenize__mutmut_14(history: list[LLMMessage]) -> str:
    """Flatten history to a single string for the /tokenize endpoint."""
    parts: list[str] = []
    for msg in history:
        role = msg.get("role", "")
        content_raw = msg.get("content")
        content = None
        if content:
            parts.append(f"{role}: {content}")
        for tc in msg.get("tool_calls") or []:
            parts.append(_json_dumps(tc))
    return "\n".join(parts)


def x__serialise_for_tokenize__mutmut_15(history: list[LLMMessage]) -> str:
    """Flatten history to a single string for the /tokenize endpoint."""
    parts: list[str] = []
    for msg in history:
        role = msg.get("role", "")
        content_raw = msg.get("content")
        content = content_raw if isinstance(content_raw, str) else "XXXX"
        if content:
            parts.append(f"{role}: {content}")
        for tc in msg.get("tool_calls") or []:
            parts.append(_json_dumps(tc))
    return "\n".join(parts)


def x__serialise_for_tokenize__mutmut_16(history: list[LLMMessage]) -> str:
    """Flatten history to a single string for the /tokenize endpoint."""
    parts: list[str] = []
    for msg in history:
        role = msg.get("role", "")
        content_raw = msg.get("content")
        content = content_raw if isinstance(content_raw, str) else ""
        if content:
            parts.append(None)
        for tc in msg.get("tool_calls") or []:
            parts.append(_json_dumps(tc))
    return "\n".join(parts)


def x__serialise_for_tokenize__mutmut_17(history: list[LLMMessage]) -> str:
    """Flatten history to a single string for the /tokenize endpoint."""
    parts: list[str] = []
    for msg in history:
        role = msg.get("role", "")
        content_raw = msg.get("content")
        content = content_raw if isinstance(content_raw, str) else ""
        if content:
            parts.append(f"{role}: {content}")
        for tc in msg.get("tool_calls") and []:
            parts.append(_json_dumps(tc))
    return "\n".join(parts)


def x__serialise_for_tokenize__mutmut_18(history: list[LLMMessage]) -> str:
    """Flatten history to a single string for the /tokenize endpoint."""
    parts: list[str] = []
    for msg in history:
        role = msg.get("role", "")
        content_raw = msg.get("content")
        content = content_raw if isinstance(content_raw, str) else ""
        if content:
            parts.append(f"{role}: {content}")
        for tc in msg.get(None) or []:
            parts.append(_json_dumps(tc))
    return "\n".join(parts)


def x__serialise_for_tokenize__mutmut_19(history: list[LLMMessage]) -> str:
    """Flatten history to a single string for the /tokenize endpoint."""
    parts: list[str] = []
    for msg in history:
        role = msg.get("role", "")
        content_raw = msg.get("content")
        content = content_raw if isinstance(content_raw, str) else ""
        if content:
            parts.append(f"{role}: {content}")
        for tc in msg.get("XXtool_callsXX") or []:
            parts.append(_json_dumps(tc))
    return "\n".join(parts)


def x__serialise_for_tokenize__mutmut_20(history: list[LLMMessage]) -> str:
    """Flatten history to a single string for the /tokenize endpoint."""
    parts: list[str] = []
    for msg in history:
        role = msg.get("role", "")
        content_raw = msg.get("content")
        content = content_raw if isinstance(content_raw, str) else ""
        if content:
            parts.append(f"{role}: {content}")
        for tc in msg.get("TOOL_CALLS") or []:
            parts.append(_json_dumps(tc))
    return "\n".join(parts)


def x__serialise_for_tokenize__mutmut_21(history: list[LLMMessage]) -> str:
    """Flatten history to a single string for the /tokenize endpoint."""
    parts: list[str] = []
    for msg in history:
        role = msg.get("role", "")
        content_raw = msg.get("content")
        content = content_raw if isinstance(content_raw, str) else ""
        if content:
            parts.append(f"{role}: {content}")
        for tc in msg.get("tool_calls") or []:
            parts.append(None)
    return "\n".join(parts)


def x__serialise_for_tokenize__mutmut_22(history: list[LLMMessage]) -> str:
    """Flatten history to a single string for the /tokenize endpoint."""
    parts: list[str] = []
    for msg in history:
        role = msg.get("role", "")
        content_raw = msg.get("content")
        content = content_raw if isinstance(content_raw, str) else ""
        if content:
            parts.append(f"{role}: {content}")
        for tc in msg.get("tool_calls") or []:
            parts.append(_json_dumps(None))
    return "\n".join(parts)


def x__serialise_for_tokenize__mutmut_23(history: list[LLMMessage]) -> str:
    """Flatten history to a single string for the /tokenize endpoint."""
    parts: list[str] = []
    for msg in history:
        role = msg.get("role", "")
        content_raw = msg.get("content")
        content = content_raw if isinstance(content_raw, str) else ""
        if content:
            parts.append(f"{role}: {content}")
        for tc in msg.get("tool_calls") or []:
            parts.append(_json_dumps(tc))
    return "\n".join(None)


def x__serialise_for_tokenize__mutmut_24(history: list[LLMMessage]) -> str:
    """Flatten history to a single string for the /tokenize endpoint."""
    parts: list[str] = []
    for msg in history:
        role = msg.get("role", "")
        content_raw = msg.get("content")
        content = content_raw if isinstance(content_raw, str) else ""
        if content:
            parts.append(f"{role}: {content}")
        for tc in msg.get("tool_calls") or []:
            parts.append(_json_dumps(tc))
    return "XX\nXX".join(parts)

mutants_x__serialise_for_tokenize__mutmut['_mutmut_orig'] = x__serialise_for_tokenize__mutmut_orig # type: ignore # mutmut generated
mutants_x__serialise_for_tokenize__mutmut['x__serialise_for_tokenize__mutmut_1'] = x__serialise_for_tokenize__mutmut_1 # type: ignore # mutmut generated
mutants_x__serialise_for_tokenize__mutmut['x__serialise_for_tokenize__mutmut_2'] = x__serialise_for_tokenize__mutmut_2 # type: ignore # mutmut generated
mutants_x__serialise_for_tokenize__mutmut['x__serialise_for_tokenize__mutmut_3'] = x__serialise_for_tokenize__mutmut_3 # type: ignore # mutmut generated
mutants_x__serialise_for_tokenize__mutmut['x__serialise_for_tokenize__mutmut_4'] = x__serialise_for_tokenize__mutmut_4 # type: ignore # mutmut generated
mutants_x__serialise_for_tokenize__mutmut['x__serialise_for_tokenize__mutmut_5'] = x__serialise_for_tokenize__mutmut_5 # type: ignore # mutmut generated
mutants_x__serialise_for_tokenize__mutmut['x__serialise_for_tokenize__mutmut_6'] = x__serialise_for_tokenize__mutmut_6 # type: ignore # mutmut generated
mutants_x__serialise_for_tokenize__mutmut['x__serialise_for_tokenize__mutmut_7'] = x__serialise_for_tokenize__mutmut_7 # type: ignore # mutmut generated
mutants_x__serialise_for_tokenize__mutmut['x__serialise_for_tokenize__mutmut_8'] = x__serialise_for_tokenize__mutmut_8 # type: ignore # mutmut generated
mutants_x__serialise_for_tokenize__mutmut['x__serialise_for_tokenize__mutmut_9'] = x__serialise_for_tokenize__mutmut_9 # type: ignore # mutmut generated
mutants_x__serialise_for_tokenize__mutmut['x__serialise_for_tokenize__mutmut_10'] = x__serialise_for_tokenize__mutmut_10 # type: ignore # mutmut generated
mutants_x__serialise_for_tokenize__mutmut['x__serialise_for_tokenize__mutmut_11'] = x__serialise_for_tokenize__mutmut_11 # type: ignore # mutmut generated
mutants_x__serialise_for_tokenize__mutmut['x__serialise_for_tokenize__mutmut_12'] = x__serialise_for_tokenize__mutmut_12 # type: ignore # mutmut generated
mutants_x__serialise_for_tokenize__mutmut['x__serialise_for_tokenize__mutmut_13'] = x__serialise_for_tokenize__mutmut_13 # type: ignore # mutmut generated
mutants_x__serialise_for_tokenize__mutmut['x__serialise_for_tokenize__mutmut_14'] = x__serialise_for_tokenize__mutmut_14 # type: ignore # mutmut generated
mutants_x__serialise_for_tokenize__mutmut['x__serialise_for_tokenize__mutmut_15'] = x__serialise_for_tokenize__mutmut_15 # type: ignore # mutmut generated
mutants_x__serialise_for_tokenize__mutmut['x__serialise_for_tokenize__mutmut_16'] = x__serialise_for_tokenize__mutmut_16 # type: ignore # mutmut generated
mutants_x__serialise_for_tokenize__mutmut['x__serialise_for_tokenize__mutmut_17'] = x__serialise_for_tokenize__mutmut_17 # type: ignore # mutmut generated
mutants_x__serialise_for_tokenize__mutmut['x__serialise_for_tokenize__mutmut_18'] = x__serialise_for_tokenize__mutmut_18 # type: ignore # mutmut generated
mutants_x__serialise_for_tokenize__mutmut['x__serialise_for_tokenize__mutmut_19'] = x__serialise_for_tokenize__mutmut_19 # type: ignore # mutmut generated
mutants_x__serialise_for_tokenize__mutmut['x__serialise_for_tokenize__mutmut_20'] = x__serialise_for_tokenize__mutmut_20 # type: ignore # mutmut generated
mutants_x__serialise_for_tokenize__mutmut['x__serialise_for_tokenize__mutmut_21'] = x__serialise_for_tokenize__mutmut_21 # type: ignore # mutmut generated
mutants_x__serialise_for_tokenize__mutmut['x__serialise_for_tokenize__mutmut_22'] = x__serialise_for_tokenize__mutmut_22 # type: ignore # mutmut generated
mutants_x__serialise_for_tokenize__mutmut['x__serialise_for_tokenize__mutmut_23'] = x__serialise_for_tokenize__mutmut_23 # type: ignore # mutmut generated
mutants_x__serialise_for_tokenize__mutmut['x__serialise_for_tokenize__mutmut_24'] = x__serialise_for_tokenize__mutmut_24 # type: ignore # mutmut generated
mutants_x_get_token_count__mutmut: MutantDict = {}  # type: ignore


@_mutmut_mutated(mutants_x_get_token_count__mutmut)
async def get_token_count(
    history: list[LLMMessage],
    tokenize_url: str,
    http: httpx.AsyncClient,
    timeout: float = 3.0,
    warn_once: _WarnOnce | None = None,
) -> tuple[int, bool]:
    """Return (token_count, is_exact) for the given history."""
    if not tokenize_url:
        return estimate_tokens(history)[0], False

    text = _serialise_for_tokenize(history)
    try:
        n_tokens = await _fetch_token_count(text, tokenize_url, http, timeout)
        if n_tokens > 0:
            if warn_once is not None:
                warn_once.reset()
            return n_tokens, True
        logger.warning("token_counter: /tokenize returned n_tokens=0, falling back")
    except (TimeoutError, httpx.HTTPStatusError, httpx.RequestError, ValueError) as exc:
        _warn_tokenize_unavailable(exc, warn_once)

    return estimate_tokens(history)[0], False


async def x_get_token_count__mutmut_orig(
    history: list[LLMMessage],
    tokenize_url: str,
    http: httpx.AsyncClient,
    timeout: float = 3.0,
    warn_once: _WarnOnce | None = None,
) -> tuple[int, bool]:
    """Return (token_count, is_exact) for the given history."""
    if not tokenize_url:
        return estimate_tokens(history)[0], False

    text = _serialise_for_tokenize(history)
    try:
        n_tokens = await _fetch_token_count(text, tokenize_url, http, timeout)
        if n_tokens > 0:
            if warn_once is not None:
                warn_once.reset()
            return n_tokens, True
        logger.warning("token_counter: /tokenize returned n_tokens=0, falling back")
    except (TimeoutError, httpx.HTTPStatusError, httpx.RequestError, ValueError) as exc:
        _warn_tokenize_unavailable(exc, warn_once)

    return estimate_tokens(history)[0], False


async def x_get_token_count__mutmut_1(
    history: list[LLMMessage],
    tokenize_url: str,
    http: httpx.AsyncClient,
    timeout: float = 4.0,
    warn_once: _WarnOnce | None = None,
) -> tuple[int, bool]:
    """Return (token_count, is_exact) for the given history."""
    if not tokenize_url:
        return estimate_tokens(history)[0], False

    text = _serialise_for_tokenize(history)
    try:
        n_tokens = await _fetch_token_count(text, tokenize_url, http, timeout)
        if n_tokens > 0:
            if warn_once is not None:
                warn_once.reset()
            return n_tokens, True
        logger.warning("token_counter: /tokenize returned n_tokens=0, falling back")
    except (TimeoutError, httpx.HTTPStatusError, httpx.RequestError, ValueError) as exc:
        _warn_tokenize_unavailable(exc, warn_once)

    return estimate_tokens(history)[0], False


async def x_get_token_count__mutmut_2(
    history: list[LLMMessage],
    tokenize_url: str,
    http: httpx.AsyncClient,
    timeout: float = 3.0,
    warn_once: _WarnOnce | None = None,
) -> tuple[int, bool]:
    """Return (token_count, is_exact) for the given history."""
    if tokenize_url:
        return estimate_tokens(history)[0], False

    text = _serialise_for_tokenize(history)
    try:
        n_tokens = await _fetch_token_count(text, tokenize_url, http, timeout)
        if n_tokens > 0:
            if warn_once is not None:
                warn_once.reset()
            return n_tokens, True
        logger.warning("token_counter: /tokenize returned n_tokens=0, falling back")
    except (TimeoutError, httpx.HTTPStatusError, httpx.RequestError, ValueError) as exc:
        _warn_tokenize_unavailable(exc, warn_once)

    return estimate_tokens(history)[0], False


async def x_get_token_count__mutmut_3(
    history: list[LLMMessage],
    tokenize_url: str,
    http: httpx.AsyncClient,
    timeout: float = 3.0,
    warn_once: _WarnOnce | None = None,
) -> tuple[int, bool]:
    """Return (token_count, is_exact) for the given history."""
    if not tokenize_url:
        return estimate_tokens(None)[0], False

    text = _serialise_for_tokenize(history)
    try:
        n_tokens = await _fetch_token_count(text, tokenize_url, http, timeout)
        if n_tokens > 0:
            if warn_once is not None:
                warn_once.reset()
            return n_tokens, True
        logger.warning("token_counter: /tokenize returned n_tokens=0, falling back")
    except (TimeoutError, httpx.HTTPStatusError, httpx.RequestError, ValueError) as exc:
        _warn_tokenize_unavailable(exc, warn_once)

    return estimate_tokens(history)[0], False


async def x_get_token_count__mutmut_4(
    history: list[LLMMessage],
    tokenize_url: str,
    http: httpx.AsyncClient,
    timeout: float = 3.0,
    warn_once: _WarnOnce | None = None,
) -> tuple[int, bool]:
    """Return (token_count, is_exact) for the given history."""
    if not tokenize_url:
        return estimate_tokens(history)[1], False

    text = _serialise_for_tokenize(history)
    try:
        n_tokens = await _fetch_token_count(text, tokenize_url, http, timeout)
        if n_tokens > 0:
            if warn_once is not None:
                warn_once.reset()
            return n_tokens, True
        logger.warning("token_counter: /tokenize returned n_tokens=0, falling back")
    except (TimeoutError, httpx.HTTPStatusError, httpx.RequestError, ValueError) as exc:
        _warn_tokenize_unavailable(exc, warn_once)

    return estimate_tokens(history)[0], False


async def x_get_token_count__mutmut_5(
    history: list[LLMMessage],
    tokenize_url: str,
    http: httpx.AsyncClient,
    timeout: float = 3.0,
    warn_once: _WarnOnce | None = None,
) -> tuple[int, bool]:
    """Return (token_count, is_exact) for the given history."""
    if not tokenize_url:
        return estimate_tokens(history)[0], True

    text = _serialise_for_tokenize(history)
    try:
        n_tokens = await _fetch_token_count(text, tokenize_url, http, timeout)
        if n_tokens > 0:
            if warn_once is not None:
                warn_once.reset()
            return n_tokens, True
        logger.warning("token_counter: /tokenize returned n_tokens=0, falling back")
    except (TimeoutError, httpx.HTTPStatusError, httpx.RequestError, ValueError) as exc:
        _warn_tokenize_unavailable(exc, warn_once)

    return estimate_tokens(history)[0], False


async def x_get_token_count__mutmut_6(
    history: list[LLMMessage],
    tokenize_url: str,
    http: httpx.AsyncClient,
    timeout: float = 3.0,
    warn_once: _WarnOnce | None = None,
) -> tuple[int, bool]:
    """Return (token_count, is_exact) for the given history."""
    if not tokenize_url:
        return estimate_tokens(history)[0], False

    text = None
    try:
        n_tokens = await _fetch_token_count(text, tokenize_url, http, timeout)
        if n_tokens > 0:
            if warn_once is not None:
                warn_once.reset()
            return n_tokens, True
        logger.warning("token_counter: /tokenize returned n_tokens=0, falling back")
    except (TimeoutError, httpx.HTTPStatusError, httpx.RequestError, ValueError) as exc:
        _warn_tokenize_unavailable(exc, warn_once)

    return estimate_tokens(history)[0], False


async def x_get_token_count__mutmut_7(
    history: list[LLMMessage],
    tokenize_url: str,
    http: httpx.AsyncClient,
    timeout: float = 3.0,
    warn_once: _WarnOnce | None = None,
) -> tuple[int, bool]:
    """Return (token_count, is_exact) for the given history."""
    if not tokenize_url:
        return estimate_tokens(history)[0], False

    text = _serialise_for_tokenize(None)
    try:
        n_tokens = await _fetch_token_count(text, tokenize_url, http, timeout)
        if n_tokens > 0:
            if warn_once is not None:
                warn_once.reset()
            return n_tokens, True
        logger.warning("token_counter: /tokenize returned n_tokens=0, falling back")
    except (TimeoutError, httpx.HTTPStatusError, httpx.RequestError, ValueError) as exc:
        _warn_tokenize_unavailable(exc, warn_once)

    return estimate_tokens(history)[0], False


async def x_get_token_count__mutmut_8(
    history: list[LLMMessage],
    tokenize_url: str,
    http: httpx.AsyncClient,
    timeout: float = 3.0,
    warn_once: _WarnOnce | None = None,
) -> tuple[int, bool]:
    """Return (token_count, is_exact) for the given history."""
    if not tokenize_url:
        return estimate_tokens(history)[0], False

    text = _serialise_for_tokenize(history)
    try:
        n_tokens = None
        if n_tokens > 0:
            if warn_once is not None:
                warn_once.reset()
            return n_tokens, True
        logger.warning("token_counter: /tokenize returned n_tokens=0, falling back")
    except (TimeoutError, httpx.HTTPStatusError, httpx.RequestError, ValueError) as exc:
        _warn_tokenize_unavailable(exc, warn_once)

    return estimate_tokens(history)[0], False


async def x_get_token_count__mutmut_9(
    history: list[LLMMessage],
    tokenize_url: str,
    http: httpx.AsyncClient,
    timeout: float = 3.0,
    warn_once: _WarnOnce | None = None,
) -> tuple[int, bool]:
    """Return (token_count, is_exact) for the given history."""
    if not tokenize_url:
        return estimate_tokens(history)[0], False

    text = _serialise_for_tokenize(history)
    try:
        n_tokens = await _fetch_token_count(None, tokenize_url, http, timeout)
        if n_tokens > 0:
            if warn_once is not None:
                warn_once.reset()
            return n_tokens, True
        logger.warning("token_counter: /tokenize returned n_tokens=0, falling back")
    except (TimeoutError, httpx.HTTPStatusError, httpx.RequestError, ValueError) as exc:
        _warn_tokenize_unavailable(exc, warn_once)

    return estimate_tokens(history)[0], False


async def x_get_token_count__mutmut_10(
    history: list[LLMMessage],
    tokenize_url: str,
    http: httpx.AsyncClient,
    timeout: float = 3.0,
    warn_once: _WarnOnce | None = None,
) -> tuple[int, bool]:
    """Return (token_count, is_exact) for the given history."""
    if not tokenize_url:
        return estimate_tokens(history)[0], False

    text = _serialise_for_tokenize(history)
    try:
        n_tokens = await _fetch_token_count(text, None, http, timeout)
        if n_tokens > 0:
            if warn_once is not None:
                warn_once.reset()
            return n_tokens, True
        logger.warning("token_counter: /tokenize returned n_tokens=0, falling back")
    except (TimeoutError, httpx.HTTPStatusError, httpx.RequestError, ValueError) as exc:
        _warn_tokenize_unavailable(exc, warn_once)

    return estimate_tokens(history)[0], False


async def x_get_token_count__mutmut_11(
    history: list[LLMMessage],
    tokenize_url: str,
    http: httpx.AsyncClient,
    timeout: float = 3.0,
    warn_once: _WarnOnce | None = None,
) -> tuple[int, bool]:
    """Return (token_count, is_exact) for the given history."""
    if not tokenize_url:
        return estimate_tokens(history)[0], False

    text = _serialise_for_tokenize(history)
    try:
        n_tokens = await _fetch_token_count(text, tokenize_url, None, timeout)
        if n_tokens > 0:
            if warn_once is not None:
                warn_once.reset()
            return n_tokens, True
        logger.warning("token_counter: /tokenize returned n_tokens=0, falling back")
    except (TimeoutError, httpx.HTTPStatusError, httpx.RequestError, ValueError) as exc:
        _warn_tokenize_unavailable(exc, warn_once)

    return estimate_tokens(history)[0], False


async def x_get_token_count__mutmut_12(
    history: list[LLMMessage],
    tokenize_url: str,
    http: httpx.AsyncClient,
    timeout: float = 3.0,
    warn_once: _WarnOnce | None = None,
) -> tuple[int, bool]:
    """Return (token_count, is_exact) for the given history."""
    if not tokenize_url:
        return estimate_tokens(history)[0], False

    text = _serialise_for_tokenize(history)
    try:
        n_tokens = await _fetch_token_count(text, tokenize_url, http, None)
        if n_tokens > 0:
            if warn_once is not None:
                warn_once.reset()
            return n_tokens, True
        logger.warning("token_counter: /tokenize returned n_tokens=0, falling back")
    except (TimeoutError, httpx.HTTPStatusError, httpx.RequestError, ValueError) as exc:
        _warn_tokenize_unavailable(exc, warn_once)

    return estimate_tokens(history)[0], False


async def x_get_token_count__mutmut_13(
    history: list[LLMMessage],
    tokenize_url: str,
    http: httpx.AsyncClient,
    timeout: float = 3.0,
    warn_once: _WarnOnce | None = None,
) -> tuple[int, bool]:
    """Return (token_count, is_exact) for the given history."""
    if not tokenize_url:
        return estimate_tokens(history)[0], False

    text = _serialise_for_tokenize(history)
    try:
        n_tokens = await _fetch_token_count(tokenize_url, http, timeout)
        if n_tokens > 0:
            if warn_once is not None:
                warn_once.reset()
            return n_tokens, True
        logger.warning("token_counter: /tokenize returned n_tokens=0, falling back")
    except (TimeoutError, httpx.HTTPStatusError, httpx.RequestError, ValueError) as exc:
        _warn_tokenize_unavailable(exc, warn_once)

    return estimate_tokens(history)[0], False


async def x_get_token_count__mutmut_14(
    history: list[LLMMessage],
    tokenize_url: str,
    http: httpx.AsyncClient,
    timeout: float = 3.0,
    warn_once: _WarnOnce | None = None,
) -> tuple[int, bool]:
    """Return (token_count, is_exact) for the given history."""
    if not tokenize_url:
        return estimate_tokens(history)[0], False

    text = _serialise_for_tokenize(history)
    try:
        n_tokens = await _fetch_token_count(text, http, timeout)
        if n_tokens > 0:
            if warn_once is not None:
                warn_once.reset()
            return n_tokens, True
        logger.warning("token_counter: /tokenize returned n_tokens=0, falling back")
    except (TimeoutError, httpx.HTTPStatusError, httpx.RequestError, ValueError) as exc:
        _warn_tokenize_unavailable(exc, warn_once)

    return estimate_tokens(history)[0], False


async def x_get_token_count__mutmut_15(
    history: list[LLMMessage],
    tokenize_url: str,
    http: httpx.AsyncClient,
    timeout: float = 3.0,
    warn_once: _WarnOnce | None = None,
) -> tuple[int, bool]:
    """Return (token_count, is_exact) for the given history."""
    if not tokenize_url:
        return estimate_tokens(history)[0], False

    text = _serialise_for_tokenize(history)
    try:
        n_tokens = await _fetch_token_count(text, tokenize_url, timeout)
        if n_tokens > 0:
            if warn_once is not None:
                warn_once.reset()
            return n_tokens, True
        logger.warning("token_counter: /tokenize returned n_tokens=0, falling back")
    except (TimeoutError, httpx.HTTPStatusError, httpx.RequestError, ValueError) as exc:
        _warn_tokenize_unavailable(exc, warn_once)

    return estimate_tokens(history)[0], False


async def x_get_token_count__mutmut_16(
    history: list[LLMMessage],
    tokenize_url: str,
    http: httpx.AsyncClient,
    timeout: float = 3.0,
    warn_once: _WarnOnce | None = None,
) -> tuple[int, bool]:
    """Return (token_count, is_exact) for the given history."""
    if not tokenize_url:
        return estimate_tokens(history)[0], False

    text = _serialise_for_tokenize(history)
    try:
        n_tokens = await _fetch_token_count(text, tokenize_url, http, )
        if n_tokens > 0:
            if warn_once is not None:
                warn_once.reset()
            return n_tokens, True
        logger.warning("token_counter: /tokenize returned n_tokens=0, falling back")
    except (TimeoutError, httpx.HTTPStatusError, httpx.RequestError, ValueError) as exc:
        _warn_tokenize_unavailable(exc, warn_once)

    return estimate_tokens(history)[0], False


async def x_get_token_count__mutmut_17(
    history: list[LLMMessage],
    tokenize_url: str,
    http: httpx.AsyncClient,
    timeout: float = 3.0,
    warn_once: _WarnOnce | None = None,
) -> tuple[int, bool]:
    """Return (token_count, is_exact) for the given history."""
    if not tokenize_url:
        return estimate_tokens(history)[0], False

    text = _serialise_for_tokenize(history)
    try:
        n_tokens = await _fetch_token_count(text, tokenize_url, http, timeout)
        if n_tokens >= 0:
            if warn_once is not None:
                warn_once.reset()
            return n_tokens, True
        logger.warning("token_counter: /tokenize returned n_tokens=0, falling back")
    except (TimeoutError, httpx.HTTPStatusError, httpx.RequestError, ValueError) as exc:
        _warn_tokenize_unavailable(exc, warn_once)

    return estimate_tokens(history)[0], False


async def x_get_token_count__mutmut_18(
    history: list[LLMMessage],
    tokenize_url: str,
    http: httpx.AsyncClient,
    timeout: float = 3.0,
    warn_once: _WarnOnce | None = None,
) -> tuple[int, bool]:
    """Return (token_count, is_exact) for the given history."""
    if not tokenize_url:
        return estimate_tokens(history)[0], False

    text = _serialise_for_tokenize(history)
    try:
        n_tokens = await _fetch_token_count(text, tokenize_url, http, timeout)
        if n_tokens > 1:
            if warn_once is not None:
                warn_once.reset()
            return n_tokens, True
        logger.warning("token_counter: /tokenize returned n_tokens=0, falling back")
    except (TimeoutError, httpx.HTTPStatusError, httpx.RequestError, ValueError) as exc:
        _warn_tokenize_unavailable(exc, warn_once)

    return estimate_tokens(history)[0], False


async def x_get_token_count__mutmut_19(
    history: list[LLMMessage],
    tokenize_url: str,
    http: httpx.AsyncClient,
    timeout: float = 3.0,
    warn_once: _WarnOnce | None = None,
) -> tuple[int, bool]:
    """Return (token_count, is_exact) for the given history."""
    if not tokenize_url:
        return estimate_tokens(history)[0], False

    text = _serialise_for_tokenize(history)
    try:
        n_tokens = await _fetch_token_count(text, tokenize_url, http, timeout)
        if n_tokens > 0:
            if warn_once is None:
                warn_once.reset()
            return n_tokens, True
        logger.warning("token_counter: /tokenize returned n_tokens=0, falling back")
    except (TimeoutError, httpx.HTTPStatusError, httpx.RequestError, ValueError) as exc:
        _warn_tokenize_unavailable(exc, warn_once)

    return estimate_tokens(history)[0], False


async def x_get_token_count__mutmut_20(
    history: list[LLMMessage],
    tokenize_url: str,
    http: httpx.AsyncClient,
    timeout: float = 3.0,
    warn_once: _WarnOnce | None = None,
) -> tuple[int, bool]:
    """Return (token_count, is_exact) for the given history."""
    if not tokenize_url:
        return estimate_tokens(history)[0], False

    text = _serialise_for_tokenize(history)
    try:
        n_tokens = await _fetch_token_count(text, tokenize_url, http, timeout)
        if n_tokens > 0:
            if warn_once is not None:
                warn_once.reset()
            return n_tokens, False
        logger.warning("token_counter: /tokenize returned n_tokens=0, falling back")
    except (TimeoutError, httpx.HTTPStatusError, httpx.RequestError, ValueError) as exc:
        _warn_tokenize_unavailable(exc, warn_once)

    return estimate_tokens(history)[0], False


async def x_get_token_count__mutmut_21(
    history: list[LLMMessage],
    tokenize_url: str,
    http: httpx.AsyncClient,
    timeout: float = 3.0,
    warn_once: _WarnOnce | None = None,
) -> tuple[int, bool]:
    """Return (token_count, is_exact) for the given history."""
    if not tokenize_url:
        return estimate_tokens(history)[0], False

    text = _serialise_for_tokenize(history)
    try:
        n_tokens = await _fetch_token_count(text, tokenize_url, http, timeout)
        if n_tokens > 0:
            if warn_once is not None:
                warn_once.reset()
            return n_tokens, True
        logger.warning(None)
    except (TimeoutError, httpx.HTTPStatusError, httpx.RequestError, ValueError) as exc:
        _warn_tokenize_unavailable(exc, warn_once)

    return estimate_tokens(history)[0], False


async def x_get_token_count__mutmut_22(
    history: list[LLMMessage],
    tokenize_url: str,
    http: httpx.AsyncClient,
    timeout: float = 3.0,
    warn_once: _WarnOnce | None = None,
) -> tuple[int, bool]:
    """Return (token_count, is_exact) for the given history."""
    if not tokenize_url:
        return estimate_tokens(history)[0], False

    text = _serialise_for_tokenize(history)
    try:
        n_tokens = await _fetch_token_count(text, tokenize_url, http, timeout)
        if n_tokens > 0:
            if warn_once is not None:
                warn_once.reset()
            return n_tokens, True
        logger.warning("XXtoken_counter: /tokenize returned n_tokens=0, falling backXX")
    except (TimeoutError, httpx.HTTPStatusError, httpx.RequestError, ValueError) as exc:
        _warn_tokenize_unavailable(exc, warn_once)

    return estimate_tokens(history)[0], False


async def x_get_token_count__mutmut_23(
    history: list[LLMMessage],
    tokenize_url: str,
    http: httpx.AsyncClient,
    timeout: float = 3.0,
    warn_once: _WarnOnce | None = None,
) -> tuple[int, bool]:
    """Return (token_count, is_exact) for the given history."""
    if not tokenize_url:
        return estimate_tokens(history)[0], False

    text = _serialise_for_tokenize(history)
    try:
        n_tokens = await _fetch_token_count(text, tokenize_url, http, timeout)
        if n_tokens > 0:
            if warn_once is not None:
                warn_once.reset()
            return n_tokens, True
        logger.warning("TOKEN_COUNTER: /TOKENIZE RETURNED N_TOKENS=0, FALLING BACK")
    except (TimeoutError, httpx.HTTPStatusError, httpx.RequestError, ValueError) as exc:
        _warn_tokenize_unavailable(exc, warn_once)

    return estimate_tokens(history)[0], False


async def x_get_token_count__mutmut_24(
    history: list[LLMMessage],
    tokenize_url: str,
    http: httpx.AsyncClient,
    timeout: float = 3.0,
    warn_once: _WarnOnce | None = None,
) -> tuple[int, bool]:
    """Return (token_count, is_exact) for the given history."""
    if not tokenize_url:
        return estimate_tokens(history)[0], False

    text = _serialise_for_tokenize(history)
    try:
        n_tokens = await _fetch_token_count(text, tokenize_url, http, timeout)
        if n_tokens > 0:
            if warn_once is not None:
                warn_once.reset()
            return n_tokens, True
        logger.warning("token_counter: /tokenize returned n_tokens=0, falling back")
    except (TimeoutError, httpx.HTTPStatusError, httpx.RequestError, ValueError) as exc:
        _warn_tokenize_unavailable(None, warn_once)

    return estimate_tokens(history)[0], False


async def x_get_token_count__mutmut_25(
    history: list[LLMMessage],
    tokenize_url: str,
    http: httpx.AsyncClient,
    timeout: float = 3.0,
    warn_once: _WarnOnce | None = None,
) -> tuple[int, bool]:
    """Return (token_count, is_exact) for the given history."""
    if not tokenize_url:
        return estimate_tokens(history)[0], False

    text = _serialise_for_tokenize(history)
    try:
        n_tokens = await _fetch_token_count(text, tokenize_url, http, timeout)
        if n_tokens > 0:
            if warn_once is not None:
                warn_once.reset()
            return n_tokens, True
        logger.warning("token_counter: /tokenize returned n_tokens=0, falling back")
    except (TimeoutError, httpx.HTTPStatusError, httpx.RequestError, ValueError) as exc:
        _warn_tokenize_unavailable(exc, None)

    return estimate_tokens(history)[0], False


async def x_get_token_count__mutmut_26(
    history: list[LLMMessage],
    tokenize_url: str,
    http: httpx.AsyncClient,
    timeout: float = 3.0,
    warn_once: _WarnOnce | None = None,
) -> tuple[int, bool]:
    """Return (token_count, is_exact) for the given history."""
    if not tokenize_url:
        return estimate_tokens(history)[0], False

    text = _serialise_for_tokenize(history)
    try:
        n_tokens = await _fetch_token_count(text, tokenize_url, http, timeout)
        if n_tokens > 0:
            if warn_once is not None:
                warn_once.reset()
            return n_tokens, True
        logger.warning("token_counter: /tokenize returned n_tokens=0, falling back")
    except (TimeoutError, httpx.HTTPStatusError, httpx.RequestError, ValueError) as exc:
        _warn_tokenize_unavailable(warn_once)

    return estimate_tokens(history)[0], False


async def x_get_token_count__mutmut_27(
    history: list[LLMMessage],
    tokenize_url: str,
    http: httpx.AsyncClient,
    timeout: float = 3.0,
    warn_once: _WarnOnce | None = None,
) -> tuple[int, bool]:
    """Return (token_count, is_exact) for the given history."""
    if not tokenize_url:
        return estimate_tokens(history)[0], False

    text = _serialise_for_tokenize(history)
    try:
        n_tokens = await _fetch_token_count(text, tokenize_url, http, timeout)
        if n_tokens > 0:
            if warn_once is not None:
                warn_once.reset()
            return n_tokens, True
        logger.warning("token_counter: /tokenize returned n_tokens=0, falling back")
    except (TimeoutError, httpx.HTTPStatusError, httpx.RequestError, ValueError) as exc:
        _warn_tokenize_unavailable(exc, )

    return estimate_tokens(history)[0], False


async def x_get_token_count__mutmut_28(
    history: list[LLMMessage],
    tokenize_url: str,
    http: httpx.AsyncClient,
    timeout: float = 3.0,
    warn_once: _WarnOnce | None = None,
) -> tuple[int, bool]:
    """Return (token_count, is_exact) for the given history."""
    if not tokenize_url:
        return estimate_tokens(history)[0], False

    text = _serialise_for_tokenize(history)
    try:
        n_tokens = await _fetch_token_count(text, tokenize_url, http, timeout)
        if n_tokens > 0:
            if warn_once is not None:
                warn_once.reset()
            return n_tokens, True
        logger.warning("token_counter: /tokenize returned n_tokens=0, falling back")
    except (TimeoutError, httpx.HTTPStatusError, httpx.RequestError, ValueError) as exc:
        _warn_tokenize_unavailable(exc, warn_once)

    return estimate_tokens(None)[0], False


async def x_get_token_count__mutmut_29(
    history: list[LLMMessage],
    tokenize_url: str,
    http: httpx.AsyncClient,
    timeout: float = 3.0,
    warn_once: _WarnOnce | None = None,
) -> tuple[int, bool]:
    """Return (token_count, is_exact) for the given history."""
    if not tokenize_url:
        return estimate_tokens(history)[0], False

    text = _serialise_for_tokenize(history)
    try:
        n_tokens = await _fetch_token_count(text, tokenize_url, http, timeout)
        if n_tokens > 0:
            if warn_once is not None:
                warn_once.reset()
            return n_tokens, True
        logger.warning("token_counter: /tokenize returned n_tokens=0, falling back")
    except (TimeoutError, httpx.HTTPStatusError, httpx.RequestError, ValueError) as exc:
        _warn_tokenize_unavailable(exc, warn_once)

    return estimate_tokens(history)[1], False


async def x_get_token_count__mutmut_30(
    history: list[LLMMessage],
    tokenize_url: str,
    http: httpx.AsyncClient,
    timeout: float = 3.0,
    warn_once: _WarnOnce | None = None,
) -> tuple[int, bool]:
    """Return (token_count, is_exact) for the given history."""
    if not tokenize_url:
        return estimate_tokens(history)[0], False

    text = _serialise_for_tokenize(history)
    try:
        n_tokens = await _fetch_token_count(text, tokenize_url, http, timeout)
        if n_tokens > 0:
            if warn_once is not None:
                warn_once.reset()
            return n_tokens, True
        logger.warning("token_counter: /tokenize returned n_tokens=0, falling back")
    except (TimeoutError, httpx.HTTPStatusError, httpx.RequestError, ValueError) as exc:
        _warn_tokenize_unavailable(exc, warn_once)

    return estimate_tokens(history)[0], True

mutants_x_get_token_count__mutmut['_mutmut_orig'] = x_get_token_count__mutmut_orig # type: ignore # mutmut generated
mutants_x_get_token_count__mutmut['x_get_token_count__mutmut_1'] = x_get_token_count__mutmut_1 # type: ignore # mutmut generated
mutants_x_get_token_count__mutmut['x_get_token_count__mutmut_2'] = x_get_token_count__mutmut_2 # type: ignore # mutmut generated
mutants_x_get_token_count__mutmut['x_get_token_count__mutmut_3'] = x_get_token_count__mutmut_3 # type: ignore # mutmut generated
mutants_x_get_token_count__mutmut['x_get_token_count__mutmut_4'] = x_get_token_count__mutmut_4 # type: ignore # mutmut generated
mutants_x_get_token_count__mutmut['x_get_token_count__mutmut_5'] = x_get_token_count__mutmut_5 # type: ignore # mutmut generated
mutants_x_get_token_count__mutmut['x_get_token_count__mutmut_6'] = x_get_token_count__mutmut_6 # type: ignore # mutmut generated
mutants_x_get_token_count__mutmut['x_get_token_count__mutmut_7'] = x_get_token_count__mutmut_7 # type: ignore # mutmut generated
mutants_x_get_token_count__mutmut['x_get_token_count__mutmut_8'] = x_get_token_count__mutmut_8 # type: ignore # mutmut generated
mutants_x_get_token_count__mutmut['x_get_token_count__mutmut_9'] = x_get_token_count__mutmut_9 # type: ignore # mutmut generated
mutants_x_get_token_count__mutmut['x_get_token_count__mutmut_10'] = x_get_token_count__mutmut_10 # type: ignore # mutmut generated
mutants_x_get_token_count__mutmut['x_get_token_count__mutmut_11'] = x_get_token_count__mutmut_11 # type: ignore # mutmut generated
mutants_x_get_token_count__mutmut['x_get_token_count__mutmut_12'] = x_get_token_count__mutmut_12 # type: ignore # mutmut generated
mutants_x_get_token_count__mutmut['x_get_token_count__mutmut_13'] = x_get_token_count__mutmut_13 # type: ignore # mutmut generated
mutants_x_get_token_count__mutmut['x_get_token_count__mutmut_14'] = x_get_token_count__mutmut_14 # type: ignore # mutmut generated
mutants_x_get_token_count__mutmut['x_get_token_count__mutmut_15'] = x_get_token_count__mutmut_15 # type: ignore # mutmut generated
mutants_x_get_token_count__mutmut['x_get_token_count__mutmut_16'] = x_get_token_count__mutmut_16 # type: ignore # mutmut generated
mutants_x_get_token_count__mutmut['x_get_token_count__mutmut_17'] = x_get_token_count__mutmut_17 # type: ignore # mutmut generated
mutants_x_get_token_count__mutmut['x_get_token_count__mutmut_18'] = x_get_token_count__mutmut_18 # type: ignore # mutmut generated
mutants_x_get_token_count__mutmut['x_get_token_count__mutmut_19'] = x_get_token_count__mutmut_19 # type: ignore # mutmut generated
mutants_x_get_token_count__mutmut['x_get_token_count__mutmut_20'] = x_get_token_count__mutmut_20 # type: ignore # mutmut generated
mutants_x_get_token_count__mutmut['x_get_token_count__mutmut_21'] = x_get_token_count__mutmut_21 # type: ignore # mutmut generated
mutants_x_get_token_count__mutmut['x_get_token_count__mutmut_22'] = x_get_token_count__mutmut_22 # type: ignore # mutmut generated
mutants_x_get_token_count__mutmut['x_get_token_count__mutmut_23'] = x_get_token_count__mutmut_23 # type: ignore # mutmut generated
mutants_x_get_token_count__mutmut['x_get_token_count__mutmut_24'] = x_get_token_count__mutmut_24 # type: ignore # mutmut generated
mutants_x_get_token_count__mutmut['x_get_token_count__mutmut_25'] = x_get_token_count__mutmut_25 # type: ignore # mutmut generated
mutants_x_get_token_count__mutmut['x_get_token_count__mutmut_26'] = x_get_token_count__mutmut_26 # type: ignore # mutmut generated
mutants_x_get_token_count__mutmut['x_get_token_count__mutmut_27'] = x_get_token_count__mutmut_27 # type: ignore # mutmut generated
mutants_x_get_token_count__mutmut['x_get_token_count__mutmut_28'] = x_get_token_count__mutmut_28 # type: ignore # mutmut generated
mutants_x_get_token_count__mutmut['x_get_token_count__mutmut_29'] = x_get_token_count__mutmut_29 # type: ignore # mutmut generated
mutants_x_get_token_count__mutmut['x_get_token_count__mutmut_30'] = x_get_token_count__mutmut_30 # type: ignore # mutmut generated
mutants_x__fetch_token_count__mutmut: MutantDict = {}  # type: ignore


@_mutmut_mutated(mutants_x__fetch_token_count__mutmut)
async def _fetch_token_count(
    text: str,
    tokenize_url: str,
    http: httpx.AsyncClient,
    timeout: float,
) -> int:
    """POST to /tokenize and extract n_tokens from the response."""
    resp = await http.post(
        tokenize_url,
        content=_json_dumps({"content": text}).encode(),
        headers={"Content-Type": "application/json"},
        timeout=timeout,
    )
    resp.raise_for_status()
    data = parse_http_json(resp)
    return _extract_n_tokens(data)


async def x__fetch_token_count__mutmut_orig(
    text: str,
    tokenize_url: str,
    http: httpx.AsyncClient,
    timeout: float,
) -> int:
    """POST to /tokenize and extract n_tokens from the response."""
    resp = await http.post(
        tokenize_url,
        content=_json_dumps({"content": text}).encode(),
        headers={"Content-Type": "application/json"},
        timeout=timeout,
    )
    resp.raise_for_status()
    data = parse_http_json(resp)
    return _extract_n_tokens(data)


async def x__fetch_token_count__mutmut_1(
    text: str,
    tokenize_url: str,
    http: httpx.AsyncClient,
    timeout: float,
) -> int:
    """POST to /tokenize and extract n_tokens from the response."""
    resp = None
    resp.raise_for_status()
    data = parse_http_json(resp)
    return _extract_n_tokens(data)


async def x__fetch_token_count__mutmut_2(
    text: str,
    tokenize_url: str,
    http: httpx.AsyncClient,
    timeout: float,
) -> int:
    """POST to /tokenize and extract n_tokens from the response."""
    resp = await http.post(
        None,
        content=_json_dumps({"content": text}).encode(),
        headers={"Content-Type": "application/json"},
        timeout=timeout,
    )
    resp.raise_for_status()
    data = parse_http_json(resp)
    return _extract_n_tokens(data)


async def x__fetch_token_count__mutmut_3(
    text: str,
    tokenize_url: str,
    http: httpx.AsyncClient,
    timeout: float,
) -> int:
    """POST to /tokenize and extract n_tokens from the response."""
    resp = await http.post(
        tokenize_url,
        content=None,
        headers={"Content-Type": "application/json"},
        timeout=timeout,
    )
    resp.raise_for_status()
    data = parse_http_json(resp)
    return _extract_n_tokens(data)


async def x__fetch_token_count__mutmut_4(
    text: str,
    tokenize_url: str,
    http: httpx.AsyncClient,
    timeout: float,
) -> int:
    """POST to /tokenize and extract n_tokens from the response."""
    resp = await http.post(
        tokenize_url,
        content=_json_dumps({"content": text}).encode(),
        headers=None,
        timeout=timeout,
    )
    resp.raise_for_status()
    data = parse_http_json(resp)
    return _extract_n_tokens(data)


async def x__fetch_token_count__mutmut_5(
    text: str,
    tokenize_url: str,
    http: httpx.AsyncClient,
    timeout: float,
) -> int:
    """POST to /tokenize and extract n_tokens from the response."""
    resp = await http.post(
        tokenize_url,
        content=_json_dumps({"content": text}).encode(),
        headers={"Content-Type": "application/json"},
        timeout=None,
    )
    resp.raise_for_status()
    data = parse_http_json(resp)
    return _extract_n_tokens(data)


async def x__fetch_token_count__mutmut_6(
    text: str,
    tokenize_url: str,
    http: httpx.AsyncClient,
    timeout: float,
) -> int:
    """POST to /tokenize and extract n_tokens from the response."""
    resp = await http.post(
        content=_json_dumps({"content": text}).encode(),
        headers={"Content-Type": "application/json"},
        timeout=timeout,
    )
    resp.raise_for_status()
    data = parse_http_json(resp)
    return _extract_n_tokens(data)


async def x__fetch_token_count__mutmut_7(
    text: str,
    tokenize_url: str,
    http: httpx.AsyncClient,
    timeout: float,
) -> int:
    """POST to /tokenize and extract n_tokens from the response."""
    resp = await http.post(
        tokenize_url,
        headers={"Content-Type": "application/json"},
        timeout=timeout,
    )
    resp.raise_for_status()
    data = parse_http_json(resp)
    return _extract_n_tokens(data)


async def x__fetch_token_count__mutmut_8(
    text: str,
    tokenize_url: str,
    http: httpx.AsyncClient,
    timeout: float,
) -> int:
    """POST to /tokenize and extract n_tokens from the response."""
    resp = await http.post(
        tokenize_url,
        content=_json_dumps({"content": text}).encode(),
        timeout=timeout,
    )
    resp.raise_for_status()
    data = parse_http_json(resp)
    return _extract_n_tokens(data)


async def x__fetch_token_count__mutmut_9(
    text: str,
    tokenize_url: str,
    http: httpx.AsyncClient,
    timeout: float,
) -> int:
    """POST to /tokenize and extract n_tokens from the response."""
    resp = await http.post(
        tokenize_url,
        content=_json_dumps({"content": text}).encode(),
        headers={"Content-Type": "application/json"},
        )
    resp.raise_for_status()
    data = parse_http_json(resp)
    return _extract_n_tokens(data)


async def x__fetch_token_count__mutmut_10(
    text: str,
    tokenize_url: str,
    http: httpx.AsyncClient,
    timeout: float,
) -> int:
    """POST to /tokenize and extract n_tokens from the response."""
    resp = await http.post(
        tokenize_url,
        content=_json_dumps(None).encode(),
        headers={"Content-Type": "application/json"},
        timeout=timeout,
    )
    resp.raise_for_status()
    data = parse_http_json(resp)
    return _extract_n_tokens(data)


async def x__fetch_token_count__mutmut_11(
    text: str,
    tokenize_url: str,
    http: httpx.AsyncClient,
    timeout: float,
) -> int:
    """POST to /tokenize and extract n_tokens from the response."""
    resp = await http.post(
        tokenize_url,
        content=_json_dumps({"XXcontentXX": text}).encode(),
        headers={"Content-Type": "application/json"},
        timeout=timeout,
    )
    resp.raise_for_status()
    data = parse_http_json(resp)
    return _extract_n_tokens(data)


async def x__fetch_token_count__mutmut_12(
    text: str,
    tokenize_url: str,
    http: httpx.AsyncClient,
    timeout: float,
) -> int:
    """POST to /tokenize and extract n_tokens from the response."""
    resp = await http.post(
        tokenize_url,
        content=_json_dumps({"CONTENT": text}).encode(),
        headers={"Content-Type": "application/json"},
        timeout=timeout,
    )
    resp.raise_for_status()
    data = parse_http_json(resp)
    return _extract_n_tokens(data)


async def x__fetch_token_count__mutmut_13(
    text: str,
    tokenize_url: str,
    http: httpx.AsyncClient,
    timeout: float,
) -> int:
    """POST to /tokenize and extract n_tokens from the response."""
    resp = await http.post(
        tokenize_url,
        content=_json_dumps({"content": text}).encode(),
        headers={"XXContent-TypeXX": "application/json"},
        timeout=timeout,
    )
    resp.raise_for_status()
    data = parse_http_json(resp)
    return _extract_n_tokens(data)


async def x__fetch_token_count__mutmut_14(
    text: str,
    tokenize_url: str,
    http: httpx.AsyncClient,
    timeout: float,
) -> int:
    """POST to /tokenize and extract n_tokens from the response."""
    resp = await http.post(
        tokenize_url,
        content=_json_dumps({"content": text}).encode(),
        headers={"content-type": "application/json"},
        timeout=timeout,
    )
    resp.raise_for_status()
    data = parse_http_json(resp)
    return _extract_n_tokens(data)


async def x__fetch_token_count__mutmut_15(
    text: str,
    tokenize_url: str,
    http: httpx.AsyncClient,
    timeout: float,
) -> int:
    """POST to /tokenize and extract n_tokens from the response."""
    resp = await http.post(
        tokenize_url,
        content=_json_dumps({"content": text}).encode(),
        headers={"CONTENT-TYPE": "application/json"},
        timeout=timeout,
    )
    resp.raise_for_status()
    data = parse_http_json(resp)
    return _extract_n_tokens(data)


async def x__fetch_token_count__mutmut_16(
    text: str,
    tokenize_url: str,
    http: httpx.AsyncClient,
    timeout: float,
) -> int:
    """POST to /tokenize and extract n_tokens from the response."""
    resp = await http.post(
        tokenize_url,
        content=_json_dumps({"content": text}).encode(),
        headers={"Content-Type": "XXapplication/jsonXX"},
        timeout=timeout,
    )
    resp.raise_for_status()
    data = parse_http_json(resp)
    return _extract_n_tokens(data)


async def x__fetch_token_count__mutmut_17(
    text: str,
    tokenize_url: str,
    http: httpx.AsyncClient,
    timeout: float,
) -> int:
    """POST to /tokenize and extract n_tokens from the response."""
    resp = await http.post(
        tokenize_url,
        content=_json_dumps({"content": text}).encode(),
        headers={"Content-Type": "APPLICATION/JSON"},
        timeout=timeout,
    )
    resp.raise_for_status()
    data = parse_http_json(resp)
    return _extract_n_tokens(data)


async def x__fetch_token_count__mutmut_18(
    text: str,
    tokenize_url: str,
    http: httpx.AsyncClient,
    timeout: float,
) -> int:
    """POST to /tokenize and extract n_tokens from the response."""
    resp = await http.post(
        tokenize_url,
        content=_json_dumps({"content": text}).encode(),
        headers={"Content-Type": "application/json"},
        timeout=timeout,
    )
    resp.raise_for_status()
    data = None
    return _extract_n_tokens(data)


async def x__fetch_token_count__mutmut_19(
    text: str,
    tokenize_url: str,
    http: httpx.AsyncClient,
    timeout: float,
) -> int:
    """POST to /tokenize and extract n_tokens from the response."""
    resp = await http.post(
        tokenize_url,
        content=_json_dumps({"content": text}).encode(),
        headers={"Content-Type": "application/json"},
        timeout=timeout,
    )
    resp.raise_for_status()
    data = parse_http_json(None)
    return _extract_n_tokens(data)


async def x__fetch_token_count__mutmut_20(
    text: str,
    tokenize_url: str,
    http: httpx.AsyncClient,
    timeout: float,
) -> int:
    """POST to /tokenize and extract n_tokens from the response."""
    resp = await http.post(
        tokenize_url,
        content=_json_dumps({"content": text}).encode(),
        headers={"Content-Type": "application/json"},
        timeout=timeout,
    )
    resp.raise_for_status()
    data = parse_http_json(resp)
    return _extract_n_tokens(None)

mutants_x__fetch_token_count__mutmut['_mutmut_orig'] = x__fetch_token_count__mutmut_orig # type: ignore # mutmut generated
mutants_x__fetch_token_count__mutmut['x__fetch_token_count__mutmut_1'] = x__fetch_token_count__mutmut_1 # type: ignore # mutmut generated
mutants_x__fetch_token_count__mutmut['x__fetch_token_count__mutmut_2'] = x__fetch_token_count__mutmut_2 # type: ignore # mutmut generated
mutants_x__fetch_token_count__mutmut['x__fetch_token_count__mutmut_3'] = x__fetch_token_count__mutmut_3 # type: ignore # mutmut generated
mutants_x__fetch_token_count__mutmut['x__fetch_token_count__mutmut_4'] = x__fetch_token_count__mutmut_4 # type: ignore # mutmut generated
mutants_x__fetch_token_count__mutmut['x__fetch_token_count__mutmut_5'] = x__fetch_token_count__mutmut_5 # type: ignore # mutmut generated
mutants_x__fetch_token_count__mutmut['x__fetch_token_count__mutmut_6'] = x__fetch_token_count__mutmut_6 # type: ignore # mutmut generated
mutants_x__fetch_token_count__mutmut['x__fetch_token_count__mutmut_7'] = x__fetch_token_count__mutmut_7 # type: ignore # mutmut generated
mutants_x__fetch_token_count__mutmut['x__fetch_token_count__mutmut_8'] = x__fetch_token_count__mutmut_8 # type: ignore # mutmut generated
mutants_x__fetch_token_count__mutmut['x__fetch_token_count__mutmut_9'] = x__fetch_token_count__mutmut_9 # type: ignore # mutmut generated
mutants_x__fetch_token_count__mutmut['x__fetch_token_count__mutmut_10'] = x__fetch_token_count__mutmut_10 # type: ignore # mutmut generated
mutants_x__fetch_token_count__mutmut['x__fetch_token_count__mutmut_11'] = x__fetch_token_count__mutmut_11 # type: ignore # mutmut generated
mutants_x__fetch_token_count__mutmut['x__fetch_token_count__mutmut_12'] = x__fetch_token_count__mutmut_12 # type: ignore # mutmut generated
mutants_x__fetch_token_count__mutmut['x__fetch_token_count__mutmut_13'] = x__fetch_token_count__mutmut_13 # type: ignore # mutmut generated
mutants_x__fetch_token_count__mutmut['x__fetch_token_count__mutmut_14'] = x__fetch_token_count__mutmut_14 # type: ignore # mutmut generated
mutants_x__fetch_token_count__mutmut['x__fetch_token_count__mutmut_15'] = x__fetch_token_count__mutmut_15 # type: ignore # mutmut generated
mutants_x__fetch_token_count__mutmut['x__fetch_token_count__mutmut_16'] = x__fetch_token_count__mutmut_16 # type: ignore # mutmut generated
mutants_x__fetch_token_count__mutmut['x__fetch_token_count__mutmut_17'] = x__fetch_token_count__mutmut_17 # type: ignore # mutmut generated
mutants_x__fetch_token_count__mutmut['x__fetch_token_count__mutmut_18'] = x__fetch_token_count__mutmut_18 # type: ignore # mutmut generated
mutants_x__fetch_token_count__mutmut['x__fetch_token_count__mutmut_19'] = x__fetch_token_count__mutmut_19 # type: ignore # mutmut generated
mutants_x__fetch_token_count__mutmut['x__fetch_token_count__mutmut_20'] = x__fetch_token_count__mutmut_20 # type: ignore # mutmut generated
mutants_x__extract_n_tokens__mutmut: MutantDict = {}  # type: ignore


@_mutmut_mutated(mutants_x__extract_n_tokens__mutmut)
def _extract_n_tokens(data: dict[str, object]) -> int:
    """Extract the token count from a decoded /tokenize response payload."""
    n_tokens_raw = data.get("n_tokens")
    tokens_raw = data.get("tokens")
    if isinstance(n_tokens_raw, int) and n_tokens_raw > 0:
        return n_tokens_raw
    if isinstance(tokens_raw, list):
        return len(tokens_raw)
    return 0


def x__extract_n_tokens__mutmut_orig(data: dict[str, object]) -> int:
    """Extract the token count from a decoded /tokenize response payload."""
    n_tokens_raw = data.get("n_tokens")
    tokens_raw = data.get("tokens")
    if isinstance(n_tokens_raw, int) and n_tokens_raw > 0:
        return n_tokens_raw
    if isinstance(tokens_raw, list):
        return len(tokens_raw)
    return 0


def x__extract_n_tokens__mutmut_1(data: dict[str, object]) -> int:
    """Extract the token count from a decoded /tokenize response payload."""
    n_tokens_raw = None
    tokens_raw = data.get("tokens")
    if isinstance(n_tokens_raw, int) and n_tokens_raw > 0:
        return n_tokens_raw
    if isinstance(tokens_raw, list):
        return len(tokens_raw)
    return 0


def x__extract_n_tokens__mutmut_2(data: dict[str, object]) -> int:
    """Extract the token count from a decoded /tokenize response payload."""
    n_tokens_raw = data.get(None)
    tokens_raw = data.get("tokens")
    if isinstance(n_tokens_raw, int) and n_tokens_raw > 0:
        return n_tokens_raw
    if isinstance(tokens_raw, list):
        return len(tokens_raw)
    return 0


def x__extract_n_tokens__mutmut_3(data: dict[str, object]) -> int:
    """Extract the token count from a decoded /tokenize response payload."""
    n_tokens_raw = data.get("XXn_tokensXX")
    tokens_raw = data.get("tokens")
    if isinstance(n_tokens_raw, int) and n_tokens_raw > 0:
        return n_tokens_raw
    if isinstance(tokens_raw, list):
        return len(tokens_raw)
    return 0


def x__extract_n_tokens__mutmut_4(data: dict[str, object]) -> int:
    """Extract the token count from a decoded /tokenize response payload."""
    n_tokens_raw = data.get("N_TOKENS")
    tokens_raw = data.get("tokens")
    if isinstance(n_tokens_raw, int) and n_tokens_raw > 0:
        return n_tokens_raw
    if isinstance(tokens_raw, list):
        return len(tokens_raw)
    return 0


def x__extract_n_tokens__mutmut_5(data: dict[str, object]) -> int:
    """Extract the token count from a decoded /tokenize response payload."""
    n_tokens_raw = data.get("n_tokens")
    tokens_raw = None
    if isinstance(n_tokens_raw, int) and n_tokens_raw > 0:
        return n_tokens_raw
    if isinstance(tokens_raw, list):
        return len(tokens_raw)
    return 0


def x__extract_n_tokens__mutmut_6(data: dict[str, object]) -> int:
    """Extract the token count from a decoded /tokenize response payload."""
    n_tokens_raw = data.get("n_tokens")
    tokens_raw = data.get(None)
    if isinstance(n_tokens_raw, int) and n_tokens_raw > 0:
        return n_tokens_raw
    if isinstance(tokens_raw, list):
        return len(tokens_raw)
    return 0


def x__extract_n_tokens__mutmut_7(data: dict[str, object]) -> int:
    """Extract the token count from a decoded /tokenize response payload."""
    n_tokens_raw = data.get("n_tokens")
    tokens_raw = data.get("XXtokensXX")
    if isinstance(n_tokens_raw, int) and n_tokens_raw > 0:
        return n_tokens_raw
    if isinstance(tokens_raw, list):
        return len(tokens_raw)
    return 0


def x__extract_n_tokens__mutmut_8(data: dict[str, object]) -> int:
    """Extract the token count from a decoded /tokenize response payload."""
    n_tokens_raw = data.get("n_tokens")
    tokens_raw = data.get("TOKENS")
    if isinstance(n_tokens_raw, int) and n_tokens_raw > 0:
        return n_tokens_raw
    if isinstance(tokens_raw, list):
        return len(tokens_raw)
    return 0


def x__extract_n_tokens__mutmut_9(data: dict[str, object]) -> int:
    """Extract the token count from a decoded /tokenize response payload."""
    n_tokens_raw = data.get("n_tokens")
    tokens_raw = data.get("tokens")
    if isinstance(n_tokens_raw, int) or n_tokens_raw > 0:
        return n_tokens_raw
    if isinstance(tokens_raw, list):
        return len(tokens_raw)
    return 0


def x__extract_n_tokens__mutmut_10(data: dict[str, object]) -> int:
    """Extract the token count from a decoded /tokenize response payload."""
    n_tokens_raw = data.get("n_tokens")
    tokens_raw = data.get("tokens")
    if isinstance(n_tokens_raw, int) and n_tokens_raw >= 0:
        return n_tokens_raw
    if isinstance(tokens_raw, list):
        return len(tokens_raw)
    return 0


def x__extract_n_tokens__mutmut_11(data: dict[str, object]) -> int:
    """Extract the token count from a decoded /tokenize response payload."""
    n_tokens_raw = data.get("n_tokens")
    tokens_raw = data.get("tokens")
    if isinstance(n_tokens_raw, int) and n_tokens_raw > 1:
        return n_tokens_raw
    if isinstance(tokens_raw, list):
        return len(tokens_raw)
    return 0


def x__extract_n_tokens__mutmut_12(data: dict[str, object]) -> int:
    """Extract the token count from a decoded /tokenize response payload."""
    n_tokens_raw = data.get("n_tokens")
    tokens_raw = data.get("tokens")
    if isinstance(n_tokens_raw, int) and n_tokens_raw > 0:
        return n_tokens_raw
    if isinstance(tokens_raw, list):
        return len(tokens_raw)
    return 1

mutants_x__extract_n_tokens__mutmut['_mutmut_orig'] = x__extract_n_tokens__mutmut_orig # type: ignore # mutmut generated
mutants_x__extract_n_tokens__mutmut['x__extract_n_tokens__mutmut_1'] = x__extract_n_tokens__mutmut_1 # type: ignore # mutmut generated
mutants_x__extract_n_tokens__mutmut['x__extract_n_tokens__mutmut_2'] = x__extract_n_tokens__mutmut_2 # type: ignore # mutmut generated
mutants_x__extract_n_tokens__mutmut['x__extract_n_tokens__mutmut_3'] = x__extract_n_tokens__mutmut_3 # type: ignore # mutmut generated
mutants_x__extract_n_tokens__mutmut['x__extract_n_tokens__mutmut_4'] = x__extract_n_tokens__mutmut_4 # type: ignore # mutmut generated
mutants_x__extract_n_tokens__mutmut['x__extract_n_tokens__mutmut_5'] = x__extract_n_tokens__mutmut_5 # type: ignore # mutmut generated
mutants_x__extract_n_tokens__mutmut['x__extract_n_tokens__mutmut_6'] = x__extract_n_tokens__mutmut_6 # type: ignore # mutmut generated
mutants_x__extract_n_tokens__mutmut['x__extract_n_tokens__mutmut_7'] = x__extract_n_tokens__mutmut_7 # type: ignore # mutmut generated
mutants_x__extract_n_tokens__mutmut['x__extract_n_tokens__mutmut_8'] = x__extract_n_tokens__mutmut_8 # type: ignore # mutmut generated
mutants_x__extract_n_tokens__mutmut['x__extract_n_tokens__mutmut_9'] = x__extract_n_tokens__mutmut_9 # type: ignore # mutmut generated
mutants_x__extract_n_tokens__mutmut['x__extract_n_tokens__mutmut_10'] = x__extract_n_tokens__mutmut_10 # type: ignore # mutmut generated
mutants_x__extract_n_tokens__mutmut['x__extract_n_tokens__mutmut_11'] = x__extract_n_tokens__mutmut_11 # type: ignore # mutmut generated
mutants_x__extract_n_tokens__mutmut['x__extract_n_tokens__mutmut_12'] = x__extract_n_tokens__mutmut_12 # type: ignore # mutmut generated
mutants_x__warn_tokenize_unavailable__mutmut: MutantDict = {}  # type: ignore


@_mutmut_mutated(mutants_x__warn_tokenize_unavailable__mutmut)
def _warn_tokenize_unavailable(
    exc: Exception,
    warn_once: _WarnOnce | None = None,
) -> None:
    """Log a warning when /tokenize is unavailable."""
    msg = "token_counter: /tokenize unavailable (%s), using category-aware estimate"
    if warn_once is not None:
        warn_once.log(msg, exc)
    else:
        logger.warning(msg, exc)


def x__warn_tokenize_unavailable__mutmut_orig(
    exc: Exception,
    warn_once: _WarnOnce | None = None,
) -> None:
    """Log a warning when /tokenize is unavailable."""
    msg = "token_counter: /tokenize unavailable (%s), using category-aware estimate"
    if warn_once is not None:
        warn_once.log(msg, exc)
    else:
        logger.warning(msg, exc)


def x__warn_tokenize_unavailable__mutmut_1(
    exc: Exception,
    warn_once: _WarnOnce | None = None,
) -> None:
    """Log a warning when /tokenize is unavailable."""
    msg = None
    if warn_once is not None:
        warn_once.log(msg, exc)
    else:
        logger.warning(msg, exc)


def x__warn_tokenize_unavailable__mutmut_2(
    exc: Exception,
    warn_once: _WarnOnce | None = None,
) -> None:
    """Log a warning when /tokenize is unavailable."""
    msg = "XXtoken_counter: /tokenize unavailable (%s), using category-aware estimateXX"
    if warn_once is not None:
        warn_once.log(msg, exc)
    else:
        logger.warning(msg, exc)


def x__warn_tokenize_unavailable__mutmut_3(
    exc: Exception,
    warn_once: _WarnOnce | None = None,
) -> None:
    """Log a warning when /tokenize is unavailable."""
    msg = "TOKEN_COUNTER: /TOKENIZE UNAVAILABLE (%S), USING CATEGORY-AWARE ESTIMATE"
    if warn_once is not None:
        warn_once.log(msg, exc)
    else:
        logger.warning(msg, exc)


def x__warn_tokenize_unavailable__mutmut_4(
    exc: Exception,
    warn_once: _WarnOnce | None = None,
) -> None:
    """Log a warning when /tokenize is unavailable."""
    msg = "token_counter: /tokenize unavailable (%s), using category-aware estimate"
    if warn_once is None:
        warn_once.log(msg, exc)
    else:
        logger.warning(msg, exc)


def x__warn_tokenize_unavailable__mutmut_5(
    exc: Exception,
    warn_once: _WarnOnce | None = None,
) -> None:
    """Log a warning when /tokenize is unavailable."""
    msg = "token_counter: /tokenize unavailable (%s), using category-aware estimate"
    if warn_once is not None:
        warn_once.log(None, exc)
    else:
        logger.warning(msg, exc)


def x__warn_tokenize_unavailable__mutmut_6(
    exc: Exception,
    warn_once: _WarnOnce | None = None,
) -> None:
    """Log a warning when /tokenize is unavailable."""
    msg = "token_counter: /tokenize unavailable (%s), using category-aware estimate"
    if warn_once is not None:
        warn_once.log(msg, None)
    else:
        logger.warning(msg, exc)


def x__warn_tokenize_unavailable__mutmut_7(
    exc: Exception,
    warn_once: _WarnOnce | None = None,
) -> None:
    """Log a warning when /tokenize is unavailable."""
    msg = "token_counter: /tokenize unavailable (%s), using category-aware estimate"
    if warn_once is not None:
        warn_once.log(exc)
    else:
        logger.warning(msg, exc)


def x__warn_tokenize_unavailable__mutmut_8(
    exc: Exception,
    warn_once: _WarnOnce | None = None,
) -> None:
    """Log a warning when /tokenize is unavailable."""
    msg = "token_counter: /tokenize unavailable (%s), using category-aware estimate"
    if warn_once is not None:
        warn_once.log(msg, )
    else:
        logger.warning(msg, exc)


def x__warn_tokenize_unavailable__mutmut_9(
    exc: Exception,
    warn_once: _WarnOnce | None = None,
) -> None:
    """Log a warning when /tokenize is unavailable."""
    msg = "token_counter: /tokenize unavailable (%s), using category-aware estimate"
    if warn_once is not None:
        warn_once.log(msg, exc)
    else:
        logger.warning(None, exc)


def x__warn_tokenize_unavailable__mutmut_10(
    exc: Exception,
    warn_once: _WarnOnce | None = None,
) -> None:
    """Log a warning when /tokenize is unavailable."""
    msg = "token_counter: /tokenize unavailable (%s), using category-aware estimate"
    if warn_once is not None:
        warn_once.log(msg, exc)
    else:
        logger.warning(msg, None)


def x__warn_tokenize_unavailable__mutmut_11(
    exc: Exception,
    warn_once: _WarnOnce | None = None,
) -> None:
    """Log a warning when /tokenize is unavailable."""
    msg = "token_counter: /tokenize unavailable (%s), using category-aware estimate"
    if warn_once is not None:
        warn_once.log(msg, exc)
    else:
        logger.warning(exc)


def x__warn_tokenize_unavailable__mutmut_12(
    exc: Exception,
    warn_once: _WarnOnce | None = None,
) -> None:
    """Log a warning when /tokenize is unavailable."""
    msg = "token_counter: /tokenize unavailable (%s), using category-aware estimate"
    if warn_once is not None:
        warn_once.log(msg, exc)
    else:
        logger.warning(msg, )

mutants_x__warn_tokenize_unavailable__mutmut['_mutmut_orig'] = x__warn_tokenize_unavailable__mutmut_orig # type: ignore # mutmut generated
mutants_x__warn_tokenize_unavailable__mutmut['x__warn_tokenize_unavailable__mutmut_1'] = x__warn_tokenize_unavailable__mutmut_1 # type: ignore # mutmut generated
mutants_x__warn_tokenize_unavailable__mutmut['x__warn_tokenize_unavailable__mutmut_2'] = x__warn_tokenize_unavailable__mutmut_2 # type: ignore # mutmut generated
mutants_x__warn_tokenize_unavailable__mutmut['x__warn_tokenize_unavailable__mutmut_3'] = x__warn_tokenize_unavailable__mutmut_3 # type: ignore # mutmut generated
mutants_x__warn_tokenize_unavailable__mutmut['x__warn_tokenize_unavailable__mutmut_4'] = x__warn_tokenize_unavailable__mutmut_4 # type: ignore # mutmut generated
mutants_x__warn_tokenize_unavailable__mutmut['x__warn_tokenize_unavailable__mutmut_5'] = x__warn_tokenize_unavailable__mutmut_5 # type: ignore # mutmut generated
mutants_x__warn_tokenize_unavailable__mutmut['x__warn_tokenize_unavailable__mutmut_6'] = x__warn_tokenize_unavailable__mutmut_6 # type: ignore # mutmut generated
mutants_x__warn_tokenize_unavailable__mutmut['x__warn_tokenize_unavailable__mutmut_7'] = x__warn_tokenize_unavailable__mutmut_7 # type: ignore # mutmut generated
mutants_x__warn_tokenize_unavailable__mutmut['x__warn_tokenize_unavailable__mutmut_8'] = x__warn_tokenize_unavailable__mutmut_8 # type: ignore # mutmut generated
mutants_x__warn_tokenize_unavailable__mutmut['x__warn_tokenize_unavailable__mutmut_9'] = x__warn_tokenize_unavailable__mutmut_9 # type: ignore # mutmut generated
mutants_x__warn_tokenize_unavailable__mutmut['x__warn_tokenize_unavailable__mutmut_10'] = x__warn_tokenize_unavailable__mutmut_10 # type: ignore # mutmut generated
mutants_x__warn_tokenize_unavailable__mutmut['x__warn_tokenize_unavailable__mutmut_11'] = x__warn_tokenize_unavailable__mutmut_11 # type: ignore # mutmut generated
mutants_x__warn_tokenize_unavailable__mutmut['x__warn_tokenize_unavailable__mutmut_12'] = x__warn_tokenize_unavailable__mutmut_12 # type: ignore # mutmut generated
