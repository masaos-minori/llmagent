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
from agent.services.models import SessionRow

logger = logging.getLogger(__name__)

SESSION_TITLE_MAX_CHARS = 32
SESSION_TITLE_TRUNCATE_AT = SESSION_TITLE_MAX_CHARS - 3


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

        self._ctx.session.set_title_pending(True)
        try:
            await SessionTitleService().generate(self._ctx, first_input)
        except SessionTitleGenerationError as e:
            logger.warning("Session title generation failed, using fallback: %s", e)
            clean_input = first_input.strip() if first_input else ""
            if not clean_input:
                fallback_title = "(New Session)"
            elif len(clean_input) > SESSION_TITLE_MAX_CHARS:
                fallback_title = clean_input[:SESSION_TITLE_TRUNCATE_AT] + "..."
            else:
                fallback_title = clean_input
            try:
                self._ctx.session.set_title(fallback_title)
            except Exception as db_err:  # noqa: BLE001
                logger.error(
                    "Session title fallback set_title failed: %s (session_id=%s)",
                    db_err,
                    self._ctx.session.session_id,
                )
            else:
                if self._ctx.services_required.audit_logger is not None:
                    self._ctx.services_required.audit_logger.warning(
                        "session_title_fallback session_id=%s fallback=%r reason=%s",
                        self._ctx.session.session_id,
                        fallback_title,
                        e,
                    )
        finally:
            self._ctx.session.set_title_pending(False)

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

    def _cmd_session(self, args: str) -> None:
        """Handle /session list [n] | load <id> | rename <title> | delete <id>."""
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
