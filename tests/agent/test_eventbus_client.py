"""tests/agent/test_eventbus_client.py
Unit tests for agent/eventbus_client.py — EventBusClient publish HTTP client.
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import httpx
import pytest
from agent.eventbus_client import (
    EventBusClient,
    EventBusClientConfig,
)


@pytest.fixture()
def config() -> EventBusClientConfig:
    return EventBusClientConfig(
        publish_url="http://localhost:8091/publish",
        timeout=1.0,
        publisher_token="test-publisher-token",
    )


class TestSuccessfulPublish:
    @pytest.mark.asyncio
    async def test_valid_response_returns_success_with_seq(
        self, config: EventBusClientConfig
    ) -> None:
        mock_resp = MagicMock()
        mock_resp.raise_for_status.return_value = None
        mock_resp.json.return_value = {"event_id": "some-uuid", "seq": 42}

        mock_http = AsyncMock(spec=httpx.AsyncClient)
        mock_http.post = AsyncMock(return_value=mock_resp)

        client = EventBusClient(config, mock_http)
        result = await client.publish(
            topic="agent.test", payload={"key": "value"}, producer="agent"
        )

        assert result.success is True
        assert result.seq == 42

    @pytest.mark.asyncio
    async def test_publish_sends_bearer_auth_header(
        self, config: EventBusClientConfig
    ) -> None:
        mock_resp = MagicMock()
        mock_resp.raise_for_status.return_value = None
        mock_resp.json.return_value = {"event_id": "some-uuid", "seq": 1}

        mock_http = AsyncMock(spec=httpx.AsyncClient)
        mock_http.post = AsyncMock(return_value=mock_resp)

        client = EventBusClient(config, mock_http)
        await client.publish(topic="agent.test", payload={}, producer="agent")

        _, kwargs = mock_http.post.call_args
        assert kwargs["headers"]["Authorization"] == "Bearer test-publisher-token"

    @pytest.mark.asyncio
    async def test_publish_request_body_matches_envelope_schema(
        self, config: EventBusClientConfig
    ) -> None:
        mock_resp = MagicMock()
        mock_resp.raise_for_status.return_value = None
        mock_resp.json.return_value = {"event_id": "some-uuid", "seq": 1}

        mock_http = AsyncMock(spec=httpx.AsyncClient)
        mock_http.post = AsyncMock(return_value=mock_resp)

        client = EventBusClient(config, mock_http)
        await client.publish(
            topic="agent.test", payload={"key": "value"}, producer="agent"
        )

        _, kwargs = mock_http.post.call_args
        body = kwargs["json"]
        assert body["topic"] == "agent.test"
        assert body["payload"] == {"key": "value"}
        assert body["producer"] == "agent"
        assert isinstance(body["event_id"], str) and len(body["event_id"]) == 36
        assert isinstance(body["published_at"], str)


class TestPublishFailures:
    @pytest.mark.asyncio
    async def test_http_status_error_returns_http_error(
        self, config: EventBusClientConfig
    ) -> None:
        mock_resp = MagicMock()
        mock_resp.status_code = 422
        mock_resp.text = "invalid envelope"
        mock_resp.raise_for_status.side_effect = httpx.HTTPStatusError(
            "422", request=MagicMock(), response=mock_resp
        )

        mock_http = AsyncMock(spec=httpx.AsyncClient)
        mock_http.post = AsyncMock(return_value=mock_resp)

        client = EventBusClient(config, mock_http)
        result = await client.publish(topic="agent.test", payload={}, producer="agent")

        assert result.success is False
        assert result.error_kind == "http_error"

    @pytest.mark.asyncio
    async def test_request_error_returns_request_error(
        self, config: EventBusClientConfig
    ) -> None:
        mock_http = AsyncMock(spec=httpx.AsyncClient)
        mock_http.post = AsyncMock(side_effect=httpx.ConnectError("connection refused"))

        client = EventBusClient(config, mock_http)
        result = await client.publish(topic="agent.test", payload={}, producer="agent")

        assert result.success is False
        assert result.error_kind == "request_error"

    @pytest.mark.asyncio
    async def test_unexpected_error_returns_unknown_error(
        self, config: EventBusClientConfig
    ) -> None:
        mock_http = AsyncMock(spec=httpx.AsyncClient)
        mock_http.post = AsyncMock(side_effect=ValueError("unexpected"))

        client = EventBusClient(config, mock_http)
        result = await client.publish(topic="agent.test", payload={}, producer="agent")

        assert result.success is False
        assert result.error_kind == "unknown_error"

    @pytest.mark.asyncio
    async def test_publish_failure_does_not_raise(
        self, config: EventBusClientConfig
    ) -> None:
        mock_http = AsyncMock(spec=httpx.AsyncClient)
        mock_http.post = AsyncMock(side_effect=httpx.ConnectTimeout("timeout"))

        client = EventBusClient(config, mock_http)
        # Must not raise — a publish failure is always a typed result.
        result = await client.publish(topic="agent.test", payload={}, producer="agent")
        assert result.success is False
