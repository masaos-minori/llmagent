"""tests/mcp_servers/cicd/test_service_github_actions_error_edges.py

Characterization tests locking two branches of
scripts/mcp_servers/cicd/service_github_actions.py that are not exercised by
tests/mcp_servers/cicd/test_cicd_mcp_service.py:

- GitHubActionsBackend._parse_error_message: the `except (ValueError,
  UnicodeDecodeError)` fallback to `default` when the response body cannot be
  parsed as JSON (parse_http_json raises ValueError on malformed JSON).
- GitHubActionsBackend.trigger_workflow: the non-204 success path (e.g. HTTP
  200), which falls through to `_check_response` (no-op for a 2xx status)
  before returning the same dispatch message as the 204 branch.

These are pre-existing behaviors of the file being refactored under
prompts/04_refactor.md; this file adds coverage only, it does not assert any
new behavior.
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest
from mcp_servers.cicd.cicd_models import CicdAuthorizationError, CicdValidationError
from mcp_servers.cicd.service_github_actions import GitHubActionsBackend


def _make_malformed_body_response(status_code: int) -> MagicMock:
    """Build a mock httpx.Response with a non-JSON body (triggers the ValueError fallback)."""
    resp = MagicMock()
    resp.status_code = status_code
    resp.is_success = 200 <= status_code < 300
    resp.content = b"not valid json"
    resp.headers = {}
    return resp


class TestParseErrorMessageMalformedBody:
    """_parse_error_message must fall back to `default` when the body isn't JSON."""

    def test_422_with_malformed_body_uses_default_message(self) -> None:
        backend = GitHubActionsBackend("token", MagicMock())
        resp = _make_malformed_body_response(422)
        with pytest.raises(CicdValidationError) as exc_info:
            backend._check_response(resp, "test context")
        assert "Unprocessable Entity" in str(exc_info.value)

    def test_403_with_malformed_body_uses_default_message(self) -> None:
        backend = GitHubActionsBackend("token", MagicMock())
        resp = _make_malformed_body_response(403)
        with pytest.raises(CicdAuthorizationError) as exc_info:
            backend._check_response(resp, "test context")
        assert "Access denied" in str(exc_info.value)


class TestTriggerWorkflowNonNoContentSuccess:
    """trigger_workflow must also succeed on a plain 2xx that isn't 204 No Content."""

    @pytest.mark.asyncio
    async def test_200_success_returns_dispatch_message(self) -> None:
        http = AsyncMock()
        resp = MagicMock()
        resp.status_code = 200
        resp.is_success = True
        http.post.return_value = resp
        backend = GitHubActionsBackend("token", http)

        result = await backend.trigger_workflow("owner", "repo", "ci.yml", "main", {})

        assert "dispatched" in result.lower()
        assert "owner/repo" in result
        assert "ci.yml" in result
