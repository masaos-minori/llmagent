# Implementation: rag/cache.py + rag/pipeline.py augment() + mcp/rag_pipeline/models.py — SemanticCache activation

## Goal

Add `history_context` to `SemanticCache.lookup/put` signatures, activate the semantic cache in `pipeline.py:augment()`, add `use_semantic_cache` to `RagPipelineConfig`, and fix tests broken by the signature change.

## Scope

- `scripts/rag/cache.py` — `CacheService` Protocol + `SemanticCache.lookup/put` signature change
- `scripts/rag/pipeline.py` — `augment()` method: add cache lookup and put with `use_semantic_cache` guard
- `scripts/mcp/rag_pipeline/models.py` — add `use_semantic_cache: bool = False` to `RagPipelineConfig`, `from_dict()`, `build_rag_cfg_adapter()`
- `tests/test_rag_pipeline_stage.py` — fix `put()` calls at lines 323, 330, 332, 338 to new 3-arg signature

## Assumptions

- `CacheEntry.history_context` field already added in previous step
- `pipeline.py` already imports `TwoStageFetchResult` from previous step
- `pipeline.py:augment()` currently has no semantic cache calls
- `embed_url` may be empty string; empty string must be checked before calling `get_embedding()`
- `except (httpx.HTTPError, OSError, TimeoutError)` is the correct catch for embedding failures (BLE001-safe)
- `stat_semantic_cache_hits` increment is out of scope; existing `logger.debug()` in `cache.py:53` is sufficient
- `RagPipelineConfig` is in `mcp/rag_pipeline/models.py`; `build_rag_cfg_adapter()` builds a `SimpleNamespace` passed to `pipeline.py` as `cfg`

## Implementation

### Target file

- `scripts/rag/cache.py`
- `scripts/rag/pipeline.py`
- `scripts/mcp/rag_pipeline/models.py`
- `tests/test_rag_pipeline_stage.py`

### Procedure

1. Update `CacheService` Protocol in `cache.py` (lines 18-23)
2. Update `SemanticCache.lookup()` — add `history_context: str = ""` param; add `entry.history_context != history_context` skip logic
3. Update `SemanticCache.put()` — change signature to `put(self, embedding, history_context, context_str)` and pass `history_context` to `CacheEntry`
4. Add `use_semantic_cache` field to `RagPipelineConfig` in `models.py`
5. Add `use_semantic_cache=bool(d.get("use_semantic_cache", False))` to `from_dict()`
6. Add `use_semantic_cache=bool(cfg.use_semantic_cache)` to `build_rag_cfg_adapter()` SimpleNamespace
7. Locate `augment()` in `pipeline.py`; add cache lookup before DB open and cache put after context_block is built
8. Fix 4 `put()` call sites in `test_rag_pipeline_stage.py`

### Method

- Edit tool for each file
- Check `pipeline.py:augment()` line numbers with grep before editing

### Details

**`cache.py` — CacheService Protocol:**
```python
class CacheService(Protocol):
    def lookup(self, embedding: list[float], history_context: str = "") -> str | None: ...
    def put(self, embedding: list[float], history_context: str, context_str: str) -> None: ...
```

**`cache.py` — SemanticCache.lookup():**
```python
def lookup(self, embedding: list[float], history_context: str = "") -> str | None:
    if self._dim is not None and len(embedding) != self._dim:
        raise ValueError(...)
    best_sim = -1.0
    best_ctx: str | None = None
    for entry in self._entries:
        if entry.history_context != history_context:
            continue
        sim = cosine_sim(embedding, entry.embedding)
        if sim > best_sim:
            best_sim = sim
            best_ctx = entry.context_str
    if best_sim >= self._threshold:
        logger.debug(f"SemanticCache hit: sim={best_sim:.4f}")
        return best_ctx
    return None
```

**`cache.py` — SemanticCache.put():**
```python
def put(self, embedding: list[float], history_context: str, context_str: str) -> None:
    if self._dim is None:
        self._dim = len(embedding)
    elif len(embedding) != self._dim:
        raise ValueError(...)
    self._entries.append(CacheEntry(
        embedding=embedding,
        context_str=context_str,
        history_context=history_context,
    ))
    self.prune()
```

**`mcp/rag_pipeline/models.py` — RagPipelineConfig:**
```python
@dataclass
class RagPipelineConfig:
    ...
    use_semantic_cache: bool = False  # add field
```

**`mcp/rag_pipeline/models.py` — from_dict():**
```python
use_semantic_cache=bool(d.get("use_semantic_cache", False)),
```

**`mcp/rag_pipeline/models.py` — build_rag_cfg_adapter():**
```python
use_semantic_cache=bool(cfg.use_semantic_cache),
```

**`pipeline.py` — augment() — cache lookup block (add after rag_url fallback, before DB open):**
```python
# Semantic cache lookup (in-process mode only)
emb: list[float] | None = None
if self._cfg.use_semantic_cache and self._embed_url:
    try:
        emb = await get_embedding(query, self._http, self._embed_url)
    except (httpx.HTTPError, OSError, TimeoutError):
        emb = None
    if emb is not None:
        cached = self.semantic_cache.lookup(emb, history_context)
        if cached is not None:
            return cached
```

**`pipeline.py` — augment() — cache put block (add after context_block is built, before return):**
```python
if self._cfg.use_semantic_cache and emb is not None and context_block:
    self.semantic_cache.put(emb, history_context, context_block)
```

**`test_rag_pipeline_stage.py` — put() call fixes:**
```python
# line 323: cache.put([1.0, 2.0, 3.0], "ctx")  →  cache.put([1.0, 2.0, 3.0], "", "ctx")
# line 330: cache.put([1.0, 2.0, 3.0], "ctx")  →  cache.put([1.0, 2.0, 3.0], "", "ctx")
# line 332: cache.put([1.0, 2.0], "other")      →  cache.put([1.0, 2.0], "", "other")
# line 338: cache.put([1.0, 2.0, 3.0], "ctx")  →  cache.put([1.0, 2.0, 3.0], "", "ctx")
```

## Validation plan

- `grep -n "semantic_cache\." scripts/rag/pipeline.py` — output includes both `lookup` and `put`
- `uv run pytest tests/test_rag_pipeline_stage.py::TestSemanticCacheDimensionGuard -v` — all pass
- `uv run mypy scripts/rag/cache.py scripts/rag/pipeline.py scripts/mcp/rag_pipeline/models.py` — 0 new errors
- `uv run ruff check scripts/rag/cache.py scripts/rag/pipeline.py` — 0 errors
- `uv run pytest tests/test_rag*.py -v` — all pass
