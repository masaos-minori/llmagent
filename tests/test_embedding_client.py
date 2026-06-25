"""tests/test_embedding_client.py
Unit tests for agent/memory/embedding_client.py — EmbeddingClient with retry and circuit breaker.
"""

from __future__ import annotations

import asyncio
import time
from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import orjson
import pytest
from agent.memory.embedding_client import (
    EmbeddingClient,
    EmbeddingClientConfig,
)
from agent.memory.types import EmbeddingResult


@pytest.fixture()
def config() -> EmbeddingClientConfig:
    return EmbeddingClientConfig(
        embed_url="http://localhost:8001/embed",
        timeout=1.0,
        max_retries=2,
        circuit_open_after=3,
        circuit_reset_sec=0.1,
        embed_dim=0,  # disable dimension validation in existing tests
    )


# ── disabled / unavailable ───────────────────────────────────────────────────


class TestDisabledPaths:
    @pytest.mark.asyncio
    async def test_disabled_client_returns_disabled_error(
        self, config: EmbeddingClientConfig
    ) -> None:
        client = EmbeddingClient(config, enabled=False)
        result = await client.fetch("hello")
        assert isinstance(result, EmbeddingResult)
        assert result.success is False
        assert result.error_kind == "disabled"

    @pytest.mark.asyncio
    async def test_no_http_client_returns_disabled_error(
        self, config: EmbeddingClientConfig
    ) -> None:
        client = EmbeddingClient(config, http=None, enabled=True)
        result = await client.fetch("hello")
        assert isinstance(result, EmbeddingResult)
        assert result.success is False
        assert result.error_kind == "disabled"

    @pytest.mark.asyncio
    async def test_empty_embed_url_returns_disabled_error(
        self, config: EmbeddingClientConfig
    ) -> None:
        config.embed_url = ""
        mock_http = AsyncMock(spec=httpx.AsyncClient)
        client = EmbeddingClient(config, http=mock_http, enabled=True)
        result = await client.fetch("hello")
        assert isinstance(result, EmbeddingResult)
        assert result.success is False
        assert result.error_kind == "disabled"


# ── circuit breaker ──────────────────────────────────────────────────────────


class TestCircuitBreaker:
    @pytest.mark.asyncio
    async def test_circuit_open_blocks_requests(
        self, config: EmbeddingClientConfig
    ) -> None:
        client = EmbeddingClient(config)
        mock_http = AsyncMock(spec=httpx.AsyncClient)
        client._http = mock_http
        client._enabled = True
        with patch.object(time, "monotonic", return_value=100.0):
            client._circuit_opened_at = 99.95  # 0.05s elapsed < circuit_reset_sec=0.1
            result = await client.fetch("hello")
            assert isinstance(result, EmbeddingResult)
            assert result.success is False
            assert result.error_kind == "circuit_open"

    @pytest.mark.asyncio
    async def test_circuit_auto_resets_after_timeout(
        self, config: EmbeddingClientConfig
    ) -> None:
        client = EmbeddingClient(config)
        client._circuit_opened_at = 0.0
        with patch.object(time, "monotonic", return_value=100.0):
            result = await client.fetch("hello")
            # Circuit should have reset; will fail because http is None
            assert isinstance(result, EmbeddingResult)
            assert result.error_kind != "circuit_open"

    @pytest.mark.asyncio
    async def test_circuit_opens_after_consecutive_failures(
        self, config: EmbeddingClientConfig
    ) -> None:
        config.circuit_open_after = 2
        client = EmbeddingClient(config)
        mock_http = AsyncMock(spec=httpx.AsyncClient)
        mock_resp = MagicMock()
        mock_resp.raise_for_status.side_effect = httpx.HTTPStatusError(
            "error", request=MagicMock(), response=MagicMock(status_code=500)
        )
        mock_http.post = AsyncMock(return_value=mock_resp)
        client._http = mock_http
        client._enabled = True

        await client.fetch("hello")  # failure 1
        await client.fetch("hello")  # failure 2 → circuit opens

        assert client._is_circuit_open() is True

    def test_record_failure_increments_counter(
        self, config: EmbeddingClientConfig
    ) -> None:
        client = EmbeddingClient(config)
        client._record_failure()
        assert client._fail_count == 1


