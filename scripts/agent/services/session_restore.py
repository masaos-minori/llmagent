"""agent/services/session_restore.py

Session restore service — rebuild history and switch the active session.

Extracted from cmd_session._SessionMixin so the restore logic can be
tested independently of the REPL.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, cast

from agent.commands.mixin_base import reset_session_stats
from agent.services.exceptions import SessionNotFoundError
from agent.services.models import SessionRestoreResult

if TYPE_CHECKING:
    from shared.types import LLMMessage

    from agent.context import AgentContext

logger = logging.getLogger(__name__)


def restore_session(ctx: AgentContext, session_id: int) -> SessionRestoreResult:
    """Restore session: rebuild history, switch session ID, reset stats.

    Raises SessionNotFoundError when the session does not exist or has no messages.
    """
    messages = ctx.session.fetch_messages(session_id)
    if not messages:
        raise SessionNotFoundError(
            f"Session {session_id} not found or has no messages."
        )
    if ctx.conv.system_prompt_content:
        system_msgs: list[LLMMessage] = cast(
            "list[LLMMessage]",
            [{"role": "system", "content": ctx.conv.system_prompt_content}],
        )
        non_system = [m for m in messages if m["role"] != "system"]
        ctx.conv.history = system_msgs + non_system
    else:
        ctx.conv.history = messages
    ctx.session.session_id = session_id
    reset_session_stats(ctx)
    logger.info("Session %s loaded: %s messages", session_id, len(messages))
    return SessionRestoreResult(session_id=session_id, n_messages=len(messages))
