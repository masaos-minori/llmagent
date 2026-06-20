# Implementation: test_fusion_mode_diagnostics.py

## Goal
Create `tests/test_fusion_mode_diagnostics.py` to verify that:
1. `get_diagnostics()["fusion_mode"]` returns `"rrf"` when `use_rrf=True`
2. `get_diagnostics()["fusion_mode"]` returns `"dedup_only"` when `use_rrf=False`
3. `FusionStage.run()` emits `logger.info("FusionStage: dedup-only mode")` when `use_rrf=False`

## Scope
- New file: `tests/test_fusion_mode_diagnostics.py`
- 3 test cases

## Assumptions
- `RagPipeline.get_diagnostics()` is callable without running `augment()`
  (it's safe to call before `run()` — returns defaults)
- `RagPipeline` can be constructed with a minimal mocked config
- `FusionStage` can be constructed with `use_rrf=False` and called with a minimal context
- `pytest` caplog can capture `logging.INFO` from `rag.stages.fusion`

## Implementation

### Target file
`tests/test_fusion_mode_diagnostics.py`

### Procedure
Write 3 test cases.

### Method
New test file using `unittest.mock.MagicMock` and `pytest` caplog.

### Details

```python
"""tests/test_fusion_mode_diagnostics.py
Verifies fusion_mode in get_diagnostics() and FusionStage logger.info.
"""
from __future__ import annotations

import logging

import pytest

from rag.stages.fusion import FusionStage
from rag.stage import PipelineContext


def _make_pipeline(use_rrf: bool):
    """Return a minimal RagPipeline with mocked config."""
    from unittest.mock import MagicMock
    from rag.pipeline import RagPipeline
    pipeline = RagPipeline.__new__(RagPipeline)
    pipeline._cfg = MagicMock()
    pipeline._cfg.use_rrf = use_rrf
    pipeline.last_stage_results = []
    pipeline.last_timings = {}
    pipeline.last_fetch_result = None
    return pipeline


def test_fusion_mode_rrf():
    """use_rrf=True → get_diagnostics()['fusion_mode'] == 'rrf'."""
    pipeline = _make_pipeline(use_rrf=True)
    diag = pipeline.get_diagnostics()
    assert diag["fusion_mode"] == "rrf"


def test_fusion_mode_dedup_only():
    """use_rrf=False → get_diagnostics()['fusion_mode'] == 'dedup_only'."""
    pipeline = _make_pipeline(use_rrf=False)
    diag = pipeline.get_diagnostics()
    assert diag["fusion_mode"] == "dedup_only"


def test_fusion_stage_logs_info_on_dedup(caplog):
    """FusionStage.run() with use_rrf=False logs INFO about dedup mode."""
    stage = FusionStage(use_rrf=False)
    ctx = PipelineContext(query="test", search_results=[[]])
    with caplog.at_level(logging.INFO, logger="rag.stages.fusion"):
        stage.run(ctx)
    assert any("dedup-only mode" in r.message for r in caplog.records)
```

## Validation plan

| Check | Command | Expected |
|---|---|---|
| All 3 tests pass | `uv run pytest tests/test_fusion_mode_diagnostics.py -v` | 3 passed |
| Lint | `uv run ruff check tests/test_fusion_mode_diagnostics.py` | 0 errors |
| Type check | `uv run mypy tests/test_fusion_mode_diagnostics.py` | no errors |
| Full suite | `uv run pytest -q` | no new failures |
