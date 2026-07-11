## Goal

Wire `RagPipelineMCPService.fmt_delete_document()` so that a successful `rag_delete_document` call invalidates the calling process's semantic cache, using the new `RagPipeline.invalidate_cache()` method exposed through the `RagPipelineLike` Protocol — never by touching `pipeline.semantic_cache` directly.

## Scope

**In-Scope:**
- `scripts/mcp_servers/rag_pipeline/service.py`:
  - Add `invalidate_cache(self) -> None: ...` to the `RagPipelineLike` Protocol (lines 32-43 currently).
  - Update `fmt_delete_document()` (lines 197-205 currently) so that when `self._doc_mgr.delete_document(url)` returns `True`, it calls `self._pipeline_or_raise().invalidate_cache()` and logs an info-level message, before returning the "Deleted" string.

**Out-of-Scope:**
- `scripts/mcp_servers/rag_pipeline/document_manager.py` — no change; `delete_document()` already returns the correct `bool` signal.
- Any other `fmt_*` handler in this file.
- Any new HTTP endpoint or admin route (explicitly out of scope per the plan's Assumption 6 / Design).

## Assumptions

- `RagPipelineLike` is a structural `Protocol`; `RagPipeline` is confirmed (via `grep -rn "RagPipelineLike"`) to be its only real implementer, so adding a required method does not require updating any other implementer or test double.
- `RagPipelineMCPService._pipeline` is `None` until `start()` is called; existing methods that need the pipeline (`fmt_run_pipeline`, `fmt_debug_pipeline`) already call `self._pipeline_or_raise()` first — this change must follow the same established pattern rather than inventing a new access path.
- Cache invalidation must occur **only** on successful deletion (`ok is True`); it must not be called when the document was not found.
- The log call is informational (`logger.info`), not a warning/error, since this is expected, successful behavior.

## Implementation

### Target file

`scripts/mcp_servers/rag_pipeline/service.py`

### Procedure

1. Locate the `RagPipelineLike` Protocol definition (around lines 32-43) and add a new abstract method `invalidate_cache(self) -> None: ...` alongside the existing `augment`, `last_fetch_result`, `last_timings` members.
2. Locate `fmt_delete_document()` (around lines 197-205).
3. After computing `ok = self._doc_mgr.delete_document(url)`, add a conditional block: if `ok` is truthy, call `self._pipeline_or_raise().invalidate_cache()` and log `logger.info(...)` with the deleted URL, **before** the existing return statement.
4. Do not change the not-found path (`ok` is `False`) — it must return `f"Not found: {url}"` unchanged, without touching `self._pipeline` or calling `_pipeline_or_raise()`.
5. Confirm `logger` is already defined at module scope (it is used elsewhere in this file); no new import needed for `invalidate_cache` since it is invoked through the existing `_pipeline_or_raise()` accessor.

### Method

Add to `RagPipelineLike` (Protocol body, structural typing — no implementation, per the plan's Design):

```python
class RagPipelineLike(Protocol):
    async def augment(self, ...) -> str: ...
    last_fetch_result: Any
    last_timings: dict[str, float]
    def invalidate_cache(self) -> None: ...
```

Update `fmt_delete_document()` to:

```python
async def fmt_delete_document(self, args: ToolArgs) -> str:
    raw_url = args.get("url")
    if not isinstance(raw_url, str):
        return "Error: url must be a string."
    url = raw_url.strip()
    if not url:
        return "Error: url is required."
    ok = self._doc_mgr.delete_document(url)
    if ok:
        self._pipeline_or_raise().invalidate_cache()
        logger.info("Semantic cache invalidated after deleting %r", url)
    return f"Deleted: {url}" if ok else f"Not found: {url}"
```

### Details

- `_pipeline_or_raise()` is the existing accessor used by `fmt_run_pipeline`/`fmt_debug_pipeline` — reuse it rather than accessing `self._pipeline` directly, so a `None` pipeline raises the same established `RuntimeError` rather than an `AttributeError`.
- The log message must be English only (per `rules/coding.md`), and use `%s`-style lazy formatting (`%r` here for the URL), not an f-string, consistent with the standard logging pattern in `skills/python-design/workflow.md` Step 6.
- Do not wrap `invalidate_cache()` in a try/except — no failure mode for it is defined in this plan; let exceptions propagate normally (consistent with `fmt_run_pipeline`/`fmt_debug_pipeline` behavior after `_pipeline_or_raise()`).
- Ordering matters: invalidate/log must happen before constructing/returning the final string, but logically only in the `ok` branch.

## Validation plan

Filtered from the plan's Validation plan table to checks relevant to `scripts/mcp_servers/rag_pipeline/service.py`:

| Check | Tool | Target |
|---|---|---|
| Lint | `uv run ruff check scripts/mcp_servers/rag_pipeline/service.py` | 0 errors |
| Type check | `uv run mypy scripts/mcp_servers/rag_pipeline/service.py` | No new errors |
| Architecture | `PYTHONPATH=scripts uv run lint-imports` | 0 violations (no import changes) |
| Tests | `uv run pytest tests/test_rag_pipeline_mcp_service.py -v` | All pass, including cache-invalidation tests added in the Tests phase |
| Regression | `uv run pytest tests/test_rag_pipeline.py tests/test_mcp_rag_pipeline.py -q` | No new failures (confirms the new `RagPipelineLike` protocol member doesn't break any other consumer) |
