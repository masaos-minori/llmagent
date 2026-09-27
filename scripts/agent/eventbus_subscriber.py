"""scripts/agent/eventbus_subscriber.py

EventBusSubscriber — SSE client for Event Bus's /subscribe endpoint, with
automatic reconnection using a fresh consumer_id per attempt.
"""

from __future__ import annotations

import asyncio
import logging
import uuid
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
        """Store config and the shared HTTP client used for the SSE stream."""
        self._config = config
        self._http = http

    async def subscribe(self) -> AsyncGenerator[EventBusEvent]:
        """Yield events from Event Bus's SSE stream.

        Reconnects with a fresh `consumer_id` on disconnection (per
        `EventBroker.subscribe()`'s one-connection-per-non-empty-consumer_id
        constraint — a fresh id never collides). Raises EventBusStreamError
        after `max_reconnect_attempts` consecutive failures.
        """
        attempt = 0
        while True:
            consumer_id = uuid.uuid4().hex
            try:
                async for event in self._stream_once(consumer_id):
                    attempt = 0
                    yield event
                # A clean stream end (server closed normally) is treated the
                # same as a disconnection: reconnect with a fresh consumer_id.
            except (httpx.HTTPError, OSError) as e:
                attempt += 1
                logger.warning(
                    "EventBusSubscriber stream disconnected (attempt %d/%d): %s",
                    attempt,
                    self._config.max_reconnect_attempts,
                    e,
                )
                if attempt >= self._config.max_reconnect_attempts:
                    raise EventBusStreamError(
                        f"subscribe stream failed after {attempt} attempts"
                    ) from e
                await asyncio.sleep(self._config.reconnect_delay_sec)
                continue

    async def _stream_once(self, consumer_id: str) -> AsyncGenerator[EventBusEvent]:
        """Open one SSE connection and yield events until it disconnects."""
        headers = {"Authorization": f"Bearer {self._config.consumer_token}"}
        params: dict[str, Any] = {"consumer_id": consumer_id}
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
