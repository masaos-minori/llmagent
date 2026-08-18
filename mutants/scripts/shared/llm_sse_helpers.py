#!/usr/bin/env python3
"""scripts/shared/llm_sse_helpers.py — SSE streaming helper methods for LLMClient."""

from collections.abc import Callable, Mapping
from typing import Any

import orjson

from shared.llm_types import LLMUsage
from shared.sse_parser import RobustSSEParser
from shared.types import AccumulatedToolCall, ToolCallDelta


from mutmut.mutation.trampoline import wrap_in_trampoline as _mutmut_mutated, MutantDict
mutants_xǁLlmSseHelpersǁmerge_tool_call_delta__mutmut: MutantDict = {}  # type: ignore
mutants_xǁLlmSseHelpersǁbuild_stream_response__mutmut: MutantDict = {}  # type: ignore
mutants_xǁLlmSseHelpersǁprocess_sse_chunk__mutmut: MutantDict = {}  # type: ignore
mutants_xǁLlmSseHelpersǁprocess_sse_payloads__mutmut: MutantDict = {}  # type: ignore
mutants_xǁLlmSseHelpersǁparse_usage__mutmut: MutantDict = {}  # type: ignore
mutants_xǁLlmSseHelpersǁaccumulate_parse_errors__mutmut: MutantDict = {}  # type: ignore


