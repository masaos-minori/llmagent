---
title: "RAG Query Pipeline Context and Diagnostics"
category: rag
tags:
  - pipeline-context
  - search-diagnostics
related:
  - 03_rag_00_document-guide.md
  - 03_rag_01_system_overview-part1.md
  - 03_rag_03_01_query_pipeline-overview.md
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

## 4. PipelineContext Dataclass (`scripts/rag/stage.py`)

```python
ctx = PipelineContext(query="search query", history_context="conversation history")
```

| フィールド | 型 | 初期値 | 変更元 |
|---|---|---|---|
| `query` | `str` | （必須） | — |
| `history_context` | `str` | `""` | — |
| `queries` | `list[str]` | `[]` | `MqeStage` |
| `search_results` | `list[list[RawHit]]` | `[]` | `SearchStage` |
| `merged` | `list[RagHit]` | `[]` | `FusionStage` |
| `reranked` | `list[RagHit]` | `[]` | `RerankStage` |
| `augment_result` | `str` | `""` | `AugmentStage` |
| `stage_results` | `list[StageResult]` | `[]` | `RagPipeline.run()` |
| `search_diagnostics` | `SearchDiagnostics` | `SearchDiagnostics()`（default_factory） | `SearchStage` — 検索中にembed_ok/embed_failed/fts_errorsを埋めた新しい `SearchDiagnostics` オブジェクトで完全に置き換えられる；HTTPモードでは、HTTPのaugmentハンドラが `dataclasses.replace()` により `result_source`、`http_result_kind`、`remote_status_code`、`remote_latency_ms` で置き換える |

### 4.2 SearchDiagnostics (`scripts/rag/models_result.py`)

```python
from rag.models_result import SearchDiagnostics, ResultSource, HttpResultKind
```

| フィールド | 型 | デフォルト | 説明 |
|---|---|---|---|
| `embed_ok` | int | 0 | 埋め込み成功件数 |
| `embed_failed` | int | 0 | 埋め込み失敗件数 |
| `fts_errors` | int | 0 | FTS5クエリのエラー件数 |
| `result_source` | ResultSource | ResultSource.LOCAL | 最終結果のソース（HTTPモードのみ） |
| `http_result_kind` | HttpResultKind | HttpResultKind.NOT_USED | HTTP RAG結果の分類（HTTPモードのみ） |
| `remote_status_code` | int \| None | None | リモートサービスからのHTTPステータスコード（HTTPモードのみ） |
| `remote_latency_ms` | float \| None | None | リモート呼び出しのレイテンシ（ミリ秒、HTTPモードのみ） |
| `fallback_reason` | str \| None | None | HTTPモードが失敗した際のフォールバック理由（HTTPモードのみ） |

### 4.3 get_diagnostics() の戻り値 (`scripts/rag/pipeline.py:562`)

```python
pipeline.get_diagnostics() -> dict
```

以下のキーを持つ構造化された診断情報を返す。

| キー | 型 | 説明 |
|---|---|---|
| `stage_results` | `list[dict]` | ステージごとの結果（`last_stage_results` と同じ） |
| `timings` | `dict[str, float]` | 各ステージの実測秒数（`last_timings` と同じ） |
| `fetch_result` | `dict \| None` | フェッチ結果: `{hits: int, min_score_applied: float}` または `None` |
| `fusion_mode` | `str` | `"rrf"` または `"dedup_only"` |
| `http_result_kind` | `str \| None` | HTTPモードの分類（`_http_result_kind` と同じ） |
| `fallback_count` | `int` | フォールバックが発生したステージ数 |
| `fallback_reasons` | `list[str]` | すべてのステージのフォールバック理由文字列 |
| `refiner_fallback_count` | `int` | リファイナーのフォールバック回数 |
| `refiner_returned_empty` | `int` | リファイナーが空の内容を返した回数 |
| `refiner_exception_count` | `int` | リファイナーの例外発生回数 |
| `refiner_exception` | `bool` | リファイナーの例外が1件でも発生した場合はTrue |
| `hit_counts` | `dict[str, int]` | `{merged: int}` — マージ後のヒット数 |
| `search_diagnostics` | `dict` | `{embed_ok, embed_failed, fts_errors, degraded}` |

**`run()` / `augment()` の前に呼び出しても安全** — 空/ゼロ値を返す。呼び出し元は `orjson.dumps(pipeline.get_diagnostics())` でシリアライズすること。

```
StageResult = TypedDict with keys:
  stage_name: str         — class name of the stage
  status: str             — "success" | "fallback" | "failure"
  elapsed_seconds: float  — wall-clock seconds for the stage
  fallback_reason: str | None — reason when status is "failure" or "fallback"; None on success
```

`RagPipeline.run()` はステージごとに `StageResult` を記録し、その全体を
`pipeline.last_stage_results: list[StageResult]` として公開する。同じリストが
デバッグと検査のために `PipelineContext.stage_results` にも保存される。

---

## Related Documents

- `03_rag_00_document-guide.md`
- `03_rag_01_system_overview-part1.md`
- `03_rag_03_01_query_pipeline-overview.md`
- `03_rag_04_05_dto-types.md`
- `03_rag_05_1-configuration-reference.md`

## Keywords

pipeline-context
search-diagnostics
rag
