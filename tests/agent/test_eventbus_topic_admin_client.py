"""tests/agent/test_eventbus_topic_admin_client.py
Unit tests for agent/eventbus_topic_admin_client.py — EventBusTopicAdminClient.
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import httpx
import pytest
from agent.eventbus_topic_admin_client import (
    EventBusTopicAdminClient,
    EventBusTopicAdminClientConfig,
)


@pytest.fixture()
def config() -> EventBusTopicAdminClientConfig:
    return EventBusTopicAdminClientConfig(
        admin_url="http://localhost:8091/admin/topics/authorization",
        timeout=1.0,
        admin_token="test-admin-token",
    )


class TestSuccessfulUpdate:
    @pytest.mark.asyncio
    async def test_valid_request_returns_success(
        self, config: EventBusTopicAdminClientConfig
    ) -> None:
        mock_resp = MagicMock()
        mock_resp.raise_for_status.return_value = None

        mock_http = AsyncMock(spec=httpx.AsyncClient)
        mock_http.post = AsyncMock(return_value=mock_resp)

        client = EventBusTopicAdminClient(config, mock_http)
        result = await client.update_topics_authorization(
            consumer_authorization={"c1": ["topicA"]}
        )

        assert result.success is True

    @pytest.mark.asyncio
    async def test_request_sends_bearer_auth_header_and_body(
        self, config: EventBusTopicAdminClientConfig
    ) -> None:
        mock_resp = MagicMock()
        mock_resp.raise_for_status.return_value = None

        mock_http = AsyncMock(spec=httpx.AsyncClient)
        mock_http.post = AsyncMock(return_value=mock_resp)

        client = EventBusTopicAdminClient(config, mock_http)
        await client.update_topics_authorization(
            consumer_authorization={"c1": ["topicA"]},
            topic_authorization={"topicB": ["c2"]},
        )

        args, kwargs = mock_http.post.call_args
        assert args[0] == "http://localhost:8091/admin/topics/authorization"
        assert kwargs["headers"]["Authorization"] == "Bearer test-admin-token"
        assert kwargs["json"] == {
            "consumer_authorization": {"c1": ["topicA"]},
            "topic_authorization": {"topicB": ["c2"]},
        }

    @pytest.mark.asyncio
    async def test_omitted_field_not_sent_in_body(
        self, config: EventBusTopicAdminClientConfig
    ) -> None:
        mock_resp = MagicMock()
        mock_resp.raise_for_status.return_value = None

        mock_http = AsyncMock(spec=httpx.AsyncClient)
        mock_http.post = AsyncMock(return_value=mock_resp)

        client = EventBusTopicAdminClient(config, mock_http)
        await client.update_topics_authorization(
            consumer_authorization={"c1": ["topicA"]}
        )

        _, kwargs = mock_http.post.call_args
        assert "topic_authorization" not in kwargs["json"]


class TestUpdateFailures:
    @pytest.mark.asyncio
    async def test_http_status_error_returns_http_error(
        self, config: EventBusTopicAdminClientConfig
    ) -> None:
        mock_resp = MagicMock()
        mock_resp.status_code = 422
        mock_resp.text = "invalid body"
        mock_resp.raise_for_status.side_effect = httpx.HTTPStatusError(
            "422", request=MagicMock(), response=mock_resp
        )

        mock_http = AsyncMock(spec=httpx.AsyncClient)
        mock_http.post = AsyncMock(return_value=mock_resp)

        client = EventBusTopicAdminClient(config, mock_http)
        result = await client.update_topics_authorization(
            consumer_authorization={"c1": ["topicA"]}
        )

        assert result.success is False
        assert result.error_kind == "http_error"

    @pytest.mark.asyncio
    async def test_request_error_returns_request_error(
        self, config: EventBusTopicAdminClientConfig
    ) -> None:
        mock_http = AsyncMock(spec=httpx.AsyncClient)
        mock_http.post = AsyncMock(side_effect=httpx.ConnectError("connection refused"))

        client = EventBusTopicAdminClient(config, mock_http)
        result = await client.update_topics_authorization(
            consumer_authorization={"c1": ["topicA"]}
        )

        assert result.success is False
        assert result.error_kind == "request_error"

    @pytest.mark.asyncio
    async def test_update_failure_does_not_raise(
        self, config: EventBusTopicAdminClientConfig
    ) -> None:
        mock_http = AsyncMock(spec=httpx.AsyncClient)
        mock_http.post = AsyncMock(side_effect=httpx.ConnectTimeout("timeout"))

        client = EventBusTopicAdminClient(config, mock_http)
        result = await client.update_topics_authorization(
            consumer_authorization={"c1": ["topicA"]}
        )
        assert result.success is False
