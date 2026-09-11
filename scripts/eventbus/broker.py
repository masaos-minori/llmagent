"""scripts/eventbus/broker.py"""

from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass, field
from typing import Any

from prometheus_client import Counter

from eventbus.config import EventBusConfig

logger = logging.getLogger(__name__)

# -- Metrics ------------------------------------------------------------------

_slow_consumer_total = Counter(
    "eventbus_slow_consumer_total",
    "Number of slow consumer events detected",
)


@dataclass
class _Subscriber:
    """Internal subscriber record holding its delivery queue and topic filter."""

    queue: asyncio.Queue[dict[str, Any] | None]
    topics: list[str]  # empty = all topics
    consumer_id: str = ""
    disconnect: asyncio.Event = field(default_factory=asyncio.Event)


class ConsumerAlreadyConnectedError(Exception):
    """Raised when a second connection attempts the same non-empty consumer_id."""


class EventBroker:
    """In-memory pub/sub broker with per-subscriber queues and topic filtering."""

    def __init__(self, config: EventBusConfig) -> None:
        """Initialize with empty subscriber list.

        Args:
            config: EventBusConfig containing operational thresholds.
        """
        self._subscribers: list[_Subscriber] = []
        self._consumer_subs: dict[str, _Subscriber] = {}
        self._overflow_disconnect_count = 0
        self._duplicate_rejection_count = 0
        self._slow_consumer_threshold = config.slow_consumer_threshold
        self._subscriber_queue_maxsize = config.subscriber_queue_maxsize
        self._backlog_health_threshold = config.backlog_health_threshold

    def subscribe(self, topics: list[str], consumer_id: str = "") -> _Subscriber:
        """Register a new subscriber. topics=[] means all topics."""
        if consumer_id and consumer_id in self._consumer_subs:
            self._duplicate_rejection_count += 1
            raise ConsumerAlreadyConnectedError(consumer_id)
        sub = _Subscriber(
            queue=asyncio.Queue(maxsize=self._subscriber_queue_maxsize),
            topics=list(topics),
            consumer_id=consumer_id,
        )
        self._subscribers.append(sub)
        if consumer_id:
            self._consumer_subs[consumer_id] = sub
        return sub

    def unsubscribe(self, sub: _Subscriber) -> None:
        """Remove subscriber from the registry. Idempotent."""
        try:
            self._subscribers.remove(sub)
        except ValueError:
            pass
        if sub.consumer_id:
            self._consumer_subs.pop(sub.consumer_id, None)

    def publish(self, event: dict[str, Any]) -> int:
        """Fan out event to matching subscribers. Returns delivery count."""
        delivered = 0
        event_topic: str = event.get("topic", "")
        for sub in list(
            self._subscribers
        ):  # snapshot to avoid mutation during iteration
            if sub.topics and event_topic not in sub.topics:
                continue
            try:
                sub.queue.put_nowait(event)
                delivered += 1
            except asyncio.QueueFull:
                logger.warning(
                    "broker: queue full sub=%d disconnecting seq=%s",
                    id(sub),
                    event.get("seq"),
                )
                sub.disconnect.set()
                self.unsubscribe(sub)
                self._overflow_disconnect_count += 1
        return delivered

    def shutdown(self) -> None:
        """Send None sentinel to all subscribers to unblock their queue.get() calls."""
        for sub in list(self._subscribers):
            try:
                sub.queue.put_nowait(None)
            except asyncio.QueueFull:
                pass

    def subscriber_count(self) -> int:
        """Return the number of active subscribers."""
        return len(self._subscribers)

    def max_queue_depth(self) -> int:
        """Return the maximum queue depth across all subscribers."""
        subs = list(self._subscribers)
        return max((sub.queue.qsize() for sub in subs), default=0)

    def slow_consumer_count(self) -> int:
        """Count subscribers whose queue depth exceeds the slow consumer threshold."""
        count = sum(
            1
            for sub in list(self._subscribers)
            if sub.queue.qsize() >= self._slow_consumer_threshold
        )
        if count > 0:
            _slow_consumer_total.inc(count)
        return count

    def overflow_disconnect_count(self) -> int:
        """Return the number of disconnects caused by queue overflow."""
        return self._overflow_disconnect_count

    def duplicate_rejection_count(self) -> int:
        """Return the number of duplicate consumer_id rejections."""
        return self._duplicate_rejection_count

    @property
    def backlog_health_threshold(self) -> int:
        """Return the configured backlog health threshold."""
        return self._backlog_health_threshold
