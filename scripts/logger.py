#!/usr/bin/env python3
"""
logger.py
Shared logging setup for entry-point scripts.

Usage (entry-point scripts only):
    logger = Logger(__name__, "/opt/llm/logs/xxx.log")

Library modules should use:
    logger = logging.getLogger(__name__)
"""

import logging
import sys
from typing import Any


class Logger:
    """Configure a named logger with a dedicated FileHandler per entry script.

    Each Logger instance attaches its own FileHandler + StreamHandler directly
    to the named logger (not the root logger).  This guarantees that
    crawl.log / ingest.log / agent.log etc. receive only their own entries,
    even when multiple entry scripts share the same process.

    propagate=False prevents records from also appearing on the root logger,
    avoiding duplicate output when the root logger has handlers of its own.
    """

    _FORMAT = "%(asctime)s %(levelname)s [%(funcName)s] %(message)s"

    def __init__(self, name: str, log_file: str) -> None:
        self._validate_args(name, log_file)
        self._logger = logging.getLogger(name)
        self._configure_logger(log_file)

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

    def _configure_logger(self, log_file: str) -> None:
        """Attach FileHandler + StreamHandler directly to the named logger."""
        if self._logger.handlers:
            # Already configured; skip to avoid duplicate handlers on reload
            return
        formatter = logging.Formatter(self._FORMAT)
        try:
            fh = logging.FileHandler(log_file)
            fh.setFormatter(formatter)
            self._logger.addHandler(fh)
        except OSError as exc:
            # Log file not writable; stderr-only fallback is attached below
            sys.stderr.write(
                f"[Logger] Cannot open log file {log_file}: {exc}"
                " — falling back to stderr only.\n"
            )
        sh = logging.StreamHandler(sys.stderr)
        sh.setFormatter(formatter)
        self._logger.addHandler(sh)
        self._logger.setLevel(logging.INFO)
        # Prevent records from propagating to the root logger to avoid duplicates
        self._logger.propagate = False
