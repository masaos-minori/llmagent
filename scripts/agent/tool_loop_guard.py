"""agent/tool_loop_guard.py
Tool-loop guard: duplicate call detection, cycle detection, retry suppression,
and consecutive error limiting.

Extracted from orchestrator.py. ToolLoopGuard encapsulates per-turn mutable
state and the guard rules applied each time the LLM returns tool_calls.
"""

from __future__ import annotations

import hashlib
import logging
from dataclasses import dataclass, field
from typing import TYPE_CHECKING

import orjson
from shared.tool_executor import tool_call_key
from shared.types import LLMMessage

if TYPE_CHECKING:
    from agent.context import AgentContext

logger = logging.getLogger(__name__)

# Control hints injected into LLM history when a guard fires.
# Using history injection (not metadata) keeps the hints visible to the LLM.
DEDUP_HINT = (
    "[System] The same tool was called with identical arguments multiple times."
    " Stop retrying and provide your best answer with the information already available."
)

CYCLE_HINT = (
    "[System] A cyclic planning pattern was detected: the same set of tool calls"
    " is being requested repeatedly across multiple rounds. Stop and provide your"
    " best answer with the information already available."
)


@dataclass
class TurnLoopState:
    """Mutable per-turn loop state passed through each inner turn."""

    seen_calls: dict[str, int] = field(default_factory=dict)
    failed_calls: set[str] = field(default_factory=set)
    consecutive_errors: int = 0
    round_fingerprints: list[str] = field(default_factory=list)


class ToolLoopGuard:
    """Guards the tool-call loop against dedup, cycle, retry, and consecutive errors.

    Stateless per-instance; all mutable state lives in TurnLoopState so that
    each call to LLMTurnRunner.run() starts from a clean slate.
    """

    def __init__(self, ctx: AgentContext) -> None:
        self._ctx = ctx

    # ── Guard checks ──────────────────────────────────────────────────────────

    def check_cycle(
        self,
        round_fingerprints: list[str],
        message: LLMMessage,
    ) -> str | None:
        """Detect repeating round-level tool fingerprints; return exit msg when hit."""
        ctx = self._ctx
        if ctx.cfg.tool.tool_cycle_detect_window <= 0:
            return None
        round_key = hashlib.md5(
            "|".join(
                sorted(
                    f"{tc.get('function', {}).get('name', '')}:"
                    f"{tc.get('function', {}).get('arguments', '{}')}"
                    for tc in message["tool_calls"]
                ),
            ).encode(),
            usedforsecurity=False,
        ).hexdigest()
        if round_fingerprints.count(round_key) >= ctx.cfg.tool.tool_cycle_detect_window:
            logger.warning(
                f"Cyclic planning detected: round fingerprint {round_key!r}"
                f" repeated {round_fingerprints.count(round_key)} times",
            )
            ctx.history.append({"role": "user", "content": CYCLE_HINT})
            return "Cyclic tool call pattern detected."
        round_fingerprints.append(round_key)
        return None

    def check_dedup(
        self,
        seen_calls: dict[str, int],
        message: LLMMessage,
    ) -> str | None:
        """Block re-execution of identical (tool, args); return exit msg when hit."""
        ctx = self._ctx
        for tc in message["tool_calls"]:
            func = tc.get("function", {})
            key = hashlib.md5(
                f"{func.get('name', '')}:{func.get('arguments', '{}')}".encode(),
                usedforsecurity=False,
            ).hexdigest()
            seen_calls[key] = seen_calls.get(key, 0) + 1
            if seen_calls[key] >= ctx.cfg.tool.tool_dedup_max_repeats:
                name = func.get("name", "<unknown>")
                logger.warning(f"Duplicate tool call blocked: {name!r}")
                ctx.history.append({"role": "user", "content": DEDUP_HINT})
                return "Repeated tool call detected."
        return None

    def check_retry(
        self,
        failed_calls: set[str],
        message: LLMMessage,
    ) -> str | None:
        """Block retry of already-failed (tool, args); return exit msg when hit."""
        ctx = self._ctx
        if ctx.cfg.tool.tool_error_retry_max <= 0:
            return None
        for tc in message["tool_calls"]:
            func = tc.get("function", {})
            try:
                tc_args = orjson.loads(func.get("arguments", "{}"))
            except (orjson.JSONDecodeError, TypeError):
                tc_args = {}
            if tool_call_key(func.get("name", ""), tc_args) in failed_calls:
                name = func.get("name", "<unknown>")
                logger.warning(f"Retry of failed tool call blocked: {name!r}")
                ctx.history.append({"role": "user", "content": DEDUP_HINT})
                return "Repeated failed tool call detected."
        return None

    def check_all(
        self,
        seen_calls: dict[str, int],
        round_fingerprints: list[str],
        failed_calls: set[str],
        message: LLMMessage,
    ) -> str | None:
        """Run cycle, dedup, and retry guards in order; return first hit or None."""
        if msg := self.check_cycle(round_fingerprints, message):
            return msg
        if msg := self.check_dedup(seen_calls, message):
            return msg
        return self.check_retry(failed_calls, message)

    # ── Consecutive-error counter ─────────────────────────────────────────────

    @staticmethod
    def update_errors(
        consecutive_errors: int,
        n_errors: int,
        n_tool_calls: int,
    ) -> int:
        """Increment counter when all calls failed; reset to 0 when any succeeded."""
        return consecutive_errors + 1 if n_errors == n_tool_calls else 0

    def check_error_limit(self, consecutive_errors: int) -> str | None:
        """Return exit message when consecutive all-error turns exceed configured max."""
        ctx = self._ctx
        if (
            ctx.cfg.tool.tool_error_max_consecutive <= 0
            or consecutive_errors < ctx.cfg.tool.tool_error_max_consecutive
        ):
            return None
        logger.warning(
            f"Aborting turn: {consecutive_errors} consecutive all-error"
            f" tool turns (max={ctx.cfg.tool.tool_error_max_consecutive})",
        )
        return "Too many consecutive tool errors."
