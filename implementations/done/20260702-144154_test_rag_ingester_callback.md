# Implementation Procedure: tests/test_rag_ingester_callback.py

## Goal

Add a pytest test that verifies `RagIngester.ingest_all()` invokes the `on_ingest_complete`
callback exactly once after successful ingestion. This test closes the coverage gap on the
callback path, which is the only trigger point for semantic cache invalidation after ingestion.

## Scope

**In scope:**
- New test file `tests/test_rag_ingester_callback.py`
- One test case: `test_ingest_all_calls_on_ingest_complete`

**Out of scope:**
- Modifying `scripts/rag/ingestion/ingester.py`
- Testing failure paths of `_process_url_groups`
- Testing the actual semantic cache invalidation behaviour

## Assumptions

1. `RagIngester` is importable from `scripts.rag.ingestion.ingester` (or the path used by
   existing tests — verify with `grep -r "from.*ingester import" tests/`).
2. `RagIngester.__init__` requires a config-like object; existing tests provide a fixture or
   a minimal mock — reuse that pattern.
3. `_process_url_groups` is the method to patch so that no real filesystem or DB I/O occurs.
4. The callback is called regardless of whether any documents were processed, as long as
   `_process_url_groups` returns without raising.
5. `uv run pytest tests/test_rag_ingester_callback.py -v` is the validation command.

## Implementation

### Target file

`tests/test_rag_ingester_callback.py`

### Procedure

1. Read `scripts/rag/ingestion/ingester.py` lines 140–160 to confirm the exact call site of
   `on_ingest_complete` and its signature (called with no args vs. with a result object).
2. Read `tests/` to find an existing test that imports `RagIngester` and reuse its fixture
   pattern for constructing a minimal instance.
3. Create `tests/test_rag_ingester_callback.py` with the test below.
4. Run `uv run pytest tests/test_rag_ingester_callback.py -v` and confirm it passes.

### Method

Patch `RagIngester._process_url_groups` at the class level with `unittest.mock.patch.object`
so the method returns a minimal valid result without touching the filesystem or DB.
Pass a `unittest.mock.Mock()` as `on_ingest_complete` and assert `.assert_called_once()`.

### Details

```python
# tests/test_rag_ingester_callback.py
from unittest.mock import Mock, patch

import pytest

# Adjust import path to match the project's convention.
# Verify with: grep -r "from.*ingester import" tests/
from scripts.rag.ingestion.ingester import RagIngester


@pytest.fixture()
def ingester(tmp_path):
    """Minimal RagIngester instance that does not hit the filesystem or DB."""
    # Reuse the config construction from existing ingester tests.
    # Replace with the actual minimal config required by RagIngester.__init__.
    cfg = ...  # copy from nearest existing fixture
    return RagIngester(cfg)


def test_ingest_all_calls_on_ingest_complete(ingester):
    """ingest_all() must call on_ingest_complete exactly once after completion."""
    callback = Mock()

    # Patch _process_url_groups to return a minimal successful result.
    with patch.object(
        type(ingester),
        "_process_url_groups",
        return_value=None,  # adjust if the method returns a result object
    ):
        ingester.ingest_all(force=False, on_ingest_complete=callback)

    callback.assert_called_once()
```

**Notes:**
- The `...` placeholder for `cfg` must be replaced by the actual minimal config used in
  peer tests. Read existing `tests/test_rag_*.py` to identify the fixture.
- If `_process_url_groups` returns a typed result object consumed by callers of
  `on_ingest_complete`, adjust `return_value` accordingly.
- If `ingest_all` is `async`, use `pytest.mark.asyncio` and `AsyncMock`.

## Validation plan

| Step | Command | Expected result |
|------|---------|----------------|
| Run new test | `uv run pytest tests/test_rag_ingester_callback.py -v` | PASSED |
| Regression: semantic cache | `uv run pytest tests/test_semantic_cache_invalidate.py -v` | all PASSED |
| Regression: quality | `uv run pytest tests/test_rag_quality_regression.py -v` | all PASSED |
| Lint | `ruff check tests/test_rag_ingester_callback.py` | 0 errors |
| Type check | `mypy tests/test_rag_ingester_callback.py` | no new errors |
