#!/usr/bin/env python3
"""scripts/shared/logger.py

Shared logging setup for entry-point scripts.

Usage (entry-point scripts only):
    logger = Logger(__name__, "/opt/llm/logs/xxx.log")

Library modules should use:
    logger = logging.getLogger(__name__)

Structured log (JSON-lines):
    logger = Logger(__name__, "/opt/llm/logs/audit.log", structured_log=True)
    logger.set_context(turn_id="abc", session_id="1")
    logger.clear_context()
"""

import logging
import sys
from contextvars import ContextVar
from typing import Any

from shared.json_utils import dumps as _json_dumps

_fallback_logger = logging.getLogger("shared.logger.fallback")
if not _fallback_logger.handlers:
    _fallback_logger.addHandler(logging.StreamHandler(sys.stderr))
    _fallback_logger.setLevel(logging.WARNING)


from mutmut.mutation.trampoline import wrap_in_trampoline as _mutmut_mutated, MutantDict
mutants_x__require_str__mutmut: MutantDict = {}  # type: ignore


@_mutmut_mutated(mutants_x__require_str__mutmut)
def _require_str(value: object, name: str) -> None:
    """Validate that value is a non-empty string; raises ValueError otherwise."""
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{name} must be a non-empty str, got: {value!r}")


def x__require_str__mutmut_orig(value: object, name: str) -> None:
    """Validate that value is a non-empty string; raises ValueError otherwise."""
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{name} must be a non-empty str, got: {value!r}")


def x__require_str__mutmut_1(value: object, name: str) -> None:
    """Validate that value is a non-empty string; raises ValueError otherwise."""
    if not isinstance(value, str) and not value.strip():
        raise ValueError(f"{name} must be a non-empty str, got: {value!r}")


def x__require_str__mutmut_2(value: object, name: str) -> None:
    """Validate that value is a non-empty string; raises ValueError otherwise."""
    if isinstance(value, str) or not value.strip():
        raise ValueError(f"{name} must be a non-empty str, got: {value!r}")


def x__require_str__mutmut_3(value: object, name: str) -> None:
    """Validate that value is a non-empty string; raises ValueError otherwise."""
    if not isinstance(value, str) or value.strip():
        raise ValueError(f"{name} must be a non-empty str, got: {value!r}")


def x__require_str__mutmut_4(value: object, name: str) -> None:
    """Validate that value is a non-empty string; raises ValueError otherwise."""
    if not isinstance(value, str) or not value.strip():
        raise ValueError(None)

mutants_x__require_str__mutmut['_mutmut_orig'] = x__require_str__mutmut_orig # type: ignore # mutmut generated
mutants_x__require_str__mutmut['x__require_str__mutmut_1'] = x__require_str__mutmut_1 # type: ignore # mutmut generated
mutants_x__require_str__mutmut['x__require_str__mutmut_2'] = x__require_str__mutmut_2 # type: ignore # mutmut generated
mutants_x__require_str__mutmut['x__require_str__mutmut_3'] = x__require_str__mutmut_3 # type: ignore # mutmut generated
mutants_x__require_str__mutmut['x__require_str__mutmut_4'] = x__require_str__mutmut_4 # type: ignore # mutmut generated
mutants_xǁ_ContextFilterǁ__init____mutmut: MutantDict = {}  # type: ignore
mutants_xǁ_ContextFilterǁset__mutmut: MutantDict = {}  # type: ignore
mutants_xǁ_ContextFilterǁclear__mutmut: MutantDict = {}  # type: ignore
mutants_xǁ_ContextFilterǁfilter__mutmut: MutantDict = {}  # type: ignore


class _ContextFilter(logging.Filter):
    """Injects per-turn trace fields into every LogRecord on this logger.

    Uses contextvars.ContextVar so each asyncio task gets its own context,
    preventing field leakage between concurrent coroutines sharing the same logger.
    """

    @_mutmut_mutated(mutants_xǁ_ContextFilterǁ__init____mutmut)
    def __init__(self) -> None:
        """Initialize with an empty context variable."""
        super().__init__()
        self._cv: ContextVar[dict[str, Any]] = ContextVar("_log_context", default={})  # noqa: S603 — log context keys vary by caller

    def xǁ_ContextFilterǁ__init____mutmut_orig(self) -> None:
        """Initialize with an empty context variable."""
        super().__init__()
        self._cv: ContextVar[dict[str, Any]] = ContextVar("_log_context", default={})  # noqa: S603 — log context keys vary by caller

    def xǁ_ContextFilterǁ__init____mutmut_1(self) -> None:
        """Initialize with an empty context variable."""
        super().__init__()
        self._cv: ContextVar[dict[str, Any]] = None  # noqa: S603 — log context keys vary by caller

    def xǁ_ContextFilterǁ__init____mutmut_2(self) -> None:
        """Initialize with an empty context variable."""
        super().__init__()
        self._cv: ContextVar[dict[str, Any]] = ContextVar(None, default={})  # noqa: S603 — log context keys vary by caller

    def xǁ_ContextFilterǁ__init____mutmut_3(self) -> None:
        """Initialize with an empty context variable."""
        super().__init__()
        self._cv: ContextVar[dict[str, Any]] = ContextVar("_log_context", default=None)  # noqa: S603 — log context keys vary by caller

    def xǁ_ContextFilterǁ__init____mutmut_4(self) -> None:
        """Initialize with an empty context variable."""
        super().__init__()
        self._cv: ContextVar[dict[str, Any]] = ContextVar(default={})  # noqa: S603 — log context keys vary by caller

    def xǁ_ContextFilterǁ__init____mutmut_5(self) -> None:
        """Initialize with an empty context variable."""
        super().__init__()
        self._cv: ContextVar[dict[str, Any]] = ContextVar("_log_context", )  # noqa: S603 — log context keys vary by caller

    def xǁ_ContextFilterǁ__init____mutmut_6(self) -> None:
        """Initialize with an empty context variable."""
        super().__init__()
        self._cv: ContextVar[dict[str, Any]] = ContextVar("XX_log_contextXX", default={})  # noqa: S603 — log context keys vary by caller

    def xǁ_ContextFilterǁ__init____mutmut_7(self) -> None:
        """Initialize with an empty context variable."""
        super().__init__()
        self._cv: ContextVar[dict[str, Any]] = ContextVar("_LOG_CONTEXT", default={})  # noqa: S603 — log context keys vary by caller

    @_mutmut_mutated(mutants_xǁ_ContextFilterǁset__mutmut)
    def set(self, **fields: Any) -> None:
        """Set trace fields into the current context."""
        self._cv.set({k: v for k, v in fields.items() if v is not None})

    def xǁ_ContextFilterǁset__mutmut_orig(self, **fields: Any) -> None:
        """Set trace fields into the current context."""
        self._cv.set({k: v for k, v in fields.items() if v is not None})

    def xǁ_ContextFilterǁset__mutmut_1(self, **fields: Any) -> None:
        """Set trace fields into the current context."""
        self._cv.set(None)

    def xǁ_ContextFilterǁset__mutmut_2(self, **fields: Any) -> None:
        """Set trace fields into the current context."""
        self._cv.set({k: v for k, v in fields.items() if v is None})

    @_mutmut_mutated(mutants_xǁ_ContextFilterǁclear__mutmut)
    def clear(self) -> None:
        """Clear all trace fields from the current context."""
        self._cv.set({})

    def xǁ_ContextFilterǁclear__mutmut_orig(self) -> None:
        """Clear all trace fields from the current context."""
        self._cv.set({})

    def xǁ_ContextFilterǁclear__mutmut_1(self) -> None:
        """Clear all trace fields from the current context."""
        self._cv.set(None)

    @_mutmut_mutated(mutants_xǁ_ContextFilterǁfilter__mutmut)
    def filter(self, record: logging.LogRecord) -> bool:
        """Add trace fields from context to the log record."""
        for k, v in self._cv.get().items():
            setattr(record, k, v)
        return True

    def xǁ_ContextFilterǁfilter__mutmut_orig(self, record: logging.LogRecord) -> bool:
        """Add trace fields from context to the log record."""
        for k, v in self._cv.get().items():
            setattr(record, k, v)
        return True

    def xǁ_ContextFilterǁfilter__mutmut_1(self, record: logging.LogRecord) -> bool:
        """Add trace fields from context to the log record."""
        for k, v in self._cv.get().items():
            setattr(None, k, v)
        return True

    def xǁ_ContextFilterǁfilter__mutmut_2(self, record: logging.LogRecord) -> bool:
        """Add trace fields from context to the log record."""
        for k, v in self._cv.get().items():
            setattr(record, None, v)
        return True

    def xǁ_ContextFilterǁfilter__mutmut_3(self, record: logging.LogRecord) -> bool:
        """Add trace fields from context to the log record."""
        for k, v in self._cv.get().items():
            setattr(record, k, None)
        return True

    def xǁ_ContextFilterǁfilter__mutmut_4(self, record: logging.LogRecord) -> bool:
        """Add trace fields from context to the log record."""
        for k, v in self._cv.get().items():
            setattr(k, v)
        return True

    def xǁ_ContextFilterǁfilter__mutmut_5(self, record: logging.LogRecord) -> bool:
        """Add trace fields from context to the log record."""
        for k, v in self._cv.get().items():
            setattr(record, v)
        return True

    def xǁ_ContextFilterǁfilter__mutmut_6(self, record: logging.LogRecord) -> bool:
        """Add trace fields from context to the log record."""
        for k, v in self._cv.get().items():
            setattr(record, k, )
        return True

    def xǁ_ContextFilterǁfilter__mutmut_7(self, record: logging.LogRecord) -> bool:
        """Add trace fields from context to the log record."""
        for k, v in self._cv.get().items():
            setattr(record, k, v)
        return False

mutants_xǁ_ContextFilterǁ__init____mutmut['_mutmut_orig'] = _ContextFilter.xǁ_ContextFilterǁ__init____mutmut_orig # type: ignore # mutmut generated
mutants_xǁ_ContextFilterǁ__init____mutmut['xǁ_ContextFilterǁ__init____mutmut_1'] = _ContextFilter.xǁ_ContextFilterǁ__init____mutmut_1 # type: ignore # mutmut generated
mutants_xǁ_ContextFilterǁ__init____mutmut['xǁ_ContextFilterǁ__init____mutmut_2'] = _ContextFilter.xǁ_ContextFilterǁ__init____mutmut_2 # type: ignore # mutmut generated
mutants_xǁ_ContextFilterǁ__init____mutmut['xǁ_ContextFilterǁ__init____mutmut_3'] = _ContextFilter.xǁ_ContextFilterǁ__init____mutmut_3 # type: ignore # mutmut generated
mutants_xǁ_ContextFilterǁ__init____mutmut['xǁ_ContextFilterǁ__init____mutmut_4'] = _ContextFilter.xǁ_ContextFilterǁ__init____mutmut_4 # type: ignore # mutmut generated
mutants_xǁ_ContextFilterǁ__init____mutmut['xǁ_ContextFilterǁ__init____mutmut_5'] = _ContextFilter.xǁ_ContextFilterǁ__init____mutmut_5 # type: ignore # mutmut generated
mutants_xǁ_ContextFilterǁ__init____mutmut['xǁ_ContextFilterǁ__init____mutmut_6'] = _ContextFilter.xǁ_ContextFilterǁ__init____mutmut_6 # type: ignore # mutmut generated
mutants_xǁ_ContextFilterǁ__init____mutmut['xǁ_ContextFilterǁ__init____mutmut_7'] = _ContextFilter.xǁ_ContextFilterǁ__init____mutmut_7 # type: ignore # mutmut generated

