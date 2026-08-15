---
title: "RAG Query Pipeline - Tests"
category: rag
tags:
  - rag-tests
  - quality-regression
related:
  - 03_rag_00_document-guide.md
  - 03_rag_01_system_overview.md
  - 03_rag_03_01_query_pipeline-overview.md
  - 03_rag_03_03_query_pipeline-context-and-diagnostics.md
  - 03_rag_03_06_query_pipeline-helpers-and-cache.md
  - 03_rag_03_06_query_pipeline-helpers-and-cache.md
  - 03_rag_04_05_dto-types.md
  - 03_rag_05_1-configuration-reference.md
source:
  - 03_rag_03_01_query_pipeline-overview.md
---

# RAG クエリパイプライン

- システム概要 → [03_rag_01_system_overview.md](03_rag_01_system_overview.md)
- 設定 → [03_rag_05_1-configuration-reference.md](03_rag_05_1-configuration-reference.md)
- 型定義 → [03_rag_04_05_dto-types.md](03_rag_04_01_dto-models_data.md)

---

## 8. テスト

### 8.1 決定論的リグレッションテスト (`tests/test_rag_quality_regression.py`)

本テストスイートは、RAGクエリパイプラインの主要な動作特性が決定論的に維持されていることを検証します。詳細なテストケースとアサーションの内容については、[tests/test_rag_quality_regression.py](tests/test_rag_quality_regression.py) を参照してください。

#### 検証される主な特性:
- **RRFおよび融合モードの挙動**:
  - RRFモードにおけるヒットの重複排除と `rrf_score` による降順ソート。
  - 非RRF（デデュープのみ）モードにおける `rrf_score == 0.0` の扱い。
  - 埋め込みサーバー未設定時のフォールバック動作（空の結果を返す）。
- **セマンティックキャッシュの動作**:
  - キャッシュヒット時のコンテキスト取得、閾値未満のミス、および無効化（invalidate）によるエントリ破棄。
- **診断情報 (Diagnostics) の正確性**:
  - 融合モード（`rrf` vs `dedup_only`）、FTSエラー件数、埋め込み失敗件数の正確なカウント。
  - Refinerステージにおけるフォールバック発生および例外発生のトラッキング。
- **検索結果の制約**:
  - `rag_top_k` に基づく `reranked` リストのスライス、および `merged` リストへの全ヒット保持。

**実行コマンド:**
`uv run pytest tests/test_rag_quality_regression.py -v`

### 8.2 参考

本節は `tests/test_rag_quality_regression.py` のスコープに限定したものです。以下のファイルには、各ステージやサービス層を個別にカバーする他のテストが含まれています。
- `test_rag_pipeline.py`
- `test_rag_pipeline_stage.py`
- `test_rag_pipeline_service.py`
- `test_rag_pipeline_mcp_service.py`
- `test_mcp_rag_pipeline.py`

**参考（Strongly implied by code、本ドキュメントのスコープ外）:** `tests/` 配下にはこのほか `test_rag_pipeline.py`、`test_rag_pipeline_stage.py`、`test_rag_pipeline_service.py`、`test_rag_pipeline_mcp_service.py`、`test_mcp_rag_pipeline.py` が存在し、ステージ単体（`MqeStage`/`SearchStage`/`FusionStage`/`RerankStage`/`AugmentStage`）や `pipeline_service`/MCPサービス層をそれぞれ個別にカバーしている。本節は決定論的な品質リグレッション（`test_rag_quality_regression.py`）に限定して記載する。

---

## Related Documents

- `03_rag_00_document-guide.md`
- `03_rag_01_system_overview.md`
- `03_rag_03_01_query_pipeline-overview.md`
- `03_rag_03_03_query_pipeline-context-and-diagnostics.md`
- `03_rag_03_04_query_pipeline-search-stages.md`
- `03_rag_03_05_query_pipeline-augment-stages.md`
- `03_rag_03_06_query_pipeline-helpers-and-cache.md`
- `03_rag_03_06_query_pipeline-helpers-and-cache.md`
- `03_rag_04_05_dto-types.md`
- `03_rag_05_1-configuration-reference.md`

## Keywords

rag-tests
quality-regression
semantic-cache-generation
refiner-diagnostics
rag