class LlmSseHelpers:
    """Static methods for SSE streaming helpers used by LLMClient."""

    @staticmethod
    @_mutmut_mutated(mutants_xǁLlmSseHelpersǁmerge_tool_call_delta__mutmut)
    def merge_tool_call_delta(
        tool_calls_map: dict[int, AccumulatedToolCall],
        tc_delta: ToolCallDelta,
    ) -> None:
        """Accumulate one streaming tool_call delta into the index-keyed map."""
        idx = tc_delta.get("index", 0)
        if idx not in tool_calls_map:
            tool_calls_map[idx] = {
                "id": "",
                "type": "function",
                "function": {"name": "", "arguments": ""},
            }
        tc = tool_calls_map[idx]
        if tc_delta.get("id"):
            tc["id"] = tc_delta.get("id", "")
        fn = tc_delta.get("function")
        if fn is not None:
            tc["function"]["name"] += fn.get("name", "")
            tc["function"]["arguments"] += fn.get("arguments", "")

    @staticmethod
    def xǁLlmSseHelpersǁmerge_tool_call_delta__mutmut_orig(
        tool_calls_map: dict[int, AccumulatedToolCall],
        tc_delta: ToolCallDelta,
    ) -> None:
        """Accumulate one streaming tool_call delta into the index-keyed map."""
        idx = tc_delta.get("index", 0)
        if idx not in tool_calls_map:
            tool_calls_map[idx] = {
                "id": "",
                "type": "function",
                "function": {"name": "", "arguments": ""},
            }
        tc = tool_calls_map[idx]
        if tc_delta.get("id"):
            tc["id"] = tc_delta.get("id", "")
        fn = tc_delta.get("function")
        if fn is not None:
            tc["function"]["name"] += fn.get("name", "")
            tc["function"]["arguments"] += fn.get("arguments", "")

    @staticmethod
    def xǁLlmSseHelpersǁmerge_tool_call_delta__mutmut_1(
        tool_calls_map: dict[int, AccumulatedToolCall],
        tc_delta: ToolCallDelta,
    ) -> None:
        """Accumulate one streaming tool_call delta into the index-keyed map."""
        idx = None
        if idx not in tool_calls_map:
            tool_calls_map[idx] = {
                "id": "",
                "type": "function",
                "function": {"name": "", "arguments": ""},
            }
        tc = tool_calls_map[idx]
        if tc_delta.get("id"):
            tc["id"] = tc_delta.get("id", "")
        fn = tc_delta.get("function")
        if fn is not None:
            tc["function"]["name"] += fn.get("name", "")
            tc["function"]["arguments"] += fn.get("arguments", "")

    @staticmethod
    def xǁLlmSseHelpersǁmerge_tool_call_delta__mutmut_2(
        tool_calls_map: dict[int, AccumulatedToolCall],
        tc_delta: ToolCallDelta,
    ) -> None:
        """Accumulate one streaming tool_call delta into the index-keyed map."""
        idx = tc_delta.get(None, 0)
        if idx not in tool_calls_map:
            tool_calls_map[idx] = {
                "id": "",
                "type": "function",
                "function": {"name": "", "arguments": ""},
            }
        tc = tool_calls_map[idx]
        if tc_delta.get("id"):
            tc["id"] = tc_delta.get("id", "")
        fn = tc_delta.get("function")
        if fn is not None:
            tc["function"]["name"] += fn.get("name", "")
            tc["function"]["arguments"] += fn.get("arguments", "")

    @staticmethod
    def xǁLlmSseHelpersǁmerge_tool_call_delta__mutmut_3(
        tool_calls_map: dict[int, AccumulatedToolCall],
        tc_delta: ToolCallDelta,
    ) -> None:
        """Accumulate one streaming tool_call delta into the index-keyed map."""
        idx = tc_delta.get("index", None)
        if idx not in tool_calls_map:
            tool_calls_map[idx] = {
                "id": "",
                "type": "function",
                "function": {"name": "", "arguments": ""},
            }
        tc = tool_calls_map[idx]
        if tc_delta.get("id"):
            tc["id"] = tc_delta.get("id", "")
        fn = tc_delta.get("function")
        if fn is not None:
            tc["function"]["name"] += fn.get("name", "")
            tc["function"]["arguments"] += fn.get("arguments", "")

    @staticmethod
    def xǁLlmSseHelpersǁmerge_tool_call_delta__mutmut_4(
        tool_calls_map: dict[int, AccumulatedToolCall],
        tc_delta: ToolCallDelta,
    ) -> None:
        """Accumulate one streaming tool_call delta into the index-keyed map."""
        idx = tc_delta.get(0)
        if idx not in tool_calls_map:
            tool_calls_map[idx] = {
                "id": "",
                "type": "function",
                "function": {"name": "", "arguments": ""},
            }
        tc = tool_calls_map[idx]
        if tc_delta.get("id"):
            tc["id"] = tc_delta.get("id", "")
        fn = tc_delta.get("function")
        if fn is not None:
            tc["function"]["name"] += fn.get("name", "")
            tc["function"]["arguments"] += fn.get("arguments", "")

    @staticmethod
    def xǁLlmSseHelpersǁmerge_tool_call_delta__mutmut_5(
        tool_calls_map: dict[int, AccumulatedToolCall],
        tc_delta: ToolCallDelta,
    ) -> None:
        """Accumulate one streaming tool_call delta into the index-keyed map."""
        idx = tc_delta.get("index", )
        if idx not in tool_calls_map:
            tool_calls_map[idx] = {
                "id": "",
                "type": "function",
                "function": {"name": "", "arguments": ""},
            }
        tc = tool_calls_map[idx]
        if tc_delta.get("id"):
            tc["id"] = tc_delta.get("id", "")
        fn = tc_delta.get("function")
        if fn is not None:
            tc["function"]["name"] += fn.get("name", "")
            tc["function"]["arguments"] += fn.get("arguments", "")

    @staticmethod
    def xǁLlmSseHelpersǁmerge_tool_call_delta__mutmut_6(
        tool_calls_map: dict[int, AccumulatedToolCall],
        tc_delta: ToolCallDelta,
    ) -> None:
        """Accumulate one streaming tool_call delta into the index-keyed map."""
        idx = tc_delta.get("XXindexXX", 0)
        if idx not in tool_calls_map:
            tool_calls_map[idx] = {
                "id": "",
                "type": "function",
                "function": {"name": "", "arguments": ""},
            }
        tc = tool_calls_map[idx]
        if tc_delta.get("id"):
            tc["id"] = tc_delta.get("id", "")
        fn = tc_delta.get("function")
        if fn is not None:
            tc["function"]["name"] += fn.get("name", "")
            tc["function"]["arguments"] += fn.get("arguments", "")

    @staticmethod
    def xǁLlmSseHelpersǁmerge_tool_call_delta__mutmut_7(
        tool_calls_map: dict[int, AccumulatedToolCall],
        tc_delta: ToolCallDelta,
    ) -> None:
        """Accumulate one streaming tool_call delta into the index-keyed map."""
        idx = tc_delta.get("INDEX", 0)
        if idx not in tool_calls_map:
            tool_calls_map[idx] = {
                "id": "",
                "type": "function",
                "function": {"name": "", "arguments": ""},
            }
        tc = tool_calls_map[idx]
        if tc_delta.get("id"):
            tc["id"] = tc_delta.get("id", "")
        fn = tc_delta.get("function")
        if fn is not None:
            tc["function"]["name"] += fn.get("name", "")
            tc["function"]["arguments"] += fn.get("arguments", "")

    @staticmethod
    def xǁLlmSseHelpersǁmerge_tool_call_delta__mutmut_8(
        tool_calls_map: dict[int, AccumulatedToolCall],
        tc_delta: ToolCallDelta,
    ) -> None:
        """Accumulate one streaming tool_call delta into the index-keyed map."""
        idx = tc_delta.get("index", 1)
        if idx not in tool_calls_map:
            tool_calls_map[idx] = {
                "id": "",
                "type": "function",
                "function": {"name": "", "arguments": ""},
            }
        tc = tool_calls_map[idx]
        if tc_delta.get("id"):
            tc["id"] = tc_delta.get("id", "")
        fn = tc_delta.get("function")
        if fn is not None:
            tc["function"]["name"] += fn.get("name", "")
            tc["function"]["arguments"] += fn.get("arguments", "")

    @staticmethod
    def xǁLlmSseHelpersǁmerge_tool_call_delta__mutmut_9(
        tool_calls_map: dict[int, AccumulatedToolCall],
        tc_delta: ToolCallDelta,
    ) -> None:
        """Accumulate one streaming tool_call delta into the index-keyed map."""
        idx = tc_delta.get("index", 0)
        if idx in tool_calls_map:
            tool_calls_map[idx] = {
                "id": "",
                "type": "function",
                "function": {"name": "", "arguments": ""},
            }
        tc = tool_calls_map[idx]
        if tc_delta.get("id"):
            tc["id"] = tc_delta.get("id", "")
        fn = tc_delta.get("function")
        if fn is not None:
            tc["function"]["name"] += fn.get("name", "")
            tc["function"]["arguments"] += fn.get("arguments", "")

    @staticmethod
    def xǁLlmSseHelpersǁmerge_tool_call_delta__mutmut_10(
        tool_calls_map: dict[int, AccumulatedToolCall],
        tc_delta: ToolCallDelta,
    ) -> None:
        """Accumulate one streaming tool_call delta into the index-keyed map."""
        idx = tc_delta.get("index", 0)
        if idx not in tool_calls_map:
            tool_calls_map[idx] = None
        tc = tool_calls_map[idx]
        if tc_delta.get("id"):
            tc["id"] = tc_delta.get("id", "")
        fn = tc_delta.get("function")
        if fn is not None:
            tc["function"]["name"] += fn.get("name", "")
            tc["function"]["arguments"] += fn.get("arguments", "")

    @staticmethod
    def xǁLlmSseHelpersǁmerge_tool_call_delta__mutmut_11(
        tool_calls_map: dict[int, AccumulatedToolCall],
        tc_delta: ToolCallDelta,
    ) -> None:
        """Accumulate one streaming tool_call delta into the index-keyed map."""
        idx = tc_delta.get("index", 0)
        if idx not in tool_calls_map:
            tool_calls_map[idx] = {
                "XXidXX": "",
                "type": "function",
                "function": {"name": "", "arguments": ""},
            }
        tc = tool_calls_map[idx]
        if tc_delta.get("id"):
            tc["id"] = tc_delta.get("id", "")
        fn = tc_delta.get("function")
        if fn is not None:
            tc["function"]["name"] += fn.get("name", "")
            tc["function"]["arguments"] += fn.get("arguments", "")

    @staticmethod
    def xǁLlmSseHelpersǁmerge_tool_call_delta__mutmut_12(
        tool_calls_map: dict[int, AccumulatedToolCall],
        tc_delta: ToolCallDelta,
    ) -> None:
        """Accumulate one streaming tool_call delta into the index-keyed map."""
        idx = tc_delta.get("index", 0)
        if idx not in tool_calls_map:
            tool_calls_map[idx] = {
                "ID": "",
                "type": "function",
                "function": {"name": "", "arguments": ""},
            }
        tc = tool_calls_map[idx]
        if tc_delta.get("id"):
            tc["id"] = tc_delta.get("id", "")
        fn = tc_delta.get("function")
        if fn is not None:
            tc["function"]["name"] += fn.get("name", "")
            tc["function"]["arguments"] += fn.get("arguments", "")

    @staticmethod
    def xǁLlmSseHelpersǁmerge_tool_call_delta__mutmut_13(
        tool_calls_map: dict[int, AccumulatedToolCall],
        tc_delta: ToolCallDelta,
    ) -> None:
        """Accumulate one streaming tool_call delta into the index-keyed map."""
        idx = tc_delta.get("index", 0)
        if idx not in tool_calls_map:
            tool_calls_map[idx] = {
                "id": "XXXX",
                "type": "function",
                "function": {"name": "", "arguments": ""},
            }
        tc = tool_calls_map[idx]
        if tc_delta.get("id"):
            tc["id"] = tc_delta.get("id", "")
        fn = tc_delta.get("function")
        if fn is not None:
            tc["function"]["name"] += fn.get("name", "")
            tc["function"]["arguments"] += fn.get("arguments", "")

    @staticmethod
    def xǁLlmSseHelpersǁmerge_tool_call_delta__mutmut_14(
        tool_calls_map: dict[int, AccumulatedToolCall],
        tc_delta: ToolCallDelta,
    ) -> None:
        """Accumulate one streaming tool_call delta into the index-keyed map."""
        idx = tc_delta.get("index", 0)
        if idx not in tool_calls_map:
            tool_calls_map[idx] = {
                "id": "",
                "XXtypeXX": "function",
                "function": {"name": "", "arguments": ""},
            }
        tc = tool_calls_map[idx]
        if tc_delta.get("id"):
            tc["id"] = tc_delta.get("id", "")
        fn = tc_delta.get("function")
        if fn is not None:
            tc["function"]["name"] += fn.get("name", "")
            tc["function"]["arguments"] += fn.get("arguments", "")

    @staticmethod
    def xǁLlmSseHelpersǁmerge_tool_call_delta__mutmut_15(
        tool_calls_map: dict[int, AccumulatedToolCall],
        tc_delta: ToolCallDelta,
    ) -> None:
        """Accumulate one streaming tool_call delta into the index-keyed map."""
        idx = tc_delta.get("index", 0)
        if idx not in tool_calls_map:
            tool_calls_map[idx] = {
                "id": "",
                "TYPE": "function",
                "function": {"name": "", "arguments": ""},
            }
        tc = tool_calls_map[idx]
        if tc_delta.get("id"):
            tc["id"] = tc_delta.get("id", "")
        fn = tc_delta.get("function")
        if fn is not None:
            tc["function"]["name"] += fn.get("name", "")
            tc["function"]["arguments"] += fn.get("arguments", "")

    @staticmethod
    def xǁLlmSseHelpersǁmerge_tool_call_delta__mutmut_16(
        tool_calls_map: dict[int, AccumulatedToolCall],
        tc_delta: ToolCallDelta,
    ) -> None:
        """Accumulate one streaming tool_call delta into the index-keyed map."""
        idx = tc_delta.get("index", 0)
        if idx not in tool_calls_map:
            tool_calls_map[idx] = {
                "id": "",
                "type": "XXfunctionXX",
                "function": {"name": "", "arguments": ""},
            }
        tc = tool_calls_map[idx]
        if tc_delta.get("id"):
            tc["id"] = tc_delta.get("id", "")
        fn = tc_delta.get("function")
        if fn is not None:
            tc["function"]["name"] += fn.get("name", "")
            tc["function"]["arguments"] += fn.get("arguments", "")

    @staticmethod
    def xǁLlmSseHelpersǁmerge_tool_call_delta__mutmut_17(
        tool_calls_map: dict[int, AccumulatedToolCall],
        tc_delta: ToolCallDelta,
    ) -> None:
        """Accumulate one streaming tool_call delta into the index-keyed map."""
        idx = tc_delta.get("index", 0)
        if idx not in tool_calls_map:
            tool_calls_map[idx] = {
                "id": "",
                "type": "FUNCTION",
                "function": {"name": "", "arguments": ""},
            }
        tc = tool_calls_map[idx]
        if tc_delta.get("id"):
            tc["id"] = tc_delta.get("id", "")
        fn = tc_delta.get("function")
        if fn is not None:
            tc["function"]["name"] += fn.get("name", "")
            tc["function"]["arguments"] += fn.get("arguments", "")

    @staticmethod
    def xǁLlmSseHelpersǁmerge_tool_call_delta__mutmut_18(
        tool_calls_map: dict[int, AccumulatedToolCall],
        tc_delta: ToolCallDelta,
    ) -> None:
        """Accumulate one streaming tool_call delta into the index-keyed map."""
        idx = tc_delta.get("index", 0)
        if idx not in tool_calls_map:
            tool_calls_map[idx] = {
                "id": "",
                "type": "function",
                "XXfunctionXX": {"name": "", "arguments": ""},
            }
        tc = tool_calls_map[idx]
        if tc_delta.get("id"):
            tc["id"] = tc_delta.get("id", "")
        fn = tc_delta.get("function")
        if fn is not None:
            tc["function"]["name"] += fn.get("name", "")
            tc["function"]["arguments"] += fn.get("arguments", "")

    @staticmethod
    def xǁLlmSseHelpersǁmerge_tool_call_delta__mutmut_19(
        tool_calls_map: dict[int, AccumulatedToolCall],
        tc_delta: ToolCallDelta,
    ) -> None:
        """Accumulate one streaming tool_call delta into the index-keyed map."""
        idx = tc_delta.get("index", 0)
        if idx not in tool_calls_map:
            tool_calls_map[idx] = {
                "id": "",
                "type": "function",
                "FUNCTION": {"name": "", "arguments": ""},
            }
        tc = tool_calls_map[idx]
        if tc_delta.get("id"):
            tc["id"] = tc_delta.get("id", "")
        fn = tc_delta.get("function")
        if fn is not None:
            tc["function"]["name"] += fn.get("name", "")
            tc["function"]["arguments"] += fn.get("arguments", "")

    @staticmethod
    def xǁLlmSseHelpersǁmerge_tool_call_delta__mutmut_20(
        tool_calls_map: dict[int, AccumulatedToolCall],
        tc_delta: ToolCallDelta,
    ) -> None:
        """Accumulate one streaming tool_call delta into the index-keyed map."""
        idx = tc_delta.get("index", 0)
        if idx not in tool_calls_map:
            tool_calls_map[idx] = {
                "id": "",
                "type": "function",
                "function": {"XXnameXX": "", "arguments": ""},
            }
        tc = tool_calls_map[idx]
        if tc_delta.get("id"):
            tc["id"] = tc_delta.get("id", "")
        fn = tc_delta.get("function")
        if fn is not None:
            tc["function"]["name"] += fn.get("name", "")
            tc["function"]["arguments"] += fn.get("arguments", "")

    @staticmethod
    def xǁLlmSseHelpersǁmerge_tool_call_delta__mutmut_21(
        tool_calls_map: dict[int, AccumulatedToolCall],
        tc_delta: ToolCallDelta,
    ) -> None:
        """Accumulate one streaming tool_call delta into the index-keyed map."""
        idx = tc_delta.get("index", 0)
        if idx not in tool_calls_map:
            tool_calls_map[idx] = {
                "id": "",
                "type": "function",
                "function": {"NAME": "", "arguments": ""},
            }
        tc = tool_calls_map[idx]
        if tc_delta.get("id"):
            tc["id"] = tc_delta.get("id", "")
        fn = tc_delta.get("function")
        if fn is not None:
            tc["function"]["name"] += fn.get("name", "")
            tc["function"]["arguments"] += fn.get("arguments", "")

    @staticmethod
    def xǁLlmSseHelpersǁmerge_tool_call_delta__mutmut_22(
        tool_calls_map: dict[int, AccumulatedToolCall],
        tc_delta: ToolCallDelta,
    ) -> None:
        """Accumulate one streaming tool_call delta into the index-keyed map."""
        idx = tc_delta.get("index", 0)
        if idx not in tool_calls_map:
            tool_calls_map[idx] = {
                "id": "",
                "type": "function",
                "function": {"name": "XXXX", "arguments": ""},
            }
        tc = tool_calls_map[idx]
        if tc_delta.get("id"):
            tc["id"] = tc_delta.get("id", "")
        fn = tc_delta.get("function")
        if fn is not None:
            tc["function"]["name"] += fn.get("name", "")
            tc["function"]["arguments"] += fn.get("arguments", "")

    @staticmethod
    def xǁLlmSseHelpersǁmerge_tool_call_delta__mutmut_23(
        tool_calls_map: dict[int, AccumulatedToolCall],
        tc_delta: ToolCallDelta,
    ) -> None:
        """Accumulate one streaming tool_call delta into the index-keyed map."""
        idx = tc_delta.get("index", 0)
        if idx not in tool_calls_map:
            tool_calls_map[idx] = {
                "id": "",
                "type": "function",
                "function": {"name": "", "XXargumentsXX": ""},
            }
        tc = tool_calls_map[idx]
        if tc_delta.get("id"):
            tc["id"] = tc_delta.get("id", "")
        fn = tc_delta.get("function")
        if fn is not None:
            tc["function"]["name"] += fn.get("name", "")
            tc["function"]["arguments"] += fn.get("arguments", "")

    @staticmethod
    def xǁLlmSseHelpersǁmerge_tool_call_delta__mutmut_24(
        tool_calls_map: dict[int, AccumulatedToolCall],
        tc_delta: ToolCallDelta,
    ) -> None:
        """Accumulate one streaming tool_call delta into the index-keyed map."""
        idx = tc_delta.get("index", 0)
        if idx not in tool_calls_map:
            tool_calls_map[idx] = {
                "id": "",
                "type": "function",
                "function": {"name": "", "ARGUMENTS": ""},
            }
        tc = tool_calls_map[idx]
        if tc_delta.get("id"):
            tc["id"] = tc_delta.get("id", "")
        fn = tc_delta.get("function")
        if fn is not None:
            tc["function"]["name"] += fn.get("name", "")
            tc["function"]["arguments"] += fn.get("arguments", "")

    @staticmethod
    def xǁLlmSseHelpersǁmerge_tool_call_delta__mutmut_25(
        tool_calls_map: dict[int, AccumulatedToolCall],
        tc_delta: ToolCallDelta,
    ) -> None:
        """Accumulate one streaming tool_call delta into the index-keyed map."""
        idx = tc_delta.get("index", 0)
        if idx not in tool_calls_map:
            tool_calls_map[idx] = {
                "id": "",
                "type": "function",
                "function": {"name": "", "arguments": "XXXX"},
            }
        tc = tool_calls_map[idx]
        if tc_delta.get("id"):
            tc["id"] = tc_delta.get("id", "")
        fn = tc_delta.get("function")
        if fn is not None:
            tc["function"]["name"] += fn.get("name", "")
            tc["function"]["arguments"] += fn.get("arguments", "")

    @staticmethod
    def xǁLlmSseHelpersǁmerge_tool_call_delta__mutmut_26(
        tool_calls_map: dict[int, AccumulatedToolCall],
        tc_delta: ToolCallDelta,
    ) -> None:
        """Accumulate one streaming tool_call delta into the index-keyed map."""
        idx = tc_delta.get("index", 0)
        if idx not in tool_calls_map:
            tool_calls_map[idx] = {
                "id": "",
                "type": "function",
                "function": {"name": "", "arguments": ""},
            }
        tc = None
        if tc_delta.get("id"):
            tc["id"] = tc_delta.get("id", "")
        fn = tc_delta.get("function")
        if fn is not None:
            tc["function"]["name"] += fn.get("name", "")
            tc["function"]["arguments"] += fn.get("arguments", "")

    @staticmethod
    def xǁLlmSseHelpersǁmerge_tool_call_delta__mutmut_27(
        tool_calls_map: dict[int, AccumulatedToolCall],
        tc_delta: ToolCallDelta,
    ) -> None:
        """Accumulate one streaming tool_call delta into the index-keyed map."""
        idx = tc_delta.get("index", 0)
        if idx not in tool_calls_map:
            tool_calls_map[idx] = {
                "id": "",
                "type": "function",
                "function": {"name": "", "arguments": ""},
            }
        tc = tool_calls_map[idx]
        if tc_delta.get(None):
            tc["id"] = tc_delta.get("id", "")
        fn = tc_delta.get("function")
        if fn is not None:
            tc["function"]["name"] += fn.get("name", "")
            tc["function"]["arguments"] += fn.get("arguments", "")

    @staticmethod
    def xǁLlmSseHelpersǁmerge_tool_call_delta__mutmut_28(
        tool_calls_map: dict[int, AccumulatedToolCall],
        tc_delta: ToolCallDelta,
    ) -> None:
        """Accumulate one streaming tool_call delta into the index-keyed map."""
        idx = tc_delta.get("index", 0)
        if idx not in tool_calls_map:
            tool_calls_map[idx] = {
                "id": "",
                "type": "function",
                "function": {"name": "", "arguments": ""},
            }
        tc = tool_calls_map[idx]
        if tc_delta.get("XXidXX"):
            tc["id"] = tc_delta.get("id", "")
        fn = tc_delta.get("function")
        if fn is not None:
            tc["function"]["name"] += fn.get("name", "")
            tc["function"]["arguments"] += fn.get("arguments", "")

    @staticmethod
    def xǁLlmSseHelpersǁmerge_tool_call_delta__mutmut_29(
        tool_calls_map: dict[int, AccumulatedToolCall],
        tc_delta: ToolCallDelta,
    ) -> None:
        """Accumulate one streaming tool_call delta into the index-keyed map."""
        idx = tc_delta.get("index", 0)
        if idx not in tool_calls_map:
            tool_calls_map[idx] = {
                "id": "",
                "type": "function",
                "function": {"name": "", "arguments": ""},
            }
        tc = tool_calls_map[idx]
        if tc_delta.get("ID"):
            tc["id"] = tc_delta.get("id", "")
        fn = tc_delta.get("function")
        if fn is not None:
            tc["function"]["name"] += fn.get("name", "")
            tc["function"]["arguments"] += fn.get("arguments", "")

    @staticmethod
    def xǁLlmSseHelpersǁmerge_tool_call_delta__mutmut_30(
        tool_calls_map: dict[int, AccumulatedToolCall],
        tc_delta: ToolCallDelta,
    ) -> None:
        """Accumulate one streaming tool_call delta into the index-keyed map."""
        idx = tc_delta.get("index", 0)
        if idx not in tool_calls_map:
            tool_calls_map[idx] = {
                "id": "",
                "type": "function",
                "function": {"name": "", "arguments": ""},
            }
        tc = tool_calls_map[idx]
        if tc_delta.get("id"):
            tc["id"] = None
        fn = tc_delta.get("function")
        if fn is not None:
            tc["function"]["name"] += fn.get("name", "")
            tc["function"]["arguments"] += fn.get("arguments", "")

    @staticmethod
    def xǁLlmSseHelpersǁmerge_tool_call_delta__mutmut_31(
        tool_calls_map: dict[int, AccumulatedToolCall],
        tc_delta: ToolCallDelta,
    ) -> None:
        """Accumulate one streaming tool_call delta into the index-keyed map."""
        idx = tc_delta.get("index", 0)
        if idx not in tool_calls_map:
            tool_calls_map[idx] = {
                "id": "",
                "type": "function",
                "function": {"name": "", "arguments": ""},
            }
        tc = tool_calls_map[idx]
        if tc_delta.get("id"):
            tc["XXidXX"] = tc_delta.get("id", "")
        fn = tc_delta.get("function")
        if fn is not None:
            tc["function"]["name"] += fn.get("name", "")
            tc["function"]["arguments"] += fn.get("arguments", "")

    @staticmethod
    def xǁLlmSseHelpersǁmerge_tool_call_delta__mutmut_32(
        tool_calls_map: dict[int, AccumulatedToolCall],
        tc_delta: ToolCallDelta,
    ) -> None:
        """Accumulate one streaming tool_call delta into the index-keyed map."""
        idx = tc_delta.get("index", 0)
        if idx not in tool_calls_map:
            tool_calls_map[idx] = {
                "id": "",
                "type": "function",
                "function": {"name": "", "arguments": ""},
            }
        tc = tool_calls_map[idx]
        if tc_delta.get("id"):
            tc["ID"] = tc_delta.get("id", "")
        fn = tc_delta.get("function")
        if fn is not None:
            tc["function"]["name"] += fn.get("name", "")
            tc["function"]["arguments"] += fn.get("arguments", "")

    @staticmethod
    def xǁLlmSseHelpersǁmerge_tool_call_delta__mutmut_33(
        tool_calls_map: dict[int, AccumulatedToolCall],
        tc_delta: ToolCallDelta,
    ) -> None:
        """Accumulate one streaming tool_call delta into the index-keyed map."""
        idx = tc_delta.get("index", 0)
        if idx not in tool_calls_map:
            tool_calls_map[idx] = {
                "id": "",
                "type": "function",
                "function": {"name": "", "arguments": ""},
            }
        tc = tool_calls_map[idx]
        if tc_delta.get("id"):
            tc["id"] = tc_delta.get(None, "")
        fn = tc_delta.get("function")
        if fn is not None:
            tc["function"]["name"] += fn.get("name", "")
            tc["function"]["arguments"] += fn.get("arguments", "")

    @staticmethod
    def xǁLlmSseHelpersǁmerge_tool_call_delta__mutmut_34(
        tool_calls_map: dict[int, AccumulatedToolCall],
        tc_delta: ToolCallDelta,
    ) -> None:
        """Accumulate one streaming tool_call delta into the index-keyed map."""
        idx = tc_delta.get("index", 0)
        if idx not in tool_calls_map:
            tool_calls_map[idx] = {
                "id": "",
                "type": "function",
                "function": {"name": "", "arguments": ""},
            }
        tc = tool_calls_map[idx]
        if tc_delta.get("id"):
            tc["id"] = tc_delta.get("id", None)
        fn = tc_delta.get("function")
        if fn is not None:
            tc["function"]["name"] += fn.get("name", "")
            tc["function"]["arguments"] += fn.get("arguments", "")

    @staticmethod
    def xǁLlmSseHelpersǁmerge_tool_call_delta__mutmut_35(
        tool_calls_map: dict[int, AccumulatedToolCall],
        tc_delta: ToolCallDelta,
    ) -> None:
        """Accumulate one streaming tool_call delta into the index-keyed map."""
        idx = tc_delta.get("index", 0)
        if idx not in tool_calls_map:
            tool_calls_map[idx] = {
                "id": "",
                "type": "function",
                "function": {"name": "", "arguments": ""},
            }
        tc = tool_calls_map[idx]
        if tc_delta.get("id"):
            tc["id"] = tc_delta.get("")
        fn = tc_delta.get("function")
        if fn is not None:
            tc["function"]["name"] += fn.get("name", "")
            tc["function"]["arguments"] += fn.get("arguments", "")

    @staticmethod
    def xǁLlmSseHelpersǁmerge_tool_call_delta__mutmut_36(
        tool_calls_map: dict[int, AccumulatedToolCall],
        tc_delta: ToolCallDelta,
    ) -> None:
        """Accumulate one streaming tool_call delta into the index-keyed map."""
        idx = tc_delta.get("index", 0)
        if idx not in tool_calls_map:
            tool_calls_map[idx] = {
                "id": "",
                "type": "function",
                "function": {"name": "", "arguments": ""},
            }
        tc = tool_calls_map[idx]
        if tc_delta.get("id"):
            tc["id"] = tc_delta.get("id", )
        fn = tc_delta.get("function")
        if fn is not None:
            tc["function"]["name"] += fn.get("name", "")
            tc["function"]["arguments"] += fn.get("arguments", "")

    @staticmethod
    def xǁLlmSseHelpersǁmerge_tool_call_delta__mutmut_37(
        tool_calls_map: dict[int, AccumulatedToolCall],
        tc_delta: ToolCallDelta,
    ) -> None:
        """Accumulate one streaming tool_call delta into the index-keyed map."""
        idx = tc_delta.get("index", 0)
        if idx not in tool_calls_map:
            tool_calls_map[idx] = {
                "id": "",
                "type": "function",
                "function": {"name": "", "arguments": ""},
            }
        tc = tool_calls_map[idx]
        if tc_delta.get("id"):
            tc["id"] = tc_delta.get("XXidXX", "")
        fn = tc_delta.get("function")
        if fn is not None:
            tc["function"]["name"] += fn.get("name", "")
            tc["function"]["arguments"] += fn.get("arguments", "")

    @staticmethod
    def xǁLlmSseHelpersǁmerge_tool_call_delta__mutmut_38(
        tool_calls_map: dict[int, AccumulatedToolCall],
        tc_delta: ToolCallDelta,
    ) -> None:
        """Accumulate one streaming tool_call delta into the index-keyed map."""
        idx = tc_delta.get("index", 0)
        if idx not in tool_calls_map:
            tool_calls_map[idx] = {
                "id": "",
                "type": "function",
                "function": {"name": "", "arguments": ""},
            }
        tc = tool_calls_map[idx]
        if tc_delta.get("id"):
            tc["id"] = tc_delta.get("ID", "")
        fn = tc_delta.get("function")
        if fn is not None:
            tc["function"]["name"] += fn.get("name", "")
            tc["function"]["arguments"] += fn.get("arguments", "")

    @staticmethod
    def xǁLlmSseHelpersǁmerge_tool_call_delta__mutmut_39(
        tool_calls_map: dict[int, AccumulatedToolCall],
        tc_delta: ToolCallDelta,
    ) -> None:
        """Accumulate one streaming tool_call delta into the index-keyed map."""
        idx = tc_delta.get("index", 0)
        if idx not in tool_calls_map:
            tool_calls_map[idx] = {
                "id": "",
                "type": "function",
                "function": {"name": "", "arguments": ""},
            }
        tc = tool_calls_map[idx]
        if tc_delta.get("id"):
            tc["id"] = tc_delta.get("id", "XXXX")
        fn = tc_delta.get("function")
        if fn is not None:
            tc["function"]["name"] += fn.get("name", "")
            tc["function"]["arguments"] += fn.get("arguments", "")

    @staticmethod
    def xǁLlmSseHelpersǁmerge_tool_call_delta__mutmut_40(
        tool_calls_map: dict[int, AccumulatedToolCall],
        tc_delta: ToolCallDelta,
    ) -> None:
        """Accumulate one streaming tool_call delta into the index-keyed map."""
        idx = tc_delta.get("index", 0)
        if idx not in tool_calls_map:
            tool_calls_map[idx] = {
                "id": "",
                "type": "function",
                "function": {"name": "", "arguments": ""},
            }
        tc = tool_calls_map[idx]
        if tc_delta.get("id"):
            tc["id"] = tc_delta.get("id", "")
        fn = None
        if fn is not None:
            tc["function"]["name"] += fn.get("name", "")
            tc["function"]["arguments"] += fn.get("arguments", "")

    @staticmethod
    def xǁLlmSseHelpersǁmerge_tool_call_delta__mutmut_41(
        tool_calls_map: dict[int, AccumulatedToolCall],
        tc_delta: ToolCallDelta,
    ) -> None:
        """Accumulate one streaming tool_call delta into the index-keyed map."""
        idx = tc_delta.get("index", 0)
        if idx not in tool_calls_map:
            tool_calls_map[idx] = {
                "id": "",
                "type": "function",
                "function": {"name": "", "arguments": ""},
            }
        tc = tool_calls_map[idx]
        if tc_delta.get("id"):
            tc["id"] = tc_delta.get("id", "")
        fn = tc_delta.get(None)
        if fn is not None:
            tc["function"]["name"] += fn.get("name", "")
            tc["function"]["arguments"] += fn.get("arguments", "")

    @staticmethod
    def xǁLlmSseHelpersǁmerge_tool_call_delta__mutmut_42(
        tool_calls_map: dict[int, AccumulatedToolCall],
        tc_delta: ToolCallDelta,
    ) -> None:
        """Accumulate one streaming tool_call delta into the index-keyed map."""
        idx = tc_delta.get("index", 0)
        if idx not in tool_calls_map:
            tool_calls_map[idx] = {
                "id": "",
                "type": "function",
                "function": {"name": "", "arguments": ""},
            }
        tc = tool_calls_map[idx]
        if tc_delta.get("id"):
            tc["id"] = tc_delta.get("id", "")
        fn = tc_delta.get("XXfunctionXX")
        if fn is not None:
            tc["function"]["name"] += fn.get("name", "")
            tc["function"]["arguments"] += fn.get("arguments", "")

    @staticmethod
    def xǁLlmSseHelpersǁmerge_tool_call_delta__mutmut_43(
        tool_calls_map: dict[int, AccumulatedToolCall],
        tc_delta: ToolCallDelta,
    ) -> None:
        """Accumulate one streaming tool_call delta into the index-keyed map."""
        idx = tc_delta.get("index", 0)
        if idx not in tool_calls_map:
            tool_calls_map[idx] = {
                "id": "",
                "type": "function",
                "function": {"name": "", "arguments": ""},
            }
        tc = tool_calls_map[idx]
        if tc_delta.get("id"):
            tc["id"] = tc_delta.get("id", "")
        fn = tc_delta.get("FUNCTION")
        if fn is not None:
            tc["function"]["name"] += fn.get("name", "")
            tc["function"]["arguments"] += fn.get("arguments", "")

    @staticmethod
    def xǁLlmSseHelpersǁmerge_tool_call_delta__mutmut_44(
        tool_calls_map: dict[int, AccumulatedToolCall],
        tc_delta: ToolCallDelta,
    ) -> None:
        """Accumulate one streaming tool_call delta into the index-keyed map."""
        idx = tc_delta.get("index", 0)
        if idx not in tool_calls_map:
            tool_calls_map[idx] = {
                "id": "",
                "type": "function",
                "function": {"name": "", "arguments": ""},
            }
        tc = tool_calls_map[idx]
        if tc_delta.get("id"):
            tc["id"] = tc_delta.get("id", "")
        fn = tc_delta.get("function")
        if fn is None:
            tc["function"]["name"] += fn.get("name", "")
            tc["function"]["arguments"] += fn.get("arguments", "")

    @staticmethod
    def xǁLlmSseHelpersǁmerge_tool_call_delta__mutmut_45(
        tool_calls_map: dict[int, AccumulatedToolCall],
        tc_delta: ToolCallDelta,
    ) -> None:
        """Accumulate one streaming tool_call delta into the index-keyed map."""
        idx = tc_delta.get("index", 0)
        if idx not in tool_calls_map:
            tool_calls_map[idx] = {
                "id": "",
                "type": "function",
                "function": {"name": "", "arguments": ""},
            }
        tc = tool_calls_map[idx]
        if tc_delta.get("id"):
            tc["id"] = tc_delta.get("id", "")
        fn = tc_delta.get("function")
        if fn is not None:
            tc["function"]["name"] = fn.get("name", "")
            tc["function"]["arguments"] += fn.get("arguments", "")

    @staticmethod
    def xǁLlmSseHelpersǁmerge_tool_call_delta__mutmut_46(
        tool_calls_map: dict[int, AccumulatedToolCall],
        tc_delta: ToolCallDelta,
    ) -> None:
        """Accumulate one streaming tool_call delta into the index-keyed map."""
        idx = tc_delta.get("index", 0)
        if idx not in tool_calls_map:
            tool_calls_map[idx] = {
                "id": "",
                "type": "function",
                "function": {"name": "", "arguments": ""},
            }
        tc = tool_calls_map[idx]
        if tc_delta.get("id"):
            tc["id"] = tc_delta.get("id", "")
        fn = tc_delta.get("function")
        if fn is not None:
            tc["function"]["name"] -= fn.get("name", "")
            tc["function"]["arguments"] += fn.get("arguments", "")

    @staticmethod
    def xǁLlmSseHelpersǁmerge_tool_call_delta__mutmut_47(
        tool_calls_map: dict[int, AccumulatedToolCall],
        tc_delta: ToolCallDelta,
    ) -> None:
        """Accumulate one streaming tool_call delta into the index-keyed map."""
        idx = tc_delta.get("index", 0)
        if idx not in tool_calls_map:
            tool_calls_map[idx] = {
                "id": "",
                "type": "function",
                "function": {"name": "", "arguments": ""},
            }
        tc = tool_calls_map[idx]
        if tc_delta.get("id"):
            tc["id"] = tc_delta.get("id", "")
        fn = tc_delta.get("function")
        if fn is not None:
            tc["XXfunctionXX"]["name"] += fn.get("name", "")
            tc["function"]["arguments"] += fn.get("arguments", "")

    @staticmethod
    def xǁLlmSseHelpersǁmerge_tool_call_delta__mutmut_48(
        tool_calls_map: dict[int, AccumulatedToolCall],
        tc_delta: ToolCallDelta,
    ) -> None:
        """Accumulate one streaming tool_call delta into the index-keyed map."""
        idx = tc_delta.get("index", 0)
        if idx not in tool_calls_map:
            tool_calls_map[idx] = {
                "id": "",
                "type": "function",
                "function": {"name": "", "arguments": ""},
            }
        tc = tool_calls_map[idx]
        if tc_delta.get("id"):
            tc["id"] = tc_delta.get("id", "")
        fn = tc_delta.get("function")
        if fn is not None:
            tc["FUNCTION"]["name"] += fn.get("name", "")
            tc["function"]["arguments"] += fn.get("arguments", "")

    @staticmethod
    def xǁLlmSseHelpersǁmerge_tool_call_delta__mutmut_49(
        tool_calls_map: dict[int, AccumulatedToolCall],
        tc_delta: ToolCallDelta,
    ) -> None:
        """Accumulate one streaming tool_call delta into the index-keyed map."""
        idx = tc_delta.get("index", 0)
        if idx not in tool_calls_map:
            tool_calls_map[idx] = {
                "id": "",
                "type": "function",
                "function": {"name": "", "arguments": ""},
            }
        tc = tool_calls_map[idx]
        if tc_delta.get("id"):
            tc["id"] = tc_delta.get("id", "")
        fn = tc_delta.get("function")
        if fn is not None:
            tc["function"]["XXnameXX"] += fn.get("name", "")
            tc["function"]["arguments"] += fn.get("arguments", "")

    @staticmethod
    def xǁLlmSseHelpersǁmerge_tool_call_delta__mutmut_50(
        tool_calls_map: dict[int, AccumulatedToolCall],
        tc_delta: ToolCallDelta,
    ) -> None:
        """Accumulate one streaming tool_call delta into the index-keyed map."""
        idx = tc_delta.get("index", 0)
        if idx not in tool_calls_map:
            tool_calls_map[idx] = {
                "id": "",
                "type": "function",
                "function": {"name": "", "arguments": ""},
            }
        tc = tool_calls_map[idx]
        if tc_delta.get("id"):
            tc["id"] = tc_delta.get("id", "")
        fn = tc_delta.get("function")
        if fn is not None:
            tc["function"]["NAME"] += fn.get("name", "")
            tc["function"]["arguments"] += fn.get("arguments", "")

    @staticmethod
    def xǁLlmSseHelpersǁmerge_tool_call_delta__mutmut_51(
        tool_calls_map: dict[int, AccumulatedToolCall],
        tc_delta: ToolCallDelta,
    ) -> None:
        """Accumulate one streaming tool_call delta into the index-keyed map."""
        idx = tc_delta.get("index", 0)
        if idx not in tool_calls_map:
            tool_calls_map[idx] = {
                "id": "",
                "type": "function",
                "function": {"name": "", "arguments": ""},
            }
        tc = tool_calls_map[idx]
        if tc_delta.get("id"):
            tc["id"] = tc_delta.get("id", "")
        fn = tc_delta.get("function")
        if fn is not None:
            tc["function"]["name"] += fn.get(None, "")
            tc["function"]["arguments"] += fn.get("arguments", "")

    @staticmethod
    def xǁLlmSseHelpersǁmerge_tool_call_delta__mutmut_52(
        tool_calls_map: dict[int, AccumulatedToolCall],
        tc_delta: ToolCallDelta,
    ) -> None:
        """Accumulate one streaming tool_call delta into the index-keyed map."""
        idx = tc_delta.get("index", 0)
        if idx not in tool_calls_map:
            tool_calls_map[idx] = {
                "id": "",
                "type": "function",
                "function": {"name": "", "arguments": ""},
            }
        tc = tool_calls_map[idx]
        if tc_delta.get("id"):
            tc["id"] = tc_delta.get("id", "")
        fn = tc_delta.get("function")
        if fn is not None:
            tc["function"]["name"] += fn.get("name", None)
            tc["function"]["arguments"] += fn.get("arguments", "")

    @staticmethod
    def xǁLlmSseHelpersǁmerge_tool_call_delta__mutmut_53(
        tool_calls_map: dict[int, AccumulatedToolCall],
        tc_delta: ToolCallDelta,
    ) -> None:
        """Accumulate one streaming tool_call delta into the index-keyed map."""
        idx = tc_delta.get("index", 0)
        if idx not in tool_calls_map:
            tool_calls_map[idx] = {
                "id": "",
                "type": "function",
                "function": {"name": "", "arguments": ""},
            }
        tc = tool_calls_map[idx]
        if tc_delta.get("id"):
            tc["id"] = tc_delta.get("id", "")
        fn = tc_delta.get("function")
        if fn is not None:
            tc["function"]["name"] += fn.get("")
            tc["function"]["arguments"] += fn.get("arguments", "")

    @staticmethod
    def xǁLlmSseHelpersǁmerge_tool_call_delta__mutmut_54(
        tool_calls_map: dict[int, AccumulatedToolCall],
        tc_delta: ToolCallDelta,
    ) -> None:
        """Accumulate one streaming tool_call delta into the index-keyed map."""
        idx = tc_delta.get("index", 0)
        if idx not in tool_calls_map:
            tool_calls_map[idx] = {
                "id": "",
                "type": "function",
                "function": {"name": "", "arguments": ""},
            }
        tc = tool_calls_map[idx]
        if tc_delta.get("id"):
            tc["id"] = tc_delta.get("id", "")
        fn = tc_delta.get("function")
        if fn is not None:
            tc["function"]["name"] += fn.get("name", )
            tc["function"]["arguments"] += fn.get("arguments", "")

    @staticmethod
    def xǁLlmSseHelpersǁmerge_tool_call_delta__mutmut_55(
        tool_calls_map: dict[int, AccumulatedToolCall],
        tc_delta: ToolCallDelta,
    ) -> None:
        """Accumulate one streaming tool_call delta into the index-keyed map."""
        idx = tc_delta.get("index", 0)
        if idx not in tool_calls_map:
            tool_calls_map[idx] = {
                "id": "",
                "type": "function",
                "function": {"name": "", "arguments": ""},
            }
        tc = tool_calls_map[idx]
        if tc_delta.get("id"):
            tc["id"] = tc_delta.get("id", "")
        fn = tc_delta.get("function")
        if fn is not None:
            tc["function"]["name"] += fn.get("XXnameXX", "")
            tc["function"]["arguments"] += fn.get("arguments", "")

    @staticmethod
    def xǁLlmSseHelpersǁmerge_tool_call_delta__mutmut_56(
        tool_calls_map: dict[int, AccumulatedToolCall],
        tc_delta: ToolCallDelta,
    ) -> None:
        """Accumulate one streaming tool_call delta into the index-keyed map."""
        idx = tc_delta.get("index", 0)
        if idx not in tool_calls_map:
            tool_calls_map[idx] = {
                "id": "",
                "type": "function",
                "function": {"name": "", "arguments": ""},
            }
        tc = tool_calls_map[idx]
        if tc_delta.get("id"):
            tc["id"] = tc_delta.get("id", "")
        fn = tc_delta.get("function")
        if fn is not None:
            tc["function"]["name"] += fn.get("NAME", "")
            tc["function"]["arguments"] += fn.get("arguments", "")

    @staticmethod
    def xǁLlmSseHelpersǁmerge_tool_call_delta__mutmut_57(
        tool_calls_map: dict[int, AccumulatedToolCall],
        tc_delta: ToolCallDelta,
    ) -> None:
        """Accumulate one streaming tool_call delta into the index-keyed map."""
        idx = tc_delta.get("index", 0)
        if idx not in tool_calls_map:
            tool_calls_map[idx] = {
                "id": "",
                "type": "function",
                "function": {"name": "", "arguments": ""},
            }
        tc = tool_calls_map[idx]
        if tc_delta.get("id"):
            tc["id"] = tc_delta.get("id", "")
        fn = tc_delta.get("function")
        if fn is not None:
            tc["function"]["name"] += fn.get("name", "XXXX")
            tc["function"]["arguments"] += fn.get("arguments", "")

    @staticmethod
    def xǁLlmSseHelpersǁmerge_tool_call_delta__mutmut_58(
        tool_calls_map: dict[int, AccumulatedToolCall],
        tc_delta: ToolCallDelta,
    ) -> None:
        """Accumulate one streaming tool_call delta into the index-keyed map."""
        idx = tc_delta.get("index", 0)
        if idx not in tool_calls_map:
            tool_calls_map[idx] = {
                "id": "",
                "type": "function",
                "function": {"name": "", "arguments": ""},
            }
        tc = tool_calls_map[idx]
        if tc_delta.get("id"):
            tc["id"] = tc_delta.get("id", "")
        fn = tc_delta.get("function")
        if fn is not None:
            tc["function"]["name"] += fn.get("name", "")
            tc["function"]["arguments"] = fn.get("arguments", "")

    @staticmethod
    def xǁLlmSseHelpersǁmerge_tool_call_delta__mutmut_59(
        tool_calls_map: dict[int, AccumulatedToolCall],
        tc_delta: ToolCallDelta,
    ) -> None:
        """Accumulate one streaming tool_call delta into the index-keyed map."""
        idx = tc_delta.get("index", 0)
        if idx not in tool_calls_map:
            tool_calls_map[idx] = {
                "id": "",
                "type": "function",
                "function": {"name": "", "arguments": ""},
            }
        tc = tool_calls_map[idx]
        if tc_delta.get("id"):
            tc["id"] = tc_delta.get("id", "")
        fn = tc_delta.get("function")
        if fn is not None:
            tc["function"]["name"] += fn.get("name", "")
            tc["function"]["arguments"] -= fn.get("arguments", "")

    @staticmethod
    def xǁLlmSseHelpersǁmerge_tool_call_delta__mutmut_60(
        tool_calls_map: dict[int, AccumulatedToolCall],
        tc_delta: ToolCallDelta,
    ) -> None:
        """Accumulate one streaming tool_call delta into the index-keyed map."""
        idx = tc_delta.get("index", 0)
        if idx not in tool_calls_map:
            tool_calls_map[idx] = {
                "id": "",
                "type": "function",
                "function": {"name": "", "arguments": ""},
            }
        tc = tool_calls_map[idx]
        if tc_delta.get("id"):
            tc["id"] = tc_delta.get("id", "")
        fn = tc_delta.get("function")
        if fn is not None:
            tc["function"]["name"] += fn.get("name", "")
            tc["XXfunctionXX"]["arguments"] += fn.get("arguments", "")

    @staticmethod
    def xǁLlmSseHelpersǁmerge_tool_call_delta__mutmut_61(
        tool_calls_map: dict[int, AccumulatedToolCall],
        tc_delta: ToolCallDelta,
    ) -> None:
        """Accumulate one streaming tool_call delta into the index-keyed map."""
        idx = tc_delta.get("index", 0)
        if idx not in tool_calls_map:
            tool_calls_map[idx] = {
                "id": "",
                "type": "function",
                "function": {"name": "", "arguments": ""},
            }
        tc = tool_calls_map[idx]
        if tc_delta.get("id"):
            tc["id"] = tc_delta.get("id", "")
        fn = tc_delta.get("function")
        if fn is not None:
            tc["function"]["name"] += fn.get("name", "")
            tc["FUNCTION"]["arguments"] += fn.get("arguments", "")

    @staticmethod
    def xǁLlmSseHelpersǁmerge_tool_call_delta__mutmut_62(
        tool_calls_map: dict[int, AccumulatedToolCall],
        tc_delta: ToolCallDelta,
    ) -> None:
        """Accumulate one streaming tool_call delta into the index-keyed map."""
        idx = tc_delta.get("index", 0)
        if idx not in tool_calls_map:
            tool_calls_map[idx] = {
                "id": "",
                "type": "function",
                "function": {"name": "", "arguments": ""},
            }
        tc = tool_calls_map[idx]
        if tc_delta.get("id"):
            tc["id"] = tc_delta.get("id", "")
        fn = tc_delta.get("function")
        if fn is not None:
            tc["function"]["name"] += fn.get("name", "")
            tc["function"]["XXargumentsXX"] += fn.get("arguments", "")

    @staticmethod
    def xǁLlmSseHelpersǁmerge_tool_call_delta__mutmut_63(
        tool_calls_map: dict[int, AccumulatedToolCall],
        tc_delta: ToolCallDelta,
    ) -> None:
        """Accumulate one streaming tool_call delta into the index-keyed map."""
        idx = tc_delta.get("index", 0)
        if idx not in tool_calls_map:
            tool_calls_map[idx] = {
                "id": "",
                "type": "function",
                "function": {"name": "", "arguments": ""},
            }
        tc = tool_calls_map[idx]
        if tc_delta.get("id"):
            tc["id"] = tc_delta.get("id", "")
        fn = tc_delta.get("function")
        if fn is not None:
            tc["function"]["name"] += fn.get("name", "")
            tc["function"]["ARGUMENTS"] += fn.get("arguments", "")

    @staticmethod
    def xǁLlmSseHelpersǁmerge_tool_call_delta__mutmut_64(
        tool_calls_map: dict[int, AccumulatedToolCall],
        tc_delta: ToolCallDelta,
    ) -> None:
        """Accumulate one streaming tool_call delta into the index-keyed map."""
        idx = tc_delta.get("index", 0)
        if idx not in tool_calls_map:
            tool_calls_map[idx] = {
                "id": "",
                "type": "function",
                "function": {"name": "", "arguments": ""},
            }
        tc = tool_calls_map[idx]
        if tc_delta.get("id"):
            tc["id"] = tc_delta.get("id", "")
        fn = tc_delta.get("function")
        if fn is not None:
            tc["function"]["name"] += fn.get("name", "")
            tc["function"]["arguments"] += fn.get(None, "")

    @staticmethod
    def xǁLlmSseHelpersǁmerge_tool_call_delta__mutmut_65(
        tool_calls_map: dict[int, AccumulatedToolCall],
        tc_delta: ToolCallDelta,
    ) -> None:
        """Accumulate one streaming tool_call delta into the index-keyed map."""
        idx = tc_delta.get("index", 0)
        if idx not in tool_calls_map:
            tool_calls_map[idx] = {
                "id": "",
                "type": "function",
                "function": {"name": "", "arguments": ""},
            }
        tc = tool_calls_map[idx]
        if tc_delta.get("id"):
            tc["id"] = tc_delta.get("id", "")
        fn = tc_delta.get("function")
        if fn is not None:
            tc["function"]["name"] += fn.get("name", "")
            tc["function"]["arguments"] += fn.get("arguments", None)

    @staticmethod
    def xǁLlmSseHelpersǁmerge_tool_call_delta__mutmut_66(
        tool_calls_map: dict[int, AccumulatedToolCall],
        tc_delta: ToolCallDelta,
    ) -> None:
        """Accumulate one streaming tool_call delta into the index-keyed map."""
        idx = tc_delta.get("index", 0)
        if idx not in tool_calls_map:
            tool_calls_map[idx] = {
                "id": "",
                "type": "function",
                "function": {"name": "", "arguments": ""},
            }
        tc = tool_calls_map[idx]
        if tc_delta.get("id"):
            tc["id"] = tc_delta.get("id", "")
        fn = tc_delta.get("function")
        if fn is not None:
            tc["function"]["name"] += fn.get("name", "")
            tc["function"]["arguments"] += fn.get("")

    @staticmethod
    def xǁLlmSseHelpersǁmerge_tool_call_delta__mutmut_67(
        tool_calls_map: dict[int, AccumulatedToolCall],
        tc_delta: ToolCallDelta,
    ) -> None:
        """Accumulate one streaming tool_call delta into the index-keyed map."""
        idx = tc_delta.get("index", 0)
        if idx not in tool_calls_map:
            tool_calls_map[idx] = {
                "id": "",
                "type": "function",
                "function": {"name": "", "arguments": ""},
            }
        tc = tool_calls_map[idx]
        if tc_delta.get("id"):
            tc["id"] = tc_delta.get("id", "")
        fn = tc_delta.get("function")
        if fn is not None:
            tc["function"]["name"] += fn.get("name", "")
            tc["function"]["arguments"] += fn.get("arguments", )

    @staticmethod
    def xǁLlmSseHelpersǁmerge_tool_call_delta__mutmut_68(
        tool_calls_map: dict[int, AccumulatedToolCall],
        tc_delta: ToolCallDelta,
    ) -> None:
        """Accumulate one streaming tool_call delta into the index-keyed map."""
        idx = tc_delta.get("index", 0)
        if idx not in tool_calls_map:
            tool_calls_map[idx] = {
                "id": "",
                "type": "function",
                "function": {"name": "", "arguments": ""},
            }
        tc = tool_calls_map[idx]
        if tc_delta.get("id"):
            tc["id"] = tc_delta.get("id", "")
        fn = tc_delta.get("function")
        if fn is not None:
            tc["function"]["name"] += fn.get("name", "")
            tc["function"]["arguments"] += fn.get("XXargumentsXX", "")

    @staticmethod
    def xǁLlmSseHelpersǁmerge_tool_call_delta__mutmut_69(
        tool_calls_map: dict[int, AccumulatedToolCall],
        tc_delta: ToolCallDelta,
    ) -> None:
        """Accumulate one streaming tool_call delta into the index-keyed map."""
        idx = tc_delta.get("index", 0)
        if idx not in tool_calls_map:
            tool_calls_map[idx] = {
                "id": "",
                "type": "function",
                "function": {"name": "", "arguments": ""},
            }
        tc = tool_calls_map[idx]
        if tc_delta.get("id"):
            tc["id"] = tc_delta.get("id", "")
        fn = tc_delta.get("function")
        if fn is not None:
            tc["function"]["name"] += fn.get("name", "")
            tc["function"]["arguments"] += fn.get("ARGUMENTS", "")

    @staticmethod
    def xǁLlmSseHelpersǁmerge_tool_call_delta__mutmut_70(
        tool_calls_map: dict[int, AccumulatedToolCall],
        tc_delta: ToolCallDelta,
    ) -> None:
        """Accumulate one streaming tool_call delta into the index-keyed map."""
        idx = tc_delta.get("index", 0)
        if idx not in tool_calls_map:
            tool_calls_map[idx] = {
                "id": "",
                "type": "function",
                "function": {"name": "", "arguments": ""},
            }
        tc = tool_calls_map[idx]
        if tc_delta.get("id"):
            tc["id"] = tc_delta.get("id", "")
        fn = tc_delta.get("function")
        if fn is not None:
            tc["function"]["name"] += fn.get("name", "")
            tc["function"]["arguments"] += fn.get("arguments", "XXXX")

    @staticmethod
    @_mutmut_mutated(mutants_xǁLlmSseHelpersǁbuild_stream_response__mutmut)
    def build_stream_response(
        content_parts: list[str],
        tool_calls_map: dict[int, AccumulatedToolCall],
        finish_reason: str | None,
    ) -> dict[str, Any]:
        """Assemble the final response dict from streamed content and tool_call deltas."""
        content = "".join(content_parts)
        tool_calls = (
            [tool_calls_map[i] for i in sorted(tool_calls_map)]
            if tool_calls_map
            else None
        )
        message: dict[str, Any] = {"role": "assistant", "content": content}
        if tool_calls:
            message["tool_calls"] = tool_calls
        return {"choices": [{"message": message, "finish_reason": finish_reason}]}

    @staticmethod
    def xǁLlmSseHelpersǁbuild_stream_response__mutmut_orig(
        content_parts: list[str],
        tool_calls_map: dict[int, AccumulatedToolCall],
        finish_reason: str | None,
    ) -> dict[str, Any]:
        """Assemble the final response dict from streamed content and tool_call deltas."""
        content = "".join(content_parts)
        tool_calls = (
            [tool_calls_map[i] for i in sorted(tool_calls_map)]
            if tool_calls_map
            else None
        )
        message: dict[str, Any] = {"role": "assistant", "content": content}
        if tool_calls:
            message["tool_calls"] = tool_calls
        return {"choices": [{"message": message, "finish_reason": finish_reason}]}

    @staticmethod
    def xǁLlmSseHelpersǁbuild_stream_response__mutmut_1(
        content_parts: list[str],
        tool_calls_map: dict[int, AccumulatedToolCall],
        finish_reason: str | None,
    ) -> dict[str, Any]:
        """Assemble the final response dict from streamed content and tool_call deltas."""
        content = None
        tool_calls = (
            [tool_calls_map[i] for i in sorted(tool_calls_map)]
            if tool_calls_map
            else None
        )
        message: dict[str, Any] = {"role": "assistant", "content": content}
        if tool_calls:
            message["tool_calls"] = tool_calls
        return {"choices": [{"message": message, "finish_reason": finish_reason}]}

    @staticmethod
    def xǁLlmSseHelpersǁbuild_stream_response__mutmut_2(
        content_parts: list[str],
        tool_calls_map: dict[int, AccumulatedToolCall],
        finish_reason: str | None,
    ) -> dict[str, Any]:
        """Assemble the final response dict from streamed content and tool_call deltas."""
        content = "".join(None)
        tool_calls = (
            [tool_calls_map[i] for i in sorted(tool_calls_map)]
            if tool_calls_map
            else None
        )
        message: dict[str, Any] = {"role": "assistant", "content": content}
        if tool_calls:
            message["tool_calls"] = tool_calls
        return {"choices": [{"message": message, "finish_reason": finish_reason}]}

    @staticmethod
    def xǁLlmSseHelpersǁbuild_stream_response__mutmut_3(
        content_parts: list[str],
        tool_calls_map: dict[int, AccumulatedToolCall],
        finish_reason: str | None,
    ) -> dict[str, Any]:
        """Assemble the final response dict from streamed content and tool_call deltas."""
        content = "XXXX".join(content_parts)
        tool_calls = (
            [tool_calls_map[i] for i in sorted(tool_calls_map)]
            if tool_calls_map
            else None
        )
        message: dict[str, Any] = {"role": "assistant", "content": content}
        if tool_calls:
            message["tool_calls"] = tool_calls
        return {"choices": [{"message": message, "finish_reason": finish_reason}]}

    @staticmethod
    def xǁLlmSseHelpersǁbuild_stream_response__mutmut_4(
        content_parts: list[str],
        tool_calls_map: dict[int, AccumulatedToolCall],
        finish_reason: str | None,
    ) -> dict[str, Any]:
        """Assemble the final response dict from streamed content and tool_call deltas."""
        content = "".join(content_parts)
        tool_calls = None
        message: dict[str, Any] = {"role": "assistant", "content": content}
        if tool_calls:
            message["tool_calls"] = tool_calls
        return {"choices": [{"message": message, "finish_reason": finish_reason}]}

    @staticmethod
    def xǁLlmSseHelpersǁbuild_stream_response__mutmut_5(
        content_parts: list[str],
        tool_calls_map: dict[int, AccumulatedToolCall],
        finish_reason: str | None,
    ) -> dict[str, Any]:
        """Assemble the final response dict from streamed content and tool_call deltas."""
        content = "".join(content_parts)
        tool_calls = (
            [tool_calls_map[i] for i in sorted(None)]
            if tool_calls_map
            else None
        )
        message: dict[str, Any] = {"role": "assistant", "content": content}
        if tool_calls:
            message["tool_calls"] = tool_calls
        return {"choices": [{"message": message, "finish_reason": finish_reason}]}

    @staticmethod
    def xǁLlmSseHelpersǁbuild_stream_response__mutmut_6(
        content_parts: list[str],
        tool_calls_map: dict[int, AccumulatedToolCall],
        finish_reason: str | None,
    ) -> dict[str, Any]:
        """Assemble the final response dict from streamed content and tool_call deltas."""
        content = "".join(content_parts)
        tool_calls = (
            [tool_calls_map[i] for i in sorted(tool_calls_map)]
            if tool_calls_map
            else None
        )
        message: dict[str, Any] = None
        if tool_calls:
            message["tool_calls"] = tool_calls
        return {"choices": [{"message": message, "finish_reason": finish_reason}]}

    @staticmethod
    def xǁLlmSseHelpersǁbuild_stream_response__mutmut_7(
        content_parts: list[str],
        tool_calls_map: dict[int, AccumulatedToolCall],
        finish_reason: str | None,
    ) -> dict[str, Any]:
        """Assemble the final response dict from streamed content and tool_call deltas."""
        content = "".join(content_parts)
        tool_calls = (
            [tool_calls_map[i] for i in sorted(tool_calls_map)]
            if tool_calls_map
            else None
        )
        message: dict[str, Any] = {"XXroleXX": "assistant", "content": content}
        if tool_calls:
            message["tool_calls"] = tool_calls
        return {"choices": [{"message": message, "finish_reason": finish_reason}]}

    @staticmethod
    def xǁLlmSseHelpersǁbuild_stream_response__mutmut_8(
        content_parts: list[str],
        tool_calls_map: dict[int, AccumulatedToolCall],
        finish_reason: str | None,
    ) -> dict[str, Any]:
        """Assemble the final response dict from streamed content and tool_call deltas."""
        content = "".join(content_parts)
        tool_calls = (
            [tool_calls_map[i] for i in sorted(tool_calls_map)]
            if tool_calls_map
            else None
        )
        message: dict[str, Any] = {"ROLE": "assistant", "content": content}
        if tool_calls:
            message["tool_calls"] = tool_calls
        return {"choices": [{"message": message, "finish_reason": finish_reason}]}

    @staticmethod
    def xǁLlmSseHelpersǁbuild_stream_response__mutmut_9(
        content_parts: list[str],
        tool_calls_map: dict[int, AccumulatedToolCall],
        finish_reason: str | None,
    ) -> dict[str, Any]:
        """Assemble the final response dict from streamed content and tool_call deltas."""
        content = "".join(content_parts)
        tool_calls = (
            [tool_calls_map[i] for i in sorted(tool_calls_map)]
            if tool_calls_map
            else None
        )
        message: dict[str, Any] = {"role": "XXassistantXX", "content": content}
        if tool_calls:
            message["tool_calls"] = tool_calls
        return {"choices": [{"message": message, "finish_reason": finish_reason}]}

    @staticmethod
    def xǁLlmSseHelpersǁbuild_stream_response__mutmut_10(
        content_parts: list[str],
        tool_calls_map: dict[int, AccumulatedToolCall],
        finish_reason: str | None,
    ) -> dict[str, Any]:
        """Assemble the final response dict from streamed content and tool_call deltas."""
        content = "".join(content_parts)
        tool_calls = (
            [tool_calls_map[i] for i in sorted(tool_calls_map)]
            if tool_calls_map
            else None
        )
        message: dict[str, Any] = {"role": "ASSISTANT", "content": content}
        if tool_calls:
            message["tool_calls"] = tool_calls
        return {"choices": [{"message": message, "finish_reason": finish_reason}]}

    @staticmethod
    def xǁLlmSseHelpersǁbuild_stream_response__mutmut_11(
        content_parts: list[str],
        tool_calls_map: dict[int, AccumulatedToolCall],
        finish_reason: str | None,
    ) -> dict[str, Any]:
        """Assemble the final response dict from streamed content and tool_call deltas."""
        content = "".join(content_parts)
        tool_calls = (
            [tool_calls_map[i] for i in sorted(tool_calls_map)]
            if tool_calls_map
            else None
        )
        message: dict[str, Any] = {"role": "assistant", "XXcontentXX": content}
        if tool_calls:
            message["tool_calls"] = tool_calls
        return {"choices": [{"message": message, "finish_reason": finish_reason}]}

    @staticmethod
    def xǁLlmSseHelpersǁbuild_stream_response__mutmut_12(
        content_parts: list[str],
        tool_calls_map: dict[int, AccumulatedToolCall],
        finish_reason: str | None,
    ) -> dict[str, Any]:
        """Assemble the final response dict from streamed content and tool_call deltas."""
        content = "".join(content_parts)
        tool_calls = (
            [tool_calls_map[i] for i in sorted(tool_calls_map)]
            if tool_calls_map
            else None
        )
        message: dict[str, Any] = {"role": "assistant", "CONTENT": content}
        if tool_calls:
            message["tool_calls"] = tool_calls
        return {"choices": [{"message": message, "finish_reason": finish_reason}]}

    @staticmethod
    def xǁLlmSseHelpersǁbuild_stream_response__mutmut_13(
        content_parts: list[str],
        tool_calls_map: dict[int, AccumulatedToolCall],
        finish_reason: str | None,
    ) -> dict[str, Any]:
        """Assemble the final response dict from streamed content and tool_call deltas."""
        content = "".join(content_parts)
        tool_calls = (
            [tool_calls_map[i] for i in sorted(tool_calls_map)]
            if tool_calls_map
            else None
        )
        message: dict[str, Any] = {"role": "assistant", "content": content}
        if tool_calls:
            message["tool_calls"] = None
        return {"choices": [{"message": message, "finish_reason": finish_reason}]}

    @staticmethod
    def xǁLlmSseHelpersǁbuild_stream_response__mutmut_14(
        content_parts: list[str],
        tool_calls_map: dict[int, AccumulatedToolCall],
        finish_reason: str | None,
    ) -> dict[str, Any]:
        """Assemble the final response dict from streamed content and tool_call deltas."""
        content = "".join(content_parts)
        tool_calls = (
            [tool_calls_map[i] for i in sorted(tool_calls_map)]
            if tool_calls_map
            else None
        )
        message: dict[str, Any] = {"role": "assistant", "content": content}
        if tool_calls:
            message["XXtool_callsXX"] = tool_calls
        return {"choices": [{"message": message, "finish_reason": finish_reason}]}

    @staticmethod
    def xǁLlmSseHelpersǁbuild_stream_response__mutmut_15(
        content_parts: list[str],
        tool_calls_map: dict[int, AccumulatedToolCall],
        finish_reason: str | None,
    ) -> dict[str, Any]:
        """Assemble the final response dict from streamed content and tool_call deltas."""
        content = "".join(content_parts)
        tool_calls = (
            [tool_calls_map[i] for i in sorted(tool_calls_map)]
            if tool_calls_map
            else None
        )
        message: dict[str, Any] = {"role": "assistant", "content": content}
        if tool_calls:
            message["TOOL_CALLS"] = tool_calls
        return {"choices": [{"message": message, "finish_reason": finish_reason}]}

    @staticmethod
    def xǁLlmSseHelpersǁbuild_stream_response__mutmut_16(
        content_parts: list[str],
        tool_calls_map: dict[int, AccumulatedToolCall],
        finish_reason: str | None,
    ) -> dict[str, Any]:
        """Assemble the final response dict from streamed content and tool_call deltas."""
        content = "".join(content_parts)
        tool_calls = (
            [tool_calls_map[i] for i in sorted(tool_calls_map)]
            if tool_calls_map
            else None
        )
        message: dict[str, Any] = {"role": "assistant", "content": content}
        if tool_calls:
            message["tool_calls"] = tool_calls
        return {"XXchoicesXX": [{"message": message, "finish_reason": finish_reason}]}

    @staticmethod
    def xǁLlmSseHelpersǁbuild_stream_response__mutmut_17(
        content_parts: list[str],
        tool_calls_map: dict[int, AccumulatedToolCall],
        finish_reason: str | None,
    ) -> dict[str, Any]:
        """Assemble the final response dict from streamed content and tool_call deltas."""
        content = "".join(content_parts)
        tool_calls = (
            [tool_calls_map[i] for i in sorted(tool_calls_map)]
            if tool_calls_map
            else None
        )
        message: dict[str, Any] = {"role": "assistant", "content": content}
        if tool_calls:
            message["tool_calls"] = tool_calls
        return {"CHOICES": [{"message": message, "finish_reason": finish_reason}]}

    @staticmethod
    def xǁLlmSseHelpersǁbuild_stream_response__mutmut_18(
        content_parts: list[str],
        tool_calls_map: dict[int, AccumulatedToolCall],
        finish_reason: str | None,
    ) -> dict[str, Any]:
        """Assemble the final response dict from streamed content and tool_call deltas."""
        content = "".join(content_parts)
        tool_calls = (
            [tool_calls_map[i] for i in sorted(tool_calls_map)]
            if tool_calls_map
            else None
        )
        message: dict[str, Any] = {"role": "assistant", "content": content}
        if tool_calls:
            message["tool_calls"] = tool_calls
        return {"choices": [{"XXmessageXX": message, "finish_reason": finish_reason}]}

    @staticmethod
    def xǁLlmSseHelpersǁbuild_stream_response__mutmut_19(
        content_parts: list[str],
        tool_calls_map: dict[int, AccumulatedToolCall],
        finish_reason: str | None,
    ) -> dict[str, Any]:
        """Assemble the final response dict from streamed content and tool_call deltas."""
        content = "".join(content_parts)
        tool_calls = (
            [tool_calls_map[i] for i in sorted(tool_calls_map)]
            if tool_calls_map
            else None
        )
        message: dict[str, Any] = {"role": "assistant", "content": content}
        if tool_calls:
            message["tool_calls"] = tool_calls
        return {"choices": [{"MESSAGE": message, "finish_reason": finish_reason}]}

    @staticmethod
    def xǁLlmSseHelpersǁbuild_stream_response__mutmut_20(
        content_parts: list[str],
        tool_calls_map: dict[int, AccumulatedToolCall],
        finish_reason: str | None,
    ) -> dict[str, Any]:
        """Assemble the final response dict from streamed content and tool_call deltas."""
        content = "".join(content_parts)
        tool_calls = (
            [tool_calls_map[i] for i in sorted(tool_calls_map)]
            if tool_calls_map
            else None
        )
        message: dict[str, Any] = {"role": "assistant", "content": content}
        if tool_calls:
            message["tool_calls"] = tool_calls
        return {"choices": [{"message": message, "XXfinish_reasonXX": finish_reason}]}

    @staticmethod
    def xǁLlmSseHelpersǁbuild_stream_response__mutmut_21(
        content_parts: list[str],
        tool_calls_map: dict[int, AccumulatedToolCall],
        finish_reason: str | None,
    ) -> dict[str, Any]:
        """Assemble the final response dict from streamed content and tool_call deltas."""
        content = "".join(content_parts)
        tool_calls = (
            [tool_calls_map[i] for i in sorted(tool_calls_map)]
            if tool_calls_map
            else None
        )
        message: dict[str, Any] = {"role": "assistant", "content": content}
        if tool_calls:
            message["tool_calls"] = tool_calls
        return {"choices": [{"message": message, "FINISH_REASON": finish_reason}]}

    @staticmethod
    @_mutmut_mutated(mutants_xǁLlmSseHelpersǁprocess_sse_chunk__mutmut)
    def process_sse_chunk(
        chunk: Mapping[str, Any],
        content_parts: list[str],
        tool_calls_map: dict[int, AccumulatedToolCall],
        on_token: Callable[[str], None] | None = None,
    ) -> str | None:
        """Process one parsed SSE chunk delta; return finish_reason or None."""
        choices = chunk.get("choices")
        if not choices:
            return None
        choice = choices[0]
        delta = choice.get("delta", {})
        finish_reason: str | None = choice.get("finish_reason") or None
        token = delta.get("content") or ""
        if token:
            content_parts.append(token)
            if on_token is not None:
                on_token(token)
        for tc_delta in delta.get("tool_calls", []):
            LlmSseHelpers.merge_tool_call_delta(tool_calls_map, tc_delta)
        return finish_reason

    @staticmethod
    def xǁLlmSseHelpersǁprocess_sse_chunk__mutmut_orig(
        chunk: Mapping[str, Any],
        content_parts: list[str],
        tool_calls_map: dict[int, AccumulatedToolCall],
        on_token: Callable[[str], None] | None = None,
    ) -> str | None:
        """Process one parsed SSE chunk delta; return finish_reason or None."""
        choices = chunk.get("choices")
        if not choices:
            return None
        choice = choices[0]
        delta = choice.get("delta", {})
        finish_reason: str | None = choice.get("finish_reason") or None
        token = delta.get("content") or ""
        if token:
            content_parts.append(token)
            if on_token is not None:
                on_token(token)
        for tc_delta in delta.get("tool_calls", []):
            LlmSseHelpers.merge_tool_call_delta(tool_calls_map, tc_delta)
        return finish_reason

    @staticmethod
    def xǁLlmSseHelpersǁprocess_sse_chunk__mutmut_1(
        chunk: Mapping[str, Any],
        content_parts: list[str],
        tool_calls_map: dict[int, AccumulatedToolCall],
        on_token: Callable[[str], None] | None = None,
    ) -> str | None:
        """Process one parsed SSE chunk delta; return finish_reason or None."""
        choices = None
        if not choices:
            return None
        choice = choices[0]
        delta = choice.get("delta", {})
        finish_reason: str | None = choice.get("finish_reason") or None
        token = delta.get("content") or ""
        if token:
            content_parts.append(token)
            if on_token is not None:
                on_token(token)
        for tc_delta in delta.get("tool_calls", []):
            LlmSseHelpers.merge_tool_call_delta(tool_calls_map, tc_delta)
        return finish_reason

    @staticmethod
    def xǁLlmSseHelpersǁprocess_sse_chunk__mutmut_2(
        chunk: Mapping[str, Any],
        content_parts: list[str],
        tool_calls_map: dict[int, AccumulatedToolCall],
        on_token: Callable[[str], None] | None = None,
    ) -> str | None:
        """Process one parsed SSE chunk delta; return finish_reason or None."""
        choices = chunk.get(None)
        if not choices:
            return None
        choice = choices[0]
        delta = choice.get("delta", {})
        finish_reason: str | None = choice.get("finish_reason") or None
        token = delta.get("content") or ""
        if token:
            content_parts.append(token)
            if on_token is not None:
                on_token(token)
        for tc_delta in delta.get("tool_calls", []):
            LlmSseHelpers.merge_tool_call_delta(tool_calls_map, tc_delta)
        return finish_reason

    @staticmethod
    def xǁLlmSseHelpersǁprocess_sse_chunk__mutmut_3(
        chunk: Mapping[str, Any],
        content_parts: list[str],
        tool_calls_map: dict[int, AccumulatedToolCall],
        on_token: Callable[[str], None] | None = None,
    ) -> str | None:
        """Process one parsed SSE chunk delta; return finish_reason or None."""
        choices = chunk.get("XXchoicesXX")
        if not choices:
            return None
        choice = choices[0]
        delta = choice.get("delta", {})
        finish_reason: str | None = choice.get("finish_reason") or None
        token = delta.get("content") or ""
        if token:
            content_parts.append(token)
            if on_token is not None:
                on_token(token)
        for tc_delta in delta.get("tool_calls", []):
            LlmSseHelpers.merge_tool_call_delta(tool_calls_map, tc_delta)
        return finish_reason

    @staticmethod
    def xǁLlmSseHelpersǁprocess_sse_chunk__mutmut_4(
        chunk: Mapping[str, Any],
        content_parts: list[str],
        tool_calls_map: dict[int, AccumulatedToolCall],
        on_token: Callable[[str], None] | None = None,
    ) -> str | None:
        """Process one parsed SSE chunk delta; return finish_reason or None."""
        choices = chunk.get("CHOICES")
        if not choices:
            return None
        choice = choices[0]
        delta = choice.get("delta", {})
        finish_reason: str | None = choice.get("finish_reason") or None
        token = delta.get("content") or ""
        if token:
            content_parts.append(token)
            if on_token is not None:
                on_token(token)
        for tc_delta in delta.get("tool_calls", []):
            LlmSseHelpers.merge_tool_call_delta(tool_calls_map, tc_delta)
        return finish_reason

    @staticmethod
    def xǁLlmSseHelpersǁprocess_sse_chunk__mutmut_5(
        chunk: Mapping[str, Any],
        content_parts: list[str],
        tool_calls_map: dict[int, AccumulatedToolCall],
        on_token: Callable[[str], None] | None = None,
    ) -> str | None:
        """Process one parsed SSE chunk delta; return finish_reason or None."""
        choices = chunk.get("choices")
        if choices:
            return None
        choice = choices[0]
        delta = choice.get("delta", {})
        finish_reason: str | None = choice.get("finish_reason") or None
        token = delta.get("content") or ""
        if token:
            content_parts.append(token)
            if on_token is not None:
                on_token(token)
        for tc_delta in delta.get("tool_calls", []):
            LlmSseHelpers.merge_tool_call_delta(tool_calls_map, tc_delta)
        return finish_reason

    @staticmethod
    def xǁLlmSseHelpersǁprocess_sse_chunk__mutmut_6(
        chunk: Mapping[str, Any],
        content_parts: list[str],
        tool_calls_map: dict[int, AccumulatedToolCall],
        on_token: Callable[[str], None] | None = None,
    ) -> str | None:
        """Process one parsed SSE chunk delta; return finish_reason or None."""
        choices = chunk.get("choices")
        if not choices:
            return None
        choice = None
        delta = choice.get("delta", {})
        finish_reason: str | None = choice.get("finish_reason") or None
        token = delta.get("content") or ""
        if token:
            content_parts.append(token)
            if on_token is not None:
                on_token(token)
        for tc_delta in delta.get("tool_calls", []):
            LlmSseHelpers.merge_tool_call_delta(tool_calls_map, tc_delta)
        return finish_reason

    @staticmethod
    def xǁLlmSseHelpersǁprocess_sse_chunk__mutmut_7(
        chunk: Mapping[str, Any],
        content_parts: list[str],
        tool_calls_map: dict[int, AccumulatedToolCall],
        on_token: Callable[[str], None] | None = None,
    ) -> str | None:
        """Process one parsed SSE chunk delta; return finish_reason or None."""
        choices = chunk.get("choices")
        if not choices:
            return None
        choice = choices[1]
        delta = choice.get("delta", {})
        finish_reason: str | None = choice.get("finish_reason") or None
        token = delta.get("content") or ""
        if token:
            content_parts.append(token)
            if on_token is not None:
                on_token(token)
        for tc_delta in delta.get("tool_calls", []):
            LlmSseHelpers.merge_tool_call_delta(tool_calls_map, tc_delta)
        return finish_reason

    @staticmethod
    def xǁLlmSseHelpersǁprocess_sse_chunk__mutmut_8(
        chunk: Mapping[str, Any],
        content_parts: list[str],
        tool_calls_map: dict[int, AccumulatedToolCall],
        on_token: Callable[[str], None] | None = None,
    ) -> str | None:
        """Process one parsed SSE chunk delta; return finish_reason or None."""
        choices = chunk.get("choices")
        if not choices:
            return None
        choice = choices[0]
        delta = None
        finish_reason: str | None = choice.get("finish_reason") or None
        token = delta.get("content") or ""
        if token:
            content_parts.append(token)
            if on_token is not None:
                on_token(token)
        for tc_delta in delta.get("tool_calls", []):
            LlmSseHelpers.merge_tool_call_delta(tool_calls_map, tc_delta)
        return finish_reason

    @staticmethod
    def xǁLlmSseHelpersǁprocess_sse_chunk__mutmut_9(
        chunk: Mapping[str, Any],
        content_parts: list[str],
        tool_calls_map: dict[int, AccumulatedToolCall],
        on_token: Callable[[str], None] | None = None,
    ) -> str | None:
        """Process one parsed SSE chunk delta; return finish_reason or None."""
        choices = chunk.get("choices")
        if not choices:
            return None
        choice = choices[0]
        delta = choice.get(None, {})
        finish_reason: str | None = choice.get("finish_reason") or None
        token = delta.get("content") or ""
        if token:
            content_parts.append(token)
            if on_token is not None:
                on_token(token)
        for tc_delta in delta.get("tool_calls", []):
            LlmSseHelpers.merge_tool_call_delta(tool_calls_map, tc_delta)
        return finish_reason

    @staticmethod
    def xǁLlmSseHelpersǁprocess_sse_chunk__mutmut_10(
        chunk: Mapping[str, Any],
        content_parts: list[str],
        tool_calls_map: dict[int, AccumulatedToolCall],
        on_token: Callable[[str], None] | None = None,
    ) -> str | None:
        """Process one parsed SSE chunk delta; return finish_reason or None."""
        choices = chunk.get("choices")
        if not choices:
            return None
        choice = choices[0]
        delta = choice.get("delta", None)
        finish_reason: str | None = choice.get("finish_reason") or None
        token = delta.get("content") or ""
        if token:
            content_parts.append(token)
            if on_token is not None:
                on_token(token)
        for tc_delta in delta.get("tool_calls", []):
            LlmSseHelpers.merge_tool_call_delta(tool_calls_map, tc_delta)
        return finish_reason

    @staticmethod
    def xǁLlmSseHelpersǁprocess_sse_chunk__mutmut_11(
        chunk: Mapping[str, Any],
        content_parts: list[str],
        tool_calls_map: dict[int, AccumulatedToolCall],
        on_token: Callable[[str], None] | None = None,
    ) -> str | None:
        """Process one parsed SSE chunk delta; return finish_reason or None."""
        choices = chunk.get("choices")
        if not choices:
            return None
        choice = choices[0]
        delta = choice.get({})
        finish_reason: str | None = choice.get("finish_reason") or None
        token = delta.get("content") or ""
        if token:
            content_parts.append(token)
            if on_token is not None:
                on_token(token)
        for tc_delta in delta.get("tool_calls", []):
            LlmSseHelpers.merge_tool_call_delta(tool_calls_map, tc_delta)
        return finish_reason

    @staticmethod
    def xǁLlmSseHelpersǁprocess_sse_chunk__mutmut_12(
        chunk: Mapping[str, Any],
        content_parts: list[str],
        tool_calls_map: dict[int, AccumulatedToolCall],
        on_token: Callable[[str], None] | None = None,
    ) -> str | None:
        """Process one parsed SSE chunk delta; return finish_reason or None."""
        choices = chunk.get("choices")
        if not choices:
            return None
        choice = choices[0]
        delta = choice.get("delta", )
        finish_reason: str | None = choice.get("finish_reason") or None
        token = delta.get("content") or ""
        if token:
            content_parts.append(token)
            if on_token is not None:
                on_token(token)
        for tc_delta in delta.get("tool_calls", []):
            LlmSseHelpers.merge_tool_call_delta(tool_calls_map, tc_delta)
        return finish_reason

    @staticmethod
    def xǁLlmSseHelpersǁprocess_sse_chunk__mutmut_13(
        chunk: Mapping[str, Any],
        content_parts: list[str],
        tool_calls_map: dict[int, AccumulatedToolCall],
        on_token: Callable[[str], None] | None = None,
    ) -> str | None:
        """Process one parsed SSE chunk delta; return finish_reason or None."""
        choices = chunk.get("choices")
        if not choices:
            return None
        choice = choices[0]
        delta = choice.get("XXdeltaXX", {})
        finish_reason: str | None = choice.get("finish_reason") or None
        token = delta.get("content") or ""
        if token:
            content_parts.append(token)
            if on_token is not None:
                on_token(token)
        for tc_delta in delta.get("tool_calls", []):
            LlmSseHelpers.merge_tool_call_delta(tool_calls_map, tc_delta)
        return finish_reason

    @staticmethod
    def xǁLlmSseHelpersǁprocess_sse_chunk__mutmut_14(
        chunk: Mapping[str, Any],
        content_parts: list[str],
        tool_calls_map: dict[int, AccumulatedToolCall],
        on_token: Callable[[str], None] | None = None,
    ) -> str | None:
        """Process one parsed SSE chunk delta; return finish_reason or None."""
        choices = chunk.get("choices")
        if not choices:
            return None
        choice = choices[0]
        delta = choice.get("DELTA", {})
        finish_reason: str | None = choice.get("finish_reason") or None
        token = delta.get("content") or ""
        if token:
            content_parts.append(token)
            if on_token is not None:
                on_token(token)
        for tc_delta in delta.get("tool_calls", []):
            LlmSseHelpers.merge_tool_call_delta(tool_calls_map, tc_delta)
        return finish_reason

    @staticmethod
    def xǁLlmSseHelpersǁprocess_sse_chunk__mutmut_15(
        chunk: Mapping[str, Any],
        content_parts: list[str],
        tool_calls_map: dict[int, AccumulatedToolCall],
        on_token: Callable[[str], None] | None = None,
    ) -> str | None:
        """Process one parsed SSE chunk delta; return finish_reason or None."""
        choices = chunk.get("choices")
        if not choices:
            return None
        choice = choices[0]
        delta = choice.get("delta", {})
        finish_reason: str | None = None
        token = delta.get("content") or ""
        if token:
            content_parts.append(token)
            if on_token is not None:
                on_token(token)
        for tc_delta in delta.get("tool_calls", []):
            LlmSseHelpers.merge_tool_call_delta(tool_calls_map, tc_delta)
        return finish_reason

    @staticmethod
    def xǁLlmSseHelpersǁprocess_sse_chunk__mutmut_16(
        chunk: Mapping[str, Any],
        content_parts: list[str],
        tool_calls_map: dict[int, AccumulatedToolCall],
        on_token: Callable[[str], None] | None = None,
    ) -> str | None:
        """Process one parsed SSE chunk delta; return finish_reason or None."""
        choices = chunk.get("choices")
        if not choices:
            return None
        choice = choices[0]
        delta = choice.get("delta", {})
        finish_reason: str | None = choice.get("finish_reason") and None
        token = delta.get("content") or ""
        if token:
            content_parts.append(token)
            if on_token is not None:
                on_token(token)
        for tc_delta in delta.get("tool_calls", []):
            LlmSseHelpers.merge_tool_call_delta(tool_calls_map, tc_delta)
        return finish_reason

    @staticmethod
    def xǁLlmSseHelpersǁprocess_sse_chunk__mutmut_17(
        chunk: Mapping[str, Any],
        content_parts: list[str],
        tool_calls_map: dict[int, AccumulatedToolCall],
        on_token: Callable[[str], None] | None = None,
    ) -> str | None:
        """Process one parsed SSE chunk delta; return finish_reason or None."""
        choices = chunk.get("choices")
        if not choices:
            return None
        choice = choices[0]
        delta = choice.get("delta", {})
        finish_reason: str | None = choice.get(None) or None
        token = delta.get("content") or ""
        if token:
            content_parts.append(token)
            if on_token is not None:
                on_token(token)
        for tc_delta in delta.get("tool_calls", []):
            LlmSseHelpers.merge_tool_call_delta(tool_calls_map, tc_delta)
        return finish_reason

    @staticmethod
    def xǁLlmSseHelpersǁprocess_sse_chunk__mutmut_18(
        chunk: Mapping[str, Any],
        content_parts: list[str],
        tool_calls_map: dict[int, AccumulatedToolCall],
        on_token: Callable[[str], None] | None = None,
    ) -> str | None:
        """Process one parsed SSE chunk delta; return finish_reason or None."""
        choices = chunk.get("choices")
        if not choices:
            return None
        choice = choices[0]
        delta = choice.get("delta", {})
        finish_reason: str | None = choice.get("XXfinish_reasonXX") or None
        token = delta.get("content") or ""
        if token:
            content_parts.append(token)
            if on_token is not None:
                on_token(token)
        for tc_delta in delta.get("tool_calls", []):
            LlmSseHelpers.merge_tool_call_delta(tool_calls_map, tc_delta)
        return finish_reason

    @staticmethod
    def xǁLlmSseHelpersǁprocess_sse_chunk__mutmut_19(
        chunk: Mapping[str, Any],
        content_parts: list[str],
        tool_calls_map: dict[int, AccumulatedToolCall],
        on_token: Callable[[str], None] | None = None,
    ) -> str | None:
        """Process one parsed SSE chunk delta; return finish_reason or None."""
        choices = chunk.get("choices")
        if not choices:
            return None
        choice = choices[0]
        delta = choice.get("delta", {})
        finish_reason: str | None = choice.get("FINISH_REASON") or None
        token = delta.get("content") or ""
        if token:
            content_parts.append(token)
            if on_token is not None:
                on_token(token)
        for tc_delta in delta.get("tool_calls", []):
            LlmSseHelpers.merge_tool_call_delta(tool_calls_map, tc_delta)
        return finish_reason

    @staticmethod
    def xǁLlmSseHelpersǁprocess_sse_chunk__mutmut_20(
        chunk: Mapping[str, Any],
        content_parts: list[str],
        tool_calls_map: dict[int, AccumulatedToolCall],
        on_token: Callable[[str], None] | None = None,
    ) -> str | None:
        """Process one parsed SSE chunk delta; return finish_reason or None."""
        choices = chunk.get("choices")
        if not choices:
            return None
        choice = choices[0]
        delta = choice.get("delta", {})
        finish_reason: str | None = choice.get("finish_reason") or None
        token = None
        if token:
            content_parts.append(token)
            if on_token is not None:
                on_token(token)
        for tc_delta in delta.get("tool_calls", []):
            LlmSseHelpers.merge_tool_call_delta(tool_calls_map, tc_delta)
        return finish_reason

    @staticmethod
    def xǁLlmSseHelpersǁprocess_sse_chunk__mutmut_21(
        chunk: Mapping[str, Any],
        content_parts: list[str],
        tool_calls_map: dict[int, AccumulatedToolCall],
        on_token: Callable[[str], None] | None = None,
    ) -> str | None:
        """Process one parsed SSE chunk delta; return finish_reason or None."""
        choices = chunk.get("choices")
        if not choices:
            return None
        choice = choices[0]
        delta = choice.get("delta", {})
        finish_reason: str | None = choice.get("finish_reason") or None
        token = delta.get("content") and ""
        if token:
            content_parts.append(token)
            if on_token is not None:
                on_token(token)
        for tc_delta in delta.get("tool_calls", []):
            LlmSseHelpers.merge_tool_call_delta(tool_calls_map, tc_delta)
        return finish_reason

    @staticmethod
    def xǁLlmSseHelpersǁprocess_sse_chunk__mutmut_22(
        chunk: Mapping[str, Any],
        content_parts: list[str],
        tool_calls_map: dict[int, AccumulatedToolCall],
        on_token: Callable[[str], None] | None = None,
    ) -> str | None:
        """Process one parsed SSE chunk delta; return finish_reason or None."""
        choices = chunk.get("choices")
        if not choices:
            return None
        choice = choices[0]
        delta = choice.get("delta", {})
        finish_reason: str | None = choice.get("finish_reason") or None
        token = delta.get(None) or ""
        if token:
            content_parts.append(token)
            if on_token is not None:
                on_token(token)
        for tc_delta in delta.get("tool_calls", []):
            LlmSseHelpers.merge_tool_call_delta(tool_calls_map, tc_delta)
        return finish_reason

    @staticmethod
    def xǁLlmSseHelpersǁprocess_sse_chunk__mutmut_23(
        chunk: Mapping[str, Any],
        content_parts: list[str],
        tool_calls_map: dict[int, AccumulatedToolCall],
        on_token: Callable[[str], None] | None = None,
    ) -> str | None:
        """Process one parsed SSE chunk delta; return finish_reason or None."""
        choices = chunk.get("choices")
        if not choices:
            return None
        choice = choices[0]
        delta = choice.get("delta", {})
        finish_reason: str | None = choice.get("finish_reason") or None
        token = delta.get("XXcontentXX") or ""
        if token:
            content_parts.append(token)
            if on_token is not None:
                on_token(token)
        for tc_delta in delta.get("tool_calls", []):
            LlmSseHelpers.merge_tool_call_delta(tool_calls_map, tc_delta)
        return finish_reason

    @staticmethod
    def xǁLlmSseHelpersǁprocess_sse_chunk__mutmut_24(
        chunk: Mapping[str, Any],
        content_parts: list[str],
        tool_calls_map: dict[int, AccumulatedToolCall],
        on_token: Callable[[str], None] | None = None,
    ) -> str | None:
        """Process one parsed SSE chunk delta; return finish_reason or None."""
        choices = chunk.get("choices")
        if not choices:
            return None
        choice = choices[0]
        delta = choice.get("delta", {})
        finish_reason: str | None = choice.get("finish_reason") or None
        token = delta.get("CONTENT") or ""
        if token:
            content_parts.append(token)
            if on_token is not None:
                on_token(token)
        for tc_delta in delta.get("tool_calls", []):
            LlmSseHelpers.merge_tool_call_delta(tool_calls_map, tc_delta)
        return finish_reason

    @staticmethod
    def xǁLlmSseHelpersǁprocess_sse_chunk__mutmut_25(
        chunk: Mapping[str, Any],
        content_parts: list[str],
        tool_calls_map: dict[int, AccumulatedToolCall],
        on_token: Callable[[str], None] | None = None,
    ) -> str | None:
        """Process one parsed SSE chunk delta; return finish_reason or None."""
        choices = chunk.get("choices")
        if not choices:
            return None
        choice = choices[0]
        delta = choice.get("delta", {})
        finish_reason: str | None = choice.get("finish_reason") or None
        token = delta.get("content") or "XXXX"
        if token:
            content_parts.append(token)
            if on_token is not None:
                on_token(token)
        for tc_delta in delta.get("tool_calls", []):
            LlmSseHelpers.merge_tool_call_delta(tool_calls_map, tc_delta)
        return finish_reason

    @staticmethod
    def xǁLlmSseHelpersǁprocess_sse_chunk__mutmut_26(
        chunk: Mapping[str, Any],
        content_parts: list[str],
        tool_calls_map: dict[int, AccumulatedToolCall],
        on_token: Callable[[str], None] | None = None,
    ) -> str | None:
        """Process one parsed SSE chunk delta; return finish_reason or None."""
        choices = chunk.get("choices")
        if not choices:
            return None
        choice = choices[0]
        delta = choice.get("delta", {})
        finish_reason: str | None = choice.get("finish_reason") or None
        token = delta.get("content") or ""
        if token:
            content_parts.append(None)
            if on_token is not None:
                on_token(token)
        for tc_delta in delta.get("tool_calls", []):
            LlmSseHelpers.merge_tool_call_delta(tool_calls_map, tc_delta)
        return finish_reason

    @staticmethod
    def xǁLlmSseHelpersǁprocess_sse_chunk__mutmut_27(
        chunk: Mapping[str, Any],
        content_parts: list[str],
        tool_calls_map: dict[int, AccumulatedToolCall],
        on_token: Callable[[str], None] | None = None,
    ) -> str | None:
        """Process one parsed SSE chunk delta; return finish_reason or None."""
        choices = chunk.get("choices")
        if not choices:
            return None
        choice = choices[0]
        delta = choice.get("delta", {})
        finish_reason: str | None = choice.get("finish_reason") or None
        token = delta.get("content") or ""
        if token:
            content_parts.append(token)
            if on_token is None:
                on_token(token)
        for tc_delta in delta.get("tool_calls", []):
            LlmSseHelpers.merge_tool_call_delta(tool_calls_map, tc_delta)
        return finish_reason

    @staticmethod
    def xǁLlmSseHelpersǁprocess_sse_chunk__mutmut_28(
        chunk: Mapping[str, Any],
        content_parts: list[str],
        tool_calls_map: dict[int, AccumulatedToolCall],
        on_token: Callable[[str], None] | None = None,
    ) -> str | None:
        """Process one parsed SSE chunk delta; return finish_reason or None."""
        choices = chunk.get("choices")
        if not choices:
            return None
        choice = choices[0]
        delta = choice.get("delta", {})
        finish_reason: str | None = choice.get("finish_reason") or None
        token = delta.get("content") or ""
        if token:
            content_parts.append(token)
            if on_token is not None:
                on_token(None)
        for tc_delta in delta.get("tool_calls", []):
            LlmSseHelpers.merge_tool_call_delta(tool_calls_map, tc_delta)
        return finish_reason

    @staticmethod
    def xǁLlmSseHelpersǁprocess_sse_chunk__mutmut_29(
        chunk: Mapping[str, Any],
        content_parts: list[str],
        tool_calls_map: dict[int, AccumulatedToolCall],
        on_token: Callable[[str], None] | None = None,
    ) -> str | None:
        """Process one parsed SSE chunk delta; return finish_reason or None."""
        choices = chunk.get("choices")
        if not choices:
            return None
        choice = choices[0]
        delta = choice.get("delta", {})
        finish_reason: str | None = choice.get("finish_reason") or None
        token = delta.get("content") or ""
        if token:
            content_parts.append(token)
            if on_token is not None:
                on_token(token)
        for tc_delta in delta.get(None, []):
            LlmSseHelpers.merge_tool_call_delta(tool_calls_map, tc_delta)
        return finish_reason

    @staticmethod
    def xǁLlmSseHelpersǁprocess_sse_chunk__mutmut_30(
        chunk: Mapping[str, Any],
        content_parts: list[str],
        tool_calls_map: dict[int, AccumulatedToolCall],
        on_token: Callable[[str], None] | None = None,
    ) -> str | None:
        """Process one parsed SSE chunk delta; return finish_reason or None."""
        choices = chunk.get("choices")
        if not choices:
            return None
        choice = choices[0]
        delta = choice.get("delta", {})
        finish_reason: str | None = choice.get("finish_reason") or None
        token = delta.get("content") or ""
        if token:
            content_parts.append(token)
            if on_token is not None:
                on_token(token)
        for tc_delta in delta.get("tool_calls", None):
            LlmSseHelpers.merge_tool_call_delta(tool_calls_map, tc_delta)
        return finish_reason

    @staticmethod
    def xǁLlmSseHelpersǁprocess_sse_chunk__mutmut_31(
        chunk: Mapping[str, Any],
        content_parts: list[str],
        tool_calls_map: dict[int, AccumulatedToolCall],
        on_token: Callable[[str], None] | None = None,
    ) -> str | None:
        """Process one parsed SSE chunk delta; return finish_reason or None."""
        choices = chunk.get("choices")
        if not choices:
            return None
        choice = choices[0]
        delta = choice.get("delta", {})
        finish_reason: str | None = choice.get("finish_reason") or None
        token = delta.get("content") or ""
        if token:
            content_parts.append(token)
            if on_token is not None:
                on_token(token)
        for tc_delta in delta.get([]):
            LlmSseHelpers.merge_tool_call_delta(tool_calls_map, tc_delta)
        return finish_reason

    @staticmethod
    def xǁLlmSseHelpersǁprocess_sse_chunk__mutmut_32(
        chunk: Mapping[str, Any],
        content_parts: list[str],
        tool_calls_map: dict[int, AccumulatedToolCall],
        on_token: Callable[[str], None] | None = None,
    ) -> str | None:
        """Process one parsed SSE chunk delta; return finish_reason or None."""
        choices = chunk.get("choices")
        if not choices:
            return None
        choice = choices[0]
        delta = choice.get("delta", {})
        finish_reason: str | None = choice.get("finish_reason") or None
        token = delta.get("content") or ""
        if token:
            content_parts.append(token)
            if on_token is not None:
                on_token(token)
        for tc_delta in delta.get("tool_calls", ):
            LlmSseHelpers.merge_tool_call_delta(tool_calls_map, tc_delta)
        return finish_reason

    @staticmethod
    def xǁLlmSseHelpersǁprocess_sse_chunk__mutmut_33(
        chunk: Mapping[str, Any],
        content_parts: list[str],
        tool_calls_map: dict[int, AccumulatedToolCall],
        on_token: Callable[[str], None] | None = None,
    ) -> str | None:
        """Process one parsed SSE chunk delta; return finish_reason or None."""
        choices = chunk.get("choices")
        if not choices:
            return None
        choice = choices[0]
        delta = choice.get("delta", {})
        finish_reason: str | None = choice.get("finish_reason") or None
        token = delta.get("content") or ""
        if token:
            content_parts.append(token)
            if on_token is not None:
                on_token(token)
        for tc_delta in delta.get("XXtool_callsXX", []):
            LlmSseHelpers.merge_tool_call_delta(tool_calls_map, tc_delta)
        return finish_reason

    @staticmethod
    def xǁLlmSseHelpersǁprocess_sse_chunk__mutmut_34(
        chunk: Mapping[str, Any],
        content_parts: list[str],
        tool_calls_map: dict[int, AccumulatedToolCall],
        on_token: Callable[[str], None] | None = None,
    ) -> str | None:
        """Process one parsed SSE chunk delta; return finish_reason or None."""
        choices = chunk.get("choices")
        if not choices:
            return None
        choice = choices[0]
        delta = choice.get("delta", {})
        finish_reason: str | None = choice.get("finish_reason") or None
        token = delta.get("content") or ""
        if token:
            content_parts.append(token)
            if on_token is not None:
                on_token(token)
        for tc_delta in delta.get("TOOL_CALLS", []):
            LlmSseHelpers.merge_tool_call_delta(tool_calls_map, tc_delta)
        return finish_reason

    @staticmethod
    def xǁLlmSseHelpersǁprocess_sse_chunk__mutmut_35(
        chunk: Mapping[str, Any],
        content_parts: list[str],
        tool_calls_map: dict[int, AccumulatedToolCall],
        on_token: Callable[[str], None] | None = None,
    ) -> str | None:
        """Process one parsed SSE chunk delta; return finish_reason or None."""
        choices = chunk.get("choices")
        if not choices:
            return None
        choice = choices[0]
        delta = choice.get("delta", {})
        finish_reason: str | None = choice.get("finish_reason") or None
        token = delta.get("content") or ""
        if token:
            content_parts.append(token)
            if on_token is not None:
                on_token(token)
        for tc_delta in delta.get("tool_calls", []):
            LlmSseHelpers.merge_tool_call_delta(None, tc_delta)
        return finish_reason

    @staticmethod
    def xǁLlmSseHelpersǁprocess_sse_chunk__mutmut_36(
        chunk: Mapping[str, Any],
        content_parts: list[str],
        tool_calls_map: dict[int, AccumulatedToolCall],
        on_token: Callable[[str], None] | None = None,
    ) -> str | None:
        """Process one parsed SSE chunk delta; return finish_reason or None."""
        choices = chunk.get("choices")
        if not choices:
            return None
        choice = choices[0]
        delta = choice.get("delta", {})
        finish_reason: str | None = choice.get("finish_reason") or None
        token = delta.get("content") or ""
        if token:
            content_parts.append(token)
            if on_token is not None:
                on_token(token)
        for tc_delta in delta.get("tool_calls", []):
            LlmSseHelpers.merge_tool_call_delta(tool_calls_map, None)
        return finish_reason

    @staticmethod
    def xǁLlmSseHelpersǁprocess_sse_chunk__mutmut_37(
        chunk: Mapping[str, Any],
        content_parts: list[str],
        tool_calls_map: dict[int, AccumulatedToolCall],
        on_token: Callable[[str], None] | None = None,
    ) -> str | None:
        """Process one parsed SSE chunk delta; return finish_reason or None."""
        choices = chunk.get("choices")
        if not choices:
            return None
        choice = choices[0]
        delta = choice.get("delta", {})
        finish_reason: str | None = choice.get("finish_reason") or None
        token = delta.get("content") or ""
        if token:
            content_parts.append(token)
            if on_token is not None:
                on_token(token)
        for tc_delta in delta.get("tool_calls", []):
            LlmSseHelpers.merge_tool_call_delta(tc_delta)
        return finish_reason

    @staticmethod
    def xǁLlmSseHelpersǁprocess_sse_chunk__mutmut_38(
        chunk: Mapping[str, Any],
        content_parts: list[str],
        tool_calls_map: dict[int, AccumulatedToolCall],
        on_token: Callable[[str], None] | None = None,
    ) -> str | None:
        """Process one parsed SSE chunk delta; return finish_reason or None."""
        choices = chunk.get("choices")
        if not choices:
            return None
        choice = choices[0]
        delta = choice.get("delta", {})
        finish_reason: str | None = choice.get("finish_reason") or None
        token = delta.get("content") or ""
        if token:
            content_parts.append(token)
            if on_token is not None:
                on_token(token)
        for tc_delta in delta.get("tool_calls", []):
            LlmSseHelpers.merge_tool_call_delta(tool_calls_map, )
        return finish_reason

    @staticmethod
    @_mutmut_mutated(mutants_xǁLlmSseHelpersǁprocess_sse_payloads__mutmut)
    def process_sse_payloads(
        payloads: list[str],
        content_parts: list[str],
        tool_calls_map: dict[int, AccumulatedToolCall],
        on_token: Callable[[str], None] | None = None,
        on_usage: Callable[[int, int], None] | None = None,
    ) -> str | None:
        """Parse and process a list of raw SSE payloads; return last finish_reason seen."""
        finish_reason: str | None = None
        for raw_payload in payloads:
            try:
                chunk = orjson.loads(raw_payload)
            except ValueError:  # orjson.JSONDecodeError is a ValueError subclass
                continue
            reason = LlmSseHelpers.process_sse_chunk(
                chunk, content_parts, tool_calls_map, on_token
            )
            if reason:
                finish_reason = reason
            LlmSseHelpers.parse_usage(chunk, on_usage)
        return finish_reason

    @staticmethod
    def xǁLlmSseHelpersǁprocess_sse_payloads__mutmut_orig(
        payloads: list[str],
        content_parts: list[str],
        tool_calls_map: dict[int, AccumulatedToolCall],
        on_token: Callable[[str], None] | None = None,
        on_usage: Callable[[int, int], None] | None = None,
    ) -> str | None:
        """Parse and process a list of raw SSE payloads; return last finish_reason seen."""
        finish_reason: str | None = None
        for raw_payload in payloads:
            try:
                chunk = orjson.loads(raw_payload)
            except ValueError:  # orjson.JSONDecodeError is a ValueError subclass
                continue
            reason = LlmSseHelpers.process_sse_chunk(
                chunk, content_parts, tool_calls_map, on_token
            )
            if reason:
                finish_reason = reason
            LlmSseHelpers.parse_usage(chunk, on_usage)
        return finish_reason

    @staticmethod
    def xǁLlmSseHelpersǁprocess_sse_payloads__mutmut_1(
        payloads: list[str],
        content_parts: list[str],
        tool_calls_map: dict[int, AccumulatedToolCall],
        on_token: Callable[[str], None] | None = None,
        on_usage: Callable[[int, int], None] | None = None,
    ) -> str | None:
        """Parse and process a list of raw SSE payloads; return last finish_reason seen."""
        finish_reason: str | None = ""
        for raw_payload in payloads:
            try:
                chunk = orjson.loads(raw_payload)
            except ValueError:  # orjson.JSONDecodeError is a ValueError subclass
                continue
            reason = LlmSseHelpers.process_sse_chunk(
                chunk, content_parts, tool_calls_map, on_token
            )
            if reason:
                finish_reason = reason
            LlmSseHelpers.parse_usage(chunk, on_usage)
        return finish_reason

    @staticmethod
    def xǁLlmSseHelpersǁprocess_sse_payloads__mutmut_2(
        payloads: list[str],
        content_parts: list[str],
        tool_calls_map: dict[int, AccumulatedToolCall],
        on_token: Callable[[str], None] | None = None,
        on_usage: Callable[[int, int], None] | None = None,
    ) -> str | None:
        """Parse and process a list of raw SSE payloads; return last finish_reason seen."""
        finish_reason: str | None = None
        for raw_payload in payloads:
            try:
                chunk = None
            except ValueError:  # orjson.JSONDecodeError is a ValueError subclass
                continue
            reason = LlmSseHelpers.process_sse_chunk(
                chunk, content_parts, tool_calls_map, on_token
            )
            if reason:
                finish_reason = reason
            LlmSseHelpers.parse_usage(chunk, on_usage)
        return finish_reason

    @staticmethod
    def xǁLlmSseHelpersǁprocess_sse_payloads__mutmut_3(
        payloads: list[str],
        content_parts: list[str],
        tool_calls_map: dict[int, AccumulatedToolCall],
        on_token: Callable[[str], None] | None = None,
        on_usage: Callable[[int, int], None] | None = None,
    ) -> str | None:
        """Parse and process a list of raw SSE payloads; return last finish_reason seen."""
        finish_reason: str | None = None
        for raw_payload in payloads:
            try:
                chunk = orjson.loads(None)
            except ValueError:  # orjson.JSONDecodeError is a ValueError subclass
                continue
            reason = LlmSseHelpers.process_sse_chunk(
                chunk, content_parts, tool_calls_map, on_token
            )
            if reason:
                finish_reason = reason
            LlmSseHelpers.parse_usage(chunk, on_usage)
        return finish_reason

    @staticmethod
    def xǁLlmSseHelpersǁprocess_sse_payloads__mutmut_4(
        payloads: list[str],
        content_parts: list[str],
        tool_calls_map: dict[int, AccumulatedToolCall],
        on_token: Callable[[str], None] | None = None,
        on_usage: Callable[[int, int], None] | None = None,
    ) -> str | None:
        """Parse and process a list of raw SSE payloads; return last finish_reason seen."""
        finish_reason: str | None = None
        for raw_payload in payloads:
            try:
                chunk = orjson.loads(raw_payload)
            except ValueError:  # orjson.JSONDecodeError is a ValueError subclass
                break
            reason = LlmSseHelpers.process_sse_chunk(
                chunk, content_parts, tool_calls_map, on_token
            )
            if reason:
                finish_reason = reason
            LlmSseHelpers.parse_usage(chunk, on_usage)
        return finish_reason

    @staticmethod
    def xǁLlmSseHelpersǁprocess_sse_payloads__mutmut_5(
        payloads: list[str],
        content_parts: list[str],
        tool_calls_map: dict[int, AccumulatedToolCall],
        on_token: Callable[[str], None] | None = None,
        on_usage: Callable[[int, int], None] | None = None,
    ) -> str | None:
        """Parse and process a list of raw SSE payloads; return last finish_reason seen."""
        finish_reason: str | None = None
        for raw_payload in payloads:
            try:
                chunk = orjson.loads(raw_payload)
            except ValueError:  # orjson.JSONDecodeError is a ValueError subclass
                continue
            reason = None
            if reason:
                finish_reason = reason
            LlmSseHelpers.parse_usage(chunk, on_usage)
        return finish_reason

    @staticmethod
    def xǁLlmSseHelpersǁprocess_sse_payloads__mutmut_6(
        payloads: list[str],
        content_parts: list[str],
        tool_calls_map: dict[int, AccumulatedToolCall],
        on_token: Callable[[str], None] | None = None,
        on_usage: Callable[[int, int], None] | None = None,
    ) -> str | None:
        """Parse and process a list of raw SSE payloads; return last finish_reason seen."""
        finish_reason: str | None = None
        for raw_payload in payloads:
            try:
                chunk = orjson.loads(raw_payload)
            except ValueError:  # orjson.JSONDecodeError is a ValueError subclass
                continue
            reason = LlmSseHelpers.process_sse_chunk(
                None, content_parts, tool_calls_map, on_token
            )
            if reason:
                finish_reason = reason
            LlmSseHelpers.parse_usage(chunk, on_usage)
        return finish_reason

    @staticmethod
    def xǁLlmSseHelpersǁprocess_sse_payloads__mutmut_7(
        payloads: list[str],
        content_parts: list[str],
        tool_calls_map: dict[int, AccumulatedToolCall],
        on_token: Callable[[str], None] | None = None,
        on_usage: Callable[[int, int], None] | None = None,
    ) -> str | None:
        """Parse and process a list of raw SSE payloads; return last finish_reason seen."""
        finish_reason: str | None = None
        for raw_payload in payloads:
            try:
                chunk = orjson.loads(raw_payload)
            except ValueError:  # orjson.JSONDecodeError is a ValueError subclass
                continue
            reason = LlmSseHelpers.process_sse_chunk(
                chunk, None, tool_calls_map, on_token
            )
            if reason:
                finish_reason = reason
            LlmSseHelpers.parse_usage(chunk, on_usage)
        return finish_reason

    @staticmethod
    def xǁLlmSseHelpersǁprocess_sse_payloads__mutmut_8(
        payloads: list[str],
        content_parts: list[str],
        tool_calls_map: dict[int, AccumulatedToolCall],
        on_token: Callable[[str], None] | None = None,
        on_usage: Callable[[int, int], None] | None = None,
    ) -> str | None:
        """Parse and process a list of raw SSE payloads; return last finish_reason seen."""
        finish_reason: str | None = None
        for raw_payload in payloads:
            try:
                chunk = orjson.loads(raw_payload)
            except ValueError:  # orjson.JSONDecodeError is a ValueError subclass
                continue
            reason = LlmSseHelpers.process_sse_chunk(
                chunk, content_parts, None, on_token
            )
            if reason:
                finish_reason = reason
            LlmSseHelpers.parse_usage(chunk, on_usage)
        return finish_reason

    @staticmethod
    def xǁLlmSseHelpersǁprocess_sse_payloads__mutmut_9(
        payloads: list[str],
        content_parts: list[str],
        tool_calls_map: dict[int, AccumulatedToolCall],
        on_token: Callable[[str], None] | None = None,
        on_usage: Callable[[int, int], None] | None = None,
    ) -> str | None:
        """Parse and process a list of raw SSE payloads; return last finish_reason seen."""
        finish_reason: str | None = None
        for raw_payload in payloads:
            try:
                chunk = orjson.loads(raw_payload)
            except ValueError:  # orjson.JSONDecodeError is a ValueError subclass
                continue
            reason = LlmSseHelpers.process_sse_chunk(
                chunk, content_parts, tool_calls_map, None
            )
            if reason:
                finish_reason = reason
            LlmSseHelpers.parse_usage(chunk, on_usage)
        return finish_reason

    @staticmethod
    def xǁLlmSseHelpersǁprocess_sse_payloads__mutmut_10(
        payloads: list[str],
        content_parts: list[str],
        tool_calls_map: dict[int, AccumulatedToolCall],
        on_token: Callable[[str], None] | None = None,
        on_usage: Callable[[int, int], None] | None = None,
    ) -> str | None:
        """Parse and process a list of raw SSE payloads; return last finish_reason seen."""
        finish_reason: str | None = None
        for raw_payload in payloads:
            try:
                chunk = orjson.loads(raw_payload)
            except ValueError:  # orjson.JSONDecodeError is a ValueError subclass
                continue
            reason = LlmSseHelpers.process_sse_chunk(
                content_parts, tool_calls_map, on_token
            )
            if reason:
                finish_reason = reason
            LlmSseHelpers.parse_usage(chunk, on_usage)
        return finish_reason

    @staticmethod
    def xǁLlmSseHelpersǁprocess_sse_payloads__mutmut_11(
        payloads: list[str],
        content_parts: list[str],
        tool_calls_map: dict[int, AccumulatedToolCall],
        on_token: Callable[[str], None] | None = None,
        on_usage: Callable[[int, int], None] | None = None,
    ) -> str | None:
        """Parse and process a list of raw SSE payloads; return last finish_reason seen."""
        finish_reason: str | None = None
        for raw_payload in payloads:
            try:
                chunk = orjson.loads(raw_payload)
            except ValueError:  # orjson.JSONDecodeError is a ValueError subclass
                continue
            reason = LlmSseHelpers.process_sse_chunk(
                chunk, tool_calls_map, on_token
            )
            if reason:
                finish_reason = reason
            LlmSseHelpers.parse_usage(chunk, on_usage)
        return finish_reason

    @staticmethod
    def xǁLlmSseHelpersǁprocess_sse_payloads__mutmut_12(
        payloads: list[str],
        content_parts: list[str],
        tool_calls_map: dict[int, AccumulatedToolCall],
        on_token: Callable[[str], None] | None = None,
        on_usage: Callable[[int, int], None] | None = None,
    ) -> str | None:
        """Parse and process a list of raw SSE payloads; return last finish_reason seen."""
        finish_reason: str | None = None
        for raw_payload in payloads:
            try:
                chunk = orjson.loads(raw_payload)
            except ValueError:  # orjson.JSONDecodeError is a ValueError subclass
                continue
            reason = LlmSseHelpers.process_sse_chunk(
                chunk, content_parts, on_token
            )
            if reason:
                finish_reason = reason
            LlmSseHelpers.parse_usage(chunk, on_usage)
        return finish_reason

    @staticmethod
    def xǁLlmSseHelpersǁprocess_sse_payloads__mutmut_13(
        payloads: list[str],
        content_parts: list[str],
        tool_calls_map: dict[int, AccumulatedToolCall],
        on_token: Callable[[str], None] | None = None,
        on_usage: Callable[[int, int], None] | None = None,
    ) -> str | None:
        """Parse and process a list of raw SSE payloads; return last finish_reason seen."""
        finish_reason: str | None = None
        for raw_payload in payloads:
            try:
                chunk = orjson.loads(raw_payload)
            except ValueError:  # orjson.JSONDecodeError is a ValueError subclass
                continue
            reason = LlmSseHelpers.process_sse_chunk(
                chunk, content_parts, tool_calls_map, )
            if reason:
                finish_reason = reason
            LlmSseHelpers.parse_usage(chunk, on_usage)
        return finish_reason

    @staticmethod
    def xǁLlmSseHelpersǁprocess_sse_payloads__mutmut_14(
        payloads: list[str],
        content_parts: list[str],
        tool_calls_map: dict[int, AccumulatedToolCall],
        on_token: Callable[[str], None] | None = None,
        on_usage: Callable[[int, int], None] | None = None,
    ) -> str | None:
        """Parse and process a list of raw SSE payloads; return last finish_reason seen."""
        finish_reason: str | None = None
        for raw_payload in payloads:
            try:
                chunk = orjson.loads(raw_payload)
            except ValueError:  # orjson.JSONDecodeError is a ValueError subclass
                continue
            reason = LlmSseHelpers.process_sse_chunk(
                chunk, content_parts, tool_calls_map, on_token
            )
            if reason:
                finish_reason = None
            LlmSseHelpers.parse_usage(chunk, on_usage)
        return finish_reason

    @staticmethod
    def xǁLlmSseHelpersǁprocess_sse_payloads__mutmut_15(
        payloads: list[str],
        content_parts: list[str],
        tool_calls_map: dict[int, AccumulatedToolCall],
        on_token: Callable[[str], None] | None = None,
        on_usage: Callable[[int, int], None] | None = None,
    ) -> str | None:
        """Parse and process a list of raw SSE payloads; return last finish_reason seen."""
        finish_reason: str | None = None
        for raw_payload in payloads:
            try:
                chunk = orjson.loads(raw_payload)
            except ValueError:  # orjson.JSONDecodeError is a ValueError subclass
                continue
            reason = LlmSseHelpers.process_sse_chunk(
                chunk, content_parts, tool_calls_map, on_token
            )
            if reason:
                finish_reason = reason
            LlmSseHelpers.parse_usage(None, on_usage)
        return finish_reason

    @staticmethod
    def xǁLlmSseHelpersǁprocess_sse_payloads__mutmut_16(
        payloads: list[str],
        content_parts: list[str],
        tool_calls_map: dict[int, AccumulatedToolCall],
        on_token: Callable[[str], None] | None = None,
        on_usage: Callable[[int, int], None] | None = None,
    ) -> str | None:
        """Parse and process a list of raw SSE payloads; return last finish_reason seen."""
        finish_reason: str | None = None
        for raw_payload in payloads:
            try:
                chunk = orjson.loads(raw_payload)
            except ValueError:  # orjson.JSONDecodeError is a ValueError subclass
                continue
            reason = LlmSseHelpers.process_sse_chunk(
                chunk, content_parts, tool_calls_map, on_token
            )
            if reason:
                finish_reason = reason
            LlmSseHelpers.parse_usage(chunk, None)
        return finish_reason

    @staticmethod
    def xǁLlmSseHelpersǁprocess_sse_payloads__mutmut_17(
        payloads: list[str],
        content_parts: list[str],
        tool_calls_map: dict[int, AccumulatedToolCall],
        on_token: Callable[[str], None] | None = None,
        on_usage: Callable[[int, int], None] | None = None,
    ) -> str | None:
        """Parse and process a list of raw SSE payloads; return last finish_reason seen."""
        finish_reason: str | None = None
        for raw_payload in payloads:
            try:
                chunk = orjson.loads(raw_payload)
            except ValueError:  # orjson.JSONDecodeError is a ValueError subclass
                continue
            reason = LlmSseHelpers.process_sse_chunk(
                chunk, content_parts, tool_calls_map, on_token
            )
            if reason:
                finish_reason = reason
            LlmSseHelpers.parse_usage(on_usage)
        return finish_reason

    @staticmethod
    def xǁLlmSseHelpersǁprocess_sse_payloads__mutmut_18(
        payloads: list[str],
        content_parts: list[str],
        tool_calls_map: dict[int, AccumulatedToolCall],
        on_token: Callable[[str], None] | None = None,
        on_usage: Callable[[int, int], None] | None = None,
    ) -> str | None:
        """Parse and process a list of raw SSE payloads; return last finish_reason seen."""
        finish_reason: str | None = None
        for raw_payload in payloads:
            try:
                chunk = orjson.loads(raw_payload)
            except ValueError:  # orjson.JSONDecodeError is a ValueError subclass
                continue
            reason = LlmSseHelpers.process_sse_chunk(
                chunk, content_parts, tool_calls_map, on_token
            )
            if reason:
                finish_reason = reason
            LlmSseHelpers.parse_usage(chunk, )
        return finish_reason

    @staticmethod
    @_mutmut_mutated(mutants_xǁLlmSseHelpersǁparse_usage__mutmut)
    def parse_usage(
        data: Mapping[str, Any], on_usage: Callable[[int, int], None] | None = None
    ) -> LLMUsage | None:
        """Extract token usage from response data; fire on_usage callback; return LLMUsage or None."""
        usage_raw = data.get("usage")
        if not isinstance(usage_raw, dict):
            return None
        pt = usage_raw.get("prompt_tokens")
        ct = usage_raw.get("completion_tokens")
        if not isinstance(pt, int) or not isinstance(ct, int):
            return None
        if on_usage is not None:
            on_usage(pt, ct)
        return LLMUsage(prompt_tokens=pt, completion_tokens=ct)

    @staticmethod
    def xǁLlmSseHelpersǁparse_usage__mutmut_orig(
        data: Mapping[str, Any], on_usage: Callable[[int, int], None] | None = None
    ) -> LLMUsage | None:
        """Extract token usage from response data; fire on_usage callback; return LLMUsage or None."""
        usage_raw = data.get("usage")
        if not isinstance(usage_raw, dict):
            return None
        pt = usage_raw.get("prompt_tokens")
        ct = usage_raw.get("completion_tokens")
        if not isinstance(pt, int) or not isinstance(ct, int):
            return None
        if on_usage is not None:
            on_usage(pt, ct)
        return LLMUsage(prompt_tokens=pt, completion_tokens=ct)

    @staticmethod
    def xǁLlmSseHelpersǁparse_usage__mutmut_1(
        data: Mapping[str, Any], on_usage: Callable[[int, int], None] | None = None
    ) -> LLMUsage | None:
        """Extract token usage from response data; fire on_usage callback; return LLMUsage or None."""
        usage_raw = None
        if not isinstance(usage_raw, dict):
            return None
        pt = usage_raw.get("prompt_tokens")
        ct = usage_raw.get("completion_tokens")
        if not isinstance(pt, int) or not isinstance(ct, int):
            return None
        if on_usage is not None:
            on_usage(pt, ct)
        return LLMUsage(prompt_tokens=pt, completion_tokens=ct)

    @staticmethod
    def xǁLlmSseHelpersǁparse_usage__mutmut_2(
        data: Mapping[str, Any], on_usage: Callable[[int, int], None] | None = None
    ) -> LLMUsage | None:
        """Extract token usage from response data; fire on_usage callback; return LLMUsage or None."""
        usage_raw = data.get(None)
        if not isinstance(usage_raw, dict):
            return None
        pt = usage_raw.get("prompt_tokens")
        ct = usage_raw.get("completion_tokens")
        if not isinstance(pt, int) or not isinstance(ct, int):
            return None
        if on_usage is not None:
            on_usage(pt, ct)
        return LLMUsage(prompt_tokens=pt, completion_tokens=ct)

    @staticmethod
    def xǁLlmSseHelpersǁparse_usage__mutmut_3(
        data: Mapping[str, Any], on_usage: Callable[[int, int], None] | None = None
    ) -> LLMUsage | None:
        """Extract token usage from response data; fire on_usage callback; return LLMUsage or None."""
        usage_raw = data.get("XXusageXX")
        if not isinstance(usage_raw, dict):
            return None
        pt = usage_raw.get("prompt_tokens")
        ct = usage_raw.get("completion_tokens")
        if not isinstance(pt, int) or not isinstance(ct, int):
            return None
        if on_usage is not None:
            on_usage(pt, ct)
        return LLMUsage(prompt_tokens=pt, completion_tokens=ct)

    @staticmethod
    def xǁLlmSseHelpersǁparse_usage__mutmut_4(
        data: Mapping[str, Any], on_usage: Callable[[int, int], None] | None = None
    ) -> LLMUsage | None:
        """Extract token usage from response data; fire on_usage callback; return LLMUsage or None."""
        usage_raw = data.get("USAGE")
        if not isinstance(usage_raw, dict):
            return None
        pt = usage_raw.get("prompt_tokens")
        ct = usage_raw.get("completion_tokens")
        if not isinstance(pt, int) or not isinstance(ct, int):
            return None
        if on_usage is not None:
            on_usage(pt, ct)
        return LLMUsage(prompt_tokens=pt, completion_tokens=ct)

    @staticmethod
    def xǁLlmSseHelpersǁparse_usage__mutmut_5(
        data: Mapping[str, Any], on_usage: Callable[[int, int], None] | None = None
    ) -> LLMUsage | None:
        """Extract token usage from response data; fire on_usage callback; return LLMUsage or None."""
        usage_raw = data.get("usage")
        if isinstance(usage_raw, dict):
            return None
        pt = usage_raw.get("prompt_tokens")
        ct = usage_raw.get("completion_tokens")
        if not isinstance(pt, int) or not isinstance(ct, int):
            return None
        if on_usage is not None:
            on_usage(pt, ct)
        return LLMUsage(prompt_tokens=pt, completion_tokens=ct)

    @staticmethod
    def xǁLlmSseHelpersǁparse_usage__mutmut_6(
        data: Mapping[str, Any], on_usage: Callable[[int, int], None] | None = None
    ) -> LLMUsage | None:
        """Extract token usage from response data; fire on_usage callback; return LLMUsage or None."""
        usage_raw = data.get("usage")
        if not isinstance(usage_raw, dict):
            return None
        pt = None
        ct = usage_raw.get("completion_tokens")
        if not isinstance(pt, int) or not isinstance(ct, int):
            return None
        if on_usage is not None:
            on_usage(pt, ct)
        return LLMUsage(prompt_tokens=pt, completion_tokens=ct)

    @staticmethod
    def xǁLlmSseHelpersǁparse_usage__mutmut_7(
        data: Mapping[str, Any], on_usage: Callable[[int, int], None] | None = None
    ) -> LLMUsage | None:
        """Extract token usage from response data; fire on_usage callback; return LLMUsage or None."""
        usage_raw = data.get("usage")
        if not isinstance(usage_raw, dict):
            return None
        pt = usage_raw.get(None)
        ct = usage_raw.get("completion_tokens")
        if not isinstance(pt, int) or not isinstance(ct, int):
            return None
        if on_usage is not None:
            on_usage(pt, ct)
        return LLMUsage(prompt_tokens=pt, completion_tokens=ct)

    @staticmethod
    def xǁLlmSseHelpersǁparse_usage__mutmut_8(
        data: Mapping[str, Any], on_usage: Callable[[int, int], None] | None = None
    ) -> LLMUsage | None:
        """Extract token usage from response data; fire on_usage callback; return LLMUsage or None."""
        usage_raw = data.get("usage")
        if not isinstance(usage_raw, dict):
            return None
        pt = usage_raw.get("XXprompt_tokensXX")
        ct = usage_raw.get("completion_tokens")
        if not isinstance(pt, int) or not isinstance(ct, int):
            return None
        if on_usage is not None:
            on_usage(pt, ct)
        return LLMUsage(prompt_tokens=pt, completion_tokens=ct)

    @staticmethod
    def xǁLlmSseHelpersǁparse_usage__mutmut_9(
        data: Mapping[str, Any], on_usage: Callable[[int, int], None] | None = None
    ) -> LLMUsage | None:
        """Extract token usage from response data; fire on_usage callback; return LLMUsage or None."""
        usage_raw = data.get("usage")
        if not isinstance(usage_raw, dict):
            return None
        pt = usage_raw.get("PROMPT_TOKENS")
        ct = usage_raw.get("completion_tokens")
        if not isinstance(pt, int) or not isinstance(ct, int):
            return None
        if on_usage is not None:
            on_usage(pt, ct)
        return LLMUsage(prompt_tokens=pt, completion_tokens=ct)

    @staticmethod
    def xǁLlmSseHelpersǁparse_usage__mutmut_10(
        data: Mapping[str, Any], on_usage: Callable[[int, int], None] | None = None
    ) -> LLMUsage | None:
        """Extract token usage from response data; fire on_usage callback; return LLMUsage or None."""
        usage_raw = data.get("usage")
        if not isinstance(usage_raw, dict):
            return None
        pt = usage_raw.get("prompt_tokens")
        ct = None
        if not isinstance(pt, int) or not isinstance(ct, int):
            return None
        if on_usage is not None:
            on_usage(pt, ct)
        return LLMUsage(prompt_tokens=pt, completion_tokens=ct)

    @staticmethod
    def xǁLlmSseHelpersǁparse_usage__mutmut_11(
        data: Mapping[str, Any], on_usage: Callable[[int, int], None] | None = None
    ) -> LLMUsage | None:
        """Extract token usage from response data; fire on_usage callback; return LLMUsage or None."""
        usage_raw = data.get("usage")
        if not isinstance(usage_raw, dict):
            return None
        pt = usage_raw.get("prompt_tokens")
        ct = usage_raw.get(None)
        if not isinstance(pt, int) or not isinstance(ct, int):
            return None
        if on_usage is not None:
            on_usage(pt, ct)
        return LLMUsage(prompt_tokens=pt, completion_tokens=ct)

    @staticmethod
    def xǁLlmSseHelpersǁparse_usage__mutmut_12(
        data: Mapping[str, Any], on_usage: Callable[[int, int], None] | None = None
    ) -> LLMUsage | None:
        """Extract token usage from response data; fire on_usage callback; return LLMUsage or None."""
        usage_raw = data.get("usage")
        if not isinstance(usage_raw, dict):
            return None
        pt = usage_raw.get("prompt_tokens")
        ct = usage_raw.get("XXcompletion_tokensXX")
        if not isinstance(pt, int) or not isinstance(ct, int):
            return None
        if on_usage is not None:
            on_usage(pt, ct)
        return LLMUsage(prompt_tokens=pt, completion_tokens=ct)

    @staticmethod
    def xǁLlmSseHelpersǁparse_usage__mutmut_13(
        data: Mapping[str, Any], on_usage: Callable[[int, int], None] | None = None
    ) -> LLMUsage | None:
        """Extract token usage from response data; fire on_usage callback; return LLMUsage or None."""
        usage_raw = data.get("usage")
        if not isinstance(usage_raw, dict):
            return None
        pt = usage_raw.get("prompt_tokens")
        ct = usage_raw.get("COMPLETION_TOKENS")
        if not isinstance(pt, int) or not isinstance(ct, int):
            return None
        if on_usage is not None:
            on_usage(pt, ct)
        return LLMUsage(prompt_tokens=pt, completion_tokens=ct)

    @staticmethod
    def xǁLlmSseHelpersǁparse_usage__mutmut_14(
        data: Mapping[str, Any], on_usage: Callable[[int, int], None] | None = None
    ) -> LLMUsage | None:
        """Extract token usage from response data; fire on_usage callback; return LLMUsage or None."""
        usage_raw = data.get("usage")
        if not isinstance(usage_raw, dict):
            return None
        pt = usage_raw.get("prompt_tokens")
        ct = usage_raw.get("completion_tokens")
        if not isinstance(pt, int) and not isinstance(ct, int):
            return None
        if on_usage is not None:
            on_usage(pt, ct)
        return LLMUsage(prompt_tokens=pt, completion_tokens=ct)

    @staticmethod
    def xǁLlmSseHelpersǁparse_usage__mutmut_15(
        data: Mapping[str, Any], on_usage: Callable[[int, int], None] | None = None
    ) -> LLMUsage | None:
        """Extract token usage from response data; fire on_usage callback; return LLMUsage or None."""
        usage_raw = data.get("usage")
        if not isinstance(usage_raw, dict):
            return None
        pt = usage_raw.get("prompt_tokens")
        ct = usage_raw.get("completion_tokens")
        if isinstance(pt, int) or not isinstance(ct, int):
            return None
        if on_usage is not None:
            on_usage(pt, ct)
        return LLMUsage(prompt_tokens=pt, completion_tokens=ct)

    @staticmethod
    def xǁLlmSseHelpersǁparse_usage__mutmut_16(
        data: Mapping[str, Any], on_usage: Callable[[int, int], None] | None = None
    ) -> LLMUsage | None:
        """Extract token usage from response data; fire on_usage callback; return LLMUsage or None."""
        usage_raw = data.get("usage")
        if not isinstance(usage_raw, dict):
            return None
        pt = usage_raw.get("prompt_tokens")
        ct = usage_raw.get("completion_tokens")
        if not isinstance(pt, int) or isinstance(ct, int):
            return None
        if on_usage is not None:
            on_usage(pt, ct)
        return LLMUsage(prompt_tokens=pt, completion_tokens=ct)

    @staticmethod
    def xǁLlmSseHelpersǁparse_usage__mutmut_17(
        data: Mapping[str, Any], on_usage: Callable[[int, int], None] | None = None
    ) -> LLMUsage | None:
        """Extract token usage from response data; fire on_usage callback; return LLMUsage or None."""
        usage_raw = data.get("usage")
        if not isinstance(usage_raw, dict):
            return None
        pt = usage_raw.get("prompt_tokens")
        ct = usage_raw.get("completion_tokens")
        if not isinstance(pt, int) or not isinstance(ct, int):
            return None
        if on_usage is None:
            on_usage(pt, ct)
        return LLMUsage(prompt_tokens=pt, completion_tokens=ct)

    @staticmethod
    def xǁLlmSseHelpersǁparse_usage__mutmut_18(
        data: Mapping[str, Any], on_usage: Callable[[int, int], None] | None = None
    ) -> LLMUsage | None:
        """Extract token usage from response data; fire on_usage callback; return LLMUsage or None."""
        usage_raw = data.get("usage")
        if not isinstance(usage_raw, dict):
            return None
        pt = usage_raw.get("prompt_tokens")
        ct = usage_raw.get("completion_tokens")
        if not isinstance(pt, int) or not isinstance(ct, int):
            return None
        if on_usage is not None:
            on_usage(None, ct)
        return LLMUsage(prompt_tokens=pt, completion_tokens=ct)

    @staticmethod
    def xǁLlmSseHelpersǁparse_usage__mutmut_19(
        data: Mapping[str, Any], on_usage: Callable[[int, int], None] | None = None
    ) -> LLMUsage | None:
        """Extract token usage from response data; fire on_usage callback; return LLMUsage or None."""
        usage_raw = data.get("usage")
        if not isinstance(usage_raw, dict):
            return None
        pt = usage_raw.get("prompt_tokens")
        ct = usage_raw.get("completion_tokens")
        if not isinstance(pt, int) or not isinstance(ct, int):
            return None
        if on_usage is not None:
            on_usage(pt, None)
        return LLMUsage(prompt_tokens=pt, completion_tokens=ct)

    @staticmethod
    def xǁLlmSseHelpersǁparse_usage__mutmut_20(
        data: Mapping[str, Any], on_usage: Callable[[int, int], None] | None = None
    ) -> LLMUsage | None:
        """Extract token usage from response data; fire on_usage callback; return LLMUsage or None."""
        usage_raw = data.get("usage")
        if not isinstance(usage_raw, dict):
            return None
        pt = usage_raw.get("prompt_tokens")
        ct = usage_raw.get("completion_tokens")
        if not isinstance(pt, int) or not isinstance(ct, int):
            return None
        if on_usage is not None:
            on_usage(ct)
        return LLMUsage(prompt_tokens=pt, completion_tokens=ct)

    @staticmethod
    def xǁLlmSseHelpersǁparse_usage__mutmut_21(
        data: Mapping[str, Any], on_usage: Callable[[int, int], None] | None = None
    ) -> LLMUsage | None:
        """Extract token usage from response data; fire on_usage callback; return LLMUsage or None."""
        usage_raw = data.get("usage")
        if not isinstance(usage_raw, dict):
            return None
        pt = usage_raw.get("prompt_tokens")
        ct = usage_raw.get("completion_tokens")
        if not isinstance(pt, int) or not isinstance(ct, int):
            return None
        if on_usage is not None:
            on_usage(pt, )
        return LLMUsage(prompt_tokens=pt, completion_tokens=ct)

    @staticmethod
    def xǁLlmSseHelpersǁparse_usage__mutmut_22(
        data: Mapping[str, Any], on_usage: Callable[[int, int], None] | None = None
    ) -> LLMUsage | None:
        """Extract token usage from response data; fire on_usage callback; return LLMUsage or None."""
        usage_raw = data.get("usage")
        if not isinstance(usage_raw, dict):
            return None
        pt = usage_raw.get("prompt_tokens")
        ct = usage_raw.get("completion_tokens")
        if not isinstance(pt, int) or not isinstance(ct, int):
            return None
        if on_usage is not None:
            on_usage(pt, ct)
        return LLMUsage(prompt_tokens=None, completion_tokens=ct)

    @staticmethod
    def xǁLlmSseHelpersǁparse_usage__mutmut_23(
        data: Mapping[str, Any], on_usage: Callable[[int, int], None] | None = None
    ) -> LLMUsage | None:
        """Extract token usage from response data; fire on_usage callback; return LLMUsage or None."""
        usage_raw = data.get("usage")
        if not isinstance(usage_raw, dict):
            return None
        pt = usage_raw.get("prompt_tokens")
        ct = usage_raw.get("completion_tokens")
        if not isinstance(pt, int) or not isinstance(ct, int):
            return None
        if on_usage is not None:
            on_usage(pt, ct)
        return LLMUsage(prompt_tokens=pt, completion_tokens=None)

    @staticmethod
    def xǁLlmSseHelpersǁparse_usage__mutmut_24(
        data: Mapping[str, Any], on_usage: Callable[[int, int], None] | None = None
    ) -> LLMUsage | None:
        """Extract token usage from response data; fire on_usage callback; return LLMUsage or None."""
        usage_raw = data.get("usage")
        if not isinstance(usage_raw, dict):
            return None
        pt = usage_raw.get("prompt_tokens")
        ct = usage_raw.get("completion_tokens")
        if not isinstance(pt, int) or not isinstance(ct, int):
            return None
        if on_usage is not None:
            on_usage(pt, ct)
        return LLMUsage(completion_tokens=ct)

    @staticmethod
    def xǁLlmSseHelpersǁparse_usage__mutmut_25(
        data: Mapping[str, Any], on_usage: Callable[[int, int], None] | None = None
    ) -> LLMUsage | None:
        """Extract token usage from response data; fire on_usage callback; return LLMUsage or None."""
        usage_raw = data.get("usage")
        if not isinstance(usage_raw, dict):
            return None
        pt = usage_raw.get("prompt_tokens")
        ct = usage_raw.get("completion_tokens")
        if not isinstance(pt, int) or not isinstance(ct, int):
            return None
        if on_usage is not None:
            on_usage(pt, ct)
        return LLMUsage(prompt_tokens=pt, )

    @staticmethod
    @_mutmut_mutated(mutants_xǁLlmSseHelpersǁaccumulate_parse_errors__mutmut)
    def accumulate_parse_errors(
        parser: RobustSSEParser,
        stat_parse_errors: int,
    ) -> int:
        """Add parse errors to instance stats and reset the parser's counter; return updated count."""
        if parser.stat_parse_errors:
            stat_parse_errors += parser.stat_parse_errors
            parser.stat_parse_errors = 0
        return stat_parse_errors

    @staticmethod
    def xǁLlmSseHelpersǁaccumulate_parse_errors__mutmut_orig(
        parser: RobustSSEParser,
        stat_parse_errors: int,
    ) -> int:
        """Add parse errors to instance stats and reset the parser's counter; return updated count."""
        if parser.stat_parse_errors:
            stat_parse_errors += parser.stat_parse_errors
            parser.stat_parse_errors = 0
        return stat_parse_errors

    @staticmethod
    def xǁLlmSseHelpersǁaccumulate_parse_errors__mutmut_1(
        parser: RobustSSEParser,
        stat_parse_errors: int,
    ) -> int:
        """Add parse errors to instance stats and reset the parser's counter; return updated count."""
        if parser.stat_parse_errors:
            stat_parse_errors = parser.stat_parse_errors
            parser.stat_parse_errors = 0
        return stat_parse_errors

    @staticmethod
    def xǁLlmSseHelpersǁaccumulate_parse_errors__mutmut_2(
        parser: RobustSSEParser,
        stat_parse_errors: int,
    ) -> int:
        """Add parse errors to instance stats and reset the parser's counter; return updated count."""
        if parser.stat_parse_errors:
            stat_parse_errors -= parser.stat_parse_errors
            parser.stat_parse_errors = 0
        return stat_parse_errors

    @staticmethod
    def xǁLlmSseHelpersǁaccumulate_parse_errors__mutmut_3(
        parser: RobustSSEParser,
        stat_parse_errors: int,
    ) -> int:
        """Add parse errors to instance stats and reset the parser's counter; return updated count."""
        if parser.stat_parse_errors:
            stat_parse_errors += parser.stat_parse_errors
            parser.stat_parse_errors = None
        return stat_parse_errors

    @staticmethod
    def xǁLlmSseHelpersǁaccumulate_parse_errors__mutmut_4(
        parser: RobustSSEParser,
        stat_parse_errors: int,
    ) -> int:
        """Add parse errors to instance stats and reset the parser's counter; return updated count."""
        if parser.stat_parse_errors:
            stat_parse_errors += parser.stat_parse_errors
            parser.stat_parse_errors = 1
        return stat_parse_errors

