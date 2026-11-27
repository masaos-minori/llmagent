"""Edge case tests for MCP CICD job log retrieval and security guards.

Requirement source: `issues/done/20261119-141110_mcpci003_cicd-log-streaming-bounds.md`
(REQ-001..REQ-006). The pins that recorded the pre-change behavior — embedded failure
strings and an overrun-allowing budget — are replaced by the contract assertions below.
The jobs-path fail-fast pins and the token-masking pins are characterization.
"""

from unittest.mock import AsyncMock, MagicMock

import httpx
import pytest
from mcp_servers.address_policy import KIND_PROHIBITED_ADDRESS, AddressRejectedError
from mcp_servers.bounded_fetch import (
    TRUNCATED_BY_DECODED,
    TRUNCATED_BY_RAW,
    BoundedFetchResult,
    FetchContentTypeError,
    FetchRedirectError,
    FetchStatusError,
    FetchUnsupportedEncodingError,
)
from mcp_servers.cicd import cicd_service_github_actions_job as job_module
from mcp_servers.cicd.cicd_models import (
    LOG_ERROR_CODES,
    LOG_FETCH_TIMEOUT_S,
    MAX_DECOMPRESSED_BYTES,
    MAX_RAW_DOWNLOAD_BYTES,
    MAX_REDIRECTS,
    TRUNCATION_REASONS,
    CicdUpstreamError,
    LogFetchResult,
)

pytestmark = pytest.mark.contract

# The jobs API call still uses the injected client; only the log download goes
# through the bounded helper, so the fake replaces the helper, not the client.
_FAKE_CLIENT = MagicMock()


def _make_backend(
    job_ids: list[int],
    max_log_size_kb: int = 256,
) -> job_module.GitHubActionsJobBackend:
    """Backend whose log path is served by the fake helper, not by a live client."""
    backend = job_module.GitHubActionsJobBackend(
        github_token="test-token",
        http=_FAKE_CLIENT,
        max_log_size_kb=max_log_size_kb,
    )
    # The jobs API call keeps the injected client; the tests pin the log path, so the
    # jobs payload is supplied without a live response object.
    backend._fetch_jobs = AsyncMock(return_value=_jobs_payload(job_ids))
    return backend


def _fake_fetch(body: bytes, truncated_by: str | None) -> AsyncMock:
    """Replace `fetch_bounded` with a fake that records the limits it was given."""
    calls: list[dict] = []

    async def _fetch(url: str, **kwargs) -> BoundedFetchResult:
        calls.append({"url": url, "kwargs": kwargs})
        return BoundedFetchResult(
            final_url=url,
            status_code=200,
            content_type="text/plain",
            charset=None,
            body=body,
            download_truncated=truncated_by is not None,
            truncated_by=truncated_by,
            declared_length=len(body),
            elapsed_sec=0.0,
        )

    fake = AsyncMock(side_effect=_fetch)
    fake.calls = calls
    return fake


def _jobs_payload(job_ids: list[int]) -> dict:
    return {
        "jobs": [
            {"id": job_id, "name": f"job-{job_id}", "status": "completed", "steps": []}
            for job_id in job_ids
        ]
    }


class TestNon2xxFailFast:
    """Verify non-2xx responses cause fail-fast behavior."""

    @pytest.mark.characterization
    @pytest.mark.asyncio
    async def test_non_2xx_on_jobs_fetch_raises_upstream_error(self) -> None:
        """Non-2xx response from jobs endpoint should raise CicdUpstreamError."""
        http_client = MagicMock()
        resp = MagicMock()
        resp.is_success = False
        resp.status_code = 500
        http_client.get = AsyncMock(return_value=resp)

        backend = job_module.GitHubActionsJobBackend(
            github_token="test-token", http=http_client
        )

        with pytest.raises(CicdUpstreamError) as exc_info:
            await backend._fetch_jobs("owner", "repo", 123)

        assert "status=500" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_non_2xx_on_log_fetch_is_a_per_job_error_code(
        self,
        monkeypatch,
    ) -> None:
        """A non-2xx log response is a per-job error code, not output text (REQ-004)."""
        backend = _make_backend([1])
        fake = _fake_fetch(b"", None)

        async def _raise(url: str, **kwargs) -> BoundedFetchResult:
            raise FetchStatusError(404, "client_error")

        fake.side_effect = _raise
        monkeypatch.setattr(job_module, "fetch_bounded", fake)

        result = await backend.get_workflow_logs("owner", "repo", 123)
        assert result.jobs[0].status == "failed"
        assert result.jobs[0].error_code == "http_status"
        assert "log fetch failed" not in result.output
        assert "HTTP 404" not in result.output


