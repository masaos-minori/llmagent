#!/usr/bin/env python3
"""scripts/shared/sse_parser.py

Stateful SSE parser for LLM streaming responses.

Provides:
  RobustSSEParser — incremental UTF-8 decoder + heartbeat tracking + malformed frame budget
  _anext_or_done  — async iterator helper to prevent PEP 479 RuntimeError
"""

from __future__ import annotations

import codecs
import time
from collections.abc import AsyncIterator

import orjson

from shared.llm_exceptions import LLMTransportError


from mutmut.mutation.trampoline import wrap_in_trampoline as _mutmut_mutated, MutantDict
mutants_xǁRobustSSEParserǁ__init____mutmut: MutantDict = {}  # type: ignore
mutants_xǁRobustSSEParserǁfeed__mutmut: MutantDict = {}  # type: ignore
mutants_xǁRobustSSEParserǁ_parse_line__mutmut: MutantDict = {}  # type: ignore
mutants_xǁRobustSSEParserǁ_is_keepalive__mutmut: MutantDict = {}  # type: ignore
mutants_xǁRobustSSEParserǁ_mark_activity__mutmut: MutantDict = {}  # type: ignore
mutants_xǁRobustSSEParserǁ_is_valid_json__mutmut: MutantDict = {}  # type: ignore
mutants_xǁRobustSSEParserǁcheck_heartbeat__mutmut: MutantDict = {}  # type: ignore


