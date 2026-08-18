#!/usr/bin/env python3
"""scripts/shared/llm_payload.py — LLM request/response payload construction."""

from collections.abc import Callable
from typing import Any, cast

import orjson

from shared.llm_sse_helpers import LlmSseHelpers
from shared.llm_types import LLMResponse
from shared.types import LLMMessage


from mutmut.mutation.trampoline import wrap_in_trampoline as _mutmut_mutated, MutantDict
mutants_xǁLlmPayloadHandlerǁbuild_payload__mutmut: MutantDict = {}  # type: ignore
mutants_xǁLlmPayloadHandlerǁ_require_dict_field__mutmut: MutantDict = {}  # type: ignore
mutants_xǁLlmPayloadHandlerǁparse_response__mutmut: MutantDict = {}  # type: ignore
mutants_xǁLlmPayloadHandlerǁparse_non_stream_response__mutmut: MutantDict = {}  # type: ignore


class LlmPayloadHandler:
    """Construct LLM request payloads and parse responses."""

    @staticmethod
    @_mutmut_mutated(mutants_xǁLlmPayloadHandlerǁbuild_payload__mutmut)
    def build_payload(
        history: list[LLMMessage],
        tool_defs: list[dict[str, Any]],
        temperature: float,
        max_tokens: int,
        stream: bool = False,
    ) -> dict[str, Any]:
        """Build the request payload for a chat completion request."""
        payload: dict[str, Any] = {
            "messages": history,
            "tools": tool_defs,
            "tool_choice": "auto",
            "temperature": temperature,
            "max_tokens": max_tokens,
        }
        if stream:
            payload["stream"] = True
        return payload

    @staticmethod
    def xǁLlmPayloadHandlerǁbuild_payload__mutmut_orig(
        history: list[LLMMessage],
        tool_defs: list[dict[str, Any]],
        temperature: float,
        max_tokens: int,
        stream: bool = False,
    ) -> dict[str, Any]:
        """Build the request payload for a chat completion request."""
        payload: dict[str, Any] = {
            "messages": history,
            "tools": tool_defs,
            "tool_choice": "auto",
            "temperature": temperature,
            "max_tokens": max_tokens,
        }
        if stream:
            payload["stream"] = True
        return payload

    @staticmethod
    def xǁLlmPayloadHandlerǁbuild_payload__mutmut_1(
        history: list[LLMMessage],
        tool_defs: list[dict[str, Any]],
        temperature: float,
        max_tokens: int,
        stream: bool = True,
    ) -> dict[str, Any]:
        """Build the request payload for a chat completion request."""
        payload: dict[str, Any] = {
            "messages": history,
            "tools": tool_defs,
            "tool_choice": "auto",
            "temperature": temperature,
            "max_tokens": max_tokens,
        }
        if stream:
            payload["stream"] = True
        return payload

    @staticmethod
    def xǁLlmPayloadHandlerǁbuild_payload__mutmut_2(
        history: list[LLMMessage],
        tool_defs: list[dict[str, Any]],
        temperature: float,
        max_tokens: int,
        stream: bool = False,
    ) -> dict[str, Any]:
        """Build the request payload for a chat completion request."""
        payload: dict[str, Any] = None
        if stream:
            payload["stream"] = True
        return payload

    @staticmethod
    def xǁLlmPayloadHandlerǁbuild_payload__mutmut_3(
        history: list[LLMMessage],
        tool_defs: list[dict[str, Any]],
        temperature: float,
        max_tokens: int,
        stream: bool = False,
    ) -> dict[str, Any]:
        """Build the request payload for a chat completion request."""
        payload: dict[str, Any] = {
            "XXmessagesXX": history,
            "tools": tool_defs,
            "tool_choice": "auto",
            "temperature": temperature,
            "max_tokens": max_tokens,
        }
        if stream:
            payload["stream"] = True
        return payload

    @staticmethod
    def xǁLlmPayloadHandlerǁbuild_payload__mutmut_4(
        history: list[LLMMessage],
        tool_defs: list[dict[str, Any]],
        temperature: float,
        max_tokens: int,
        stream: bool = False,
    ) -> dict[str, Any]:
        """Build the request payload for a chat completion request."""
        payload: dict[str, Any] = {
            "MESSAGES": history,
            "tools": tool_defs,
            "tool_choice": "auto",
            "temperature": temperature,
            "max_tokens": max_tokens,
        }
        if stream:
            payload["stream"] = True
        return payload

    @staticmethod
    def xǁLlmPayloadHandlerǁbuild_payload__mutmut_5(
        history: list[LLMMessage],
        tool_defs: list[dict[str, Any]],
        temperature: float,
        max_tokens: int,
        stream: bool = False,
    ) -> dict[str, Any]:
        """Build the request payload for a chat completion request."""
        payload: dict[str, Any] = {
            "messages": history,
            "XXtoolsXX": tool_defs,
            "tool_choice": "auto",
            "temperature": temperature,
            "max_tokens": max_tokens,
        }
        if stream:
            payload["stream"] = True
        return payload

    @staticmethod
    def xǁLlmPayloadHandlerǁbuild_payload__mutmut_6(
        history: list[LLMMessage],
        tool_defs: list[dict[str, Any]],
        temperature: float,
        max_tokens: int,
        stream: bool = False,
    ) -> dict[str, Any]:
        """Build the request payload for a chat completion request."""
        payload: dict[str, Any] = {
            "messages": history,
            "TOOLS": tool_defs,
            "tool_choice": "auto",
            "temperature": temperature,
            "max_tokens": max_tokens,
        }
        if stream:
            payload["stream"] = True
        return payload

    @staticmethod
    def xǁLlmPayloadHandlerǁbuild_payload__mutmut_7(
        history: list[LLMMessage],
        tool_defs: list[dict[str, Any]],
        temperature: float,
        max_tokens: int,
        stream: bool = False,
    ) -> dict[str, Any]:
        """Build the request payload for a chat completion request."""
        payload: dict[str, Any] = {
            "messages": history,
            "tools": tool_defs,
            "XXtool_choiceXX": "auto",
            "temperature": temperature,
            "max_tokens": max_tokens,
        }
        if stream:
            payload["stream"] = True
        return payload

    @staticmethod
    def xǁLlmPayloadHandlerǁbuild_payload__mutmut_8(
        history: list[LLMMessage],
        tool_defs: list[dict[str, Any]],
        temperature: float,
        max_tokens: int,
        stream: bool = False,
    ) -> dict[str, Any]:
        """Build the request payload for a chat completion request."""
        payload: dict[str, Any] = {
            "messages": history,
            "tools": tool_defs,
            "TOOL_CHOICE": "auto",
            "temperature": temperature,
            "max_tokens": max_tokens,
        }
        if stream:
            payload["stream"] = True
        return payload

    @staticmethod
    def xǁLlmPayloadHandlerǁbuild_payload__mutmut_9(
        history: list[LLMMessage],
        tool_defs: list[dict[str, Any]],
        temperature: float,
        max_tokens: int,
        stream: bool = False,
    ) -> dict[str, Any]:
        """Build the request payload for a chat completion request."""
        payload: dict[str, Any] = {
            "messages": history,
            "tools": tool_defs,
            "tool_choice": "XXautoXX",
            "temperature": temperature,
            "max_tokens": max_tokens,
        }
        if stream:
            payload["stream"] = True
        return payload

    @staticmethod
    def xǁLlmPayloadHandlerǁbuild_payload__mutmut_10(
        history: list[LLMMessage],
        tool_defs: list[dict[str, Any]],
        temperature: float,
        max_tokens: int,
        stream: bool = False,
    ) -> dict[str, Any]:
        """Build the request payload for a chat completion request."""
        payload: dict[str, Any] = {
            "messages": history,
            "tools": tool_defs,
            "tool_choice": "AUTO",
            "temperature": temperature,
            "max_tokens": max_tokens,
        }
        if stream:
            payload["stream"] = True
        return payload

    @staticmethod
    def xǁLlmPayloadHandlerǁbuild_payload__mutmut_11(
        history: list[LLMMessage],
        tool_defs: list[dict[str, Any]],
        temperature: float,
        max_tokens: int,
        stream: bool = False,
    ) -> dict[str, Any]:
        """Build the request payload for a chat completion request."""
        payload: dict[str, Any] = {
            "messages": history,
            "tools": tool_defs,
            "tool_choice": "auto",
            "XXtemperatureXX": temperature,
            "max_tokens": max_tokens,
        }
        if stream:
            payload["stream"] = True
        return payload

    @staticmethod
    def xǁLlmPayloadHandlerǁbuild_payload__mutmut_12(
        history: list[LLMMessage],
        tool_defs: list[dict[str, Any]],
        temperature: float,
        max_tokens: int,
        stream: bool = False,
    ) -> dict[str, Any]:
        """Build the request payload for a chat completion request."""
        payload: dict[str, Any] = {
            "messages": history,
            "tools": tool_defs,
            "tool_choice": "auto",
            "TEMPERATURE": temperature,
            "max_tokens": max_tokens,
        }
        if stream:
            payload["stream"] = True
        return payload

    @staticmethod
    def xǁLlmPayloadHandlerǁbuild_payload__mutmut_13(
        history: list[LLMMessage],
        tool_defs: list[dict[str, Any]],
        temperature: float,
        max_tokens: int,
        stream: bool = False,
    ) -> dict[str, Any]:
        """Build the request payload for a chat completion request."""
        payload: dict[str, Any] = {
            "messages": history,
            "tools": tool_defs,
            "tool_choice": "auto",
            "temperature": temperature,
            "XXmax_tokensXX": max_tokens,
        }
        if stream:
            payload["stream"] = True
        return payload

    @staticmethod
    def xǁLlmPayloadHandlerǁbuild_payload__mutmut_14(
        history: list[LLMMessage],
        tool_defs: list[dict[str, Any]],
        temperature: float,
        max_tokens: int,
        stream: bool = False,
    ) -> dict[str, Any]:
        """Build the request payload for a chat completion request."""
        payload: dict[str, Any] = {
            "messages": history,
            "tools": tool_defs,
            "tool_choice": "auto",
            "temperature": temperature,
            "MAX_TOKENS": max_tokens,
        }
        if stream:
            payload["stream"] = True
        return payload

    @staticmethod
    def xǁLlmPayloadHandlerǁbuild_payload__mutmut_15(
        history: list[LLMMessage],
        tool_defs: list[dict[str, Any]],
        temperature: float,
        max_tokens: int,
        stream: bool = False,
    ) -> dict[str, Any]:
        """Build the request payload for a chat completion request."""
        payload: dict[str, Any] = {
            "messages": history,
            "tools": tool_defs,
            "tool_choice": "auto",
            "temperature": temperature,
            "max_tokens": max_tokens,
        }
        if stream:
            payload["stream"] = None
        return payload

    @staticmethod
    def xǁLlmPayloadHandlerǁbuild_payload__mutmut_16(
        history: list[LLMMessage],
        tool_defs: list[dict[str, Any]],
        temperature: float,
        max_tokens: int,
        stream: bool = False,
    ) -> dict[str, Any]:
        """Build the request payload for a chat completion request."""
        payload: dict[str, Any] = {
            "messages": history,
            "tools": tool_defs,
            "tool_choice": "auto",
            "temperature": temperature,
            "max_tokens": max_tokens,
        }
        if stream:
            payload["XXstreamXX"] = True
        return payload

    @staticmethod
    def xǁLlmPayloadHandlerǁbuild_payload__mutmut_17(
        history: list[LLMMessage],
        tool_defs: list[dict[str, Any]],
        temperature: float,
        max_tokens: int,
        stream: bool = False,
    ) -> dict[str, Any]:
        """Build the request payload for a chat completion request."""
        payload: dict[str, Any] = {
            "messages": history,
            "tools": tool_defs,
            "tool_choice": "auto",
            "temperature": temperature,
            "max_tokens": max_tokens,
        }
        if stream:
            payload["STREAM"] = True
        return payload

    @staticmethod
    def xǁLlmPayloadHandlerǁbuild_payload__mutmut_18(
        history: list[LLMMessage],
        tool_defs: list[dict[str, Any]],
        temperature: float,
        max_tokens: int,
        stream: bool = False,
    ) -> dict[str, Any]:
        """Build the request payload for a chat completion request."""
        payload: dict[str, Any] = {
            "messages": history,
            "tools": tool_defs,
            "tool_choice": "auto",
            "temperature": temperature,
            "max_tokens": max_tokens,
        }
        if stream:
            payload["stream"] = False
        return payload

    @staticmethod
    @_mutmut_mutated(mutants_xǁLlmPayloadHandlerǁ_require_dict_field__mutmut)
    def _require_dict_field(value: object, field_repr: str) -> dict[str, Any]:
        """Validate that a raw response field is a dict; raise ValueError with field context."""
        if not isinstance(value, dict):
            raise ValueError(f"Unexpected LLM response: {field_repr} is not a dict")
        return value

    @staticmethod
    def xǁLlmPayloadHandlerǁ_require_dict_field__mutmut_orig(value: object, field_repr: str) -> dict[str, Any]:
        """Validate that a raw response field is a dict; raise ValueError with field context."""
        if not isinstance(value, dict):
            raise ValueError(f"Unexpected LLM response: {field_repr} is not a dict")
        return value

    @staticmethod
    def xǁLlmPayloadHandlerǁ_require_dict_field__mutmut_1(value: object, field_repr: str) -> dict[str, Any]:
        """Validate that a raw response field is a dict; raise ValueError with field context."""
        if isinstance(value, dict):
            raise ValueError(f"Unexpected LLM response: {field_repr} is not a dict")
        return value

    @staticmethod
    def xǁLlmPayloadHandlerǁ_require_dict_field__mutmut_2(value: object, field_repr: str) -> dict[str, Any]:
        """Validate that a raw response field is a dict; raise ValueError with field context."""
        if not isinstance(value, dict):
            raise ValueError(None)
        return value

    @staticmethod
    @_mutmut_mutated(mutants_xǁLlmPayloadHandlerǁparse_response__mutmut)
    def parse_response(
        raw: dict[str, Any],
        on_usage: Callable[[int, int], None] | None = None,
    ) -> LLMResponse:
        """Validate and parse raw LLM JSON into LLMResponse DTO; raises ValueError on schema mismatch."""
        choices = raw.get("choices")
        if not isinstance(choices, list) or not choices:
            raise ValueError("Unexpected LLM response: missing or empty 'choices'")
        choice = LlmPayloadHandler._require_dict_field(choices[0], "choices[0]")
        message_raw = LlmPayloadHandler._require_dict_field(
            choice.get("message"), "'message'"
        )
        finish_reason = choice.get("finish_reason")
        if finish_reason is not None and not isinstance(finish_reason, str):
            finish_reason = None
        usage = LlmSseHelpers.parse_usage(raw, on_usage)
        return LLMResponse(
            message=cast(LLMMessage, message_raw),
            finish_reason=finish_reason,
            usage=usage,
        )

    @staticmethod
    def xǁLlmPayloadHandlerǁparse_response__mutmut_orig(
        raw: dict[str, Any],
        on_usage: Callable[[int, int], None] | None = None,
    ) -> LLMResponse:
        """Validate and parse raw LLM JSON into LLMResponse DTO; raises ValueError on schema mismatch."""
        choices = raw.get("choices")
        if not isinstance(choices, list) or not choices:
            raise ValueError("Unexpected LLM response: missing or empty 'choices'")
        choice = LlmPayloadHandler._require_dict_field(choices[0], "choices[0]")
        message_raw = LlmPayloadHandler._require_dict_field(
            choice.get("message"), "'message'"
        )
        finish_reason = choice.get("finish_reason")
        if finish_reason is not None and not isinstance(finish_reason, str):
            finish_reason = None
        usage = LlmSseHelpers.parse_usage(raw, on_usage)
        return LLMResponse(
            message=cast(LLMMessage, message_raw),
            finish_reason=finish_reason,
            usage=usage,
        )

    @staticmethod
    def xǁLlmPayloadHandlerǁparse_response__mutmut_1(
        raw: dict[str, Any],
        on_usage: Callable[[int, int], None] | None = None,
    ) -> LLMResponse:
        """Validate and parse raw LLM JSON into LLMResponse DTO; raises ValueError on schema mismatch."""
        choices = None
        if not isinstance(choices, list) or not choices:
            raise ValueError("Unexpected LLM response: missing or empty 'choices'")
        choice = LlmPayloadHandler._require_dict_field(choices[0], "choices[0]")
        message_raw = LlmPayloadHandler._require_dict_field(
            choice.get("message"), "'message'"
        )
        finish_reason = choice.get("finish_reason")
        if finish_reason is not None and not isinstance(finish_reason, str):
            finish_reason = None
        usage = LlmSseHelpers.parse_usage(raw, on_usage)
        return LLMResponse(
            message=cast(LLMMessage, message_raw),
            finish_reason=finish_reason,
            usage=usage,
        )

    @staticmethod
    def xǁLlmPayloadHandlerǁparse_response__mutmut_2(
        raw: dict[str, Any],
        on_usage: Callable[[int, int], None] | None = None,
    ) -> LLMResponse:
        """Validate and parse raw LLM JSON into LLMResponse DTO; raises ValueError on schema mismatch."""
        choices = raw.get(None)
        if not isinstance(choices, list) or not choices:
            raise ValueError("Unexpected LLM response: missing or empty 'choices'")
        choice = LlmPayloadHandler._require_dict_field(choices[0], "choices[0]")
        message_raw = LlmPayloadHandler._require_dict_field(
            choice.get("message"), "'message'"
        )
        finish_reason = choice.get("finish_reason")
        if finish_reason is not None and not isinstance(finish_reason, str):
            finish_reason = None
        usage = LlmSseHelpers.parse_usage(raw, on_usage)
        return LLMResponse(
            message=cast(LLMMessage, message_raw),
            finish_reason=finish_reason,
            usage=usage,
        )

    @staticmethod
    def xǁLlmPayloadHandlerǁparse_response__mutmut_3(
        raw: dict[str, Any],
        on_usage: Callable[[int, int], None] | None = None,
    ) -> LLMResponse:
        """Validate and parse raw LLM JSON into LLMResponse DTO; raises ValueError on schema mismatch."""
        choices = raw.get("XXchoicesXX")
        if not isinstance(choices, list) or not choices:
            raise ValueError("Unexpected LLM response: missing or empty 'choices'")
        choice = LlmPayloadHandler._require_dict_field(choices[0], "choices[0]")
        message_raw = LlmPayloadHandler._require_dict_field(
            choice.get("message"), "'message'"
        )
        finish_reason = choice.get("finish_reason")
        if finish_reason is not None and not isinstance(finish_reason, str):
            finish_reason = None
        usage = LlmSseHelpers.parse_usage(raw, on_usage)
        return LLMResponse(
            message=cast(LLMMessage, message_raw),
            finish_reason=finish_reason,
            usage=usage,
        )

    @staticmethod
    def xǁLlmPayloadHandlerǁparse_response__mutmut_4(
        raw: dict[str, Any],
        on_usage: Callable[[int, int], None] | None = None,
    ) -> LLMResponse:
        """Validate and parse raw LLM JSON into LLMResponse DTO; raises ValueError on schema mismatch."""
        choices = raw.get("CHOICES")
        if not isinstance(choices, list) or not choices:
            raise ValueError("Unexpected LLM response: missing or empty 'choices'")
        choice = LlmPayloadHandler._require_dict_field(choices[0], "choices[0]")
        message_raw = LlmPayloadHandler._require_dict_field(
            choice.get("message"), "'message'"
        )
        finish_reason = choice.get("finish_reason")
        if finish_reason is not None and not isinstance(finish_reason, str):
            finish_reason = None
        usage = LlmSseHelpers.parse_usage(raw, on_usage)
        return LLMResponse(
            message=cast(LLMMessage, message_raw),
            finish_reason=finish_reason,
            usage=usage,
        )

    @staticmethod
    def xǁLlmPayloadHandlerǁparse_response__mutmut_5(
        raw: dict[str, Any],
        on_usage: Callable[[int, int], None] | None = None,
    ) -> LLMResponse:
        """Validate and parse raw LLM JSON into LLMResponse DTO; raises ValueError on schema mismatch."""
        choices = raw.get("choices")
        if not isinstance(choices, list) and not choices:
            raise ValueError("Unexpected LLM response: missing or empty 'choices'")
        choice = LlmPayloadHandler._require_dict_field(choices[0], "choices[0]")
        message_raw = LlmPayloadHandler._require_dict_field(
            choice.get("message"), "'message'"
        )
        finish_reason = choice.get("finish_reason")
        if finish_reason is not None and not isinstance(finish_reason, str):
            finish_reason = None
        usage = LlmSseHelpers.parse_usage(raw, on_usage)
        return LLMResponse(
            message=cast(LLMMessage, message_raw),
            finish_reason=finish_reason,
            usage=usage,
        )

    @staticmethod
    def xǁLlmPayloadHandlerǁparse_response__mutmut_6(
        raw: dict[str, Any],
        on_usage: Callable[[int, int], None] | None = None,
    ) -> LLMResponse:
        """Validate and parse raw LLM JSON into LLMResponse DTO; raises ValueError on schema mismatch."""
        choices = raw.get("choices")
        if isinstance(choices, list) or not choices:
            raise ValueError("Unexpected LLM response: missing or empty 'choices'")
        choice = LlmPayloadHandler._require_dict_field(choices[0], "choices[0]")
        message_raw = LlmPayloadHandler._require_dict_field(
            choice.get("message"), "'message'"
        )
        finish_reason = choice.get("finish_reason")
        if finish_reason is not None and not isinstance(finish_reason, str):
            finish_reason = None
        usage = LlmSseHelpers.parse_usage(raw, on_usage)
        return LLMResponse(
            message=cast(LLMMessage, message_raw),
            finish_reason=finish_reason,
            usage=usage,
        )

    @staticmethod
    def xǁLlmPayloadHandlerǁparse_response__mutmut_7(
        raw: dict[str, Any],
        on_usage: Callable[[int, int], None] | None = None,
    ) -> LLMResponse:
        """Validate and parse raw LLM JSON into LLMResponse DTO; raises ValueError on schema mismatch."""
        choices = raw.get("choices")
        if not isinstance(choices, list) or choices:
            raise ValueError("Unexpected LLM response: missing or empty 'choices'")
        choice = LlmPayloadHandler._require_dict_field(choices[0], "choices[0]")
        message_raw = LlmPayloadHandler._require_dict_field(
            choice.get("message"), "'message'"
        )
        finish_reason = choice.get("finish_reason")
        if finish_reason is not None and not isinstance(finish_reason, str):
            finish_reason = None
        usage = LlmSseHelpers.parse_usage(raw, on_usage)
        return LLMResponse(
            message=cast(LLMMessage, message_raw),
            finish_reason=finish_reason,
            usage=usage,
        )

    @staticmethod
    def xǁLlmPayloadHandlerǁparse_response__mutmut_8(
        raw: dict[str, Any],
        on_usage: Callable[[int, int], None] | None = None,
    ) -> LLMResponse:
        """Validate and parse raw LLM JSON into LLMResponse DTO; raises ValueError on schema mismatch."""
        choices = raw.get("choices")
        if not isinstance(choices, list) or not choices:
            raise ValueError(None)
        choice = LlmPayloadHandler._require_dict_field(choices[0], "choices[0]")
        message_raw = LlmPayloadHandler._require_dict_field(
            choice.get("message"), "'message'"
        )
        finish_reason = choice.get("finish_reason")
        if finish_reason is not None and not isinstance(finish_reason, str):
            finish_reason = None
        usage = LlmSseHelpers.parse_usage(raw, on_usage)
        return LLMResponse(
            message=cast(LLMMessage, message_raw),
            finish_reason=finish_reason,
            usage=usage,
        )

    @staticmethod
    def xǁLlmPayloadHandlerǁparse_response__mutmut_9(
        raw: dict[str, Any],
        on_usage: Callable[[int, int], None] | None = None,
    ) -> LLMResponse:
        """Validate and parse raw LLM JSON into LLMResponse DTO; raises ValueError on schema mismatch."""
        choices = raw.get("choices")
        if not isinstance(choices, list) or not choices:
            raise ValueError("XXUnexpected LLM response: missing or empty 'choices'XX")
        choice = LlmPayloadHandler._require_dict_field(choices[0], "choices[0]")
        message_raw = LlmPayloadHandler._require_dict_field(
            choice.get("message"), "'message'"
        )
        finish_reason = choice.get("finish_reason")
        if finish_reason is not None and not isinstance(finish_reason, str):
            finish_reason = None
        usage = LlmSseHelpers.parse_usage(raw, on_usage)
        return LLMResponse(
            message=cast(LLMMessage, message_raw),
            finish_reason=finish_reason,
            usage=usage,
        )

    @staticmethod
    def xǁLlmPayloadHandlerǁparse_response__mutmut_10(
        raw: dict[str, Any],
        on_usage: Callable[[int, int], None] | None = None,
    ) -> LLMResponse:
        """Validate and parse raw LLM JSON into LLMResponse DTO; raises ValueError on schema mismatch."""
        choices = raw.get("choices")
        if not isinstance(choices, list) or not choices:
            raise ValueError("unexpected llm response: missing or empty 'choices'")
        choice = LlmPayloadHandler._require_dict_field(choices[0], "choices[0]")
        message_raw = LlmPayloadHandler._require_dict_field(
            choice.get("message"), "'message'"
        )
        finish_reason = choice.get("finish_reason")
        if finish_reason is not None and not isinstance(finish_reason, str):
            finish_reason = None
        usage = LlmSseHelpers.parse_usage(raw, on_usage)
        return LLMResponse(
            message=cast(LLMMessage, message_raw),
            finish_reason=finish_reason,
            usage=usage,
        )

    @staticmethod
    def xǁLlmPayloadHandlerǁparse_response__mutmut_11(
        raw: dict[str, Any],
        on_usage: Callable[[int, int], None] | None = None,
    ) -> LLMResponse:
        """Validate and parse raw LLM JSON into LLMResponse DTO; raises ValueError on schema mismatch."""
        choices = raw.get("choices")
        if not isinstance(choices, list) or not choices:
            raise ValueError("UNEXPECTED LLM RESPONSE: MISSING OR EMPTY 'CHOICES'")
        choice = LlmPayloadHandler._require_dict_field(choices[0], "choices[0]")
        message_raw = LlmPayloadHandler._require_dict_field(
            choice.get("message"), "'message'"
        )
        finish_reason = choice.get("finish_reason")
        if finish_reason is not None and not isinstance(finish_reason, str):
            finish_reason = None
        usage = LlmSseHelpers.parse_usage(raw, on_usage)
        return LLMResponse(
            message=cast(LLMMessage, message_raw),
            finish_reason=finish_reason,
            usage=usage,
        )

    @staticmethod
    def xǁLlmPayloadHandlerǁparse_response__mutmut_12(
        raw: dict[str, Any],
        on_usage: Callable[[int, int], None] | None = None,
    ) -> LLMResponse:
        """Validate and parse raw LLM JSON into LLMResponse DTO; raises ValueError on schema mismatch."""
        choices = raw.get("choices")
        if not isinstance(choices, list) or not choices:
            raise ValueError("Unexpected LLM response: missing or empty 'choices'")
        choice = None
        message_raw = LlmPayloadHandler._require_dict_field(
            choice.get("message"), "'message'"
        )
        finish_reason = choice.get("finish_reason")
        if finish_reason is not None and not isinstance(finish_reason, str):
            finish_reason = None
        usage = LlmSseHelpers.parse_usage(raw, on_usage)
        return LLMResponse(
            message=cast(LLMMessage, message_raw),
            finish_reason=finish_reason,
            usage=usage,
        )

    @staticmethod
    def xǁLlmPayloadHandlerǁparse_response__mutmut_13(
        raw: dict[str, Any],
        on_usage: Callable[[int, int], None] | None = None,
    ) -> LLMResponse:
        """Validate and parse raw LLM JSON into LLMResponse DTO; raises ValueError on schema mismatch."""
        choices = raw.get("choices")
        if not isinstance(choices, list) or not choices:
            raise ValueError("Unexpected LLM response: missing or empty 'choices'")
        choice = LlmPayloadHandler._require_dict_field(None, "choices[0]")
        message_raw = LlmPayloadHandler._require_dict_field(
            choice.get("message"), "'message'"
        )
        finish_reason = choice.get("finish_reason")
        if finish_reason is not None and not isinstance(finish_reason, str):
            finish_reason = None
        usage = LlmSseHelpers.parse_usage(raw, on_usage)
        return LLMResponse(
            message=cast(LLMMessage, message_raw),
            finish_reason=finish_reason,
            usage=usage,
        )

    @staticmethod
    def xǁLlmPayloadHandlerǁparse_response__mutmut_14(
        raw: dict[str, Any],
        on_usage: Callable[[int, int], None] | None = None,
    ) -> LLMResponse:
        """Validate and parse raw LLM JSON into LLMResponse DTO; raises ValueError on schema mismatch."""
        choices = raw.get("choices")
        if not isinstance(choices, list) or not choices:
            raise ValueError("Unexpected LLM response: missing or empty 'choices'")
        choice = LlmPayloadHandler._require_dict_field(choices[0], None)
        message_raw = LlmPayloadHandler._require_dict_field(
            choice.get("message"), "'message'"
        )
        finish_reason = choice.get("finish_reason")
        if finish_reason is not None and not isinstance(finish_reason, str):
            finish_reason = None
        usage = LlmSseHelpers.parse_usage(raw, on_usage)
        return LLMResponse(
            message=cast(LLMMessage, message_raw),
            finish_reason=finish_reason,
            usage=usage,
        )

    @staticmethod
    def xǁLlmPayloadHandlerǁparse_response__mutmut_15(
        raw: dict[str, Any],
        on_usage: Callable[[int, int], None] | None = None,
    ) -> LLMResponse:
        """Validate and parse raw LLM JSON into LLMResponse DTO; raises ValueError on schema mismatch."""
        choices = raw.get("choices")
        if not isinstance(choices, list) or not choices:
            raise ValueError("Unexpected LLM response: missing or empty 'choices'")
        choice = LlmPayloadHandler._require_dict_field("choices[0]")
        message_raw = LlmPayloadHandler._require_dict_field(
            choice.get("message"), "'message'"
        )
        finish_reason = choice.get("finish_reason")
        if finish_reason is not None and not isinstance(finish_reason, str):
            finish_reason = None
        usage = LlmSseHelpers.parse_usage(raw, on_usage)
        return LLMResponse(
            message=cast(LLMMessage, message_raw),
            finish_reason=finish_reason,
            usage=usage,
        )

    @staticmethod
    def xǁLlmPayloadHandlerǁparse_response__mutmut_16(
        raw: dict[str, Any],
        on_usage: Callable[[int, int], None] | None = None,
    ) -> LLMResponse:
        """Validate and parse raw LLM JSON into LLMResponse DTO; raises ValueError on schema mismatch."""
        choices = raw.get("choices")
        if not isinstance(choices, list) or not choices:
            raise ValueError("Unexpected LLM response: missing or empty 'choices'")
        choice = LlmPayloadHandler._require_dict_field(choices[0], )
        message_raw = LlmPayloadHandler._require_dict_field(
            choice.get("message"), "'message'"
        )
        finish_reason = choice.get("finish_reason")
        if finish_reason is not None and not isinstance(finish_reason, str):
            finish_reason = None
        usage = LlmSseHelpers.parse_usage(raw, on_usage)
        return LLMResponse(
            message=cast(LLMMessage, message_raw),
            finish_reason=finish_reason,
            usage=usage,
        )

    @staticmethod
    def xǁLlmPayloadHandlerǁparse_response__mutmut_17(
        raw: dict[str, Any],
        on_usage: Callable[[int, int], None] | None = None,
    ) -> LLMResponse:
        """Validate and parse raw LLM JSON into LLMResponse DTO; raises ValueError on schema mismatch."""
        choices = raw.get("choices")
        if not isinstance(choices, list) or not choices:
            raise ValueError("Unexpected LLM response: missing or empty 'choices'")
        choice = LlmPayloadHandler._require_dict_field(choices[1], "choices[0]")
        message_raw = LlmPayloadHandler._require_dict_field(
            choice.get("message"), "'message'"
        )
        finish_reason = choice.get("finish_reason")
        if finish_reason is not None and not isinstance(finish_reason, str):
            finish_reason = None
        usage = LlmSseHelpers.parse_usage(raw, on_usage)
        return LLMResponse(
            message=cast(LLMMessage, message_raw),
            finish_reason=finish_reason,
            usage=usage,
        )

    @staticmethod
    def xǁLlmPayloadHandlerǁparse_response__mutmut_18(
        raw: dict[str, Any],
        on_usage: Callable[[int, int], None] | None = None,
    ) -> LLMResponse:
        """Validate and parse raw LLM JSON into LLMResponse DTO; raises ValueError on schema mismatch."""
        choices = raw.get("choices")
        if not isinstance(choices, list) or not choices:
            raise ValueError("Unexpected LLM response: missing or empty 'choices'")
        choice = LlmPayloadHandler._require_dict_field(choices[0], "XXchoices[0]XX")
        message_raw = LlmPayloadHandler._require_dict_field(
            choice.get("message"), "'message'"
        )
        finish_reason = choice.get("finish_reason")
        if finish_reason is not None and not isinstance(finish_reason, str):
            finish_reason = None
        usage = LlmSseHelpers.parse_usage(raw, on_usage)
        return LLMResponse(
            message=cast(LLMMessage, message_raw),
            finish_reason=finish_reason,
            usage=usage,
        )

    @staticmethod
    def xǁLlmPayloadHandlerǁparse_response__mutmut_19(
        raw: dict[str, Any],
        on_usage: Callable[[int, int], None] | None = None,
    ) -> LLMResponse:
        """Validate and parse raw LLM JSON into LLMResponse DTO; raises ValueError on schema mismatch."""
        choices = raw.get("choices")
        if not isinstance(choices, list) or not choices:
            raise ValueError("Unexpected LLM response: missing or empty 'choices'")
        choice = LlmPayloadHandler._require_dict_field(choices[0], "CHOICES[0]")
        message_raw = LlmPayloadHandler._require_dict_field(
            choice.get("message"), "'message'"
        )
        finish_reason = choice.get("finish_reason")
        if finish_reason is not None and not isinstance(finish_reason, str):
            finish_reason = None
        usage = LlmSseHelpers.parse_usage(raw, on_usage)
        return LLMResponse(
            message=cast(LLMMessage, message_raw),
            finish_reason=finish_reason,
            usage=usage,
        )

    @staticmethod
    def xǁLlmPayloadHandlerǁparse_response__mutmut_20(
        raw: dict[str, Any],
        on_usage: Callable[[int, int], None] | None = None,
    ) -> LLMResponse:
        """Validate and parse raw LLM JSON into LLMResponse DTO; raises ValueError on schema mismatch."""
        choices = raw.get("choices")
        if not isinstance(choices, list) or not choices:
            raise ValueError("Unexpected LLM response: missing or empty 'choices'")
        choice = LlmPayloadHandler._require_dict_field(choices[0], "choices[0]")
        message_raw = None
        finish_reason = choice.get("finish_reason")
        if finish_reason is not None and not isinstance(finish_reason, str):
            finish_reason = None
        usage = LlmSseHelpers.parse_usage(raw, on_usage)
        return LLMResponse(
            message=cast(LLMMessage, message_raw),
            finish_reason=finish_reason,
            usage=usage,
        )

    @staticmethod
    def xǁLlmPayloadHandlerǁparse_response__mutmut_21(
        raw: dict[str, Any],
        on_usage: Callable[[int, int], None] | None = None,
    ) -> LLMResponse:
        """Validate and parse raw LLM JSON into LLMResponse DTO; raises ValueError on schema mismatch."""
        choices = raw.get("choices")
        if not isinstance(choices, list) or not choices:
            raise ValueError("Unexpected LLM response: missing or empty 'choices'")
        choice = LlmPayloadHandler._require_dict_field(choices[0], "choices[0]")
        message_raw = LlmPayloadHandler._require_dict_field(
            None, "'message'"
        )
        finish_reason = choice.get("finish_reason")
        if finish_reason is not None and not isinstance(finish_reason, str):
            finish_reason = None
        usage = LlmSseHelpers.parse_usage(raw, on_usage)
        return LLMResponse(
            message=cast(LLMMessage, message_raw),
            finish_reason=finish_reason,
            usage=usage,
        )

    @staticmethod
    def xǁLlmPayloadHandlerǁparse_response__mutmut_22(
        raw: dict[str, Any],
        on_usage: Callable[[int, int], None] | None = None,
    ) -> LLMResponse:
        """Validate and parse raw LLM JSON into LLMResponse DTO; raises ValueError on schema mismatch."""
        choices = raw.get("choices")
        if not isinstance(choices, list) or not choices:
            raise ValueError("Unexpected LLM response: missing or empty 'choices'")
        choice = LlmPayloadHandler._require_dict_field(choices[0], "choices[0]")
        message_raw = LlmPayloadHandler._require_dict_field(
            choice.get("message"), None
        )
        finish_reason = choice.get("finish_reason")
        if finish_reason is not None and not isinstance(finish_reason, str):
            finish_reason = None
        usage = LlmSseHelpers.parse_usage(raw, on_usage)
        return LLMResponse(
            message=cast(LLMMessage, message_raw),
            finish_reason=finish_reason,
            usage=usage,
        )

    @staticmethod
    def xǁLlmPayloadHandlerǁparse_response__mutmut_23(
        raw: dict[str, Any],
        on_usage: Callable[[int, int], None] | None = None,
    ) -> LLMResponse:
        """Validate and parse raw LLM JSON into LLMResponse DTO; raises ValueError on schema mismatch."""
        choices = raw.get("choices")
        if not isinstance(choices, list) or not choices:
            raise ValueError("Unexpected LLM response: missing or empty 'choices'")
        choice = LlmPayloadHandler._require_dict_field(choices[0], "choices[0]")
        message_raw = LlmPayloadHandler._require_dict_field(
            "'message'"
        )
        finish_reason = choice.get("finish_reason")
        if finish_reason is not None and not isinstance(finish_reason, str):
            finish_reason = None
        usage = LlmSseHelpers.parse_usage(raw, on_usage)
        return LLMResponse(
            message=cast(LLMMessage, message_raw),
            finish_reason=finish_reason,
            usage=usage,
        )

    @staticmethod
    def xǁLlmPayloadHandlerǁparse_response__mutmut_24(
        raw: dict[str, Any],
        on_usage: Callable[[int, int], None] | None = None,
    ) -> LLMResponse:
        """Validate and parse raw LLM JSON into LLMResponse DTO; raises ValueError on schema mismatch."""
        choices = raw.get("choices")
        if not isinstance(choices, list) or not choices:
            raise ValueError("Unexpected LLM response: missing or empty 'choices'")
        choice = LlmPayloadHandler._require_dict_field(choices[0], "choices[0]")
        message_raw = LlmPayloadHandler._require_dict_field(
            choice.get("message"), )
        finish_reason = choice.get("finish_reason")
        if finish_reason is not None and not isinstance(finish_reason, str):
            finish_reason = None
        usage = LlmSseHelpers.parse_usage(raw, on_usage)
        return LLMResponse(
            message=cast(LLMMessage, message_raw),
            finish_reason=finish_reason,
            usage=usage,
        )

    @staticmethod
    def xǁLlmPayloadHandlerǁparse_response__mutmut_25(
        raw: dict[str, Any],
        on_usage: Callable[[int, int], None] | None = None,
    ) -> LLMResponse:
        """Validate and parse raw LLM JSON into LLMResponse DTO; raises ValueError on schema mismatch."""
        choices = raw.get("choices")
        if not isinstance(choices, list) or not choices:
            raise ValueError("Unexpected LLM response: missing or empty 'choices'")
        choice = LlmPayloadHandler._require_dict_field(choices[0], "choices[0]")
        message_raw = LlmPayloadHandler._require_dict_field(
            choice.get(None), "'message'"
        )
        finish_reason = choice.get("finish_reason")
        if finish_reason is not None and not isinstance(finish_reason, str):
            finish_reason = None
        usage = LlmSseHelpers.parse_usage(raw, on_usage)
        return LLMResponse(
            message=cast(LLMMessage, message_raw),
            finish_reason=finish_reason,
            usage=usage,
        )

    @staticmethod
    def xǁLlmPayloadHandlerǁparse_response__mutmut_26(
        raw: dict[str, Any],
        on_usage: Callable[[int, int], None] | None = None,
    ) -> LLMResponse:
        """Validate and parse raw LLM JSON into LLMResponse DTO; raises ValueError on schema mismatch."""
        choices = raw.get("choices")
        if not isinstance(choices, list) or not choices:
            raise ValueError("Unexpected LLM response: missing or empty 'choices'")
        choice = LlmPayloadHandler._require_dict_field(choices[0], "choices[0]")
        message_raw = LlmPayloadHandler._require_dict_field(
            choice.get("XXmessageXX"), "'message'"
        )
        finish_reason = choice.get("finish_reason")
        if finish_reason is not None and not isinstance(finish_reason, str):
            finish_reason = None
        usage = LlmSseHelpers.parse_usage(raw, on_usage)
        return LLMResponse(
            message=cast(LLMMessage, message_raw),
            finish_reason=finish_reason,
            usage=usage,
        )

    @staticmethod
    def xǁLlmPayloadHandlerǁparse_response__mutmut_27(
        raw: dict[str, Any],
        on_usage: Callable[[int, int], None] | None = None,
    ) -> LLMResponse:
        """Validate and parse raw LLM JSON into LLMResponse DTO; raises ValueError on schema mismatch."""
        choices = raw.get("choices")
        if not isinstance(choices, list) or not choices:
            raise ValueError("Unexpected LLM response: missing or empty 'choices'")
        choice = LlmPayloadHandler._require_dict_field(choices[0], "choices[0]")
        message_raw = LlmPayloadHandler._require_dict_field(
            choice.get("MESSAGE"), "'message'"
        )
        finish_reason = choice.get("finish_reason")
        if finish_reason is not None and not isinstance(finish_reason, str):
            finish_reason = None
        usage = LlmSseHelpers.parse_usage(raw, on_usage)
        return LLMResponse(
            message=cast(LLMMessage, message_raw),
            finish_reason=finish_reason,
            usage=usage,
        )

    @staticmethod
    def xǁLlmPayloadHandlerǁparse_response__mutmut_28(
        raw: dict[str, Any],
        on_usage: Callable[[int, int], None] | None = None,
    ) -> LLMResponse:
        """Validate and parse raw LLM JSON into LLMResponse DTO; raises ValueError on schema mismatch."""
        choices = raw.get("choices")
        if not isinstance(choices, list) or not choices:
            raise ValueError("Unexpected LLM response: missing or empty 'choices'")
        choice = LlmPayloadHandler._require_dict_field(choices[0], "choices[0]")
        message_raw = LlmPayloadHandler._require_dict_field(
            choice.get("message"), "XX'message'XX"
        )
        finish_reason = choice.get("finish_reason")
        if finish_reason is not None and not isinstance(finish_reason, str):
            finish_reason = None
        usage = LlmSseHelpers.parse_usage(raw, on_usage)
        return LLMResponse(
            message=cast(LLMMessage, message_raw),
            finish_reason=finish_reason,
            usage=usage,
        )

    @staticmethod
    def xǁLlmPayloadHandlerǁparse_response__mutmut_29(
        raw: dict[str, Any],
        on_usage: Callable[[int, int], None] | None = None,
    ) -> LLMResponse:
        """Validate and parse raw LLM JSON into LLMResponse DTO; raises ValueError on schema mismatch."""
        choices = raw.get("choices")
        if not isinstance(choices, list) or not choices:
            raise ValueError("Unexpected LLM response: missing or empty 'choices'")
        choice = LlmPayloadHandler._require_dict_field(choices[0], "choices[0]")
        message_raw = LlmPayloadHandler._require_dict_field(
            choice.get("message"), "'MESSAGE'"
        )
        finish_reason = choice.get("finish_reason")
        if finish_reason is not None and not isinstance(finish_reason, str):
            finish_reason = None
        usage = LlmSseHelpers.parse_usage(raw, on_usage)
        return LLMResponse(
            message=cast(LLMMessage, message_raw),
            finish_reason=finish_reason,
            usage=usage,
        )

    @staticmethod
    def xǁLlmPayloadHandlerǁparse_response__mutmut_30(
        raw: dict[str, Any],
        on_usage: Callable[[int, int], None] | None = None,
    ) -> LLMResponse:
        """Validate and parse raw LLM JSON into LLMResponse DTO; raises ValueError on schema mismatch."""
        choices = raw.get("choices")
        if not isinstance(choices, list) or not choices:
            raise ValueError("Unexpected LLM response: missing or empty 'choices'")
        choice = LlmPayloadHandler._require_dict_field(choices[0], "choices[0]")
        message_raw = LlmPayloadHandler._require_dict_field(
            choice.get("message"), "'message'"
        )
        finish_reason = None
        if finish_reason is not None and not isinstance(finish_reason, str):
            finish_reason = None
        usage = LlmSseHelpers.parse_usage(raw, on_usage)
        return LLMResponse(
            message=cast(LLMMessage, message_raw),
            finish_reason=finish_reason,
            usage=usage,
        )

    @staticmethod
    def xǁLlmPayloadHandlerǁparse_response__mutmut_31(
        raw: dict[str, Any],
        on_usage: Callable[[int, int], None] | None = None,
    ) -> LLMResponse:
        """Validate and parse raw LLM JSON into LLMResponse DTO; raises ValueError on schema mismatch."""
        choices = raw.get("choices")
        if not isinstance(choices, list) or not choices:
            raise ValueError("Unexpected LLM response: missing or empty 'choices'")
        choice = LlmPayloadHandler._require_dict_field(choices[0], "choices[0]")
        message_raw = LlmPayloadHandler._require_dict_field(
            choice.get("message"), "'message'"
        )
        finish_reason = choice.get(None)
        if finish_reason is not None and not isinstance(finish_reason, str):
            finish_reason = None
        usage = LlmSseHelpers.parse_usage(raw, on_usage)
        return LLMResponse(
            message=cast(LLMMessage, message_raw),
            finish_reason=finish_reason,
            usage=usage,
        )

    @staticmethod
    def xǁLlmPayloadHandlerǁparse_response__mutmut_32(
        raw: dict[str, Any],
        on_usage: Callable[[int, int], None] | None = None,
    ) -> LLMResponse:
        """Validate and parse raw LLM JSON into LLMResponse DTO; raises ValueError on schema mismatch."""
        choices = raw.get("choices")
        if not isinstance(choices, list) or not choices:
            raise ValueError("Unexpected LLM response: missing or empty 'choices'")
        choice = LlmPayloadHandler._require_dict_field(choices[0], "choices[0]")
        message_raw = LlmPayloadHandler._require_dict_field(
            choice.get("message"), "'message'"
        )
        finish_reason = choice.get("XXfinish_reasonXX")
        if finish_reason is not None and not isinstance(finish_reason, str):
            finish_reason = None
        usage = LlmSseHelpers.parse_usage(raw, on_usage)
        return LLMResponse(
            message=cast(LLMMessage, message_raw),
            finish_reason=finish_reason,
            usage=usage,
        )

    @staticmethod
    def xǁLlmPayloadHandlerǁparse_response__mutmut_33(
        raw: dict[str, Any],
        on_usage: Callable[[int, int], None] | None = None,
    ) -> LLMResponse:
        """Validate and parse raw LLM JSON into LLMResponse DTO; raises ValueError on schema mismatch."""
        choices = raw.get("choices")
        if not isinstance(choices, list) or not choices:
            raise ValueError("Unexpected LLM response: missing or empty 'choices'")
        choice = LlmPayloadHandler._require_dict_field(choices[0], "choices[0]")
        message_raw = LlmPayloadHandler._require_dict_field(
            choice.get("message"), "'message'"
        )
        finish_reason = choice.get("FINISH_REASON")
        if finish_reason is not None and not isinstance(finish_reason, str):
            finish_reason = None
        usage = LlmSseHelpers.parse_usage(raw, on_usage)
        return LLMResponse(
            message=cast(LLMMessage, message_raw),
            finish_reason=finish_reason,
            usage=usage,
        )

    @staticmethod
    def xǁLlmPayloadHandlerǁparse_response__mutmut_34(
        raw: dict[str, Any],
        on_usage: Callable[[int, int], None] | None = None,
    ) -> LLMResponse:
        """Validate and parse raw LLM JSON into LLMResponse DTO; raises ValueError on schema mismatch."""
        choices = raw.get("choices")
        if not isinstance(choices, list) or not choices:
            raise ValueError("Unexpected LLM response: missing or empty 'choices'")
        choice = LlmPayloadHandler._require_dict_field(choices[0], "choices[0]")
        message_raw = LlmPayloadHandler._require_dict_field(
            choice.get("message"), "'message'"
        )
        finish_reason = choice.get("finish_reason")
        if finish_reason is not None or not isinstance(finish_reason, str):
            finish_reason = None
        usage = LlmSseHelpers.parse_usage(raw, on_usage)
        return LLMResponse(
            message=cast(LLMMessage, message_raw),
            finish_reason=finish_reason,
            usage=usage,
        )

    @staticmethod
    def xǁLlmPayloadHandlerǁparse_response__mutmut_35(
        raw: dict[str, Any],
        on_usage: Callable[[int, int], None] | None = None,
    ) -> LLMResponse:
        """Validate and parse raw LLM JSON into LLMResponse DTO; raises ValueError on schema mismatch."""
        choices = raw.get("choices")
        if not isinstance(choices, list) or not choices:
            raise ValueError("Unexpected LLM response: missing or empty 'choices'")
        choice = LlmPayloadHandler._require_dict_field(choices[0], "choices[0]")
        message_raw = LlmPayloadHandler._require_dict_field(
            choice.get("message"), "'message'"
        )
        finish_reason = choice.get("finish_reason")
        if finish_reason is None and not isinstance(finish_reason, str):
            finish_reason = None
        usage = LlmSseHelpers.parse_usage(raw, on_usage)
        return LLMResponse(
            message=cast(LLMMessage, message_raw),
            finish_reason=finish_reason,
            usage=usage,
        )

    @staticmethod
    def xǁLlmPayloadHandlerǁparse_response__mutmut_36(
        raw: dict[str, Any],
        on_usage: Callable[[int, int], None] | None = None,
    ) -> LLMResponse:
        """Validate and parse raw LLM JSON into LLMResponse DTO; raises ValueError on schema mismatch."""
        choices = raw.get("choices")
        if not isinstance(choices, list) or not choices:
            raise ValueError("Unexpected LLM response: missing or empty 'choices'")
        choice = LlmPayloadHandler._require_dict_field(choices[0], "choices[0]")
        message_raw = LlmPayloadHandler._require_dict_field(
            choice.get("message"), "'message'"
        )
        finish_reason = choice.get("finish_reason")
        if finish_reason is not None and isinstance(finish_reason, str):
            finish_reason = None
        usage = LlmSseHelpers.parse_usage(raw, on_usage)
        return LLMResponse(
            message=cast(LLMMessage, message_raw),
            finish_reason=finish_reason,
            usage=usage,
        )

    @staticmethod
    def xǁLlmPayloadHandlerǁparse_response__mutmut_37(
        raw: dict[str, Any],
        on_usage: Callable[[int, int], None] | None = None,
    ) -> LLMResponse:
        """Validate and parse raw LLM JSON into LLMResponse DTO; raises ValueError on schema mismatch."""
        choices = raw.get("choices")
        if not isinstance(choices, list) or not choices:
            raise ValueError("Unexpected LLM response: missing or empty 'choices'")
        choice = LlmPayloadHandler._require_dict_field(choices[0], "choices[0]")
        message_raw = LlmPayloadHandler._require_dict_field(
            choice.get("message"), "'message'"
        )
        finish_reason = choice.get("finish_reason")
        if finish_reason is not None and not isinstance(finish_reason, str):
            finish_reason = ""
        usage = LlmSseHelpers.parse_usage(raw, on_usage)
        return LLMResponse(
            message=cast(LLMMessage, message_raw),
            finish_reason=finish_reason,
            usage=usage,
        )

    @staticmethod
    def xǁLlmPayloadHandlerǁparse_response__mutmut_38(
        raw: dict[str, Any],
        on_usage: Callable[[int, int], None] | None = None,
    ) -> LLMResponse:
        """Validate and parse raw LLM JSON into LLMResponse DTO; raises ValueError on schema mismatch."""
        choices = raw.get("choices")
        if not isinstance(choices, list) or not choices:
            raise ValueError("Unexpected LLM response: missing or empty 'choices'")
        choice = LlmPayloadHandler._require_dict_field(choices[0], "choices[0]")
        message_raw = LlmPayloadHandler._require_dict_field(
            choice.get("message"), "'message'"
        )
        finish_reason = choice.get("finish_reason")
        if finish_reason is not None and not isinstance(finish_reason, str):
            finish_reason = None
        usage = None
        return LLMResponse(
            message=cast(LLMMessage, message_raw),
            finish_reason=finish_reason,
            usage=usage,
        )

    @staticmethod
    def xǁLlmPayloadHandlerǁparse_response__mutmut_39(
        raw: dict[str, Any],
        on_usage: Callable[[int, int], None] | None = None,
    ) -> LLMResponse:
        """Validate and parse raw LLM JSON into LLMResponse DTO; raises ValueError on schema mismatch."""
        choices = raw.get("choices")
        if not isinstance(choices, list) or not choices:
            raise ValueError("Unexpected LLM response: missing or empty 'choices'")
        choice = LlmPayloadHandler._require_dict_field(choices[0], "choices[0]")
        message_raw = LlmPayloadHandler._require_dict_field(
            choice.get("message"), "'message'"
        )
        finish_reason = choice.get("finish_reason")
        if finish_reason is not None and not isinstance(finish_reason, str):
            finish_reason = None
        usage = LlmSseHelpers.parse_usage(None, on_usage)
        return LLMResponse(
            message=cast(LLMMessage, message_raw),
            finish_reason=finish_reason,
            usage=usage,
        )

    @staticmethod
    def xǁLlmPayloadHandlerǁparse_response__mutmut_40(
        raw: dict[str, Any],
        on_usage: Callable[[int, int], None] | None = None,
    ) -> LLMResponse:
        """Validate and parse raw LLM JSON into LLMResponse DTO; raises ValueError on schema mismatch."""
        choices = raw.get("choices")
        if not isinstance(choices, list) or not choices:
            raise ValueError("Unexpected LLM response: missing or empty 'choices'")
        choice = LlmPayloadHandler._require_dict_field(choices[0], "choices[0]")
        message_raw = LlmPayloadHandler._require_dict_field(
            choice.get("message"), "'message'"
        )
        finish_reason = choice.get("finish_reason")
        if finish_reason is not None and not isinstance(finish_reason, str):
            finish_reason = None
        usage = LlmSseHelpers.parse_usage(raw, None)
        return LLMResponse(
            message=cast(LLMMessage, message_raw),
            finish_reason=finish_reason,
            usage=usage,
        )

    @staticmethod
    def xǁLlmPayloadHandlerǁparse_response__mutmut_41(
        raw: dict[str, Any],
        on_usage: Callable[[int, int], None] | None = None,
    ) -> LLMResponse:
        """Validate and parse raw LLM JSON into LLMResponse DTO; raises ValueError on schema mismatch."""
        choices = raw.get("choices")
        if not isinstance(choices, list) or not choices:
            raise ValueError("Unexpected LLM response: missing or empty 'choices'")
        choice = LlmPayloadHandler._require_dict_field(choices[0], "choices[0]")
        message_raw = LlmPayloadHandler._require_dict_field(
            choice.get("message"), "'message'"
        )
        finish_reason = choice.get("finish_reason")
        if finish_reason is not None and not isinstance(finish_reason, str):
            finish_reason = None
        usage = LlmSseHelpers.parse_usage(on_usage)
        return LLMResponse(
            message=cast(LLMMessage, message_raw),
            finish_reason=finish_reason,
            usage=usage,
        )

    @staticmethod
    def xǁLlmPayloadHandlerǁparse_response__mutmut_42(
        raw: dict[str, Any],
        on_usage: Callable[[int, int], None] | None = None,
    ) -> LLMResponse:
        """Validate and parse raw LLM JSON into LLMResponse DTO; raises ValueError on schema mismatch."""
        choices = raw.get("choices")
        if not isinstance(choices, list) or not choices:
            raise ValueError("Unexpected LLM response: missing or empty 'choices'")
        choice = LlmPayloadHandler._require_dict_field(choices[0], "choices[0]")
        message_raw = LlmPayloadHandler._require_dict_field(
            choice.get("message"), "'message'"
        )
        finish_reason = choice.get("finish_reason")
        if finish_reason is not None and not isinstance(finish_reason, str):
            finish_reason = None
        usage = LlmSseHelpers.parse_usage(raw, )
        return LLMResponse(
            message=cast(LLMMessage, message_raw),
            finish_reason=finish_reason,
            usage=usage,
        )

    @staticmethod
    def xǁLlmPayloadHandlerǁparse_response__mutmut_43(
        raw: dict[str, Any],
        on_usage: Callable[[int, int], None] | None = None,
    ) -> LLMResponse:
        """Validate and parse raw LLM JSON into LLMResponse DTO; raises ValueError on schema mismatch."""
        choices = raw.get("choices")
        if not isinstance(choices, list) or not choices:
            raise ValueError("Unexpected LLM response: missing or empty 'choices'")
        choice = LlmPayloadHandler._require_dict_field(choices[0], "choices[0]")
        message_raw = LlmPayloadHandler._require_dict_field(
            choice.get("message"), "'message'"
        )
        finish_reason = choice.get("finish_reason")
        if finish_reason is not None and not isinstance(finish_reason, str):
            finish_reason = None
        usage = LlmSseHelpers.parse_usage(raw, on_usage)
        return LLMResponse(
            message=None,
            finish_reason=finish_reason,
            usage=usage,
        )

    @staticmethod
    def xǁLlmPayloadHandlerǁparse_response__mutmut_44(
        raw: dict[str, Any],
        on_usage: Callable[[int, int], None] | None = None,
    ) -> LLMResponse:
        """Validate and parse raw LLM JSON into LLMResponse DTO; raises ValueError on schema mismatch."""
        choices = raw.get("choices")
        if not isinstance(choices, list) or not choices:
            raise ValueError("Unexpected LLM response: missing or empty 'choices'")
        choice = LlmPayloadHandler._require_dict_field(choices[0], "choices[0]")
        message_raw = LlmPayloadHandler._require_dict_field(
            choice.get("message"), "'message'"
        )
        finish_reason = choice.get("finish_reason")
        if finish_reason is not None and not isinstance(finish_reason, str):
            finish_reason = None
        usage = LlmSseHelpers.parse_usage(raw, on_usage)
        return LLMResponse(
            message=cast(LLMMessage, message_raw),
            finish_reason=None,
            usage=usage,
        )

    @staticmethod
    def xǁLlmPayloadHandlerǁparse_response__mutmut_45(
        raw: dict[str, Any],
        on_usage: Callable[[int, int], None] | None = None,
    ) -> LLMResponse:
        """Validate and parse raw LLM JSON into LLMResponse DTO; raises ValueError on schema mismatch."""
        choices = raw.get("choices")
        if not isinstance(choices, list) or not choices:
            raise ValueError("Unexpected LLM response: missing or empty 'choices'")
        choice = LlmPayloadHandler._require_dict_field(choices[0], "choices[0]")
        message_raw = LlmPayloadHandler._require_dict_field(
            choice.get("message"), "'message'"
        )
        finish_reason = choice.get("finish_reason")
        if finish_reason is not None and not isinstance(finish_reason, str):
            finish_reason = None
        usage = LlmSseHelpers.parse_usage(raw, on_usage)
        return LLMResponse(
            message=cast(LLMMessage, message_raw),
            finish_reason=finish_reason,
            usage=None,
        )

    @staticmethod
    def xǁLlmPayloadHandlerǁparse_response__mutmut_46(
        raw: dict[str, Any],
        on_usage: Callable[[int, int], None] | None = None,
    ) -> LLMResponse:
        """Validate and parse raw LLM JSON into LLMResponse DTO; raises ValueError on schema mismatch."""
        choices = raw.get("choices")
        if not isinstance(choices, list) or not choices:
            raise ValueError("Unexpected LLM response: missing or empty 'choices'")
        choice = LlmPayloadHandler._require_dict_field(choices[0], "choices[0]")
        message_raw = LlmPayloadHandler._require_dict_field(
            choice.get("message"), "'message'"
        )
        finish_reason = choice.get("finish_reason")
        if finish_reason is not None and not isinstance(finish_reason, str):
            finish_reason = None
        usage = LlmSseHelpers.parse_usage(raw, on_usage)
        return LLMResponse(
            finish_reason=finish_reason,
            usage=usage,
        )

    @staticmethod
    def xǁLlmPayloadHandlerǁparse_response__mutmut_47(
        raw: dict[str, Any],
        on_usage: Callable[[int, int], None] | None = None,
    ) -> LLMResponse:
        """Validate and parse raw LLM JSON into LLMResponse DTO; raises ValueError on schema mismatch."""
        choices = raw.get("choices")
        if not isinstance(choices, list) or not choices:
            raise ValueError("Unexpected LLM response: missing or empty 'choices'")
        choice = LlmPayloadHandler._require_dict_field(choices[0], "choices[0]")
        message_raw = LlmPayloadHandler._require_dict_field(
            choice.get("message"), "'message'"
        )
        finish_reason = choice.get("finish_reason")
        if finish_reason is not None and not isinstance(finish_reason, str):
            finish_reason = None
        usage = LlmSseHelpers.parse_usage(raw, on_usage)
        return LLMResponse(
            message=cast(LLMMessage, message_raw),
            usage=usage,
        )

    @staticmethod
    def xǁLlmPayloadHandlerǁparse_response__mutmut_48(
        raw: dict[str, Any],
        on_usage: Callable[[int, int], None] | None = None,
    ) -> LLMResponse:
        """Validate and parse raw LLM JSON into LLMResponse DTO; raises ValueError on schema mismatch."""
        choices = raw.get("choices")
        if not isinstance(choices, list) or not choices:
            raise ValueError("Unexpected LLM response: missing or empty 'choices'")
        choice = LlmPayloadHandler._require_dict_field(choices[0], "choices[0]")
        message_raw = LlmPayloadHandler._require_dict_field(
            choice.get("message"), "'message'"
        )
        finish_reason = choice.get("finish_reason")
        if finish_reason is not None and not isinstance(finish_reason, str):
            finish_reason = None
        usage = LlmSseHelpers.parse_usage(raw, on_usage)
        return LLMResponse(
            message=cast(LLMMessage, message_raw),
            finish_reason=finish_reason,
            )

    @staticmethod
    def xǁLlmPayloadHandlerǁparse_response__mutmut_49(
        raw: dict[str, Any],
        on_usage: Callable[[int, int], None] | None = None,
    ) -> LLMResponse:
        """Validate and parse raw LLM JSON into LLMResponse DTO; raises ValueError on schema mismatch."""
        choices = raw.get("choices")
        if not isinstance(choices, list) or not choices:
            raise ValueError("Unexpected LLM response: missing or empty 'choices'")
        choice = LlmPayloadHandler._require_dict_field(choices[0], "choices[0]")
        message_raw = LlmPayloadHandler._require_dict_field(
            choice.get("message"), "'message'"
        )
        finish_reason = choice.get("finish_reason")
        if finish_reason is not None and not isinstance(finish_reason, str):
            finish_reason = None
        usage = LlmSseHelpers.parse_usage(raw, on_usage)
        return LLMResponse(
            message=cast(None, message_raw),
            finish_reason=finish_reason,
            usage=usage,
        )

    @staticmethod
    def xǁLlmPayloadHandlerǁparse_response__mutmut_50(
        raw: dict[str, Any],
        on_usage: Callable[[int, int], None] | None = None,
    ) -> LLMResponse:
        """Validate and parse raw LLM JSON into LLMResponse DTO; raises ValueError on schema mismatch."""
        choices = raw.get("choices")
        if not isinstance(choices, list) or not choices:
            raise ValueError("Unexpected LLM response: missing or empty 'choices'")
        choice = LlmPayloadHandler._require_dict_field(choices[0], "choices[0]")
        message_raw = LlmPayloadHandler._require_dict_field(
            choice.get("message"), "'message'"
        )
        finish_reason = choice.get("finish_reason")
        if finish_reason is not None and not isinstance(finish_reason, str):
            finish_reason = None
        usage = LlmSseHelpers.parse_usage(raw, on_usage)
        return LLMResponse(
            message=cast(LLMMessage, None),
            finish_reason=finish_reason,
            usage=usage,
        )

    @staticmethod
    def xǁLlmPayloadHandlerǁparse_response__mutmut_51(
        raw: dict[str, Any],
        on_usage: Callable[[int, int], None] | None = None,
    ) -> LLMResponse:
        """Validate and parse raw LLM JSON into LLMResponse DTO; raises ValueError on schema mismatch."""
        choices = raw.get("choices")
        if not isinstance(choices, list) or not choices:
            raise ValueError("Unexpected LLM response: missing or empty 'choices'")
        choice = LlmPayloadHandler._require_dict_field(choices[0], "choices[0]")
        message_raw = LlmPayloadHandler._require_dict_field(
            choice.get("message"), "'message'"
        )
        finish_reason = choice.get("finish_reason")
        if finish_reason is not None and not isinstance(finish_reason, str):
            finish_reason = None
        usage = LlmSseHelpers.parse_usage(raw, on_usage)
        return LLMResponse(
            message=cast(message_raw),
            finish_reason=finish_reason,
            usage=usage,
        )

    @staticmethod
    def xǁLlmPayloadHandlerǁparse_response__mutmut_52(
        raw: dict[str, Any],
        on_usage: Callable[[int, int], None] | None = None,
    ) -> LLMResponse:
        """Validate and parse raw LLM JSON into LLMResponse DTO; raises ValueError on schema mismatch."""
        choices = raw.get("choices")
        if not isinstance(choices, list) or not choices:
            raise ValueError("Unexpected LLM response: missing or empty 'choices'")
        choice = LlmPayloadHandler._require_dict_field(choices[0], "choices[0]")
        message_raw = LlmPayloadHandler._require_dict_field(
            choice.get("message"), "'message'"
        )
        finish_reason = choice.get("finish_reason")
        if finish_reason is not None and not isinstance(finish_reason, str):
            finish_reason = None
        usage = LlmSseHelpers.parse_usage(raw, on_usage)
        return LLMResponse(
            message=cast(LLMMessage, ),
            finish_reason=finish_reason,
            usage=usage,
        )

    @staticmethod
    @_mutmut_mutated(mutants_xǁLlmPayloadHandlerǁparse_non_stream_response__mutmut)
    def parse_non_stream_response(
        content: bytes, on_usage: Callable[[int, int], None] | None = None
    ) -> LLMResponse:
        """Parse a non-streaming LLM response body into LLMResponse."""
        raw = orjson.loads(content)
        if not isinstance(raw, dict):
            raise ValueError(f"LLM response is not a JSON object: {type(raw).__name__}")
        return LlmPayloadHandler.parse_response(raw, on_usage)

    @staticmethod
    def xǁLlmPayloadHandlerǁparse_non_stream_response__mutmut_orig(
        content: bytes, on_usage: Callable[[int, int], None] | None = None
    ) -> LLMResponse:
        """Parse a non-streaming LLM response body into LLMResponse."""
        raw = orjson.loads(content)
        if not isinstance(raw, dict):
            raise ValueError(f"LLM response is not a JSON object: {type(raw).__name__}")
        return LlmPayloadHandler.parse_response(raw, on_usage)

    @staticmethod
    def xǁLlmPayloadHandlerǁparse_non_stream_response__mutmut_1(
        content: bytes, on_usage: Callable[[int, int], None] | None = None
    ) -> LLMResponse:
        """Parse a non-streaming LLM response body into LLMResponse."""
        raw = None
        if not isinstance(raw, dict):
            raise ValueError(f"LLM response is not a JSON object: {type(raw).__name__}")
        return LlmPayloadHandler.parse_response(raw, on_usage)

    @staticmethod
    def xǁLlmPayloadHandlerǁparse_non_stream_response__mutmut_2(
        content: bytes, on_usage: Callable[[int, int], None] | None = None
    ) -> LLMResponse:
        """Parse a non-streaming LLM response body into LLMResponse."""
        raw = orjson.loads(None)
        if not isinstance(raw, dict):
            raise ValueError(f"LLM response is not a JSON object: {type(raw).__name__}")
        return LlmPayloadHandler.parse_response(raw, on_usage)

    @staticmethod
    def xǁLlmPayloadHandlerǁparse_non_stream_response__mutmut_3(
        content: bytes, on_usage: Callable[[int, int], None] | None = None
    ) -> LLMResponse:
        """Parse a non-streaming LLM response body into LLMResponse."""
        raw = orjson.loads(content)
        if isinstance(raw, dict):
            raise ValueError(f"LLM response is not a JSON object: {type(raw).__name__}")
        return LlmPayloadHandler.parse_response(raw, on_usage)

    @staticmethod
    def xǁLlmPayloadHandlerǁparse_non_stream_response__mutmut_4(
        content: bytes, on_usage: Callable[[int, int], None] | None = None
    ) -> LLMResponse:
        """Parse a non-streaming LLM response body into LLMResponse."""
        raw = orjson.loads(content)
        if not isinstance(raw, dict):
            raise ValueError(None)
        return LlmPayloadHandler.parse_response(raw, on_usage)

    @staticmethod
    def xǁLlmPayloadHandlerǁparse_non_stream_response__mutmut_5(
        content: bytes, on_usage: Callable[[int, int], None] | None = None
    ) -> LLMResponse:
        """Parse a non-streaming LLM response body into LLMResponse."""
        raw = orjson.loads(content)
        if not isinstance(raw, dict):
            raise ValueError(f"LLM response is not a JSON object: {type(None).__name__}")
        return LlmPayloadHandler.parse_response(raw, on_usage)

    @staticmethod
    def xǁLlmPayloadHandlerǁparse_non_stream_response__mutmut_6(
        content: bytes, on_usage: Callable[[int, int], None] | None = None
    ) -> LLMResponse:
        """Parse a non-streaming LLM response body into LLMResponse."""
        raw = orjson.loads(content)
        if not isinstance(raw, dict):
            raise ValueError(f"LLM response is not a JSON object: {type(raw).__name__}")
        return LlmPayloadHandler.parse_response(None, on_usage)

    @staticmethod
    def xǁLlmPayloadHandlerǁparse_non_stream_response__mutmut_7(
        content: bytes, on_usage: Callable[[int, int], None] | None = None
    ) -> LLMResponse:
        """Parse a non-streaming LLM response body into LLMResponse."""
        raw = orjson.loads(content)
        if not isinstance(raw, dict):
            raise ValueError(f"LLM response is not a JSON object: {type(raw).__name__}")
        return LlmPayloadHandler.parse_response(raw, None)

    @staticmethod
    def xǁLlmPayloadHandlerǁparse_non_stream_response__mutmut_8(
        content: bytes, on_usage: Callable[[int, int], None] | None = None
    ) -> LLMResponse:
        """Parse a non-streaming LLM response body into LLMResponse."""
        raw = orjson.loads(content)
        if not isinstance(raw, dict):
            raise ValueError(f"LLM response is not a JSON object: {type(raw).__name__}")
        return LlmPayloadHandler.parse_response(on_usage)

    @staticmethod
    def xǁLlmPayloadHandlerǁparse_non_stream_response__mutmut_9(
        content: bytes, on_usage: Callable[[int, int], None] | None = None
    ) -> LLMResponse:
        """Parse a non-streaming LLM response body into LLMResponse."""
        raw = orjson.loads(content)
        if not isinstance(raw, dict):
            raise ValueError(f"LLM response is not a JSON object: {type(raw).__name__}")
        return LlmPayloadHandler.parse_response(raw, )

