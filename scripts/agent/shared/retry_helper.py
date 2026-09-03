"""scripts/agent/shared/retry_helper.py

Shared retry-once-with-delay helper for startup.py refactor (REQ-002).

Consolidates duplicated retry logic from _start_servers/_start_http_subprocess_once
and _verify_mcp_health into a single parameterized function.
"""

from __future__ import annotations

import asyncio
from collections.abc import Awaitable, Callable
from typing import TYPE_CHECKING, TypeVar

if TYPE_CHECKING:
    from agent.cli_view import CLIView

T = TypeVar("T")


async def retry_once_with_delay[T](
    fn: Callable[..., Awaitable[T]],
    delay: float,
    shutdown_event: asyncio.Event | None,
    interrupt_msg: str,
    *,
    production_mode: bool,
    fatal_prefix: str,
    non_fatal_prefix: str,
    view: CLIView | None = None,
) -> T:
    """Execute *fn* once; if it raises, wait *delay* seconds and retry once.

    On second failure:
    - production_mode=True: raise RuntimeError with *fatal_prefix*.
    - production_mode=False: log warning and display via *view* with *non_fatal_prefix*.

    Always races against *shutdown_event*; raises StartupInterrupted if shutdown
    fires during the retry delay.
    """
    from shared.logger import Logger

    logger = Logger(__name__, "/opt/llm/logs/agent.log")

    try:
        return await fn()
    except Exception:  # noqa: BLE001 — first attempt failure triggers retry logic below
        pass

    # Interruptible sleep before retry
    if shutdown_event is not None and shutdown_event.is_set():
        from agent.startup import StartupInterrupted

        raise StartupInterrupted(interrupt_msg) from None

    if await _interruptible_sleep(shutdown_event, delay):
        from agent.startup import StartupInterrupted

        raise StartupInterrupted(interrupt_msg) from None

    try:
        return await fn()
    except Exception as retry_err:
        if production_mode:
            msg = f"{fatal_prefix} {_mask_secrets(str(retry_err))}"
            masked_msg = _mask_secrets(msg)
            logger.error(masked_msg)
            raise RuntimeError(masked_msg) from retry_err
        logger.warning("%s %s", non_fatal_prefix, _mask_secrets(str(retry_err)))
        if view is not None:
            view.write_warning(f"{non_fatal_prefix} {_mask_secrets(str(retry_err))}")
        raise  # Re-raise so caller can decide what to do


async def _interruptible_sleep(
    shutdown_event: asyncio.Event | None, delay: float
) -> bool:
    """Sleep for `delay` seconds, racing against *shutdown_event*.

    Returns True iff the shutdown event fired before `delay` elapsed.
    """
    if shutdown_event is None:
        await asyncio.sleep(delay)
        return False
    sleep_task = asyncio.ensure_future(asyncio.sleep(delay))
    shutdown_task = asyncio.ensure_future(shutdown_event.wait())
    done, pending = await asyncio.wait(
        {sleep_task, shutdown_task}, return_when=asyncio.FIRST_COMPLETED
    )
    for task in pending:
        task.cancel()
    return shutdown_task in done


def _mask_secrets(text: str) -> str:
    """Mask secrets in error messages."""
    from agent.secrets_masker import _mask_secrets as _ms

    return _ms(text)