mutants_xǁLlmSseHelpersǁmerge_tool_call_delta__mutmut['_mutmut_orig'] = LlmSseHelpers.xǁLlmSseHelpersǁmerge_tool_call_delta__mutmut_orig # type: ignore # mutmut generated
mutants_xǁLlmSseHelpersǁmerge_tool_call_delta__mutmut['xǁLlmSseHelpersǁmerge_tool_call_delta__mutmut_1'] = LlmSseHelpers.xǁLlmSseHelpersǁmerge_tool_call_delta__mutmut_1 # type: ignore # mutmut generated
mutants_xǁLlmSseHelpersǁmerge_tool_call_delta__mutmut['xǁLlmSseHelpersǁmerge_tool_call_delta__mutmut_2'] = LlmSseHelpers.xǁLlmSseHelpersǁmerge_tool_call_delta__mutmut_2 # type: ignore # mutmut generated
mutants_xǁLlmSseHelpersǁmerge_tool_call_delta__mutmut['xǁLlmSseHelpersǁmerge_tool_call_delta__mutmut_3'] = LlmSseHelpers.xǁLlmSseHelpersǁmerge_tool_call_delta__mutmut_3 # type: ignore # mutmut generated
mutants_xǁLlmSseHelpersǁmerge_tool_call_delta__mutmut['xǁLlmSseHelpersǁmerge_tool_call_delta__mutmut_4'] = LlmSseHelpers.xǁLlmSseHelpersǁmerge_tool_call_delta__mutmut_4 # type: ignore # mutmut generated
mutants_xǁLlmSseHelpersǁmerge_tool_call_delta__mutmut['xǁLlmSseHelpersǁmerge_tool_call_delta__mutmut_5'] = LlmSseHelpers.xǁLlmSseHelpersǁmerge_tool_call_delta__mutmut_5 # type: ignore # mutmut generated
mutants_xǁLlmSseHelpersǁmerge_tool_call_delta__mutmut['xǁLlmSseHelpersǁmerge_tool_call_delta__mutmut_6'] = LlmSseHelpers.xǁLlmSseHelpersǁmerge_tool_call_delta__mutmut_6 # type: ignore # mutmut generated
mutants_xǁLlmSseHelpersǁmerge_tool_call_delta__mutmut['xǁLlmSseHelpersǁmerge_tool_call_delta__mutmut_7'] = LlmSseHelpers.xǁLlmSseHelpersǁmerge_tool_call_delta__mutmut_7 # type: ignore # mutmut generated
mutants_xǁLlmSseHelpersǁmerge_tool_call_delta__mutmut['xǁLlmSseHelpersǁmerge_tool_call_delta__mutmut_8'] = LlmSseHelpers.xǁLlmSseHelpersǁmerge_tool_call_delta__mutmut_8 # type: ignore # mutmut generated
mutants_xǁLlmSseHelpersǁmerge_tool_call_delta__mutmut['xǁLlmSseHelpersǁmerge_tool_call_delta__mutmut_9'] = LlmSseHelpers.xǁLlmSseHelpersǁmerge_tool_call_delta__mutmut_9 # type: ignore # mutmut generated
mutants_xǁLlmSseHelpersǁmerge_tool_call_delta__mutmut['xǁLlmSseHelpersǁmerge_tool_call_delta__mutmut_10'] = LlmSseHelpers.xǁLlmSseHelpersǁmerge_tool_call_delta__mutmut_10 # type: ignore # mutmut generated
mutants_xǁLlmSseHelpersǁmerge_tool_call_delta__mutmut['xǁLlmSseHelpersǁmerge_tool_call_delta__mutmut_11'] = LlmSseHelpers.xǁLlmSseHelpersǁmerge_tool_call_delta__mutmut_11 # type: ignore # mutmut generated
mutants_xǁLlmSseHelpersǁmerge_tool_call_delta__mutmut['xǁLlmSseHelpersǁmerge_tool_call_delta__mutmut_12'] = LlmSseHelpers.xǁLlmSseHelpersǁmerge_tool_call_delta__mutmut_12 # type: ignore # mutmut generated
mutants_xǁLlmSseHelpersǁmerge_tool_call_delta__mutmut['xǁLlmSseHelpersǁmerge_tool_call_delta__mutmut_13'] = LlmSseHelpers.xǁLlmSseHelpersǁmerge_tool_call_delta__mutmut_13 # type: ignore # mutmut generated
mutants_xǁLlmSseHelpersǁmerge_tool_call_delta__mutmut['xǁLlmSseHelpersǁmerge_tool_call_delta__mutmut_14'] = LlmSseHelpers.xǁLlmSseHelpersǁmerge_tool_call_delta__mutmut_14 # type: ignore # mutmut generated
mutants_xǁLlmSseHelpersǁmerge_tool_call_delta__mutmut['xǁLlmSseHelpersǁmerge_tool_call_delta__mutmut_15'] = LlmSseHelpers.xǁLlmSseHelpersǁmerge_tool_call_delta__mutmut_15 # type: ignore # mutmut generated
mutants_xǁLlmSseHelpersǁmerge_tool_call_delta__mutmut['xǁLlmSseHelpersǁmerge_tool_call_delta__mutmut_16'] = LlmSseHelpers.xǁLlmSseHelpersǁmerge_tool_call_delta__mutmut_16 # type: ignore # mutmut generated
mutants_xǁLlmSseHelpersǁmerge_tool_call_delta__mutmut['xǁLlmSseHelpersǁmerge_tool_call_delta__mutmut_17'] = LlmSseHelpers.xǁLlmSseHelpersǁmerge_tool_call_delta__mutmut_17 # type: ignore # mutmut generated
mutants_xǁLlmSseHelpersǁmerge_tool_call_delta__mutmut['xǁLlmSseHelpersǁmerge_tool_call_delta__mutmut_18'] = LlmSseHelpers.xǁLlmSseHelpersǁmerge_tool_call_delta__mutmut_18 # type: ignore # mutmut generated
mutants_xǁLlmSseHelpersǁmerge_tool_call_delta__mutmut['xǁLlmSseHelpersǁmerge_tool_call_delta__mutmut_19'] = LlmSseHelpers.xǁLlmSseHelpersǁmerge_tool_call_delta__mutmut_19 # type: ignore # mutmut generated
mutants_xǁLlmSseHelpersǁmerge_tool_call_delta__mutmut['xǁLlmSseHelpersǁmerge_tool_call_delta__mutmut_20'] = LlmSseHelpers.xǁLlmSseHelpersǁmerge_tool_call_delta__mutmut_20 # type: ignore # mutmut generated
mutants_xǁLlmSseHelpersǁmerge_tool_call_delta__mutmut['xǁLlmSseHelpersǁmerge_tool_call_delta__mutmut_21'] = LlmSseHelpers.xǁLlmSseHelpersǁmerge_tool_call_delta__mutmut_21 # type: ignore # mutmut generated
mutants_xǁLlmSseHelpersǁmerge_tool_call_delta__mutmut['xǁLlmSseHelpersǁmerge_tool_call_delta__mutmut_22'] = LlmSseHelpers.xǁLlmSseHelpersǁmerge_tool_call_delta__mutmut_22 # type: ignore # mutmut generated
mutants_xǁLlmSseHelpersǁmerge_tool_call_delta__mutmut['xǁLlmSseHelpersǁmerge_tool_call_delta__mutmut_23'] = LlmSseHelpers.xǁLlmSseHelpersǁmerge_tool_call_delta__mutmut_23 # type: ignore # mutmut generated
mutants_xǁLlmSseHelpersǁmerge_tool_call_delta__mutmut['xǁLlmSseHelpersǁmerge_tool_call_delta__mutmut_24'] = LlmSseHelpers.xǁLlmSseHelpersǁmerge_tool_call_delta__mutmut_24 # type: ignore # mutmut generated
mutants_xǁLlmSseHelpersǁmerge_tool_call_delta__mutmut['xǁLlmSseHelpersǁmerge_tool_call_delta__mutmut_25'] = LlmSseHelpers.xǁLlmSseHelpersǁmerge_tool_call_delta__mutmut_25 # type: ignore # mutmut generated
mutants_xǁLlmSseHelpersǁmerge_tool_call_delta__mutmut['xǁLlmSseHelpersǁmerge_tool_call_delta__mutmut_26'] = LlmSseHelpers.xǁLlmSseHelpersǁmerge_tool_call_delta__mutmut_26 # type: ignore # mutmut generated
mutants_xǁLlmSseHelpersǁmerge_tool_call_delta__mutmut['xǁLlmSseHelpersǁmerge_tool_call_delta__mutmut_27'] = LlmSseHelpers.xǁLlmSseHelpersǁmerge_tool_call_delta__mutmut_27 # type: ignore # mutmut generated
mutants_xǁLlmSseHelpersǁmerge_tool_call_delta__mutmut['xǁLlmSseHelpersǁmerge_tool_call_delta__mutmut_28'] = LlmSseHelpers.xǁLlmSseHelpersǁmerge_tool_call_delta__mutmut_28 # type: ignore # mutmut generated
mutants_xǁLlmSseHelpersǁmerge_tool_call_delta__mutmut['xǁLlmSseHelpersǁmerge_tool_call_delta__mutmut_29'] = LlmSseHelpers.xǁLlmSseHelpersǁmerge_tool_call_delta__mutmut_29 # type: ignore # mutmut generated
mutants_xǁLlmSseHelpersǁmerge_tool_call_delta__mutmut['xǁLlmSseHelpersǁmerge_tool_call_delta__mutmut_30'] = LlmSseHelpers.xǁLlmSseHelpersǁmerge_tool_call_delta__mutmut_30 # type: ignore # mutmut generated
mutants_xǁLlmSseHelpersǁmerge_tool_call_delta__mutmut['xǁLlmSseHelpersǁmerge_tool_call_delta__mutmut_31'] = LlmSseHelpers.xǁLlmSseHelpersǁmerge_tool_call_delta__mutmut_31 # type: ignore # mutmut generated
mutants_xǁLlmSseHelpersǁmerge_tool_call_delta__mutmut['xǁLlmSseHelpersǁmerge_tool_call_delta__mutmut_32'] = LlmSseHelpers.xǁLlmSseHelpersǁmerge_tool_call_delta__mutmut_32 # type: ignore # mutmut generated
mutants_xǁLlmSseHelpersǁmerge_tool_call_delta__mutmut['xǁLlmSseHelpersǁmerge_tool_call_delta__mutmut_33'] = LlmSseHelpers.xǁLlmSseHelpersǁmerge_tool_call_delta__mutmut_33 # type: ignore # mutmut generated
mutants_xǁLlmSseHelpersǁmerge_tool_call_delta__mutmut['xǁLlmSseHelpersǁmerge_tool_call_delta__mutmut_34'] = LlmSseHelpers.xǁLlmSseHelpersǁmerge_tool_call_delta__mutmut_34 # type: ignore # mutmut generated
mutants_xǁLlmSseHelpersǁmerge_tool_call_delta__mutmut['xǁLlmSseHelpersǁmerge_tool_call_delta__mutmut_35'] = LlmSseHelpers.xǁLlmSseHelpersǁmerge_tool_call_delta__mutmut_35 # type: ignore # mutmut generated
mutants_xǁLlmSseHelpersǁmerge_tool_call_delta__mutmut['xǁLlmSseHelpersǁmerge_tool_call_delta__mutmut_36'] = LlmSseHelpers.xǁLlmSseHelpersǁmerge_tool_call_delta__mutmut_36 # type: ignore # mutmut generated
mutants_xǁLlmSseHelpersǁmerge_tool_call_delta__mutmut['xǁLlmSseHelpersǁmerge_tool_call_delta__mutmut_37'] = LlmSseHelpers.xǁLlmSseHelpersǁmerge_tool_call_delta__mutmut_37 # type: ignore # mutmut generated
mutants_xǁLlmSseHelpersǁmerge_tool_call_delta__mutmut['xǁLlmSseHelpersǁmerge_tool_call_delta__mutmut_38'] = LlmSseHelpers.xǁLlmSseHelpersǁmerge_tool_call_delta__mutmut_38 # type: ignore # mutmut generated
mutants_xǁLlmSseHelpersǁmerge_tool_call_delta__mutmut['xǁLlmSseHelpersǁmerge_tool_call_delta__mutmut_39'] = LlmSseHelpers.xǁLlmSseHelpersǁmerge_tool_call_delta__mutmut_39 # type: ignore # mutmut generated
mutants_xǁLlmSseHelpersǁmerge_tool_call_delta__mutmut['xǁLlmSseHelpersǁmerge_tool_call_delta__mutmut_40'] = LlmSseHelpers.xǁLlmSseHelpersǁmerge_tool_call_delta__mutmut_40 # type: ignore # mutmut generated
mutants_xǁLlmSseHelpersǁmerge_tool_call_delta__mutmut['xǁLlmSseHelpersǁmerge_tool_call_delta__mutmut_41'] = LlmSseHelpers.xǁLlmSseHelpersǁmerge_tool_call_delta__mutmut_41 # type: ignore # mutmut generated
mutants_xǁLlmSseHelpersǁmerge_tool_call_delta__mutmut['xǁLlmSseHelpersǁmerge_tool_call_delta__mutmut_42'] = LlmSseHelpers.xǁLlmSseHelpersǁmerge_tool_call_delta__mutmut_42 # type: ignore # mutmut generated
mutants_xǁLlmSseHelpersǁmerge_tool_call_delta__mutmut['xǁLlmSseHelpersǁmerge_tool_call_delta__mutmut_43'] = LlmSseHelpers.xǁLlmSseHelpersǁmerge_tool_call_delta__mutmut_43 # type: ignore # mutmut generated
mutants_xǁLlmSseHelpersǁmerge_tool_call_delta__mutmut['xǁLlmSseHelpersǁmerge_tool_call_delta__mutmut_44'] = LlmSseHelpers.xǁLlmSseHelpersǁmerge_tool_call_delta__mutmut_44 # type: ignore # mutmut generated
mutants_xǁLlmSseHelpersǁmerge_tool_call_delta__mutmut['xǁLlmSseHelpersǁmerge_tool_call_delta__mutmut_45'] = LlmSseHelpers.xǁLlmSseHelpersǁmerge_tool_call_delta__mutmut_45 # type: ignore # mutmut generated
mutants_xǁLlmSseHelpersǁmerge_tool_call_delta__mutmut['xǁLlmSseHelpersǁmerge_tool_call_delta__mutmut_46'] = LlmSseHelpers.xǁLlmSseHelpersǁmerge_tool_call_delta__mutmut_46 # type: ignore # mutmut generated
mutants_xǁLlmSseHelpersǁmerge_tool_call_delta__mutmut['xǁLlmSseHelpersǁmerge_tool_call_delta__mutmut_47'] = LlmSseHelpers.xǁLlmSseHelpersǁmerge_tool_call_delta__mutmut_47 # type: ignore # mutmut generated
mutants_xǁLlmSseHelpersǁmerge_tool_call_delta__mutmut['xǁLlmSseHelpersǁmerge_tool_call_delta__mutmut_48'] = LlmSseHelpers.xǁLlmSseHelpersǁmerge_tool_call_delta__mutmut_48 # type: ignore # mutmut generated
mutants_xǁLlmSseHelpersǁmerge_tool_call_delta__mutmut['xǁLlmSseHelpersǁmerge_tool_call_delta__mutmut_49'] = LlmSseHelpers.xǁLlmSseHelpersǁmerge_tool_call_delta__mutmut_49 # type: ignore # mutmut generated
mutants_xǁLlmSseHelpersǁmerge_tool_call_delta__mutmut['xǁLlmSseHelpersǁmerge_tool_call_delta__mutmut_50'] = LlmSseHelpers.xǁLlmSseHelpersǁmerge_tool_call_delta__mutmut_50 # type: ignore # mutmut generated
mutants_xǁLlmSseHelpersǁmerge_tool_call_delta__mutmut['xǁLlmSseHelpersǁmerge_tool_call_delta__mutmut_51'] = LlmSseHelpers.xǁLlmSseHelpersǁmerge_tool_call_delta__mutmut_51 # type: ignore # mutmut generated
mutants_xǁLlmSseHelpersǁmerge_tool_call_delta__mutmut['xǁLlmSseHelpersǁmerge_tool_call_delta__mutmut_52'] = LlmSseHelpers.xǁLlmSseHelpersǁmerge_tool_call_delta__mutmut_52 # type: ignore # mutmut generated
mutants_xǁLlmSseHelpersǁmerge_tool_call_delta__mutmut['xǁLlmSseHelpersǁmerge_tool_call_delta__mutmut_53'] = LlmSseHelpers.xǁLlmSseHelpersǁmerge_tool_call_delta__mutmut_53 # type: ignore # mutmut generated
mutants_xǁLlmSseHelpersǁmerge_tool_call_delta__mutmut['xǁLlmSseHelpersǁmerge_tool_call_delta__mutmut_54'] = LlmSseHelpers.xǁLlmSseHelpersǁmerge_tool_call_delta__mutmut_54 # type: ignore # mutmut generated
mutants_xǁLlmSseHelpersǁmerge_tool_call_delta__mutmut['xǁLlmSseHelpersǁmerge_tool_call_delta__mutmut_55'] = LlmSseHelpers.xǁLlmSseHelpersǁmerge_tool_call_delta__mutmut_55 # type: ignore # mutmut generated
mutants_xǁLlmSseHelpersǁmerge_tool_call_delta__mutmut['xǁLlmSseHelpersǁmerge_tool_call_delta__mutmut_56'] = LlmSseHelpers.xǁLlmSseHelpersǁmerge_tool_call_delta__mutmut_56 # type: ignore # mutmut generated
mutants_xǁLlmSseHelpersǁmerge_tool_call_delta__mutmut['xǁLlmSseHelpersǁmerge_tool_call_delta__mutmut_57'] = LlmSseHelpers.xǁLlmSseHelpersǁmerge_tool_call_delta__mutmut_57 # type: ignore # mutmut generated
mutants_xǁLlmSseHelpersǁmerge_tool_call_delta__mutmut['xǁLlmSseHelpersǁmerge_tool_call_delta__mutmut_58'] = LlmSseHelpers.xǁLlmSseHelpersǁmerge_tool_call_delta__mutmut_58 # type: ignore # mutmut generated
mutants_xǁLlmSseHelpersǁmerge_tool_call_delta__mutmut['xǁLlmSseHelpersǁmerge_tool_call_delta__mutmut_59'] = LlmSseHelpers.xǁLlmSseHelpersǁmerge_tool_call_delta__mutmut_59 # type: ignore # mutmut generated
mutants_xǁLlmSseHelpersǁmerge_tool_call_delta__mutmut['xǁLlmSseHelpersǁmerge_tool_call_delta__mutmut_60'] = LlmSseHelpers.xǁLlmSseHelpersǁmerge_tool_call_delta__mutmut_60 # type: ignore # mutmut generated
mutants_xǁLlmSseHelpersǁmerge_tool_call_delta__mutmut['xǁLlmSseHelpersǁmerge_tool_call_delta__mutmut_61'] = LlmSseHelpers.xǁLlmSseHelpersǁmerge_tool_call_delta__mutmut_61 # type: ignore # mutmut generated
mutants_xǁLlmSseHelpersǁmerge_tool_call_delta__mutmut['xǁLlmSseHelpersǁmerge_tool_call_delta__mutmut_62'] = LlmSseHelpers.xǁLlmSseHelpersǁmerge_tool_call_delta__mutmut_62 # type: ignore # mutmut generated
mutants_xǁLlmSseHelpersǁmerge_tool_call_delta__mutmut['xǁLlmSseHelpersǁmerge_tool_call_delta__mutmut_63'] = LlmSseHelpers.xǁLlmSseHelpersǁmerge_tool_call_delta__mutmut_63 # type: ignore # mutmut generated
mutants_xǁLlmSseHelpersǁmerge_tool_call_delta__mutmut['xǁLlmSseHelpersǁmerge_tool_call_delta__mutmut_64'] = LlmSseHelpers.xǁLlmSseHelpersǁmerge_tool_call_delta__mutmut_64 # type: ignore # mutmut generated
mutants_xǁLlmSseHelpersǁmerge_tool_call_delta__mutmut['xǁLlmSseHelpersǁmerge_tool_call_delta__mutmut_65'] = LlmSseHelpers.xǁLlmSseHelpersǁmerge_tool_call_delta__mutmut_65 # type: ignore # mutmut generated
mutants_xǁLlmSseHelpersǁmerge_tool_call_delta__mutmut['xǁLlmSseHelpersǁmerge_tool_call_delta__mutmut_66'] = LlmSseHelpers.xǁLlmSseHelpersǁmerge_tool_call_delta__mutmut_66 # type: ignore # mutmut generated
mutants_xǁLlmSseHelpersǁmerge_tool_call_delta__mutmut['xǁLlmSseHelpersǁmerge_tool_call_delta__mutmut_67'] = LlmSseHelpers.xǁLlmSseHelpersǁmerge_tool_call_delta__mutmut_67 # type: ignore # mutmut generated
mutants_xǁLlmSseHelpersǁmerge_tool_call_delta__mutmut['xǁLlmSseHelpersǁmerge_tool_call_delta__mutmut_68'] = LlmSseHelpers.xǁLlmSseHelpersǁmerge_tool_call_delta__mutmut_68 # type: ignore # mutmut generated
mutants_xǁLlmSseHelpersǁmerge_tool_call_delta__mutmut['xǁLlmSseHelpersǁmerge_tool_call_delta__mutmut_69'] = LlmSseHelpers.xǁLlmSseHelpersǁmerge_tool_call_delta__mutmut_69 # type: ignore # mutmut generated
mutants_xǁLlmSseHelpersǁmerge_tool_call_delta__mutmut['xǁLlmSseHelpersǁmerge_tool_call_delta__mutmut_70'] = LlmSseHelpers.xǁLlmSseHelpersǁmerge_tool_call_delta__mutmut_70 # type: ignore # mutmut generated

