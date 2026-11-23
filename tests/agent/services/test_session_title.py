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
    assert result.stale is False
    ctx.session.set_title.assert_called_once_with("My Session Title", target=None)


@pytest.mark.asyncio
async def test_generate_success_log_carries_no_title_text(
    caplog: pytest.LogCaptureFixture,
) -> None:
    """REQ-005 / AC-2: the success log names ids only, never the title text."""
    import logging

    from agent.services.session_title import SessionTitleService

    ctx = MagicMock()
    ctx.session.session_id = 11
    ctx.session.generation = 2
    mock_resp = MagicMock()
    mock_resp.raise_for_status = MagicMock()
    mock_resp.content = orjson.dumps(
        {"choices": [{"message": {"content": "Secret User Title"}}]}
    )
    ctx.services_required.http.post = AsyncMock(return_value=mock_resp)
    with caplog.at_level(logging.INFO, logger="agent.services.session_title"):
        await SessionTitleService().generate(ctx, "hello")
    assert "Secret User Title" not in caplog.text
    assert "session=11" in caplog.text


@pytest.mark.asyncio
async def test_generate_stale_target_refused_stale_result_and_redacted_log(
    caplog: pytest.LogCaptureFixture,
) -> None:
    """REQ-004: a refused (stale) write surfaces as stale=True with a
    title-free rejection log."""
    import logging

    from agent.services.session_title import SessionTitleService

    ctx = MagicMock()
    ctx.session.set_title.return_value = False
    mock_resp = MagicMock()
    mock_resp.raise_for_status = MagicMock()
    mock_resp.content = orjson.dumps(
        {"choices": [{"message": {"content": "Stale Title Text"}}]}
    )
    ctx.services_required.http.post = AsyncMock(return_value=mock_resp)
    with caplog.at_level(logging.WARNING, logger="agent.services.session_title"):
        result = await SessionTitleService().generate(ctx, "hello")
    assert result.stale is True
    ctx.session.set_title.assert_called_once()
    assert "refused" in caplog.text
    assert "Stale Title Text" not in caplog.text


@pytest.mark.asyncio
async def test_generate_writes_to_captured_target() -> None:
    """REQ-004: the captured context-variable target is passed to set_title."""
    from agent.conversation_state_manager import (
        capture_session_target,
        current_session_target,
    )
    from agent.services.session_title import SessionTitleService
    from agent.session import SessionTarget

    ctx = MagicMock()
    ctx.session.set_title.return_value = True
    mock_resp = MagicMock()
    mock_resp.raise_for_status = MagicMock()
    mock_resp.content = orjson.dumps(
        {"choices": [{"message": {"content": "My Session Title"}}]}
    )
    ctx.services_required.http.post = AsyncMock(return_value=mock_resp)

    target = SessionTarget(session_id=7, generation=3)
    token = capture_session_target(target)
    try:
        result = await SessionTitleService().generate(ctx, "hello")
    finally:
        current_session_target.reset(token)

    assert result.stale is False
    ctx.session.set_title.assert_called_once_with("My Session Title", target=target)


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