# ── successful embedding ─────────────────────────────────────────────────────


class TestSuccessfulEmbedding:
    @pytest.mark.asyncio
    async def test_valid_response_returns_embedding(
        self, config: EmbeddingClientConfig
    ) -> None:
        client = EmbeddingClient(config)
        mock_resp = MagicMock()
        mock_resp.content = orjson.dumps({"embedding": [0.1, 0.2, 0.3]})
        mock_resp.raise_for_status.return_value = None

        mock_http = AsyncMock(spec=httpx.AsyncClient)
        mock_http.post = AsyncMock(return_value=mock_resp)
        client._http = mock_http
        client._enabled = True

        result = await client.fetch("hello")
        assert result.success is True
        assert result.embedding == [0.1, 0.2, 0.3]

    @pytest.mark.asyncio
    async def test_response_with_non_list_embedding_returns_error(
        self,
        config: EmbeddingClientConfig,
    ) -> None:
        config.max_retries = 0
        client = EmbeddingClient(config)
        mock_resp = MagicMock()
        mock_resp.json.return_value = {"embedding": "not_a_list"}
        mock_resp.raise_for_status.return_value = None

        mock_http = AsyncMock(spec=httpx.AsyncClient)
        mock_http.post = AsyncMock(return_value=mock_resp)
        client._http = mock_http
        client._enabled = True

        result = await client.fetch("hello")
        assert result.success is False
        assert result.error_kind == "invalid_response"

    @pytest.mark.asyncio
    async def test_empty_embedding_list_returns_error(
        self, config: EmbeddingClientConfig
    ) -> None:
        config.max_retries = 0
        client = EmbeddingClient(config)
        mock_resp = MagicMock()
        mock_resp.json.return_value = {"embedding": []}
        mock_resp.raise_for_status.return_value = None

        mock_http = AsyncMock(spec=httpx.AsyncClient)
        mock_http.post = AsyncMock(return_value=mock_resp)
        client._http = mock_http
        client._enabled = True

        result = await client.fetch("hello")
        assert result.success is False
        assert result.error_kind == "invalid_response"


# ── error handling ───────────────────────────────────────────────────────────


class TestErrorHandling:
    @pytest.mark.asyncio
    async def test_http_status_error_returns_error(
        self, config: EmbeddingClientConfig
    ) -> None:
        config.max_retries = 0
        client = EmbeddingClient(config)
        mock_resp = MagicMock()
        mock_http = AsyncMock(spec=httpx.AsyncClient)
        mock_http.post = AsyncMock(
            side_effect=httpx.HTTPStatusError(
                "500", request=MagicMock(), response=mock_resp
            )
        )
        client._http = mock_http
        client._enabled = True

        result = await client.fetch("hello")
        assert result.success is False
        assert result.error_kind == "http_error"

    @pytest.mark.asyncio
    async def test_generic_exception_returns_error(
        self, config: EmbeddingClientConfig
    ) -> None:
        config.max_retries = 0
        client = EmbeddingClient(config)
        mock_http = AsyncMock(spec=httpx.AsyncClient)
        mock_http.post = AsyncMock(side_effect=RuntimeError("unexpected"))
        client._http = mock_http
        client._enabled = True

        result = await client.fetch("hello")
        assert result.success is False
        assert result.error_kind == "http_error"


# ── retry logic ──────────────────────────────────────────────────────────────


