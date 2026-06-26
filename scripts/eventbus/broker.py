from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass
from typing import Any

logger = logging.getLogger(__name__)

_SLOW_CONSUMER_THRESHOLD = 100


@dataclass
class _Subscriber:
    queue: asyncio.Queue[dict[str, Any] | None]
    topics: list[str]  # empty = all topics


class EventBroker:
    def __init__(self) -> None:
        self._subscribers: list[_Subscriber] = []

    def subscribe(self, topics: list[str]) -> _Subscriber:
        """Register a new subscriber. topics=[] means all topics."""
        sub = _Subscriber(queue=asyncio.Queue(maxsize=1000), topics=list(topics))
        self._subscribers.append(sub)
        return sub

    def unsubscribe(self, sub: _Subscriber) -> None:
        """Remove subscriber from the registry. Idempotent."""
        try:
            self._subscribers.remove(sub)
        except ValueError:
            pass

    def publish(self, event: dict[str, Any]) -> int:
        """Fan out event to matching subscribers. Returns delivery count."""
        delivered = 0
        event_topic: str = event.get("topic", "")
        for sub in list(self._subscribers):  # snapshot to avoid mutation during iteration
            if sub.topics and event_topic not in sub.topics:
                continue
            try:
                sub.queue.put_nowait(event)
                delivered += 1
            except asyncio.QueueFull:
                logger.warning(
                    "broker: queue full sub=%d dropping seq=%s",
                    id(sub),
                    event.get("seq"),
                )
        return delivered

    def shutdown(self) -> None:
        """Send None sentinel to all subscribers to unblock their queue.get() calls."""
        for sub in list(self._subscribers):
            try:
                sub.queue.put_nowait(None)
            except asyncio.QueueFull:
                pass

    def subscriber_count(self) -> int:
        return len(self._subscribers)

    def max_queue_depth(self) -> int:
        subs = list(self._subscribers)
        return max((sub.queue.qsize() for sub in subs), default=0)

    def slow_consumer_count(self) -> int:
        return sum(
            1 for sub in list(self._subscribers)
            if sub.queue.qsize() >= _SLOW_CONSUMER_THRESHOLD
        )
