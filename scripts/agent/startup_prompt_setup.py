"""scripts/agent/startup_prompt_setup.py

Prompt/memory setup: inject semantic memories into the initial system prompt.
"""

from __future__ import annotations

import sqlite3
from collections.abc import Sequence
from typing import TYPE_CHECKING, Any

from agent.memory.snippet_filter import build_memory_block
from agent.output_tags import OutputTag
from agent.prompt_source import load_prompt_source

if TYPE_CHECKING:
    from agent.cli_view import CLIView

# Exception types that signal a defect in the memory service (or in this module)
# rather than a runtime condition; ValueError is left out because it can come from data.
_PROGRAMMING_ERROR_TYPES: tuple[type[Exception], ...] = (
    AttributeError,
    NameError,
    TypeError,
    LookupError,
    AssertionError,
)


class PromptSetup:
    """Owns system prompt and memory setup."""

    def __init__(self, ctx: Any, view: CLIView) -> None:
        self._ctx = ctx
        self._view = view

    def _classify_memory_failure(self, exc: Exception) -> str:
        """Classify memory injection failure by root cause category.

        Returns one of: "NETWORK_TRANSIENT", "DATABASE_OR_IO", "PROGRAMMING_ERROR",
        "UNKNOWN".
        """
        if isinstance(exc, (ConnectionError, TimeoutError)):
            return "NETWORK_TRANSIENT"
        if isinstance(exc, (sqlite3.Error, OSError)):
            return "DATABASE_OR_IO"
        if isinstance(exc, _PROGRAMMING_ERROR_TYPES):
            return "PROGRAMMING_ERROR"
        return "UNKNOWN"

    @staticmethod
    def _append_memory_block(
        initial_prompt: str, memory_snippets: Sequence[Any]
    ) -> str:
        """Append the framed memory block to *initial_prompt*; unchanged if empty."""
        block = build_memory_block([snippet.text for snippet in memory_snippets])
        if block:
            return initial_prompt + "\n\n" + block
        return initial_prompt

    async def setup_prompt(self) -> None:
        """Inject semantic memories into the initial system prompt."""
        from shared.logger import Logger

        logger = Logger(__name__, "/opt/llm/logs/agent.log")

        ctx = self._ctx
        # Read boundary of the single source (agent.prompt_source): a missing
        # source or missing default entry raises here, at the read, with no
        # code-level fallback.
        initial_prompt = load_prompt_source().content(ctx.conv.system_prompt_name)
        if ctx.services_required.memory is not None:
            try:
                memory_snippets = ctx.services_required.memory.on_session_start(
                    ctx.session.session_id,
                )
                if memory_snippets:
                    max_snippets = ctx.cfg.agent_memory_max_startup_snippets
                    if len(memory_snippets) > max_snippets:
                        logger.warning(
                            "Startup: truncating %d memory snippets to %d for %r",
                            len(memory_snippets),
                            max_snippets,
                            ctx.session.session_id,
                        )
                        memory_snippets = memory_snippets[:max_snippets]
                    initial_prompt = self._append_memory_block(
                        initial_prompt, memory_snippets
                    )
            except Exception as exc:  # noqa: BLE001 — the catch stays so startup completes without memory; programming errors are classified separately so they are not mistaken for benign conditions
                ctx.conv.memory_disabled = True
                category = self._classify_memory_failure(exc)
                if category == "DATABASE_OR_IO":
                    logger.error(
                        "Memory injection failed during startup (DB/IO error): %s; continuing without memory",
                        exc,
                    )
                elif category == "NETWORK_TRANSIENT":
                    logger.warning(
                        "Memory injection failed during startup (network transient): %s; continuing without memory",
                        exc,
                    )
                elif category == "PROGRAMMING_ERROR":
                    logger.error(
                        "Memory injection failed during startup (internal error): %s; continuing without memory",
                        exc,
                        exc_info=True,
                    )
                else:
                    logger.info(
                        "Memory injection failed during startup (unknown error): %s; continuing without memory",
                        exc,
                    )
                if category == "PROGRAMMING_ERROR":
                    warning = (
                        f"{OutputTag.NON_FATAL} Memory injection failed: internal error "
                        f"({type(exc).__name__}): {exc}; memory is disabled for this "
                        "session. This indicates a defect; see agent.log"
                    )
                else:
                    warning = f"{OutputTag.NON_FATAL} Memory injection failed: {exc}"
                self._view.write_warning(warning)
        ctx.conv.system_prompt_content = initial_prompt
        await ctx.conv.replace_history([{"role": "system", "content": initial_prompt}])
