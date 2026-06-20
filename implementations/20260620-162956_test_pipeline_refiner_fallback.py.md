# Implementation: test_pipeline_refiner_fallback.py

## Goal
Create `tests/test_pipeline_refiner_fallback.py` to verify that `refine_context()`
correctly produces `RefineResult(text=None, reason="refiner_returned_empty")` when
the LLM returns empty/whitespace content, and `RefineResult(text=None, reason="refiner_exception: ...")`
on HTTP/transport/ValueError exceptions.

Also verify that `augment()` emits `logger.info` on refiner fallback.

## Scope
- New file: `tests/test_pipeline_refiner_fallback.py`
- Tests for:
  1. Empty LLM response → `refiner_returned_empty`
  2. Whitespace-only LLM response → `refiner_returned_empty`
  3. `httpx.HTTPStatusError` → `refiner_exception: ...`
  4. `httpx.RequestError` → `refiner_exception: ...`
  5. `ValueError` → `refiner_exception: ...`
  6. `augment()` emits `logger.info` when `refined.text is None` (requires caplog)

## Assumptions
- `refine_context()` is importable from `rag.pipeline_refiner`
- `RagLLM.refine_context()` is the async method that can be mocked
- `RagLLM` can be constructed with a minimal mock or replaced entirely via `unittest.mock.AsyncMock`
- `_extract_chat_content()` on a `""` response returns `""` (confirmed: `.strip()` of `""` is `""`)
- For `augment()` caplog test: use the `RagPipeline` with `use_refiner=True` and mock
  `_augment_refiner()` to return `RefineResult(text=None, reason="refiner_returned_empty")`

## Implementation

### Target file
`tests/test_pipeline_refiner_fallback.py`

### Procedure
Write a pytest test file with 6 test cases.

### Method
New test file. Mock `RagLLM.refine_context()` using `pytest-asyncio` + `unittest.mock.AsyncMock`.

### Details

```python
"""tests/test_pipeline_refiner_fallback.py
Verifies refine_context() fallback paths and augment() logger.info emission.
"""
from __future__ import annotations

import logging
from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest

from rag.pipeline_refiner import RefineResult, refine_context


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
    llm = _make_llm(return_value="   \n\t  ")
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
```

## Validation plan

| Check | Command | Expected |
|---|---|---|
| All tests pass | `uv run pytest tests/test_pipeline_refiner_fallback.py -v` | 6 passed |
| Lint | `uv run ruff check tests/test_pipeline_refiner_fallback.py` | 0 errors |
| Type check | `uv run mypy tests/test_pipeline_refiner_fallback.py` | no errors |
| Full suite | `uv run pytest -q` | no new failures |
