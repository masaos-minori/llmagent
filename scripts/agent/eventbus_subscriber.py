"""scripts/agent/eventbus_subscriber.py

EventBusSubscriber — SSE client for Event Bus's /subscribe endpoint, with
automatic reconnection that resumes from the last processed seq using a
stable configured consumer_id.
"""

from __future__ import annotations

import asyncio
import logging
from collections.abc import AsyncGenerator
from dataclasses import dataclass
from typing import Any

import httpx
import orjson

logger = logging.getLogger(__name__)


class EventBusStreamError(Exception):
    """Raised when the subscribe stream cannot be established or maintained
    after exhausting reconnection attempts.
    """


@dataclass
class EventBusSubscriberConfig:
    """Configuration for the Event Bus SSE subscribe client connection."""

    subscribe_url: str = ""
    timeout: float = 30.0
    consumer_token: str = ""
    consumer_id: str = ""
    topics: list[str] | None = None
    max_reconnect_attempts: int = 5
    reconnect_delay_sec: float = 1.0


@dataclass(frozen=True)
class EventBusEvent:
    """One event received from the SSE stream."""

    seq: int
    data: dict[str, Any]


def _parse_sse_lines(raw_id: str | None, raw_data: str | None) -> EventBusEvent | None:
    """Parse one SSE frame's `id:`/`data:` lines into an EventBusEvent.

    Returns None for a heartbeat frame (no `id:`/`data:` pair) rather than
    raising, since a heartbeat is expected stream traffic, not malformed input.
    """
    if raw_id is None or raw_data is None:
        return None
    return EventBusEvent(seq=int(raw_id), data=orjson.loads(raw_data))


class EventBusSubscriber:
    """Async SSE client for Event Bus's /subscribe endpoint."""

    def __init__(
        self,
        config: EventBusSubscriberConfig,
        http: httpx.AsyncClient,
    ) -> None:
        """Store config and the shared HTTP client used for the SSE stream.

        Raises ValueError when `config.consumer_id` is empty: both `since_seq`
        resume and the consumer grant model require a stable, known id.
        """
        if not config.consumer_id:
            raise ValueError("EventBusSubscriberConfig.consumer_id must be non-empty")
        self._config = config
        self._http = http

    async def subscribe(self) -> AsyncGenerator[EventBusEvent]:
        """Yield events from Event Bus's SSE stream.

        Reconnects with the configured stable `consumer_id` and, once at least
        one event has been processed, resumes with a `since_seq` parameter set
        to the last processed event seq (no `Last-Event-ID` is sent). A 409
        conflict is retried inside the same budget with a warning naming the
        `consumer_id`. Raises EventBusStreamError after
        `max_reconnect_attempts` consecutive failures.
        """
        consumer_id = self._config.consumer_id
        last_seq: int | None = None
        attempt = 0

        async def reconnect_or_raise(exc: Exception, conflict: bool) -> None:
            nonlocal attempt
            attempt += 1
            if conflict:
                logger.warning(
                    "EventBusSubscriber consumer_id %s is already connected to "
                    "the Event Bus (attempt %d/%d): %s",
                    consumer_id,
                    attempt,
                    self._config.max_reconnect_attempts,
                    exc,
                )
            else:
                logger.warning(
                    "EventBusSubscriber stream disconnected (attempt %d/%d): %s",
                    attempt,
                    self._config.max_reconnect_attempts,
                    exc,
                )
            if attempt >= self._config.max_reconnect_attempts:
                raise EventBusStreamError(
                    f"subscribe stream failed after {attempt} attempts"
                ) from exc
            await asyncio.sleep(self._config.reconnect_delay_sec)

        while True:
            try:
                async for event in self._stream_once(consumer_id, since_seq=last_seq):
                    attempt = 0
                    yield event
                    last_seq = (
                        event.seq if last_seq is None else max(last_seq, event.seq)
                    )
                # A clean stream end (server closed normally) is treated the
                # same as a disconnection: reconnect, resuming from last_seq.
            except httpx.HTTPStatusError as e:
                await reconnect_or_raise(e, conflict=e.response.status_code == 409)
            except (httpx.HTTPError, OSError) as e:
                await reconnect_or_raise(e, conflict=False)

    async def _stream_once(
        self, consumer_id: str, since_seq: int | None = None
    ) -> AsyncGenerator[EventBusEvent]:
        """Open one SSE connection and yield events until it disconnects.

        `since_seq` is sent only when at least one event was already
        processed; the server treats it as an exclusive replay lower bound.
        """
        headers = {"Authorization": f"Bearer {self._config.consumer_token}"}
        params: dict[str, Any] = {"consumer_id": consumer_id}
        if since_seq is not None:
            params["since_seq"] = since_seq
        if self._config.topics:
            params["topic"] = self._config.topics

        async with self._http.stream(
            "GET",
            self._config.subscribe_url,
            headers=headers,
            params=params,
            timeout=self._config.timeout,
        ) as resp:
            resp.raise_for_status()
            raw_id: str | None = None
            raw_data: str | None = None
            async for line in resp.aiter_lines():
                if line == "":
                    event = _parse_sse_lines(raw_id, raw_data)
                    raw_id = None
                    raw_data = None
                    if event is not None:
                        yield event
                    continue
                if line.startswith("id:"):
                    raw_id = line[len("id:") :]
                elif line.startswith("data:"):
                    raw_data = line[len("data:") :]
                # A line starting with ": " (e.g. ": heartbeat") is a comment
                # frame per the SSE spec — ignored, not an id:/data: pair.