mutants_xǁ_ContextFilterǁset__mutmut['_mutmut_orig'] = _ContextFilter.xǁ_ContextFilterǁset__mutmut_orig # type: ignore # mutmut generated
mutants_xǁ_ContextFilterǁset__mutmut['xǁ_ContextFilterǁset__mutmut_1'] = _ContextFilter.xǁ_ContextFilterǁset__mutmut_1 # type: ignore # mutmut generated
mutants_xǁ_ContextFilterǁset__mutmut['xǁ_ContextFilterǁset__mutmut_2'] = _ContextFilter.xǁ_ContextFilterǁset__mutmut_2 # type: ignore # mutmut generated

mutants_xǁ_ContextFilterǁclear__mutmut['_mutmut_orig'] = _ContextFilter.xǁ_ContextFilterǁclear__mutmut_orig # type: ignore # mutmut generated
mutants_xǁ_ContextFilterǁclear__mutmut['xǁ_ContextFilterǁclear__mutmut_1'] = _ContextFilter.xǁ_ContextFilterǁclear__mutmut_1 # type: ignore # mutmut generated

mutants_xǁ_ContextFilterǁfilter__mutmut['_mutmut_orig'] = _ContextFilter.xǁ_ContextFilterǁfilter__mutmut_orig # type: ignore # mutmut generated
mutants_xǁ_ContextFilterǁfilter__mutmut['xǁ_ContextFilterǁfilter__mutmut_1'] = _ContextFilter.xǁ_ContextFilterǁfilter__mutmut_1 # type: ignore # mutmut generated
mutants_xǁ_ContextFilterǁfilter__mutmut['xǁ_ContextFilterǁfilter__mutmut_2'] = _ContextFilter.xǁ_ContextFilterǁfilter__mutmut_2 # type: ignore # mutmut generated
mutants_xǁ_ContextFilterǁfilter__mutmut['xǁ_ContextFilterǁfilter__mutmut_3'] = _ContextFilter.xǁ_ContextFilterǁfilter__mutmut_3 # type: ignore # mutmut generated
mutants_xǁ_ContextFilterǁfilter__mutmut['xǁ_ContextFilterǁfilter__mutmut_4'] = _ContextFilter.xǁ_ContextFilterǁfilter__mutmut_4 # type: ignore # mutmut generated
mutants_xǁ_ContextFilterǁfilter__mutmut['xǁ_ContextFilterǁfilter__mutmut_5'] = _ContextFilter.xǁ_ContextFilterǁfilter__mutmut_5 # type: ignore # mutmut generated
mutants_xǁ_ContextFilterǁfilter__mutmut['xǁ_ContextFilterǁfilter__mutmut_6'] = _ContextFilter.xǁ_ContextFilterǁfilter__mutmut_6 # type: ignore # mutmut generated
mutants_xǁ_ContextFilterǁfilter__mutmut['xǁ_ContextFilterǁfilter__mutmut_7'] = _ContextFilter.xǁ_ContextFilterǁfilter__mutmut_7 # type: ignore # mutmut generated
mutants_xǁ_JsonFormatterǁformat__mutmut: MutantDict = {}  # type: ignore