class RobustSSEParser:
    """Stateful SSE parser: incremental UTF-8 decoder + heartbeat tracking + malformed frame budget; one instance per connection."""

    _DATA_PREFIX = "data:"

    @_mutmut_mutated(mutants_xǁRobustSSEParserǁ__init____mutmut)
    def __init__(self, malformed_retry: int, heartbeat_timeout: float) -> None:
        """Initialize with malformed retry budget and heartbeat timeout duration."""
        if malformed_retry < 0:
            raise ValueError(f"malformed_retry must be >= 0, got {malformed_retry}")
        if heartbeat_timeout < 0:
            raise ValueError(f"heartbeat_timeout must be >= 0, got {heartbeat_timeout}")
        self._decoder = codecs.getincrementaldecoder("utf-8")("replace")
        self._buf = ""
        self._malformed_retry = malformed_retry
        self._heartbeat_timeout = heartbeat_timeout
        self._last_event_at: float = time.monotonic()
        self._malformed_count: int = 0
        # Accumulated per-feed parse error count; caller resets after reading
        self.stat_parse_errors: int = 0

    def xǁRobustSSEParserǁ__init____mutmut_orig(self, malformed_retry: int, heartbeat_timeout: float) -> None:
        """Initialize with malformed retry budget and heartbeat timeout duration."""
        if malformed_retry < 0:
            raise ValueError(f"malformed_retry must be >= 0, got {malformed_retry}")
        if heartbeat_timeout < 0:
            raise ValueError(f"heartbeat_timeout must be >= 0, got {heartbeat_timeout}")
        self._decoder = codecs.getincrementaldecoder("utf-8")("replace")
        self._buf = ""
        self._malformed_retry = malformed_retry
        self._heartbeat_timeout = heartbeat_timeout
        self._last_event_at: float = time.monotonic()
        self._malformed_count: int = 0
        # Accumulated per-feed parse error count; caller resets after reading
        self.stat_parse_errors: int = 0

    def xǁRobustSSEParserǁ__init____mutmut_1(self, malformed_retry: int, heartbeat_timeout: float) -> None:
        """Initialize with malformed retry budget and heartbeat timeout duration."""
        if malformed_retry <= 0:
            raise ValueError(f"malformed_retry must be >= 0, got {malformed_retry}")
        if heartbeat_timeout < 0:
            raise ValueError(f"heartbeat_timeout must be >= 0, got {heartbeat_timeout}")
        self._decoder = codecs.getincrementaldecoder("utf-8")("replace")
        self._buf = ""
        self._malformed_retry = malformed_retry
        self._heartbeat_timeout = heartbeat_timeout
        self._last_event_at: float = time.monotonic()
        self._malformed_count: int = 0
        # Accumulated per-feed parse error count; caller resets after reading
        self.stat_parse_errors: int = 0

    def xǁRobustSSEParserǁ__init____mutmut_2(self, malformed_retry: int, heartbeat_timeout: float) -> None:
        """Initialize with malformed retry budget and heartbeat timeout duration."""
        if malformed_retry < 1:
            raise ValueError(f"malformed_retry must be >= 0, got {malformed_retry}")
        if heartbeat_timeout < 0:
            raise ValueError(f"heartbeat_timeout must be >= 0, got {heartbeat_timeout}")
        self._decoder = codecs.getincrementaldecoder("utf-8")("replace")
        self._buf = ""
        self._malformed_retry = malformed_retry
        self._heartbeat_timeout = heartbeat_timeout
        self._last_event_at: float = time.monotonic()
        self._malformed_count: int = 0
        # Accumulated per-feed parse error count; caller resets after reading
        self.stat_parse_errors: int = 0

    def xǁRobustSSEParserǁ__init____mutmut_3(self, malformed_retry: int, heartbeat_timeout: float) -> None:
        """Initialize with malformed retry budget and heartbeat timeout duration."""
        if malformed_retry < 0:
            raise ValueError(None)
        if heartbeat_timeout < 0:
            raise ValueError(f"heartbeat_timeout must be >= 0, got {heartbeat_timeout}")
        self._decoder = codecs.getincrementaldecoder("utf-8")("replace")
        self._buf = ""
        self._malformed_retry = malformed_retry
        self._heartbeat_timeout = heartbeat_timeout
        self._last_event_at: float = time.monotonic()
        self._malformed_count: int = 0
        # Accumulated per-feed parse error count; caller resets after reading
        self.stat_parse_errors: int = 0

    def xǁRobustSSEParserǁ__init____mutmut_4(self, malformed_retry: int, heartbeat_timeout: float) -> None:
        """Initialize with malformed retry budget and heartbeat timeout duration."""
        if malformed_retry < 0:
            raise ValueError(f"malformed_retry must be >= 0, got {malformed_retry}")
        if heartbeat_timeout <= 0:
            raise ValueError(f"heartbeat_timeout must be >= 0, got {heartbeat_timeout}")
        self._decoder = codecs.getincrementaldecoder("utf-8")("replace")
        self._buf = ""
        self._malformed_retry = malformed_retry
        self._heartbeat_timeout = heartbeat_timeout
        self._last_event_at: float = time.monotonic()
        self._malformed_count: int = 0
        # Accumulated per-feed parse error count; caller resets after reading
        self.stat_parse_errors: int = 0

    def xǁRobustSSEParserǁ__init____mutmut_5(self, malformed_retry: int, heartbeat_timeout: float) -> None:
        """Initialize with malformed retry budget and heartbeat timeout duration."""
        if malformed_retry < 0:
            raise ValueError(f"malformed_retry must be >= 0, got {malformed_retry}")
        if heartbeat_timeout < 1:
            raise ValueError(f"heartbeat_timeout must be >= 0, got {heartbeat_timeout}")
        self._decoder = codecs.getincrementaldecoder("utf-8")("replace")
        self._buf = ""
        self._malformed_retry = malformed_retry
        self._heartbeat_timeout = heartbeat_timeout
        self._last_event_at: float = time.monotonic()
        self._malformed_count: int = 0
        # Accumulated per-feed parse error count; caller resets after reading
        self.stat_parse_errors: int = 0

    def xǁRobustSSEParserǁ__init____mutmut_6(self, malformed_retry: int, heartbeat_timeout: float) -> None:
        """Initialize with malformed retry budget and heartbeat timeout duration."""
        if malformed_retry < 0:
            raise ValueError(f"malformed_retry must be >= 0, got {malformed_retry}")
        if heartbeat_timeout < 0:
            raise ValueError(None)
        self._decoder = codecs.getincrementaldecoder("utf-8")("replace")
        self._buf = ""
        self._malformed_retry = malformed_retry
        self._heartbeat_timeout = heartbeat_timeout
        self._last_event_at: float = time.monotonic()
        self._malformed_count: int = 0
        # Accumulated per-feed parse error count; caller resets after reading
        self.stat_parse_errors: int = 0

    def xǁRobustSSEParserǁ__init____mutmut_7(self, malformed_retry: int, heartbeat_timeout: float) -> None:
        """Initialize with malformed retry budget and heartbeat timeout duration."""
        if malformed_retry < 0:
            raise ValueError(f"malformed_retry must be >= 0, got {malformed_retry}")
        if heartbeat_timeout < 0:
            raise ValueError(f"heartbeat_timeout must be >= 0, got {heartbeat_timeout}")
        self._decoder = None
        self._buf = ""
        self._malformed_retry = malformed_retry
        self._heartbeat_timeout = heartbeat_timeout
        self._last_event_at: float = time.monotonic()
        self._malformed_count: int = 0
        # Accumulated per-feed parse error count; caller resets after reading
        self.stat_parse_errors: int = 0

    def xǁRobustSSEParserǁ__init____mutmut_8(self, malformed_retry: int, heartbeat_timeout: float) -> None:
        """Initialize with malformed retry budget and heartbeat timeout duration."""
        if malformed_retry < 0:
            raise ValueError(f"malformed_retry must be >= 0, got {malformed_retry}")
        if heartbeat_timeout < 0:
            raise ValueError(f"heartbeat_timeout must be >= 0, got {heartbeat_timeout}")
        self._decoder = codecs.getincrementaldecoder("utf-8")(None)
        self._buf = ""
        self._malformed_retry = malformed_retry
        self._heartbeat_timeout = heartbeat_timeout
        self._last_event_at: float = time.monotonic()
        self._malformed_count: int = 0
        # Accumulated per-feed parse error count; caller resets after reading
        self.stat_parse_errors: int = 0

    def xǁRobustSSEParserǁ__init____mutmut_9(self, malformed_retry: int, heartbeat_timeout: float) -> None:
        """Initialize with malformed retry budget and heartbeat timeout duration."""
        if malformed_retry < 0:
            raise ValueError(f"malformed_retry must be >= 0, got {malformed_retry}")
        if heartbeat_timeout < 0:
            raise ValueError(f"heartbeat_timeout must be >= 0, got {heartbeat_timeout}")
        self._decoder = codecs.getincrementaldecoder(None)("replace")
        self._buf = ""
        self._malformed_retry = malformed_retry
        self._heartbeat_timeout = heartbeat_timeout
        self._last_event_at: float = time.monotonic()
        self._malformed_count: int = 0
        # Accumulated per-feed parse error count; caller resets after reading
        self.stat_parse_errors: int = 0

    def xǁRobustSSEParserǁ__init____mutmut_10(self, malformed_retry: int, heartbeat_timeout: float) -> None:
        """Initialize with malformed retry budget and heartbeat timeout duration."""
        if malformed_retry < 0:
            raise ValueError(f"malformed_retry must be >= 0, got {malformed_retry}")
        if heartbeat_timeout < 0:
            raise ValueError(f"heartbeat_timeout must be >= 0, got {heartbeat_timeout}")
        self._decoder = codecs.getincrementaldecoder("XXutf-8XX")("replace")
        self._buf = ""
        self._malformed_retry = malformed_retry
        self._heartbeat_timeout = heartbeat_timeout
        self._last_event_at: float = time.monotonic()
        self._malformed_count: int = 0
        # Accumulated per-feed parse error count; caller resets after reading
        self.stat_parse_errors: int = 0

    def xǁRobustSSEParserǁ__init____mutmut_11(self, malformed_retry: int, heartbeat_timeout: float) -> None:
        """Initialize with malformed retry budget and heartbeat timeout duration."""
        if malformed_retry < 0:
            raise ValueError(f"malformed_retry must be >= 0, got {malformed_retry}")
        if heartbeat_timeout < 0:
            raise ValueError(f"heartbeat_timeout must be >= 0, got {heartbeat_timeout}")
        self._decoder = codecs.getincrementaldecoder("UTF-8")("replace")
        self._buf = ""
        self._malformed_retry = malformed_retry
        self._heartbeat_timeout = heartbeat_timeout
        self._last_event_at: float = time.monotonic()
        self._malformed_count: int = 0
        # Accumulated per-feed parse error count; caller resets after reading
        self.stat_parse_errors: int = 0

    def xǁRobustSSEParserǁ__init____mutmut_12(self, malformed_retry: int, heartbeat_timeout: float) -> None:
        """Initialize with malformed retry budget and heartbeat timeout duration."""
        if malformed_retry < 0:
            raise ValueError(f"malformed_retry must be >= 0, got {malformed_retry}")
        if heartbeat_timeout < 0:
            raise ValueError(f"heartbeat_timeout must be >= 0, got {heartbeat_timeout}")
        self._decoder = codecs.getincrementaldecoder("utf-8")("XXreplaceXX")
        self._buf = ""
        self._malformed_retry = malformed_retry
        self._heartbeat_timeout = heartbeat_timeout
        self._last_event_at: float = time.monotonic()
        self._malformed_count: int = 0
        # Accumulated per-feed parse error count; caller resets after reading
        self.stat_parse_errors: int = 0

    def xǁRobustSSEParserǁ__init____mutmut_13(self, malformed_retry: int, heartbeat_timeout: float) -> None:
        """Initialize with malformed retry budget and heartbeat timeout duration."""
        if malformed_retry < 0:
            raise ValueError(f"malformed_retry must be >= 0, got {malformed_retry}")
        if heartbeat_timeout < 0:
            raise ValueError(f"heartbeat_timeout must be >= 0, got {heartbeat_timeout}")
        self._decoder = codecs.getincrementaldecoder("utf-8")("REPLACE")
        self._buf = ""
        self._malformed_retry = malformed_retry
        self._heartbeat_timeout = heartbeat_timeout
        self._last_event_at: float = time.monotonic()
        self._malformed_count: int = 0
        # Accumulated per-feed parse error count; caller resets after reading
        self.stat_parse_errors: int = 0

    def xǁRobustSSEParserǁ__init____mutmut_14(self, malformed_retry: int, heartbeat_timeout: float) -> None:
        """Initialize with malformed retry budget and heartbeat timeout duration."""
        if malformed_retry < 0:
            raise ValueError(f"malformed_retry must be >= 0, got {malformed_retry}")
        if heartbeat_timeout < 0:
            raise ValueError(f"heartbeat_timeout must be >= 0, got {heartbeat_timeout}")
        self._decoder = codecs.getincrementaldecoder("utf-8")("replace")
        self._buf = None
        self._malformed_retry = malformed_retry
        self._heartbeat_timeout = heartbeat_timeout
        self._last_event_at: float = time.monotonic()
        self._malformed_count: int = 0
        # Accumulated per-feed parse error count; caller resets after reading
        self.stat_parse_errors: int = 0

    def xǁRobustSSEParserǁ__init____mutmut_15(self, malformed_retry: int, heartbeat_timeout: float) -> None:
        """Initialize with malformed retry budget and heartbeat timeout duration."""
        if malformed_retry < 0:
            raise ValueError(f"malformed_retry must be >= 0, got {malformed_retry}")
        if heartbeat_timeout < 0:
            raise ValueError(f"heartbeat_timeout must be >= 0, got {heartbeat_timeout}")
        self._decoder = codecs.getincrementaldecoder("utf-8")("replace")
        self._buf = "XXXX"
        self._malformed_retry = malformed_retry
        self._heartbeat_timeout = heartbeat_timeout
        self._last_event_at: float = time.monotonic()
        self._malformed_count: int = 0
        # Accumulated per-feed parse error count; caller resets after reading
        self.stat_parse_errors: int = 0

    def xǁRobustSSEParserǁ__init____mutmut_16(self, malformed_retry: int, heartbeat_timeout: float) -> None:
        """Initialize with malformed retry budget and heartbeat timeout duration."""
        if malformed_retry < 0:
            raise ValueError(f"malformed_retry must be >= 0, got {malformed_retry}")
        if heartbeat_timeout < 0:
            raise ValueError(f"heartbeat_timeout must be >= 0, got {heartbeat_timeout}")
        self._decoder = codecs.getincrementaldecoder("utf-8")("replace")
        self._buf = ""
        self._malformed_retry = None
        self._heartbeat_timeout = heartbeat_timeout
        self._last_event_at: float = time.monotonic()
        self._malformed_count: int = 0
        # Accumulated per-feed parse error count; caller resets after reading
        self.stat_parse_errors: int = 0

    def xǁRobustSSEParserǁ__init____mutmut_17(self, malformed_retry: int, heartbeat_timeout: float) -> None:
        """Initialize with malformed retry budget and heartbeat timeout duration."""
        if malformed_retry < 0:
            raise ValueError(f"malformed_retry must be >= 0, got {malformed_retry}")
        if heartbeat_timeout < 0:
            raise ValueError(f"heartbeat_timeout must be >= 0, got {heartbeat_timeout}")
        self._decoder = codecs.getincrementaldecoder("utf-8")("replace")
        self._buf = ""
        self._malformed_retry = malformed_retry
        self._heartbeat_timeout = None
        self._last_event_at: float = time.monotonic()
        self._malformed_count: int = 0
        # Accumulated per-feed parse error count; caller resets after reading
        self.stat_parse_errors: int = 0

    def xǁRobustSSEParserǁ__init____mutmut_18(self, malformed_retry: int, heartbeat_timeout: float) -> None:
        """Initialize with malformed retry budget and heartbeat timeout duration."""
        if malformed_retry < 0:
            raise ValueError(f"malformed_retry must be >= 0, got {malformed_retry}")
        if heartbeat_timeout < 0:
            raise ValueError(f"heartbeat_timeout must be >= 0, got {heartbeat_timeout}")
        self._decoder = codecs.getincrementaldecoder("utf-8")("replace")
        self._buf = ""
        self._malformed_retry = malformed_retry
        self._heartbeat_timeout = heartbeat_timeout
        self._last_event_at: float = None
        self._malformed_count: int = 0
        # Accumulated per-feed parse error count; caller resets after reading
        self.stat_parse_errors: int = 0

    def xǁRobustSSEParserǁ__init____mutmut_19(self, malformed_retry: int, heartbeat_timeout: float) -> None:
        """Initialize with malformed retry budget and heartbeat timeout duration."""
        if malformed_retry < 0:
            raise ValueError(f"malformed_retry must be >= 0, got {malformed_retry}")
        if heartbeat_timeout < 0:
            raise ValueError(f"heartbeat_timeout must be >= 0, got {heartbeat_timeout}")
        self._decoder = codecs.getincrementaldecoder("utf-8")("replace")
        self._buf = ""
        self._malformed_retry = malformed_retry
        self._heartbeat_timeout = heartbeat_timeout
        self._last_event_at: float = time.monotonic()
        self._malformed_count: int = None
        # Accumulated per-feed parse error count; caller resets after reading
        self.stat_parse_errors: int = 0

    def xǁRobustSSEParserǁ__init____mutmut_20(self, malformed_retry: int, heartbeat_timeout: float) -> None:
        """Initialize with malformed retry budget and heartbeat timeout duration."""
        if malformed_retry < 0:
            raise ValueError(f"malformed_retry must be >= 0, got {malformed_retry}")
        if heartbeat_timeout < 0:
            raise ValueError(f"heartbeat_timeout must be >= 0, got {heartbeat_timeout}")
        self._decoder = codecs.getincrementaldecoder("utf-8")("replace")
        self._buf = ""
        self._malformed_retry = malformed_retry
        self._heartbeat_timeout = heartbeat_timeout
        self._last_event_at: float = time.monotonic()
        self._malformed_count: int = 1
        # Accumulated per-feed parse error count; caller resets after reading
        self.stat_parse_errors: int = 0

    def xǁRobustSSEParserǁ__init____mutmut_21(self, malformed_retry: int, heartbeat_timeout: float) -> None:
        """Initialize with malformed retry budget and heartbeat timeout duration."""
        if malformed_retry < 0:
            raise ValueError(f"malformed_retry must be >= 0, got {malformed_retry}")
        if heartbeat_timeout < 0:
            raise ValueError(f"heartbeat_timeout must be >= 0, got {heartbeat_timeout}")
        self._decoder = codecs.getincrementaldecoder("utf-8")("replace")
        self._buf = ""
        self._malformed_retry = malformed_retry
        self._heartbeat_timeout = heartbeat_timeout
        self._last_event_at: float = time.monotonic()
        self._malformed_count: int = 0
        # Accumulated per-feed parse error count; caller resets after reading
        self.stat_parse_errors: int = None

    def xǁRobustSSEParserǁ__init____mutmut_22(self, malformed_retry: int, heartbeat_timeout: float) -> None:
        """Initialize with malformed retry budget and heartbeat timeout duration."""
        if malformed_retry < 0:
            raise ValueError(f"malformed_retry must be >= 0, got {malformed_retry}")
        if heartbeat_timeout < 0:
            raise ValueError(f"heartbeat_timeout must be >= 0, got {heartbeat_timeout}")
        self._decoder = codecs.getincrementaldecoder("utf-8")("replace")
        self._buf = ""
        self._malformed_retry = malformed_retry
        self._heartbeat_timeout = heartbeat_timeout
        self._last_event_at: float = time.monotonic()
        self._malformed_count: int = 0
        # Accumulated per-feed parse error count; caller resets after reading
        self.stat_parse_errors: int = 1

    @_mutmut_mutated(mutants_xǁRobustSSEParserǁfeed__mutmut)
    def feed(self, raw: bytes) -> tuple[list[str], bool]:
        """Decode raw bytes and extract complete SSE data payloads; returns (payloads, is_done); raises MALFORMED_SSE_FRAME after malformed budget exhausted."""
        text = self._decoder.decode(raw, final=False)
        self._buf += text
        payloads: list[str] = []
        is_done = False
        while "\n" in self._buf:
            line, self._buf = self._buf.split("\n", 1)
            line = line.rstrip("\r")
            result = self._parse_line(line)
            if result is None:
                continue
            payload, done = result
            if done:
                is_done = True
                break
            if payload is not None:
                payloads.append(payload)
        return payloads, is_done

    def xǁRobustSSEParserǁfeed__mutmut_orig(self, raw: bytes) -> tuple[list[str], bool]:
        """Decode raw bytes and extract complete SSE data payloads; returns (payloads, is_done); raises MALFORMED_SSE_FRAME after malformed budget exhausted."""
        text = self._decoder.decode(raw, final=False)
        self._buf += text
        payloads: list[str] = []
        is_done = False
        while "\n" in self._buf:
            line, self._buf = self._buf.split("\n", 1)
            line = line.rstrip("\r")
            result = self._parse_line(line)
            if result is None:
                continue
            payload, done = result
            if done:
                is_done = True
                break
            if payload is not None:
                payloads.append(payload)
        return payloads, is_done

    def xǁRobustSSEParserǁfeed__mutmut_1(self, raw: bytes) -> tuple[list[str], bool]:
        """Decode raw bytes and extract complete SSE data payloads; returns (payloads, is_done); raises MALFORMED_SSE_FRAME after malformed budget exhausted."""
        text = None
        self._buf += text
        payloads: list[str] = []
        is_done = False
        while "\n" in self._buf:
            line, self._buf = self._buf.split("\n", 1)
            line = line.rstrip("\r")
            result = self._parse_line(line)
            if result is None:
                continue
            payload, done = result
            if done:
                is_done = True
                break
            if payload is not None:
                payloads.append(payload)
        return payloads, is_done

    def xǁRobustSSEParserǁfeed__mutmut_2(self, raw: bytes) -> tuple[list[str], bool]:
        """Decode raw bytes and extract complete SSE data payloads; returns (payloads, is_done); raises MALFORMED_SSE_FRAME after malformed budget exhausted."""
        text = self._decoder.decode(None, final=False)
        self._buf += text
        payloads: list[str] = []
        is_done = False
        while "\n" in self._buf:
            line, self._buf = self._buf.split("\n", 1)
            line = line.rstrip("\r")
            result = self._parse_line(line)
            if result is None:
                continue
            payload, done = result
            if done:
                is_done = True
                break
            if payload is not None:
                payloads.append(payload)
        return payloads, is_done

    def xǁRobustSSEParserǁfeed__mutmut_3(self, raw: bytes) -> tuple[list[str], bool]:
        """Decode raw bytes and extract complete SSE data payloads; returns (payloads, is_done); raises MALFORMED_SSE_FRAME after malformed budget exhausted."""
        text = self._decoder.decode(raw, final=None)
        self._buf += text
        payloads: list[str] = []
        is_done = False
        while "\n" in self._buf:
            line, self._buf = self._buf.split("\n", 1)
            line = line.rstrip("\r")
            result = self._parse_line(line)
            if result is None:
                continue
            payload, done = result
            if done:
                is_done = True
                break
            if payload is not None:
                payloads.append(payload)
        return payloads, is_done

    def xǁRobustSSEParserǁfeed__mutmut_4(self, raw: bytes) -> tuple[list[str], bool]:
        """Decode raw bytes and extract complete SSE data payloads; returns (payloads, is_done); raises MALFORMED_SSE_FRAME after malformed budget exhausted."""
        text = self._decoder.decode(final=False)
        self._buf += text
        payloads: list[str] = []
        is_done = False
        while "\n" in self._buf:
            line, self._buf = self._buf.split("\n", 1)
            line = line.rstrip("\r")
            result = self._parse_line(line)
            if result is None:
                continue
            payload, done = result
            if done:
                is_done = True
                break
            if payload is not None:
                payloads.append(payload)
        return payloads, is_done

    def xǁRobustSSEParserǁfeed__mutmut_5(self, raw: bytes) -> tuple[list[str], bool]:
        """Decode raw bytes and extract complete SSE data payloads; returns (payloads, is_done); raises MALFORMED_SSE_FRAME after malformed budget exhausted."""
        text = self._decoder.decode(raw, )
        self._buf += text
        payloads: list[str] = []
        is_done = False
        while "\n" in self._buf:
            line, self._buf = self._buf.split("\n", 1)
            line = line.rstrip("\r")
            result = self._parse_line(line)
            if result is None:
                continue
            payload, done = result
            if done:
                is_done = True
                break
            if payload is not None:
                payloads.append(payload)
        return payloads, is_done

    def xǁRobustSSEParserǁfeed__mutmut_6(self, raw: bytes) -> tuple[list[str], bool]:
        """Decode raw bytes and extract complete SSE data payloads; returns (payloads, is_done); raises MALFORMED_SSE_FRAME after malformed budget exhausted."""
        text = self._decoder.decode(raw, final=True)
        self._buf += text
        payloads: list[str] = []
        is_done = False
        while "\n" in self._buf:
            line, self._buf = self._buf.split("\n", 1)
            line = line.rstrip("\r")
            result = self._parse_line(line)
            if result is None:
                continue
            payload, done = result
            if done:
                is_done = True
                break
            if payload is not None:
                payloads.append(payload)
        return payloads, is_done

    def xǁRobustSSEParserǁfeed__mutmut_7(self, raw: bytes) -> tuple[list[str], bool]:
        """Decode raw bytes and extract complete SSE data payloads; returns (payloads, is_done); raises MALFORMED_SSE_FRAME after malformed budget exhausted."""
        text = self._decoder.decode(raw, final=False)
        self._buf = text
        payloads: list[str] = []
        is_done = False
        while "\n" in self._buf:
            line, self._buf = self._buf.split("\n", 1)
            line = line.rstrip("\r")
            result = self._parse_line(line)
            if result is None:
                continue
            payload, done = result
            if done:
                is_done = True
                break
            if payload is not None:
                payloads.append(payload)
        return payloads, is_done

    def xǁRobustSSEParserǁfeed__mutmut_8(self, raw: bytes) -> tuple[list[str], bool]:
        """Decode raw bytes and extract complete SSE data payloads; returns (payloads, is_done); raises MALFORMED_SSE_FRAME after malformed budget exhausted."""
        text = self._decoder.decode(raw, final=False)
        self._buf -= text
        payloads: list[str] = []
        is_done = False
        while "\n" in self._buf:
            line, self._buf = self._buf.split("\n", 1)
            line = line.rstrip("\r")
            result = self._parse_line(line)
            if result is None:
                continue
            payload, done = result
            if done:
                is_done = True
                break
            if payload is not None:
                payloads.append(payload)
        return payloads, is_done

    def xǁRobustSSEParserǁfeed__mutmut_9(self, raw: bytes) -> tuple[list[str], bool]:
        """Decode raw bytes and extract complete SSE data payloads; returns (payloads, is_done); raises MALFORMED_SSE_FRAME after malformed budget exhausted."""
        text = self._decoder.decode(raw, final=False)
        self._buf += text
        payloads: list[str] = None
        is_done = False
        while "\n" in self._buf:
            line, self._buf = self._buf.split("\n", 1)
            line = line.rstrip("\r")
            result = self._parse_line(line)
            if result is None:
                continue
            payload, done = result
            if done:
                is_done = True
                break
            if payload is not None:
                payloads.append(payload)
        return payloads, is_done

    def xǁRobustSSEParserǁfeed__mutmut_10(self, raw: bytes) -> tuple[list[str], bool]:
        """Decode raw bytes and extract complete SSE data payloads; returns (payloads, is_done); raises MALFORMED_SSE_FRAME after malformed budget exhausted."""
        text = self._decoder.decode(raw, final=False)
        self._buf += text
        payloads: list[str] = []
        is_done = None
        while "\n" in self._buf:
            line, self._buf = self._buf.split("\n", 1)
            line = line.rstrip("\r")
            result = self._parse_line(line)
            if result is None:
                continue
            payload, done = result
            if done:
                is_done = True
                break
            if payload is not None:
                payloads.append(payload)
        return payloads, is_done

    def xǁRobustSSEParserǁfeed__mutmut_11(self, raw: bytes) -> tuple[list[str], bool]:
        """Decode raw bytes and extract complete SSE data payloads; returns (payloads, is_done); raises MALFORMED_SSE_FRAME after malformed budget exhausted."""
        text = self._decoder.decode(raw, final=False)
        self._buf += text
        payloads: list[str] = []
        is_done = True
        while "\n" in self._buf:
            line, self._buf = self._buf.split("\n", 1)
            line = line.rstrip("\r")
            result = self._parse_line(line)
            if result is None:
                continue
            payload, done = result
            if done:
                is_done = True
                break
            if payload is not None:
                payloads.append(payload)
        return payloads, is_done

    def xǁRobustSSEParserǁfeed__mutmut_12(self, raw: bytes) -> tuple[list[str], bool]:
        """Decode raw bytes and extract complete SSE data payloads; returns (payloads, is_done); raises MALFORMED_SSE_FRAME after malformed budget exhausted."""
        text = self._decoder.decode(raw, final=False)
        self._buf += text
        payloads: list[str] = []
        is_done = False
        while "XX\nXX" in self._buf:
            line, self._buf = self._buf.split("\n", 1)
            line = line.rstrip("\r")
            result = self._parse_line(line)
            if result is None:
                continue
            payload, done = result
            if done:
                is_done = True
                break
            if payload is not None:
                payloads.append(payload)
        return payloads, is_done

    def xǁRobustSSEParserǁfeed__mutmut_13(self, raw: bytes) -> tuple[list[str], bool]:
        """Decode raw bytes and extract complete SSE data payloads; returns (payloads, is_done); raises MALFORMED_SSE_FRAME after malformed budget exhausted."""
        text = self._decoder.decode(raw, final=False)
        self._buf += text
        payloads: list[str] = []
        is_done = False
        while "\n" not in self._buf:
            line, self._buf = self._buf.split("\n", 1)
            line = line.rstrip("\r")
            result = self._parse_line(line)
            if result is None:
                continue
            payload, done = result
            if done:
                is_done = True
                break
            if payload is not None:
                payloads.append(payload)
        return payloads, is_done

    def xǁRobustSSEParserǁfeed__mutmut_14(self, raw: bytes) -> tuple[list[str], bool]:
        """Decode raw bytes and extract complete SSE data payloads; returns (payloads, is_done); raises MALFORMED_SSE_FRAME after malformed budget exhausted."""
        text = self._decoder.decode(raw, final=False)
        self._buf += text
        payloads: list[str] = []
        is_done = False
        while "\n" in self._buf:
            line, self._buf = None
            line = line.rstrip("\r")
            result = self._parse_line(line)
            if result is None:
                continue
            payload, done = result
            if done:
                is_done = True
                break
            if payload is not None:
                payloads.append(payload)
        return payloads, is_done

    def xǁRobustSSEParserǁfeed__mutmut_15(self, raw: bytes) -> tuple[list[str], bool]:
        """Decode raw bytes and extract complete SSE data payloads; returns (payloads, is_done); raises MALFORMED_SSE_FRAME after malformed budget exhausted."""
        text = self._decoder.decode(raw, final=False)
        self._buf += text
        payloads: list[str] = []
        is_done = False
        while "\n" in self._buf:
            line, self._buf = self._buf.split(None, 1)
            line = line.rstrip("\r")
            result = self._parse_line(line)
            if result is None:
                continue
            payload, done = result
            if done:
                is_done = True
                break
            if payload is not None:
                payloads.append(payload)
        return payloads, is_done

    def xǁRobustSSEParserǁfeed__mutmut_16(self, raw: bytes) -> tuple[list[str], bool]:
        """Decode raw bytes and extract complete SSE data payloads; returns (payloads, is_done); raises MALFORMED_SSE_FRAME after malformed budget exhausted."""
        text = self._decoder.decode(raw, final=False)
        self._buf += text
        payloads: list[str] = []
        is_done = False
        while "\n" in self._buf:
            line, self._buf = self._buf.split("\n", None)
            line = line.rstrip("\r")
            result = self._parse_line(line)
            if result is None:
                continue
            payload, done = result
            if done:
                is_done = True
                break
            if payload is not None:
                payloads.append(payload)
        return payloads, is_done

    def xǁRobustSSEParserǁfeed__mutmut_17(self, raw: bytes) -> tuple[list[str], bool]:
        """Decode raw bytes and extract complete SSE data payloads; returns (payloads, is_done); raises MALFORMED_SSE_FRAME after malformed budget exhausted."""
        text = self._decoder.decode(raw, final=False)
        self._buf += text
        payloads: list[str] = []
        is_done = False
        while "\n" in self._buf:
            line, self._buf = self._buf.split(1)
            line = line.rstrip("\r")
            result = self._parse_line(line)
            if result is None:
                continue
            payload, done = result
            if done:
                is_done = True
                break
            if payload is not None:
                payloads.append(payload)
        return payloads, is_done

    def xǁRobustSSEParserǁfeed__mutmut_18(self, raw: bytes) -> tuple[list[str], bool]:
        """Decode raw bytes and extract complete SSE data payloads; returns (payloads, is_done); raises MALFORMED_SSE_FRAME after malformed budget exhausted."""
        text = self._decoder.decode(raw, final=False)
        self._buf += text
        payloads: list[str] = []
        is_done = False
        while "\n" in self._buf:
            line, self._buf = self._buf.split("\n", )
            line = line.rstrip("\r")
            result = self._parse_line(line)
            if result is None:
                continue
            payload, done = result
            if done:
                is_done = True
                break
            if payload is not None:
                payloads.append(payload)
        return payloads, is_done

    def xǁRobustSSEParserǁfeed__mutmut_19(self, raw: bytes) -> tuple[list[str], bool]:
        """Decode raw bytes and extract complete SSE data payloads; returns (payloads, is_done); raises MALFORMED_SSE_FRAME after malformed budget exhausted."""
        text = self._decoder.decode(raw, final=False)
        self._buf += text
        payloads: list[str] = []
        is_done = False
        while "\n" in self._buf:
            line, self._buf = self._buf.rsplit("\n", 1)
            line = line.rstrip("\r")
            result = self._parse_line(line)
            if result is None:
                continue
            payload, done = result
            if done:
                is_done = True
                break
            if payload is not None:
                payloads.append(payload)
        return payloads, is_done

    def xǁRobustSSEParserǁfeed__mutmut_20(self, raw: bytes) -> tuple[list[str], bool]:
        """Decode raw bytes and extract complete SSE data payloads; returns (payloads, is_done); raises MALFORMED_SSE_FRAME after malformed budget exhausted."""
        text = self._decoder.decode(raw, final=False)
        self._buf += text
        payloads: list[str] = []
        is_done = False
        while "\n" in self._buf:
            line, self._buf = self._buf.split("XX\nXX", 1)
            line = line.rstrip("\r")
            result = self._parse_line(line)
            if result is None:
                continue
            payload, done = result
            if done:
                is_done = True
                break
            if payload is not None:
                payloads.append(payload)
        return payloads, is_done

    def xǁRobustSSEParserǁfeed__mutmut_21(self, raw: bytes) -> tuple[list[str], bool]:
        """Decode raw bytes and extract complete SSE data payloads; returns (payloads, is_done); raises MALFORMED_SSE_FRAME after malformed budget exhausted."""
        text = self._decoder.decode(raw, final=False)
        self._buf += text
        payloads: list[str] = []
        is_done = False
        while "\n" in self._buf:
            line, self._buf = self._buf.split("\n", 2)
            line = line.rstrip("\r")
            result = self._parse_line(line)
            if result is None:
                continue
            payload, done = result
            if done:
                is_done = True
                break
            if payload is not None:
                payloads.append(payload)
        return payloads, is_done

    def xǁRobustSSEParserǁfeed__mutmut_22(self, raw: bytes) -> tuple[list[str], bool]:
        """Decode raw bytes and extract complete SSE data payloads; returns (payloads, is_done); raises MALFORMED_SSE_FRAME after malformed budget exhausted."""
        text = self._decoder.decode(raw, final=False)
        self._buf += text
        payloads: list[str] = []
        is_done = False
        while "\n" in self._buf:
            line, self._buf = self._buf.split("\n", 1)
            line = None
            result = self._parse_line(line)
            if result is None:
                continue
            payload, done = result
            if done:
                is_done = True
                break
            if payload is not None:
                payloads.append(payload)
        return payloads, is_done

    def xǁRobustSSEParserǁfeed__mutmut_23(self, raw: bytes) -> tuple[list[str], bool]:
        """Decode raw bytes and extract complete SSE data payloads; returns (payloads, is_done); raises MALFORMED_SSE_FRAME after malformed budget exhausted."""
        text = self._decoder.decode(raw, final=False)
        self._buf += text
        payloads: list[str] = []
        is_done = False
        while "\n" in self._buf:
            line, self._buf = self._buf.split("\n", 1)
            line = line.rstrip(None)
            result = self._parse_line(line)
            if result is None:
                continue
            payload, done = result
            if done:
                is_done = True
                break
            if payload is not None:
                payloads.append(payload)
        return payloads, is_done

    def xǁRobustSSEParserǁfeed__mutmut_24(self, raw: bytes) -> tuple[list[str], bool]:
        """Decode raw bytes and extract complete SSE data payloads; returns (payloads, is_done); raises MALFORMED_SSE_FRAME after malformed budget exhausted."""
        text = self._decoder.decode(raw, final=False)
        self._buf += text
        payloads: list[str] = []
        is_done = False
        while "\n" in self._buf:
            line, self._buf = self._buf.split("\n", 1)
            line = line.lstrip("\r")
            result = self._parse_line(line)
            if result is None:
                continue
            payload, done = result
            if done:
                is_done = True
                break
            if payload is not None:
                payloads.append(payload)
        return payloads, is_done

    def xǁRobustSSEParserǁfeed__mutmut_25(self, raw: bytes) -> tuple[list[str], bool]:
        """Decode raw bytes and extract complete SSE data payloads; returns (payloads, is_done); raises MALFORMED_SSE_FRAME after malformed budget exhausted."""
        text = self._decoder.decode(raw, final=False)
        self._buf += text
        payloads: list[str] = []
        is_done = False
        while "\n" in self._buf:
            line, self._buf = self._buf.split("\n", 1)
            line = line.rstrip("XX\rXX")
            result = self._parse_line(line)
            if result is None:
                continue
            payload, done = result
            if done:
                is_done = True
                break
            if payload is not None:
                payloads.append(payload)
        return payloads, is_done

    def xǁRobustSSEParserǁfeed__mutmut_26(self, raw: bytes) -> tuple[list[str], bool]:
        """Decode raw bytes and extract complete SSE data payloads; returns (payloads, is_done); raises MALFORMED_SSE_FRAME after malformed budget exhausted."""
        text = self._decoder.decode(raw, final=False)
        self._buf += text
        payloads: list[str] = []
        is_done = False
        while "\n" in self._buf:
            line, self._buf = self._buf.split("\n", 1)
            line = line.rstrip("\r")
            result = None
            if result is None:
                continue
            payload, done = result
            if done:
                is_done = True
                break
            if payload is not None:
                payloads.append(payload)
        return payloads, is_done

    def xǁRobustSSEParserǁfeed__mutmut_27(self, raw: bytes) -> tuple[list[str], bool]:
        """Decode raw bytes and extract complete SSE data payloads; returns (payloads, is_done); raises MALFORMED_SSE_FRAME after malformed budget exhausted."""
        text = self._decoder.decode(raw, final=False)
        self._buf += text
        payloads: list[str] = []
        is_done = False
        while "\n" in self._buf:
            line, self._buf = self._buf.split("\n", 1)
            line = line.rstrip("\r")
            result = self._parse_line(None)
            if result is None:
                continue
            payload, done = result
            if done:
                is_done = True
                break
            if payload is not None:
                payloads.append(payload)
        return payloads, is_done

    def xǁRobustSSEParserǁfeed__mutmut_28(self, raw: bytes) -> tuple[list[str], bool]:
        """Decode raw bytes and extract complete SSE data payloads; returns (payloads, is_done); raises MALFORMED_SSE_FRAME after malformed budget exhausted."""
        text = self._decoder.decode(raw, final=False)
        self._buf += text
        payloads: list[str] = []
        is_done = False
        while "\n" in self._buf:
            line, self._buf = self._buf.split("\n", 1)
            line = line.rstrip("\r")
            result = self._parse_line(line)
            if result is not None:
                continue
            payload, done = result
            if done:
                is_done = True
                break
            if payload is not None:
                payloads.append(payload)
        return payloads, is_done

    def xǁRobustSSEParserǁfeed__mutmut_29(self, raw: bytes) -> tuple[list[str], bool]:
        """Decode raw bytes and extract complete SSE data payloads; returns (payloads, is_done); raises MALFORMED_SSE_FRAME after malformed budget exhausted."""
        text = self._decoder.decode(raw, final=False)
        self._buf += text
        payloads: list[str] = []
        is_done = False
        while "\n" in self._buf:
            line, self._buf = self._buf.split("\n", 1)
            line = line.rstrip("\r")
            result = self._parse_line(line)
            if result is None:
                break
            payload, done = result
            if done:
                is_done = True
                break
            if payload is not None:
                payloads.append(payload)
        return payloads, is_done

    def xǁRobustSSEParserǁfeed__mutmut_30(self, raw: bytes) -> tuple[list[str], bool]:
        """Decode raw bytes and extract complete SSE data payloads; returns (payloads, is_done); raises MALFORMED_SSE_FRAME after malformed budget exhausted."""
        text = self._decoder.decode(raw, final=False)
        self._buf += text
        payloads: list[str] = []
        is_done = False
        while "\n" in self._buf:
            line, self._buf = self._buf.split("\n", 1)
            line = line.rstrip("\r")
            result = self._parse_line(line)
            if result is None:
                continue
            payload, done = None
            if done:
                is_done = True
                break
            if payload is not None:
                payloads.append(payload)
        return payloads, is_done

    def xǁRobustSSEParserǁfeed__mutmut_31(self, raw: bytes) -> tuple[list[str], bool]:
        """Decode raw bytes and extract complete SSE data payloads; returns (payloads, is_done); raises MALFORMED_SSE_FRAME after malformed budget exhausted."""
        text = self._decoder.decode(raw, final=False)
        self._buf += text
        payloads: list[str] = []
        is_done = False
        while "\n" in self._buf:
            line, self._buf = self._buf.split("\n", 1)
            line = line.rstrip("\r")
            result = self._parse_line(line)
            if result is None:
                continue
            payload, done = result
            if done:
                is_done = None
                break
            if payload is not None:
                payloads.append(payload)
        return payloads, is_done

    def xǁRobustSSEParserǁfeed__mutmut_32(self, raw: bytes) -> tuple[list[str], bool]:
        """Decode raw bytes and extract complete SSE data payloads; returns (payloads, is_done); raises MALFORMED_SSE_FRAME after malformed budget exhausted."""
        text = self._decoder.decode(raw, final=False)
        self._buf += text
        payloads: list[str] = []
        is_done = False
        while "\n" in self._buf:
            line, self._buf = self._buf.split("\n", 1)
            line = line.rstrip("\r")
            result = self._parse_line(line)
            if result is None:
                continue
            payload, done = result
            if done:
                is_done = False
                break
            if payload is not None:
                payloads.append(payload)
        return payloads, is_done

    def xǁRobustSSEParserǁfeed__mutmut_33(self, raw: bytes) -> tuple[list[str], bool]:
        """Decode raw bytes and extract complete SSE data payloads; returns (payloads, is_done); raises MALFORMED_SSE_FRAME after malformed budget exhausted."""
        text = self._decoder.decode(raw, final=False)
        self._buf += text
        payloads: list[str] = []
        is_done = False
        while "\n" in self._buf:
            line, self._buf = self._buf.split("\n", 1)
            line = line.rstrip("\r")
            result = self._parse_line(line)
            if result is None:
                continue
            payload, done = result
            if done:
                is_done = True
                return
            if payload is not None:
                payloads.append(payload)
        return payloads, is_done

    def xǁRobustSSEParserǁfeed__mutmut_34(self, raw: bytes) -> tuple[list[str], bool]:
        """Decode raw bytes and extract complete SSE data payloads; returns (payloads, is_done); raises MALFORMED_SSE_FRAME after malformed budget exhausted."""
        text = self._decoder.decode(raw, final=False)
        self._buf += text
        payloads: list[str] = []
        is_done = False
        while "\n" in self._buf:
            line, self._buf = self._buf.split("\n", 1)
            line = line.rstrip("\r")
            result = self._parse_line(line)
            if result is None:
                continue
            payload, done = result
            if done:
                is_done = True
                break
            if payload is None:
                payloads.append(payload)
        return payloads, is_done

    def xǁRobustSSEParserǁfeed__mutmut_35(self, raw: bytes) -> tuple[list[str], bool]:
        """Decode raw bytes and extract complete SSE data payloads; returns (payloads, is_done); raises MALFORMED_SSE_FRAME after malformed budget exhausted."""
        text = self._decoder.decode(raw, final=False)
        self._buf += text
        payloads: list[str] = []
        is_done = False
        while "\n" in self._buf:
            line, self._buf = self._buf.split("\n", 1)
            line = line.rstrip("\r")
            result = self._parse_line(line)
            if result is None:
                continue
            payload, done = result
            if done:
                is_done = True
                break
            if payload is not None:
                payloads.append(None)
        return payloads, is_done

    @_mutmut_mutated(mutants_xǁRobustSSEParserǁ_parse_line__mutmut)
    def _parse_line(self, line: str) -> tuple[str | None, bool] | None:
        """Parse one SSE text line; returns None to skip, (None, True) for [DONE], (payload_str, False) for valid data; raises MALFORMED_SSE_FRAME on budget exhaustion."""
        if self._is_keepalive(line):
            return None
        if not line.startswith(self._DATA_PREFIX):
            return None
        payload = line[len(self._DATA_PREFIX) :].lstrip(" ")
        if payload.strip() == "[DONE]":
            self._mark_activity()
            return None, True
        if not self._is_valid_json(payload):
            return None
        self._mark_activity()
        return payload, False

    def xǁRobustSSEParserǁ_parse_line__mutmut_orig(self, line: str) -> tuple[str | None, bool] | None:
        """Parse one SSE text line; returns None to skip, (None, True) for [DONE], (payload_str, False) for valid data; raises MALFORMED_SSE_FRAME on budget exhaustion."""
        if self._is_keepalive(line):
            return None
        if not line.startswith(self._DATA_PREFIX):
            return None
        payload = line[len(self._DATA_PREFIX) :].lstrip(" ")
        if payload.strip() == "[DONE]":
            self._mark_activity()
            return None, True
        if not self._is_valid_json(payload):
            return None
        self._mark_activity()
        return payload, False

    def xǁRobustSSEParserǁ_parse_line__mutmut_1(self, line: str) -> tuple[str | None, bool] | None:
        """Parse one SSE text line; returns None to skip, (None, True) for [DONE], (payload_str, False) for valid data; raises MALFORMED_SSE_FRAME on budget exhaustion."""
        if self._is_keepalive(None):
            return None
        if not line.startswith(self._DATA_PREFIX):
            return None
        payload = line[len(self._DATA_PREFIX) :].lstrip(" ")
        if payload.strip() == "[DONE]":
            self._mark_activity()
            return None, True
        if not self._is_valid_json(payload):
            return None
        self._mark_activity()
        return payload, False

    def xǁRobustSSEParserǁ_parse_line__mutmut_2(self, line: str) -> tuple[str | None, bool] | None:
        """Parse one SSE text line; returns None to skip, (None, True) for [DONE], (payload_str, False) for valid data; raises MALFORMED_SSE_FRAME on budget exhaustion."""
        if self._is_keepalive(line):
            return None
        if line.startswith(self._DATA_PREFIX):
            return None
        payload = line[len(self._DATA_PREFIX) :].lstrip(" ")
        if payload.strip() == "[DONE]":
            self._mark_activity()
            return None, True
        if not self._is_valid_json(payload):
            return None
        self._mark_activity()
        return payload, False

    def xǁRobustSSEParserǁ_parse_line__mutmut_3(self, line: str) -> tuple[str | None, bool] | None:
        """Parse one SSE text line; returns None to skip, (None, True) for [DONE], (payload_str, False) for valid data; raises MALFORMED_SSE_FRAME on budget exhaustion."""
        if self._is_keepalive(line):
            return None
        if not line.startswith(None):
            return None
        payload = line[len(self._DATA_PREFIX) :].lstrip(" ")
        if payload.strip() == "[DONE]":
            self._mark_activity()
            return None, True
        if not self._is_valid_json(payload):
            return None
        self._mark_activity()
        return payload, False

    def xǁRobustSSEParserǁ_parse_line__mutmut_4(self, line: str) -> tuple[str | None, bool] | None:
        """Parse one SSE text line; returns None to skip, (None, True) for [DONE], (payload_str, False) for valid data; raises MALFORMED_SSE_FRAME on budget exhaustion."""
        if self._is_keepalive(line):
            return None
        if not line.startswith(self._DATA_PREFIX):
            return None
        payload = None
        if payload.strip() == "[DONE]":
            self._mark_activity()
            return None, True
        if not self._is_valid_json(payload):
            return None
        self._mark_activity()
        return payload, False

    def xǁRobustSSEParserǁ_parse_line__mutmut_5(self, line: str) -> tuple[str | None, bool] | None:
        """Parse one SSE text line; returns None to skip, (None, True) for [DONE], (payload_str, False) for valid data; raises MALFORMED_SSE_FRAME on budget exhaustion."""
        if self._is_keepalive(line):
            return None
        if not line.startswith(self._DATA_PREFIX):
            return None
        payload = line[len(self._DATA_PREFIX) :].lstrip(None)
        if payload.strip() == "[DONE]":
            self._mark_activity()
            return None, True
        if not self._is_valid_json(payload):
            return None
        self._mark_activity()
        return payload, False

    def xǁRobustSSEParserǁ_parse_line__mutmut_6(self, line: str) -> tuple[str | None, bool] | None:
        """Parse one SSE text line; returns None to skip, (None, True) for [DONE], (payload_str, False) for valid data; raises MALFORMED_SSE_FRAME on budget exhaustion."""
        if self._is_keepalive(line):
            return None
        if not line.startswith(self._DATA_PREFIX):
            return None
        payload = line[len(self._DATA_PREFIX) :].rstrip(" ")
        if payload.strip() == "[DONE]":
            self._mark_activity()
            return None, True
        if not self._is_valid_json(payload):
            return None
        self._mark_activity()
        return payload, False

    def xǁRobustSSEParserǁ_parse_line__mutmut_7(self, line: str) -> tuple[str | None, bool] | None:
        """Parse one SSE text line; returns None to skip, (None, True) for [DONE], (payload_str, False) for valid data; raises MALFORMED_SSE_FRAME on budget exhaustion."""
        if self._is_keepalive(line):
            return None
        if not line.startswith(self._DATA_PREFIX):
            return None
        payload = line[len(self._DATA_PREFIX) :].lstrip("XX XX")
        if payload.strip() == "[DONE]":
            self._mark_activity()
            return None, True
        if not self._is_valid_json(payload):
            return None
        self._mark_activity()
        return payload, False

    def xǁRobustSSEParserǁ_parse_line__mutmut_8(self, line: str) -> tuple[str | None, bool] | None:
        """Parse one SSE text line; returns None to skip, (None, True) for [DONE], (payload_str, False) for valid data; raises MALFORMED_SSE_FRAME on budget exhaustion."""
        if self._is_keepalive(line):
            return None
        if not line.startswith(self._DATA_PREFIX):
            return None
        payload = line[len(self._DATA_PREFIX) :].lstrip(" ")
        if payload.strip() != "[DONE]":
            self._mark_activity()
            return None, True
        if not self._is_valid_json(payload):
            return None
        self._mark_activity()
        return payload, False

    def xǁRobustSSEParserǁ_parse_line__mutmut_9(self, line: str) -> tuple[str | None, bool] | None:
        """Parse one SSE text line; returns None to skip, (None, True) for [DONE], (payload_str, False) for valid data; raises MALFORMED_SSE_FRAME on budget exhaustion."""
        if self._is_keepalive(line):
            return None
        if not line.startswith(self._DATA_PREFIX):
            return None
        payload = line[len(self._DATA_PREFIX) :].lstrip(" ")
        if payload.strip() == "XX[DONE]XX":
            self._mark_activity()
            return None, True
        if not self._is_valid_json(payload):
            return None
        self._mark_activity()
        return payload, False

    def xǁRobustSSEParserǁ_parse_line__mutmut_10(self, line: str) -> tuple[str | None, bool] | None:
        """Parse one SSE text line; returns None to skip, (None, True) for [DONE], (payload_str, False) for valid data; raises MALFORMED_SSE_FRAME on budget exhaustion."""
        if self._is_keepalive(line):
            return None
        if not line.startswith(self._DATA_PREFIX):
            return None
        payload = line[len(self._DATA_PREFIX) :].lstrip(" ")
        if payload.strip() == "[done]":
            self._mark_activity()
            return None, True
        if not self._is_valid_json(payload):
            return None
        self._mark_activity()
        return payload, False

    def xǁRobustSSEParserǁ_parse_line__mutmut_11(self, line: str) -> tuple[str | None, bool] | None:
        """Parse one SSE text line; returns None to skip, (None, True) for [DONE], (payload_str, False) for valid data; raises MALFORMED_SSE_FRAME on budget exhaustion."""
        if self._is_keepalive(line):
            return None
        if not line.startswith(self._DATA_PREFIX):
            return None
        payload = line[len(self._DATA_PREFIX) :].lstrip(" ")
        if payload.strip() == "[DONE]":
            self._mark_activity()
            return None, False
        if not self._is_valid_json(payload):
            return None
        self._mark_activity()
        return payload, False

    def xǁRobustSSEParserǁ_parse_line__mutmut_12(self, line: str) -> tuple[str | None, bool] | None:
        """Parse one SSE text line; returns None to skip, (None, True) for [DONE], (payload_str, False) for valid data; raises MALFORMED_SSE_FRAME on budget exhaustion."""
        if self._is_keepalive(line):
            return None
        if not line.startswith(self._DATA_PREFIX):
            return None
        payload = line[len(self._DATA_PREFIX) :].lstrip(" ")
        if payload.strip() == "[DONE]":
            self._mark_activity()
            return None, True
        if self._is_valid_json(payload):
            return None
        self._mark_activity()
        return payload, False

    def xǁRobustSSEParserǁ_parse_line__mutmut_13(self, line: str) -> tuple[str | None, bool] | None:
        """Parse one SSE text line; returns None to skip, (None, True) for [DONE], (payload_str, False) for valid data; raises MALFORMED_SSE_FRAME on budget exhaustion."""
        if self._is_keepalive(line):
            return None
        if not line.startswith(self._DATA_PREFIX):
            return None
        payload = line[len(self._DATA_PREFIX) :].lstrip(" ")
        if payload.strip() == "[DONE]":
            self._mark_activity()
            return None, True
        if not self._is_valid_json(None):
            return None
        self._mark_activity()
        return payload, False

    def xǁRobustSSEParserǁ_parse_line__mutmut_14(self, line: str) -> tuple[str | None, bool] | None:
        """Parse one SSE text line; returns None to skip, (None, True) for [DONE], (payload_str, False) for valid data; raises MALFORMED_SSE_FRAME on budget exhaustion."""
        if self._is_keepalive(line):
            return None
        if not line.startswith(self._DATA_PREFIX):
            return None
        payload = line[len(self._DATA_PREFIX) :].lstrip(" ")
        if payload.strip() == "[DONE]":
            self._mark_activity()
            return None, True
        if not self._is_valid_json(payload):
            return None
        self._mark_activity()
        return payload, True

    @_mutmut_mutated(mutants_xǁRobustSSEParserǁ_is_keepalive__mutmut)
    def _is_keepalive(self, line: str) -> bool:
        """Return True for blank lines and SSE comments (keepalive)."""
        if not line or line.startswith(":"):
            self._mark_activity()
            return True
        return False

    def xǁRobustSSEParserǁ_is_keepalive__mutmut_orig(self, line: str) -> bool:
        """Return True for blank lines and SSE comments (keepalive)."""
        if not line or line.startswith(":"):
            self._mark_activity()
            return True
        return False

    def xǁRobustSSEParserǁ_is_keepalive__mutmut_1(self, line: str) -> bool:
        """Return True for blank lines and SSE comments (keepalive)."""
        if not line and line.startswith(":"):
            self._mark_activity()
            return True
        return False

    def xǁRobustSSEParserǁ_is_keepalive__mutmut_2(self, line: str) -> bool:
        """Return True for blank lines and SSE comments (keepalive)."""
        if line or line.startswith(":"):
            self._mark_activity()
            return True
        return False

    def xǁRobustSSEParserǁ_is_keepalive__mutmut_3(self, line: str) -> bool:
        """Return True for blank lines and SSE comments (keepalive)."""
        if not line or line.startswith(None):
            self._mark_activity()
            return True
        return False

    def xǁRobustSSEParserǁ_is_keepalive__mutmut_4(self, line: str) -> bool:
        """Return True for blank lines and SSE comments (keepalive)."""
        if not line or line.startswith("XX:XX"):
            self._mark_activity()
            return True
        return False

    def xǁRobustSSEParserǁ_is_keepalive__mutmut_5(self, line: str) -> bool:
        """Return True for blank lines and SSE comments (keepalive)."""
        if not line or line.startswith(":"):
            self._mark_activity()
            return False
        return False

    def xǁRobustSSEParserǁ_is_keepalive__mutmut_6(self, line: str) -> bool:
        """Return True for blank lines and SSE comments (keepalive)."""
        if not line or line.startswith(":"):
            self._mark_activity()
            return True
        return True

    @_mutmut_mutated(mutants_xǁRobustSSEParserǁ_mark_activity__mutmut)
    def _mark_activity(self) -> None:
        """Record the current time as the last observed SSE event/keepalive."""
        self._last_event_at = time.monotonic()

    def xǁRobustSSEParserǁ_mark_activity__mutmut_orig(self) -> None:
        """Record the current time as the last observed SSE event/keepalive."""
        self._last_event_at = time.monotonic()

    def xǁRobustSSEParserǁ_mark_activity__mutmut_1(self) -> None:
        """Record the current time as the last observed SSE event/keepalive."""
        self._last_event_at = None

    @_mutmut_mutated(mutants_xǁRobustSSEParserǁ_is_valid_json__mutmut)
    def _is_valid_json(self, payload: str) -> bool:
        """Validate that payload is valid JSON; track malformed count."""
        try:
            orjson.loads(payload)
            return True
        except ValueError:
            self._malformed_count += 1
            self.stat_parse_errors += 1
            if self._malformed_count > self._malformed_retry:
                raise LLMTransportError(
                    kind="MALFORMED_SSE_FRAME",
                    phase="in_stream",
                    url="",
                    retryable=False,
                    detail=f"malformed SSE frame (count={self._malformed_count})",
                )
            return False

    def xǁRobustSSEParserǁ_is_valid_json__mutmut_orig(self, payload: str) -> bool:
        """Validate that payload is valid JSON; track malformed count."""
        try:
            orjson.loads(payload)
            return True
        except ValueError:
            self._malformed_count += 1
            self.stat_parse_errors += 1
            if self._malformed_count > self._malformed_retry:
                raise LLMTransportError(
                    kind="MALFORMED_SSE_FRAME",
                    phase="in_stream",
                    url="",
                    retryable=False,
                    detail=f"malformed SSE frame (count={self._malformed_count})",
                )
            return False

    def xǁRobustSSEParserǁ_is_valid_json__mutmut_1(self, payload: str) -> bool:
        """Validate that payload is valid JSON; track malformed count."""
        try:
            orjson.loads(None)
            return True
        except ValueError:
            self._malformed_count += 1
            self.stat_parse_errors += 1
            if self._malformed_count > self._malformed_retry:
                raise LLMTransportError(
                    kind="MALFORMED_SSE_FRAME",
                    phase="in_stream",
                    url="",
                    retryable=False,
                    detail=f"malformed SSE frame (count={self._malformed_count})",
                )
            return False

    def xǁRobustSSEParserǁ_is_valid_json__mutmut_2(self, payload: str) -> bool:
        """Validate that payload is valid JSON; track malformed count."""
        try:
            orjson.loads(payload)
            return False
        except ValueError:
            self._malformed_count += 1
            self.stat_parse_errors += 1
            if self._malformed_count > self._malformed_retry:
                raise LLMTransportError(
                    kind="MALFORMED_SSE_FRAME",
                    phase="in_stream",
                    url="",
                    retryable=False,
                    detail=f"malformed SSE frame (count={self._malformed_count})",
                )
            return False

    def xǁRobustSSEParserǁ_is_valid_json__mutmut_3(self, payload: str) -> bool:
        """Validate that payload is valid JSON; track malformed count."""
        try:
            orjson.loads(payload)
            return True
        except ValueError:
            self._malformed_count = 1
            self.stat_parse_errors += 1
            if self._malformed_count > self._malformed_retry:
                raise LLMTransportError(
                    kind="MALFORMED_SSE_FRAME",
                    phase="in_stream",
                    url="",
                    retryable=False,
                    detail=f"malformed SSE frame (count={self._malformed_count})",
                )
            return False

    def xǁRobustSSEParserǁ_is_valid_json__mutmut_4(self, payload: str) -> bool:
        """Validate that payload is valid JSON; track malformed count."""
        try:
            orjson.loads(payload)
            return True
        except ValueError:
            self._malformed_count -= 1
            self.stat_parse_errors += 1
            if self._malformed_count > self._malformed_retry:
                raise LLMTransportError(
                    kind="MALFORMED_SSE_FRAME",
                    phase="in_stream",
                    url="",
                    retryable=False,
                    detail=f"malformed SSE frame (count={self._malformed_count})",
                )
            return False

    def xǁRobustSSEParserǁ_is_valid_json__mutmut_5(self, payload: str) -> bool:
        """Validate that payload is valid JSON; track malformed count."""
        try:
            orjson.loads(payload)
            return True
        except ValueError:
            self._malformed_count += 2
            self.stat_parse_errors += 1
            if self._malformed_count > self._malformed_retry:
                raise LLMTransportError(
                    kind="MALFORMED_SSE_FRAME",
                    phase="in_stream",
                    url="",
                    retryable=False,
                    detail=f"malformed SSE frame (count={self._malformed_count})",
                )
            return False

    def xǁRobustSSEParserǁ_is_valid_json__mutmut_6(self, payload: str) -> bool:
        """Validate that payload is valid JSON; track malformed count."""
        try:
            orjson.loads(payload)
            return True
        except ValueError:
            self._malformed_count += 1
            self.stat_parse_errors = 1
            if self._malformed_count > self._malformed_retry:
                raise LLMTransportError(
                    kind="MALFORMED_SSE_FRAME",
                    phase="in_stream",
                    url="",
                    retryable=False,
                    detail=f"malformed SSE frame (count={self._malformed_count})",
                )
            return False

    def xǁRobustSSEParserǁ_is_valid_json__mutmut_7(self, payload: str) -> bool:
        """Validate that payload is valid JSON; track malformed count."""
        try:
            orjson.loads(payload)
            return True
        except ValueError:
            self._malformed_count += 1
            self.stat_parse_errors -= 1
            if self._malformed_count > self._malformed_retry:
                raise LLMTransportError(
                    kind="MALFORMED_SSE_FRAME",
                    phase="in_stream",
                    url="",
                    retryable=False,
                    detail=f"malformed SSE frame (count={self._malformed_count})",
                )
            return False

    def xǁRobustSSEParserǁ_is_valid_json__mutmut_8(self, payload: str) -> bool:
        """Validate that payload is valid JSON; track malformed count."""
        try:
            orjson.loads(payload)
            return True
        except ValueError:
            self._malformed_count += 1
            self.stat_parse_errors += 2
            if self._malformed_count > self._malformed_retry:
                raise LLMTransportError(
                    kind="MALFORMED_SSE_FRAME",
                    phase="in_stream",
                    url="",
                    retryable=False,
                    detail=f"malformed SSE frame (count={self._malformed_count})",
                )
            return False

    def xǁRobustSSEParserǁ_is_valid_json__mutmut_9(self, payload: str) -> bool:
        """Validate that payload is valid JSON; track malformed count."""
        try:
            orjson.loads(payload)
            return True
        except ValueError:
            self._malformed_count += 1
            self.stat_parse_errors += 1
            if self._malformed_count >= self._malformed_retry:
                raise LLMTransportError(
                    kind="MALFORMED_SSE_FRAME",
                    phase="in_stream",
                    url="",
                    retryable=False,
                    detail=f"malformed SSE frame (count={self._malformed_count})",
                )
            return False

    def xǁRobustSSEParserǁ_is_valid_json__mutmut_10(self, payload: str) -> bool:
        """Validate that payload is valid JSON; track malformed count."""
        try:
            orjson.loads(payload)
            return True
        except ValueError:
            self._malformed_count += 1
            self.stat_parse_errors += 1
            if self._malformed_count > self._malformed_retry:
                raise LLMTransportError(
                    kind=None,
                    phase="in_stream",
                    url="",
                    retryable=False,
                    detail=f"malformed SSE frame (count={self._malformed_count})",
                )
            return False

    def xǁRobustSSEParserǁ_is_valid_json__mutmut_11(self, payload: str) -> bool:
        """Validate that payload is valid JSON; track malformed count."""
        try:
            orjson.loads(payload)
            return True
        except ValueError:
            self._malformed_count += 1
            self.stat_parse_errors += 1
            if self._malformed_count > self._malformed_retry:
                raise LLMTransportError(
                    kind="MALFORMED_SSE_FRAME",
                    phase=None,
                    url="",
                    retryable=False,
                    detail=f"malformed SSE frame (count={self._malformed_count})",
                )
            return False

    def xǁRobustSSEParserǁ_is_valid_json__mutmut_12(self, payload: str) -> bool:
        """Validate that payload is valid JSON; track malformed count."""
        try:
            orjson.loads(payload)
            return True
        except ValueError:
            self._malformed_count += 1
            self.stat_parse_errors += 1
            if self._malformed_count > self._malformed_retry:
                raise LLMTransportError(
                    kind="MALFORMED_SSE_FRAME",
                    phase="in_stream",
                    url=None,
                    retryable=False,
                    detail=f"malformed SSE frame (count={self._malformed_count})",
                )
            return False

    def xǁRobustSSEParserǁ_is_valid_json__mutmut_13(self, payload: str) -> bool:
        """Validate that payload is valid JSON; track malformed count."""
        try:
            orjson.loads(payload)
            return True
        except ValueError:
            self._malformed_count += 1
            self.stat_parse_errors += 1
            if self._malformed_count > self._malformed_retry:
                raise LLMTransportError(
                    kind="MALFORMED_SSE_FRAME",
                    phase="in_stream",
                    url="",
                    retryable=None,
                    detail=f"malformed SSE frame (count={self._malformed_count})",
                )
            return False

    def xǁRobustSSEParserǁ_is_valid_json__mutmut_14(self, payload: str) -> bool:
        """Validate that payload is valid JSON; track malformed count."""
        try:
            orjson.loads(payload)
            return True
        except ValueError:
            self._malformed_count += 1
            self.stat_parse_errors += 1
            if self._malformed_count > self._malformed_retry:
                raise LLMTransportError(
                    kind="MALFORMED_SSE_FRAME",
                    phase="in_stream",
                    url="",
                    retryable=False,
                    detail=None,
                )
            return False

    def xǁRobustSSEParserǁ_is_valid_json__mutmut_15(self, payload: str) -> bool:
        """Validate that payload is valid JSON; track malformed count."""
        try:
            orjson.loads(payload)
            return True
        except ValueError:
            self._malformed_count += 1
            self.stat_parse_errors += 1
            if self._malformed_count > self._malformed_retry:
                raise LLMTransportError(
                    phase="in_stream",
                    url="",
                    retryable=False,
                    detail=f"malformed SSE frame (count={self._malformed_count})",
                )
            return False

    def xǁRobustSSEParserǁ_is_valid_json__mutmut_16(self, payload: str) -> bool:
        """Validate that payload is valid JSON; track malformed count."""
        try:
            orjson.loads(payload)
            return True
        except ValueError:
            self._malformed_count += 1
            self.stat_parse_errors += 1
            if self._malformed_count > self._malformed_retry:
                raise LLMTransportError(
                    kind="MALFORMED_SSE_FRAME",
                    url="",
                    retryable=False,
                    detail=f"malformed SSE frame (count={self._malformed_count})",
                )
            return False

    def xǁRobustSSEParserǁ_is_valid_json__mutmut_17(self, payload: str) -> bool:
        """Validate that payload is valid JSON; track malformed count."""
        try:
            orjson.loads(payload)
            return True
        except ValueError:
            self._malformed_count += 1
            self.stat_parse_errors += 1
            if self._malformed_count > self._malformed_retry:
                raise LLMTransportError(
                    kind="MALFORMED_SSE_FRAME",
                    phase="in_stream",
                    retryable=False,
                    detail=f"malformed SSE frame (count={self._malformed_count})",
                )
            return False

    def xǁRobustSSEParserǁ_is_valid_json__mutmut_18(self, payload: str) -> bool:
        """Validate that payload is valid JSON; track malformed count."""
        try:
            orjson.loads(payload)
            return True
        except ValueError:
            self._malformed_count += 1
            self.stat_parse_errors += 1
            if self._malformed_count > self._malformed_retry:
                raise LLMTransportError(
                    kind="MALFORMED_SSE_FRAME",
                    phase="in_stream",
                    url="",
                    detail=f"malformed SSE frame (count={self._malformed_count})",
                )
            return False

    def xǁRobustSSEParserǁ_is_valid_json__mutmut_19(self, payload: str) -> bool:
        """Validate that payload is valid JSON; track malformed count."""
        try:
            orjson.loads(payload)
            return True
        except ValueError:
            self._malformed_count += 1
            self.stat_parse_errors += 1
            if self._malformed_count > self._malformed_retry:
                raise LLMTransportError(
                    kind="MALFORMED_SSE_FRAME",
                    phase="in_stream",
                    url="",
                    retryable=False,
                    )
            return False

    def xǁRobustSSEParserǁ_is_valid_json__mutmut_20(self, payload: str) -> bool:
        """Validate that payload is valid JSON; track malformed count."""
        try:
            orjson.loads(payload)
            return True
        except ValueError:
            self._malformed_count += 1
            self.stat_parse_errors += 1
            if self._malformed_count > self._malformed_retry:
                raise LLMTransportError(
                    kind="XXMALFORMED_SSE_FRAMEXX",
                    phase="in_stream",
                    url="",
                    retryable=False,
                    detail=f"malformed SSE frame (count={self._malformed_count})",
                )
            return False

    def xǁRobustSSEParserǁ_is_valid_json__mutmut_21(self, payload: str) -> bool:
        """Validate that payload is valid JSON; track malformed count."""
        try:
            orjson.loads(payload)
            return True
        except ValueError:
            self._malformed_count += 1
            self.stat_parse_errors += 1
            if self._malformed_count > self._malformed_retry:
                raise LLMTransportError(
                    kind="malformed_sse_frame",
                    phase="in_stream",
                    url="",
                    retryable=False,
                    detail=f"malformed SSE frame (count={self._malformed_count})",
                )
            return False

    def xǁRobustSSEParserǁ_is_valid_json__mutmut_22(self, payload: str) -> bool:
        """Validate that payload is valid JSON; track malformed count."""
        try:
            orjson.loads(payload)
            return True
        except ValueError:
            self._malformed_count += 1
            self.stat_parse_errors += 1
            if self._malformed_count > self._malformed_retry:
                raise LLMTransportError(
                    kind="MALFORMED_SSE_FRAME",
                    phase="XXin_streamXX",
                    url="",
                    retryable=False,
                    detail=f"malformed SSE frame (count={self._malformed_count})",
                )
            return False

    def xǁRobustSSEParserǁ_is_valid_json__mutmut_23(self, payload: str) -> bool:
        """Validate that payload is valid JSON; track malformed count."""
        try:
            orjson.loads(payload)
            return True
        except ValueError:
            self._malformed_count += 1
            self.stat_parse_errors += 1
            if self._malformed_count > self._malformed_retry:
                raise LLMTransportError(
                    kind="MALFORMED_SSE_FRAME",
                    phase="IN_STREAM",
                    url="",
                    retryable=False,
                    detail=f"malformed SSE frame (count={self._malformed_count})",
                )
            return False

    def xǁRobustSSEParserǁ_is_valid_json__mutmut_24(self, payload: str) -> bool:
        """Validate that payload is valid JSON; track malformed count."""
        try:
            orjson.loads(payload)
            return True
        except ValueError:
            self._malformed_count += 1
            self.stat_parse_errors += 1
            if self._malformed_count > self._malformed_retry:
                raise LLMTransportError(
                    kind="MALFORMED_SSE_FRAME",
                    phase="in_stream",
                    url="XXXX",
                    retryable=False,
                    detail=f"malformed SSE frame (count={self._malformed_count})",
                )
            return False

    def xǁRobustSSEParserǁ_is_valid_json__mutmut_25(self, payload: str) -> bool:
        """Validate that payload is valid JSON; track malformed count."""
        try:
            orjson.loads(payload)
            return True
        except ValueError:
            self._malformed_count += 1
            self.stat_parse_errors += 1
            if self._malformed_count > self._malformed_retry:
                raise LLMTransportError(
                    kind="MALFORMED_SSE_FRAME",
                    phase="in_stream",
                    url="",
                    retryable=True,
                    detail=f"malformed SSE frame (count={self._malformed_count})",
                )
            return False

    def xǁRobustSSEParserǁ_is_valid_json__mutmut_26(self, payload: str) -> bool:
        """Validate that payload is valid JSON; track malformed count."""
        try:
            orjson.loads(payload)
            return True
        except ValueError:
            self._malformed_count += 1
            self.stat_parse_errors += 1
            if self._malformed_count > self._malformed_retry:
                raise LLMTransportError(
                    kind="MALFORMED_SSE_FRAME",
                    phase="in_stream",
                    url="",
                    retryable=False,
                    detail=f"malformed SSE frame (count={self._malformed_count})",
                )
            return True

    @_mutmut_mutated(mutants_xǁRobustSSEParserǁcheck_heartbeat__mutmut)
    def check_heartbeat(self, url: str) -> None:
        """Raise HEARTBEAT_TIMEOUT when stream has been idle longer than timeout."""
        if self._heartbeat_timeout <= 0:
            return
        elapsed = time.monotonic() - self._last_event_at
        if elapsed > self._heartbeat_timeout:
            raise LLMTransportError(
                kind="HEARTBEAT_TIMEOUT",
                phase="in_stream",
                url=url,
                retryable=True,
                detail=f"no SSE event for {elapsed:.1f}s",
            )

    def xǁRobustSSEParserǁcheck_heartbeat__mutmut_orig(self, url: str) -> None:
        """Raise HEARTBEAT_TIMEOUT when stream has been idle longer than timeout."""
        if self._heartbeat_timeout <= 0:
            return
        elapsed = time.monotonic() - self._last_event_at
        if elapsed > self._heartbeat_timeout:
            raise LLMTransportError(
                kind="HEARTBEAT_TIMEOUT",
                phase="in_stream",
                url=url,
                retryable=True,
                detail=f"no SSE event for {elapsed:.1f}s",
            )

    def xǁRobustSSEParserǁcheck_heartbeat__mutmut_1(self, url: str) -> None:
        """Raise HEARTBEAT_TIMEOUT when stream has been idle longer than timeout."""
        if self._heartbeat_timeout < 0:
            return
        elapsed = time.monotonic() - self._last_event_at
        if elapsed > self._heartbeat_timeout:
            raise LLMTransportError(
                kind="HEARTBEAT_TIMEOUT",
                phase="in_stream",
                url=url,
                retryable=True,
                detail=f"no SSE event for {elapsed:.1f}s",
            )

    def xǁRobustSSEParserǁcheck_heartbeat__mutmut_2(self, url: str) -> None:
        """Raise HEARTBEAT_TIMEOUT when stream has been idle longer than timeout."""
        if self._heartbeat_timeout <= 1:
            return
        elapsed = time.monotonic() - self._last_event_at
        if elapsed > self._heartbeat_timeout:
            raise LLMTransportError(
                kind="HEARTBEAT_TIMEOUT",
                phase="in_stream",
                url=url,
                retryable=True,
                detail=f"no SSE event for {elapsed:.1f}s",
            )

    def xǁRobustSSEParserǁcheck_heartbeat__mutmut_3(self, url: str) -> None:
        """Raise HEARTBEAT_TIMEOUT when stream has been idle longer than timeout."""
        if self._heartbeat_timeout <= 0:
            return
        elapsed = None
        if elapsed > self._heartbeat_timeout:
            raise LLMTransportError(
                kind="HEARTBEAT_TIMEOUT",
                phase="in_stream",
                url=url,
                retryable=True,
                detail=f"no SSE event for {elapsed:.1f}s",
            )

    def xǁRobustSSEParserǁcheck_heartbeat__mutmut_4(self, url: str) -> None:
        """Raise HEARTBEAT_TIMEOUT when stream has been idle longer than timeout."""
        if self._heartbeat_timeout <= 0:
            return
        elapsed = time.monotonic() + self._last_event_at
        if elapsed > self._heartbeat_timeout:
            raise LLMTransportError(
                kind="HEARTBEAT_TIMEOUT",
                phase="in_stream",
                url=url,
                retryable=True,
                detail=f"no SSE event for {elapsed:.1f}s",
            )

    def xǁRobustSSEParserǁcheck_heartbeat__mutmut_5(self, url: str) -> None:
        """Raise HEARTBEAT_TIMEOUT when stream has been idle longer than timeout."""
        if self._heartbeat_timeout <= 0:
            return
        elapsed = time.monotonic() - self._last_event_at
        if elapsed >= self._heartbeat_timeout:
            raise LLMTransportError(
                kind="HEARTBEAT_TIMEOUT",
                phase="in_stream",
                url=url,
                retryable=True,
                detail=f"no SSE event for {elapsed:.1f}s",
            )

    def xǁRobustSSEParserǁcheck_heartbeat__mutmut_6(self, url: str) -> None:
        """Raise HEARTBEAT_TIMEOUT when stream has been idle longer than timeout."""
        if self._heartbeat_timeout <= 0:
            return
        elapsed = time.monotonic() - self._last_event_at
        if elapsed > self._heartbeat_timeout:
            raise LLMTransportError(
                kind=None,
                phase="in_stream",
                url=url,
                retryable=True,
                detail=f"no SSE event for {elapsed:.1f}s",
            )

    def xǁRobustSSEParserǁcheck_heartbeat__mutmut_7(self, url: str) -> None:
        """Raise HEARTBEAT_TIMEOUT when stream has been idle longer than timeout."""
        if self._heartbeat_timeout <= 0:
            return
        elapsed = time.monotonic() - self._last_event_at
        if elapsed > self._heartbeat_timeout:
            raise LLMTransportError(
                kind="HEARTBEAT_TIMEOUT",
                phase=None,
                url=url,
                retryable=True,
                detail=f"no SSE event for {elapsed:.1f}s",
            )

    def xǁRobustSSEParserǁcheck_heartbeat__mutmut_8(self, url: str) -> None:
        """Raise HEARTBEAT_TIMEOUT when stream has been idle longer than timeout."""
        if self._heartbeat_timeout <= 0:
            return
        elapsed = time.monotonic() - self._last_event_at
        if elapsed > self._heartbeat_timeout:
            raise LLMTransportError(
                kind="HEARTBEAT_TIMEOUT",
                phase="in_stream",
                url=None,
                retryable=True,
                detail=f"no SSE event for {elapsed:.1f}s",
            )

    def xǁRobustSSEParserǁcheck_heartbeat__mutmut_9(self, url: str) -> None:
        """Raise HEARTBEAT_TIMEOUT when stream has been idle longer than timeout."""
        if self._heartbeat_timeout <= 0:
            return
        elapsed = time.monotonic() - self._last_event_at
        if elapsed > self._heartbeat_timeout:
            raise LLMTransportError(
                kind="HEARTBEAT_TIMEOUT",
                phase="in_stream",
                url=url,
                retryable=None,
                detail=f"no SSE event for {elapsed:.1f}s",
            )

    def xǁRobustSSEParserǁcheck_heartbeat__mutmut_10(self, url: str) -> None:
        """Raise HEARTBEAT_TIMEOUT when stream has been idle longer than timeout."""
        if self._heartbeat_timeout <= 0:
            return
        elapsed = time.monotonic() - self._last_event_at
        if elapsed > self._heartbeat_timeout:
            raise LLMTransportError(
                kind="HEARTBEAT_TIMEOUT",
                phase="in_stream",
                url=url,
                retryable=True,
                detail=None,
            )

    def xǁRobustSSEParserǁcheck_heartbeat__mutmut_11(self, url: str) -> None:
        """Raise HEARTBEAT_TIMEOUT when stream has been idle longer than timeout."""
        if self._heartbeat_timeout <= 0:
            return
        elapsed = time.monotonic() - self._last_event_at
        if elapsed > self._heartbeat_timeout:
            raise LLMTransportError(
                phase="in_stream",
                url=url,
                retryable=True,
                detail=f"no SSE event for {elapsed:.1f}s",
            )

    def xǁRobustSSEParserǁcheck_heartbeat__mutmut_12(self, url: str) -> None:
        """Raise HEARTBEAT_TIMEOUT when stream has been idle longer than timeout."""
        if self._heartbeat_timeout <= 0:
            return
        elapsed = time.monotonic() - self._last_event_at
        if elapsed > self._heartbeat_timeout:
            raise LLMTransportError(
                kind="HEARTBEAT_TIMEOUT",
                url=url,
                retryable=True,
                detail=f"no SSE event for {elapsed:.1f}s",
            )

    def xǁRobustSSEParserǁcheck_heartbeat__mutmut_13(self, url: str) -> None:
        """Raise HEARTBEAT_TIMEOUT when stream has been idle longer than timeout."""
        if self._heartbeat_timeout <= 0:
            return
        elapsed = time.monotonic() - self._last_event_at
        if elapsed > self._heartbeat_timeout:
            raise LLMTransportError(
                kind="HEARTBEAT_TIMEOUT",
                phase="in_stream",
                retryable=True,
                detail=f"no SSE event for {elapsed:.1f}s",
            )

    def xǁRobustSSEParserǁcheck_heartbeat__mutmut_14(self, url: str) -> None:
        """Raise HEARTBEAT_TIMEOUT when stream has been idle longer than timeout."""
        if self._heartbeat_timeout <= 0:
            return
        elapsed = time.monotonic() - self._last_event_at
        if elapsed > self._heartbeat_timeout:
            raise LLMTransportError(
                kind="HEARTBEAT_TIMEOUT",
                phase="in_stream",
                url=url,
                detail=f"no SSE event for {elapsed:.1f}s",
            )

    def xǁRobustSSEParserǁcheck_heartbeat__mutmut_15(self, url: str) -> None:
        """Raise HEARTBEAT_TIMEOUT when stream has been idle longer than timeout."""
        if self._heartbeat_timeout <= 0:
            return
        elapsed = time.monotonic() - self._last_event_at
        if elapsed > self._heartbeat_timeout:
            raise LLMTransportError(
                kind="HEARTBEAT_TIMEOUT",
                phase="in_stream",
                url=url,
                retryable=True,
                )

    def xǁRobustSSEParserǁcheck_heartbeat__mutmut_16(self, url: str) -> None:
        """Raise HEARTBEAT_TIMEOUT when stream has been idle longer than timeout."""
        if self._heartbeat_timeout <= 0:
            return
        elapsed = time.monotonic() - self._last_event_at
        if elapsed > self._heartbeat_timeout:
            raise LLMTransportError(
                kind="XXHEARTBEAT_TIMEOUTXX",
                phase="in_stream",
                url=url,
                retryable=True,
                detail=f"no SSE event for {elapsed:.1f}s",
            )

    def xǁRobustSSEParserǁcheck_heartbeat__mutmut_17(self, url: str) -> None:
        """Raise HEARTBEAT_TIMEOUT when stream has been idle longer than timeout."""
        if self._heartbeat_timeout <= 0:
            return
        elapsed = time.monotonic() - self._last_event_at
        if elapsed > self._heartbeat_timeout:
            raise LLMTransportError(
                kind="heartbeat_timeout",
                phase="in_stream",
                url=url,
                retryable=True,
                detail=f"no SSE event for {elapsed:.1f}s",
            )

    def xǁRobustSSEParserǁcheck_heartbeat__mutmut_18(self, url: str) -> None:
        """Raise HEARTBEAT_TIMEOUT when stream has been idle longer than timeout."""
        if self._heartbeat_timeout <= 0:
            return
        elapsed = time.monotonic() - self._last_event_at
        if elapsed > self._heartbeat_timeout:
            raise LLMTransportError(
                kind="HEARTBEAT_TIMEOUT",
                phase="XXin_streamXX",
                url=url,
                retryable=True,
                detail=f"no SSE event for {elapsed:.1f}s",
            )

    def xǁRobustSSEParserǁcheck_heartbeat__mutmut_19(self, url: str) -> None:
        """Raise HEARTBEAT_TIMEOUT when stream has been idle longer than timeout."""
        if self._heartbeat_timeout <= 0:
            return
        elapsed = time.monotonic() - self._last_event_at
        if elapsed > self._heartbeat_timeout:
            raise LLMTransportError(
                kind="HEARTBEAT_TIMEOUT",
                phase="IN_STREAM",
                url=url,
                retryable=True,
                detail=f"no SSE event for {elapsed:.1f}s",
            )

    def xǁRobustSSEParserǁcheck_heartbeat__mutmut_20(self, url: str) -> None:
        """Raise HEARTBEAT_TIMEOUT when stream has been idle longer than timeout."""
        if self._heartbeat_timeout <= 0:
            return
        elapsed = time.monotonic() - self._last_event_at
        if elapsed > self._heartbeat_timeout:
            raise LLMTransportError(
                kind="HEARTBEAT_TIMEOUT",
                phase="in_stream",
                url=url,
                retryable=False,
                detail=f"no SSE event for {elapsed:.1f}s",
            )

