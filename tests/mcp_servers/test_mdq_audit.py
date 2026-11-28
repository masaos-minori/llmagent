"""tests/test_mdq_audit.py

Regression tests for mdq_server.py's structured audit-detail block. Verifies
that audit `detail`/`error_type` fields are sourced from the metadata each
`MdqService` method now returns (search_docs, index_paths, refresh_index,
grep_docs) rather than inferred by parsing the tool's formatted output text.
"""

from __future__ import annotations

import asyncio
import json
import os
import uuid
from collections.abc import Callable
from pathlib import Path
from tempfile import mkstemp
from unittest.mock import AsyncMock, MagicMock

import httpx
import mcp_servers.mdq.mdq_server as mdq_server_module
import pytest
from mcp_servers.audit import hash_query_value, path_identifier
from mcp_servers.mdq.indexer import index_paths
from mcp_servers.mdq.mdq_models import IndexPathsRequest
from mcp_servers.mdq.mdq_service import MdqService

from tests.mcp_servers._auth_headers import MCP_TEST_AUTH_HEADERS
from tests.mcp_servers.mdq._startup import make_startup

# ── fixtures ──────────────────────────────────────────────────────────────────


@pytest.fixture
def service(tmp_path: Path) -> MdqService:
    """MdqService with a temp DB path and tmp_path in allowed_dirs."""
    fd, db = mkstemp(suffix=".db", dir=str(tmp_path))
    try:
        svc = MdqService(make_startup(db))
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
def client() -> httpx.Client:
    """A sync TestClient-equivalent over the mdq FastAPI app."""
    from fastapi.testclient import TestClient

    return TestClient(mdq_server_module.app, headers=MCP_TEST_AUTH_HEADERS)


# ── search_docs ───────────────────────────────────────────────────────────────