class _JsonFormatter(logging.Formatter):
    """Format a LogRecord as a single JSON line for structured log output."""

    _CONTEXT_KEYS = ("turn_id", "session_id", "rag_query_id", "workflow_id", "task_id")

    @_mutmut_mutated(mutants_xǁ_JsonFormatterǁformat__mutmut)
    def format(self, record: logging.LogRecord) -> str:
        """Format the log record as a JSON string with trace fields included."""
        entry: dict[str, Any] = {  # noqa: S603 — log entry keys vary by formatter
            "ts": self.formatTime(record, "%Y-%m-%dT%H:%M:%S"),
            "level": record.levelname,
            "func": record.funcName,
            "msg": record.getMessage(),
        }
        for key in self._CONTEXT_KEYS:
            val = getattr(record, key, None)
            if val is not None:
                entry[key] = val
        if record.exc_info:
            entry["exc"] = self.formatException(record.exc_info)
        formatted: str = _json_dumps(entry)
        return formatted

    def xǁ_JsonFormatterǁformat__mutmut_orig(self, record: logging.LogRecord) -> str:
        """Format the log record as a JSON string with trace fields included."""
        entry: dict[str, Any] = {  # noqa: S603 — log entry keys vary by formatter
            "ts": self.formatTime(record, "%Y-%m-%dT%H:%M:%S"),
            "level": record.levelname,
            "func": record.funcName,
            "msg": record.getMessage(),
        }
        for key in self._CONTEXT_KEYS:
            val = getattr(record, key, None)
            if val is not None:
                entry[key] = val
        if record.exc_info:
            entry["exc"] = self.formatException(record.exc_info)
        formatted: str = _json_dumps(entry)
        return formatted

    def xǁ_JsonFormatterǁformat__mutmut_1(self, record: logging.LogRecord) -> str:
        """Format the log record as a JSON string with trace fields included."""
        entry: dict[str, Any] = None
        for key in self._CONTEXT_KEYS:
            val = getattr(record, key, None)
            if val is not None:
                entry[key] = val
        if record.exc_info:
            entry["exc"] = self.formatException(record.exc_info)
        formatted: str = _json_dumps(entry)
        return formatted

    def xǁ_JsonFormatterǁformat__mutmut_2(self, record: logging.LogRecord) -> str:
        """Format the log record as a JSON string with trace fields included."""
        entry: dict[str, Any] = {  # noqa: S603 — log entry keys vary by formatter
            "XXtsXX": self.formatTime(record, "%Y-%m-%dT%H:%M:%S"),
            "level": record.levelname,
            "func": record.funcName,
            "msg": record.getMessage(),
        }
        for key in self._CONTEXT_KEYS:
            val = getattr(record, key, None)
            if val is not None:
                entry[key] = val
        if record.exc_info:
            entry["exc"] = self.formatException(record.exc_info)
        formatted: str = _json_dumps(entry)
        return formatted

    def xǁ_JsonFormatterǁformat__mutmut_3(self, record: logging.LogRecord) -> str:
        """Format the log record as a JSON string with trace fields included."""
        entry: dict[str, Any] = {  # noqa: S603 — log entry keys vary by formatter
            "TS": self.formatTime(record, "%Y-%m-%dT%H:%M:%S"),
            "level": record.levelname,
            "func": record.funcName,
            "msg": record.getMessage(),
        }
        for key in self._CONTEXT_KEYS:
            val = getattr(record, key, None)
            if val is not None:
                entry[key] = val
        if record.exc_info:
            entry["exc"] = self.formatException(record.exc_info)
        formatted: str = _json_dumps(entry)
        return formatted

    def xǁ_JsonFormatterǁformat__mutmut_4(self, record: logging.LogRecord) -> str:
        """Format the log record as a JSON string with trace fields included."""
        entry: dict[str, Any] = {  # noqa: S603 — log entry keys vary by formatter
            "ts": self.formatTime(None, "%Y-%m-%dT%H:%M:%S"),
            "level": record.levelname,
            "func": record.funcName,
            "msg": record.getMessage(),
        }
        for key in self._CONTEXT_KEYS:
            val = getattr(record, key, None)
            if val is not None:
                entry[key] = val
        if record.exc_info:
            entry["exc"] = self.formatException(record.exc_info)
        formatted: str = _json_dumps(entry)
        return formatted

    def xǁ_JsonFormatterǁformat__mutmut_5(self, record: logging.LogRecord) -> str:
        """Format the log record as a JSON string with trace fields included."""
        entry: dict[str, Any] = {  # noqa: S603 — log entry keys vary by formatter
            "ts": self.formatTime(record, None),
            "level": record.levelname,
            "func": record.funcName,
            "msg": record.getMessage(),
        }
        for key in self._CONTEXT_KEYS:
            val = getattr(record, key, None)
            if val is not None:
                entry[key] = val
        if record.exc_info:
            entry["exc"] = self.formatException(record.exc_info)
        formatted: str = _json_dumps(entry)
        return formatted

    def xǁ_JsonFormatterǁformat__mutmut_6(self, record: logging.LogRecord) -> str:
        """Format the log record as a JSON string with trace fields included."""
        entry: dict[str, Any] = {  # noqa: S603 — log entry keys vary by formatter
            "ts": self.formatTime("%Y-%m-%dT%H:%M:%S"),
            "level": record.levelname,
            "func": record.funcName,
            "msg": record.getMessage(),
        }
        for key in self._CONTEXT_KEYS:
            val = getattr(record, key, None)
            if val is not None:
                entry[key] = val
        if record.exc_info:
            entry["exc"] = self.formatException(record.exc_info)
        formatted: str = _json_dumps(entry)
        return formatted

    def xǁ_JsonFormatterǁformat__mutmut_7(self, record: logging.LogRecord) -> str:
        """Format the log record as a JSON string with trace fields included."""
        entry: dict[str, Any] = {  # noqa: S603 — log entry keys vary by formatter
            "ts": self.formatTime(record, ),
            "level": record.levelname,
            "func": record.funcName,
            "msg": record.getMessage(),
        }
        for key in self._CONTEXT_KEYS:
            val = getattr(record, key, None)
            if val is not None:
                entry[key] = val
        if record.exc_info:
            entry["exc"] = self.formatException(record.exc_info)
        formatted: str = _json_dumps(entry)
        return formatted

    def xǁ_JsonFormatterǁformat__mutmut_8(self, record: logging.LogRecord) -> str:
        """Format the log record as a JSON string with trace fields included."""
        entry: dict[str, Any] = {  # noqa: S603 — log entry keys vary by formatter
            "ts": self.formatTime(record, "XX%Y-%m-%dT%H:%M:%SXX"),
            "level": record.levelname,
            "func": record.funcName,
            "msg": record.getMessage(),
        }
        for key in self._CONTEXT_KEYS:
            val = getattr(record, key, None)
            if val is not None:
                entry[key] = val
        if record.exc_info:
            entry["exc"] = self.formatException(record.exc_info)
        formatted: str = _json_dumps(entry)
        return formatted

    def xǁ_JsonFormatterǁformat__mutmut_9(self, record: logging.LogRecord) -> str:
        """Format the log record as a JSON string with trace fields included."""
        entry: dict[str, Any] = {  # noqa: S603 — log entry keys vary by formatter
            "ts": self.formatTime(record, "%y-%m-%dt%h:%m:%s"),
            "level": record.levelname,
            "func": record.funcName,
            "msg": record.getMessage(),
        }
        for key in self._CONTEXT_KEYS:
            val = getattr(record, key, None)
            if val is not None:
                entry[key] = val
        if record.exc_info:
            entry["exc"] = self.formatException(record.exc_info)
        formatted: str = _json_dumps(entry)
        return formatted

    def xǁ_JsonFormatterǁformat__mutmut_10(self, record: logging.LogRecord) -> str:
        """Format the log record as a JSON string with trace fields included."""
        entry: dict[str, Any] = {  # noqa: S603 — log entry keys vary by formatter
            "ts": self.formatTime(record, "%Y-%M-%DT%H:%M:%S"),
            "level": record.levelname,
            "func": record.funcName,
            "msg": record.getMessage(),
        }
        for key in self._CONTEXT_KEYS:
            val = getattr(record, key, None)
            if val is not None:
                entry[key] = val
        if record.exc_info:
            entry["exc"] = self.formatException(record.exc_info)
        formatted: str = _json_dumps(entry)
        return formatted

    def xǁ_JsonFormatterǁformat__mutmut_11(self, record: logging.LogRecord) -> str:
        """Format the log record as a JSON string with trace fields included."""
        entry: dict[str, Any] = {  # noqa: S603 — log entry keys vary by formatter
            "ts": self.formatTime(record, "%Y-%m-%dT%H:%M:%S"),
            "XXlevelXX": record.levelname,
            "func": record.funcName,
            "msg": record.getMessage(),
        }
        for key in self._CONTEXT_KEYS:
            val = getattr(record, key, None)
            if val is not None:
                entry[key] = val
        if record.exc_info:
            entry["exc"] = self.formatException(record.exc_info)
        formatted: str = _json_dumps(entry)
        return formatted

    def xǁ_JsonFormatterǁformat__mutmut_12(self, record: logging.LogRecord) -> str:
        """Format the log record as a JSON string with trace fields included."""
        entry: dict[str, Any] = {  # noqa: S603 — log entry keys vary by formatter
            "ts": self.formatTime(record, "%Y-%m-%dT%H:%M:%S"),
            "LEVEL": record.levelname,
            "func": record.funcName,
            "msg": record.getMessage(),
        }
        for key in self._CONTEXT_KEYS:
            val = getattr(record, key, None)
            if val is not None:
                entry[key] = val
        if record.exc_info:
            entry["exc"] = self.formatException(record.exc_info)
        formatted: str = _json_dumps(entry)
        return formatted

    def xǁ_JsonFormatterǁformat__mutmut_13(self, record: logging.LogRecord) -> str:
        """Format the log record as a JSON string with trace fields included."""
        entry: dict[str, Any] = {  # noqa: S603 — log entry keys vary by formatter
            "ts": self.formatTime(record, "%Y-%m-%dT%H:%M:%S"),
            "level": record.levelname,
            "XXfuncXX": record.funcName,
            "msg": record.getMessage(),
        }
        for key in self._CONTEXT_KEYS:
            val = getattr(record, key, None)
            if val is not None:
                entry[key] = val
        if record.exc_info:
            entry["exc"] = self.formatException(record.exc_info)
        formatted: str = _json_dumps(entry)
        return formatted

    def xǁ_JsonFormatterǁformat__mutmut_14(self, record: logging.LogRecord) -> str:
        """Format the log record as a JSON string with trace fields included."""
        entry: dict[str, Any] = {  # noqa: S603 — log entry keys vary by formatter
            "ts": self.formatTime(record, "%Y-%m-%dT%H:%M:%S"),
            "level": record.levelname,
            "FUNC": record.funcName,
            "msg": record.getMessage(),
        }
        for key in self._CONTEXT_KEYS:
            val = getattr(record, key, None)
            if val is not None:
                entry[key] = val
        if record.exc_info:
            entry["exc"] = self.formatException(record.exc_info)
        formatted: str = _json_dumps(entry)
        return formatted

    def xǁ_JsonFormatterǁformat__mutmut_15(self, record: logging.LogRecord) -> str:
        """Format the log record as a JSON string with trace fields included."""
        entry: dict[str, Any] = {  # noqa: S603 — log entry keys vary by formatter
            "ts": self.formatTime(record, "%Y-%m-%dT%H:%M:%S"),
            "level": record.levelname,
            "func": record.funcName,
            "XXmsgXX": record.getMessage(),
        }
        for key in self._CONTEXT_KEYS:
            val = getattr(record, key, None)
            if val is not None:
                entry[key] = val
        if record.exc_info:
            entry["exc"] = self.formatException(record.exc_info)
        formatted: str = _json_dumps(entry)
        return formatted

    def xǁ_JsonFormatterǁformat__mutmut_16(self, record: logging.LogRecord) -> str:
        """Format the log record as a JSON string with trace fields included."""
        entry: dict[str, Any] = {  # noqa: S603 — log entry keys vary by formatter
            "ts": self.formatTime(record, "%Y-%m-%dT%H:%M:%S"),
            "level": record.levelname,
            "func": record.funcName,
            "MSG": record.getMessage(),
        }
        for key in self._CONTEXT_KEYS:
            val = getattr(record, key, None)
            if val is not None:
                entry[key] = val
        if record.exc_info:
            entry["exc"] = self.formatException(record.exc_info)
        formatted: str = _json_dumps(entry)
        return formatted

    def xǁ_JsonFormatterǁformat__mutmut_17(self, record: logging.LogRecord) -> str:
        """Format the log record as a JSON string with trace fields included."""
        entry: dict[str, Any] = {  # noqa: S603 — log entry keys vary by formatter
            "ts": self.formatTime(record, "%Y-%m-%dT%H:%M:%S"),
            "level": record.levelname,
            "func": record.funcName,
            "msg": record.getMessage(),
        }
        for key in self._CONTEXT_KEYS:
            val = None
            if val is not None:
                entry[key] = val
        if record.exc_info:
            entry["exc"] = self.formatException(record.exc_info)
        formatted: str = _json_dumps(entry)
        return formatted

    def xǁ_JsonFormatterǁformat__mutmut_18(self, record: logging.LogRecord) -> str:
        """Format the log record as a JSON string with trace fields included."""
        entry: dict[str, Any] = {  # noqa: S603 — log entry keys vary by formatter
            "ts": self.formatTime(record, "%Y-%m-%dT%H:%M:%S"),
            "level": record.levelname,
            "func": record.funcName,
            "msg": record.getMessage(),
        }
        for key in self._CONTEXT_KEYS:
            val = getattr(None, key, None)
            if val is not None:
                entry[key] = val
        if record.exc_info:
            entry["exc"] = self.formatException(record.exc_info)
        formatted: str = _json_dumps(entry)
        return formatted

    def xǁ_JsonFormatterǁformat__mutmut_19(self, record: logging.LogRecord) -> str:
        """Format the log record as a JSON string with trace fields included."""
        entry: dict[str, Any] = {  # noqa: S603 — log entry keys vary by formatter
            "ts": self.formatTime(record, "%Y-%m-%dT%H:%M:%S"),
            "level": record.levelname,
            "func": record.funcName,
            "msg": record.getMessage(),
        }
        for key in self._CONTEXT_KEYS:
            val = getattr(record, None, None)
            if val is not None:
                entry[key] = val
        if record.exc_info:
            entry["exc"] = self.formatException(record.exc_info)
        formatted: str = _json_dumps(entry)
        return formatted

    def xǁ_JsonFormatterǁformat__mutmut_20(self, record: logging.LogRecord) -> str:
        """Format the log record as a JSON string with trace fields included."""
        entry: dict[str, Any] = {  # noqa: S603 — log entry keys vary by formatter
            "ts": self.formatTime(record, "%Y-%m-%dT%H:%M:%S"),
            "level": record.levelname,
            "func": record.funcName,
            "msg": record.getMessage(),
        }
        for key in self._CONTEXT_KEYS:
            val = getattr(key, None)
            if val is not None:
                entry[key] = val
        if record.exc_info:
            entry["exc"] = self.formatException(record.exc_info)
        formatted: str = _json_dumps(entry)
        return formatted

    def xǁ_JsonFormatterǁformat__mutmut_21(self, record: logging.LogRecord) -> str:
        """Format the log record as a JSON string with trace fields included."""
        entry: dict[str, Any] = {  # noqa: S603 — log entry keys vary by formatter
            "ts": self.formatTime(record, "%Y-%m-%dT%H:%M:%S"),
            "level": record.levelname,
            "func": record.funcName,
            "msg": record.getMessage(),
        }
        for key in self._CONTEXT_KEYS:
            val = getattr(record, None)
            if val is not None:
                entry[key] = val
        if record.exc_info:
            entry["exc"] = self.formatException(record.exc_info)
        formatted: str = _json_dumps(entry)
        return formatted

    def xǁ_JsonFormatterǁformat__mutmut_22(self, record: logging.LogRecord) -> str:
        """Format the log record as a JSON string with trace fields included."""
        entry: dict[str, Any] = {  # noqa: S603 — log entry keys vary by formatter
            "ts": self.formatTime(record, "%Y-%m-%dT%H:%M:%S"),
            "level": record.levelname,
            "func": record.funcName,
            "msg": record.getMessage(),
        }
        for key in self._CONTEXT_KEYS:
            val = getattr(record, key, )
            if val is not None:
                entry[key] = val
        if record.exc_info:
            entry["exc"] = self.formatException(record.exc_info)
        formatted: str = _json_dumps(entry)
        return formatted

    def xǁ_JsonFormatterǁformat__mutmut_23(self, record: logging.LogRecord) -> str:
        """Format the log record as a JSON string with trace fields included."""
        entry: dict[str, Any] = {  # noqa: S603 — log entry keys vary by formatter
            "ts": self.formatTime(record, "%Y-%m-%dT%H:%M:%S"),
            "level": record.levelname,
            "func": record.funcName,
            "msg": record.getMessage(),
        }
        for key in self._CONTEXT_KEYS:
            val = getattr(record, key, None)
            if val is None:
                entry[key] = val
        if record.exc_info:
            entry["exc"] = self.formatException(record.exc_info)
        formatted: str = _json_dumps(entry)
        return formatted

    def xǁ_JsonFormatterǁformat__mutmut_24(self, record: logging.LogRecord) -> str:
        """Format the log record as a JSON string with trace fields included."""
        entry: dict[str, Any] = {  # noqa: S603 — log entry keys vary by formatter
            "ts": self.formatTime(record, "%Y-%m-%dT%H:%M:%S"),
            "level": record.levelname,
            "func": record.funcName,
            "msg": record.getMessage(),
        }
        for key in self._CONTEXT_KEYS:
            val = getattr(record, key, None)
            if val is not None:
                entry[key] = None
        if record.exc_info:
            entry["exc"] = self.formatException(record.exc_info)
        formatted: str = _json_dumps(entry)
        return formatted

    def xǁ_JsonFormatterǁformat__mutmut_25(self, record: logging.LogRecord) -> str:
        """Format the log record as a JSON string with trace fields included."""
        entry: dict[str, Any] = {  # noqa: S603 — log entry keys vary by formatter
            "ts": self.formatTime(record, "%Y-%m-%dT%H:%M:%S"),
            "level": record.levelname,
            "func": record.funcName,
            "msg": record.getMessage(),
        }
        for key in self._CONTEXT_KEYS:
            val = getattr(record, key, None)
            if val is not None:
                entry[key] = val
        if record.exc_info:
            entry["exc"] = None
        formatted: str = _json_dumps(entry)
        return formatted

    def xǁ_JsonFormatterǁformat__mutmut_26(self, record: logging.LogRecord) -> str:
        """Format the log record as a JSON string with trace fields included."""
        entry: dict[str, Any] = {  # noqa: S603 — log entry keys vary by formatter
            "ts": self.formatTime(record, "%Y-%m-%dT%H:%M:%S"),
            "level": record.levelname,
            "func": record.funcName,
            "msg": record.getMessage(),
        }
        for key in self._CONTEXT_KEYS:
            val = getattr(record, key, None)
            if val is not None:
                entry[key] = val
        if record.exc_info:
            entry["XXexcXX"] = self.formatException(record.exc_info)
        formatted: str = _json_dumps(entry)
        return formatted

    def xǁ_JsonFormatterǁformat__mutmut_27(self, record: logging.LogRecord) -> str:
        """Format the log record as a JSON string with trace fields included."""
        entry: dict[str, Any] = {  # noqa: S603 — log entry keys vary by formatter
            "ts": self.formatTime(record, "%Y-%m-%dT%H:%M:%S"),
            "level": record.levelname,
            "func": record.funcName,
            "msg": record.getMessage(),
        }
        for key in self._CONTEXT_KEYS:
            val = getattr(record, key, None)
            if val is not None:
                entry[key] = val
        if record.exc_info:
            entry["EXC"] = self.formatException(record.exc_info)
        formatted: str = _json_dumps(entry)
        return formatted

    def xǁ_JsonFormatterǁformat__mutmut_28(self, record: logging.LogRecord) -> str:
        """Format the log record as a JSON string with trace fields included."""
        entry: dict[str, Any] = {  # noqa: S603 — log entry keys vary by formatter
            "ts": self.formatTime(record, "%Y-%m-%dT%H:%M:%S"),
            "level": record.levelname,
            "func": record.funcName,
            "msg": record.getMessage(),
        }
        for key in self._CONTEXT_KEYS:
            val = getattr(record, key, None)
            if val is not None:
                entry[key] = val
        if record.exc_info:
            entry["exc"] = self.formatException(None)
        formatted: str = _json_dumps(entry)
        return formatted

    def xǁ_JsonFormatterǁformat__mutmut_29(self, record: logging.LogRecord) -> str:
        """Format the log record as a JSON string with trace fields included."""
        entry: dict[str, Any] = {  # noqa: S603 — log entry keys vary by formatter
            "ts": self.formatTime(record, "%Y-%m-%dT%H:%M:%S"),
            "level": record.levelname,
            "func": record.funcName,
            "msg": record.getMessage(),
        }
        for key in self._CONTEXT_KEYS:
            val = getattr(record, key, None)
            if val is not None:
                entry[key] = val
        if record.exc_info:
            entry["exc"] = self.formatException(record.exc_info)
        formatted: str = None
        return formatted

    def xǁ_JsonFormatterǁformat__mutmut_30(self, record: logging.LogRecord) -> str:
        """Format the log record as a JSON string with trace fields included."""
        entry: dict[str, Any] = {  # noqa: S603 — log entry keys vary by formatter
            "ts": self.formatTime(record, "%Y-%m-%dT%H:%M:%S"),
            "level": record.levelname,
            "func": record.funcName,
            "msg": record.getMessage(),
        }
        for key in self._CONTEXT_KEYS:
            val = getattr(record, key, None)
            if val is not None:
                entry[key] = val
        if record.exc_info:
            entry["exc"] = self.formatException(record.exc_info)
        formatted: str = _json_dumps(None)
        return formatted

