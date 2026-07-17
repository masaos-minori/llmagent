#!/usr/bin/env python3
"""agent/commands/cmd_audit.py

Audit log inspection mixin for CommandRegistry.

Provides _AuditMixin with:
  _cmd_audit  -- /audit: tail, turn, tool subcommands for browsing audit.log
"""

from __future__ import annotations

import collections
import logging
import pathlib
from collections.abc import Iterator
from typing import Any

import orjson
from shared.json_utils import dumps as _json_dumps

from agent.commands.mixin_base import MixinBase

_AUDIT_TAIL_LINES = 20
_AUDIT_TOOL_SCAN_LINES = 1000
_AUDIT_TOOL_MAX_RESULTS = 50

logger = logging.getLogger(__name__)


class _AuditMixin(MixinBase):
    """Audit log inspection slash-command handlers."""

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        """Forward arguments to MixinBase constructor."""
        super().__init__(*args, **kwargs)

    def _audit_log_path(self) -> pathlib.Path:
        """Resolve the audit log file path from config."""
        return pathlib.Path(self._ctx.cfg.obs.audit_log_file)

    def _iter_audit_lines(self, path: pathlib.Path) -> Iterator[dict[str, Any]]:
        """Yield parsed JSONL records from path, skipping non-JSON lines."""
        with path.open(encoding="utf-8") as f:
            for raw in f:
                line = raw.strip()
                if not line:
                    continue
                try:
                    yield orjson.loads(line)
                except orjson.JSONDecodeError:
                    continue

    def _audit_tail(self, n: int) -> None:
        """Display the last N lines of the audit log file."""
        path = self._audit_log_path()
        if not path.exists():
            self._out.write(f"Audit log not found: {path}")
            return
        try:
            with path.open(encoding="utf-8") as f:
                buf = collections.deque(f, maxlen=n)
        except OSError as e:
            self._out.write_error(f"Cannot read audit log: {e}")
            return
        if not buf:
            self._out.write_no_data("Audit log is empty.")
            return
        for line in buf:
            self._out.write(line.rstrip("\n"))

    def _audit_turn(self, task_id: str) -> None:
        """Display all audit log entries for the given task ID."""
        path = self._audit_log_path()
        if not path.exists():
            self._out.write(f"Audit log not found: {path}")
            return
        count = 0
        try:
            for rec in self._iter_audit_lines(path):
                if rec.get("task_id") == task_id:
                    self._out.write(_json_dumps(rec))
                    count += 1
        except OSError as e:
            self._out.write_error(f"Cannot read audit log: {e}")
            return
        if count == 0:
            self._out.write_no_data(f"No events found for turn: {task_id}")

    def _audit_tool(self, tool_name: str) -> None:
        """Scan the audit log for events matching the given tool name and display them."""
        path = self._audit_log_path()
        if not path.exists():
            self._out.write(f"Audit log not found: {path}")
            return
        try:
            tail: collections.deque[dict[str, Any]] = collections.deque(
                self._iter_audit_lines(path), maxlen=_AUDIT_TOOL_SCAN_LINES
            )
        except OSError as e:
            self._out.write_error(f"Cannot read audit log: {e}")
            return
        results = [rec for rec in tail if rec.get("tool") == tool_name]
        if not results:
            self._out.write_no_data(f"No events found for tool: {tool_name}")
            return
        for rec in results[:_AUDIT_TOOL_MAX_RESULTS]:
            self._out.write(_json_dumps(rec))
        if len(results) > _AUDIT_TOOL_MAX_RESULTS:
            self._out.write(
                f"  ... {len(results) - _AUDIT_TOOL_MAX_RESULTS} more events omitted"
            )

    def _cmd_audit(self, args: str = "") -> None:
        """Browse the audit log.

        Usage:
          /audit [tail [N]]          Show last N raw lines (default: 20)
          /audit turn <task_id>      Show all events for one turn
          /audit tool <name>         Show recent events for a tool
        """
        parts = args.strip().split(None, 1)
        sub = parts[0] if parts else "tail"
        rest = parts[1].strip() if len(parts) > 1 else ""

        if not sub or sub == "tail":
            n = _AUDIT_TAIL_LINES
            if rest:
                try:
                    n = int(rest)
                    if n <= 0:
                        raise ValueError
                except (ValueError, TypeError):
                    self._out.write_validation_error("Usage: /audit tail [N]")
                    return
            self._audit_tail(n)
        elif sub == "turn":
            if not rest:
                self._out.write_validation_error("Usage: /audit turn <task_id>")
                return
            self._audit_turn(rest)
        elif sub == "tool":
            if not rest:
                self._out.write_validation_error("Usage: /audit tool <name>")
                return
            self._audit_tool(rest)
        else:
            self._out.write_validation_error(
                "Usage: /audit [tail [N] | turn <task_id> | tool <name>]"
            )
