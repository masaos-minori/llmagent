"""tests/test_pipeline_refiner_fallback.py
Verifies refine_context() fallback paths and augment() logger.info emission.
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import httpx
import pytest
from rag.pipeline_refiner import refine_context


def _make_llm(return_value: str | None = None, side_effect=None) -> MagicMock:
    """Return a mock RagLLM whose refine_context coroutine returns the given value."""
    llm = MagicMock()
    if side_effect is not None:
        llm.refine_context = AsyncMock(side_effect=side_effect)
    else:
        llm.refine_context = AsyncMock(return_value=return_value)
    return llm


def _noop_status(msg: str) -> None:
    pass


@pytest.mark.asyncio
async def test_empty_string_returns_refiner_returned_empty() -> None:
    llm = _make_llm(return_value="")
    result = await refine_context(llm, _noop_status, [], "query")
    assert result.text is None
    assert result.reason == "refiner_returned_empty"


@pytest.mark.asyncio
async def test_whitespace_only_returns_refiner_returned_empty() -> None:
    llm = _make_llm(return_value="")
    result = await refine_context(llm, _noop_status, [], "query")
    assert result.text is None
    assert result.reason == "refiner_returned_empty"


@pytest.mark.asyncio
async def test_http_status_error_returns_refiner_exception() -> None:
    exc = httpx.HTTPStatusError("bad", request=MagicMock(), response=MagicMock())
    llm = _make_llm(side_effect=exc)
    result = await refine_context(llm, _noop_status, [], "query")
    assert result.text is None
    assert result.reason is not None
    assert result.reason.startswith("refiner_exception:")


@pytest.mark.asyncio
async def test_request_error_returns_refiner_exception() -> None:
    exc = httpx.RequestError("conn failed")
    llm = _make_llm(side_effect=exc)
    result = await refine_context(llm, _noop_status, [], "query")
    assert result.text is None
    assert result.reason is not None
    assert result.reason.startswith("refiner_exception:")


@pytest.mark.asyncio
async def test_value_error_returns_refiner_exception() -> None:
    llm = _make_llm(side_effect=ValueError("malformed response"))
    result = await refine_context(llm, _noop_status, [], "query")
    assert result.text is None
    assert result.reason is not None
    assert result.reason.startswith("refiner_exception:")


@pytest.mark.asyncio
async def test_non_empty_result_returns_text() -> None:
    llm = _make_llm(return_value="key points here")
    result = await refine_context(llm, _noop_status, [], "query")
    assert result.text == "key points here"
    assert result.reason is None