mutants_xǁ_JsonFormatterǁformat__mutmut['_mutmut_orig'] = _JsonFormatter.xǁ_JsonFormatterǁformat__mutmut_orig # type: ignore # mutmut generated
mutants_xǁ_JsonFormatterǁformat__mutmut['xǁ_JsonFormatterǁformat__mutmut_1'] = _JsonFormatter.xǁ_JsonFormatterǁformat__mutmut_1 # type: ignore # mutmut generated
mutants_xǁ_JsonFormatterǁformat__mutmut['xǁ_JsonFormatterǁformat__mutmut_2'] = _JsonFormatter.xǁ_JsonFormatterǁformat__mutmut_2 # type: ignore # mutmut generated
mutants_xǁ_JsonFormatterǁformat__mutmut['xǁ_JsonFormatterǁformat__mutmut_3'] = _JsonFormatter.xǁ_JsonFormatterǁformat__mutmut_3 # type: ignore # mutmut generated
mutants_xǁ_JsonFormatterǁformat__mutmut['xǁ_JsonFormatterǁformat__mutmut_4'] = _JsonFormatter.xǁ_JsonFormatterǁformat__mutmut_4 # type: ignore # mutmut generated
mutants_xǁ_JsonFormatterǁformat__mutmut['xǁ_JsonFormatterǁformat__mutmut_5'] = _JsonFormatter.xǁ_JsonFormatterǁformat__mutmut_5 # type: ignore # mutmut generated
mutants_xǁ_JsonFormatterǁformat__mutmut['xǁ_JsonFormatterǁformat__mutmut_6'] = _JsonFormatter.xǁ_JsonFormatterǁformat__mutmut_6 # type: ignore # mutmut generated
mutants_xǁ_JsonFormatterǁformat__mutmut['xǁ_JsonFormatterǁformat__mutmut_7'] = _JsonFormatter.xǁ_JsonFormatterǁformat__mutmut_7 # type: ignore # mutmut generated
mutants_xǁ_JsonFormatterǁformat__mutmut['xǁ_JsonFormatterǁformat__mutmut_8'] = _JsonFormatter.xǁ_JsonFormatterǁformat__mutmut_8 # type: ignore # mutmut generated
mutants_xǁ_JsonFormatterǁformat__mutmut['xǁ_JsonFormatterǁformat__mutmut_9'] = _JsonFormatter.xǁ_JsonFormatterǁformat__mutmut_9 # type: ignore # mutmut generated
mutants_xǁ_JsonFormatterǁformat__mutmut['xǁ_JsonFormatterǁformat__mutmut_10'] = _JsonFormatter.xǁ_JsonFormatterǁformat__mutmut_10 # type: ignore # mutmut generated
mutants_xǁ_JsonFormatterǁformat__mutmut['xǁ_JsonFormatterǁformat__mutmut_11'] = _JsonFormatter.xǁ_JsonFormatterǁformat__mutmut_11 # type: ignore # mutmut generated
mutants_xǁ_JsonFormatterǁformat__mutmut['xǁ_JsonFormatterǁformat__mutmut_12'] = _JsonFormatter.xǁ_JsonFormatterǁformat__mutmut_12 # type: ignore # mutmut generated
mutants_xǁ_JsonFormatterǁformat__mutmut['xǁ_JsonFormatterǁformat__mutmut_13'] = _JsonFormatter.xǁ_JsonFormatterǁformat__mutmut_13 # type: ignore # mutmut generated
mutants_xǁ_JsonFormatterǁformat__mutmut['xǁ_JsonFormatterǁformat__mutmut_14'] = _JsonFormatter.xǁ_JsonFormatterǁformat__mutmut_14 # type: ignore # mutmut generated
mutants_xǁ_JsonFormatterǁformat__mutmut['xǁ_JsonFormatterǁformat__mutmut_15'] = _JsonFormatter.xǁ_JsonFormatterǁformat__mutmut_15 # type: ignore # mutmut generated
mutants_xǁ_JsonFormatterǁformat__mutmut['xǁ_JsonFormatterǁformat__mutmut_16'] = _JsonFormatter.xǁ_JsonFormatterǁformat__mutmut_16 # type: ignore # mutmut generated
mutants_xǁ_JsonFormatterǁformat__mutmut['xǁ_JsonFormatterǁformat__mutmut_17'] = _JsonFormatter.xǁ_JsonFormatterǁformat__mutmut_17 # type: ignore # mutmut generated
mutants_xǁ_JsonFormatterǁformat__mutmut['xǁ_JsonFormatterǁformat__mutmut_18'] = _JsonFormatter.xǁ_JsonFormatterǁformat__mutmut_18 # type: ignore # mutmut generated
mutants_xǁ_JsonFormatterǁformat__mutmut['xǁ_JsonFormatterǁformat__mutmut_19'] = _JsonFormatter.xǁ_JsonFormatterǁformat__mutmut_19 # type: ignore # mutmut generated
mutants_xǁ_JsonFormatterǁformat__mutmut['xǁ_JsonFormatterǁformat__mutmut_20'] = _JsonFormatter.xǁ_JsonFormatterǁformat__mutmut_20 # type: ignore # mutmut generated
mutants_xǁ_JsonFormatterǁformat__mutmut['xǁ_JsonFormatterǁformat__mutmut_21'] = _JsonFormatter.xǁ_JsonFormatterǁformat__mutmut_21 # type: ignore # mutmut generated
mutants_xǁ_JsonFormatterǁformat__mutmut['xǁ_JsonFormatterǁformat__mutmut_22'] = _JsonFormatter.xǁ_JsonFormatterǁformat__mutmut_22 # type: ignore # mutmut generated
mutants_xǁ_JsonFormatterǁformat__mutmut['xǁ_JsonFormatterǁformat__mutmut_23'] = _JsonFormatter.xǁ_JsonFormatterǁformat__mutmut_23 # type: ignore # mutmut generated
mutants_xǁ_JsonFormatterǁformat__mutmut['xǁ_JsonFormatterǁformat__mutmut_24'] = _JsonFormatter.xǁ_JsonFormatterǁformat__mutmut_24 # type: ignore # mutmut generated
mutants_xǁ_JsonFormatterǁformat__mutmut['xǁ_JsonFormatterǁformat__mutmut_25'] = _JsonFormatter.xǁ_JsonFormatterǁformat__mutmut_25 # type: ignore # mutmut generated
mutants_xǁ_JsonFormatterǁformat__mutmut['xǁ_JsonFormatterǁformat__mutmut_26'] = _JsonFormatter.xǁ_JsonFormatterǁformat__mutmut_26 # type: ignore # mutmut generated
mutants_xǁ_JsonFormatterǁformat__mutmut['xǁ_JsonFormatterǁformat__mutmut_27'] = _JsonFormatter.xǁ_JsonFormatterǁformat__mutmut_27 # type: ignore # mutmut generated
mutants_xǁ_JsonFormatterǁformat__mutmut['xǁ_JsonFormatterǁformat__mutmut_28'] = _JsonFormatter.xǁ_JsonFormatterǁformat__mutmut_28 # type: ignore # mutmut generated
mutants_xǁ_JsonFormatterǁformat__mutmut['xǁ_JsonFormatterǁformat__mutmut_29'] = _JsonFormatter.xǁ_JsonFormatterǁformat__mutmut_29 # type: ignore # mutmut generated
mutants_xǁ_JsonFormatterǁformat__mutmut['xǁ_JsonFormatterǁformat__mutmut_30'] = _JsonFormatter.xǁ_JsonFormatterǁformat__mutmut_30 # type: ignore # mutmut generated
mutants_xǁLoggerǁ__init____mutmut: MutantDict = {}  # type: ignore
mutants_xǁLoggerǁ__getattr____mutmut: MutantDict = {}  # type: ignore
mutants_xǁLoggerǁ_configure_logger__mutmut: MutantDict = {}  # type: ignore