class TestRetry:
    @pytest.mark.asyncio
    async def test_retries_on_failure_then_succeeds(
        self, config: EmbeddingClientConfig
    ) -> None:
        config.max_retries = 2
        client = EmbeddingClient(config)
        call_count = 0

        async def _fake_post(*a: object, **kw: object) -> MagicMock:
            nonlocal call_count
            call_count += 1
            mock_resp = MagicMock()
            if call_count <= 1:
                raise httpx.HTTPStatusError(
                    "fail", request=MagicMock(), response=MagicMock(status_code=500)
                )
            mock_resp.content = orjson.dumps({"embedding": [0.1]})
            mock_resp.raise_for_status.return_value = None
            return mock_resp

        mock_http = AsyncMock(spec=httpx.AsyncClient)
        mock_http.post = _fake_post
        client._http = mock_http
        client._enabled = True

        result = await client.fetch("hello")
        assert result.success is True
        assert call_count == 2

    @pytest.mark.asyncio
    async def test_all_retries_fail_returns_last_error(
        self,
        config: EmbeddingClientConfig,
    ) -> None:
        config.max_retries = 1
        client = EmbeddingClient(config)
        mock_resp = MagicMock()
        mock_http = AsyncMock(spec=httpx.AsyncClient)
        mock_http.post = AsyncMock(
            side_effect=httpx.HTTPStatusError(
                "fail", request=MagicMock(), response=mock_resp
            )
        )
        client._http = mock_http
        client._enabled = True

        result = await client.fetch("hello")
        assert result.success is False
        assert result.error_kind == "http_error"

    @pytest.mark.asyncio
    async def test_max_retries_zero_single_attempt_on_failure(
        self, config: EmbeddingClientConfig
    ) -> None:
        config.max_retries = 0
        client = EmbeddingClient(config)
        call_count = 0

        async def _fake_post(*a: object, **kw: object) -> MagicMock:
            nonlocal call_count
            call_count += 1
            raise httpx.HTTPStatusError(
                "fail", request=MagicMock(), response=MagicMock(status_code=500)
            )

        mock_http = AsyncMock(spec=httpx.AsyncClient)
        mock_http.post = _fake_post
        client._http = mock_http
        client._enabled = True

        result = await client.fetch("hello")
        assert result.success is False
        assert call_count == 1

    @pytest.mark.asyncio
    async def test_max_retries_zero_single_attempt_on_success(
        self, config: EmbeddingClientConfig
    ) -> None:
        config.max_retries = 0
        client = EmbeddingClient(config)
        call_count = 0

        async def _fake_post(*a: object, **kw: object) -> MagicMock:
            nonlocal call_count
            call_count += 1
            mock_resp = MagicMock()
            mock_resp.content = orjson.dumps({"embedding": [0.1]})
            mock_resp.raise_for_status.return_value = None
            return mock_resp

        mock_http = AsyncMock(spec=httpx.AsyncClient)
        mock_http.post = _fake_post
        client._http = mock_http
        client._enabled = True

        result = await client.fetch("hello")
        assert result.success is True
        assert call_count == 1

    @pytest.mark.asyncio
    async def test_max_retries_two_all_fail_three_attempts(
        self, config: EmbeddingClientConfig
    ) -> None:
        config.max_retries = 2
        client = EmbeddingClient(config)
        mock_resp = MagicMock()
        call_count = 0

        async def _fake_post(*a: object, **kw: object) -> MagicMock:
            nonlocal call_count
            call_count += 1
            raise httpx.HTTPStatusError("fail", request=MagicMock(), response=mock_resp)

        mock_http = AsyncMock(spec=httpx.AsyncClient)
        mock_http.post = _fake_post
        client._http = mock_http
        client._enabled = True

        result = await client.fetch("hello")
        assert result.success is False
        assert call_count == 3

    @pytest.mark.asyncio
    async def test_max_retries_one_success_on_second_attempt(
        self, config: EmbeddingClientConfig
    ) -> None:
        config.max_retries = 1
        client = EmbeddingClient(config)
        call_count = 0

        async def _fake_post(*a: object, **kw: object) -> MagicMock:
            nonlocal call_count
            call_count += 1
            mock_resp = MagicMock()
            if call_count == 1:
                raise httpx.HTTPStatusError(
                    "fail", request=MagicMock(), response=MagicMock(status_code=500)
                )
            mock_resp.content = orjson.dumps({"embedding": [0.1]})
            mock_resp.raise_for_status.return_value = None
            return mock_resp

        mock_http = AsyncMock(spec=httpx.AsyncClient)
        mock_http.post = _fake_post
        client._http = mock_http
        client._enabled = True

        result = await client.fetch("hello")
        assert result.success is True
        assert call_count == 2

    @pytest.mark.asyncio
    async def test_max_retries_two_fail_twice_then_succeed_on_third(
        self, config: EmbeddingClientConfig
    ) -> None:
        config.max_retries = 2
        client = EmbeddingClient(config)
        call_count = 0

        async def _fake_post(*a: object, **kw: object) -> MagicMock:
            nonlocal call_count
            call_count += 1
            if call_count <= 2:
                raise httpx.HTTPStatusError(
                    "fail", request=MagicMock(), response=MagicMock(status_code=500)
                )
            mock_resp = MagicMock()
            mock_resp.content = orjson.dumps({"embedding": [0.1]})
            mock_resp.raise_for_status.return_value = None
            return mock_resp

        mock_http = AsyncMock(spec=httpx.AsyncClient)
        mock_http.post = _fake_post
        client._http = mock_http
        client._enabled = True

        result = await client.fetch("hello")
        assert result.success is True
        assert call_count == 3

    @pytest.mark.asyncio
    async def test_max_retries_one_all_fail_exactly_two_attempts(
        self, config: EmbeddingClientConfig
    ) -> None:
        config.max_retries = 1
        client = EmbeddingClient(config)
        call_count = 0

        async def _fake_post(*a: object, **kw: object) -> MagicMock:
            nonlocal call_count
            call_count += 1
            raise httpx.HTTPStatusError(
                "fail", request=MagicMock(), response=MagicMock(status_code=503)
            )

        mock_http = AsyncMock(spec=httpx.AsyncClient)
        mock_http.post = _fake_post
        client._http = mock_http
        client._enabled = True

        result = await client.fetch("hello")
        assert result.success is False
        assert call_count == 2

    @pytest.mark.asyncio
    async def test_max_retries_two_no_retry_on_first_success(
        self, config: EmbeddingClientConfig
    ) -> None:
        config.max_retries = 2
        client = EmbeddingClient(config)
        call_count = 0

        async def _fake_post(*a: object, **kw: object) -> MagicMock:
            nonlocal call_count
            call_count += 1
            mock_resp = MagicMock()
            mock_resp.content = orjson.dumps({"embedding": [0.2, 0.3]})
            mock_resp.raise_for_status.return_value = None
            return mock_resp

        mock_http = AsyncMock(spec=httpx.AsyncClient)
        mock_http.post = _fake_post
        client._http = mock_http
        client._enabled = True

        result = await client.fetch("hello")
        assert result.success is True
        assert call_count == 1


