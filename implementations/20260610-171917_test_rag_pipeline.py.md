# Implementation: tests/test_rag_*.py — Abnormal Path Test Coverage

## Goal

Add 8 abnormal-path test cases covering the newly fail-fast behaviors introduced in Steps 1–6, ensuring DB failure, parse failure, embedding validation failure, and cache dimension mismatch are all caught and correctly propagate.

---

## Scope

**Target files:**
- `tests/test_rag_utils.py` — NaN/inf/non-numeric embedding float tests
- `tests/test_rag_pipeline_stage.py` — SemanticCache dimension mismatch; DB fetch failure
- `tests/test_rag_stages.py` — MqeParseError, RagExpansionError, RagRerankError propagation
- `tests/test_rag_pipeline.py` — RagPipelineError on DB open failure; empty-hit vs failure distinction

**In:**
- 8 new test functions (one per abnormal case)
- Use `pytest.raises` for all exception assertions
- Mock LLM/HTTP/DB as needed with `unittest.mock.AsyncMock` / `MagicMock`

**Out:**
- No changes to existing test functions
- No new test files — add to existing test modules

---

## Assumptions

1. `RagExpansionError` and `RagRerankError` are defined in `rag/llm.py` (Step 4).
2. `RagPipelineError` is defined in `rag/pipeline.py` (Step 5).
3. `MqeParseError` is defined in `rag/llm.py` (Step 4).
4. `SemanticCache` is in `rag/cache.py` after Step 6.
5. Existing test infrastructure uses `pytest-asyncio` for async tests.

---

## Implementation

### Target file
Multiple (see Scope)

### Procedure

**test_rag_utils.py additions:**

1. `test_floats_to_blob_nan_raises` — `floats_to_blob([1.0, float("nan"), 2.0])` raises `ValueError`
2. `test_floats_to_blob_inf_raises` — `floats_to_blob([float("inf")])` raises `ValueError`
3. `test_floats_to_blob_non_numeric_mid_list_raises` — `floats_to_blob([1.0, "x", 3.0])` raises `ValueError`

**test_rag_pipeline_stage.py additions:**

4. `test_semantic_cache_dimension_mismatch_on_put` — put dim=3, then put dim=4 → `ValueError`
5. `test_semantic_cache_dimension_mismatch_on_lookup` — put dim=3, lookup dim=4 → `ValueError`

**test_rag_stages.py additions:**

6. `test_mqe_stage_malformed_json_raises` — mock LLM returns `"not json"` → stage propagates `RagExpansionError`
7. `test_rerank_stage_http_failure_raises` — mock HTTP returns 500 → stage propagates `RagRerankError`

**test_rag_pipeline.py additions:**

8. `test_augment_db_open_failure_raises` — mock `SQLiteHelper().open()` to raise `sqlite3.OperationalError` → `augment()` raises `RagPipelineError`
9. `test_empty_results_vs_db_failure` — mock DB returning empty rows returns `[]` (not an exception); DB raising `OperationalError` raises `RagPipelineError`

### Method

```python
# test_rag_utils.py
import math
import pytest
from rag.utils import floats_to_blob

def test_floats_to_blob_nan_raises():
    with pytest.raises(ValueError, match="not finite"):
        floats_to_blob([1.0, float("nan"), 2.0])

def test_floats_to_blob_inf_raises():
    with pytest.raises(ValueError, match="not finite"):
        floats_to_blob([float("inf")])

# test_rag_pipeline_stage.py
from rag.cache import SemanticCache

def test_semantic_cache_dimension_mismatch_on_put():
    cache = SemanticCache()
    cache.put([1.0, 2.0, 3.0], "context")
    with pytest.raises(ValueError, match="dimension mismatch"):
        cache.put([1.0, 2.0], "other")

# test_rag_stages.py
import pytest
from unittest.mock import AsyncMock, patch
from rag.llm import RagExpansionError
from rag.stages.mqe import MqeStage
from rag.stage import PipelineContext

@pytest.mark.asyncio
async def test_mqe_stage_malformed_json_raises():
    mock_llm = AsyncMock()
    mock_llm.expand_queries.side_effect = RagExpansionError("bad json")
    stage = MqeStage({"use_mqe": True}, mock_llm)
    ctx = PipelineContext(query="test")
    with pytest.raises(RagExpansionError):
        await stage.run(ctx)
```

### Details

- For `test_augment_db_open_failure_raises`: patch `rag.pipeline.SQLiteHelper` to raise `sqlite3.OperationalError` on `.open()`. Verify that `augment()` raises `RagPipelineError`.
- For `test_empty_results_vs_db_failure`: use two sub-tests. In the first, mock `RagRepository.vector_search` to return `[]` — verify `augment()` returns `""`. In the second, mock it to raise `sqlite3.OperationalError` — verify `augment()` raises `RagPipelineError`.
- All async test functions need `@pytest.mark.asyncio` decorator.
- Use `pytest.raises(ExceptionType, match="pattern")` to assert the exception message too.

---

## Validation plan

| Check | Command | Target |
|---|---|---|
| Tests | `uv run pytest tests/test_rag_utils.py tests/test_rag_pipeline_stage.py tests/test_rag_stages.py tests/test_rag_pipeline.py -v` | all pass (including new tests) |
| Coverage | `uv run coverage run -m pytest tests/test_rag_*.py && uv run coverage xml && uv run diff-cover coverage.xml --compare-branch=master` | ≥ 90% on changed lines |
| Full suite | `uv run pytest -v` | all pass |
