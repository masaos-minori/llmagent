"""scripts/agent/eventbus_topic_admin_client.py

EventBusTopicAdminClient — HTTP client for Event Bus's admin
/admin/topics/authorization endpoint.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from enum import StrEnum

import httpx

logger = logging.getLogger(__name__)


class EventBusTopicAdminErrorKind(StrEnum):
    """Enumeration of admin-update failure reasons."""

    HTTP_ERROR = "http_error"
    REQUEST_ERROR = "request_error"
    UNKNOWN_ERROR = "unknown_error"


@dataclass(frozen=True)
class EventBusTopicAdminResult:
    """Result of an authorization-update attempt."""

    success: bool
    error_kind: EventBusTopicAdminErrorKind | None = None


@dataclass
class EventBusTopicAdminClientConfig:
    """Configuration for the Event Bus admin topics-authorization client."""

    admin_url: str = ""
    timeout: float = 5.0
    admin_token: str = ""


class EventBusTopicAdminClient:
    """Async HTTP client for Event Bus's admin topics-authorization endpoint."""

    def __init__(
        self,
        config: EventBusTopicAdminClientConfig,
        http: httpx.AsyncClient,
    ) -> None:
        """Store config and the shared HTTP client used for admin requests."""
        self._config = config
        self._http = http

    async def update_topics_authorization(
        self,
        consumer_authorization: dict[str, list[str]] | None = None,
        topic_authorization: dict[str, list[str]] | None = None,
    ) -> EventBusTopicAdminResult:
        """Update consumer_authorization/topic_authorization on Event Bus.

        Both parameters are optional — omit one to leave it unchanged.
        """
        body: dict[str, object] = {}
        if consumer_authorization is not None:
            body["consumer_authorization"] = consumer_authorization
        if topic_authorization is not None:
            body["topic_authorization"] = topic_authorization

        headers = {"Authorization": f"Bearer {self._config.admin_token}"}
        try:
            resp = await self._http.post(
                self._config.admin_url,
                json=body,
                headers=headers,
                timeout=self._config.timeout,
            )
            resp.raise_for_status()
            return EventBusTopicAdminResult(success=True)
        except httpx.HTTPStatusError as e:
            logger.warning(
                "EventBusTopicAdminClient.update_topics_authorization HTTP error: status=%d body=%.200s",
                e.response.status_code,
                e.response.text,
            )
            return EventBusTopicAdminResult(
                success=False, error_kind=EventBusTopicAdminErrorKind.HTTP_ERROR
            )
        except httpx.RequestError as e:
            logger.warning(
                "EventBusTopicAdminClient.update_topics_authorization request error: %s",
                e,
            )
            return EventBusTopicAdminResult(
                success=False, error_kind=EventBusTopicAdminErrorKind.REQUEST_ERROR
            )
        except Exception as e:  # noqa: BLE001 — classification fallback for any error not covered by the specific httpx branches above
            logger.warning(
                "EventBusTopicAdminClient.update_topics_authorization unexpected error: %s",
                e,
            )
            return EventBusTopicAdminResult(
                success=False, error_kind=EventBusTopicAdminErrorKind.UNKNOWN_ERROR
            )