mutants_xǁLlmSseHelpersǁbuild_stream_response__mutmut['_mutmut_orig'] = LlmSseHelpers.xǁLlmSseHelpersǁbuild_stream_response__mutmut_orig # type: ignore # mutmut generated
mutants_xǁLlmSseHelpersǁbuild_stream_response__mutmut['xǁLlmSseHelpersǁbuild_stream_response__mutmut_1'] = LlmSseHelpers.xǁLlmSseHelpersǁbuild_stream_response__mutmut_1 # type: ignore # mutmut generated
mutants_xǁLlmSseHelpersǁbuild_stream_response__mutmut['xǁLlmSseHelpersǁbuild_stream_response__mutmut_2'] = LlmSseHelpers.xǁLlmSseHelpersǁbuild_stream_response__mutmut_2 # type: ignore # mutmut generated
mutants_xǁLlmSseHelpersǁbuild_stream_response__mutmut['xǁLlmSseHelpersǁbuild_stream_response__mutmut_3'] = LlmSseHelpers.xǁLlmSseHelpersǁbuild_stream_response__mutmut_3 # type: ignore # mutmut generated
mutants_xǁLlmSseHelpersǁbuild_stream_response__mutmut['xǁLlmSseHelpersǁbuild_stream_response__mutmut_4'] = LlmSseHelpers.xǁLlmSseHelpersǁbuild_stream_response__mutmut_4 # type: ignore # mutmut generated
mutants_xǁLlmSseHelpersǁbuild_stream_response__mutmut['xǁLlmSseHelpersǁbuild_stream_response__mutmut_5'] = LlmSseHelpers.xǁLlmSseHelpersǁbuild_stream_response__mutmut_5 # type: ignore # mutmut generated
mutants_xǁLlmSseHelpersǁbuild_stream_response__mutmut['xǁLlmSseHelpersǁbuild_stream_response__mutmut_6'] = LlmSseHelpers.xǁLlmSseHelpersǁbuild_stream_response__mutmut_6 # type: ignore # mutmut generated
mutants_xǁLlmSseHelpersǁbuild_stream_response__mutmut['xǁLlmSseHelpersǁbuild_stream_response__mutmut_7'] = LlmSseHelpers.xǁLlmSseHelpersǁbuild_stream_response__mutmut_7 # type: ignore # mutmut generated
mutants_xǁLlmSseHelpersǁbuild_stream_response__mutmut['xǁLlmSseHelpersǁbuild_stream_response__mutmut_8'] = LlmSseHelpers.xǁLlmSseHelpersǁbuild_stream_response__mutmut_8 # type: ignore # mutmut generated
mutants_xǁLlmSseHelpersǁbuild_stream_response__mutmut['xǁLlmSseHelpersǁbuild_stream_response__mutmut_9'] = LlmSseHelpers.xǁLlmSseHelpersǁbuild_stream_response__mutmut_9 # type: ignore # mutmut generated
mutants_xǁLlmSseHelpersǁbuild_stream_response__mutmut['xǁLlmSseHelpersǁbuild_stream_response__mutmut_10'] = LlmSseHelpers.xǁLlmSseHelpersǁbuild_stream_response__mutmut_10 # type: ignore # mutmut generated
mutants_xǁLlmSseHelpersǁbuild_stream_response__mutmut['xǁLlmSseHelpersǁbuild_stream_response__mutmut_11'] = LlmSseHelpers.xǁLlmSseHelpersǁbuild_stream_response__mutmut_11 # type: ignore # mutmut generated
mutants_xǁLlmSseHelpersǁbuild_stream_response__mutmut['xǁLlmSseHelpersǁbuild_stream_response__mutmut_12'] = LlmSseHelpers.xǁLlmSseHelpersǁbuild_stream_response__mutmut_12 # type: ignore # mutmut generated
mutants_xǁLlmSseHelpersǁbuild_stream_response__mutmut['xǁLlmSseHelpersǁbuild_stream_response__mutmut_13'] = LlmSseHelpers.xǁLlmSseHelpersǁbuild_stream_response__mutmut_13 # type: ignore # mutmut generated
mutants_xǁLlmSseHelpersǁbuild_stream_response__mutmut['xǁLlmSseHelpersǁbuild_stream_response__mutmut_14'] = LlmSseHelpers.xǁLlmSseHelpersǁbuild_stream_response__mutmut_14 # type: ignore # mutmut generated
mutants_xǁLlmSseHelpersǁbuild_stream_response__mutmut['xǁLlmSseHelpersǁbuild_stream_response__mutmut_15'] = LlmSseHelpers.xǁLlmSseHelpersǁbuild_stream_response__mutmut_15 # type: ignore # mutmut generated
mutants_xǁLlmSseHelpersǁbuild_stream_response__mutmut['xǁLlmSseHelpersǁbuild_stream_response__mutmut_16'] = LlmSseHelpers.xǁLlmSseHelpersǁbuild_stream_response__mutmut_16 # type: ignore # mutmut generated
mutants_xǁLlmSseHelpersǁbuild_stream_response__mutmut['xǁLlmSseHelpersǁbuild_stream_response__mutmut_17'] = LlmSseHelpers.xǁLlmSseHelpersǁbuild_stream_response__mutmut_17 # type: ignore # mutmut generated
mutants_xǁLlmSseHelpersǁbuild_stream_response__mutmut['xǁLlmSseHelpersǁbuild_stream_response__mutmut_18'] = LlmSseHelpers.xǁLlmSseHelpersǁbuild_stream_response__mutmut_18 # type: ignore # mutmut generated
mutants_xǁLlmSseHelpersǁbuild_stream_response__mutmut['xǁLlmSseHelpersǁbuild_stream_response__mutmut_19'] = LlmSseHelpers.xǁLlmSseHelpersǁbuild_stream_response__mutmut_19 # type: ignore # mutmut generated
mutants_xǁLlmSseHelpersǁbuild_stream_response__mutmut['xǁLlmSseHelpersǁbuild_stream_response__mutmut_20'] = LlmSseHelpers.xǁLlmSseHelpersǁbuild_stream_response__mutmut_20 # type: ignore # mutmut generated
mutants_xǁLlmSseHelpersǁbuild_stream_response__mutmut['xǁLlmSseHelpersǁbuild_stream_response__mutmut_21'] = LlmSseHelpers.xǁLlmSseHelpersǁbuild_stream_response__mutmut_21 # type: ignore # mutmut generated

