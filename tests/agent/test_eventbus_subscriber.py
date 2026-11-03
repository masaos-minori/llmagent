"""tests/agent/test_eventbus_subscriber.py
Unit tests for agent/eventbus_subscriber.py — EventBusSubscriber SSE client.
"""

from __future__ import annotations

from collections.abc import AsyncIterator
from unittest.mock import AsyncMock, MagicMock

import httpx
import pytest
from agent.eventbus_subscriber import (
    EventBusStreamError,
    EventBusSubscriber,
    EventBusSubscriberConfig,
)


@pytest.fixture()
def config() -> EventBusSubscriberConfig:
    return EventBusSubscriberConfig(
        subscribe_url="http://localhost:8091/subscribe",
        timeout=1.0,
        consumer_token="test-consumer-token",
        consumer_id="test-consumer",
        max_reconnect_attempts=2,
        reconnect_delay_sec=0.0,
    )


class _FakeStreamResponse:
    """Minimal stand-in for httpx's streaming response, driven by a fixed
    list of SSE lines (as `aiter_lines()` would yield them)."""

    def __init__(
        self,
        lines: list[str],
        raise_error: Exception | None = None,
        raise_for_status_error: Exception | None = None,
    ) -> None:
        self._lines = lines
        self._raise_error = raise_error
        self._raise_for_status_error = raise_for_status_error

    def raise_for_status(self) -> None:
        if self._raise_for_status_error is not None:
            raise self._raise_for_status_error

    async def aiter_lines(self) -> AsyncIterator[str]:
        for line in self._lines:
            yield line
        if self._raise_error is not None:
            raise self._raise_error


class _FakeStreamContextManager:
    """Stand-in for the object `httpx.AsyncClient.stream()` returns."""

    def __init__(self, response: _FakeStreamResponse) -> None:
        self._response = response

    async def __aenter__(self) -> _FakeStreamResponse:
        return self._response

    async def __aexit__(self, *exc_info: object) -> None:
        return None


def _mock_http_with_lines(
    lines: list[str], raise_error: Exception | None = None
) -> AsyncMock:
    mock_http = AsyncMock(spec=httpx.AsyncClient)
    response = _FakeStreamResponse(lines, raise_error=raise_error)
    mock_http.stream = MagicMock(return_value=_FakeStreamContextManager(response))
    return mock_http


def _http_409_error() -> httpx.HTTPStatusError:
    """Build an httpx.HTTPStatusError whose status_code is 409."""
    request = httpx.Request("GET", "http://localhost:8091/subscribe")
    response = httpx.Response(409, request=request)
    return httpx.HTTPStatusError("409 Conflict", request=request, response=response)


class TestSuccessfulSubscribe:
    @pytest.mark.asyncio
    async def test_yields_parsed_events(self, config: EventBusSubscriberConfig) -> None:
        lines = [
            "id:1",
            'data:{"topic": "agent.test", "payload": {"k": "v"}}',
            "",
        ]
        mock_http = _mock_http_with_lines(lines)
        subscriber = EventBusSubscriber(config, mock_http)

        events = []
        async for event in subscriber.subscribe():
            events.append(event)
            break

        assert len(events) == 1
        assert events[0].seq == 1
        assert events[0].data == {"topic": "agent.test", "payload": {"k": "v"}}

    @pytest.mark.asyncio
    async def test_heartbeat_comment_lines_are_ignored(
        self, config: EventBusSubscriberConfig
    ) -> None:
        lines = [
            ": heartbeat",
            "",
            "id:1",
            'data:{"topic": "t"}',
            "",
        ]
        mock_http = _mock_http_with_lines(lines)
        subscriber = EventBusSubscriber(config, mock_http)

        events = []
        async for event in subscriber.subscribe():
            events.append(event)
            break

        assert len(events) == 1
        assert events[0].seq == 1

    @pytest.mark.asyncio
    async def test_subscribe_sends_stable_consumer_id_and_no_since_seq_first_connect(
        self, config: EventBusSubscriberConfig
    ) -> None:
        mock_http = _mock_http_with_lines(["id:1", 'data:{"a": 1}', ""])
        subscriber = EventBusSubscriber(config, mock_http)

        async for _event in subscriber.subscribe():
            break

        _, kwargs = mock_http.stream.call_args
        assert kwargs["headers"]["Authorization"] == "Bearer test-consumer-token"
        # stable configured id, not a fresh uuid per attempt
        assert kwargs["params"]["consumer_id"] == "test-consumer"
        # first connect carries no since_seq
        assert "since_seq" not in kwargs["params"]