mutants_xǁRobustSSEParserǁ__init____mutmut['_mutmut_orig'] = RobustSSEParser.xǁRobustSSEParserǁ__init____mutmut_orig # type: ignore # mutmut generated
mutants_xǁRobustSSEParserǁ__init____mutmut['xǁRobustSSEParserǁ__init____mutmut_1'] = RobustSSEParser.xǁRobustSSEParserǁ__init____mutmut_1 # type: ignore # mutmut generated
mutants_xǁRobustSSEParserǁ__init____mutmut['xǁRobustSSEParserǁ__init____mutmut_2'] = RobustSSEParser.xǁRobustSSEParserǁ__init____mutmut_2 # type: ignore # mutmut generated
mutants_xǁRobustSSEParserǁ__init____mutmut['xǁRobustSSEParserǁ__init____mutmut_3'] = RobustSSEParser.xǁRobustSSEParserǁ__init____mutmut_3 # type: ignore # mutmut generated
mutants_xǁRobustSSEParserǁ__init____mutmut['xǁRobustSSEParserǁ__init____mutmut_4'] = RobustSSEParser.xǁRobustSSEParserǁ__init____mutmut_4 # type: ignore # mutmut generated
mutants_xǁRobustSSEParserǁ__init____mutmut['xǁRobustSSEParserǁ__init____mutmut_5'] = RobustSSEParser.xǁRobustSSEParserǁ__init____mutmut_5 # type: ignore # mutmut generated
mutants_xǁRobustSSEParserǁ__init____mutmut['xǁRobustSSEParserǁ__init____mutmut_6'] = RobustSSEParser.xǁRobustSSEParserǁ__init____mutmut_6 # type: ignore # mutmut generated
mutants_xǁRobustSSEParserǁ__init____mutmut['xǁRobustSSEParserǁ__init____mutmut_7'] = RobustSSEParser.xǁRobustSSEParserǁ__init____mutmut_7 # type: ignore # mutmut generated
mutants_xǁRobustSSEParserǁ__init____mutmut['xǁRobustSSEParserǁ__init____mutmut_8'] = RobustSSEParser.xǁRobustSSEParserǁ__init____mutmut_8 # type: ignore # mutmut generated
mutants_xǁRobustSSEParserǁ__init____mutmut['xǁRobustSSEParserǁ__init____mutmut_9'] = RobustSSEParser.xǁRobustSSEParserǁ__init____mutmut_9 # type: ignore # mutmut generated
mutants_xǁRobustSSEParserǁ__init____mutmut['xǁRobustSSEParserǁ__init____mutmut_10'] = RobustSSEParser.xǁRobustSSEParserǁ__init____mutmut_10 # type: ignore # mutmut generated
mutants_xǁRobustSSEParserǁ__init____mutmut['xǁRobustSSEParserǁ__init____mutmut_11'] = RobustSSEParser.xǁRobustSSEParserǁ__init____mutmut_11 # type: ignore # mutmut generated
mutants_xǁRobustSSEParserǁ__init____mutmut['xǁRobustSSEParserǁ__init____mutmut_12'] = RobustSSEParser.xǁRobustSSEParserǁ__init____mutmut_12 # type: ignore # mutmut generated
mutants_xǁRobustSSEParserǁ__init____mutmut['xǁRobustSSEParserǁ__init____mutmut_13'] = RobustSSEParser.xǁRobustSSEParserǁ__init____mutmut_13 # type: ignore # mutmut generated
mutants_xǁRobustSSEParserǁ__init____mutmut['xǁRobustSSEParserǁ__init____mutmut_14'] = RobustSSEParser.xǁRobustSSEParserǁ__init____mutmut_14 # type: ignore # mutmut generated
mutants_xǁRobustSSEParserǁ__init____mutmut['xǁRobustSSEParserǁ__init____mutmut_15'] = RobustSSEParser.xǁRobustSSEParserǁ__init____mutmut_15 # type: ignore # mutmut generated
mutants_xǁRobustSSEParserǁ__init____mutmut['xǁRobustSSEParserǁ__init____mutmut_16'] = RobustSSEParser.xǁRobustSSEParserǁ__init____mutmut_16 # type: ignore # mutmut generated
mutants_xǁRobustSSEParserǁ__init____mutmut['xǁRobustSSEParserǁ__init____mutmut_17'] = RobustSSEParser.xǁRobustSSEParserǁ__init____mutmut_17 # type: ignore # mutmut generated
mutants_xǁRobustSSEParserǁ__init____mutmut['xǁRobustSSEParserǁ__init____mutmut_18'] = RobustSSEParser.xǁRobustSSEParserǁ__init____mutmut_18 # type: ignore # mutmut generated
mutants_xǁRobustSSEParserǁ__init____mutmut['xǁRobustSSEParserǁ__init____mutmut_19'] = RobustSSEParser.xǁRobustSSEParserǁ__init____mutmut_19 # type: ignore # mutmut generated
mutants_xǁRobustSSEParserǁ__init____mutmut['xǁRobustSSEParserǁ__init____mutmut_20'] = RobustSSEParser.xǁRobustSSEParserǁ__init____mutmut_20 # type: ignore # mutmut generated
mutants_xǁRobustSSEParserǁ__init____mutmut['xǁRobustSSEParserǁ__init____mutmut_21'] = RobustSSEParser.xǁRobustSSEParserǁ__init____mutmut_21 # type: ignore # mutmut generated
mutants_xǁRobustSSEParserǁ__init____mutmut['xǁRobustSSEParserǁ__init____mutmut_22'] = RobustSSEParser.xǁRobustSSEParserǁ__init____mutmut_22 # type: ignore # mutmut generated