class Logger:
    """Configure a named logger with a dedicated FileHandler per entry script; propagate=False prevents duplicate output; structured_log=True switches to JSON-lines."""

    _FORMAT = "%(asctime)s %(levelname)s [%(funcName)s] %(message)s"

    @_mutmut_mutated(mutants_xǁLoggerǁ__init____mutmut)
    def __init__(
        self,
        name: str,
        log_file: str,
        *,
        structured_log: bool = False,
    ) -> None:
        """Initialize the logger with a name, log file path, and optional structured logging mode."""
        _require_str(name, "Logger name")
        _require_str(log_file, "log_file")
        self._logger = logging.getLogger(name)
        self._filter = _ContextFilter()
        self._configure_logger(log_file, structured_log)

    def xǁLoggerǁ__init____mutmut_orig(
        self,
        name: str,
        log_file: str,
        *,
        structured_log: bool = False,
    ) -> None:
        """Initialize the logger with a name, log file path, and optional structured logging mode."""
        _require_str(name, "Logger name")
        _require_str(log_file, "log_file")
        self._logger = logging.getLogger(name)
        self._filter = _ContextFilter()
        self._configure_logger(log_file, structured_log)

    def xǁLoggerǁ__init____mutmut_1(
        self,
        name: str,
        log_file: str,
        *,
        structured_log: bool = True,
    ) -> None:
        """Initialize the logger with a name, log file path, and optional structured logging mode."""
        _require_str(name, "Logger name")
        _require_str(log_file, "log_file")
        self._logger = logging.getLogger(name)
        self._filter = _ContextFilter()
        self._configure_logger(log_file, structured_log)

    def xǁLoggerǁ__init____mutmut_2(
        self,
        name: str,
        log_file: str,
        *,
        structured_log: bool = False,
    ) -> None:
        """Initialize the logger with a name, log file path, and optional structured logging mode."""
        _require_str(None, "Logger name")
        _require_str(log_file, "log_file")
        self._logger = logging.getLogger(name)
        self._filter = _ContextFilter()
        self._configure_logger(log_file, structured_log)

    def xǁLoggerǁ__init____mutmut_3(
        self,
        name: str,
        log_file: str,
        *,
        structured_log: bool = False,
    ) -> None:
        """Initialize the logger with a name, log file path, and optional structured logging mode."""
        _require_str(name, None)
        _require_str(log_file, "log_file")
        self._logger = logging.getLogger(name)
        self._filter = _ContextFilter()
        self._configure_logger(log_file, structured_log)

    def xǁLoggerǁ__init____mutmut_4(
        self,
        name: str,
        log_file: str,
        *,
        structured_log: bool = False,
    ) -> None:
        """Initialize the logger with a name, log file path, and optional structured logging mode."""
        _require_str("Logger name")
        _require_str(log_file, "log_file")
        self._logger = logging.getLogger(name)
        self._filter = _ContextFilter()
        self._configure_logger(log_file, structured_log)

    def xǁLoggerǁ__init____mutmut_5(
        self,
        name: str,
        log_file: str,
        *,
        structured_log: bool = False,
    ) -> None:
        """Initialize the logger with a name, log file path, and optional structured logging mode."""
        _require_str(name, )
        _require_str(log_file, "log_file")
        self._logger = logging.getLogger(name)
        self._filter = _ContextFilter()
        self._configure_logger(log_file, structured_log)

    def xǁLoggerǁ__init____mutmut_6(
        self,
        name: str,
        log_file: str,
        *,
        structured_log: bool = False,
    ) -> None:
        """Initialize the logger with a name, log file path, and optional structured logging mode."""
        _require_str(name, "XXLogger nameXX")
        _require_str(log_file, "log_file")
        self._logger = logging.getLogger(name)
        self._filter = _ContextFilter()
        self._configure_logger(log_file, structured_log)

    def xǁLoggerǁ__init____mutmut_7(
        self,
        name: str,
        log_file: str,
        *,
        structured_log: bool = False,
    ) -> None:
        """Initialize the logger with a name, log file path, and optional structured logging mode."""
        _require_str(name, "logger name")
        _require_str(log_file, "log_file")
        self._logger = logging.getLogger(name)
        self._filter = _ContextFilter()
        self._configure_logger(log_file, structured_log)

    def xǁLoggerǁ__init____mutmut_8(
        self,
        name: str,
        log_file: str,
        *,
        structured_log: bool = False,
    ) -> None:
        """Initialize the logger with a name, log file path, and optional structured logging mode."""
        _require_str(name, "LOGGER NAME")
        _require_str(log_file, "log_file")
        self._logger = logging.getLogger(name)
        self._filter = _ContextFilter()
        self._configure_logger(log_file, structured_log)

    def xǁLoggerǁ__init____mutmut_9(
        self,
        name: str,
        log_file: str,
        *,
        structured_log: bool = False,
    ) -> None:
        """Initialize the logger with a name, log file path, and optional structured logging mode."""
        _require_str(name, "Logger name")
        _require_str(None, "log_file")
        self._logger = logging.getLogger(name)
        self._filter = _ContextFilter()
        self._configure_logger(log_file, structured_log)

    def xǁLoggerǁ__init____mutmut_10(
        self,
        name: str,
        log_file: str,
        *,
        structured_log: bool = False,
    ) -> None:
        """Initialize the logger with a name, log file path, and optional structured logging mode."""
        _require_str(name, "Logger name")
        _require_str(log_file, None)
        self._logger = logging.getLogger(name)
        self._filter = _ContextFilter()
        self._configure_logger(log_file, structured_log)

    def xǁLoggerǁ__init____mutmut_11(
        self,
        name: str,
        log_file: str,
        *,
        structured_log: bool = False,
    ) -> None:
        """Initialize the logger with a name, log file path, and optional structured logging mode."""
        _require_str(name, "Logger name")
        _require_str("log_file")
        self._logger = logging.getLogger(name)
        self._filter = _ContextFilter()
        self._configure_logger(log_file, structured_log)

    def xǁLoggerǁ__init____mutmut_12(
        self,
        name: str,
        log_file: str,
        *,
        structured_log: bool = False,
    ) -> None:
        """Initialize the logger with a name, log file path, and optional structured logging mode."""
        _require_str(name, "Logger name")
        _require_str(log_file, )
        self._logger = logging.getLogger(name)
        self._filter = _ContextFilter()
        self._configure_logger(log_file, structured_log)

    def xǁLoggerǁ__init____mutmut_13(
        self,
        name: str,
        log_file: str,
        *,
        structured_log: bool = False,
    ) -> None:
        """Initialize the logger with a name, log file path, and optional structured logging mode."""
        _require_str(name, "Logger name")
        _require_str(log_file, "XXlog_fileXX")
        self._logger = logging.getLogger(name)
        self._filter = _ContextFilter()
        self._configure_logger(log_file, structured_log)

    def xǁLoggerǁ__init____mutmut_14(
        self,
        name: str,
        log_file: str,
        *,
        structured_log: bool = False,
    ) -> None:
        """Initialize the logger with a name, log file path, and optional structured logging mode."""
        _require_str(name, "Logger name")
        _require_str(log_file, "LOG_FILE")
        self._logger = logging.getLogger(name)
        self._filter = _ContextFilter()
        self._configure_logger(log_file, structured_log)

    def xǁLoggerǁ__init____mutmut_15(
        self,
        name: str,
        log_file: str,
        *,
        structured_log: bool = False,
    ) -> None:
        """Initialize the logger with a name, log file path, and optional structured logging mode."""
        _require_str(name, "Logger name")
        _require_str(log_file, "log_file")
        self._logger = None
        self._filter = _ContextFilter()
        self._configure_logger(log_file, structured_log)

    def xǁLoggerǁ__init____mutmut_16(
        self,
        name: str,
        log_file: str,
        *,
        structured_log: bool = False,
    ) -> None:
        """Initialize the logger with a name, log file path, and optional structured logging mode."""
        _require_str(name, "Logger name")
        _require_str(log_file, "log_file")
        self._logger = logging.getLogger(None)
        self._filter = _ContextFilter()
        self._configure_logger(log_file, structured_log)

    def xǁLoggerǁ__init____mutmut_17(
        self,
        name: str,
        log_file: str,
        *,
        structured_log: bool = False,
    ) -> None:
        """Initialize the logger with a name, log file path, and optional structured logging mode."""
        _require_str(name, "Logger name")
        _require_str(log_file, "log_file")
        self._logger = logging.getLogger(name)
        self._filter = None
        self._configure_logger(log_file, structured_log)

    def xǁLoggerǁ__init____mutmut_18(
        self,
        name: str,
        log_file: str,
        *,
        structured_log: bool = False,
    ) -> None:
        """Initialize the logger with a name, log file path, and optional structured logging mode."""
        _require_str(name, "Logger name")
        _require_str(log_file, "log_file")
        self._logger = logging.getLogger(name)
        self._filter = _ContextFilter()
        self._configure_logger(None, structured_log)

    def xǁLoggerǁ__init____mutmut_19(
        self,
        name: str,
        log_file: str,
        *,
        structured_log: bool = False,
    ) -> None:
        """Initialize the logger with a name, log file path, and optional structured logging mode."""
        _require_str(name, "Logger name")
        _require_str(log_file, "log_file")
        self._logger = logging.getLogger(name)
        self._filter = _ContextFilter()
        self._configure_logger(log_file, None)

    def xǁLoggerǁ__init____mutmut_20(
        self,
        name: str,
        log_file: str,
        *,
        structured_log: bool = False,
    ) -> None:
        """Initialize the logger with a name, log file path, and optional structured logging mode."""
        _require_str(name, "Logger name")
        _require_str(log_file, "log_file")
        self._logger = logging.getLogger(name)
        self._filter = _ContextFilter()
        self._configure_logger(structured_log)

    def xǁLoggerǁ__init____mutmut_21(
        self,
        name: str,
        log_file: str,
        *,
        structured_log: bool = False,
    ) -> None:
        """Initialize the logger with a name, log file path, and optional structured logging mode."""
        _require_str(name, "Logger name")
        _require_str(log_file, "log_file")
        self._logger = logging.getLogger(name)
        self._filter = _ContextFilter()
        self._configure_logger(log_file, )

    def set_context(self, **fields: Any) -> None:
        """Inject trace fields (turn_id, session_id, rag_query_id) into log records."""
        self._filter.set(**fields)

    def clear_context(self) -> None:
        """Remove all injected trace fields from subsequent log records."""
        self._filter.clear()

    @_mutmut_mutated(mutants_xǁLoggerǁ__getattr____mutmut)
    def __getattr__(self, name: str) -> Any:
        """Delegate attribute access to the underlying stdlib logger."""
        return getattr(self._logger, name)

    def xǁLoggerǁ__getattr____mutmut_orig(self, name: str) -> Any:
        """Delegate attribute access to the underlying stdlib logger."""
        return getattr(self._logger, name)

    def xǁLoggerǁ__getattr____mutmut_1(self, name: str) -> Any:
        """Delegate attribute access to the underlying stdlib logger."""
        return getattr(None, name)

    def xǁLoggerǁ__getattr____mutmut_2(self, name: str) -> Any:
        """Delegate attribute access to the underlying stdlib logger."""
        return getattr(self._logger, None)

    def xǁLoggerǁ__getattr____mutmut_3(self, name: str) -> Any:
        """Delegate attribute access to the underlying stdlib logger."""
        return getattr(name)

    def xǁLoggerǁ__getattr____mutmut_4(self, name: str) -> Any:
        """Delegate attribute access to the underlying stdlib logger."""
        return getattr(self._logger, )

    @_mutmut_mutated(mutants_xǁLoggerǁ_configure_logger__mutmut)
    def _configure_logger(self, log_file: str, structured_log: bool) -> None:
        """Attach FileHandler + StreamHandler and context filter to the named logger."""
        self._logger.addFilter(self._filter)
        if self._logger.handlers:
            return
        formatter: logging.Formatter = (
            _JsonFormatter() if structured_log else logging.Formatter(self._FORMAT)
        )
        try:
            fh = logging.FileHandler(log_file)
            fh.setFormatter(formatter)
            self._logger.addHandler(fh)
        except OSError as exc:
            _fallback_logger.warning(
                "Cannot open log file %s: %s — falling back to stream handler only",
                log_file,
                exc,
            )
        sh = logging.StreamHandler(sys.stderr)
        sh.setFormatter(formatter)
        self._logger.addHandler(sh)
        self._logger.setLevel(logging.INFO)
        self._logger.propagate = False

    def xǁLoggerǁ_configure_logger__mutmut_orig(self, log_file: str, structured_log: bool) -> None:
        """Attach FileHandler + StreamHandler and context filter to the named logger."""
        self._logger.addFilter(self._filter)
        if self._logger.handlers:
            return
        formatter: logging.Formatter = (
            _JsonFormatter() if structured_log else logging.Formatter(self._FORMAT)
        )
        try:
            fh = logging.FileHandler(log_file)
            fh.setFormatter(formatter)
            self._logger.addHandler(fh)
        except OSError as exc:
            _fallback_logger.warning(
                "Cannot open log file %s: %s — falling back to stream handler only",
                log_file,
                exc,
            )
        sh = logging.StreamHandler(sys.stderr)
        sh.setFormatter(formatter)
        self._logger.addHandler(sh)
        self._logger.setLevel(logging.INFO)
        self._logger.propagate = False

    def xǁLoggerǁ_configure_logger__mutmut_1(self, log_file: str, structured_log: bool) -> None:
        """Attach FileHandler + StreamHandler and context filter to the named logger."""
        self._logger.addFilter(None)
        if self._logger.handlers:
            return
        formatter: logging.Formatter = (
            _JsonFormatter() if structured_log else logging.Formatter(self._FORMAT)
        )
        try:
            fh = logging.FileHandler(log_file)
            fh.setFormatter(formatter)
            self._logger.addHandler(fh)
        except OSError as exc:
            _fallback_logger.warning(
                "Cannot open log file %s: %s — falling back to stream handler only",
                log_file,
                exc,
            )
        sh = logging.StreamHandler(sys.stderr)
        sh.setFormatter(formatter)
        self._logger.addHandler(sh)
        self._logger.setLevel(logging.INFO)
        self._logger.propagate = False

    def xǁLoggerǁ_configure_logger__mutmut_2(self, log_file: str, structured_log: bool) -> None:
        """Attach FileHandler + StreamHandler and context filter to the named logger."""
        self._logger.addFilter(self._filter)
        if self._logger.handlers:
            return
        formatter: logging.Formatter = None
        try:
            fh = logging.FileHandler(log_file)
            fh.setFormatter(formatter)
            self._logger.addHandler(fh)
        except OSError as exc:
            _fallback_logger.warning(
                "Cannot open log file %s: %s — falling back to stream handler only",
                log_file,
                exc,
            )
        sh = logging.StreamHandler(sys.stderr)
        sh.setFormatter(formatter)
        self._logger.addHandler(sh)
        self._logger.setLevel(logging.INFO)
        self._logger.propagate = False

    def xǁLoggerǁ_configure_logger__mutmut_3(self, log_file: str, structured_log: bool) -> None:
        """Attach FileHandler + StreamHandler and context filter to the named logger."""
        self._logger.addFilter(self._filter)
        if self._logger.handlers:
            return
        formatter: logging.Formatter = (
            _JsonFormatter() if structured_log else logging.Formatter(None)
        )
        try:
            fh = logging.FileHandler(log_file)
            fh.setFormatter(formatter)
            self._logger.addHandler(fh)
        except OSError as exc:
            _fallback_logger.warning(
                "Cannot open log file %s: %s — falling back to stream handler only",
                log_file,
                exc,
            )
        sh = logging.StreamHandler(sys.stderr)
        sh.setFormatter(formatter)
        self._logger.addHandler(sh)
        self._logger.setLevel(logging.INFO)
        self._logger.propagate = False

    def xǁLoggerǁ_configure_logger__mutmut_4(self, log_file: str, structured_log: bool) -> None:
        """Attach FileHandler + StreamHandler and context filter to the named logger."""
        self._logger.addFilter(self._filter)
        if self._logger.handlers:
            return
        formatter: logging.Formatter = (
            _JsonFormatter() if structured_log else logging.Formatter(self._FORMAT)
        )
        try:
            fh = None
            fh.setFormatter(formatter)
            self._logger.addHandler(fh)
        except OSError as exc:
            _fallback_logger.warning(
                "Cannot open log file %s: %s — falling back to stream handler only",
                log_file,
                exc,
            )
        sh = logging.StreamHandler(sys.stderr)
        sh.setFormatter(formatter)
        self._logger.addHandler(sh)
        self._logger.setLevel(logging.INFO)
        self._logger.propagate = False

    def xǁLoggerǁ_configure_logger__mutmut_5(self, log_file: str, structured_log: bool) -> None:
        """Attach FileHandler + StreamHandler and context filter to the named logger."""
        self._logger.addFilter(self._filter)
        if self._logger.handlers:
            return
        formatter: logging.Formatter = (
            _JsonFormatter() if structured_log else logging.Formatter(self._FORMAT)
        )
        try:
            fh = logging.FileHandler(None)
            fh.setFormatter(formatter)
            self._logger.addHandler(fh)
        except OSError as exc:
            _fallback_logger.warning(
                "Cannot open log file %s: %s — falling back to stream handler only",
                log_file,
                exc,
            )
        sh = logging.StreamHandler(sys.stderr)
        sh.setFormatter(formatter)
        self._logger.addHandler(sh)
        self._logger.setLevel(logging.INFO)
        self._logger.propagate = False

    def xǁLoggerǁ_configure_logger__mutmut_6(self, log_file: str, structured_log: bool) -> None:
        """Attach FileHandler + StreamHandler and context filter to the named logger."""
        self._logger.addFilter(self._filter)
        if self._logger.handlers:
            return
        formatter: logging.Formatter = (
            _JsonFormatter() if structured_log else logging.Formatter(self._FORMAT)
        )
        try:
            fh = logging.FileHandler(log_file)
            fh.setFormatter(None)
            self._logger.addHandler(fh)
        except OSError as exc:
            _fallback_logger.warning(
                "Cannot open log file %s: %s — falling back to stream handler only",
                log_file,
                exc,
            )
        sh = logging.StreamHandler(sys.stderr)
        sh.setFormatter(formatter)
        self._logger.addHandler(sh)
        self._logger.setLevel(logging.INFO)
        self._logger.propagate = False

    def xǁLoggerǁ_configure_logger__mutmut_7(self, log_file: str, structured_log: bool) -> None:
        """Attach FileHandler + StreamHandler and context filter to the named logger."""
        self._logger.addFilter(self._filter)
        if self._logger.handlers:
            return
        formatter: logging.Formatter = (
            _JsonFormatter() if structured_log else logging.Formatter(self._FORMAT)
        )
        try:
            fh = logging.FileHandler(log_file)
            fh.setFormatter(formatter)
            self._logger.addHandler(None)
        except OSError as exc:
            _fallback_logger.warning(
                "Cannot open log file %s: %s — falling back to stream handler only",
                log_file,
                exc,
            )
        sh = logging.StreamHandler(sys.stderr)
        sh.setFormatter(formatter)
        self._logger.addHandler(sh)
        self._logger.setLevel(logging.INFO)
        self._logger.propagate = False

    def xǁLoggerǁ_configure_logger__mutmut_8(self, log_file: str, structured_log: bool) -> None:
        """Attach FileHandler + StreamHandler and context filter to the named logger."""
        self._logger.addFilter(self._filter)
        if self._logger.handlers:
            return
        formatter: logging.Formatter = (
            _JsonFormatter() if structured_log else logging.Formatter(self._FORMAT)
        )
        try:
            fh = logging.FileHandler(log_file)
            fh.setFormatter(formatter)
            self._logger.addHandler(fh)
        except OSError as exc:
            _fallback_logger.warning(
                None,
                log_file,
                exc,
            )
        sh = logging.StreamHandler(sys.stderr)
        sh.setFormatter(formatter)
        self._logger.addHandler(sh)
        self._logger.setLevel(logging.INFO)
        self._logger.propagate = False

    def xǁLoggerǁ_configure_logger__mutmut_9(self, log_file: str, structured_log: bool) -> None:
        """Attach FileHandler + StreamHandler and context filter to the named logger."""
        self._logger.addFilter(self._filter)
        if self._logger.handlers:
            return
        formatter: logging.Formatter = (
            _JsonFormatter() if structured_log else logging.Formatter(self._FORMAT)
        )
        try:
            fh = logging.FileHandler(log_file)
            fh.setFormatter(formatter)
            self._logger.addHandler(fh)
        except OSError as exc:
            _fallback_logger.warning(
                "Cannot open log file %s: %s — falling back to stream handler only",
                None,
                exc,
            )
        sh = logging.StreamHandler(sys.stderr)
        sh.setFormatter(formatter)
        self._logger.addHandler(sh)
        self._logger.setLevel(logging.INFO)
        self._logger.propagate = False

    def xǁLoggerǁ_configure_logger__mutmut_10(self, log_file: str, structured_log: bool) -> None:
        """Attach FileHandler + StreamHandler and context filter to the named logger."""
        self._logger.addFilter(self._filter)
        if self._logger.handlers:
            return
        formatter: logging.Formatter = (
            _JsonFormatter() if structured_log else logging.Formatter(self._FORMAT)
        )
        try:
            fh = logging.FileHandler(log_file)
            fh.setFormatter(formatter)
            self._logger.addHandler(fh)
        except OSError as exc:
            _fallback_logger.warning(
                "Cannot open log file %s: %s — falling back to stream handler only",
                log_file,
                None,
            )
        sh = logging.StreamHandler(sys.stderr)
        sh.setFormatter(formatter)
        self._logger.addHandler(sh)
        self._logger.setLevel(logging.INFO)
        self._logger.propagate = False

    def xǁLoggerǁ_configure_logger__mutmut_11(self, log_file: str, structured_log: bool) -> None:
        """Attach FileHandler + StreamHandler and context filter to the named logger."""
        self._logger.addFilter(self._filter)
        if self._logger.handlers:
            return
        formatter: logging.Formatter = (
            _JsonFormatter() if structured_log else logging.Formatter(self._FORMAT)
        )
        try:
            fh = logging.FileHandler(log_file)
            fh.setFormatter(formatter)
            self._logger.addHandler(fh)
        except OSError as exc:
            _fallback_logger.warning(
                log_file,
                exc,
            )
        sh = logging.StreamHandler(sys.stderr)
        sh.setFormatter(formatter)
        self._logger.addHandler(sh)
        self._logger.setLevel(logging.INFO)
        self._logger.propagate = False

    def xǁLoggerǁ_configure_logger__mutmut_12(self, log_file: str, structured_log: bool) -> None:
        """Attach FileHandler + StreamHandler and context filter to the named logger."""
        self._logger.addFilter(self._filter)
        if self._logger.handlers:
            return
        formatter: logging.Formatter = (
            _JsonFormatter() if structured_log else logging.Formatter(self._FORMAT)
        )
        try:
            fh = logging.FileHandler(log_file)
            fh.setFormatter(formatter)
            self._logger.addHandler(fh)
        except OSError as exc:
            _fallback_logger.warning(
                "Cannot open log file %s: %s — falling back to stream handler only",
                exc,
            )
        sh = logging.StreamHandler(sys.stderr)
        sh.setFormatter(formatter)
        self._logger.addHandler(sh)
        self._logger.setLevel(logging.INFO)
        self._logger.propagate = False

    def xǁLoggerǁ_configure_logger__mutmut_13(self, log_file: str, structured_log: bool) -> None:
        """Attach FileHandler + StreamHandler and context filter to the named logger."""
        self._logger.addFilter(self._filter)
        if self._logger.handlers:
            return
        formatter: logging.Formatter = (
            _JsonFormatter() if structured_log else logging.Formatter(self._FORMAT)
        )
        try:
            fh = logging.FileHandler(log_file)
            fh.setFormatter(formatter)
            self._logger.addHandler(fh)
        except OSError as exc:
            _fallback_logger.warning(
                "Cannot open log file %s: %s — falling back to stream handler only",
                log_file,
                )
        sh = logging.StreamHandler(sys.stderr)
        sh.setFormatter(formatter)
        self._logger.addHandler(sh)
        self._logger.setLevel(logging.INFO)
        self._logger.propagate = False

    def xǁLoggerǁ_configure_logger__mutmut_14(self, log_file: str, structured_log: bool) -> None:
        """Attach FileHandler + StreamHandler and context filter to the named logger."""
        self._logger.addFilter(self._filter)
        if self._logger.handlers:
            return
        formatter: logging.Formatter = (
            _JsonFormatter() if structured_log else logging.Formatter(self._FORMAT)
        )
        try:
            fh = logging.FileHandler(log_file)
            fh.setFormatter(formatter)
            self._logger.addHandler(fh)
        except OSError as exc:
            _fallback_logger.warning(
                "XXCannot open log file %s: %s — falling back to stream handler onlyXX",
                log_file,
                exc,
            )
        sh = logging.StreamHandler(sys.stderr)
        sh.setFormatter(formatter)
        self._logger.addHandler(sh)
        self._logger.setLevel(logging.INFO)
        self._logger.propagate = False

    def xǁLoggerǁ_configure_logger__mutmut_15(self, log_file: str, structured_log: bool) -> None:
        """Attach FileHandler + StreamHandler and context filter to the named logger."""
        self._logger.addFilter(self._filter)
        if self._logger.handlers:
            return
        formatter: logging.Formatter = (
            _JsonFormatter() if structured_log else logging.Formatter(self._FORMAT)
        )
        try:
            fh = logging.FileHandler(log_file)
            fh.setFormatter(formatter)
            self._logger.addHandler(fh)
        except OSError as exc:
            _fallback_logger.warning(
                "cannot open log file %s: %s — falling back to stream handler only",
                log_file,
                exc,
            )
        sh = logging.StreamHandler(sys.stderr)
        sh.setFormatter(formatter)
        self._logger.addHandler(sh)
        self._logger.setLevel(logging.INFO)
        self._logger.propagate = False

    def xǁLoggerǁ_configure_logger__mutmut_16(self, log_file: str, structured_log: bool) -> None:
        """Attach FileHandler + StreamHandler and context filter to the named logger."""
        self._logger.addFilter(self._filter)
        if self._logger.handlers:
            return
        formatter: logging.Formatter = (
            _JsonFormatter() if structured_log else logging.Formatter(self._FORMAT)
        )
        try:
            fh = logging.FileHandler(log_file)
            fh.setFormatter(formatter)
            self._logger.addHandler(fh)
        except OSError as exc:
            _fallback_logger.warning(
                "CANNOT OPEN LOG FILE %S: %S — FALLING BACK TO STREAM HANDLER ONLY",
                log_file,
                exc,
            )
        sh = logging.StreamHandler(sys.stderr)
        sh.setFormatter(formatter)
        self._logger.addHandler(sh)
        self._logger.setLevel(logging.INFO)
        self._logger.propagate = False

    def xǁLoggerǁ_configure_logger__mutmut_17(self, log_file: str, structured_log: bool) -> None:
        """Attach FileHandler + StreamHandler and context filter to the named logger."""
        self._logger.addFilter(self._filter)
        if self._logger.handlers:
            return
        formatter: logging.Formatter = (
            _JsonFormatter() if structured_log else logging.Formatter(self._FORMAT)
        )
        try:
            fh = logging.FileHandler(log_file)
            fh.setFormatter(formatter)
            self._logger.addHandler(fh)
        except OSError as exc:
            _fallback_logger.warning(
                "Cannot open log file %s: %s — falling back to stream handler only",
                log_file,
                exc,
            )
        sh = None
        sh.setFormatter(formatter)
        self._logger.addHandler(sh)
        self._logger.setLevel(logging.INFO)
        self._logger.propagate = False

    def xǁLoggerǁ_configure_logger__mutmut_18(self, log_file: str, structured_log: bool) -> None:
        """Attach FileHandler + StreamHandler and context filter to the named logger."""
        self._logger.addFilter(self._filter)
        if self._logger.handlers:
            return
        formatter: logging.Formatter = (
            _JsonFormatter() if structured_log else logging.Formatter(self._FORMAT)
        )
        try:
            fh = logging.FileHandler(log_file)
            fh.setFormatter(formatter)
            self._logger.addHandler(fh)
        except OSError as exc:
            _fallback_logger.warning(
                "Cannot open log file %s: %s — falling back to stream handler only",
                log_file,
                exc,
            )
        sh = logging.StreamHandler(None)
        sh.setFormatter(formatter)
        self._logger.addHandler(sh)
        self._logger.setLevel(logging.INFO)
        self._logger.propagate = False

    def xǁLoggerǁ_configure_logger__mutmut_19(self, log_file: str, structured_log: bool) -> None:
        """Attach FileHandler + StreamHandler and context filter to the named logger."""
        self._logger.addFilter(self._filter)
        if self._logger.handlers:
            return
        formatter: logging.Formatter = (
            _JsonFormatter() if structured_log else logging.Formatter(self._FORMAT)
        )
        try:
            fh = logging.FileHandler(log_file)
            fh.setFormatter(formatter)
            self._logger.addHandler(fh)
        except OSError as exc:
            _fallback_logger.warning(
                "Cannot open log file %s: %s — falling back to stream handler only",
                log_file,
                exc,
            )
        sh = logging.StreamHandler(sys.stderr)
        sh.setFormatter(None)
        self._logger.addHandler(sh)
        self._logger.setLevel(logging.INFO)
        self._logger.propagate = False

    def xǁLoggerǁ_configure_logger__mutmut_20(self, log_file: str, structured_log: bool) -> None:
        """Attach FileHandler + StreamHandler and context filter to the named logger."""
        self._logger.addFilter(self._filter)
        if self._logger.handlers:
            return
        formatter: logging.Formatter = (
            _JsonFormatter() if structured_log else logging.Formatter(self._FORMAT)
        )
        try:
            fh = logging.FileHandler(log_file)
            fh.setFormatter(formatter)
            self._logger.addHandler(fh)
        except OSError as exc:
            _fallback_logger.warning(
                "Cannot open log file %s: %s — falling back to stream handler only",
                log_file,
                exc,
            )
        sh = logging.StreamHandler(sys.stderr)
        sh.setFormatter(formatter)
        self._logger.addHandler(None)
        self._logger.setLevel(logging.INFO)
        self._logger.propagate = False

    def xǁLoggerǁ_configure_logger__mutmut_21(self, log_file: str, structured_log: bool) -> None:
        """Attach FileHandler + StreamHandler and context filter to the named logger."""
        self._logger.addFilter(self._filter)
        if self._logger.handlers:
            return
        formatter: logging.Formatter = (
            _JsonFormatter() if structured_log else logging.Formatter(self._FORMAT)
        )
        try:
            fh = logging.FileHandler(log_file)
            fh.setFormatter(formatter)
            self._logger.addHandler(fh)
        except OSError as exc:
            _fallback_logger.warning(
                "Cannot open log file %s: %s — falling back to stream handler only",
                log_file,
                exc,
            )
        sh = logging.StreamHandler(sys.stderr)
        sh.setFormatter(formatter)
        self._logger.addHandler(sh)
        self._logger.setLevel(None)
        self._logger.propagate = False

    def xǁLoggerǁ_configure_logger__mutmut_22(self, log_file: str, structured_log: bool) -> None:
        """Attach FileHandler + StreamHandler and context filter to the named logger."""
        self._logger.addFilter(self._filter)
        if self._logger.handlers:
            return
        formatter: logging.Formatter = (
            _JsonFormatter() if structured_log else logging.Formatter(self._FORMAT)
        )
        try:
            fh = logging.FileHandler(log_file)
            fh.setFormatter(formatter)
            self._logger.addHandler(fh)
        except OSError as exc:
            _fallback_logger.warning(
                "Cannot open log file %s: %s — falling back to stream handler only",
                log_file,
                exc,
            )
        sh = logging.StreamHandler(sys.stderr)
        sh.setFormatter(formatter)
        self._logger.addHandler(sh)
        self._logger.setLevel(logging.INFO)
        self._logger.propagate = None

    def xǁLoggerǁ_configure_logger__mutmut_23(self, log_file: str, structured_log: bool) -> None:
        """Attach FileHandler + StreamHandler and context filter to the named logger."""
        self._logger.addFilter(self._filter)
        if self._logger.handlers:
            return
        formatter: logging.Formatter = (
            _JsonFormatter() if structured_log else logging.Formatter(self._FORMAT)
        )
        try:
            fh = logging.FileHandler(log_file)
            fh.setFormatter(formatter)
            self._logger.addHandler(fh)
        except OSError as exc:
            _fallback_logger.warning(
                "Cannot open log file %s: %s — falling back to stream handler only",
                log_file,
                exc,
            )
        sh = logging.StreamHandler(sys.stderr)
        sh.setFormatter(formatter)
        self._logger.addHandler(sh)
        self._logger.setLevel(logging.INFO)
        self._logger.propagate = True

