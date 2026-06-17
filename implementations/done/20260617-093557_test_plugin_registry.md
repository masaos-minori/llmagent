# Implementation: Tests for run_pipeline_stages() hook isolation (req 24 — Step 3)

## Goal

Add a `TestRunPipelineStages` test class to `tests/test_plugin_registry.py` covering error isolation, strict mode, sync/async hooks, and multi-hook behavior.

## Scope

- `tests/test_plugin_registry.py` — add `TestRunPipelineStages` class

## Assumptions

1. `run_pipeline_stages()` is already implemented in `shared/plugin_registry.py` (Step 1).
2. Tests use the existing `reset_registry` autouse fixture to isolate state.
3. Async hooks are awaited; sync hooks are called directly.
4. `@register_pipeline_stage(when="post")` registers the hook for use by `run_pipeline_stages()`.

## Implementation

### Target file

`tests/test_plugin_registry.py`

### Procedure

1. Add `import pytest` import for `pytest.mark.asyncio`.
2. Add `TestRunPipelineStages` class after existing test classes.

### Method

Edit tool. Append after `TestReset` class.

### Details

```python
class TestRunPipelineStages:
    """Tests for run_pipeline_stages() error isolation."""

    @pytest.mark.asyncio
    async def test_no_hooks_returns_original(self) -> None:
        """Empty hook list returns hits unchanged."""
        hits = [{"url": "u1"}, {"url": "u2"}]
        result = await plugin_registry.run_pipeline_stages(hits, "test query")
        assert result == hits

    @pytest.mark.asyncio
    async def test_hook_modifies_hits(self) -> None:
        """Successful hook return value replaces hits."""
        @plugin_registry.register_pipeline_stage(when="post")
        def add_score(hits, query):
            return [{**h, "score": 1.0} for h in hits]

        hits = [{"url": "u1"}]
        result = await plugin_registry.run_pipeline_stages(hits, "q")
        assert result[0]["score"] == 1.0

    @pytest.mark.asyncio
    async def test_async_hook_modifies_hits(self) -> None:
        """Async hook is awaited and its return value replaces hits."""
        @plugin_registry.register_pipeline_stage(when="post")
        async def async_tag(hits, query):
            return [{**h, "async": True} for h in hits]

        hits = [{"url": "u1"}]
        result = await plugin_registry.run_pipeline_stages(hits, "q")
        assert result[0]["async"] is True

    @pytest.mark.asyncio
    async def test_hook_isolation_skips_failed_sync(self) -> None:
        """Sync hook that raises is logged and skipped; hits unchanged."""
        @plugin_registry.register_pipeline_stage(when="post")
        def bad_hook(hits, query):
            raise RuntimeError("sync failure")

        hits = [{"url": "u1"}]
        result = await plugin_registry.run_pipeline_stages(hits, "q")
        assert result == hits  # unchanged

    @pytest.mark.asyncio
    async def test_hook_isolation_skips_failed_async(self) -> None:
        """Async hook that raises is logged and skipped; hits unchanged."""
        @plugin_registry.register_pipeline_stage(when="post")
        async def bad_async(hits, query):
            raise ValueError("async failure")

        hits = [{"url": "u1"}]
        result = await plugin_registry.run_pipeline_stages(hits, "q")
        assert result == hits

    @pytest.mark.asyncio
    async def test_hook_strict_mode_re_raises(self) -> None:
        """strict=True causes first hook failure to propagate."""
        @plugin_registry.register_pipeline_stage(when="post")
        def strict_fail(hits, query):
            raise RuntimeError("strict mode error")

        with pytest.raises(RuntimeError, match="strict mode error"):
            await plugin_registry.run_pipeline_stages([{"url": "u"}], "q", strict=True)

    @pytest.mark.asyncio
    async def test_multiple_hooks_first_fails(self) -> None:
        """First hook fails; second hook still runs on original hits."""
        ran = {"second": False}

        @plugin_registry.register_pipeline_stage(when="post")
        def first_fail(hits, query):
            raise RuntimeError("first fails")

        @plugin_registry.register_pipeline_stage(when="post")
        def second_ok(hits, query):
            ran["second"] = True
            return hits

        hits = [{"url": "u"}]
        result = await plugin_registry.run_pipeline_stages(hits, "q")
        assert ran["second"] is True
        assert result == hits

    @pytest.mark.asyncio
    async def test_hook_returning_none_keeps_prior_hits(self) -> None:
        """Hook returning None leaves hits from previous stage intact."""
        @plugin_registry.register_pipeline_stage(when="post")
        def no_return(hits, query):
            return None

        hits = [{"url": "u1"}]
        result = await plugin_registry.run_pipeline_stages(hits, "q")
        assert result == hits
```

## Validation plan

| Check | Tool | Target |
|---|---|---|
| Format | `uv run ruff format tests/test_plugin_registry.py` | clean |
| Lint | `uv run ruff check tests/test_plugin_registry.py` | 0 errors |
| Type check | `uv run mypy tests/test_plugin_registry.py` | no new errors |
| Tests | `uv run pytest tests/test_plugin_registry.py -v` | all pass |