mutants_xǁLlmSseHelpersǁprocess_sse_chunk__mutmut['_mutmut_orig'] = LlmSseHelpers.xǁLlmSseHelpersǁprocess_sse_chunk__mutmut_orig # type: ignore # mutmut generated
mutants_xǁLlmSseHelpersǁprocess_sse_chunk__mutmut['xǁLlmSseHelpersǁprocess_sse_chunk__mutmut_1'] = LlmSseHelpers.xǁLlmSseHelpersǁprocess_sse_chunk__mutmut_1 # type: ignore # mutmut generated
mutants_xǁLlmSseHelpersǁprocess_sse_chunk__mutmut['xǁLlmSseHelpersǁprocess_sse_chunk__mutmut_2'] = LlmSseHelpers.xǁLlmSseHelpersǁprocess_sse_chunk__mutmut_2 # type: ignore # mutmut generated
mutants_xǁLlmSseHelpersǁprocess_sse_chunk__mutmut['xǁLlmSseHelpersǁprocess_sse_chunk__mutmut_3'] = LlmSseHelpers.xǁLlmSseHelpersǁprocess_sse_chunk__mutmut_3 # type: ignore # mutmut generated
mutants_xǁLlmSseHelpersǁprocess_sse_chunk__mutmut['xǁLlmSseHelpersǁprocess_sse_chunk__mutmut_4'] = LlmSseHelpers.xǁLlmSseHelpersǁprocess_sse_chunk__mutmut_4 # type: ignore # mutmut generated
mutants_xǁLlmSseHelpersǁprocess_sse_chunk__mutmut['xǁLlmSseHelpersǁprocess_sse_chunk__mutmut_5'] = LlmSseHelpers.xǁLlmSseHelpersǁprocess_sse_chunk__mutmut_5 # type: ignore # mutmut generated
mutants_xǁLlmSseHelpersǁprocess_sse_chunk__mutmut['xǁLlmSseHelpersǁprocess_sse_chunk__mutmut_6'] = LlmSseHelpers.xǁLlmSseHelpersǁprocess_sse_chunk__mutmut_6 # type: ignore # mutmut generated
mutants_xǁLlmSseHelpersǁprocess_sse_chunk__mutmut['xǁLlmSseHelpersǁprocess_sse_chunk__mutmut_7'] = LlmSseHelpers.xǁLlmSseHelpersǁprocess_sse_chunk__mutmut_7 # type: ignore # mutmut generated
mutants_xǁLlmSseHelpersǁprocess_sse_chunk__mutmut['xǁLlmSseHelpersǁprocess_sse_chunk__mutmut_8'] = LlmSseHelpers.xǁLlmSseHelpersǁprocess_sse_chunk__mutmut_8 # type: ignore # mutmut generated
mutants_xǁLlmSseHelpersǁprocess_sse_chunk__mutmut['xǁLlmSseHelpersǁprocess_sse_chunk__mutmut_9'] = LlmSseHelpers.xǁLlmSseHelpersǁprocess_sse_chunk__mutmut_9 # type: ignore # mutmut generated
mutants_xǁLlmSseHelpersǁprocess_sse_chunk__mutmut['xǁLlmSseHelpersǁprocess_sse_chunk__mutmut_10'] = LlmSseHelpers.xǁLlmSseHelpersǁprocess_sse_chunk__mutmut_10 # type: ignore # mutmut generated
mutants_xǁLlmSseHelpersǁprocess_sse_chunk__mutmut['xǁLlmSseHelpersǁprocess_sse_chunk__mutmut_11'] = LlmSseHelpers.xǁLlmSseHelpersǁprocess_sse_chunk__mutmut_11 # type: ignore # mutmut generated
mutants_xǁLlmSseHelpersǁprocess_sse_chunk__mutmut['xǁLlmSseHelpersǁprocess_sse_chunk__mutmut_12'] = LlmSseHelpers.xǁLlmSseHelpersǁprocess_sse_chunk__mutmut_12 # type: ignore # mutmut generated
mutants_xǁLlmSseHelpersǁprocess_sse_chunk__mutmut['xǁLlmSseHelpersǁprocess_sse_chunk__mutmut_13'] = LlmSseHelpers.xǁLlmSseHelpersǁprocess_sse_chunk__mutmut_13 # type: ignore # mutmut generated
mutants_xǁLlmSseHelpersǁprocess_sse_chunk__mutmut['xǁLlmSseHelpersǁprocess_sse_chunk__mutmut_14'] = LlmSseHelpers.xǁLlmSseHelpersǁprocess_sse_chunk__mutmut_14 # type: ignore # mutmut generated
mutants_xǁLlmSseHelpersǁprocess_sse_chunk__mutmut['xǁLlmSseHelpersǁprocess_sse_chunk__mutmut_15'] = LlmSseHelpers.xǁLlmSseHelpersǁprocess_sse_chunk__mutmut_15 # type: ignore # mutmut generated
mutants_xǁLlmSseHelpersǁprocess_sse_chunk__mutmut['xǁLlmSseHelpersǁprocess_sse_chunk__mutmut_16'] = LlmSseHelpers.xǁLlmSseHelpersǁprocess_sse_chunk__mutmut_16 # type: ignore # mutmut generated
mutants_xǁLlmSseHelpersǁprocess_sse_chunk__mutmut['xǁLlmSseHelpersǁprocess_sse_chunk__mutmut_17'] = LlmSseHelpers.xǁLlmSseHelpersǁprocess_sse_chunk__mutmut_17 # type: ignore # mutmut generated
mutants_xǁLlmSseHelpersǁprocess_sse_chunk__mutmut['xǁLlmSseHelpersǁprocess_sse_chunk__mutmut_18'] = LlmSseHelpers.xǁLlmSseHelpersǁprocess_sse_chunk__mutmut_18 # type: ignore # mutmut generated
mutants_xǁLlmSseHelpersǁprocess_sse_chunk__mutmut['xǁLlmSseHelpersǁprocess_sse_chunk__mutmut_19'] = LlmSseHelpers.xǁLlmSseHelpersǁprocess_sse_chunk__mutmut_19 # type: ignore # mutmut generated
mutants_xǁLlmSseHelpersǁprocess_sse_chunk__mutmut['xǁLlmSseHelpersǁprocess_sse_chunk__mutmut_20'] = LlmSseHelpers.xǁLlmSseHelpersǁprocess_sse_chunk__mutmut_20 # type: ignore # mutmut generated
mutants_xǁLlmSseHelpersǁprocess_sse_chunk__mutmut['xǁLlmSseHelpersǁprocess_sse_chunk__mutmut_21'] = LlmSseHelpers.xǁLlmSseHelpersǁprocess_sse_chunk__mutmut_21 # type: ignore # mutmut generated
mutants_xǁLlmSseHelpersǁprocess_sse_chunk__mutmut['xǁLlmSseHelpersǁprocess_sse_chunk__mutmut_22'] = LlmSseHelpers.xǁLlmSseHelpersǁprocess_sse_chunk__mutmut_22 # type: ignore # mutmut generated
mutants_xǁLlmSseHelpersǁprocess_sse_chunk__mutmut['xǁLlmSseHelpersǁprocess_sse_chunk__mutmut_23'] = LlmSseHelpers.xǁLlmSseHelpersǁprocess_sse_chunk__mutmut_23 # type: ignore # mutmut generated
mutants_xǁLlmSseHelpersǁprocess_sse_chunk__mutmut['xǁLlmSseHelpersǁprocess_sse_chunk__mutmut_24'] = LlmSseHelpers.xǁLlmSseHelpersǁprocess_sse_chunk__mutmut_24 # type: ignore # mutmut generated
mutants_xǁLlmSseHelpersǁprocess_sse_chunk__mutmut['xǁLlmSseHelpersǁprocess_sse_chunk__mutmut_25'] = LlmSseHelpers.xǁLlmSseHelpersǁprocess_sse_chunk__mutmut_25 # type: ignore # mutmut generated
mutants_xǁLlmSseHelpersǁprocess_sse_chunk__mutmut['xǁLlmSseHelpersǁprocess_sse_chunk__mutmut_26'] = LlmSseHelpers.xǁLlmSseHelpersǁprocess_sse_chunk__mutmut_26 # type: ignore # mutmut generated
mutants_xǁLlmSseHelpersǁprocess_sse_chunk__mutmut['xǁLlmSseHelpersǁprocess_sse_chunk__mutmut_27'] = LlmSseHelpers.xǁLlmSseHelpersǁprocess_sse_chunk__mutmut_27 # type: ignore # mutmut generated
mutants_xǁLlmSseHelpersǁprocess_sse_chunk__mutmut['xǁLlmSseHelpersǁprocess_sse_chunk__mutmut_28'] = LlmSseHelpers.xǁLlmSseHelpersǁprocess_sse_chunk__mutmut_28 # type: ignore # mutmut generated
mutants_xǁLlmSseHelpersǁprocess_sse_chunk__mutmut['xǁLlmSseHelpersǁprocess_sse_chunk__mutmut_29'] = LlmSseHelpers.xǁLlmSseHelpersǁprocess_sse_chunk__mutmut_29 # type: ignore # mutmut generated
mutants_xǁLlmSseHelpersǁprocess_sse_chunk__mutmut['xǁLlmSseHelpersǁprocess_sse_chunk__mutmut_30'] = LlmSseHelpers.xǁLlmSseHelpersǁprocess_sse_chunk__mutmut_30 # type: ignore # mutmut generated
mutants_xǁLlmSseHelpersǁprocess_sse_chunk__mutmut['xǁLlmSseHelpersǁprocess_sse_chunk__mutmut_31'] = LlmSseHelpers.xǁLlmSseHelpersǁprocess_sse_chunk__mutmut_31 # type: ignore # mutmut generated
mutants_xǁLlmSseHelpersǁprocess_sse_chunk__mutmut['xǁLlmSseHelpersǁprocess_sse_chunk__mutmut_32'] = LlmSseHelpers.xǁLlmSseHelpersǁprocess_sse_chunk__mutmut_32 # type: ignore # mutmut generated
mutants_xǁLlmSseHelpersǁprocess_sse_chunk__mutmut['xǁLlmSseHelpersǁprocess_sse_chunk__mutmut_33'] = LlmSseHelpers.xǁLlmSseHelpersǁprocess_sse_chunk__mutmut_33 # type: ignore # mutmut generated
mutants_xǁLlmSseHelpersǁprocess_sse_chunk__mutmut['xǁLlmSseHelpersǁprocess_sse_chunk__mutmut_34'] = LlmSseHelpers.xǁLlmSseHelpersǁprocess_sse_chunk__mutmut_34 # type: ignore # mutmut generated
mutants_xǁLlmSseHelpersǁprocess_sse_chunk__mutmut['xǁLlmSseHelpersǁprocess_sse_chunk__mutmut_35'] = LlmSseHelpers.xǁLlmSseHelpersǁprocess_sse_chunk__mutmut_35 # type: ignore # mutmut generated
mutants_xǁLlmSseHelpersǁprocess_sse_chunk__mutmut['xǁLlmSseHelpersǁprocess_sse_chunk__mutmut_36'] = LlmSseHelpers.xǁLlmSseHelpersǁprocess_sse_chunk__mutmut_36 # type: ignore # mutmut generated
mutants_xǁLlmSseHelpersǁprocess_sse_chunk__mutmut['xǁLlmSseHelpersǁprocess_sse_chunk__mutmut_37'] = LlmSseHelpers.xǁLlmSseHelpersǁprocess_sse_chunk__mutmut_37 # type: ignore # mutmut generated
mutants_xǁLlmSseHelpersǁprocess_sse_chunk__mutmut['xǁLlmSseHelpersǁprocess_sse_chunk__mutmut_38'] = LlmSseHelpers.xǁLlmSseHelpersǁprocess_sse_chunk__mutmut_38 # type: ignore # mutmut generated