mutants_xǁLoggerǁ__init____mutmut['_mutmut_orig'] = Logger.xǁLoggerǁ__init____mutmut_orig # type: ignore # mutmut generated
mutants_xǁLoggerǁ__init____mutmut['xǁLoggerǁ__init____mutmut_1'] = Logger.xǁLoggerǁ__init____mutmut_1 # type: ignore # mutmut generated
mutants_xǁLoggerǁ__init____mutmut['xǁLoggerǁ__init____mutmut_2'] = Logger.xǁLoggerǁ__init____mutmut_2 # type: ignore # mutmut generated
mutants_xǁLoggerǁ__init____mutmut['xǁLoggerǁ__init____mutmut_3'] = Logger.xǁLoggerǁ__init____mutmut_3 # type: ignore # mutmut generated
mutants_xǁLoggerǁ__init____mutmut['xǁLoggerǁ__init____mutmut_4'] = Logger.xǁLoggerǁ__init____mutmut_4 # type: ignore # mutmut generated
mutants_xǁLoggerǁ__init____mutmut['xǁLoggerǁ__init____mutmut_5'] = Logger.xǁLoggerǁ__init____mutmut_5 # type: ignore # mutmut generated
mutants_xǁLoggerǁ__init____mutmut['xǁLoggerǁ__init____mutmut_6'] = Logger.xǁLoggerǁ__init____mutmut_6 # type: ignore # mutmut generated
mutants_xǁLoggerǁ__init____mutmut['xǁLoggerǁ__init____mutmut_7'] = Logger.xǁLoggerǁ__init____mutmut_7 # type: ignore # mutmut generated
mutants_xǁLoggerǁ__init____mutmut['xǁLoggerǁ__init____mutmut_8'] = Logger.xǁLoggerǁ__init____mutmut_8 # type: ignore # mutmut generated
mutants_xǁLoggerǁ__init____mutmut['xǁLoggerǁ__init____mutmut_9'] = Logger.xǁLoggerǁ__init____mutmut_9 # type: ignore # mutmut generated
mutants_xǁLoggerǁ__init____mutmut['xǁLoggerǁ__init____mutmut_10'] = Logger.xǁLoggerǁ__init____mutmut_10 # type: ignore # mutmut generated
mutants_xǁLoggerǁ__init____mutmut['xǁLoggerǁ__init____mutmut_11'] = Logger.xǁLoggerǁ__init____mutmut_11 # type: ignore # mutmut generated
mutants_xǁLoggerǁ__init____mutmut['xǁLoggerǁ__init____mutmut_12'] = Logger.xǁLoggerǁ__init____mutmut_12 # type: ignore # mutmut generated
mutants_xǁLoggerǁ__init____mutmut['xǁLoggerǁ__init____mutmut_13'] = Logger.xǁLoggerǁ__init____mutmut_13 # type: ignore # mutmut generated
mutants_xǁLoggerǁ__init____mutmut['xǁLoggerǁ__init____mutmut_14'] = Logger.xǁLoggerǁ__init____mutmut_14 # type: ignore # mutmut generated
mutants_xǁLoggerǁ__init____mutmut['xǁLoggerǁ__init____mutmut_15'] = Logger.xǁLoggerǁ__init____mutmut_15 # type: ignore # mutmut generated
mutants_xǁLoggerǁ__init____mutmut['xǁLoggerǁ__init____mutmut_16'] = Logger.xǁLoggerǁ__init____mutmut_16 # type: ignore # mutmut generated
mutants_xǁLoggerǁ__init____mutmut['xǁLoggerǁ__init____mutmut_17'] = Logger.xǁLoggerǁ__init____mutmut_17 # type: ignore # mutmut generated
mutants_xǁLoggerǁ__init____mutmut['xǁLoggerǁ__init____mutmut_18'] = Logger.xǁLoggerǁ__init____mutmut_18 # type: ignore # mutmut generated
mutants_xǁLoggerǁ__init____mutmut['xǁLoggerǁ__init____mutmut_19'] = Logger.xǁLoggerǁ__init____mutmut_19 # type: ignore # mutmut generated
mutants_xǁLoggerǁ__init____mutmut['xǁLoggerǁ__init____mutmut_20'] = Logger.xǁLoggerǁ__init____mutmut_20 # type: ignore # mutmut generated
mutants_xǁLoggerǁ__init____mutmut['xǁLoggerǁ__init____mutmut_21'] = Logger.xǁLoggerǁ__init____mutmut_21 # type: ignore # mutmut generated

