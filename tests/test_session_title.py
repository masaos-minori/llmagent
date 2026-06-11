"""tests/test_session_title.py
Error-path unit tests for SessionTitleService.
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import httpx
import orjson
import pytest


@pytest.mark.asyncio
async def test_generate_no_http_client_raises() -> None:
    from agent.services.exceptions import SessionTitleGenerationError
    from agent.services.session_title import SessionTitleService

    ctx = MagicMock()
    ctx.services.http = None
    with pytest.raises(SessionTitleGenerationError, match="not configured"):
        await SessionTitleService().generate(ctx, "hello")


@pytest.mark.asyncio
async def test_generate_http_request_error_raises() -> None:
    from agent.services.exceptions import SessionTitleGenerationError
    from agent.services.session_title import SessionTitleService

    ctx = MagicMock()
    ctx.services.http.post = AsyncMock(side_effect=httpx.RequestError("timeout"))
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
    ctx.services.http.post = AsyncMock(return_value=mock_resp)
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
    ctx.services.http.post = AsyncMock(return_value=mock_resp)
    with pytest.raises(SessionTitleGenerationError, match="no choices"):
        await SessionTitleService().generate(ctx, "hello")


@pytest.mark.asyncio
async def test_generate_empty_title_raises() -> None:
    from agent.services.exceptions import SessionTitleGenerationError
    from agent.services.session_title import SessionTitleService

    ctx = MagicMock()
    mock_resp = MagicMock()
    mock_resp.raise_for_status = MagicMock()
    mock_resp.content = orjson.dumps({"choices": [{"message": {"content": "  "}}]})
    ctx.services.http.post = AsyncMock(return_value=mock_resp)
    with pytest.raises(SessionTitleGenerationError, match="empty title"):
        await SessionTitleService().generate(ctx, "hello")


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
    ctx.services.http.post = AsyncMock(return_value=mock_resp)
    result = await SessionTitleService().generate(ctx, "hello world")
    assert isinstance(result, SessionTitleResult)
    assert result.title == "My Session Title"
    ctx.session.set_title.assert_called_once_with("My Session Title")