class TestBoundedStreaming:
    """The log download goes through the shared helper under the independent limits."""

    @pytest.mark.asyncio
    async def test_log_fetch_uses_the_independent_limits(self, monkeypatch) -> None:
        backend = _make_backend([1], max_log_size_kb=1)
        fake = _fake_fetch(b"log line\n", None)
        monkeypatch.setattr(job_module, "fetch_bounded", fake)

        await backend.get_workflow_logs("owner", "repo", 1)

        kwargs = fake.calls[0]["kwargs"]
        limits = kwargs["limits"]
        assert limits.raw_bytes == MAX_RAW_DOWNLOAD_BYTES
        assert limits.decoded_bytes == MAX_DECOMPRESSED_BYTES
        # The parser-input limit is the remaining output budget, not the raw limit.
        assert limits.parser_input_bytes <= MAX_DECOMPRESSED_BYTES
        assert limits.returned_bytes == 1024
        assert kwargs["max_redirects"] == MAX_REDIRECTS
        assert kwargs["timeout_sec"] == LOG_FETCH_TIMEOUT_S
        assert kwargs["allowed_content_types"] == frozenset({"text/plain"})

    @pytest.mark.asyncio
    async def test_untrusted_redirect_host_is_rejected_by_the_host_policy(
        self,
    ) -> None:
        """A hop to a host outside the trusted GitHub log hosts is rejected (AC-3)."""
        with pytest.raises(AddressRejectedError):
            job_module.trusted_log_host("https://evil.example.com/logs")

        assert (
            job_module.trusted_log_host("https://api.github.com/x") == "api.github.com"
        )
        assert (
            job_module.trusted_log_host(
                "https://productionresultssa9.blob.core.windows.net/x"
            )
            == "productionresultssa9.blob.core.windows.net"
        )

    @pytest.mark.asyncio
    async def test_host_policy_rejects_a_url_without_a_host(self) -> None:
        with pytest.raises(AddressRejectedError):
            job_module.trusted_log_host("https:///logs")

    @pytest.mark.asyncio
    async def test_host_rejection_is_its_own_error_code(self, monkeypatch) -> None:
        """The helper's rejection reaches the result as `address_rejected`, not as text."""
        backend = _make_backend([1])
        monkeypatch.setattr(
            job_module,
            "trusted_log_host",
            lambda url: (_ for _ in ()).throw(
                AddressRejectedError("evil.example.com", KIND_PROHIBITED_ADDRESS)
            ),
        )

        async def _fetch(url: str, **kwargs) -> BoundedFetchResult:
            # Run the policy the backend passed, so the rejection travels through the
            # helper unchanged, as the contract says it must.
            kwargs["host_policy"](url)
            raise AssertionError("the rejected hop must not return a body")

        fake = AsyncMock(side_effect=_fetch)
        monkeypatch.setattr(job_module, "fetch_bounded", fake)

        result = await backend.get_workflow_logs("owner", "repo", 1)
        assert result.jobs[0].status == "failed"
        assert result.jobs[0].error_code == "address_rejected"
        assert "evil" not in result.output

    @pytest.mark.asyncio
    async def test_helper_errors_map_to_stable_error_codes(self, monkeypatch) -> None:
        """Raw transport text never reaches the result; only the code does (REQ-004)."""
        backend = _make_backend([1])
        cases = [
            (FetchRedirectError("more than 3 redirects"), "redirect"),
            (FetchContentTypeError("text/html"), "content_type"),
            (FetchUnsupportedEncodingError("br"), "content_encoding"),
            (httpx.ConnectError("connection refused"), "transport"),
        ]
        for exc, code in cases:
            fake = _fake_fetch(b"", None)

            async def _raise(url: str, **kwargs) -> BoundedFetchResult:
                raise exc

            fake.side_effect = _raise
            monkeypatch.setattr(job_module, "fetch_bounded", fake)

            result = await backend.get_workflow_logs("owner", "repo", 1)
            assert result.jobs[0].status == "failed"
            assert result.jobs[0].error_code == code
            assert code in LOG_ERROR_CODES
            assert str(exc) not in result.output

    @pytest.mark.asyncio
    async def test_truncation_reason_comes_from_the_helper(self, monkeypatch) -> None:
        backend = _make_backend([1], max_log_size_kb=1)
        fake = _fake_fetch(b"x" * 1024, TRUNCATED_BY_RAW)
        monkeypatch.setattr(job_module, "fetch_bounded", fake)

        result = await backend.get_workflow_logs("owner", "repo", 1)
        assert result.totals.truncation_reason in TRUNCATION_REASONS
        assert result.jobs[0].truncated is True

    @pytest.mark.asyncio
    async def test_compressed_and_chunked_body_is_counted_after_decoding(
        self,
        monkeypatch,
    ) -> None:
        """The helper hands decoded bytes; the budget is counted on those bytes (AC-1)."""
        backend = _make_backend([1], max_log_size_kb=1)
        decoded = "x" * 900
        fake = _fake_fetch(decoded.encode(), TRUNCATED_BY_DECODED)
        monkeypatch.setattr(job_module, "fetch_bounded", fake)

        result = await backend.get_workflow_logs("owner", "repo", 1)
        assert len(result.output.encode()) <= 1024
        assert result.totals.downloaded_bytes == len(decoded.encode())


