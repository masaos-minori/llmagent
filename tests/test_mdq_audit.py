"""tests/test_mdq_audit.py

Regression tests for mdq_server.py's structured audit-detail block. Verifies
that audit `detail`/`error_type` fields are sourced from the metadata each
`MdqService` method now returns (search_docs, index_paths, refresh_index,
grep_docs) rather than inferred by parsing the tool's formatted output text.
"""

from __future__ import annotations

import asyncio
import os
from pathlib import Path
from tempfile import mkstemp
from unittest.mock import AsyncMock, MagicMock

import httpx
import mcp_servers.mdq.mdq_server as mdq_server_module
import pytest
from mcp_servers.mdq.indexer import index_paths
from mcp_servers.mdq.mdq_models import IndexPathsRequest
from mcp_servers.mdq.mdq_service import MdqService

# ── fixtures ──────────────────────────────────────────────────────────────────


@pytest.fixture
def service(tmp_path: Path) -> MdqService:
    """MdqService with a temp DB path and tmp_path in allowed_dirs."""
    fd, db = mkstemp(suffix=".db", dir=str(tmp_path))
    try:
        svc = MdqService(db_path=db)
        svc._allowed_dirs = [str(tmp_path)]
        return svc
    finally:
        os.close(fd)


@pytest.fixture
def md_file(tmp_path: Path) -> Path:
    """A temporary Markdown file with a real heading/section."""
    f = tmp_path / "test.md"
    f.write_text("# Title\n\nContent here.", encoding="utf-8")
    return f


@pytest.fixture
def mock_audit(monkeypatch: pytest.MonkeyPatch, service: MdqService) -> MagicMock:
    """Patch mdq_server's _audit_log and _service, returning the audit mock."""
    mock = MagicMock()
    monkeypatch.setattr(mdq_server_module, "_audit_log", mock)
    monkeypatch.setattr(mdq_server_module, "_service", service)
    return mock


@pytest.fixture
def client() -> httpx.Client:
    """A sync TestClient-equivalent over the mdq FastAPI app."""
    from fastapi.testclient import TestClient

    return TestClient(mdq_server_module.app)


# ── search_docs ───────────────────────────────────────────────────────────────


class TestSearchDocsAudit:
    def test_result_count_matches_indexed_content(
        self,
        service: MdqService,
        md_file: Path,
        mock_audit: MagicMock,
        client: httpx.Client,
    ) -> None:
        asyncio.run(index_paths(service, IndexPathsRequest(paths=[str(md_file)])))
        response = client.post(
            "/v1/call_tool", json={"name": "search_docs", "args": {"query": "Content"}}
        )
        assert response.status_code == 200
        detail = mock_audit.call_args.kwargs["detail"]
        assert "result_count=1" in detail
        assert "shown_count=1" in detail

    def test_truncated_flag_present_when_results_truncated(
        self,
        service: MdqService,
        tmp_path: Path,
        mock_audit: MagicMock,
        client: httpx.Client,
    ) -> None:
        for i in range(5):
            f = tmp_path / f"doc{i}.md"
            f.write_text(f"# Section {i}\n\nKeyword content here.", encoding="utf-8")
        asyncio.run(index_paths(service, IndexPathsRequest(paths=[str(tmp_path)])))
        service.max_results_limit = 2
        response = client.post(
            "/v1/call_tool", json={"name": "search_docs", "args": {"query": "Keyword"}}
        )
        assert response.status_code == 200
        detail = mock_audit.call_args.kwargs["detail"]
        assert "truncated=true" in detail


# ── index_paths ───────────────────────────────────────────────────────────────


class TestIndexPathsAudit:
    def test_mixed_scenario_counts(
        self,
        service: MdqService,
        tmp_path: Path,
        mock_audit: MagicMock,
        client: httpx.Client,
    ) -> None:
        valid_md = tmp_path / "valid.md"
        valid_md.write_text("# Title\n\nBody.", encoding="utf-8")
        nonexistent = tmp_path / "ghost.md"
        non_md = tmp_path / "notes.txt"
        non_md.write_text("plain text", encoding="utf-8")

        response = client.post(
            "/v1/call_tool",
            json={
                "name": "index_paths",
                "args": {"paths": [str(valid_md), str(nonexistent), str(non_md)]},
            },
        )
        assert response.status_code == 200
        detail = mock_audit.call_args.kwargs["detail"]
        assert "indexed_count=1" in detail
        assert "skipped_count=2" in detail
        assert "failed_count=0" in detail