mutants_xǁLlmSseHelpersǁprocess_sse_payloads__mutmut['_mutmut_orig'] = LlmSseHelpers.xǁLlmSseHelpersǁprocess_sse_payloads__mutmut_orig # type: ignore # mutmut generated
mutants_xǁLlmSseHelpersǁprocess_sse_payloads__mutmut['xǁLlmSseHelpersǁprocess_sse_payloads__mutmut_1'] = LlmSseHelpers.xǁLlmSseHelpersǁprocess_sse_payloads__mutmut_1 # type: ignore # mutmut generated
mutants_xǁLlmSseHelpersǁprocess_sse_payloads__mutmut['xǁLlmSseHelpersǁprocess_sse_payloads__mutmut_2'] = LlmSseHelpers.xǁLlmSseHelpersǁprocess_sse_payloads__mutmut_2 # type: ignore # mutmut generated
mutants_xǁLlmSseHelpersǁprocess_sse_payloads__mutmut['xǁLlmSseHelpersǁprocess_sse_payloads__mutmut_3'] = LlmSseHelpers.xǁLlmSseHelpersǁprocess_sse_payloads__mutmut_3 # type: ignore # mutmut generated
mutants_xǁLlmSseHelpersǁprocess_sse_payloads__mutmut['xǁLlmSseHelpersǁprocess_sse_payloads__mutmut_4'] = LlmSseHelpers.xǁLlmSseHelpersǁprocess_sse_payloads__mutmut_4 # type: ignore # mutmut generated
mutants_xǁLlmSseHelpersǁprocess_sse_payloads__mutmut['xǁLlmSseHelpersǁprocess_sse_payloads__mutmut_5'] = LlmSseHelpers.xǁLlmSseHelpersǁprocess_sse_payloads__mutmut_5 # type: ignore # mutmut generated
mutants_xǁLlmSseHelpersǁprocess_sse_payloads__mutmut['xǁLlmSseHelpersǁprocess_sse_payloads__mutmut_6'] = LlmSseHelpers.xǁLlmSseHelpersǁprocess_sse_payloads__mutmut_6 # type: ignore # mutmut generated
mutants_xǁLlmSseHelpersǁprocess_sse_payloads__mutmut['xǁLlmSseHelpersǁprocess_sse_payloads__mutmut_7'] = LlmSseHelpers.xǁLlmSseHelpersǁprocess_sse_payloads__mutmut_7 # type: ignore # mutmut generated
mutants_xǁLlmSseHelpersǁprocess_sse_payloads__mutmut['xǁLlmSseHelpersǁprocess_sse_payloads__mutmut_8'] = LlmSseHelpers.xǁLlmSseHelpersǁprocess_sse_payloads__mutmut_8 # type: ignore # mutmut generated
mutants_xǁLlmSseHelpersǁprocess_sse_payloads__mutmut['xǁLlmSseHelpersǁprocess_sse_payloads__mutmut_9'] = LlmSseHelpers.xǁLlmSseHelpersǁprocess_sse_payloads__mutmut_9 # type: ignore # mutmut generated
mutants_xǁLlmSseHelpersǁprocess_sse_payloads__mutmut['xǁLlmSseHelpersǁprocess_sse_payloads__mutmut_10'] = LlmSseHelpers.xǁLlmSseHelpersǁprocess_sse_payloads__mutmut_10 # type: ignore # mutmut generated
mutants_xǁLlmSseHelpersǁprocess_sse_payloads__mutmut['xǁLlmSseHelpersǁprocess_sse_payloads__mutmut_11'] = LlmSseHelpers.xǁLlmSseHelpersǁprocess_sse_payloads__mutmut_11 # type: ignore # mutmut generated
mutants_xǁLlmSseHelpersǁprocess_sse_payloads__mutmut['xǁLlmSseHelpersǁprocess_sse_payloads__mutmut_12'] = LlmSseHelpers.xǁLlmSseHelpersǁprocess_sse_payloads__mutmut_12 # type: ignore # mutmut generated
mutants_xǁLlmSseHelpersǁprocess_sse_payloads__mutmut['xǁLlmSseHelpersǁprocess_sse_payloads__mutmut_13'] = LlmSseHelpers.xǁLlmSseHelpersǁprocess_sse_payloads__mutmut_13 # type: ignore # mutmut generated
mutants_xǁLlmSseHelpersǁprocess_sse_payloads__mutmut['xǁLlmSseHelpersǁprocess_sse_payloads__mutmut_14'] = LlmSseHelpers.xǁLlmSseHelpersǁprocess_sse_payloads__mutmut_14 # type: ignore # mutmut generated
mutants_xǁLlmSseHelpersǁprocess_sse_payloads__mutmut['xǁLlmSseHelpersǁprocess_sse_payloads__mutmut_15'] = LlmSseHelpers.xǁLlmSseHelpersǁprocess_sse_payloads__mutmut_15 # type: ignore # mutmut generated
mutants_xǁLlmSseHelpersǁprocess_sse_payloads__mutmut['xǁLlmSseHelpersǁprocess_sse_payloads__mutmut_16'] = LlmSseHelpers.xǁLlmSseHelpersǁprocess_sse_payloads__mutmut_16 # type: ignore # mutmut generated
mutants_xǁLlmSseHelpersǁprocess_sse_payloads__mutmut['xǁLlmSseHelpersǁprocess_sse_payloads__mutmut_17'] = LlmSseHelpers.xǁLlmSseHelpersǁprocess_sse_payloads__mutmut_17 # type: ignore # mutmut generated
mutants_xǁLlmSseHelpersǁprocess_sse_payloads__mutmut['xǁLlmSseHelpersǁprocess_sse_payloads__mutmut_18'] = LlmSseHelpers.xǁLlmSseHelpersǁprocess_sse_payloads__mutmut_18 # type: ignore # mutmut generated

