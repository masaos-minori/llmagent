"""scripts/eventbus/broker.py"""

from __future__ import annotations

import asyncio
import dataclasses
import logging
from dataclasses import dataclass
from typing import Any

logger = logging.getLogger(__name__)

_SLOW_CONSUMER_THRESHOLD = 100


@dataclass(frozen=False)
class _Subscriber:
    """Internal subscriber record holding its delivery queue and topic filter."""

    queue: asyncio.Queue[dict[str, Any] | None]
    topics: list[str]  # empty = all topics
    disconnect_signal: asyncio.Event = dataclasses.field(
        default_factory=asyncio.Event, repr=False, compare=False
    )


class EventBroker:
    """In-memory pub/sub broker with per-subscriber queues and topic filtering."""

    def __init__(self) -> None:
        """Initialize with empty subscriber list."""
        self._subscribers: list[_Subscriber] = []
        self._consumer_registry: dict[str, _Subscriber] = {}
        self._overflow_disconnect_count: int = 0
        self._duplicate_rejection_count: int = 0

    def subscribe(self, topics: list[str], consumer_id: str = "") -> _Subscriber:
        """Register a new subscriber. topics=[] means all topics.

        Args:
            topics: Topic filter; empty list matches all topics.
            consumer_id: Non-empty consumer identifier; if present, checked against
                the consumer-connection registry. A second concurrent connection for
                the same non-empty consumer_id raises ValueError.

        Returns:
            The newly registered _Subscriber.

        Raises:
            ValueError: If consumer_id is non-empty and already present in the
                consumer-connection registry (duplicate connection attempt).
        """
        # Check consumer-connection registry before subscribing
        if consumer_id and consumer_id in self._consumer_registry:
            self._duplicate_rejection_count += 1
            logger.warning(
                "broker: duplicate consumer_id=%s rejected",
                consumer_id,
            )
            raise ValueError(f"duplicate consumer_id: {consumer_id}")

        sub = _Subscriber(queue=asyncio.Queue(maxsize=1000), topics=list(topics))
        self._subscribers.append(sub)

        # Register in consumer-connection registry (only non-empty consumer_id)
        if consumer_id:
            self._consumer_registry[consumer_id] = sub

        return sub

    def unsubscribe(self, sub: _Subscriber) -> None:
        """Remove subscriber from the registry. Idempotent.

        Also clears the consumer-connection registry entry if present.
        """
        # Clear consumer-connection registry entry first
        keys_to_remove = [cid for cid, s in self._consumer_registry.items() if s is sub]
        for cid in keys_to_remove:
            del self._consumer_registry[cid]

        try:
            self._subscribers.remove(sub)
        except ValueError:
            pass

    def publish(self, event: dict[str, Any]) -> int:
        """Fan out event to matching subscribers. Returns delivery count.

        On QueueFull, sets the subscriber's disconnect signal and removes it
        from the active-subscriber list instead of silently dropping the event.
        """
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
                self._overflow_disconnect_count += 1
                logger.warning(
                    "broker: queue full sub=%d disconnecting seq=%s",
                    id(sub),
                    event.get("seq"),
                )
                # Set disconnect signal and remove subscriber immediately
                sub.disconnect_signal.set()
                self._subscribers.remove(sub)
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
        return sum(
            1
            for sub in list(self._subscribers)
            if sub.queue.qsize() >= _SLOW_CONSUMER_THRESHOLD
        )

    def overflow_disconnect_count(self) -> int:
        """Return the number of overflow-triggered disconnects."""
        return self._overflow_disconnect_count

    def duplicate_rejection_count(self) -> int:
        """Return the number of duplicate consumer-connection rejections."""
        return self._duplicate_rejection_count
