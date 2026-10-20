"""tests/test_session_title.py
Error-path unit tests for SessionTitleService.
"""

from __future__ import annotations

import sqlite3
from unittest.mock import AsyncMock, MagicMock

import httpx
import orjson
import pytest


@pytest.mark.asyncio
async def test_generate_no_http_client_raises() -> None:
    from agent.services.exceptions import SessionTitleGenerationError
    from agent.services.session_title import SessionTitleService

    ctx = MagicMock()
    ctx.services_required.http = None
    with pytest.raises(SessionTitleGenerationError, match="not configured"):
        await SessionTitleService().generate(ctx, "hello")


@pytest.mark.asyncio
async def test_generate_http_request_error_raises() -> None:
    from agent.services.exceptions import SessionTitleGenerationError
    from agent.services.session_title import SessionTitleService

    ctx = MagicMock()
    ctx.services_required.http.post = AsyncMock(
        side_effect=httpx.RequestError("timeout")
    )
    with pytest.raises(SessionTitleGenerationError, match="timeout"):
        await SessionTitleService().generate(ctx, "hello")


@pytest.mark.asyncio
async def test_generate_http_status_error_raises() -> None:
    from agent.services.exceptions import SessionTitleGenerationError
    from agent.services.session_title import SessionTitleService

    ctx = MagicMock()
    mock_resp = MagicMock()
    mock_resp.raise_for_status.side_effect = httpx.HTTPStatusError(
        "500", request=MagicMock(), response=MagicMock()
    )
    ctx.services_required.http.post = AsyncMock(return_value=mock_resp)
    with pytest.raises(SessionTitleGenerationError):
        await SessionTitleService().generate(ctx, "hello")


@pytest.mark.asyncio
async def test_generate_empty_choices_raises() -> None:
    from agent.services.exceptions import SessionTitleGenerationError
    from agent.services.session_title import SessionTitleService

    ctx = MagicMock()
    mock_resp = MagicMock()
    mock_resp.raise_for_status = MagicMock()
    mock_resp.content = orjson.dumps({"choices": []})
    ctx.services_required.http.post = AsyncMock(return_value=mock_resp)
    with pytest.raises(SessionTitleGenerationError, match="Missing or empty"):
        await SessionTitleService().generate(ctx, "hello")


@pytest.mark.asyncio
async def test_generate_empty_title_raises() -> None:
    from agent.services.exceptions import SessionTitleGenerationError
    from agent.services.session_title import SessionTitleService

    ctx = MagicMock()
    mock_resp = MagicMock()
    mock_resp.raise_for_status = MagicMock()
    mock_resp.content = orjson.dumps({"choices": [{"message": {"content": "  "}}]})
    ctx.services_required.http.post = AsyncMock(return_value=mock_resp)
    with pytest.raises(SessionTitleGenerationError, match="empty content"):
        await SessionTitleService().generate(ctx, "hello")


@pytest.mark.asyncio
async def test_generate_unexpected_exception_wrapped_as_title_error() -> None:
    from agent.services.exceptions import SessionTitleGenerationError
    from agent.services.session_title import SessionTitleService

    ctx = MagicMock()
    ctx.services_required.http.post = AsyncMock(side_effect=RuntimeError("boom"))
    with pytest.raises(SessionTitleGenerationError, match="Unexpected error"):
        await SessionTitleService().generate(ctx, "hello")


@pytest.mark.asyncio
async def test_generate_db_error_on_set_title_wrapped_as_title_error() -> None:
    from agent.services.exceptions import SessionTitleGenerationError
    from agent.services.session_title import SessionTitleService

    ctx = MagicMock()
    mock_resp = MagicMock()
    mock_resp.raise_for_status = MagicMock()
    mock_resp.content = orjson.dumps(
        {"choices": [{"message": {"content": "My Session Title"}}]}
    )
    ctx.services_required.http.post = AsyncMock(return_value=mock_resp)
    cause = sqlite3.OperationalError("disk I/O error")
    ctx.session.set_title.side_effect = cause
    with pytest.raises(SessionTitleGenerationError, match="DB error") as excinfo:
        await SessionTitleService().generate(ctx, "hello world")
    # The DB failure is converted, and the original error stays reachable as the cause.
    assert excinfo.value.__cause__ is cause


@pytest.mark.asyncio
async def test_generate_success_returns_title() -> None:
    from agent.services.models import SessionTitleResult
    from agent.services.session_title import SessionTitleService

    ctx = MagicMock()
    mock_resp = MagicMock()
    mock_resp.raise_for_status = MagicMock()
    mock_resp.content = orjson.dumps(
        {"choices": [{"message": {"content": "My Session Title"}}]}
    )
    ctx.services_required.http.post = AsyncMock(return_value=mock_resp)
    result = await SessionTitleService().generate(ctx, "hello world")
    assert isinstance(result, SessionTitleResult)
    assert result.title == "My Session Title"
    ctx.session.set_title.assert_called_once_with("My Session Title")


@pytest.mark.asyncio
async def test_generate_sqlite_error_wrapped_as_title_error() -> None:
    from agent.services.exceptions import SessionTitleGenerationError
    from agent.services.session_title import SessionTitleService

    ctx = MagicMock()
    # Succeed the HTTP path so generate reaches ctx.session.set_title(...).
    mock_resp = MagicMock()
    mock_resp.raise_for_status = MagicMock()
    mock_resp.content = orjson.dumps(
        {"choices": [{"message": {"content": "My Session Title"}}]}
    )
    ctx.services_required.http.post = AsyncMock(return_value=mock_resp)
    # Fail the DB write performed by set_title.
    ctx.session.set_title.side_effect = sqlite3.Error("disk I/O error")
    with pytest.raises(SessionTitleGenerationError) as exc_info:
        await SessionTitleService().generate(ctx, "hello")
    # The DB error must be converted AND chained from the original cause.
    assert isinstance(exc_info.value.__cause__, sqlite3.Error)