mutants_xǁLlmSseHelpersǁparse_usage__mutmut['_mutmut_orig'] = LlmSseHelpers.xǁLlmSseHelpersǁparse_usage__mutmut_orig # type: ignore # mutmut generated
mutants_xǁLlmSseHelpersǁparse_usage__mutmut['xǁLlmSseHelpersǁparse_usage__mutmut_1'] = LlmSseHelpers.xǁLlmSseHelpersǁparse_usage__mutmut_1 # type: ignore # mutmut generated
mutants_xǁLlmSseHelpersǁparse_usage__mutmut['xǁLlmSseHelpersǁparse_usage__mutmut_2'] = LlmSseHelpers.xǁLlmSseHelpersǁparse_usage__mutmut_2 # type: ignore # mutmut generated
mutants_xǁLlmSseHelpersǁparse_usage__mutmut['xǁLlmSseHelpersǁparse_usage__mutmut_3'] = LlmSseHelpers.xǁLlmSseHelpersǁparse_usage__mutmut_3 # type: ignore # mutmut generated
mutants_xǁLlmSseHelpersǁparse_usage__mutmut['xǁLlmSseHelpersǁparse_usage__mutmut_4'] = LlmSseHelpers.xǁLlmSseHelpersǁparse_usage__mutmut_4 # type: ignore # mutmut generated
mutants_xǁLlmSseHelpersǁparse_usage__mutmut['xǁLlmSseHelpersǁparse_usage__mutmut_5'] = LlmSseHelpers.xǁLlmSseHelpersǁparse_usage__mutmut_5 # type: ignore # mutmut generated
mutants_xǁLlmSseHelpersǁparse_usage__mutmut['xǁLlmSseHelpersǁparse_usage__mutmut_6'] = LlmSseHelpers.xǁLlmSseHelpersǁparse_usage__mutmut_6 # type: ignore # mutmut generated
mutants_xǁLlmSseHelpersǁparse_usage__mutmut['xǁLlmSseHelpersǁparse_usage__mutmut_7'] = LlmSseHelpers.xǁLlmSseHelpersǁparse_usage__mutmut_7 # type: ignore # mutmut generated
mutants_xǁLlmSseHelpersǁparse_usage__mutmut['xǁLlmSseHelpersǁparse_usage__mutmut_8'] = LlmSseHelpers.xǁLlmSseHelpersǁparse_usage__mutmut_8 # type: ignore # mutmut generated
mutants_xǁLlmSseHelpersǁparse_usage__mutmut['xǁLlmSseHelpersǁparse_usage__mutmut_9'] = LlmSseHelpers.xǁLlmSseHelpersǁparse_usage__mutmut_9 # type: ignore # mutmut generated
mutants_xǁLlmSseHelpersǁparse_usage__mutmut['xǁLlmSseHelpersǁparse_usage__mutmut_10'] = LlmSseHelpers.xǁLlmSseHelpersǁparse_usage__mutmut_10 # type: ignore # mutmut generated
mutants_xǁLlmSseHelpersǁparse_usage__mutmut['xǁLlmSseHelpersǁparse_usage__mutmut_11'] = LlmSseHelpers.xǁLlmSseHelpersǁparse_usage__mutmut_11 # type: ignore # mutmut generated
mutants_xǁLlmSseHelpersǁparse_usage__mutmut['xǁLlmSseHelpersǁparse_usage__mutmut_12'] = LlmSseHelpers.xǁLlmSseHelpersǁparse_usage__mutmut_12 # type: ignore # mutmut generated
mutants_xǁLlmSseHelpersǁparse_usage__mutmut['xǁLlmSseHelpersǁparse_usage__mutmut_13'] = LlmSseHelpers.xǁLlmSseHelpersǁparse_usage__mutmut_13 # type: ignore # mutmut generated
mutants_xǁLlmSseHelpersǁparse_usage__mutmut['xǁLlmSseHelpersǁparse_usage__mutmut_14'] = LlmSseHelpers.xǁLlmSseHelpersǁparse_usage__mutmut_14 # type: ignore # mutmut generated
mutants_xǁLlmSseHelpersǁparse_usage__mutmut['xǁLlmSseHelpersǁparse_usage__mutmut_15'] = LlmSseHelpers.xǁLlmSseHelpersǁparse_usage__mutmut_15 # type: ignore # mutmut generated
mutants_xǁLlmSseHelpersǁparse_usage__mutmut['xǁLlmSseHelpersǁparse_usage__mutmut_16'] = LlmSseHelpers.xǁLlmSseHelpersǁparse_usage__mutmut_16 # type: ignore # mutmut generated
mutants_xǁLlmSseHelpersǁparse_usage__mutmut['xǁLlmSseHelpersǁparse_usage__mutmut_17'] = LlmSseHelpers.xǁLlmSseHelpersǁparse_usage__mutmut_17 # type: ignore # mutmut generated
mutants_xǁLlmSseHelpersǁparse_usage__mutmut['xǁLlmSseHelpersǁparse_usage__mutmut_18'] = LlmSseHelpers.xǁLlmSseHelpersǁparse_usage__mutmut_18 # type: ignore # mutmut generated
mutants_xǁLlmSseHelpersǁparse_usage__mutmut['xǁLlmSseHelpersǁparse_usage__mutmut_19'] = LlmSseHelpers.xǁLlmSseHelpersǁparse_usage__mutmut_19 # type: ignore # mutmut generated
mutants_xǁLlmSseHelpersǁparse_usage__mutmut['xǁLlmSseHelpersǁparse_usage__mutmut_20'] = LlmSseHelpers.xǁLlmSseHelpersǁparse_usage__mutmut_20 # type: ignore # mutmut generated
mutants_xǁLlmSseHelpersǁparse_usage__mutmut['xǁLlmSseHelpersǁparse_usage__mutmut_21'] = LlmSseHelpers.xǁLlmSseHelpersǁparse_usage__mutmut_21 # type: ignore # mutmut generated
mutants_xǁLlmSseHelpersǁparse_usage__mutmut['xǁLlmSseHelpersǁparse_usage__mutmut_22'] = LlmSseHelpers.xǁLlmSseHelpersǁparse_usage__mutmut_22 # type: ignore # mutmut generated
mutants_xǁLlmSseHelpersǁparse_usage__mutmut['xǁLlmSseHelpersǁparse_usage__mutmut_23'] = LlmSseHelpers.xǁLlmSseHelpersǁparse_usage__mutmut_23 # type: ignore # mutmut generated
mutants_xǁLlmSseHelpersǁparse_usage__mutmut['xǁLlmSseHelpersǁparse_usage__mutmut_24'] = LlmSseHelpers.xǁLlmSseHelpersǁparse_usage__mutmut_24 # type: ignore # mutmut generated
mutants_xǁLlmSseHelpersǁparse_usage__mutmut['xǁLlmSseHelpersǁparse_usage__mutmut_25'] = LlmSseHelpers.xǁLlmSseHelpersǁparse_usage__mutmut_25 # type: ignore # mutmut generated

