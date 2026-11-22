"""scripts/agent/stdin_reader.py — Blocking stdin reads on a daemon thread so an abandoned read never delays process exit.

Exposes one process-shared reader through get_stdin_reader() so every call site
shares the cancelled-request line hand-off.
"""

from __future__ import annotations

import asyncio
import builtins
import threading
from collections.abc import Callable
from typing import NamedTuple


class _Waiter(NamedTuple):
    """The one pending read request: where to deliver the line and which prompt it asked for."""

    loop: asyncio.AbstractEventLoop
    future: asyncio.Future[str]
    prompt: str


def _deliver(
    future: asyncio.Future[str], line: str | None, exc: BaseException | None
) -> None:
    """Complete a request's future in its loop thread; a cancelled request is skipped."""
    if future.done():
        return
    if exc is not None:
        future.set_exception(exc)
    else:
        future.set_result(line if line is not None else "")


class StdinReader:
    """Owns one daemon thread that performs one blocking read per request.

    A default-executor or pool worker blocked in input() is joined at interpreter exit,
    so a cancelled read would hold the process open until a key is pressed. A plain
    daemon thread is not joined. The worker never reads ahead: it performs one read per
    request and keeps at most one read outstanding. A line is delivered only to the
    request that started its read: a line that arrives after that request was cancelled or
    timed out is discarded, and a later request waits for a fresh read.
    """

    def __init__(
        self, prompt: str = "", read_fn: Callable[[str], str] | None = None
    ) -> None:
        """Store the default prompt; the worker starts lazily on the first read."""
        self._prompt = prompt
        self._read_fn = read_fn
        self._lock = threading.Lock()
        self._wake = threading.Event()
        self._thread: threading.Thread | None = None
        self._waiter: _Waiter | None = None
        self._reading = False
        self._reading_waiter: _Waiter | None = None

    @property
    def orphaned_read(self) -> bool:
        """True while a blocked read belongs to a request that already ended."""
        with self._lock:
            started_for = self._reading_waiter
            return (
                self._reading
                and started_for is not None
                and (started_for is not self._waiter or started_for.future.done())
            )

    async def read(self, prompt: str | None = None) -> str:
        """Read one line; raises RuntimeError when a request is already pending."""
        loop = asyncio.get_running_loop()
        waiter = _Waiter(
            loop, loop.create_future(), self._prompt if prompt is None else prompt
        )
        with self._lock:
            current = self._waiter
            if (
                current is not None
                and not current.future.done()
                and not current.loop.is_closed()
            ):
                raise RuntimeError("a stdin read is already pending")
            self._waiter = waiter
            wake = not self._reading
            if self._thread is None:
                self._thread = threading.Thread(
                    target=self._run, name="stdin-reader", daemon=True
                )
                self._thread.start()
        if wake:
            self._wake.set()
        try:
            return await waiter.future
        finally:
            with self._lock:
                if self._waiter is waiter:
                    self._waiter = None

    def _run(self) -> None:
        """Worker loop: wait for a request, perform one read, deliver the outcome.

        The waiter is captured before the blocking read starts and is the only
        delivery target, so a line never reaches a request that began later.
        """
        while True:
            self._wake.wait()
            self._wake.clear()
            with self._lock:
                waiter = self._waiter
                if waiter is None or self._reading or waiter.future.done():
                    continue
                self._reading = True
                self._reading_waiter = waiter
            line: str | None = None
            exc: BaseException | None = None
            try:
                line = (self._read_fn or builtins.input)(waiter.prompt)
            except (Exception, KeyboardInterrupt, SystemExit) as caught:  # noqa: BLE001 — every outcome of the read, including interpreter-level ones, must reach the awaiting caller
                exc = caught
            with self._lock:
                self._reading = False
                self._reading_waiter = None
                pending = self._waiter
                restart = (
                    pending is not None
                    and pending is not waiter
                    and not pending.future.done()
                )
            try:
                waiter.loop.call_soon_threadsafe(_deliver, waiter.future, line, exc)
            except RuntimeError:
                pass  # the loop is closed: nobody is waiting for this line
            if restart:
                self._wake.set()


_shared_reader: StdinReader | None = None


def get_stdin_reader() -> StdinReader:
    """Return the process-shared reader, creating it on first use."""
    global _shared_reader
    if _shared_reader is None:
        _shared_reader = StdinReader()
    return _shared_reader


def reset_stdin_reader() -> None:
    """Drop the shared instance so the next get_stdin_reader() builds a fresh reader."""
    global _shared_reader
    _shared_reader = None