mutants_xǁRobustSSEParserǁfeed__mutmut['_mutmut_orig'] = RobustSSEParser.xǁRobustSSEParserǁfeed__mutmut_orig # type: ignore # mutmut generated
mutants_xǁRobustSSEParserǁfeed__mutmut['xǁRobustSSEParserǁfeed__mutmut_1'] = RobustSSEParser.xǁRobustSSEParserǁfeed__mutmut_1 # type: ignore # mutmut generated
mutants_xǁRobustSSEParserǁfeed__mutmut['xǁRobustSSEParserǁfeed__mutmut_2'] = RobustSSEParser.xǁRobustSSEParserǁfeed__mutmut_2 # type: ignore # mutmut generated
mutants_xǁRobustSSEParserǁfeed__mutmut['xǁRobustSSEParserǁfeed__mutmut_3'] = RobustSSEParser.xǁRobustSSEParserǁfeed__mutmut_3 # type: ignore # mutmut generated
mutants_xǁRobustSSEParserǁfeed__mutmut['xǁRobustSSEParserǁfeed__mutmut_4'] = RobustSSEParser.xǁRobustSSEParserǁfeed__mutmut_4 # type: ignore # mutmut generated
mutants_xǁRobustSSEParserǁfeed__mutmut['xǁRobustSSEParserǁfeed__mutmut_5'] = RobustSSEParser.xǁRobustSSEParserǁfeed__mutmut_5 # type: ignore # mutmut generated
mutants_xǁRobustSSEParserǁfeed__mutmut['xǁRobustSSEParserǁfeed__mutmut_6'] = RobustSSEParser.xǁRobustSSEParserǁfeed__mutmut_6 # type: ignore # mutmut generated
mutants_xǁRobustSSEParserǁfeed__mutmut['xǁRobustSSEParserǁfeed__mutmut_7'] = RobustSSEParser.xǁRobustSSEParserǁfeed__mutmut_7 # type: ignore # mutmut generated
mutants_xǁRobustSSEParserǁfeed__mutmut['xǁRobustSSEParserǁfeed__mutmut_8'] = RobustSSEParser.xǁRobustSSEParserǁfeed__mutmut_8 # type: ignore # mutmut generated
mutants_xǁRobustSSEParserǁfeed__mutmut['xǁRobustSSEParserǁfeed__mutmut_9'] = RobustSSEParser.xǁRobustSSEParserǁfeed__mutmut_9 # type: ignore # mutmut generated
mutants_xǁRobustSSEParserǁfeed__mutmut['xǁRobustSSEParserǁfeed__mutmut_10'] = RobustSSEParser.xǁRobustSSEParserǁfeed__mutmut_10 # type: ignore # mutmut generated
mutants_xǁRobustSSEParserǁfeed__mutmut['xǁRobustSSEParserǁfeed__mutmut_11'] = RobustSSEParser.xǁRobustSSEParserǁfeed__mutmut_11 # type: ignore # mutmut generated
mutants_xǁRobustSSEParserǁfeed__mutmut['xǁRobustSSEParserǁfeed__mutmut_12'] = RobustSSEParser.xǁRobustSSEParserǁfeed__mutmut_12 # type: ignore # mutmut generated
mutants_xǁRobustSSEParserǁfeed__mutmut['xǁRobustSSEParserǁfeed__mutmut_13'] = RobustSSEParser.xǁRobustSSEParserǁfeed__mutmut_13 # type: ignore # mutmut generated
mutants_xǁRobustSSEParserǁfeed__mutmut['xǁRobustSSEParserǁfeed__mutmut_14'] = RobustSSEParser.xǁRobustSSEParserǁfeed__mutmut_14 # type: ignore # mutmut generated
mutants_xǁRobustSSEParserǁfeed__mutmut['xǁRobustSSEParserǁfeed__mutmut_15'] = RobustSSEParser.xǁRobustSSEParserǁfeed__mutmut_15 # type: ignore # mutmut generated
mutants_xǁRobustSSEParserǁfeed__mutmut['xǁRobustSSEParserǁfeed__mutmut_16'] = RobustSSEParser.xǁRobustSSEParserǁfeed__mutmut_16 # type: ignore # mutmut generated
mutants_xǁRobustSSEParserǁfeed__mutmut['xǁRobustSSEParserǁfeed__mutmut_17'] = RobustSSEParser.xǁRobustSSEParserǁfeed__mutmut_17 # type: ignore # mutmut generated
mutants_xǁRobustSSEParserǁfeed__mutmut['xǁRobustSSEParserǁfeed__mutmut_18'] = RobustSSEParser.xǁRobustSSEParserǁfeed__mutmut_18 # type: ignore # mutmut generated
mutants_xǁRobustSSEParserǁfeed__mutmut['xǁRobustSSEParserǁfeed__mutmut_19'] = RobustSSEParser.xǁRobustSSEParserǁfeed__mutmut_19 # type: ignore # mutmut generated
mutants_xǁRobustSSEParserǁfeed__mutmut['xǁRobustSSEParserǁfeed__mutmut_20'] = RobustSSEParser.xǁRobustSSEParserǁfeed__mutmut_20 # type: ignore # mutmut generated
mutants_xǁRobustSSEParserǁfeed__mutmut['xǁRobustSSEParserǁfeed__mutmut_21'] = RobustSSEParser.xǁRobustSSEParserǁfeed__mutmut_21 # type: ignore # mutmut generated
mutants_xǁRobustSSEParserǁfeed__mutmut['xǁRobustSSEParserǁfeed__mutmut_22'] = RobustSSEParser.xǁRobustSSEParserǁfeed__mutmut_22 # type: ignore # mutmut generated
mutants_xǁRobustSSEParserǁfeed__mutmut['xǁRobustSSEParserǁfeed__mutmut_23'] = RobustSSEParser.xǁRobustSSEParserǁfeed__mutmut_23 # type: ignore # mutmut generated
mutants_xǁRobustSSEParserǁfeed__mutmut['xǁRobustSSEParserǁfeed__mutmut_24'] = RobustSSEParser.xǁRobustSSEParserǁfeed__mutmut_24 # type: ignore # mutmut generated
mutants_xǁRobustSSEParserǁfeed__mutmut['xǁRobustSSEParserǁfeed__mutmut_25'] = RobustSSEParser.xǁRobustSSEParserǁfeed__mutmut_25 # type: ignore # mutmut generated
mutants_xǁRobustSSEParserǁfeed__mutmut['xǁRobustSSEParserǁfeed__mutmut_26'] = RobustSSEParser.xǁRobustSSEParserǁfeed__mutmut_26 # type: ignore # mutmut generated
mutants_xǁRobustSSEParserǁfeed__mutmut['xǁRobustSSEParserǁfeed__mutmut_27'] = RobustSSEParser.xǁRobustSSEParserǁfeed__mutmut_27 # type: ignore # mutmut generated
mutants_xǁRobustSSEParserǁfeed__mutmut['xǁRobustSSEParserǁfeed__mutmut_28'] = RobustSSEParser.xǁRobustSSEParserǁfeed__mutmut_28 # type: ignore # mutmut generated
mutants_xǁRobustSSEParserǁfeed__mutmut['xǁRobustSSEParserǁfeed__mutmut_29'] = RobustSSEParser.xǁRobustSSEParserǁfeed__mutmut_29 # type: ignore # mutmut generated
mutants_xǁRobustSSEParserǁfeed__mutmut['xǁRobustSSEParserǁfeed__mutmut_30'] = RobustSSEParser.xǁRobustSSEParserǁfeed__mutmut_30 # type: ignore # mutmut generated
mutants_xǁRobustSSEParserǁfeed__mutmut['xǁRobustSSEParserǁfeed__mutmut_31'] = RobustSSEParser.xǁRobustSSEParserǁfeed__mutmut_31 # type: ignore # mutmut generated
mutants_xǁRobustSSEParserǁfeed__mutmut['xǁRobustSSEParserǁfeed__mutmut_32'] = RobustSSEParser.xǁRobustSSEParserǁfeed__mutmut_32 # type: ignore # mutmut generated
mutants_xǁRobustSSEParserǁfeed__mutmut['xǁRobustSSEParserǁfeed__mutmut_33'] = RobustSSEParser.xǁRobustSSEParserǁfeed__mutmut_33 # type: ignore # mutmut generated
mutants_xǁRobustSSEParserǁfeed__mutmut['xǁRobustSSEParserǁfeed__mutmut_34'] = RobustSSEParser.xǁRobustSSEParserǁfeed__mutmut_34 # type: ignore # mutmut generated
mutants_xǁRobustSSEParserǁfeed__mutmut['xǁRobustSSEParserǁfeed__mutmut_35'] = RobustSSEParser.xǁRobustSSEParserǁfeed__mutmut_35 # type: ignore # mutmut generated