mutants_xǁLoggerǁ__getattr____mutmut['_mutmut_orig'] = Logger.xǁLoggerǁ__getattr____mutmut_orig # type: ignore # mutmut generated
mutants_xǁLoggerǁ__getattr____mutmut['xǁLoggerǁ__getattr____mutmut_1'] = Logger.xǁLoggerǁ__getattr____mutmut_1 # type: ignore # mutmut generated
mutants_xǁLoggerǁ__getattr____mutmut['xǁLoggerǁ__getattr____mutmut_2'] = Logger.xǁLoggerǁ__getattr____mutmut_2 # type: ignore # mutmut generated
mutants_xǁLoggerǁ__getattr____mutmut['xǁLoggerǁ__getattr____mutmut_3'] = Logger.xǁLoggerǁ__getattr____mutmut_3 # type: ignore # mutmut generated
mutants_xǁLoggerǁ__getattr____mutmut['xǁLoggerǁ__getattr____mutmut_4'] = Logger.xǁLoggerǁ__getattr____mutmut_4 # type: ignore # mutmut generated

mutants_xǁLoggerǁ_configure_logger__mutmut['_mutmut_orig'] = Logger.xǁLoggerǁ_configure_logger__mutmut_orig # type: ignore # mutmut generated
mutants_xǁLoggerǁ_configure_logger__mutmut['xǁLoggerǁ_configure_logger__mutmut_1'] = Logger.xǁLoggerǁ_configure_logger__mutmut_1 # type: ignore # mutmut generated
mutants_xǁLoggerǁ_configure_logger__mutmut['xǁLoggerǁ_configure_logger__mutmut_2'] = Logger.xǁLoggerǁ_configure_logger__mutmut_2 # type: ignore # mutmut generated
mutants_xǁLoggerǁ_configure_logger__mutmut['xǁLoggerǁ_configure_logger__mutmut_3'] = Logger.xǁLoggerǁ_configure_logger__mutmut_3 # type: ignore # mutmut generated
mutants_xǁLoggerǁ_configure_logger__mutmut['xǁLoggerǁ_configure_logger__mutmut_4'] = Logger.xǁLoggerǁ_configure_logger__mutmut_4 # type: ignore # mutmut generated
mutants_xǁLoggerǁ_configure_logger__mutmut['xǁLoggerǁ_configure_logger__mutmut_5'] = Logger.xǁLoggerǁ_configure_logger__mutmut_5 # type: ignore # mutmut generated
mutants_xǁLoggerǁ_configure_logger__mutmut['xǁLoggerǁ_configure_logger__mutmut_6'] = Logger.xǁLoggerǁ_configure_logger__mutmut_6 # type: ignore # mutmut generated
mutants_xǁLoggerǁ_configure_logger__mutmut['xǁLoggerǁ_configure_logger__mutmut_7'] = Logger.xǁLoggerǁ_configure_logger__mutmut_7 # type: ignore # mutmut generated
mutants_xǁLoggerǁ_configure_logger__mutmut['xǁLoggerǁ_configure_logger__mutmut_8'] = Logger.xǁLoggerǁ_configure_logger__mutmut_8 # type: ignore # mutmut generated
mutants_xǁLoggerǁ_configure_logger__mutmut['xǁLoggerǁ_configure_logger__mutmut_9'] = Logger.xǁLoggerǁ_configure_logger__mutmut_9 # type: ignore # mutmut generated
mutants_xǁLoggerǁ_configure_logger__mutmut['xǁLoggerǁ_configure_logger__mutmut_10'] = Logger.xǁLoggerǁ_configure_logger__mutmut_10 # type: ignore # mutmut generated
mutants_xǁLoggerǁ_configure_logger__mutmut['xǁLoggerǁ_configure_logger__mutmut_11'] = Logger.xǁLoggerǁ_configure_logger__mutmut_11 # type: ignore # mutmut generated
mutants_xǁLoggerǁ_configure_logger__mutmut['xǁLoggerǁ_configure_logger__mutmut_12'] = Logger.xǁLoggerǁ_configure_logger__mutmut_12 # type: ignore # mutmut generated
mutants_xǁLoggerǁ_configure_logger__mutmut['xǁLoggerǁ_configure_logger__mutmut_13'] = Logger.xǁLoggerǁ_configure_logger__mutmut_13 # type: ignore # mutmut generated
mutants_xǁLoggerǁ_configure_logger__mutmut['xǁLoggerǁ_configure_logger__mutmut_14'] = Logger.xǁLoggerǁ_configure_logger__mutmut_14 # type: ignore # mutmut generated
mutants_xǁLoggerǁ_configure_logger__mutmut['xǁLoggerǁ_configure_logger__mutmut_15'] = Logger.xǁLoggerǁ_configure_logger__mutmut_15 # type: ignore # mutmut generated
mutants_xǁLoggerǁ_configure_logger__mutmut['xǁLoggerǁ_configure_logger__mutmut_16'] = Logger.xǁLoggerǁ_configure_logger__mutmut_16 # type: ignore # mutmut generated
mutants_xǁLoggerǁ_configure_logger__mutmut['xǁLoggerǁ_configure_logger__mutmut_17'] = Logger.xǁLoggerǁ_configure_logger__mutmut_17 # type: ignore # mutmut generated
mutants_xǁLoggerǁ_configure_logger__mutmut['xǁLoggerǁ_configure_logger__mutmut_18'] = Logger.xǁLoggerǁ_configure_logger__mutmut_18 # type: ignore # mutmut generated
mutants_xǁLoggerǁ_configure_logger__mutmut['xǁLoggerǁ_configure_logger__mutmut_19'] = Logger.xǁLoggerǁ_configure_logger__mutmut_19 # type: ignore # mutmut generated
mutants_xǁLoggerǁ_configure_logger__mutmut['xǁLoggerǁ_configure_logger__mutmut_20'] = Logger.xǁLoggerǁ_configure_logger__mutmut_20 # type: ignore # mutmut generated
mutants_xǁLoggerǁ_configure_logger__mutmut['xǁLoggerǁ_configure_logger__mutmut_21'] = Logger.xǁLoggerǁ_configure_logger__mutmut_21 # type: ignore # mutmut generated
mutants_xǁLoggerǁ_configure_logger__mutmut['xǁLoggerǁ_configure_logger__mutmut_22'] = Logger.xǁLoggerǁ_configure_logger__mutmut_22 # type: ignore # mutmut generated
mutants_xǁLoggerǁ_configure_logger__mutmut['xǁLoggerǁ_configure_logger__mutmut_23'] = Logger.xǁLoggerǁ_configure_logger__mutmut_23 # type: ignore # mutmut generated