class TestExactByteBudget:
    """The final output never exceeds the budget, headers and markers included."""

    @pytest.mark.asyncio
    async def test_output_never_exceeds_the_budget(self, monkeypatch) -> None:
        backend = _make_backend([1], max_log_size_kb=1)
        fake = _fake_fetch(b"x" * 4096, TRUNCATED_BY_RAW)
        monkeypatch.setattr(job_module, "fetch_bounded", fake)

        result = await backend.get_workflow_logs("owner", "repo", 1)
        assert len(result.output.encode()) <= 1024
        assert result.totals.visible_bytes == len(result.output.encode())
        assert "[TRUNCATED:" in result.output

    @pytest.mark.asyncio
    async def test_header_only_exhaustion_skips_the_job(self, monkeypatch) -> None:
        """A job whose header no longer fits is not appended (REQ-003)."""
        backend = _make_backend([1], max_log_size_kb=1)
        fake = _fake_fetch(b"", None)
        monkeypatch.setattr(job_module, "fetch_bounded", fake)

        jobs = {
            "jobs": [{"id": 1, "name": "a" * 2000, "status": "completed", "steps": []}]
        }
        monkeypatch.setattr(backend, "_fetch_jobs", AsyncMock(return_value=jobs))

        result = await backend.get_workflow_logs("owner", "repo", 1)
        assert result.jobs[0].status == "skipped"
        assert result.jobs[0].included_bytes == 0
        assert result.output == ""
        assert result.totals.truncation_reason == "output_budget"

    @pytest.mark.asyncio
    async def test_utf8_truncation_keeps_complete_characters(self, monkeypatch) -> None:
        """No replacement character appears at the budget edge (AC-2)."""
        backend = _make_backend([1], max_log_size_kb=1)
        # A multi-byte character straddles the cut point.
        body = ("あ" * 400).encode()
        fake = _fake_fetch(body, TRUNCATED_BY_RAW)
        monkeypatch.setattr(job_module, "fetch_bounded", fake)

        result = await backend.get_workflow_logs("owner", "repo", 1)
        assert "\ufffd" not in result.output
        assert len(result.output.encode()) <= 1024
        assert result.jobs[0].truncated is True

    @pytest.mark.asyncio
    async def test_cut_inside_a_character_drops_the_whole_character(
        self,
        monkeypatch,
    ) -> None:
        """AC-2: a cut that lands inside a character drops it rather than splitting it."""
        backend = _make_backend([1], max_log_size_kb=1)
        # An odd-length name makes the remaining room odd, so the cut lands inside a
        # two-byte character.
        job = {
            "id": 1,
            "name": "x",
            "status": "completed",
            "conclusion": "success",
            "steps": [],
        }
        assert len(backend._format_job_header(job).encode()) % 2 == 1
        monkeypatch.setattr(
            backend, "_fetch_jobs", AsyncMock(return_value={"jobs": [job]})
        )
        fake = _fake_fetch(("あ" * 600).encode(), TRUNCATED_BY_RAW)
        monkeypatch.setattr(job_module, "fetch_bounded", fake)

        result = await backend.get_workflow_logs("owner", "repo", 1)
        header = backend._format_job_header(job)
        text = result.output.split("\n[TRUNCATED:")[0]
        assert "\ufffd" not in result.output
        # The kept log bytes are whole characters only: the straddling one is dropped.
        kept = len(text.encode()) - len(header.encode())
        assert kept % 3 == 0
        assert kept == 933
        assert len(result.output.encode()) <= 1024

    @pytest.mark.asyncio
    async def test_cut_on_a_character_boundary_keeps_everything_before_it(
        self,
        monkeypatch,
    ) -> None:
        backend = _make_backend([1], max_log_size_kb=1)
        job = {
            "id": 1,
            "name": "xxx",
            "status": "completed",
            "conclusion": "success",
            "steps": [],
        }
        # 1024 - header - marker = 933, a multiple of the three-byte character, so the
        # cut lands on a boundary and keeps every character before it.
        assert (1024 - len(backend._format_job_header(job).encode()) - 34) % 3 == 0
        monkeypatch.setattr(
            backend, "_fetch_jobs", AsyncMock(return_value={"jobs": [job]})
        )
        fake = _fake_fetch(("あ" * 600).encode(), TRUNCATED_BY_RAW)
        monkeypatch.setattr(job_module, "fetch_bounded", fake)

        result = await backend.get_workflow_logs("owner", "repo", 1)
        header = backend._format_job_header(job)
        text = result.output.split("\n[TRUNCATED:")[0]
        assert "\ufffd" not in result.output
        assert len(text.encode()) - len(header.encode()) == 933
        assert len(result.output.encode()) <= 1024

    @pytest.mark.asyncio
    async def test_marker_that_no_longer_fits_skips_the_log_text(
        self, monkeypatch
    ) -> None:
        """The marker is inside the budget, so a job with no room for it contributes none."""
        backend = _make_backend([1], max_log_size_kb=1)
        base = {
            "id": 1,
            "name": "",
            "status": "completed",
            "conclusion": "success",
            "steps": [],
        }
        # Leave 24 bytes after the header: less than the marker needs.
        name = "n" * (1000 - len(backend._format_job_header(base).encode()))
        monkeypatch.setattr(
            backend,
            "_fetch_jobs",
            AsyncMock(return_value={"jobs": [{**base, "name": name}]}),
        )
        fake = _fake_fetch(b"x" * 100, TRUNCATED_BY_RAW)
        monkeypatch.setattr(job_module, "fetch_bounded", fake)

        result = await backend.get_workflow_logs("owner", "repo", 1)
        assert result.jobs[0].status == "included"
        assert result.jobs[0].included_bytes == 1000
        assert result.output == backend._format_job_header({**base, "name": name})
        assert result.totals.truncation_reason == "output_budget"

    @pytest.mark.asyncio
    async def test_exact_header_budget_records_the_job_as_included(
        self, monkeypatch
    ) -> None:
        """A budget consumed exactly by the header leaves no room for log text."""
        backend = _make_backend([1], max_log_size_kb=1)
        base = {
            "id": 1,
            "name": "",
            "status": "completed",
            "conclusion": "success",
            "steps": [],
        }
        name = "n" * (1024 - len(backend._format_job_header(base).encode()))
        job = {**base, "name": name}
        monkeypatch.setattr(
            backend, "_fetch_jobs", AsyncMock(return_value={"jobs": [job]})
        )
        fake = _fake_fetch(b"x" * 100, TRUNCATED_BY_RAW)
        monkeypatch.setattr(job_module, "fetch_bounded", fake)

        result = await backend.get_workflow_logs("owner", "repo", 1)
        assert result.jobs[0].status == "included"
        assert result.jobs[0].included_bytes == 1024
        assert result.output == backend._format_job_header(job)
        assert fake.call_count == 0
        assert result.totals.truncation_reason == "output_budget"

    @pytest.mark.asyncio
    async def test_cumulative_budget_across_jobs(self, monkeypatch) -> None:
        backend = _make_backend([1, 2, 3, 4, 5], max_log_size_kb=1)
        fake = _fake_fetch(b"y" * 300, None)
        monkeypatch.setattr(job_module, "fetch_bounded", fake)

        result = await backend.get_workflow_logs("owner", "repo", 1)
        assert len(result.output.encode()) <= 1024
        assert result.totals.included_jobs < result.totals.jobs


