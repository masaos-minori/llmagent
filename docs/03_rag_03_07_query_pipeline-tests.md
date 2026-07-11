---
title: "RAG Query Pipeline - Tests"
category: rag
tags:
  - rag-tests
  - quality-regression
related:
  - 03_rag_00_document-guide.md
  - 03_rag_01_system_overview-part1.md
  - 03_rag_03_01_query_pipeline-overview.md
  - 03_rag_03_03_query_pipeline-context-and-diagnostics.md
  - 03_rag_03_query_pipeline-stages.md
  - 03_rag_03_06_query_pipeline-helpers-and-cache-part1.md
  - 03_rag_04_05_dto-types.md
  - 03_rag_05_1-configuration-reference.md
source:
  - 03_rag_03_01_query_pipeline-overview.md
---

# RAG クエリパイプライン

- システム概要 → [03_rag_01_system_overview-part1.md](03_rag_01_system_overview-part1.md)
- 設定 → [03_rag_05_1-configuration-reference.md](03_rag_05_1-configuration-reference.md)
- 型定義 → [03_rag_04_05_dto-types.md](03_rag_04_01_dto-models_data.md)

---

## 8. テスト

### 8.1 決定論的リグレッションテスト (`tests/test_rag_quality_regression.py`)

フィクスチャ: 既知の3ドキュメントを持つインメモリSQLite DB、固定ベクトルのモックエンベッダー。

| テスト | モード | アサーション |
|---|---|---|
| `test_rrf_returns_result_for_known_query` | RRF (デフォルト) | `len(result.reranked) >= 0` — 例外を発生させないこと |
| `test_no_rrf_returns_result` | RRFなし | `len(result.reranked) >= 0` — 例外を発生させないこと |
| `test_semantic_cache_hit` | RRF + キャッシュ | 同一クエリの2回目はキャッシュされたコンテキストまたはリランク結果を返す |
| `test_fallback_no_embed_server` | RRF、埋め込み失敗 | `result.reranked == []` — フォールバックは例外ではなく空の結果を返す |
| `test_rrf_score_values_with_known_hits` | `use_rrf=True, rrf_k=60` | 両方のリストでヒットした項目は`rrf_score`が厳密に高くなる |
| `test_top_n_retrieval_count` | `use_rrf=True, use_rerank=False, rag_top_k=3` | `len(reranked)==3`、`len(merged)==5` |
| `test_semantic_cache_hit_returns_cached_result` | `SemanticCache`単体の直接テスト | `lookup()`が保存済みコンテキストを返す |
| `test_semantic_cache_miss_below_threshold` | `SemanticCache`単体の直接テスト | コサイン類似度が閾値未満の場合、`lookup()`は`None`を返す |
| `test_rrf_merged_order_is_descending` | `use_rrf=True` | `merged`は`rrf_score`の降順にソートされている |

実行: `uv run pytest tests/test_rag_quality_regression.py -v`

---

## Related Documents

- `03_rag_00_document-guide.md`
- `03_rag_01_system_overview-part1.md`
- `03_rag_03_01_query_pipeline-overview.md`
- `03_rag_03_03_query_pipeline-context-and-diagnostics.md`
- `03_rag_03_query_pipeline-stages.md`
- `03_rag_03_06_query_pipeline-helpers-and-cache-part1.md`
- `03_rag_04_05_dto-types.md`
- `03_rag_05_1-configuration-reference.md`

## Keywords


rag-tests
quality-regression
rag