class TestSearchDocsAudit:
    def test_result_count_matches_indexed_content(
        self,
        service: MdqService,
        md_file: Path,
        persisted_records: Callable[[], list[dict[str, object]]],
        client: httpx.Client,
    ) -> None:
        asyncio.run(index_paths(service, IndexPathsRequest(paths=[str(md_file)])))
        response = client.post(
            "/v1/call_tool", json={"name": "search_docs", "args": {"query": "Content"}}
        )
        assert response.status_code == 200
        detail = _only_record(persisted_records)["detail"]
        assert "result_count=1" in detail
        assert "shown_count=1" in detail

    def test_truncated_flag_present_when_results_truncated(
        self,
        service: MdqService,
        tmp_path: Path,
        persisted_records: Callable[[], list[dict[str, object]]],
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
        detail = _only_record(persisted_records)["detail"]
        assert "truncated=true" in detail


# ── index_paths ───────────────────────────────────────────────────────────────


class TestIndexPathsAudit:
    def test_mixed_scenario_counts(
        self,
        service: MdqService,
        tmp_path: Path,
        persisted_records: Callable[[], list[dict[str, object]]],
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
            headers={"x-idempotency-key": str(uuid.uuid4())},
        )
        assert response.status_code == 200
        detail = _only_record(persisted_records)["detail"]
        assert "indexed_count=1" in detail
        assert "skipped_count=2" in detail
        assert "failed_count=0" in detail


# ── refresh_index ─────────────────────────────────────────────────────────────


class TestRefreshIndexAudit:
    def test_detail_reports_refresh_summary_counts(
        self,
        service: MdqService,
        md_file: Path,
        persisted_records: Callable[[], list[dict[str, object]]],
        client: httpx.Client,
    ) -> None:
        response = client.post(
            "/v1/call_tool",
            json={"name": "refresh_index", "args": {"paths": [str(md_file)]}},
            headers={"x-idempotency-key": str(uuid.uuid4())},
        )
        assert response.status_code == 200
        detail = _only_record(persisted_records)["detail"]
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
        persisted_records: Callable[[], list[dict[str, object]]],
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
        detail = _only_record(persisted_records)["detail"]
        assert "match_count=1" in detail

    def test_truncated_flag_present_when_matches_capped(
        self,
        service: MdqService,
        tmp_path: Path,
        persisted_records: Callable[[], list[dict[str, object]]],
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
        detail = _only_record(persisted_records)["detail"]
        assert "truncated=true" in detail


# ── error paths ───────────────────────────────────────────────────────────────


class TestAuthorizationErrorAudit:
    def test_error_type_used_not_embedded_in_detail(
        self,
        service: MdqService,
        persisted_records: Callable[[], list[dict[str, object]]],
        client: httpx.Client,
    ) -> None:
        response = client.post(
            "/v1/call_tool",
            json={"name": "outline", "args": {"path": "/etc/passwd"}},
        )
        assert response.status_code == 200
        record = _only_record(persisted_records)
        assert record["error_type"] == "authorization_error"
        assert "error_kind=" not in record["detail"]


class TestValidationErrorAudit:
    def test_error_type_used_not_embedded_in_detail(
        self,
        service: MdqService,
        persisted_records: Callable[[], list[dict[str, object]]],
        client: httpx.Client,
    ) -> None:
        service.enable_grep = False
        response = client.post(
            "/v1/call_tool",
            json={"name": "grep_docs", "args": {"pattern": "test"}},
        )
        assert response.status_code == 200
        record = _only_record(persisted_records)
        # Step 3b correction (20261128): the availability gate refuses `grep_docs` before the
        # service runs, so the record names the refusal by code rather than the exception class
        # or the class-derived name.
        assert record["error_type"] == "tool_disabled"
        assert record["outcome"] == "rejected"
        assert "error_kind=" not in record["detail"]


# ── core regression: audit detail independent of output text wording ─────────


class TestAuditDetailIndependentOfOutputText:
    def test_result_count_sourced_from_metadata_not_text(
        self,
        service: MdqService,
        persisted_records: Callable[[], list[dict[str, object]]],
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
        detail = _only_record(persisted_records)["detail"]
        assert "result_count=1" in detail
        assert "shown_count=1" in detail


# ── concurrency isolation ─────────────────────────────────────────────────────


class TestConcurrentAuditIsolation:
    def test_concurrent_requests_do_not_leak_metadata(
        self,
        service: MdqService,
        tmp_path: Path,
        persisted_records: Callable[[], list[dict[str, object]]],
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
                transport=transport,
                base_url="http://test",
                headers=MCP_TEST_AUTH_HEADERS,
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

        # Step 3b correction (20261128): the target is hashed by seq 03, so the calls are
        # selected by the hashed form of each query. Selecting by the raw query would fail
        # for the reason this file guards against, not for the reason this test checks.
        alpha_calls = [
            c
            for c in persisted_records()
            if hash_query_value("AlphaKeyword") in c["target"]
        ]
        beta_calls = [
            c
            for c in persisted_records()
            if hash_query_value("BetaKeyword") in c["target"]
        ]
        assert len(alpha_calls) == 1
        assert len(beta_calls) == 1
        assert "result_count=2" in alpha_calls[0]["detail"]
        assert "result_count=4" in beta_calls[0]["detail"]


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


# ── redaction (AC-4): no raw value reaches a persisted record ───────────────────

CUSTOMER_NAME = "Acme-Corp"
SECRET_VALUE = "sk-live-9f2c1a7b4d8e"
OUTSIDE_ROOT = "/etc/passwd"


@pytest.fixture
def persisted_records(
    monkeypatch: pytest.MonkeyPatch, service: MdqService
) -> Callable[[], list[dict[str, object]]]:
    """Read the records the emission boundary writes.

    The logger is replaced rather than `_audit_log`, because the boundary writes
    through the logger it is given; patching the module-level `_audit_log` would miss
    a record written through `AuditEmission`. Non-record info lines are skipped, so
    the count is the count of audit records.
    """
    sink = MagicMock()
    monkeypatch.setattr(mdq_server_module, "logger", sink)
    monkeypatch.setattr(mdq_server_module, "_service", service)

    def records() -> list[dict[str, object]]:
        parsed: list[dict[str, object]] = []
        for call in sink.info.call_args_list:
            try:
                parsed.append(json.loads(call.args[0]))
            except (json.JSONDecodeError, IndexError):
                continue
        return parsed

    return records


def _only_record(
    records: Callable[[], list[dict[str, object]]],
) -> dict[str, object]:
    """AC-3: one authenticated call writes exactly one record."""
    emitted = records()
    assert len(emitted) == 1, "one authenticated call must write exactly one record"
    return emitted[0]


class TestRedactedTargets:
    """AC-4: the persisted record holds a hashed or root-relative value, never the raw one."""

    def test_query_value_is_persisted_as_a_hash(
        self,
        service: MdqService,
        persisted_records: Callable[[], list[dict[str, object]]],
        client: httpx.Client,
    ) -> None:
        query = f"{CUSTOMER_NAME} {SECRET_VALUE}"
        client.post(
            "/v1/call_tool", json={"name": "search_docs", "args": {"query": query}}
        )

        record = _only_record(persisted_records)
        assert record["target"] == hash_query_value(query)
        persisted = json.dumps(record)
        assert CUSTOMER_NAME not in persisted
        assert SECRET_VALUE not in persisted

    def test_regex_pattern_is_persisted_as_a_hash(
        self,
        service: MdqService,
        persisted_records: Callable[[], list[dict[str, object]]],
        client: httpx.Client,
    ) -> None:
        pattern = f"{SECRET_VALUE}.*{CUSTOMER_NAME}"
        client.post(
            "/v1/call_tool", json={"name": "grep_docs", "args": {"pattern": pattern}}
        )

        record = _only_record(persisted_records)
        assert record["target"] == hash_query_value(pattern)
        persisted = json.dumps(record)
        assert SECRET_VALUE not in persisted
        assert CUSTOMER_NAME not in persisted

    def test_path_inside_an_authorized_root_is_a_root_relative_identifier(
        self,
        service: MdqService,
        md_file: Path,
        tmp_path: Path,
        persisted_records: Callable[[], list[dict[str, object]]],
        client: httpx.Client,
    ) -> None:
        client.post(
            "/v1/call_tool",
            json={"name": "index_paths", "args": {"paths": [str(md_file)]}},
            headers={"x-idempotency-key": str(uuid.uuid4())},
        )

        record = _only_record(persisted_records)
        assert record["target"] == path_identifier(str(md_file), [str(tmp_path)])
        assert str(tmp_path) not in json.dumps(record), (
            "the absolute root is persisted, so the record still exposes an absolute path"
        )

    def test_path_outside_an_authorized_root_is_hashed(
        self,
        service: MdqService,
        persisted_records: Callable[[], list[dict[str, object]]],
        client: httpx.Client,
    ) -> None:
        client.post(
            "/v1/call_tool", json={"name": "outline", "args": {"path": OUTSIDE_ROOT}}
        )

        record = _only_record(persisted_records)
        assert record["target"] == path_identifier(
            OUTSIDE_ROOT, [str(service.allowed_dirs[0])]
        )
        assert OUTSIDE_ROOT not in json.dumps(record)

    def test_chunk_id_is_persisted_as_a_hash(
        self,
        service: MdqService,
        persisted_records: Callable[[], list[dict[str, object]]],
        client: httpx.Client,
    ) -> None:
        chunk_id = SECRET_VALUE + "-chunk"
        client.post(
            "/v1/call_tool", json={"name": "get_chunk", "args": {"chunk_id": chunk_id}}
        )

        record = _only_record(persisted_records)
        assert record["target"] == hash_query_value(chunk_id)
        assert chunk_id not in json.dumps(record)