mutants_xǁLlmSseHelpersǁaccumulate_parse_errors__mutmut['_mutmut_orig'] = LlmSseHelpers.xǁLlmSseHelpersǁaccumulate_parse_errors__mutmut_orig # type: ignore # mutmut generated
mutants_xǁLlmSseHelpersǁaccumulate_parse_errors__mutmut['xǁLlmSseHelpersǁaccumulate_parse_errors__mutmut_1'] = LlmSseHelpers.xǁLlmSseHelpersǁaccumulate_parse_errors__mutmut_1 # type: ignore # mutmut generated
mutants_xǁLlmSseHelpersǁaccumulate_parse_errors__mutmut['xǁLlmSseHelpersǁaccumulate_parse_errors__mutmut_2'] = LlmSseHelpers.xǁLlmSseHelpersǁaccumulate_parse_errors__mutmut_2 # type: ignore # mutmut generated
mutants_xǁLlmSseHelpersǁaccumulate_parse_errors__mutmut['xǁLlmSseHelpersǁaccumulate_parse_errors__mutmut_3'] = LlmSseHelpers.xǁLlmSseHelpersǁaccumulate_parse_errors__mutmut_3 # type: ignore # mutmut generated
mutants_xǁLlmSseHelpersǁaccumulate_parse_errors__mutmut['xǁLlmSseHelpersǁaccumulate_parse_errors__mutmut_4'] = LlmSseHelpers.xǁLlmSseHelpersǁaccumulate_parse_errors__mutmut_4 # type: ignore # mutmut generated