class TestPerJobStatusAndTotals:
    """Complete, partial, and total failure are machine-distinguishable (AC-4)."""

    @pytest.mark.asyncio
    async def test_mixed_result_reports_partial_success(self, monkeypatch) -> None:
        backend = _make_backend([1, 2], max_log_size_kb=4)

        async def _fetch(url: str, **kwargs) -> BoundedFetchResult:
            if "jobs/2" in url:
                raise FetchStatusError(500, "server_error")
            return BoundedFetchResult(
                final_url=url,
                status_code=200,
                content_type="text/plain",
                charset=None,
                body=b"log\n",
                download_truncated=False,
                truncated_by=None,
                declared_length=4,
                elapsed_sec=0.0,
            )

        fake = AsyncMock(side_effect=_fetch)
        monkeypatch.setattr(job_module, "fetch_bounded", fake)

        result = await backend.get_workflow_logs("owner", "repo", 1)
        assert result.partial_success is True
        assert result.totals.included_jobs == 1
        assert result.totals.failed_jobs == 1
        assert result.totals.jobs == 2

    @pytest.mark.asyncio
    async def test_all_failed_is_not_a_successful_result(self, monkeypatch) -> None:
        backend = _make_backend([1, 2])

        async def _fetch(url: str, **kwargs) -> BoundedFetchResult:
            raise FetchStatusError(500, "server_error")

        fake = AsyncMock(side_effect=_fetch)
        monkeypatch.setattr(job_module, "fetch_bounded", fake)

        result = await backend.get_workflow_logs("owner", "repo", 1)
        assert result.partial_success is False
        assert result.totals.failed_jobs == 2
        assert all(job.status == "failed" for job in result.jobs)

    @pytest.mark.asyncio
    async def test_no_jobs_returns_the_message(self, monkeypatch) -> None:
        backend = _make_backend([])

        result = await backend.get_workflow_logs("owner", "repo", 99)
        assert isinstance(result, LogFetchResult)
        assert "No jobs found" in result.output
        assert result.totals.jobs == 0


class TestReprMasksToken:
    """Characterization tests locking __repr__'s token-masking behavior (R-4)."""

    @pytest.mark.characterization
    def test_repr_with_token_set_shows_set_not_value(self) -> None:
        """When a token is configured, __repr__ must report 'set' without leaking it."""
        http_client = MagicMock()
        backend = job_module.GitHubActionsJobBackend(
            github_token="super-secret-token", http=http_client
        )

        result = repr(backend)

        assert result == "GitHubActionsJobBackend(token='set')"
        assert "super-secret-token" not in result

    @pytest.mark.characterization
    def test_repr_with_empty_token_shows_not_set(self) -> None:
        """When no token is configured, __repr__ must report 'not set'."""
        http_client = MagicMock()
        backend = job_module.GitHubActionsJobBackend(github_token="", http=http_client)

        result = repr(backend)

        assert result == "GitHubActionsJobBackend(token='not set')"
