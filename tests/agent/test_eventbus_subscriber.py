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


def _make_config(
    consumer_id: str = "test-consumer",
    max_reconnect_attempts: int = 2,
    reconnect_delay_sec: float = 0.0,
) -> EventBusSubscriberConfig:
    return EventBusSubscriberConfig(
        subscribe_url="http://localhost:8091/subscribe",
        timeout=1.0,
        consumer_token="test-consumer-token",
        consumer_id=consumer_id,
        max_reconnect_attempts=max_reconnect_attempts,
        reconnect_delay_sec=reconnect_delay_sec,
    )


@pytest.fixture()
def config() -> EventBusSubscriberConfig:
    return _make_config()


class _FakeStreamResponse:
    """Minimal stand-in for httpx's streaming response, driven by a fixed
    list of SSE lines (as `aiter_lines()` would yield them).

    `status_error` is raised by `raise_for_status()` (a rejected connection),
    `raise_error` is raised after the lines are exhausted (a mid-stream drop).
    """

    def __init__(
        self,
        lines: list[str],
        raise_error: Exception | None = None,
        status_error: Exception | None = None,
    ) -> None:
        self._lines = lines
        self._raise_error = raise_error
        self._status_error = status_error

    def raise_for_status(self) -> None:
        if self._status_error is not None:
            raise self._status_error

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


def _stream_ctx(
    lines: list[str],
    raise_error: Exception | None = None,
    status_error: Exception | None = None,
) -> _FakeStreamContextManager:
    return _FakeStreamContextManager(
        _FakeStreamResponse(lines, raise_error=raise_error, status_error=status_error)
    )


def _mock_http(*responses: _FakeStreamContextManager) -> AsyncMock:
    mock_http = AsyncMock(spec=httpx.AsyncClient)
    mock_http.stream = MagicMock(side_effect=list(responses))
    return mock_http


def _status_error(status: int) -> httpx.HTTPStatusError:
    request = httpx.Request("GET", "http://localhost:8091/subscribe")
    response = httpx.Response(status, request=request)
    return httpx.HTTPStatusError(f"HTTP {status}", request=request, response=response)


def _frame(seq: int) -> list[str]:
    return [f"id:{seq}", f'data:{{"topic": "agent.test", "seq": {seq}}}', ""]


async def _collect(subscriber: EventBusSubscriber, count: int) -> list[int]:
    seqs: list[int] = []
    async for event in subscriber.subscribe():
        seqs.append(event.seq)
        if len(seqs) == count:
            break
    return seqs


class TestSuccessfulSubscribe:
    @pytest.mark.asyncio
    async def test_yields_parsed_events(self, config: EventBusSubscriberConfig) -> None:
        mock_http = _mock_http(_stream_ctx(_frame(1)))
        subscriber = EventBusSubscriber(config, mock_http)

        events = []
        async for event in subscriber.subscribe():
            events.append(event)
            break

        assert len(events) == 1
        assert events[0].seq == 1
        assert events[0].data == {"topic": "agent.test", "seq": 1}

    @pytest.mark.asyncio
    async def test_heartbeat_comment_lines_are_ignored(
        self, config: EventBusSubscriberConfig
    ) -> None:
        lines = [": heartbeat", "", *_frame(1)]
        mock_http = _mock_http(_stream_ctx(lines))
        subscriber = EventBusSubscriber(config, mock_http)

        events = []
        async for event in subscriber.subscribe():
            events.append(event)
            break

        assert len(events) == 1
        assert events[0].seq == 1

    @pytest.mark.asyncio
    async def test_subscribe_sends_bearer_auth_and_configured_consumer_id(
        self, config: EventBusSubscriberConfig
    ) -> None:
        mock_http = _mock_http(_stream_ctx(_frame(1)))
        subscriber = EventBusSubscriber(config, mock_http)

        async for _event in subscriber.subscribe():
            break

        _, kwargs = mock_http.stream.call_args
        assert kwargs["headers"]["Authorization"] == "Bearer test-consumer-token"
        assert kwargs["params"]["consumer_id"] == "test-consumer"


class TestReconnection:
    @pytest.mark.asyncio
    async def test_reconnects_with_configured_consumer_id_after_disconnect(
        self, config: EventBusSubscriberConfig
    ) -> None:
        mock_http = _mock_http(
            _stream_ctx([], raise_error=httpx.ReadTimeout("connection dropped")),
            _stream_ctx(_frame(1)),
        )
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
        assert first_call_id == "test-consumer"
        assert second_call_id == "test-consumer"

    @pytest.mark.asyncio
    async def test_raises_typed_error_after_max_reconnect_attempts(
        self, config: EventBusSubscriberConfig
    ) -> None:
        failing = [
            _stream_ctx([], raise_error=httpx.ReadTimeout("dropped"))
            for _ in range(config.max_reconnect_attempts)
        ]
        mock_http = _mock_http(*failing)

        subscriber = EventBusSubscriber(config, mock_http)
        with pytest.raises(EventBusStreamError):
            async for _event in subscriber.subscribe():
                pass

    @pytest.mark.asyncio
    async def test_attempt_counter_resets_after_yielded_events(
        self, config: EventBusSubscriberConfig
    ) -> None:
        # 2 consecutive failures would exhaust max_reconnect_attempts=2, but
        # each stream delivers one event first, resetting the counter each time.
        mock_http = _mock_http(
            _stream_ctx(_frame(1), raise_error=httpx.ReadTimeout("dropped")),
            _stream_ctx(_frame(2), raise_error=httpx.ReadTimeout("dropped")),
            _stream_ctx(_frame(3)),
        )
        subscriber = EventBusSubscriber(config, mock_http)

        seqs = await _collect(subscriber, 3)

        assert seqs == [1, 2, 3]
        assert mock_http.stream.call_count == 3


