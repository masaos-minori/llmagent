#!/usr/bin/env python3
"""agent/commands/cmd_session.py
Session management mixin for CommandRegistry.

Provides _SessionMixin with:
  _generate_session_title  — background task: LLM-generated short title (delegates to SessionTitleService)
  _session_load_safe       — safe session restore by ID
  _session_delete          — session deletion with self-guard
  _cmd_session             — /session dispatcher
  _load_session            — restore messages into ctx.conv.history (delegates to restore_session)
"""

import logging

from agent.commands.mixin_base import MixinBase
from agent.commands.utils import parse_command_args

logger = logging.getLogger(__name__)


class _SessionMixin(MixinBase):
    """Session management slash-command handlers."""

    async def _generate_session_title(self, first_input: str) -> None:
        """Generate and persist a session title via LLM (background task)."""
        from agent.services.exceptions import (
            SessionTitleGenerationError,  # noqa: PLC0415 — lazy: deferred to avoid import cost
        )
        from agent.services.session_title import (
            SessionTitleService,  # noqa: PLC0415 — lazy: deferred to avoid import cost
        )

        try:
            await SessionTitleService().generate(self._ctx, first_input)
        except SessionTitleGenerationError as e:
            logger.warning("Session title generation failed: %s", e)

    def _session_load_safe(self, arg: str) -> None:
        """Parse arg as an integer session ID and load it; print error on invalid."""
        if not arg.isdigit():
            self._out.write_validation_error(f"Invalid session ID: {arg}")
            return
        self._load_session(int(arg))

    def _session_delete(self, arg: str) -> None:
        """Parse arg as an integer session ID and delete it; guard current session."""
        if not arg.isdigit():
            self._out.write_validation_error(f"Invalid session ID: {arg}")
            return
        sid = int(arg)
        if sid == self._ctx.session.session_id:
            self._out.write_validation_error("Cannot delete the current session.")
            return
        ok = self._ctx.session.delete_session(sid)
        if ok:
            self._out.write_success(f"Session {sid} deleted.")
        else:
            self._out.write_no_data(f"Session {sid} not found.")

    def _cmd_session(self, args: str) -> None:
        """Handle /session list [n] | load <id> | rename <title> | delete <id>."""
        parsed = parse_command_args(args.strip().split())
        sub = parsed.subcommand or "list"

        if sub == "list":
            limit_raw = parsed.positional[0] if parsed.positional else "20"
            limit = int(limit_raw) if limit_raw.isdigit() else 20
            rows = self._ctx.session.list_sessions(limit)
            if not rows:
                self._out.write_no_data("No sessions found")
                return
            table_rows = []
            for r in rows:
                title = r["title"] if r["title"] is not None else ""
                title_display = title[:29] + "..." if len(title) > 32 else title
                table_rows.append(
                    [
                        f"{r['session_id']:>4}{'*' if r['is_current'] else ' '}",
                        title_display,
                        r["created_at"],
                    ]
                )
            self._out.write_table(["ID  ", "Title", "Created"], table_rows)
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

        self._out.write_validation_error(
            "/session list [n] | /session load <id>"
            " | /session rename <title> | /session delete <id>"
        )

    def _load_session(self, session_id: int) -> None:
        """Restore a previous session via session_restore service."""
        from agent.services.exceptions import (
            SessionNotFoundError,  # noqa: PLC0415 — lazy: deferred to avoid import cost
        )
        from agent.services.session_restore import (
            restore_session,  # noqa: PLC0415 — lazy: deferred to avoid import cost
        )

        try:
            result = restore_session(self._ctx, session_id)
            self._out.write_success(
                f"Session {result.session_id} loaded:"
                f" {result.n_messages} messages restored."
            )
        except SessionNotFoundError as e:
            self._out.write_no_data(str(e))
