"""Edge case tests for MCP CICD job log retrieval and security guards."""

from unittest.mock import AsyncMock, MagicMock

import pytest
from mcp_servers.cicd.cicd_models import CicdUpstreamError
from mcp_servers.cicd.service_github_actions_job import GitHubActionsJobBackend


class TestNon2xxFailFast:
    """Verify non-2xx responses cause fail-fast behavior."""

    @pytest.mark.asyncio
    async def test_non_2xx_on_jobs_fetch_raises_upstream_error(self) -> None:
        """Non-2xx response from jobs endpoint should raise CicdUpstreamError."""
        http_client = MagicMock()
        resp = MagicMock()
        resp.is_success = False
        resp.status_code = 500
        http_client.get = AsyncMock(return_value=resp)

        backend = GitHubActionsJobBackend(github_token="test-token", http=http_client)

        with pytest.raises(CicdUpstreamError) as exc_info:
            await backend._fetch_jobs("owner", "repo", 123)

        assert "status=500" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_non_2xx_on_log_fetch_appends_error_message(self) -> None:
        """Non-2xx response from logs endpoint should append error message, not crash."""
        http_client = MagicMock()
        resp = MagicMock()
        resp.is_success = False
        resp.status_code = 404
        http_client.get = AsyncMock(return_value=resp)

        backend = GitHubActionsJobBackend(github_token="test-token", http=http_client)

        output_parts: list[str] = []
        total_bytes = 0
        max_bytes = 256 * 1024

        result_parts, result_bytes = await backend._append_job_log(
            "owner", "repo", 123, output_parts, total_bytes, max_bytes
        )

        assert any("(log fetch failed: HTTP 404)" in part for part in result_parts)

    @pytest.mark.asyncio
    async def test_http_status_error_appended_not_raised(self) -> None:
        """HTTPStatusError from log fetch should be caught and appended, not re-raised."""
        import httpx

        http_client = MagicMock()
        http_client.get = AsyncMock(
            side_effect=httpx.HTTPStatusError(
                "error", request=MagicMock(), response=MagicMock()
            )
        )

        backend = GitHubActionsJobBackend(github_token="test-token", http=http_client)

        output_parts: list[str] = []
        total_bytes = 0
        max_bytes = 256 * 1024

        result_parts, result_bytes = await backend._append_job_log(
            "owner", "repo", 123, output_parts, total_bytes, max_bytes
        )

        assert any("(log fetch error:" in part for part in result_parts)


class TestMaxBytesTruncation:
    """Verify max_bytes truncation on job log retrieval."""

    @pytest.mark.asyncio
    async def test_truncation_applied_when_exceeding_limit(self) -> None:
        """When log exceeds remaining budget, truncation marker is appended."""
        http_client = MagicMock()
        large_text = "x" * 50000
        resp = MagicMock()
        resp.is_success = True
        resp.text = large_text
        http_client.get = AsyncMock(return_value=resp)

        backend = GitHubActionsJobBackend(
            github_token="test-token",
            http=http_client,
            max_log_size_kb=1,
        )

        output_parts: list[str] = ["header\n"]
        total_bytes = len(b"header\n") + 100  # Simulate some header bytes
        max_bytes = 1024  # 1 KB limit

        result_parts, result_bytes = await backend._append_job_log(
            "owner", "repo", 123, output_parts, total_bytes, max_bytes
        )

        assert any("[TRUNCATED:" in part for part in result_parts)
        assert result_bytes >= max_bytes

    @pytest.mark.asyncio
    async def test_no_truncation_when_within_limit(self) -> None:
        """When log fits within remaining budget, no truncation occurs."""
        http_client = MagicMock()
        small_text = "hello world"
        resp = MagicMock()
        resp.is_success = True
        resp.text = small_text
        http_client.get = AsyncMock(return_value=resp)

        backend = GitHubActionsJobBackend(
            github_token="test-token",
            http=http_client,
            max_log_size_kb=1,
        )

        output_parts: list[str] = []
        total_bytes = 0
        max_bytes = 1024

        result_parts, result_bytes = await backend._append_job_log(
            "owner", "repo", 123, output_parts, total_bytes, max_bytes
        )

        assert not any("[TRUNCATED:" in part for part in result_parts)
        assert result_bytes < max_bytes

    @pytest.mark.asyncio
    async def test_truncation_preserves_partial_content(self) -> None:
        """Truncated content includes partial text before the truncation marker."""
        http_client = MagicMock()
        long_text = "a" * 10000
        resp = MagicMock()
        resp.is_success = True
        resp.text = long_text
        http_client.get = AsyncMock(return_value=resp)

        backend = GitHubActionsJobBackend(
            github_token="test-token",
            http=http_client,
            max_log_size_kb=1,
        )

        output_parts: list[str] = []
        total_bytes = 0
        max_bytes = 100  # Very tight limit

        result_parts, result_bytes = await backend._append_job_log(
            "owner", "repo", 123, output_parts, total_bytes, max_bytes
        )

        # Should have partial content plus truncation marker
        combined = "".join(result_parts)
        assert "[TRUNCATED:" in combined
        assert "a" in combined  # Partial content preserved

    @pytest.mark.asyncio
    async def test_multiple_jobs_respect_cumulative_budget(self) -> None:
        """Subsequent jobs respect the cumulative byte budget across all jobs."""
        http_client = MagicMock()
        resp = MagicMock()
        resp.is_success = True
        resp.text = "job-log-content"
        http_client.get = AsyncMock(return_value=resp)

        backend = GitHubActionsJobBackend(
            github_token="test-token",
            http=http_client,
            max_log_size_kb=1,
        )

        output_parts: list[str] = []
        total_bytes = 0
        max_bytes = 100  # Tight budget

        # First few jobs fill most of the budget
        for i in range(5):
            output_parts.append(f"job-header-{i}\n")
            total_bytes += len(f"job-header-{i}\n".encode())

        # Subsequent jobs should hit truncation
        for i in range(5):
            truncated, total_bytes = await backend._append_job_log(
                "owner", "repo", i, output_parts, total_bytes, max_bytes
            )
            if total_bytes >= max_bytes:
                break

        # At least one truncation should have occurred
        assert any("[TRUNCATED:" in part for part in output_parts)
