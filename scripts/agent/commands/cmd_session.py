#!/usr/bin/env python3
"""agent/commands/cmd_session.py

Session management mixin for CommandRegistry.

Provides _SessionMixin with:
  _cmd_session             — /session dispatcher (list/load/rename/delete/export/stats/health/checkpoint/vacuum/purge/recover)
  _generate_session_title  — background task: LLM-generated short title (delegates to SessionTitleService)
  _session_load_safe       — safe session restore by ID
  _session_delete          — session deletion with self-guard
  _load_session            — restore messages into ctx.conv.history (delegates to restore_session)
"""

import logging
from collections.abc import Callable

from agent.commands.db_session_ops import DbSessionOps
from agent.commands.mixin_base import MixinBase
from agent.commands.session_title import SessionTitleGen
from agent.commands.utils import parse_command_args
from agent.services.db_maintenance_service import DbMaintenanceService
from agent.services.export_formatter import render_export, write_export
from agent.services.models import SessionRow

logger = logging.getLogger(__name__)


class _SessionMixin(MixinBase):
    """Session management slash-command handlers."""

    def __init__(self, *args, **kwargs) -> None:
        """Initialize the session mixin via MixinBase constructor and sub-components."""
        super().__init__(*args, **kwargs)
        self._title_gen = SessionTitleGen(self._ctx, self._out)
        self._db_session_ops = DbSessionOps(self._ctx, self._out)

    async def _generate_session_title(self, first_input: str) -> None:
        """Generate and persist a session title via LLM (background task)."""
        await self._title_gen.generate(first_input)

    def _session_load_safe(self, arg: str) -> None:
        """Parse arg as an integer session ID and load it; print error on invalid."""
        try:
            sid = int(arg)
            if sid <= 0:
                raise ValueError
        except (ValueError, TypeError):
            self._out.write_validation_error(
                "Invalid session ID: must be a positive integer"
            )
            return
        self._load_session(sid)

    def _session_delete(self, arg: str) -> None:
        """Parse arg as an integer session ID and delete it; guard current session."""
        try:
            sid = int(arg)
            if sid <= 0:
                raise ValueError
        except (ValueError, TypeError):
            self._out.write_validation_error(
                "Invalid session ID: must be a positive integer"
            )
            return
        if sid == self._ctx.session.session_id:
            self._out.write_validation_error("Cannot delete the current session.")
            return
        ok = self._ctx.session.delete_session(sid)
        if ok:
            self._out.write_success(f"Session {sid} deleted.")
        else:
            self._out.write_no_data(f"Session {sid} not found.")

    def _session_list(self, limit_arg: str) -> None:
        """List sessions table; limit_arg is the raw CLI positional (digit string or empty)."""
        from agent.commands.session_title import (  # noqa: PLC0415 — lazy import
            SESSION_TITLE_MAX_CHARS,
            SESSION_TITLE_TRUNCATE_AT,
        )

        try:
            limit = int(limit_arg) if limit_arg else 20
        except (ValueError, TypeError):
            limit = 20
        raw_rows = self._ctx.session.list_sessions(limit)
        if not raw_rows:
            self._out.write_no_data("No sessions found")
            return
        session_rows = []
        for r in raw_rows:
            ca = r.get("created_at")
            if ca is not None and not isinstance(ca, str):
                raise TypeError(
                    f"created_at must be str or None, got {type(ca).__name__}"
                )
            session_rows.append(
                SessionRow(
                    session_id=r["session_id"],
                    title=r.get("title"),
                    created_at=ca if ca is not None else "",
                    is_current=bool(r.get("is_current", False)),
                )
            )
        current_id = self._ctx.session.session_id
        table_rows = []
        for sr in session_rows:
            is_current = sr.session_id == current_id
            if is_current and self._ctx.session.is_title_pending():
                title_display = "(generating...)"
            elif sr.title:
                title_display = (
                    sr.title[:SESSION_TITLE_TRUNCATE_AT] + "..."
                    if len(sr.title) > SESSION_TITLE_MAX_CHARS
                    else sr.title
                )
            else:
                title_display = "(no title)"
            table_rows.append(
                [
                    f"{sr.session_id:>4}{'*' if sr.is_current else ' '}",
                    title_display,
                    sr.created_at,
                ]
            )
        self._out.write_table(["ID  ", "Title", "Created"], table_rows)

    def _db_session_stats(self) -> None:
        """Print session/message counts from the Session database."""
        result = DbMaintenanceService().stats()
        self._out.write_kv(
            [
                ("sessions", f"{result.sessions:,}"),
                ("messages", f"{result.messages:,}"),
                ("target", "Session"),
            ]
        )

    def _session_export(self, args: str) -> None:
        """Export the current conversation history to Markdown or JSON.

        Usage: /session export [markdown|json] [filename]
        """
        ctx = self._ctx
        parts = args.strip().split()
        fmt = "md"
        outfile: str | None = None
        for part in parts:
            if part in ("markdown", "md"):
                fmt = "md"
            elif part == "json":
                fmt = "json"
            else:
                outfile = part
        content = render_export(ctx.conv.history, fmt)
        write_export(content, outfile, len(ctx.conv.history))

    def _cmd_session(self, args: str) -> None:
        """Handle /session list [n] | load <id> | rename <title> | delete <id>
        | export markdown|json [file] | stats|health|checkpoint|vacuum|purge|recover.
        """
        parsed = parse_command_args(args.strip().split())
        sub = parsed.subcommand or "list"

        if sub == "list":
            self._session_list(parsed.positional[0] if parsed.positional else "20")
            return

        if sub == "load":
            arg = parsed.positional[0] if parsed.positional else ""
            self._session_load_safe(arg)
            return

        if sub == "rename":
            title = " ".join(parsed.positional)
            if not title:
                self._out.write_validation_error("/session rename <title>")
                return
            self._ctx.session.set_title(title)
            self._out.write_success(f"Session renamed: {title[:50]!r}")
            return

        if sub == "delete":
            arg = parsed.positional[0] if parsed.positional else ""
            self._session_delete(arg)
            return

        rest = args.strip()[len(sub) :].strip()
        db_dispatch: dict[str, Callable[[], None]] = {
            "export": lambda: self._session_export(rest),
            "stats": self._db_session_stats,
            "health": self._db_session_ops.health,
            "checkpoint": lambda: self._db_session_ops.checkpoint(
                rest.strip().upper() or None
            ),
            "vacuum": self._db_session_ops.vacuum,
            "purge": lambda: self._db_session_ops.purge(rest),
            "recover": lambda: self._db_session_ops.recover(rest.strip() or None),
        }
        handler = db_dispatch.get(sub)
        if handler is not None:
            handler()
            return

        self._out.write_validation_error(
            "/session list [n] | /session load <id>"
            " | /session rename <title> | /session delete <id>"
            " | /session export markdown|json [file]"
            " | /session stats|health|checkpoint|vacuum|purge|recover"
        )

    def _load_session(self, session_id: int) -> None:
        """Restore a previous session via session_restore service."""
        from agent.services.exceptions import (  # noqa: PLC0415 — lazy import
            SessionNotFoundError,
        )
        from agent.services.session_restore import (  # noqa: PLC0415 — lazy import
            restore_session,
        )

        try:
            result = restore_session(self._ctx, session_id)
            self._out.write_success(
                f"Session {result.session_id} loaded: {result.n_messages} messages restored."
            )
        except SessionNotFoundError as e:
            self._out.write_no_data(str(e))