# ── timeout ──────────────────────────────────────────────────────────────────


class TestTimeout:
    @pytest.mark.asyncio
    async def test_timeout_returns_timeout_error(
        self, config: EmbeddingClientConfig
    ) -> None:
        config.max_retries = 0
        client = EmbeddingClient(config)

        async def _slow_post(*a: object, **kw: object) -> MagicMock:
            await asyncio.sleep(10)
            return MagicMock()

        mock_http = AsyncMock(spec=httpx.AsyncClient)
        mock_http.post = _slow_post
        client._http = mock_http
        client._enabled = True

        result = await client.fetch("hello")
        assert result.success is False
        assert result.error_kind == "timeout"


# ── _record_failure() call count verification ────────────────────────────────


class TestRecordFailureCount:
    @pytest.mark.asyncio
    async def test_record_failure_called_on_http_error_retry(
        self, config: EmbeddingClientConfig
    ) -> None:
        config.max_retries = 2
        client = EmbeddingClient(config)
        call_count = 0

        async def _side_effect(*a: object, **kw: object) -> MagicMock:
            nonlocal call_count
            call_count += 1
            mock_resp = MagicMock()
            raise httpx.HTTPStatusError("fail", request=MagicMock(), response=mock_resp)

        mock_http = AsyncMock(spec=httpx.AsyncClient)
        mock_http.post = _side_effect
        client._http = mock_http
        client._enabled = True

        result = await client.fetch("hello")
        assert result.success is False
        assert call_count == 3
        assert client._fail_count == 3

    @pytest.mark.asyncio
    async def test_record_failure_called_on_timeout_retry(
        self, config: EmbeddingClientConfig
    ) -> None:
        config.max_retries = 2
        client = EmbeddingClient(config)
        call_count = 0

        async def _slow_post(*a: object, **kw: object) -> MagicMock:
            nonlocal call_count
            call_count += 1
            await asyncio.sleep(10)
            return MagicMock()

        mock_http = AsyncMock(spec=httpx.AsyncClient)
        mock_http.post = _slow_post
        client._http = mock_http
        client._enabled = True

        await client.fetch("hello")
        assert call_count == 3
        assert client._fail_count == 3

    @pytest.mark.asyncio
    async def test_record_failure_not_called_on_success(
        self, config: EmbeddingClientConfig
    ) -> None:
        config.max_retries = 2
        client = EmbeddingClient(config)
        call_count = 0

        async def _side_effect(*a: object, **kw: object) -> MagicMock:
            nonlocal call_count
            call_count += 1
            mock_resp = MagicMock()
            if call_count <= 2:
                raise httpx.HTTPStatusError(
                    "fail", request=MagicMock(), response=MagicMock(status_code=500)
                )
            mock_resp.content = orjson.dumps({"embedding": [0.1]})
            mock_resp.raise_for_status.return_value = None
            return mock_resp

        mock_http = AsyncMock(spec=httpx.AsyncClient)
        mock_http.post = _side_effect
        client._http = mock_http
        client._enabled = True

        result = await client.fetch("hello")
        assert result.success is True
        assert call_count == 3
        assert client._fail_count == 0


