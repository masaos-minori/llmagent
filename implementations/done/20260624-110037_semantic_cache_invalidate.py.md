# Implementation Procedure: SemanticCache invalidate after ingest

## Goal

`SemanticCache` に `invalidate()` メソッドとジェネレーションカウンタを追加し、インジェスト完了後に呼び出す。

## Scope

**In:**
- `scripts/rag/cache.py` — `_generation` カウンタ; `invalidate()` メソッド; `CacheEntry.generation` フィールド
- `scripts/rag/ingestion/ingester.py` — `on_ingest_complete` コールバックパラメータ
- `scripts/agent/services/ingest_workflow.py` — `on_ingest_complete` パラメータの伝播
- `scripts/agent/commands/cmd_ingest.py` — `/ingest` で一時 pipeline から cache を取得し、invalidate コールバックを渡す
- `scripts/rag/models_data.py` — `CacheEntry.generation` フィールド追加

**Out:** FIFO から LRU への変更、キャッシュ実装全体の再設計

## Design Decision

`invalidate()` 時に `clear()` を使用 (最もシンプル; 部分的ステールエントリなし)。`CacheEntry.generation` フィールドはドキュメント目的。

インジェスト完了コールバックは `RagIngester.ingest_all()` → `IngestWorkflowService.run()` のチェーンを介して渡す。REPL `/ingest` コマンドは一時 pipeline を作成して semantic cache を取得し、無効化コールバックを渡す。

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

    @property
    def generation(self) -> int:
        return self._generation

    def put(self, embedding, history_context, context_str):
        # entry.generation = self._generation
        ...
```

### ingester.py — on_ingest_complete コールバック

```python
def ingest_all(
    self,
    force: bool = False,
    on_ingest_complete: Callable[[], None] | None = None,
) -> RagConsistencyReport | None:
    ...
    if on_ingest_complete is not None:
        try:
            on_ingest_complete()
        except Exception:
            logger.exception("on_ingest_complete callback failed")
    return report
```

### ingest_workflow.py — コールバック伝播

```python
async def run(
    self,
    target: str,
    lang: str = "ja",
    snippets_only: bool = False,
    on_status: Callable[[str], None] | None = None,
    on_ingest_complete: Callable[[], None] | None = None,
) -> IngestOutcome:
    ...

async def _split_and_ingest(
    self,
    loop: asyncio.AbstractEventLoop,
    snippets_only: bool,
    messages: list[str],
    on_status: Callable[[str], None] | None = None,
    on_ingest_complete: Callable[[], None] | None = None,
) -> tuple[int, list[str], int]:
    ...

async def _ingest_to_db(
    self,
    loop: asyncio.AbstractEventLoop,
    on_status: Callable[[str], None] | None = None,
    on_ingest_complete: Callable[[], None] | None = None,
) -> tuple[list[str], int]:
    ...
    report = await loop.run_in_executor(
        None,
        lambda: ingester.ingest_all(on_ingest_complete=on_ingest_complete),
    )
```

### cmd_ingest.py — 一時 pipeline から cache を取得

```python
# Build a temporary pipeline to get the semantic cache for invalidation
cache = None
if self._ctx.services is not None and self._ctx.services.http is not None:
    from rag.pipeline import RagPipeline
    from shared.config_loader import ConfigLoader

    rag_cfg_dict = ConfigLoader().load_all()
    if rag_cfg_dict.get("use_search", True):
        rag_cfg = build_rag_cfg_adapter(RagPipelineConfig.from_dict(rag_cfg_dict))
        temp_pipeline = RagPipeline(self._ctx.services.http, rag_cfg)
        cache = temp_pipeline.semantic_cache

svc = IngestWorkflowService()
await svc.run(
    target,
    lang=lang,
    snippets_only=snippets_only,
    on_status=on_status,
    on_ingest_complete=(
        lambda: cache.invalidate() if cache is not None else None
    ),
)
```

## Validation plan

| Check | Command | Expected |
|---|---|---|
| invalidate 存在 | `grep -n "def invalidate" scripts/rag/cache.py` | found |
| generation counter 存在 | `grep -n "_generation" scripts/rag/cache.py` | found |
| CacheEntry.generation 存在 | `grep -n "generation:" scripts/rag/models_data.py` | found |
| on_ingest_complete 存在 | `grep -n "on_ingest_complete" scripts/rag/ingestion/ingester.py` | found |
| Tests | `uv run pytest tests/ -k "cache" -x -q` | all pass |