mutants_xǁLlmPayloadHandlerǁbuild_payload__mutmut['_mutmut_orig'] = LlmPayloadHandler.xǁLlmPayloadHandlerǁbuild_payload__mutmut_orig # type: ignore # mutmut generated
mutants_xǁLlmPayloadHandlerǁbuild_payload__mutmut['xǁLlmPayloadHandlerǁbuild_payload__mutmut_1'] = LlmPayloadHandler.xǁLlmPayloadHandlerǁbuild_payload__mutmut_1 # type: ignore # mutmut generated
mutants_xǁLlmPayloadHandlerǁbuild_payload__mutmut['xǁLlmPayloadHandlerǁbuild_payload__mutmut_2'] = LlmPayloadHandler.xǁLlmPayloadHandlerǁbuild_payload__mutmut_2 # type: ignore # mutmut generated
mutants_xǁLlmPayloadHandlerǁbuild_payload__mutmut['xǁLlmPayloadHandlerǁbuild_payload__mutmut_3'] = LlmPayloadHandler.xǁLlmPayloadHandlerǁbuild_payload__mutmut_3 # type: ignore # mutmut generated
mutants_xǁLlmPayloadHandlerǁbuild_payload__mutmut['xǁLlmPayloadHandlerǁbuild_payload__mutmut_4'] = LlmPayloadHandler.xǁLlmPayloadHandlerǁbuild_payload__mutmut_4 # type: ignore # mutmut generated
mutants_xǁLlmPayloadHandlerǁbuild_payload__mutmut['xǁLlmPayloadHandlerǁbuild_payload__mutmut_5'] = LlmPayloadHandler.xǁLlmPayloadHandlerǁbuild_payload__mutmut_5 # type: ignore # mutmut generated
mutants_xǁLlmPayloadHandlerǁbuild_payload__mutmut['xǁLlmPayloadHandlerǁbuild_payload__mutmut_6'] = LlmPayloadHandler.xǁLlmPayloadHandlerǁbuild_payload__mutmut_6 # type: ignore # mutmut generated
mutants_xǁLlmPayloadHandlerǁbuild_payload__mutmut['xǁLlmPayloadHandlerǁbuild_payload__mutmut_7'] = LlmPayloadHandler.xǁLlmPayloadHandlerǁbuild_payload__mutmut_7 # type: ignore # mutmut generated
mutants_xǁLlmPayloadHandlerǁbuild_payload__mutmut['xǁLlmPayloadHandlerǁbuild_payload__mutmut_8'] = LlmPayloadHandler.xǁLlmPayloadHandlerǁbuild_payload__mutmut_8 # type: ignore # mutmut generated
mutants_xǁLlmPayloadHandlerǁbuild_payload__mutmut['xǁLlmPayloadHandlerǁbuild_payload__mutmut_9'] = LlmPayloadHandler.xǁLlmPayloadHandlerǁbuild_payload__mutmut_9 # type: ignore # mutmut generated
mutants_xǁLlmPayloadHandlerǁbuild_payload__mutmut['xǁLlmPayloadHandlerǁbuild_payload__mutmut_10'] = LlmPayloadHandler.xǁLlmPayloadHandlerǁbuild_payload__mutmut_10 # type: ignore # mutmut generated
mutants_xǁLlmPayloadHandlerǁbuild_payload__mutmut['xǁLlmPayloadHandlerǁbuild_payload__mutmut_11'] = LlmPayloadHandler.xǁLlmPayloadHandlerǁbuild_payload__mutmut_11 # type: ignore # mutmut generated
mutants_xǁLlmPayloadHandlerǁbuild_payload__mutmut['xǁLlmPayloadHandlerǁbuild_payload__mutmut_12'] = LlmPayloadHandler.xǁLlmPayloadHandlerǁbuild_payload__mutmut_12 # type: ignore # mutmut generated
mutants_xǁLlmPayloadHandlerǁbuild_payload__mutmut['xǁLlmPayloadHandlerǁbuild_payload__mutmut_13'] = LlmPayloadHandler.xǁLlmPayloadHandlerǁbuild_payload__mutmut_13 # type: ignore # mutmut generated
mutants_xǁLlmPayloadHandlerǁbuild_payload__mutmut['xǁLlmPayloadHandlerǁbuild_payload__mutmut_14'] = LlmPayloadHandler.xǁLlmPayloadHandlerǁbuild_payload__mutmut_14 # type: ignore # mutmut generated
mutants_xǁLlmPayloadHandlerǁbuild_payload__mutmut['xǁLlmPayloadHandlerǁbuild_payload__mutmut_15'] = LlmPayloadHandler.xǁLlmPayloadHandlerǁbuild_payload__mutmut_15 # type: ignore # mutmut generated
mutants_xǁLlmPayloadHandlerǁbuild_payload__mutmut['xǁLlmPayloadHandlerǁbuild_payload__mutmut_16'] = LlmPayloadHandler.xǁLlmPayloadHandlerǁbuild_payload__mutmut_16 # type: ignore # mutmut generated
mutants_xǁLlmPayloadHandlerǁbuild_payload__mutmut['xǁLlmPayloadHandlerǁbuild_payload__mutmut_17'] = LlmPayloadHandler.xǁLlmPayloadHandlerǁbuild_payload__mutmut_17 # type: ignore # mutmut generated
mutants_xǁLlmPayloadHandlerǁbuild_payload__mutmut['xǁLlmPayloadHandlerǁbuild_payload__mutmut_18'] = LlmPayloadHandler.xǁLlmPayloadHandlerǁbuild_payload__mutmut_18 # type: ignore # mutmut generated