# ── timeout + retry ──────────────────────────────────────────────────────────


class TestTimeoutRetry:
    @pytest.mark.asyncio
    async def test_all_timeout_retries_fail_returns_timeout(
        self, config: EmbeddingClientConfig
    ) -> None:
        config.max_retries = 2
        client = EmbeddingClient(config)
        call_count = 0

        async def _slow_post(*a: object, **kw: object) -> MagicMock:
            nonlocal call_count
            call_count += 1
            await asyncio.sleep(10)
            return MagicMock()

        mock_http = AsyncMock(spec=httpx.AsyncClient)
        mock_http.post = _slow_post
        client._http = mock_http
        client._enabled = True

        result = await client.fetch("hello")
        assert result.success is False
        assert result.error_kind == "circuit_open"
        assert call_count == 3

    @pytest.mark.asyncio
    async def test_timeout_then_success_on_retry(
        self, config: EmbeddingClientConfig
    ) -> None:
        config.max_retries = 2
        client = EmbeddingClient(config)
        call_count = 0

        async def _slow_post(*a: object, **kw: object) -> MagicMock:
            nonlocal call_count
            call_count += 1
            if call_count <= 1:
                await asyncio.sleep(10)
                return MagicMock()
            mock_resp = MagicMock()
            mock_resp.content = orjson.dumps({"embedding": [0.1]})
            mock_resp.raise_for_status.return_value = None
            return mock_resp

        mock_http = AsyncMock(spec=httpx.AsyncClient)
        mock_http.post = _slow_post
        client._http = mock_http
        client._enabled = True

        result = await client.fetch("hello")
        assert result.success is True
        assert call_count == 2

    @pytest.mark.asyncio
    async def test_max_retries_zero_timeout_single_attempt(
        self, config: EmbeddingClientConfig
    ) -> None:
        config.max_retries = 0
        client = EmbeddingClient(config)
        call_count = 0

        async def _slow_post(*a: object, **kw: object) -> MagicMock:
            nonlocal call_count
            call_count += 1
            await asyncio.sleep(10)
            return MagicMock()

        mock_http = AsyncMock(spec=httpx.AsyncClient)
        mock_http.post = _slow_post
        client._http = mock_http
        client._enabled = True

        result = await client.fetch("hello")
        assert result.success is False
        assert result.error_kind == "timeout"
        assert call_count == 1


# ── mixed failure pattern (timeout + http_error) ─────────────────────────────