mutants_xǁRobustSSEParserǁ_parse_line__mutmut['_mutmut_orig'] = RobustSSEParser.xǁRobustSSEParserǁ_parse_line__mutmut_orig # type: ignore # mutmut generated
mutants_xǁRobustSSEParserǁ_parse_line__mutmut['xǁRobustSSEParserǁ_parse_line__mutmut_1'] = RobustSSEParser.xǁRobustSSEParserǁ_parse_line__mutmut_1 # type: ignore # mutmut generated
mutants_xǁRobustSSEParserǁ_parse_line__mutmut['xǁRobustSSEParserǁ_parse_line__mutmut_2'] = RobustSSEParser.xǁRobustSSEParserǁ_parse_line__mutmut_2 # type: ignore # mutmut generated
mutants_xǁRobustSSEParserǁ_parse_line__mutmut['xǁRobustSSEParserǁ_parse_line__mutmut_3'] = RobustSSEParser.xǁRobustSSEParserǁ_parse_line__mutmut_3 # type: ignore # mutmut generated
mutants_xǁRobustSSEParserǁ_parse_line__mutmut['xǁRobustSSEParserǁ_parse_line__mutmut_4'] = RobustSSEParser.xǁRobustSSEParserǁ_parse_line__mutmut_4 # type: ignore # mutmut generated
mutants_xǁRobustSSEParserǁ_parse_line__mutmut['xǁRobustSSEParserǁ_parse_line__mutmut_5'] = RobustSSEParser.xǁRobustSSEParserǁ_parse_line__mutmut_5 # type: ignore # mutmut generated
mutants_xǁRobustSSEParserǁ_parse_line__mutmut['xǁRobustSSEParserǁ_parse_line__mutmut_6'] = RobustSSEParser.xǁRobustSSEParserǁ_parse_line__mutmut_6 # type: ignore # mutmut generated
mutants_xǁRobustSSEParserǁ_parse_line__mutmut['xǁRobustSSEParserǁ_parse_line__mutmut_7'] = RobustSSEParser.xǁRobustSSEParserǁ_parse_line__mutmut_7 # type: ignore # mutmut generated
mutants_xǁRobustSSEParserǁ_parse_line__mutmut['xǁRobustSSEParserǁ_parse_line__mutmut_8'] = RobustSSEParser.xǁRobustSSEParserǁ_parse_line__mutmut_8 # type: ignore # mutmut generated
mutants_xǁRobustSSEParserǁ_parse_line__mutmut['xǁRobustSSEParserǁ_parse_line__mutmut_9'] = RobustSSEParser.xǁRobustSSEParserǁ_parse_line__mutmut_9 # type: ignore # mutmut generated
mutants_xǁRobustSSEParserǁ_parse_line__mutmut['xǁRobustSSEParserǁ_parse_line__mutmut_10'] = RobustSSEParser.xǁRobustSSEParserǁ_parse_line__mutmut_10 # type: ignore # mutmut generated
mutants_xǁRobustSSEParserǁ_parse_line__mutmut['xǁRobustSSEParserǁ_parse_line__mutmut_11'] = RobustSSEParser.xǁRobustSSEParserǁ_parse_line__mutmut_11 # type: ignore # mutmut generated
mutants_xǁRobustSSEParserǁ_parse_line__mutmut['xǁRobustSSEParserǁ_parse_line__mutmut_12'] = RobustSSEParser.xǁRobustSSEParserǁ_parse_line__mutmut_12 # type: ignore # mutmut generated
mutants_xǁRobustSSEParserǁ_parse_line__mutmut['xǁRobustSSEParserǁ_parse_line__mutmut_13'] = RobustSSEParser.xǁRobustSSEParserǁ_parse_line__mutmut_13 # type: ignore # mutmut generated
mutants_xǁRobustSSEParserǁ_parse_line__mutmut['xǁRobustSSEParserǁ_parse_line__mutmut_14'] = RobustSSEParser.xǁRobustSSEParserǁ_parse_line__mutmut_14 # type: ignore # mutmut generated