mutants_xǁLlmPayloadHandlerǁ_require_dict_field__mutmut['_mutmut_orig'] = LlmPayloadHandler.xǁLlmPayloadHandlerǁ_require_dict_field__mutmut_orig # type: ignore # mutmut generated
mutants_xǁLlmPayloadHandlerǁ_require_dict_field__mutmut['xǁLlmPayloadHandlerǁ_require_dict_field__mutmut_1'] = LlmPayloadHandler.xǁLlmPayloadHandlerǁ_require_dict_field__mutmut_1 # type: ignore # mutmut generated
mutants_xǁLlmPayloadHandlerǁ_require_dict_field__mutmut['xǁLlmPayloadHandlerǁ_require_dict_field__mutmut_2'] = LlmPayloadHandler.xǁLlmPayloadHandlerǁ_require_dict_field__mutmut_2 # type: ignore # mutmut generated

mutants_xǁLlmPayloadHandlerǁparse_response__mutmut['_mutmut_orig'] = LlmPayloadHandler.xǁLlmPayloadHandlerǁparse_response__mutmut_orig # type: ignore # mutmut generated
mutants_xǁLlmPayloadHandlerǁparse_response__mutmut['xǁLlmPayloadHandlerǁparse_response__mutmut_1'] = LlmPayloadHandler.xǁLlmPayloadHandlerǁparse_response__mutmut_1 # type: ignore # mutmut generated
mutants_xǁLlmPayloadHandlerǁparse_response__mutmut['xǁLlmPayloadHandlerǁparse_response__mutmut_2'] = LlmPayloadHandler.xǁLlmPayloadHandlerǁparse_response__mutmut_2 # type: ignore # mutmut generated
mutants_xǁLlmPayloadHandlerǁparse_response__mutmut['xǁLlmPayloadHandlerǁparse_response__mutmut_3'] = LlmPayloadHandler.xǁLlmPayloadHandlerǁparse_response__mutmut_3 # type: ignore # mutmut generated
mutants_xǁLlmPayloadHandlerǁparse_response__mutmut['xǁLlmPayloadHandlerǁparse_response__mutmut_4'] = LlmPayloadHandler.xǁLlmPayloadHandlerǁparse_response__mutmut_4 # type: ignore # mutmut generated
mutants_xǁLlmPayloadHandlerǁparse_response__mutmut['xǁLlmPayloadHandlerǁparse_response__mutmut_5'] = LlmPayloadHandler.xǁLlmPayloadHandlerǁparse_response__mutmut_5 # type: ignore # mutmut generated
mutants_xǁLlmPayloadHandlerǁparse_response__mutmut['xǁLlmPayloadHandlerǁparse_response__mutmut_6'] = LlmPayloadHandler.xǁLlmPayloadHandlerǁparse_response__mutmut_6 # type: ignore # mutmut generated
mutants_xǁLlmPayloadHandlerǁparse_response__mutmut['xǁLlmPayloadHandlerǁparse_response__mutmut_7'] = LlmPayloadHandler.xǁLlmPayloadHandlerǁparse_response__mutmut_7 # type: ignore # mutmut generated
mutants_xǁLlmPayloadHandlerǁparse_response__mutmut['xǁLlmPayloadHandlerǁparse_response__mutmut_8'] = LlmPayloadHandler.xǁLlmPayloadHandlerǁparse_response__mutmut_8 # type: ignore # mutmut generated
mutants_xǁLlmPayloadHandlerǁparse_response__mutmut['xǁLlmPayloadHandlerǁparse_response__mutmut_9'] = LlmPayloadHandler.xǁLlmPayloadHandlerǁparse_response__mutmut_9 # type: ignore # mutmut generated
mutants_xǁLlmPayloadHandlerǁparse_response__mutmut['xǁLlmPayloadHandlerǁparse_response__mutmut_10'] = LlmPayloadHandler.xǁLlmPayloadHandlerǁparse_response__mutmut_10 # type: ignore # mutmut generated
mutants_xǁLlmPayloadHandlerǁparse_response__mutmut['xǁLlmPayloadHandlerǁparse_response__mutmut_11'] = LlmPayloadHandler.xǁLlmPayloadHandlerǁparse_response__mutmut_11 # type: ignore # mutmut generated
mutants_xǁLlmPayloadHandlerǁparse_response__mutmut['xǁLlmPayloadHandlerǁparse_response__mutmut_12'] = LlmPayloadHandler.xǁLlmPayloadHandlerǁparse_response__mutmut_12 # type: ignore # mutmut generated
mutants_xǁLlmPayloadHandlerǁparse_response__mutmut['xǁLlmPayloadHandlerǁparse_response__mutmut_13'] = LlmPayloadHandler.xǁLlmPayloadHandlerǁparse_response__mutmut_13 # type: ignore # mutmut generated
mutants_xǁLlmPayloadHandlerǁparse_response__mutmut['xǁLlmPayloadHandlerǁparse_response__mutmut_14'] = LlmPayloadHandler.xǁLlmPayloadHandlerǁparse_response__mutmut_14 # type: ignore # mutmut generated
mutants_xǁLlmPayloadHandlerǁparse_response__mutmut['xǁLlmPayloadHandlerǁparse_response__mutmut_15'] = LlmPayloadHandler.xǁLlmPayloadHandlerǁparse_response__mutmut_15 # type: ignore # mutmut generated
mutants_xǁLlmPayloadHandlerǁparse_response__mutmut['xǁLlmPayloadHandlerǁparse_response__mutmut_16'] = LlmPayloadHandler.xǁLlmPayloadHandlerǁparse_response__mutmut_16 # type: ignore # mutmut generated
mutants_xǁLlmPayloadHandlerǁparse_response__mutmut['xǁLlmPayloadHandlerǁparse_response__mutmut_17'] = LlmPayloadHandler.xǁLlmPayloadHandlerǁparse_response__mutmut_17 # type: ignore # mutmut generated
mutants_xǁLlmPayloadHandlerǁparse_response__mutmut['xǁLlmPayloadHandlerǁparse_response__mutmut_18'] = LlmPayloadHandler.xǁLlmPayloadHandlerǁparse_response__mutmut_18 # type: ignore # mutmut generated
mutants_xǁLlmPayloadHandlerǁparse_response__mutmut['xǁLlmPayloadHandlerǁparse_response__mutmut_19'] = LlmPayloadHandler.xǁLlmPayloadHandlerǁparse_response__mutmut_19 # type: ignore # mutmut generated
mutants_xǁLlmPayloadHandlerǁparse_response__mutmut['xǁLlmPayloadHandlerǁparse_response__mutmut_20'] = LlmPayloadHandler.xǁLlmPayloadHandlerǁparse_response__mutmut_20 # type: ignore # mutmut generated
mutants_xǁLlmPayloadHandlerǁparse_response__mutmut['xǁLlmPayloadHandlerǁparse_response__mutmut_21'] = LlmPayloadHandler.xǁLlmPayloadHandlerǁparse_response__mutmut_21 # type: ignore # mutmut generated
mutants_xǁLlmPayloadHandlerǁparse_response__mutmut['xǁLlmPayloadHandlerǁparse_response__mutmut_22'] = LlmPayloadHandler.xǁLlmPayloadHandlerǁparse_response__mutmut_22 # type: ignore # mutmut generated
mutants_xǁLlmPayloadHandlerǁparse_response__mutmut['xǁLlmPayloadHandlerǁparse_response__mutmut_23'] = LlmPayloadHandler.xǁLlmPayloadHandlerǁparse_response__mutmut_23 # type: ignore # mutmut generated
mutants_xǁLlmPayloadHandlerǁparse_response__mutmut['xǁLlmPayloadHandlerǁparse_response__mutmut_24'] = LlmPayloadHandler.xǁLlmPayloadHandlerǁparse_response__mutmut_24 # type: ignore # mutmut generated
mutants_xǁLlmPayloadHandlerǁparse_response__mutmut['xǁLlmPayloadHandlerǁparse_response__mutmut_25'] = LlmPayloadHandler.xǁLlmPayloadHandlerǁparse_response__mutmut_25 # type: ignore # mutmut generated
mutants_xǁLlmPayloadHandlerǁparse_response__mutmut['xǁLlmPayloadHandlerǁparse_response__mutmut_26'] = LlmPayloadHandler.xǁLlmPayloadHandlerǁparse_response__mutmut_26 # type: ignore # mutmut generated
mutants_xǁLlmPayloadHandlerǁparse_response__mutmut['xǁLlmPayloadHandlerǁparse_response__mutmut_27'] = LlmPayloadHandler.xǁLlmPayloadHandlerǁparse_response__mutmut_27 # type: ignore # mutmut generated
mutants_xǁLlmPayloadHandlerǁparse_response__mutmut['xǁLlmPayloadHandlerǁparse_response__mutmut_28'] = LlmPayloadHandler.xǁLlmPayloadHandlerǁparse_response__mutmut_28 # type: ignore # mutmut generated
mutants_xǁLlmPayloadHandlerǁparse_response__mutmut['xǁLlmPayloadHandlerǁparse_response__mutmut_29'] = LlmPayloadHandler.xǁLlmPayloadHandlerǁparse_response__mutmut_29 # type: ignore # mutmut generated
mutants_xǁLlmPayloadHandlerǁparse_response__mutmut['xǁLlmPayloadHandlerǁparse_response__mutmut_30'] = LlmPayloadHandler.xǁLlmPayloadHandlerǁparse_response__mutmut_30 # type: ignore # mutmut generated
mutants_xǁLlmPayloadHandlerǁparse_response__mutmut['xǁLlmPayloadHandlerǁparse_response__mutmut_31'] = LlmPayloadHandler.xǁLlmPayloadHandlerǁparse_response__mutmut_31 # type: ignore # mutmut generated
mutants_xǁLlmPayloadHandlerǁparse_response__mutmut['xǁLlmPayloadHandlerǁparse_response__mutmut_32'] = LlmPayloadHandler.xǁLlmPayloadHandlerǁparse_response__mutmut_32 # type: ignore # mutmut generated
mutants_xǁLlmPayloadHandlerǁparse_response__mutmut['xǁLlmPayloadHandlerǁparse_response__mutmut_33'] = LlmPayloadHandler.xǁLlmPayloadHandlerǁparse_response__mutmut_33 # type: ignore # mutmut generated
mutants_xǁLlmPayloadHandlerǁparse_response__mutmut['xǁLlmPayloadHandlerǁparse_response__mutmut_34'] = LlmPayloadHandler.xǁLlmPayloadHandlerǁparse_response__mutmut_34 # type: ignore # mutmut generated
mutants_xǁLlmPayloadHandlerǁparse_response__mutmut['xǁLlmPayloadHandlerǁparse_response__mutmut_35'] = LlmPayloadHandler.xǁLlmPayloadHandlerǁparse_response__mutmut_35 # type: ignore # mutmut generated
mutants_xǁLlmPayloadHandlerǁparse_response__mutmut['xǁLlmPayloadHandlerǁparse_response__mutmut_36'] = LlmPayloadHandler.xǁLlmPayloadHandlerǁparse_response__mutmut_36 # type: ignore # mutmut generated
mutants_xǁLlmPayloadHandlerǁparse_response__mutmut['xǁLlmPayloadHandlerǁparse_response__mutmut_37'] = LlmPayloadHandler.xǁLlmPayloadHandlerǁparse_response__mutmut_37 # type: ignore # mutmut generated
mutants_xǁLlmPayloadHandlerǁparse_response__mutmut['xǁLlmPayloadHandlerǁparse_response__mutmut_38'] = LlmPayloadHandler.xǁLlmPayloadHandlerǁparse_response__mutmut_38 # type: ignore # mutmut generated
mutants_xǁLlmPayloadHandlerǁparse_response__mutmut['xǁLlmPayloadHandlerǁparse_response__mutmut_39'] = LlmPayloadHandler.xǁLlmPayloadHandlerǁparse_response__mutmut_39 # type: ignore # mutmut generated
mutants_xǁLlmPayloadHandlerǁparse_response__mutmut['xǁLlmPayloadHandlerǁparse_response__mutmut_40'] = LlmPayloadHandler.xǁLlmPayloadHandlerǁparse_response__mutmut_40 # type: ignore # mutmut generated
mutants_xǁLlmPayloadHandlerǁparse_response__mutmut['xǁLlmPayloadHandlerǁparse_response__mutmut_41'] = LlmPayloadHandler.xǁLlmPayloadHandlerǁparse_response__mutmut_41 # type: ignore # mutmut generated
mutants_xǁLlmPayloadHandlerǁparse_response__mutmut['xǁLlmPayloadHandlerǁparse_response__mutmut_42'] = LlmPayloadHandler.xǁLlmPayloadHandlerǁparse_response__mutmut_42 # type: ignore # mutmut generated
mutants_xǁLlmPayloadHandlerǁparse_response__mutmut['xǁLlmPayloadHandlerǁparse_response__mutmut_43'] = LlmPayloadHandler.xǁLlmPayloadHandlerǁparse_response__mutmut_43 # type: ignore # mutmut generated
mutants_xǁLlmPayloadHandlerǁparse_response__mutmut['xǁLlmPayloadHandlerǁparse_response__mutmut_44'] = LlmPayloadHandler.xǁLlmPayloadHandlerǁparse_response__mutmut_44 # type: ignore # mutmut generated
mutants_xǁLlmPayloadHandlerǁparse_response__mutmut['xǁLlmPayloadHandlerǁparse_response__mutmut_45'] = LlmPayloadHandler.xǁLlmPayloadHandlerǁparse_response__mutmut_45 # type: ignore # mutmut generated
mutants_xǁLlmPayloadHandlerǁparse_response__mutmut['xǁLlmPayloadHandlerǁparse_response__mutmut_46'] = LlmPayloadHandler.xǁLlmPayloadHandlerǁparse_response__mutmut_46 # type: ignore # mutmut generated
mutants_xǁLlmPayloadHandlerǁparse_response__mutmut['xǁLlmPayloadHandlerǁparse_response__mutmut_47'] = LlmPayloadHandler.xǁLlmPayloadHandlerǁparse_response__mutmut_47 # type: ignore # mutmut generated
mutants_xǁLlmPayloadHandlerǁparse_response__mutmut['xǁLlmPayloadHandlerǁparse_response__mutmut_48'] = LlmPayloadHandler.xǁLlmPayloadHandlerǁparse_response__mutmut_48 # type: ignore # mutmut generated
mutants_xǁLlmPayloadHandlerǁparse_response__mutmut['xǁLlmPayloadHandlerǁparse_response__mutmut_49'] = LlmPayloadHandler.xǁLlmPayloadHandlerǁparse_response__mutmut_49 # type: ignore # mutmut generated
mutants_xǁLlmPayloadHandlerǁparse_response__mutmut['xǁLlmPayloadHandlerǁparse_response__mutmut_50'] = LlmPayloadHandler.xǁLlmPayloadHandlerǁparse_response__mutmut_50 # type: ignore # mutmut generated
mutants_xǁLlmPayloadHandlerǁparse_response__mutmut['xǁLlmPayloadHandlerǁparse_response__mutmut_51'] = LlmPayloadHandler.xǁLlmPayloadHandlerǁparse_response__mutmut_51 # type: ignore # mutmut generated
mutants_xǁLlmPayloadHandlerǁparse_response__mutmut['xǁLlmPayloadHandlerǁparse_response__mutmut_52'] = LlmPayloadHandler.xǁLlmPayloadHandlerǁparse_response__mutmut_52 # type: ignore # mutmut generated

