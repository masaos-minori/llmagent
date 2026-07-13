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
  - 03_rag_03_06_query_pipeline-helpers-and-cache-part1.md
  - 03_rag_03_06_query_pipeline-helpers-and-cache-part2.md
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
| `test_rrf_returns_result_for_known_query` | RRF (デフォルト) | 埋め込みサーバー未設定のため全埋め込み取得が失敗し `result.reranked == []`、`diagnostics.embed_failed >= 1` かつ `embed_ok == 0` |
| `test_no_rrf_returns_result` | RRFなし | 同上の埋め込み失敗により `result.reranked == []`；`len(result.queries) >= 1` |
| `test_fallback_no_embed_server` | RRF、埋め込み失敗 | `result.reranked == []` — フォールバックは例外ではなく空の結果を返す |
| `test_rrf_score_values_with_known_hits` | `use_rrf=True, rrf_k=60` | 両方のリストでヒットした項目は`rrf_score`が厳密に高くなる |
| `test_top_n_retrieval_count` | `use_rrf=True, use_rerank=False, rag_top_k=3` | `len(reranked)==3`、`len(merged)==5` |
| `test_semantic_cache_hit_returns_cached_result` | `SemanticCache`単体の直接テスト | `lookup()`が保存済みコンテキストを返す |
| `test_semantic_cache_miss_below_threshold` | `SemanticCache`単体の直接テスト | コサイン類似度が閾値未満の場合、`lookup()`は`None`を返す |
| `test_rrf_merged_order_is_descending` | `use_rrf=True` | `merged`は`rrf_score`の降順にソートされている |

**訂正（Explicit in code）:** 旧記述にあった `test_semantic_cache_hit`（RRF + キャッシュで2回目の呼び出しがキャッシュ結果を返すことを検証）という名前のテストは現在の `tests/test_rag_quality_regression.py` に存在しない。同種の観点は `test_semantic_cache_hit_returns_cached_result`（`SemanticCache` 単体テスト）と `test_diagnostics_semantic_cache_hits`（下表）でカバーされている。

### 8.2 追加されたテスト（現行実装のみに存在し、旧ドキュメントに未記載だったもの）

| テスト | モード | アサーション |
|---|---|---|
| `test_rrf_vs_no_rrf_fusion_mode` | 固定ヒットをモック注入 | RRFモードの `merged` は全件 `MergedHit` かつ `rrf_score > 0`；no-RRF（dedupのみ）モードは `rrf_score == 0.0` |
| `test_two_runs_same_query_consistent` | RRF | 同一クエリを2回実行すると `reranked` と `diagnostics.embed_failed` が一致する（パイプラインは決定論的） |
| `test_ranking_order_with_known_hits` | `use_rrf=True, use_rerank=False` | リランカー未使用時、`merged`/`reranked` の順序はRRFマージ順（`chunk_ids == [3, 1, 2]`）で全件 `rrf_score > 0.0` |
| `test_semantic_cache_generation_invalidation` | `SemanticCache`単体 | `invalidate()` 後に `generation` が1増加し、既存エントリは全て `lookup()` でヒットしなくなる（`size == 0`） |
| `test_diagnostics_fusion_mode` | RRF / dedup_only 両方 | `get_diagnostics()["fusion_mode"]` がそれぞれ `"rrf"` / `"dedup_only"` を返す |
| `test_diagnostics_semantic_cache_hits` | `SemanticCache`単体 | `threshold=0.0` で `put()` 後に同一ベクトルの `lookup()` がヒットする |
| `test_diagnostics_fts_error_counts` | 固定ヒット + `fts_errors=2` を注入 | `result.diagnostics.fts_errors == 2` がそのまま伝播する |
| `test_diagnostics_refiner_returned_empty` | `use_refiner=True`、Refinerステージ結果をモック | `get_diagnostics()["refiner_returned_empty"] == 1` かつ `["refiner_fallback_count"] == 1` |
| `test_diagnostics_refiner_exception` | `use_refiner=True`、`refiner_exception: ...` をモック | `get_diagnostics()["refiner_exception_count"] == 1` かつ `["refiner_fallback_count"] == 1` |
| `test_diagnostics_refiner_no_retry` | `use_refiner=True` | Refiner失敗1回につきフォールバック記録は1件のみ（リトライされない） |

実行: `uv run pytest tests/test_rag_quality_regression.py -v`

**参考（Strongly implied by code、本ドキュメントのスコープ外）:** `tests/` 配下にはこのほか `test_rag_pipeline.py`、`test_rag_pipeline_stage.py`、`test_rag_pipeline_service.py`、`test_rag_pipeline_mcp_service.py`、`test_mcp_rag_pipeline.py` が存在し、ステージ単体（`MqeStage`/`SearchStage`/`FusionStage`/`RerankStage`/`AugmentStage`）や `pipeline_service`/MCPサービス層をそれぞれ個別にカバーしている。本節は決定論的な品質リグレッション（`test_rag_quality_regression.py`）に限定して記載する。

---

## Related Documents

- `03_rag_00_document-guide.md`
- `03_rag_01_system_overview-part1.md`
- `03_rag_03_01_query_pipeline-overview.md`
- `03_rag_03_03_query_pipeline-context-and-diagnostics.md`
- `03_rag_03_04_query_pipeline-search-stages.md`
- `03_rag_03_05_query_pipeline-augment-stages.md`
- `03_rag_03_06_query_pipeline-helpers-and-cache-part1.md`
- `03_rag_03_06_query_pipeline-helpers-and-cache-part2.md`
- `03_rag_04_05_dto-types.md`
- `03_rag_05_1-configuration-reference.md`

## Keywords

rag-tests
quality-regression
semantic-cache-generation
refiner-diagnostics
rag