mutants_xǁRobustSSEParserǁ_is_keepalive__mutmut['_mutmut_orig'] = RobustSSEParser.xǁRobustSSEParserǁ_is_keepalive__mutmut_orig # type: ignore # mutmut generated
mutants_xǁRobustSSEParserǁ_is_keepalive__mutmut['xǁRobustSSEParserǁ_is_keepalive__mutmut_1'] = RobustSSEParser.xǁRobustSSEParserǁ_is_keepalive__mutmut_1 # type: ignore # mutmut generated
mutants_xǁRobustSSEParserǁ_is_keepalive__mutmut['xǁRobustSSEParserǁ_is_keepalive__mutmut_2'] = RobustSSEParser.xǁRobustSSEParserǁ_is_keepalive__mutmut_2 # type: ignore # mutmut generated
mutants_xǁRobustSSEParserǁ_is_keepalive__mutmut['xǁRobustSSEParserǁ_is_keepalive__mutmut_3'] = RobustSSEParser.xǁRobustSSEParserǁ_is_keepalive__mutmut_3 # type: ignore # mutmut generated
mutants_xǁRobustSSEParserǁ_is_keepalive__mutmut['xǁRobustSSEParserǁ_is_keepalive__mutmut_4'] = RobustSSEParser.xǁRobustSSEParserǁ_is_keepalive__mutmut_4 # type: ignore # mutmut generated
mutants_xǁRobustSSEParserǁ_is_keepalive__mutmut['xǁRobustSSEParserǁ_is_keepalive__mutmut_5'] = RobustSSEParser.xǁRobustSSEParserǁ_is_keepalive__mutmut_5 # type: ignore # mutmut generated
mutants_xǁRobustSSEParserǁ_is_keepalive__mutmut['xǁRobustSSEParserǁ_is_keepalive__mutmut_6'] = RobustSSEParser.xǁRobustSSEParserǁ_is_keepalive__mutmut_6 # type: ignore # mutmut generated

