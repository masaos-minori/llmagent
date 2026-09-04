"""scripts/agent/shared/retry_helper.py

Shared retry-once-with-delay helper for startup.py refactor (REQ-002).

Consolidates duplicated retry logic from _start_servers/_start_http_subprocess_once
and _verify_mcp_health into a single parameterized function.
"""

from __future__ import annotations

import asyncio
from collections.abc import Awaitable, Callable
from typing import TypeVar

T = TypeVar("T")


async def retry_once_with_delay[T](
    fn: Callable[..., Awaitable[T]],
    delay: float,
    shutdown_event: asyncio.Event | None,
    interrupt_msg: str,
    *,
    fatal_prefix: str,
) -> T:
    """Execute *fn* once; if it raises, wait *delay* seconds and retry once.

    On second failure, raises RuntimeError with *fatal_prefix*.

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
        msg = f"{fatal_prefix} {_mask_secrets(str(retry_err))}"
        masked_msg = _mask_secrets(msg)
        logger.error(masked_msg)
        raise RuntimeError(masked_msg) from retry_err


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
