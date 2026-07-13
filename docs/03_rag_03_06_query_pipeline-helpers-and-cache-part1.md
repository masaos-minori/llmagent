---
title: "RAG Query Pipeline - Helpers and Cache (Part 1)"
category: rag
tags:
  - semantic-cache
  - rag-repository
  - rag-scorer
  - rag-llm
related:
  - 03_rag_00_document-guide.md
  - 03_rag_01_system_overview-part1.md
  - 03_rag_03_01_query_pipeline-overview.md
  - 03_rag_03_03_query_pipeline-context-and-diagnostics.md
  - 03_rag_03_06_query_pipeline-helpers-and-cache-part2.md
  - 03_rag_04_05_dto-types.md
  - 03_rag_05_1-configuration-reference.md
source:
  - 03_rag_03_06_query_pipeline-helpers-and-cache-part1.md
---

# RAG クエリパイプライン

- システム概要 → [03_rag_01_system_overview-part1.md](03_rag_01_system_overview-part1.md)
- 設定 → [03_rag_05_1-configuration-reference.md](03_rag_05_1-configuration-reference.md)
- 型定義 → [03_rag_04_05_dto-types.md](03_rag_04_01_dto-models_data.md)

---

## 6. SemanticCache (`scripts/rag/cache.py`)

`SemanticCache` は（`rag/cache.py` にも定義されている）`CacheService` プロトコルを実装する。このプロトコルは `lookup()` と `put()` のみを宣言する — 代替可能性が重要な箇所では、呼び出し元は `SemanticCache` を直接ではなく `CacheService` として型付けすべきである。

```python
from rag.cache import SemanticCache  # defined in rag/cache.py:31; imported by rag/pipeline.py:29

cache = SemanticCache(max_size=100, threshold=0.92)
```

| メソッド / プロパティ | シグネチャ | 説明 |
|---|---|---|
| `lookup` | `(embedding, history_context="") -> str \| None` | 一致する `history_context` エントリの中でコサイン類似度がしきい値以上のものがあればキャッシュ結果を返す；埋め込み次元の不一致時は `ValueError` を発生させる；それ以外は `None` |
| `put` | `(embedding, history_context, context_str) -> None` | エントリを保存する；`history_context` はキャッシュキーの一部；埋め込み次元の不一致時は `ValueError` を発生させる；その後 `prune()` を呼び出す |
| `prune` | `() -> None` | `max_size <= 0` の場合は全エントリを即時空にする；`len > max_size` の場合は FIFO で `max_size` 件まで削除 |
| `size` | プロパティ `int` | 現在のエントリ数 |
| `invalidate` | `() -> None` | 世代カウンタをインクリメントし、キャッシュ済みエントリをすべてアトミックにクリアする |
| `generation` | プロパティ `int` | キャッシュ無効化世代カウント（観測用のみ；エントリの鮮度フィルタには使用されない） |

**テストで確認されている挙動（`tests/test_rag_quality_regression.py::test_semantic_cache_generation_invalidation`）:** `invalidate()` 呼び出しにより `generation` が1増加し、既存エントリは即座に全て `lookup()` でヒットしなくなる（`size == 0` になる）。

### RagPipeline.invalidate_cache()

```python
RagPipeline.invalidate_cache(self) -> None
```

`self.semantic_cache.invalidate()` に委譲する。MCP `rag_pipeline` サービスの `fmt_delete_document()` が成功時のみ呼び出す。

**Why this exists（Strongly implied by code）:** コーパス変更操作（例: MCP `rag_delete_document`）後にこのパイプラインインスタンスが認識しているキャッシュを破棄し、以降のクエリが削除済みドキュメントのコンテキストを返さないようにするため。`SemanticCache.invalidate()` は内部で `threading.RLock` を使用しスレッドセーフに実装されている（`scripts/rag/cache.py`）。

### CLI インジェスト後のキャッシュ鮮度

MCP `rag_delete_document` は呼び出し元のMCPプロセス内の `RagPipeline.semantic_cache` を `invalidate_cache()` 経由で無効化する — これは**1つのプロセス内のみ**をクリアする。CLIインジェスト（`uv run python -m rag.ingestion.ingester`）は**別のプロセス**で実行され、MCPサービスのメモリ内キャッシュにはアクセスできない。**CLIインジェスト後に即座のクエリ鮮度を必要とする場合は、rag-pipeline-mcpサービス（またはエージェントプロセス、サブプロセスモードのMCPサーバーを再起動する）を再起動する必要がある** — これはオペレーショナルな手順であり、CLIインジェストが自動で行うものではない。再起動がない場合、インジェスト前に作成されたキャッシュエントリは、キャッシュ自体のEviction/TTL（[cache configuration]参照）が自然に期限切れになるまでの制限付きウィンドウの間、古いコンテキストを返す可能性がある。

---

## Related Documents

- `03_rag_00_document-guide.md`
- `03_rag_01_system_overview-part1.md`
- `03_rag_03_01_query_pipeline-overview.md`
- `03_rag_03_03_query_pipeline-context-and-diagnostics.md`
- `03_rag_03_04_query_pipeline-search-stages.md`
- `03_rag_03_05_query_pipeline-augment-stages.md`
- `03_rag_04_05_dto-types.md`
- `03_rag_05_1-configuration-reference.md`
- `03_rag_03_06_query_pipeline-helpers-and-cache-part2.md`

## Keywords

semantic-cache
rag-repository
rag-scorer
rag-llm
rag