mutants_xǁRobustSSEParserǁ_mark_activity__mutmut['_mutmut_orig'] = RobustSSEParser.xǁRobustSSEParserǁ_mark_activity__mutmut_orig # type: ignore # mutmut generated
mutants_xǁRobustSSEParserǁ_mark_activity__mutmut['xǁRobustSSEParserǁ_mark_activity__mutmut_1'] = RobustSSEParser.xǁRobustSSEParserǁ_mark_activity__mutmut_1 # type: ignore # mutmut generated

mutants_xǁRobustSSEParserǁ_is_valid_json__mutmut['_mutmut_orig'] = RobustSSEParser.xǁRobustSSEParserǁ_is_valid_json__mutmut_orig # type: ignore # mutmut generated
mutants_xǁRobustSSEParserǁ_is_valid_json__mutmut['xǁRobustSSEParserǁ_is_valid_json__mutmut_1'] = RobustSSEParser.xǁRobustSSEParserǁ_is_valid_json__mutmut_1 # type: ignore # mutmut generated
mutants_xǁRobustSSEParserǁ_is_valid_json__mutmut['xǁRobustSSEParserǁ_is_valid_json__mutmut_2'] = RobustSSEParser.xǁRobustSSEParserǁ_is_valid_json__mutmut_2 # type: ignore # mutmut generated
mutants_xǁRobustSSEParserǁ_is_valid_json__mutmut['xǁRobustSSEParserǁ_is_valid_json__mutmut_3'] = RobustSSEParser.xǁRobustSSEParserǁ_is_valid_json__mutmut_3 # type: ignore # mutmut generated
mutants_xǁRobustSSEParserǁ_is_valid_json__mutmut['xǁRobustSSEParserǁ_is_valid_json__mutmut_4'] = RobustSSEParser.xǁRobustSSEParserǁ_is_valid_json__mutmut_4 # type: ignore # mutmut generated
mutants_xǁRobustSSEParserǁ_is_valid_json__mutmut['xǁRobustSSEParserǁ_is_valid_json__mutmut_5'] = RobustSSEParser.xǁRobustSSEParserǁ_is_valid_json__mutmut_5 # type: ignore # mutmut generated
mutants_xǁRobustSSEParserǁ_is_valid_json__mutmut['xǁRobustSSEParserǁ_is_valid_json__mutmut_6'] = RobustSSEParser.xǁRobustSSEParserǁ_is_valid_json__mutmut_6 # type: ignore # mutmut generated
mutants_xǁRobustSSEParserǁ_is_valid_json__mutmut['xǁRobustSSEParserǁ_is_valid_json__mutmut_7'] = RobustSSEParser.xǁRobustSSEParserǁ_is_valid_json__mutmut_7 # type: ignore # mutmut generated
mutants_xǁRobustSSEParserǁ_is_valid_json__mutmut['xǁRobustSSEParserǁ_is_valid_json__mutmut_8'] = RobustSSEParser.xǁRobustSSEParserǁ_is_valid_json__mutmut_8 # type: ignore # mutmut generated
mutants_xǁRobustSSEParserǁ_is_valid_json__mutmut['xǁRobustSSEParserǁ_is_valid_json__mutmut_9'] = RobustSSEParser.xǁRobustSSEParserǁ_is_valid_json__mutmut_9 # type: ignore # mutmut generated
mutants_xǁRobustSSEParserǁ_is_valid_json__mutmut['xǁRobustSSEParserǁ_is_valid_json__mutmut_10'] = RobustSSEParser.xǁRobustSSEParserǁ_is_valid_json__mutmut_10 # type: ignore # mutmut generated
mutants_xǁRobustSSEParserǁ_is_valid_json__mutmut['xǁRobustSSEParserǁ_is_valid_json__mutmut_11'] = RobustSSEParser.xǁRobustSSEParserǁ_is_valid_json__mutmut_11 # type: ignore # mutmut generated
mutants_xǁRobustSSEParserǁ_is_valid_json__mutmut['xǁRobustSSEParserǁ_is_valid_json__mutmut_12'] = RobustSSEParser.xǁRobustSSEParserǁ_is_valid_json__mutmut_12 # type: ignore # mutmut generated
mutants_xǁRobustSSEParserǁ_is_valid_json__mutmut['xǁRobustSSEParserǁ_is_valid_json__mutmut_13'] = RobustSSEParser.xǁRobustSSEParserǁ_is_valid_json__mutmut_13 # type: ignore # mutmut generated
mutants_xǁRobustSSEParserǁ_is_valid_json__mutmut['xǁRobustSSEParserǁ_is_valid_json__mutmut_14'] = RobustSSEParser.xǁRobustSSEParserǁ_is_valid_json__mutmut_14 # type: ignore # mutmut generated
mutants_xǁRobustSSEParserǁ_is_valid_json__mutmut['xǁRobustSSEParserǁ_is_valid_json__mutmut_15'] = RobustSSEParser.xǁRobustSSEParserǁ_is_valid_json__mutmut_15 # type: ignore # mutmut generated
mutants_xǁRobustSSEParserǁ_is_valid_json__mutmut['xǁRobustSSEParserǁ_is_valid_json__mutmut_16'] = RobustSSEParser.xǁRobustSSEParserǁ_is_valid_json__mutmut_16 # type: ignore # mutmut generated
mutants_xǁRobustSSEParserǁ_is_valid_json__mutmut['xǁRobustSSEParserǁ_is_valid_json__mutmut_17'] = RobustSSEParser.xǁRobustSSEParserǁ_is_valid_json__mutmut_17 # type: ignore # mutmut generated
mutants_xǁRobustSSEParserǁ_is_valid_json__mutmut['xǁRobustSSEParserǁ_is_valid_json__mutmut_18'] = RobustSSEParser.xǁRobustSSEParserǁ_is_valid_json__mutmut_18 # type: ignore # mutmut generated
mutants_xǁRobustSSEParserǁ_is_valid_json__mutmut['xǁRobustSSEParserǁ_is_valid_json__mutmut_19'] = RobustSSEParser.xǁRobustSSEParserǁ_is_valid_json__mutmut_19 # type: ignore # mutmut generated
mutants_xǁRobustSSEParserǁ_is_valid_json__mutmut['xǁRobustSSEParserǁ_is_valid_json__mutmut_20'] = RobustSSEParser.xǁRobustSSEParserǁ_is_valid_json__mutmut_20 # type: ignore # mutmut generated
mutants_xǁRobustSSEParserǁ_is_valid_json__mutmut['xǁRobustSSEParserǁ_is_valid_json__mutmut_21'] = RobustSSEParser.xǁRobustSSEParserǁ_is_valid_json__mutmut_21 # type: ignore # mutmut generated
mutants_xǁRobustSSEParserǁ_is_valid_json__mutmut['xǁRobustSSEParserǁ_is_valid_json__mutmut_22'] = RobustSSEParser.xǁRobustSSEParserǁ_is_valid_json__mutmut_22 # type: ignore # mutmut generated
mutants_xǁRobustSSEParserǁ_is_valid_json__mutmut['xǁRobustSSEParserǁ_is_valid_json__mutmut_23'] = RobustSSEParser.xǁRobustSSEParserǁ_is_valid_json__mutmut_23 # type: ignore # mutmut generated
mutants_xǁRobustSSEParserǁ_is_valid_json__mutmut['xǁRobustSSEParserǁ_is_valid_json__mutmut_24'] = RobustSSEParser.xǁRobustSSEParserǁ_is_valid_json__mutmut_24 # type: ignore # mutmut generated
mutants_xǁRobustSSEParserǁ_is_valid_json__mutmut['xǁRobustSSEParserǁ_is_valid_json__mutmut_25'] = RobustSSEParser.xǁRobustSSEParserǁ_is_valid_json__mutmut_25 # type: ignore # mutmut generated
mutants_xǁRobustSSEParserǁ_is_valid_json__mutmut['xǁRobustSSEParserǁ_is_valid_json__mutmut_26'] = RobustSSEParser.xǁRobustSSEParserǁ_is_valid_json__mutmut_26 # type: ignore # mutmut generated

