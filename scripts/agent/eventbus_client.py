"""scripts/agent/eventbus_client.py

EventBusClient — HTTP client for publishing events to Event Bus's /publish endpoint.
"""

from __future__ import annotations

import logging
import uuid
from dataclasses import dataclass
from datetime import UTC, datetime
from enum import StrEnum
from typing import Any

import httpx

logger = logging.getLogger(__name__)


class EventBusPublishErrorKind(StrEnum):
    """Enumeration of publish failure reasons."""

    HTTP_ERROR = "http_error"
    REQUEST_ERROR = "request_error"
    UNKNOWN_ERROR = "unknown_error"


@dataclass(frozen=True)
class EventBusPublishResult:
    """Result of a publish attempt."""

    success: bool
    seq: int | None = None
    error_kind: EventBusPublishErrorKind | None = None


@dataclass
class EventBusClientConfig:
    """Configuration for the Event Bus publish client connection."""

    publish_url: str = ""
    timeout: float = 5.0
    publisher_token: str = ""


class EventBusClient:
    """Async HTTP client for publishing events to Event Bus."""

    def __init__(
        self,
        config: EventBusClientConfig,
        http: httpx.AsyncClient,
    ) -> None:
        """Store config and the shared HTTP client used for publish requests."""
        self._config = config
        self._http = http

    async def publish(
        self, topic: str, payload: dict[str, Any], producer: str
    ) -> EventBusPublishResult:
        """Publish one event; return EventBusPublishResult indicating success or failure.

        `event_id` and `published_at` are generated here (UUID v4 and the current
        UTC timestamp respectively) so every caller satisfies Event Bus's envelope
        schema (`schemas/event_envelope.json`) without repeating that logic.
        """
        body = {
            "event_id": str(uuid.uuid4()),
            "topic": topic,
            "payload": payload,
            "producer": producer,
            "published_at": datetime.now(UTC).isoformat(),
        }
        headers = {"Authorization": f"Bearer {self._config.publisher_token}"}
        try:
            resp = await self._http.post(
                self._config.publish_url,
                json=body,
                headers=headers,
                timeout=self._config.timeout,
            )
            resp.raise_for_status()
            data = resp.json()
            seq = data.get("seq") if isinstance(data, dict) else None
            return EventBusPublishResult(success=True, seq=seq)
        except httpx.HTTPStatusError as e:
            logger.warning(
                "EventBusClient.publish HTTP error: status=%d body=%.200s",
                e.response.status_code,
                e.response.text,
            )
            return EventBusPublishResult(
                success=False, error_kind=EventBusPublishErrorKind.HTTP_ERROR
            )
        except httpx.RequestError as e:
            logger.warning("EventBusClient.publish request error: %s", e)
            return EventBusPublishResult(
                success=False, error_kind=EventBusPublishErrorKind.REQUEST_ERROR
            )
        except Exception as e:  # noqa: BLE001 — classification fallback for any error not covered by the specific httpx branches above
            logger.warning("EventBusClient.publish unexpected error: %s", e)
            return EventBusPublishResult(
                success=False, error_kind=EventBusPublishErrorKind.UNKNOWN_ERROR
            )
