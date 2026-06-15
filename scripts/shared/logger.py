#!/usr/bin/env python3
"""logger.py
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

import orjson


def _require_str(value: Any, name: str) -> None:
    """Validate that value is a non-empty string; raises ValueError otherwise."""
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{name} must be a non-empty str, got: {value!r}")


class _ContextFilter(logging.Filter):
    """Injects per-turn trace fields into every LogRecord on this logger.

    Uses contextvars.ContextVar so each asyncio task gets its own context,
    preventing field leakage between concurrent coroutines sharing the same logger.
    """

    def __init__(self) -> None:
        super().__init__()
        self._cv: ContextVar[dict[str, Any]] = ContextVar("_log_context", default={})

    def set(self, **fields: Any) -> None:
        self._cv.set({k: v for k, v in fields.items() if v is not None})

    def clear(self) -> None:
        self._cv.set({})

    def filter(self, record: logging.LogRecord) -> bool:
        for k, v in self._cv.get().items():
            setattr(record, k, v)
        return True


class _JsonFormatter(logging.Formatter):
    """Format a LogRecord as a single JSON line for structured log output."""

    _CONTEXT_KEYS = ("turn_id", "session_id", "rag_query_id")

    def format(self, record: logging.LogRecord) -> str:
        entry: dict[str, Any] = {
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
        return orjson.dumps(entry).decode()


class Logger:
    """Configure a named logger with a dedicated FileHandler per entry script; propagate=False prevents duplicate output; structured_log=True switches to JSON-lines."""

    _FORMAT = "%(asctime)s %(levelname)s [%(funcName)s] %(message)s"

    def __init__(
        self,
        name: str,
        log_file: str,
        *,
        structured_log: bool = False,
    ) -> None:
        _require_str(name, "Logger name")
        _require_str(log_file, "log_file")
        self._logger = logging.getLogger(name)
        self._filter = _ContextFilter()
        self._configure_logger(log_file, structured_log)

    def set_context(self, **fields: Any) -> None:
        """Inject trace fields (turn_id, session_id, rag_query_id) into log records."""
        self._filter.set(**fields)

    def clear_context(self) -> None:
        """Remove all injected trace fields from subsequent log records."""
        self._filter.clear()

    def __getattr__(self, name: str) -> Any:
        return getattr(self._logger, name)

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
            sys.stderr.write(
                f"[Logger] Cannot open log file {log_file}: {exc}"
                " — falling back to stderr only.\n",
            )
        sh = logging.StreamHandler(sys.stderr)
        sh.setFormatter(formatter)
        self._logger.addHandler(sh)
        self._logger.setLevel(logging.INFO)
        self._logger.propagate = False