mutants_xǁRobustSSEParserǁcheck_heartbeat__mutmut['_mutmut_orig'] = RobustSSEParser.xǁRobustSSEParserǁcheck_heartbeat__mutmut_orig # type: ignore # mutmut generated
mutants_xǁRobustSSEParserǁcheck_heartbeat__mutmut['xǁRobustSSEParserǁcheck_heartbeat__mutmut_1'] = RobustSSEParser.xǁRobustSSEParserǁcheck_heartbeat__mutmut_1 # type: ignore # mutmut generated
mutants_xǁRobustSSEParserǁcheck_heartbeat__mutmut['xǁRobustSSEParserǁcheck_heartbeat__mutmut_2'] = RobustSSEParser.xǁRobustSSEParserǁcheck_heartbeat__mutmut_2 # type: ignore # mutmut generated
mutants_xǁRobustSSEParserǁcheck_heartbeat__mutmut['xǁRobustSSEParserǁcheck_heartbeat__mutmut_3'] = RobustSSEParser.xǁRobustSSEParserǁcheck_heartbeat__mutmut_3 # type: ignore # mutmut generated
mutants_xǁRobustSSEParserǁcheck_heartbeat__mutmut['xǁRobustSSEParserǁcheck_heartbeat__mutmut_4'] = RobustSSEParser.xǁRobustSSEParserǁcheck_heartbeat__mutmut_4 # type: ignore # mutmut generated
mutants_xǁRobustSSEParserǁcheck_heartbeat__mutmut['xǁRobustSSEParserǁcheck_heartbeat__mutmut_5'] = RobustSSEParser.xǁRobustSSEParserǁcheck_heartbeat__mutmut_5 # type: ignore # mutmut generated
mutants_xǁRobustSSEParserǁcheck_heartbeat__mutmut['xǁRobustSSEParserǁcheck_heartbeat__mutmut_6'] = RobustSSEParser.xǁRobustSSEParserǁcheck_heartbeat__mutmut_6 # type: ignore # mutmut generated
mutants_xǁRobustSSEParserǁcheck_heartbeat__mutmut['xǁRobustSSEParserǁcheck_heartbeat__mutmut_7'] = RobustSSEParser.xǁRobustSSEParserǁcheck_heartbeat__mutmut_7 # type: ignore # mutmut generated
mutants_xǁRobustSSEParserǁcheck_heartbeat__mutmut['xǁRobustSSEParserǁcheck_heartbeat__mutmut_8'] = RobustSSEParser.xǁRobustSSEParserǁcheck_heartbeat__mutmut_8 # type: ignore # mutmut generated
mutants_xǁRobustSSEParserǁcheck_heartbeat__mutmut['xǁRobustSSEParserǁcheck_heartbeat__mutmut_9'] = RobustSSEParser.xǁRobustSSEParserǁcheck_heartbeat__mutmut_9 # type: ignore # mutmut generated
mutants_xǁRobustSSEParserǁcheck_heartbeat__mutmut['xǁRobustSSEParserǁcheck_heartbeat__mutmut_10'] = RobustSSEParser.xǁRobustSSEParserǁcheck_heartbeat__mutmut_10 # type: ignore # mutmut generated
mutants_xǁRobustSSEParserǁcheck_heartbeat__mutmut['xǁRobustSSEParserǁcheck_heartbeat__mutmut_11'] = RobustSSEParser.xǁRobustSSEParserǁcheck_heartbeat__mutmut_11 # type: ignore # mutmut generated
mutants_xǁRobustSSEParserǁcheck_heartbeat__mutmut['xǁRobustSSEParserǁcheck_heartbeat__mutmut_12'] = RobustSSEParser.xǁRobustSSEParserǁcheck_heartbeat__mutmut_12 # type: ignore # mutmut generated
mutants_xǁRobustSSEParserǁcheck_heartbeat__mutmut['xǁRobustSSEParserǁcheck_heartbeat__mutmut_13'] = RobustSSEParser.xǁRobustSSEParserǁcheck_heartbeat__mutmut_13 # type: ignore # mutmut generated
mutants_xǁRobustSSEParserǁcheck_heartbeat__mutmut['xǁRobustSSEParserǁcheck_heartbeat__mutmut_14'] = RobustSSEParser.xǁRobustSSEParserǁcheck_heartbeat__mutmut_14 # type: ignore # mutmut generated
mutants_xǁRobustSSEParserǁcheck_heartbeat__mutmut['xǁRobustSSEParserǁcheck_heartbeat__mutmut_15'] = RobustSSEParser.xǁRobustSSEParserǁcheck_heartbeat__mutmut_15 # type: ignore # mutmut generated
mutants_xǁRobustSSEParserǁcheck_heartbeat__mutmut['xǁRobustSSEParserǁcheck_heartbeat__mutmut_16'] = RobustSSEParser.xǁRobustSSEParserǁcheck_heartbeat__mutmut_16 # type: ignore # mutmut generated
mutants_xǁRobustSSEParserǁcheck_heartbeat__mutmut['xǁRobustSSEParserǁcheck_heartbeat__mutmut_17'] = RobustSSEParser.xǁRobustSSEParserǁcheck_heartbeat__mutmut_17 # type: ignore # mutmut generated
mutants_xǁRobustSSEParserǁcheck_heartbeat__mutmut['xǁRobustSSEParserǁcheck_heartbeat__mutmut_18'] = RobustSSEParser.xǁRobustSSEParserǁcheck_heartbeat__mutmut_18 # type: ignore # mutmut generated
mutants_xǁRobustSSEParserǁcheck_heartbeat__mutmut['xǁRobustSSEParserǁcheck_heartbeat__mutmut_19'] = RobustSSEParser.xǁRobustSSEParserǁcheck_heartbeat__mutmut_19 # type: ignore # mutmut generated
mutants_xǁRobustSSEParserǁcheck_heartbeat__mutmut['xǁRobustSSEParserǁcheck_heartbeat__mutmut_20'] = RobustSSEParser.xǁRobustSSEParserǁcheck_heartbeat__mutmut_20 # type: ignore # mutmut generated
mutants_x__anext_or_done__mutmut: MutantDict = {}  # type: ignore


@_mutmut_mutated(mutants_x__anext_or_done__mutmut)
async def _anext_or_done(aiter: AsyncIterator[bytes]) -> tuple[bytes, bool]:
    """Await one item from an async bytes iterator; returns (item, False) on success or (b"", True) on StopAsyncIteration; prevents PEP 479 RuntimeError in wait_for."""
    try:
        item = await aiter.__anext__()
        return item, False
    except StopAsyncIteration:
        return b"", True


async def x__anext_or_done__mutmut_orig(aiter: AsyncIterator[bytes]) -> tuple[bytes, bool]:
    """Await one item from an async bytes iterator; returns (item, False) on success or (b"", True) on StopAsyncIteration; prevents PEP 479 RuntimeError in wait_for."""
    try:
        item = await aiter.__anext__()
        return item, False
    except StopAsyncIteration:
        return b"", True


async def x__anext_or_done__mutmut_1(aiter: AsyncIterator[bytes]) -> tuple[bytes, bool]:
    """Await one item from an async bytes iterator; returns (item, False) on success or (b"", True) on StopAsyncIteration; prevents PEP 479 RuntimeError in wait_for."""
    try:
        item = None
        return item, False
    except StopAsyncIteration:
        return b"", True


async def x__anext_or_done__mutmut_2(aiter: AsyncIterator[bytes]) -> tuple[bytes, bool]:
    """Await one item from an async bytes iterator; returns (item, False) on success or (b"", True) on StopAsyncIteration; prevents PEP 479 RuntimeError in wait_for."""
    try:
        item = await aiter.__anext__()
        return item, True
    except StopAsyncIteration:
        return b"", True


async def x__anext_or_done__mutmut_3(aiter: AsyncIterator[bytes]) -> tuple[bytes, bool]:
    """Await one item from an async bytes iterator; returns (item, False) on success or (b"", True) on StopAsyncIteration; prevents PEP 479 RuntimeError in wait_for."""
    try:
        item = await aiter.__anext__()
        return item, False
    except StopAsyncIteration:
        return b"XXXX", True


async def x__anext_or_done__mutmut_4(aiter: AsyncIterator[bytes]) -> tuple[bytes, bool]:
    """Await one item from an async bytes iterator; returns (item, False) on success or (b"", True) on StopAsyncIteration; prevents PEP 479 RuntimeError in wait_for."""
    try:
        item = await aiter.__anext__()
        return item, False
    except StopAsyncIteration:
        return b"", False

mutants_x__anext_or_done__mutmut['_mutmut_orig'] = x__anext_or_done__mutmut_orig # type: ignore # mutmut generated
mutants_x__anext_or_done__mutmut['x__anext_or_done__mutmut_1'] = x__anext_or_done__mutmut_1 # type: ignore # mutmut generated
mutants_x__anext_or_done__mutmut['x__anext_or_done__mutmut_2'] = x__anext_or_done__mutmut_2 # type: ignore # mutmut generated
mutants_x__anext_or_done__mutmut['x__anext_or_done__mutmut_3'] = x__anext_or_done__mutmut_3 # type: ignore # mutmut generated
mutants_x__anext_or_done__mutmut['x__anext_or_done__mutmut_4'] = x__anext_or_done__mutmut_4 # type: ignore # mutmut generated
