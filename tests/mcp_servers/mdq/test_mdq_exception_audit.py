"""tests/mcp_servers/mdq/test_mdq_exception_audit.py

Exactly-one-audit tests for mdq-mcp (REQ-005, AC-3): every authenticated call emits
one record from the single emission boundary, including the paths that emit none today.

Records are read from the audit sink the boundary writes to, so the emission sites are
observable rather than stubbed. The code assertions are in
`tests/mcp_servers/mdq/test_mdq_exception_handlers.py` (seq 01's companion); this file
counts records only, so the two do not duplicate the same assertion.

Written in Phase 1 before the production change. The two paths that emit nothing today
are the malformed-execution-context path and the refused-tool path; the other paths
already emit one record and stay as the behavior lock.
"""

from __future__ import annotations

import json
import os
from collections.abc import Callable
from pathlib import Path
from tempfile import mkstemp
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi.testclient import TestClient
from mcp_servers.mdq import mdq_server
from mcp_servers.mdq.mdq_models import (
    MdqAuthorizationError,
    MdqConsistencyError,
    MdqDatabaseError,
    MdqIndexNotReadyError,
    MdqNotFoundError,
    MdqServiceError,
    MdqValidationError,
)
from mcp_servers.mdq.mdq_service import MdqService

from tests.mcp_servers._auth_headers import MCP_TEST_AUTH_HEADERS
from tests.mcp_servers.mdq._startup import make_startup

# Every MDQ exception class, each with the transport status its handler returns.
ERROR_CLASSES: list[tuple[type[Exception], int]] = [
    (MdqValidationError, 400),
    (MdqAuthorizationError, 403),
    (MdqNotFoundError, 404),
    (MdqIndexNotReadyError, 503),
    (MdqDatabaseError, 503),
    (MdqConsistencyError, 500),
    (MdqServiceError, 500),
]


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
def audit_records(
    monkeypatch: pytest.MonkeyPatch, service: MdqService
) -> Callable[[], list[dict[str, Any]]]:
    """Capture the records the emission boundary writes, without stubbing the emission."""
    sink = MagicMock()
    monkeypatch.setattr(mdq_server, "logger", sink)
    monkeypatch.setattr(mdq_server, "_service", service)

    def records() -> list[dict[str, Any]]:
        # Non-record info lines are skipped so the count is the count of audit records.
        parsed: list[dict[str, Any]] = []
        for call in sink.info.call_args_list:
            try:
                parsed.append(json.loads(call.args[0]))
            except (json.JSONDecodeError, IndexError):
                continue
        return parsed

    return records


def _client() -> TestClient:
    return TestClient(mdq_server.app, headers=MCP_TEST_AUTH_HEADERS)


class TestExactlyOneRecordPerCall:
    """AC-3: one record per authenticated call, from one boundary."""

    def test_the_success_path_emits_exactly_one_record(
        self, audit_records: Callable[[], list[dict[str, Any]]]
    ) -> None:
        handler = AsyncMock(return_value="ok")
        with patch.dict(mdq_server._DISPATCH_TABLE, {"search_docs": handler}):
            _client().post("/v1/call_tool", json={"name": "search_docs", "args": {}})

        assert len(audit_records()) == 1

    @pytest.mark.parametrize(("exc_class", "status"), ERROR_CLASSES)
    def test_every_error_class_emits_exactly_one_record(
        self,
        audit_records: Callable[[], list[dict[str, Any]]],
        exc_class: type[Exception],
        status: int,
    ) -> None:
        handler = AsyncMock(side_effect=exc_class("failure"))
        with patch.dict(mdq_server._DISPATCH_TABLE, {"search_docs": handler}):
            response = _client().post(
                "/v1/call_tool", json={"name": "search_docs", "args": {}}
            )

        # The four classes caught in `call_tool()` stay tool-level (HTTP 200); the rest
        # reach the transport handler, so the status is the handler's.
        if exc_class in (
            MdqValidationError,
            MdqAuthorizationError,
            MdqNotFoundError,
            MdqIndexNotReadyError,
        ):
            assert response.status_code == 200
        else:
            assert response.status_code == status

        assert len(audit_records()) == 1, (
            f"{exc_class.__name__} must produce exactly one record from the boundary"
        )

    def test_the_malformed_execution_context_path_emits_exactly_one_record(
        self, audit_records: Callable[[], list[dict[str, Any]]]
    ) -> None:
        # A claimed mode that disagrees with the resolved mode is refused before dispatch,
        # and this branch emits nothing today. `search_docs` resolves to `applied`, so the
        # `preview` claim is the disagreement.
        handler = AsyncMock(return_value="ok")
        with patch.dict(mdq_server._DISPATCH_TABLE, {"search_docs": handler}):
            response = _client().post(
                "/v1/call_tool",
                json={"name": "search_docs", "args": {}},
                headers={"X-Execution-Mode": "preview"},
            )

        assert response.json()["is_error"] is True
        assert handler.await_count == 0
        assert len(audit_records()) == 1, (
            "the malformed-execution-context path emits no record today; AC-3 requires one"
        )

    def test_the_refused_tool_path_emits_exactly_one_record(
        self, audit_records: Callable[[], list[dict[str, Any]]], service: MdqService
    ) -> None:
        service._allowed_dirs = []
        handler = AsyncMock(return_value="ok")
        with patch.dict(mdq_server._DISPATCH_TABLE, {"search_docs": handler}):
            response = _client().post(
                "/v1/call_tool", json={"name": "search_docs", "args": {}}
            )

        assert len(audit_records()) == 1
        assert response.json()["is_error"] is True