class TestMixedFailure:
    @pytest.mark.asyncio
    async def test_timeout_then_http_error_all_fail(
        self, config: EmbeddingClientConfig
    ) -> None:
        config.max_retries = 2
        client = EmbeddingClient(config)
        call_count = 0

        async def _side_effect(*a: object, **kw: object) -> MagicMock:
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                await asyncio.sleep(10)
                return MagicMock()
            mock_resp = MagicMock()
            raise httpx.HTTPStatusError("fail", request=MagicMock(), response=mock_resp)

        mock_http = AsyncMock(spec=httpx.AsyncClient)
        mock_http.post = _side_effect
        client._http = mock_http
        client._enabled = True

        result = await client.fetch("hello")
        assert result.success is False
        assert call_count == 3

    @pytest.mark.asyncio
    async def test_http_error_then_timeout_then_success(
        self, config: EmbeddingClientConfig
    ) -> None:
        config.max_retries = 2
        client = EmbeddingClient(config)
        call_count = 0

        async def _side_effect(*a: object, **kw: object) -> MagicMock:
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                mock_resp = MagicMock()
                raise httpx.HTTPStatusError(
                    "fail", request=MagicMock(), response=mock_resp
                )
            if call_count == 2:
                await asyncio.sleep(10)
                return MagicMock()
            mock_resp = MagicMock()
            mock_resp.content = orjson.dumps({"embedding": [0.1]})
            mock_resp.raise_for_status.return_value = None
            return mock_resp

        mock_http = AsyncMock(spec=httpx.AsyncClient)
        mock_http.post = _side_effect
        client._http = mock_http
        client._enabled = True

        result = await client.fetch("hello")
        assert result.success is True
        assert call_count == 3

    @pytest.mark.asyncio
    async def test_mixed_failure_all_fail_returns_last_error(
        self, config: EmbeddingClientConfig
    ) -> None:
        config.max_retries = 2
        client = EmbeddingClient(config)
        call_count = 0

        async def _side_effect(*a: object, **kw: object) -> MagicMock:
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                await asyncio.sleep(10)
                return MagicMock()
            mock_resp = MagicMock()
            raise httpx.HTTPStatusError("fail", request=MagicMock(), response=mock_resp)

        mock_http = AsyncMock(spec=httpx.AsyncClient)
        mock_http.post = _side_effect
        client._http = mock_http
        client._enabled = True

        result = await client.fetch("hello")
        assert result.success is False
        assert call_count == 3


# ── circuit breaker during retry loop ────────────────────────────────────────


class TestCircuitDuringRetry:
    @pytest.mark.asyncio
    async def test_circuit_opens_during_retry(
        self, config: EmbeddingClientConfig
    ) -> None:
        config.max_retries = 2
        config.circuit_open_after = 2
        client = EmbeddingClient(config)
        call_count = 0

        async def _side_effect(*a: object, **kw: object) -> MagicMock:
            nonlocal call_count
            call_count += 1
            mock_resp = MagicMock()
            raise httpx.HTTPStatusError("fail", request=MagicMock(), response=mock_resp)

        mock_http = AsyncMock(spec=httpx.AsyncClient)
        mock_http.post = _side_effect
        client._http = mock_http
        client._enabled = True

        result = await client.fetch("hello")
        assert result.success is False
        assert result.error_kind == "circuit_open"
        assert call_count == 2

    @pytest.mark.asyncio
    async def test_circuit_opens_after_timeout_then_success_on_retry(
        self, config: EmbeddingClientConfig
    ) -> None:
        config.max_retries = 2
        config.circuit_open_after = 1
        client = EmbeddingClient(config)
        call_count = 0

        async def _side_effect(*a: object, **kw: object) -> MagicMock:
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                await asyncio.sleep(10)
                return MagicMock()
            mock_resp = MagicMock()
            mock_resp.content = orjson.dumps({"embedding": [0.1]})
            mock_resp.raise_for_status.return_value = None
            return mock_resp

        mock_http = AsyncMock(spec=httpx.AsyncClient)
        mock_http.post = _side_effect
        client._http = mock_http
        client._enabled = True

        result = await client.fetch("hello")
        assert result.success is False
        assert result.error_kind == "circuit_open"
        assert call_count == 1


# ── timeout triggers circuit after max failures ──────────────────────────────


class TestTimeoutCircuit:
    @pytest.mark.asyncio
    async def test_timeout_triggers_circuit_after_max_failures(
        self,
        config: EmbeddingClientConfig,
    ) -> None:
        config.max_retries = 0
        config.circuit_open_after = 2
        client = EmbeddingClient(config)

        async def _slow_post(*a: object, **kw: object) -> MagicMock:
            await asyncio.sleep(10)
            return MagicMock()

        mock_http = AsyncMock(spec=httpx.AsyncClient)
        mock_http.post = _slow_post
        client._http = mock_http
        client._enabled = True

        await client.fetch("hello")  # failure 1
        assert client._fail_count == 1

        await client.fetch("hello")  # failure 2 → circuit opens
        assert client._is_circuit_open() is True


