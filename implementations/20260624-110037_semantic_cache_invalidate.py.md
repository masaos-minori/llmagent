# Implementation Procedure: scripts/rag/cache.py + pipeline.py

## Goal

`SemanticCache` に `invalidate()` メソッドとジェネレーションカウンタを追加し、インジェスト完了後に呼び出す。

## Scope

**In:**
- `scripts/rag/cache.py` — `_generation` カウンタ; `invalidate()` メソッド; `CacheEntry.generation` フィールド
- `scripts/rag/pipeline.py` — インジェスト完了後に `cache.invalidate()` 呼び出し

**Out:** FIFO から LRU への変更、キャッシュ実装全体の再設計

## Design Decision

`invalidate()` 時に `clear()` を使用 (最もシンプル; 部分的ステールエントリなし)。`CacheEntry.generation` フィールドはドキュメント目的。

## Implementation

### cache.py — _generation + invalidate()

```python
@dataclasses.dataclass
class CacheEntry:
    embedding: list[float]
    context_str: str
    history_context: str
    generation: int = 0  # matches SemanticCache._generation at time of insertion

class SemanticCache:
    def __init__(self, max_size: int = 100, threshold: float = 0.92) -> None:
        ...
        self._generation: int = 0

    def invalidate(self) -> None:
        """Bump generation; clear all cached entries atomically."""
        with self._lock:
            self._generation += 1
            self._entries.clear()

    def put(self, embedding, history_context, context_str):
        # entry.generation = self._generation
        ...
```

### pipeline.py — インジェスト後に invalidate()

```python
# インジェスト完了コールバックまたは ingest() メソッド末尾:
if self._semantic_cache is not None:
    self._semantic_cache.invalidate()
```

## Validation plan

| Check | Command | Expected |
|---|---|---|
| invalidate 存在 | `grep -n "def invalidate" scripts/rag/cache.py` | found |
| Tests | `uv run pytest tests/ -k "cache" -x -q` | all pass |
