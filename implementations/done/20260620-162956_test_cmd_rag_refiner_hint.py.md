# Implementation: test_cmd_rag_refiner_hint.py

## Goal
Create `tests/test_cmd_rag_refiner_hint.py` to verify that `_cmd_rag()` writes the
`[warn] refiner fallback: <reason>` hint line when `pipeline.last_stage_results` contains
a Refiner entry with `status == "fallback"`, and does NOT write the hint when refiner
succeeded or was not used.

## Scope
- New file: `tests/test_cmd_rag_refiner_hint.py`
- Tests for:
  1. Refiner fallback → hint written to output
  2. Refiner success → no hint written
  3. Refiner not used (no Refiner entry in last_stage_results) → no hint written
  4. Fallback reason included verbatim in hint

## Assumptions
- `IngestCommand` (or the class that owns `_cmd_rag()`) can be instantiated with mocks
  for `_out`, `pipeline`, and `AgentContext`
- `pipeline.last_stage_results` is a `list[StageResult]` (TypedDict) — set directly on mock
- `pipeline.augment()` returns `"context text"` or `""` for these tests
- `pipeline.last_timings` = `{}` (empty, not under test)
- `pipeline.get_diagnostics()` returns `{}` to avoid DiagnosticsManager interaction
- `ctx.diagnostics` = `None` to skip diagnostics persistence path

## Implementation

### Target file
`tests/test_cmd_rag_refiner_hint.py`

### Procedure
Write a pytest test file with 4 test cases using `AsyncMock` for `pipeline.augment()`.

### Method
New test file. Use `unittest.mock.MagicMock` + `AsyncMock` to inject a mock pipeline.

### Details

```python
"""tests/test_cmd_rag_refiner_hint.py
Verifies that _cmd_rag() emits the [warn] refiner fallback hint line when appropriate.
"""
from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest

from rag.stage import StageResult


def _make_stage_result(
    stage_name: str,
    status: str,
    fallback_reason: str | None = None,
    elapsed_seconds: float = 0.1,
) -> StageResult:
    return StageResult(
        stage_name=stage_name,
        status=status,
        elapsed_seconds=elapsed_seconds,
        fallback_reason=fallback_reason,
    )


def _make_pipeline(context: str = "result text", stage_results=None) -> MagicMock:
    pipeline = MagicMock()
    pipeline.augment = AsyncMock(return_value=context)
    pipeline.last_stage_results = stage_results or []
    pipeline.last_timings = {}
    pipeline.get_diagnostics = MagicMock(return_value={})
    return pipeline


class FakeOut:
    def __init__(self):
        self.lines: list[str] = []

    def write(self, msg: str) -> None:
        self.lines.append(msg)

    def write_debug_rag(self, *args, **kwargs) -> None:
        pass


@pytest.mark.asyncio
async def test_refiner_fallback_hint_written(monkeypatch) -> None:
    """When Refiner status=fallback, hint line is written."""
    out = FakeOut()
    pipeline = _make_pipeline(
        stage_results=[
            _make_stage_result("Refiner", "fallback", "refiner_returned_empty")
        ]
    )
    # Invoke _cmd_rag() via the command class (adjust import to match project structure)
    from agent.commands.cmd_ingest import IngestCommand  # adjust import as needed
    cmd = IngestCommand.__new__(IngestCommand)
    cmd._out = out
    ctx = MagicMock()
    ctx.diagnostics = None
    ctx.http_client = MagicMock()
    ctx.config = MagicMock()
    ctx.config.use_search = True
    monkeypatch.setattr(cmd, "_build_pipeline", lambda ctx: pipeline)

    await cmd._cmd_rag("search test query", ctx)

    hint_lines = [l for l in out.lines if "[warn] refiner fallback" in l]
    assert len(hint_lines) == 1
    assert "refiner_returned_empty" in hint_lines[0]


@pytest.mark.asyncio
async def test_no_hint_when_refiner_succeeded(monkeypatch) -> None:
    """When Refiner status=success, no hint line is written."""
    out = FakeOut()
    pipeline = _make_pipeline(
        stage_results=[
            _make_stage_result("Refiner", "success")
        ]
    )
    from agent.commands.cmd_ingest import IngestCommand
    cmd = IngestCommand.__new__(IngestCommand)
    cmd._out = out
    ctx = MagicMock()
    ctx.diagnostics = None
    ctx.http_client = MagicMock()
    ctx.config = MagicMock()
    ctx.config.use_search = True
    monkeypatch.setattr(cmd, "_build_pipeline", lambda ctx: pipeline)

    await cmd._cmd_rag("search test query", ctx)

    hint_lines = [l for l in out.lines if "[warn] refiner fallback" in l]
    assert len(hint_lines) == 0


@pytest.mark.asyncio
async def test_no_hint_when_refiner_not_used(monkeypatch) -> None:
    """When no Refiner entry in last_stage_results, no hint is written."""
    out = FakeOut()
    pipeline = _make_pipeline(stage_results=[])

    from agent.commands.cmd_ingest import IngestCommand
    cmd = IngestCommand.__new__(IngestCommand)
    cmd._out = out
    ctx = MagicMock()
    ctx.diagnostics = None
    ctx.http_client = MagicMock()
    ctx.config = MagicMock()
    ctx.config.use_search = True
    monkeypatch.setattr(cmd, "_build_pipeline", lambda ctx: pipeline)

    await cmd._cmd_rag("search test query", ctx)

    hint_lines = [l for l in out.lines if "[warn] refiner fallback" in l]
    assert len(hint_lines) == 0


@pytest.mark.asyncio
async def test_fallback_reason_in_hint(monkeypatch) -> None:
    """Fallback reason string appears verbatim in the hint line."""
    out = FakeOut()
    reason = "refiner_exception: HTTPStatusError 429"
    pipeline = _make_pipeline(
        stage_results=[
            _make_stage_result("Refiner", "fallback", reason)
        ]
    )
    from agent.commands.cmd_ingest import IngestCommand
    cmd = IngestCommand.__new__(IngestCommand)
    cmd._out = out
    ctx = MagicMock()
    ctx.diagnostics = None
    ctx.http_client = MagicMock()
    ctx.config = MagicMock()
    ctx.config.use_search = True
    monkeypatch.setattr(cmd, "_build_pipeline", lambda ctx: pipeline)

    await cmd._cmd_rag("search test query", ctx)

    hint_lines = [l for l in out.lines if "[warn] refiner fallback" in l]
    assert len(hint_lines) == 1
    assert reason in hint_lines[0]
```

**Note:** The exact import path for `IngestCommand` and the `_build_pipeline` injection point
must be verified against the actual class structure in `scripts/agent/commands/cmd_ingest.py`.
Adjust `monkeypatch` targets as needed during implementation.

## Validation plan

| Check | Command | Expected |
|---|---|---|
| All 4 tests pass | `uv run pytest tests/test_cmd_rag_refiner_hint.py -v` | 4 passed |
| Lint | `uv run ruff check tests/test_cmd_rag_refiner_hint.py` | 0 errors |
| Type check | `uv run mypy tests/test_cmd_rag_refiner_hint.py` | no errors |
| Full suite | `uv run pytest -q` | no new failures |
