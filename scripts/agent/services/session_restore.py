"""agent/services/session_restore.py
Session restore service — rebuild history and switch the active session.

Extracted from cmd_session._SessionMixin so the restore logic can be
tested independently of the REPL.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from agent.commands.mixin_base import reset_session_stats

if TYPE_CHECKING:
    from agent.context import AgentContext

logger = logging.getLogger(__name__)


def restore_session(ctx: AgentContext, session_id: int) -> tuple[bool, str]:
    """Restore session: rebuild history, switch session ID, reset stats.

    Returns (True, message) on success, (False, message) when not found.
    """
    messages = ctx.session.fetch_messages(session_id)
    if not messages:
        return False, f"Session {session_id} not found or has no messages."
    system_msgs = [m for m in ctx.conv.history if m["role"] == "system"]
    ctx.conv.history = system_msgs + messages
    ctx.session.session_id = session_id
    reset_session_stats(ctx)
    logger.info(f"Session {session_id} loaded: {len(messages)} messages")
    return True, f"Session {session_id} loaded: {len(messages)} messages restored."