class TestReconnection:
    @pytest.mark.asyncio
    async def test_reconnects_with_stable_consumer_id_after_disconnect(
        self, config: EventBusSubscriberConfig
    ) -> None:
        mock_http = AsyncMock(spec=httpx.AsyncClient)
        first = _FakeStreamContextManager(
            _FakeStreamResponse([], raise_error=httpx.ReadTimeout("connection dropped"))
        )
        second = _FakeStreamContextManager(
            _FakeStreamResponse(["id:1", 'data:{"a": 1}', ""])
        )
        mock_http.stream = MagicMock(side_effect=[first, second])

        subscriber = EventBusSubscriber(config, mock_http)
        events = []
        async for event in subscriber.subscribe():
            events.append(event)
            break

        assert len(events) == 1
        assert mock_http.stream.call_count == 2
        first_call_id = mock_http.stream.call_args_list[0].kwargs["params"][
            "consumer_id"
        ]
        second_call_id = mock_http.stream.call_args_list[1].kwargs["params"][
            "consumer_id"
        ]
        # stable id reused across reconnects (was: fresh uuid each attempt)
        assert first_call_id == second_call_id == "test-consumer"

    @pytest.mark.asyncio
    async def test_raises_typed_error_after_max_reconnect_attempts(
        self, config: EventBusSubscriberConfig
    ) -> None:
        mock_http = AsyncMock(spec=httpx.AsyncClient)
        failing = [
            _FakeStreamContextManager(
                _FakeStreamResponse([], raise_error=httpx.ReadTimeout("dropped"))
            )
            for _ in range(config.max_reconnect_attempts)
        ]
        mock_http.stream = MagicMock(side_effect=failing)

        subscriber = EventBusSubscriber(config, mock_http)
        with pytest.raises(EventBusStreamError):
            async for _event in subscriber.subscribe():
                pass

    @pytest.mark.asyncio
    async def test_gap_event_delivered_in_order_with_since_seq(
        self, config: EventBusSubscriberConfig
    ) -> None:
        # First connection yields seq 1 then drops; the reconnect replays and
        # delivers seq 2. Both arrive in order and the reconnect carries the
        # last processed seq as since_seq.
        mock_http = AsyncMock(spec=httpx.AsyncClient)
        first = _FakeStreamContextManager(
            _FakeStreamResponse(
                ["id:1", 'data:{"a": 1}', ""],
                raise_error=httpx.ReadTimeout("dropped after event 1"),
            )
        )
        second = _FakeStreamContextManager(
            _FakeStreamResponse(["id:2", 'data:{"a": 2}', ""])
        )
        mock_http.stream = MagicMock(side_effect=[first, second])

        subscriber = EventBusSubscriber(config, mock_http)
        events = []
        async for event in subscriber.subscribe():
            events.append(event)
            if len(events) == 2:
                break

        assert [e.seq for e in events] == [1, 2]
        reconnect_params = mock_http.stream.call_args_list[1].kwargs["params"]
        assert reconnect_params["consumer_id"] == "test-consumer"
        assert reconnect_params["since_seq"] == 1

    @pytest.mark.asyncio
    async def test_first_connect_carries_no_since_seq(
        self, config: EventBusSubscriberConfig
    ) -> None:
        mock_http = _mock_http_with_lines(["id:1", 'data:{"a": 1}', ""])
        subscriber = EventBusSubscriber(config, mock_http)

        async for _event in subscriber.subscribe():
            break

        _, kwargs = mock_http.stream.call_args
        assert "since_seq" not in kwargs["params"]
        assert kwargs["params"]["consumer_id"] == "test-consumer"

    @pytest.mark.asyncio
    async def test_409_is_retried_with_same_id_then_success(
        self, config: EventBusSubscriberConfig
    ) -> None:
        mock_http = AsyncMock(spec=httpx.AsyncClient)
        first = _FakeStreamContextManager(
            _FakeStreamResponse([], raise_for_status_error=_http_409_error())
        )
        second = _FakeStreamContextManager(
            _FakeStreamResponse(["id:1", 'data:{"a": 1}', ""])
        )
        mock_http.stream = MagicMock(side_effect=[first, second])

        subscriber = EventBusSubscriber(config, mock_http)
        events = []
        async for event in subscriber.subscribe():
            events.append(event)
            break

        assert [e.seq for e in events] == [1]
        assert mock_http.stream.call_count == 2
        for call in mock_http.stream.call_args_list:
            assert call.kwargs["params"]["consumer_id"] == "test-consumer"

    @pytest.mark.asyncio
    async def test_409_exhaustion_raises_typed_error(
        self, config: EventBusSubscriberConfig
    ) -> None:
        mock_http = AsyncMock(spec=httpx.AsyncClient)
        failing = [
            _FakeStreamContextManager(
                _FakeStreamResponse([], raise_for_status_error=_http_409_error())
            )
            for _ in range(config.max_reconnect_attempts)
        ]
        mock_http.stream = MagicMock(side_effect=failing)

        subscriber = EventBusSubscriber(config, mock_http)
        with pytest.raises(EventBusStreamError):
            async for _event in subscriber.subscribe():
                pass

    @pytest.mark.asyncio
    async def test_attempt_counter_resets_after_successful_event(
        self, config: EventBusSubscriberConfig
    ) -> None:
        # With max_reconnect_attempts == 2, two disconnects would exhaust the
        # budget unless the counter resets after each yielded event.
        assert config.max_reconnect_attempts == 2
        mock_http = AsyncMock(spec=httpx.AsyncClient)
        first = _FakeStreamContextManager(
            _FakeStreamResponse(
                ["id:1", 'data:{"a": 1}', ""],
                raise_error=httpx.ReadTimeout("dropped after event 1"),
            )
        )
        second = _FakeStreamContextManager(
            _FakeStreamResponse(
                ["id:2", 'data:{"a": 2}', ""],
                raise_error=httpx.ReadTimeout("dropped after event 2"),
            )
        )
        third = _FakeStreamContextManager(
            _FakeStreamResponse(["id:3", 'data:{"a": 3}', ""])
        )
        mock_http.stream = MagicMock(side_effect=[first, second, third])

        subscriber = EventBusSubscriber(config, mock_http)
        events = []
        async for event in subscriber.subscribe():
            events.append(event)
            if len(events) == 3:
                break

        assert [e.seq for e in events] == [1, 2, 3]


class TestConfiguration:
    @pytest.mark.asyncio
    async def test_empty_consumer_id_raises_value_error(self) -> None:
        empty = EventBusSubscriberConfig(
            subscribe_url="http://localhost:8091/subscribe",
            consumer_token="t",
            consumer_id="",
        )
        with pytest.raises(ValueError):
            EventBusSubscriber(empty, MagicMock(spec=httpx.AsyncClient))