mutants_xǁLlmPayloadHandlerǁparse_non_stream_response__mutmut['_mutmut_orig'] = LlmPayloadHandler.xǁLlmPayloadHandlerǁparse_non_stream_response__mutmut_orig # type: ignore # mutmut generated
mutants_xǁLlmPayloadHandlerǁparse_non_stream_response__mutmut['xǁLlmPayloadHandlerǁparse_non_stream_response__mutmut_1'] = LlmPayloadHandler.xǁLlmPayloadHandlerǁparse_non_stream_response__mutmut_1 # type: ignore # mutmut generated
mutants_xǁLlmPayloadHandlerǁparse_non_stream_response__mutmut['xǁLlmPayloadHandlerǁparse_non_stream_response__mutmut_2'] = LlmPayloadHandler.xǁLlmPayloadHandlerǁparse_non_stream_response__mutmut_2 # type: ignore # mutmut generated
mutants_xǁLlmPayloadHandlerǁparse_non_stream_response__mutmut['xǁLlmPayloadHandlerǁparse_non_stream_response__mutmut_3'] = LlmPayloadHandler.xǁLlmPayloadHandlerǁparse_non_stream_response__mutmut_3 # type: ignore # mutmut generated
mutants_xǁLlmPayloadHandlerǁparse_non_stream_response__mutmut['xǁLlmPayloadHandlerǁparse_non_stream_response__mutmut_4'] = LlmPayloadHandler.xǁLlmPayloadHandlerǁparse_non_stream_response__mutmut_4 # type: ignore # mutmut generated
mutants_xǁLlmPayloadHandlerǁparse_non_stream_response__mutmut['xǁLlmPayloadHandlerǁparse_non_stream_response__mutmut_5'] = LlmPayloadHandler.xǁLlmPayloadHandlerǁparse_non_stream_response__mutmut_5 # type: ignore # mutmut generated
mutants_xǁLlmPayloadHandlerǁparse_non_stream_response__mutmut['xǁLlmPayloadHandlerǁparse_non_stream_response__mutmut_6'] = LlmPayloadHandler.xǁLlmPayloadHandlerǁparse_non_stream_response__mutmut_6 # type: ignore # mutmut generated
mutants_xǁLlmPayloadHandlerǁparse_non_stream_response__mutmut['xǁLlmPayloadHandlerǁparse_non_stream_response__mutmut_7'] = LlmPayloadHandler.xǁLlmPayloadHandlerǁparse_non_stream_response__mutmut_7 # type: ignore # mutmut generated
mutants_xǁLlmPayloadHandlerǁparse_non_stream_response__mutmut['xǁLlmPayloadHandlerǁparse_non_stream_response__mutmut_8'] = LlmPayloadHandler.xǁLlmPayloadHandlerǁparse_non_stream_response__mutmut_8 # type: ignore # mutmut generated
mutants_xǁLlmPayloadHandlerǁparse_non_stream_response__mutmut['xǁLlmPayloadHandlerǁparse_non_stream_response__mutmut_9'] = LlmPayloadHandler.xǁLlmPayloadHandlerǁparse_non_stream_response__mutmut_9 # type: ignore # mutmut generated