# ── refresh_index ─────────────────────────────────────────────────────────────


class TestRefreshIndexAudit:
    def test_detail_reports_refresh_summary_counts(
        self,
        service: MdqService,
        md_file: Path,
        mock_audit: MagicMock,
        client: httpx.Client,
    ) -> None:
        response = client.post(
            "/v1/call_tool",
            json={"name": "refresh_index", "args": {"paths": [str(md_file)]}},
        )
        assert response.status_code == 200
        detail = mock_audit.call_args.kwargs["detail"]
        assert "indexed_count=1" in detail
        assert "skipped_count=0" in detail
        assert "deleted_count=0" in detail
        assert "failed_count=0" in detail


# ── grep_docs ─────────────────────────────────────────────────────────────────


class TestGrepDocsAudit:
    def test_match_count_matches_real_matches(
        self,
        service: MdqService,
        tmp_path: Path,
        mock_audit: MagicMock,
        client: httpx.Client,
    ) -> None:
        f = tmp_path / "grep_target.md"
        f.write_text("# Title\n\nfind_me_pattern content.", encoding="utf-8")
        asyncio.run(index_paths(service, IndexPathsRequest(paths=[str(f)])))

        response = client.post(
            "/v1/call_tool",
            json={"name": "grep_docs", "args": {"pattern": "find_me_pattern"}},
        )
        assert response.status_code == 200
        detail = mock_audit.call_args.kwargs["detail"]
        assert "match_count=1" in detail

    def test_truncated_flag_present_when_matches_capped(
        self,
        service: MdqService,
        tmp_path: Path,
        mock_audit: MagicMock,
        client: httpx.Client,
    ) -> None:
        for i in range(5):
            f = tmp_path / f"g{i}.md"
            f.write_text(f"# G{i}\n\nfind_me content.", encoding="utf-8")
        asyncio.run(index_paths(service, IndexPathsRequest(paths=[str(tmp_path)])))
        service.max_grep_matches = 2

        response = client.post(
            "/v1/call_tool",
            json={"name": "grep_docs", "args": {"pattern": "find_me"}},
        )
        assert response.status_code == 200
        detail = mock_audit.call_args.kwargs["detail"]
        assert "truncated=true" in detail


# ── error paths ───────────────────────────────────────────────────────────────


class TestAuthorizationErrorAudit:
    def test_error_type_used_not_embedded_in_detail(
        self,
        service: MdqService,
        mock_audit: MagicMock,
        client: httpx.Client,
    ) -> None:
        response = client.post(
            "/v1/call_tool",
            json={"name": "outline", "args": {"path": "/etc/passwd"}},
        )
        assert response.status_code == 200
        call_kwargs = mock_audit.call_args.kwargs
        assert call_kwargs["error_type"] == "MdqAuthorizationError"
        assert "error_kind=" not in call_kwargs["detail"]


class TestValidationErrorAudit:
    def test_error_type_used_not_embedded_in_detail(
        self,
        service: MdqService,
        mock_audit: MagicMock,
        client: httpx.Client,
    ) -> None:
        service.enable_grep = False
        response = client.post(
            "/v1/call_tool",
            json={"name": "grep_docs", "args": {"pattern": "test"}},
        )
        assert response.status_code == 200
        call_kwargs = mock_audit.call_args.kwargs
        assert call_kwargs["error_type"] == "MdqValidationError"
        assert "error_kind=" not in call_kwargs["detail"]


# ── core regression: audit detail independent of output text wording ─────────