class TestResume:
    @pytest.mark.asyncio
    async def test_reconnect_sends_since_seq_and_delivers_gap_event_once(
        self, config: EventBusSubscriberConfig
    ) -> None:
        # First stream delivers seq 1, then drops mid-stream. The server
        # answers the reconnect's since_seq=1 with the gap event seq 2 only.
        mock_http = _mock_http(
            _stream_ctx(_frame(1), raise_error=httpx.ReadError("dropped")),
            _stream_ctx(_frame(2)),
        )
        subscriber = EventBusSubscriber(config, mock_http)

        seqs = await _collect(subscriber, 2)

        assert seqs == [1, 2]
        assert mock_http.stream.call_count == 2
        first_params = mock_http.stream.call_args_list[0].kwargs["params"]
        second_params = mock_http.stream.call_args_list[1].kwargs["params"]
        assert "since_seq" not in first_params
        assert second_params["since_seq"] == 1
        assert first_params["consumer_id"] == "test-consumer"
        assert second_params["consumer_id"] == "test-consumer"

    @pytest.mark.asyncio
    async def test_first_connect_and_pre_event_reconnect_send_no_since_seq(
        self, config: EventBusSubscriberConfig
    ) -> None:
        # Reconnect before any event was processed: no seq is known yet.
        mock_http = _mock_http(
            _stream_ctx([], raise_error=httpx.ConnectError("refused")),
            _stream_ctx(_frame(1)),
        )
        subscriber = EventBusSubscriber(config, mock_http)

        seqs = await _collect(subscriber, 1)

        assert seqs == [1]
        assert mock_http.stream.call_count == 2
        for call in mock_http.stream.call_args_list:
            assert "since_seq" not in call.kwargs["params"]
            assert "Last-Event-ID" not in call.kwargs["headers"]


class TestConflict409:
    @pytest.mark.asyncio
    async def test_409_is_retried_with_same_id_and_warns_naming_it(
        self, config: EventBusSubscriberConfig, caplog: pytest.LogCaptureFixture
    ) -> None:
        # Old connection still registered server-side: 409 mid-stream after
        # seq 1 was delivered; the next attempt resumes from since_seq=1.
        mock_http = _mock_http(
            _stream_ctx(_frame(1), raise_error=_status_error(409)),
            _stream_ctx(_frame(2)),
        )
        subscriber = EventBusSubscriber(config, mock_http)

        seqs = await _collect(subscriber, 2)

        assert seqs == [1, 2]
        assert mock_http.stream.call_count == 2
        first_params = mock_http.stream.call_args_list[0].kwargs["params"]
        second_params = mock_http.stream.call_args_list[1].kwargs["params"]
        assert first_params["consumer_id"] == "test-consumer"
        assert second_params["consumer_id"] == "test-consumer"
        assert second_params["since_seq"] == 1
        warnings = [
            record
            for record in caplog.records
            if "test-consumer" in record.getMessage()
        ]
        assert len(warnings) >= 1

    @pytest.mark.asyncio
    async def test_409_exhaustion_raises_eventbus_stream_error_chained(
        self, config: EventBusSubscriberConfig
    ) -> None:
        conflict_config = _make_config(
            max_reconnect_attempts=1,
            reconnect_delay_sec=0.0,
        )
        mock_http = _mock_http(_stream_ctx([], status_error=_status_error(409)))
        subscriber = EventBusSubscriber(conflict_config, mock_http)

        with pytest.raises(EventBusStreamError) as excinfo:
            async for _event in subscriber.subscribe():
                pass

        assert isinstance(excinfo.value.__cause__, httpx.HTTPStatusError)
        assert excinfo.value.__cause__.response.status_code == 409
        assert mock_http.stream.call_count == 1


class TestConfigValidation:
    @pytest.mark.asyncio
    async def test_empty_consumer_id_raises_value_error(self) -> None:
        empty_config = _make_config(consumer_id="")
        mock_http = _mock_http(_stream_ctx(_frame(1)))

        with pytest.raises(ValueError):
            EventBusSubscriber(empty_config, mock_http)

    @pytest.mark.asyncio
    async def test_subscribe_with_valid_config_does_not_raise(self) -> None:
        config = _make_config()
        mock_http = _mock_http(_stream_ctx(_frame(1)))
        subscriber = EventBusSubscriber(config, mock_http)

        seqs = await _collect(subscriber, 1)

        assert seqs == [1]
