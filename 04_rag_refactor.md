# 04_rag_refactor.md — scripts/rag/ リファクタリング計画

## 1. 現状分析

`scripts/rag/` のモジュール構成と課題:

| ファイル | 行数 | 内容 | 課題 |
|---|---|---|---|
| `__init__.py` | 0 | 空 | パッケージエクスポートがない |
| `models.py` | 192 | DTO(20種) — config/data/result/audit が混在 | **巨大**。責務が4種類に分裂すべき |
| `pipeline.py` | 325 | RagPipeline orchestrator | 9モジュールからインポート。外部RAGサービス・キャッシュ・リファイナー・フォーマットが混在 |
| `llm.py` | 413 | RagLLM + embedding utility | MQE, rerank, summarization, refining, embedding が混在 |
| `repository.py` | 326 | RagRepository, RagScorer | Sudachi tokenization, FTS query, search, scoring が混在 |
| `utils.py` | 123 | cosine_sim, sanitize, normalize, validate | なし（適切に分離済み） |
| `cache.py` | 93 | SemanticCache | なし（適切に分離済み） |
| `stage.py` | 31 | PipelineContext, PipelineStage Protocol | なし（適切に分離済み） |
| `types.py` | 77 | RawHit/MergedHit/RankedHit TypedDict | なし（適切に分離済み） |
| `enums.py` | 39 | LanguageCode, PipelineStageName等 | なし |
| `exceptions.py` | 33 | RagLayerError等 | なし |
| `stages/*` | ~180 | 5ステージクラス | なし（適切に分離済み） |
| `ingestion/` | ~1400 | crawler/chunker/ingester | 別フェーズで対象 |

## 2. 計画対象

### 2.1 models.py の分割（最優先）

**現状:** 192行で config/data/result/audit の4種類のdataclassが混在

**目標:**
- `rag/models_config.py` — Config DTOs (`MqeConfig`, `FusionConfig`, `RerankConfig`, `SearchConfig`, `ChunkSplitterConfig`, `IngesterConfig`, `PipelineConfig`)
- `rag/models_data.py` — Data DTOs (`EmbeddingResponse`, `CrawlTarget`, `ChunkDocument`, `ChunkRecord`, `RegisteredDocument`, `CacheEntry`, `TwoStageFetchResult`)
- `rag/models_result.py` — Result DTOs (`ExpandedQuerySet`, `SkipInfo`, `RagSearchRequest`, `RagSearchResult`, `PipelineExecutionResult`, `SearchDocsResult`, `SanitizeResult`)
- `rag/models_audit.py` — Audit DTOs (`AuditLogRecord`, `ApprovalDecision`)

**後方互換:** `rag/models.py` を re-export stub に変更（既存インポートを壊さない）

### 2.2 pipeline.py の分割

**現状:** 325行で外部RAGサービス委譲・セマンティックキャッシュ・リファイナー・フォーマットが混在

**目標:**
- `rag/pipeline.py` — RagPipeline core orchestration (MQE→search→RRF→rerank)
- `rag/pipeline_service.py` — External RAG service delegation (`_augment_http`)
- `rag/pipeline_refiner.py` — Context refiner (`_augment_refiner`)

**後方互換:** `rag/pipeline.py` で再エクスポート（既存インポートを壊さない）

### 2.3 __init__.py の整備

**目標:** パッケージの公開APIを一元エクスポート

## 3. ブラストレイサー表

### models.py 分割の影響

| ファイル | 変更内容 | 影響 |
|---|---|---|
| `rag/models_config.py` | 新規作成 | インポート追加が必要 |
| `rag/models_data.py` | 新規作成 | インポート追加が必要 |
| `rag/models_result.py` | 新規作成 | インポート追加が必要 |
| `rag/models_audit.py` | 新規作成 | インポート追加が必要 |
| `rag/models.py` | re-export stub に変更 | 既存インポート維持 |
| `rag/cache.py` | `rag.models.CacheEntry` → `rag.models_data.CacheEntry` | インポートパス変更 |
| `rag/enums.py` | 変更なし | なし |
| `rag/utils.py` | `rag.models.SanitizeResult` → `rag.models_result.SanitizeResult` | インポートパス変更 |
| `rag/stages/mqe.py` | `rag.models.MqeConfig` → `rag.models_config.MqeConfig` | インポートパス変更 |
| `rag/stages/search.py` | `rag.models.SearchConfig` → `rag.models_config.SearchConfig` | インポートパス変更 |
| `rag/stages/fusion.py` | `rag.models.FusionConfig` → `rag.models_config.FusionConfig` | インポートパス変更 |
| `rag/stages/rerank.py` | `rag.models.RerankConfig` → `rag.models_config.RerankConfig` | インポートパス変更 |
| `rag/repository.py` | 各種 Config → models_config | インポートパス変更 |
| `rag/llm.py` | 各種 Config → models_config | インポートパス変更 |

### pipeline.py 分割の影響

| ファイル | 変更内容 | 影響 |
|---|---|---|
| `rag/pipeline_service.py` | 新規作成 | インポート追加が必要 |
| `rag/pipeline_refiner.py` | 新規作成 | インポート追加が必要 |
| `rag/pipeline.py` | core orchestrationのみ + re-export stub | 行数削減 |

## 4. 手順（フェーズ別）

### Step 1: models の分割
- `models_config.py`, `models_data.py`, `models_result.py`, `models_audit.py` を作成
- `models.py` を re-export stub に変更
- 全インポートを更新
- ruff + mypy チェック

### Step 2: pipeline の分割 ✅ 完了
- `pipeline_service.py` — 外部 RAG サービス委譲 (`call_rag_service()`)
- `pipeline_refiner.py` — コンテキストリファイナー (`refine_context()`)
- `pipeline.py` — core orchestration のみ + `_augment_http`/`_augment_refiner` は new module に委譲
- ruff + mypy + lint-imports 全チェック OK
- 関連テスト全通過 (test_rag_utils.py, test_chunk_splitter.py, test_rag_pipeline_mcp_service.py, test_agent_rag.py)

### Step 3: __init__.py の整備
- パッケージ公開APIを定義

### Step 4: 最終検証
- ruff format + ruff check
- mypy scripts/
- lint-imports
- pytest (affected tests)

## 5. 後方互換性

すべての既存 import パスは re-export stub によって維持される:

```python
# これらすべてが動作し続ける:
from rag.models import PipelineConfig, EmbeddingResponse, TwoStageFetchResult
from rag.pipeline import RagPipeline, RagPipelineError, fetch_full_document
```
