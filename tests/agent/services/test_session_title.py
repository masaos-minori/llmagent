"""tests/test_session_title.py
Error-path unit tests for SessionTitleService.
"""

from __future__ import annotations

import logging
import sqlite3
from collections.abc import Generator
from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import orjson
import pytest
from agent.bg_task_monitor import TaskIdentity, bind_task_identity
from agent.session import AgentSession

from tests.agent._config_test_defaults import MIN_DB_CONFIG
from tests.agent.test_session_restore import _SCHEMA_SQL, _FakeSQLiteHelper


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
    ctx.session.set_title.assert_called_once_with("My Session Title", target=None)


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


_TITLE = "Secret Quarterly Plan"


def _llm_ctx(session: AgentSession) -> MagicMock:
    ctx = MagicMock()
    ctx.session = session
    resp = MagicMock()
    resp.raise_for_status = MagicMock()
    resp.content = orjson.dumps({"choices": [{"message": {"content": _TITLE}}]})
    ctx.services_required.http.post = AsyncMock(return_value=resp)
    return ctx


@pytest.fixture
def real_session() -> Generator[tuple[AgentSession, sqlite3.Connection]]:
    conn = sqlite3.connect(":memory:")
    conn.executescript(_SCHEMA_SQL)

    def _make(target: str = "session", db_config=None) -> _FakeSQLiteHelper:  # noqa: ARG001 — factory-signature parity, unused
        return _FakeSQLiteHelper(conn)

    with (
        patch("agent.session.SQLiteHelper", side_effect=_make),
        patch("agent.session_message_repo.SQLiteHelper", side_effect=_make),
    ):
        session = AgentSession(db_config=MIN_DB_CONFIG)
        session.start()
        yield session, conn


def _titles(conn: sqlite3.Connection) -> dict[int, str | None]:
    return dict(conn.execute("SELECT session_id, title FROM sessions").fetchall())


class TestTargetBoundTitle:
    @pytest.mark.asyncio
    async def test_title_lands_on_the_session_that_created_the_task(
        self, real_session: tuple[AgentSession, sqlite3.Connection]
    ) -> None:
        from agent.services.session_title import SessionTitleService

        session, conn = real_session
        sid = session.session_id
        target = session.capture_target()
        identity = TaskIdentity(
            "session_title", "i-1", target.session_id, target.generation
        )

        with bind_task_identity(identity):
            await SessionTitleService().generate(_llm_ctx(session), "hello")

        assert _titles(conn)[sid] == _TITLE

    @pytest.mark.asyncio
    async def test_stale_generation_title_is_rejected_without_a_write(
        self, real_session: tuple[AgentSession, sqlite3.Connection]
    ) -> None:
        from agent.services.session_title import SessionTitleService

        session, conn = real_session
        old_id = session.session_id
        target = session.capture_target()
        identity = TaskIdentity(
            "session_title", "i-1", target.session_id, target.generation
        )
        session.start()  # a transition: new session id and generation
        new_id = session.session_id

        with bind_task_identity(identity):
            result = await SessionTitleService().generate(_llm_ctx(session), "hello")

        assert result.title == _TITLE
        assert _titles(conn)[old_id] is None
        assert _titles(conn)[new_id] is None

    @pytest.mark.asyncio
    async def test_same_id_new_generation_is_also_rejected(
        self, real_session: tuple[AgentSession, sqlite3.Connection]
    ) -> None:
        from agent.services.session_title import SessionTitleService

        session, conn = real_session
        sid = session.session_id
        target = session.capture_target()
        identity = TaskIdentity(
            "session_title", "i-1", target.session_id, target.generation
        )
        session.switch_session(sid)  # reload of the same id advances the generation

        with bind_task_identity(identity):
            await SessionTitleService().generate(_llm_ctx(session), "hello")

        assert _titles(conn)[sid] is None

    @pytest.mark.asyncio
    async def test_title_text_never_reaches_the_log(
        self,
        real_session: tuple[AgentSession, sqlite3.Connection],
        caplog: pytest.LogCaptureFixture,
    ) -> None:
        from agent.services.session_title import SessionTitleService

        session, _ = real_session
        target = session.capture_target()
        identity = TaskIdentity(
            "session_title", "i-1", target.session_id, target.generation
        )

        with (
            caplog.at_level(logging.DEBUG, logger="agent.services.session_title"),
            bind_task_identity(identity),
        ):
            await SessionTitleService().generate(_llm_ctx(session), "hello")
            session.start()
            await SessionTitleService().generate(_llm_ctx(session), "hello")

        assert caplog.records
        assert _TITLE not in caplog.text
        assert "Quarterly" not in caplog.text