# ── success resets fail count ────────────────────────────────────────────────


class TestSuccessResetsFailCount:
    @pytest.mark.asyncio
    async def test_success_resets_fail_count(
        self, config: EmbeddingClientConfig
    ) -> None:
        config.circuit_open_after = 3
        config.max_retries = 0
        client = EmbeddingClient(config)
        mock_resp_ok = MagicMock()
        mock_resp_ok.content = orjson.dumps({"embedding": [0.1]})
        mock_resp_ok.raise_for_status = MagicMock()

        call_count = 0

        async def _side_effect(*a: object, **kw: object) -> MagicMock:
            nonlocal call_count
            call_count += 1
            if call_count <= 2:
                raise httpx.HTTPStatusError(
                    "fail", request=MagicMock(), response=MagicMock(status_code=500)
                )
            return mock_resp_ok

        mock_http = AsyncMock(spec=httpx.AsyncClient)
        mock_http.post = _side_effect
        client._http = mock_http
        client._enabled = True

        await client.fetch("hello")  # failure 1
        assert client._fail_count == 1

        await client.fetch("hello")  # failure 2
        assert client._fail_count == 2

        result = await client.fetch("hello")  # success → reset
        assert result.success is True
        assert client._fail_count == 0


# ── dimension validation ─────────────────────────────────────────────────────


class TestDimensionValidation:
    @pytest.mark.asyncio
    async def test_rejects_wrong_dimension(self) -> None:
        """EmbeddingClient returns DIMENSION_MISMATCH when server returns wrong dims."""
        from agent.memory.types import EmbeddingErrorKind

        cfg = EmbeddingClientConfig(
            embed_url="http://localhost:8001/embed",
            timeout=1.0,
            max_retries=0,
            embed_dim=384,
        )
        client = EmbeddingClient(cfg, enabled=True)
        mock_resp = MagicMock()
        mock_resp.raise_for_status.return_value = None
        mock_resp.content = orjson.dumps({"embedding": [0.1] * 768})
        mock_http = AsyncMock(spec=httpx.AsyncClient)
        mock_http.post.return_value = mock_resp
        client._http = mock_http

        result = await client.fetch("test")
        assert result.success is False
        assert result.error_kind == EmbeddingErrorKind.DIMENSION_MISMATCH

    @pytest.mark.asyncio
    async def test_accepts_correct_dimension(self) -> None:
        """EmbeddingClient returns success when dims match."""
        cfg = EmbeddingClientConfig(
            embed_url="http://localhost:8001/embed",
            timeout=1.0,
            max_retries=0,
            embed_dim=384,
        )
        client = EmbeddingClient(cfg, enabled=True)
        mock_resp = MagicMock()
        mock_resp.raise_for_status.return_value = None
        mock_resp.content = orjson.dumps({"embedding": [0.1] * 384})
        mock_http = AsyncMock(spec=httpx.AsyncClient)
        mock_http.post.return_value = mock_resp
        client._http = mock_http

        result = await client.fetch("test")
        assert result.success is True
        assert result.embedding is not None and len(result.embedding) == 384

    @pytest.mark.asyncio
    async def test_dim_zero_disables_validation(self) -> None:
        """embed_dim=0 disables dimension validation; any size accepted."""
        cfg = EmbeddingClientConfig(
            embed_url="http://localhost:8001/embed",
            timeout=1.0,
            max_retries=0,
            embed_dim=0,
        )
        client = EmbeddingClient(cfg, enabled=True)
        mock_resp = MagicMock()
        mock_resp.raise_for_status.return_value = None
        mock_resp.content = orjson.dumps({"embedding": [0.1] * 768})
        mock_http = AsyncMock(spec=httpx.AsyncClient)
        mock_http.post.return_value = mock_resp
        client._http = mock_http

        result = await client.fetch("test")
        assert result.success is True
