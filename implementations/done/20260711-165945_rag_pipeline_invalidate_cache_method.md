## Goal

Add a public `RagPipeline.invalidate_cache()` method to `scripts/rag/pipeline.py` that clears all cached semantic-search entries by delegating to the already-existing, thread-safe `self.semantic_cache.invalidate()`. This gives external callers (e.g. the MCP `rag_pipeline` service) a supported way to invalidate the cache without reaching into `pipeline.semantic_cache` directly.

## Scope

**In-Scope:**
- `scripts/rag/pipeline.py`: add one new public instance method, `invalidate_cache(self) -> None`, on `RagPipeline`.

**Out-of-Scope:**
- `scripts/rag/cache.py::SemanticCache.invalidate()` — already implemented (lines 102-106), thread-safe (`with self._lock:`), bumps a generation counter and clears entries. No change needed.
- Any caller-side change (MCP service wiring is a separate phase/doc).
- Any change to `RagPipeline.__init__` or `semantic_cache` attribute visibility — `semantic_cache` (`pipeline.py:114`) is already a public, directly-accessible attribute.

## Assumptions

- `SemanticCache.invalidate()` requires no arguments and returns `None`.
- `RagPipeline` instances always have `self.semantic_cache` set by the time any caller could reasonably invoke `invalidate_cache()` (mirrors existing usage elsewhere in the class).
- No existing test currently asserts that `RagPipeline` lacks this method (i.e. this is a pure additive change with no behavior change to existing code paths).

## Implementation

### Target file

`scripts/rag/pipeline.py`

### Procedure

1. Locate the `RagPipeline` class definition and its existing public methods (e.g. near where `semantic_cache` is defined/used, `pipeline.py:114` and surrounding methods) to place the new method in a logically consistent spot (grouped with other cache-related or public API methods).
2. Add the new method `invalidate_cache(self) -> None` with a docstring explaining when to call it and what it delegates to.
3. Do not add any new imports — `self.semantic_cache` is already an attribute of `RagPipeline`.

### Method

Add exactly this method body (signature and behavior fixed by the plan's Design section):

```python
def invalidate_cache(self) -> None:
    """Clear all cached semantic-search entries.

    Call after any corpus-changing operation this pipeline instance is aware
    of (e.g. MCP rag_delete_document) so subsequent queries don't return
    context for a document that no longer exists. Delegates to
    SemanticCache.invalidate(), which is thread-safe.
    """
    self.semantic_cache.invalidate()
```

### Details

- No new state, no new error handling — this is a pure delegation method (single line body).
- Return type is `None`; do not swallow or transform any exception `SemanticCache.invalidate()` might raise (none are documented, but do not add a broad `except` around this call).
- Do not rename or change the existing `semantic_cache` attribute.
- Keep the docstring in English per `rules/coding.md` (comments/log output must be English only).
- Line length must stay within 120 chars (ruff `E501` is ignored for strings but this is not a string literal issue — keep normal formatting via `ruff format`).

## Validation plan

Filtered from the plan's Validation plan table to checks relevant to `scripts/rag/pipeline.py`:

| Check | Tool | Target |
|---|---|---|
| Lint | `uv run ruff check scripts/rag/pipeline.py` | 0 errors |
| Type check | `uv run mypy scripts/rag/pipeline.py` | No new errors |
| Architecture | `PYTHONPATH=scripts uv run lint-imports` | 0 violations (no import changes) |
| Regression | `uv run pytest tests/test_rag_pipeline.py tests/test_mcp_rag_pipeline.py -q` | No new failures |
| Manual | `PYTHONPATH=scripts uv run python -c "from rag.pipeline import RagPipeline; assert hasattr(RagPipeline, 'invalidate_cache')"` | Confirms the method exists on the real class |