class TestAuditDetailIndependentOfOutputText:
    def test_result_count_sourced_from_metadata_not_text(
        self,
        service: MdqService,
        mock_audit: MagicMock,
        client: httpx.Client,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """Rephrasing search_docs()'s output text must not change the audit
        detail's result_count — it must come from the returned metadata, not
        from parsing the (deliberately numberless) text."""
        rephrased_text = "completely rephrased wording with no numbers"
        metadata = {
            "query_preview": "Content",
            "result_count": 1,
            "shown_count": 1,
            "truncated": False,
            "total_count": 1,
            "duration_ms": 5.0,
        }
        monkeypatch.setattr(
            service,
            "search_docs",
            AsyncMock(return_value=(rephrased_text, metadata)),
        )

        response = client.post(
            "/v1/call_tool", json={"name": "search_docs", "args": {"query": "Content"}}
        )
        assert response.status_code == 200
        assert response.json()["result"] == rephrased_text
        detail = mock_audit.call_args.kwargs["detail"]
        assert "result_count=1" in detail
        assert "shown_count=1" in detail


# ── concurrency isolation ─────────────────────────────────────────────────────


class TestConcurrentAuditIsolation:
    def test_concurrent_requests_do_not_leak_metadata(
        self,
        service: MdqService,
        tmp_path: Path,
        mock_audit: MagicMock,
    ) -> None:
        """Two concurrent search_docs calls with different queries and
        different expected result counts must each produce an audit record
        matching their own request, not the other's — regression guard
        against the mdq-local ContextVar metadata side-channel leaking
        across requests."""
        alpha_dir = tmp_path / "alpha"
        alpha_dir.mkdir()
        for i in range(2):
            (alpha_dir / f"a{i}.md").write_text(
                f"# Alpha {i}\n\nAlphaKeyword content.", encoding="utf-8"
            )
        beta_dir = tmp_path / "beta"
        beta_dir.mkdir()
        for i in range(4):
            (beta_dir / f"b{i}.md").write_text(
                f"# Beta {i}\n\nBetaKeyword content.", encoding="utf-8"
            )
        asyncio.run(index_paths(service, IndexPathsRequest(paths=[str(tmp_path)])))

        async def _run_both() -> tuple[httpx.Response, httpx.Response]:
            transport = httpx.ASGITransport(app=mdq_server_module.app)
            async with httpx.AsyncClient(
                transport=transport, base_url="http://test"
            ) as ac:
                return await asyncio.gather(
                    ac.post(
                        "/v1/call_tool",
                        json={
                            "name": "search_docs",
                            "args": {"query": "AlphaKeyword"},
                        },
                    ),
                    ac.post(
                        "/v1/call_tool",
                        json={"name": "search_docs", "args": {"query": "BetaKeyword"}},
                    ),
                )

        responses = asyncio.run(_run_both())
        assert all(r.status_code == 200 for r in responses)

        alpha_calls = [
            c for c in mock_audit.call_args_list if "AlphaKeyword" in c.kwargs["target"]
        ]
        beta_calls = [
            c for c in mock_audit.call_args_list if "BetaKeyword" in c.kwargs["target"]
        ]
        assert len(alpha_calls) == 1
        assert len(beta_calls) == 1
        assert "result_count=2" in alpha_calls[0].kwargs["detail"]
        assert "result_count=4" in beta_calls[0].kwargs["detail"]


# ── MdqMCPServer.dispatch() ────────────────────────────────────────────────────


class TestMdqMCPServerDispatch:
    def test_dispatch_returns_plain_dispatch_result(
        self, service: MdqService, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """MdqMCPServer.dispatch() must keep the MCPServer base class contract
        (a plain DispatchResult), never leaking the mdq-local
        MdqDispatchResult/metadata wrapper through the base-class interface."""
        from mcp_servers.dispatch import DispatchResult
        from mcp_servers.mdq.mdq_server import MdqMCPServer

        monkeypatch.setattr(mdq_server_module, "_service", service)
        server = MdqMCPServer()
        result = asyncio.run(server.dispatch("stats", {}))
        assert type(result) is DispatchResult
        assert result.is_error is False
        assert "Documents:" in result.output
