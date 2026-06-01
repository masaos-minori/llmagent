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
from typing import Any

import orjson


class _ContextFilter(logging.Filter):
    """Injects per-turn trace fields into every LogRecord on this logger."""

    def __init__(self) -> None:
        super().__init__()
        self._fields: dict[str, Any] = {}

    def set(self, **fields: Any) -> None:
        # Store only non-None fields to keep log records clean
        self._fields = {k: v for k, v in fields.items() if v is not None}

    def clear(self) -> None:
        self._fields = {}

    def filter(self, record: logging.LogRecord) -> bool:
        for k, v in self._fields.items():
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
        serialized: bytes = orjson.dumps(entry)
        return serialized.decode()


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
        self._validate_args(name, log_file)
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
        # Delegate all logging methods (info, warning, error, exception, debug …)
        # to the underlying logging.Logger instance so this class is a drop-in.
        return getattr(self._logger, name)

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _validate_args(name: str, log_file: str) -> None:
        """Guard: reject blank logger name or log file path."""
        if not isinstance(name, str) or not name.strip():
            raise ValueError(f"Logger name must be a non-empty str, got: {name!r}")
        if not isinstance(log_file, str) or not log_file.strip():
            raise ValueError(f"log_file must be a non-empty str, got: {log_file!r}")

    def _configure_logger(self, log_file: str, structured_log: bool) -> None:
        """Attach FileHandler + StreamHandler and context filter to the named logger."""
        # The filter is added each time; multiple Logger instances with the same name
        # each add their own filter, which is harmless (later filter overwrites fields).
        self._logger.addFilter(self._filter)
        if self._logger.handlers:
            # Already configured; skip to avoid duplicate handlers on reload
            return
        formatter: logging.Formatter = (
            _JsonFormatter() if structured_log else logging.Formatter(self._FORMAT)
        )
        try:
            fh = logging.FileHandler(log_file)
            fh.setFormatter(formatter)
            self._logger.addHandler(fh)
        except OSError as exc:
            # Log file not writable; stderr-only fallback is attached below
            sys.stderr.write(
                f"[Logger] Cannot open log file {log_file}: {exc}"
                " — falling back to stderr only.\n",
            )
        sh = logging.StreamHandler(sys.stderr)
        sh.setFormatter(formatter)
        self._logger.addHandler(sh)
        self._logger.setLevel(logging.INFO)
        # Prevent records from propagating to the root logger to avoid duplicates
        self._logger.propagate = False
