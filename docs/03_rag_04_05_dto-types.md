---
title: "6.3 types.py (`scripts/rag/types.py`)"
category: rag
tags:
  - rag
  - dto
  - data-model
related:
  - 03_rag_00_document-guide.md
  - 03_rag_04_05_dto-types.md
source:
  - 03_rag_04_05_dto-types.md
---

# 6.3 types.py (`scripts/rag/types.py`)

### 6.3 types.py (`scripts/rag/types.py`)

**RagQuery** — 省略可能なコンテキスト付きのクエリ。

| Field | Type | Default | Description |
|---|---|---|---|
| `query` | `str` | (required) | クエリ文字列 |
| `context` | `str` | `""` | 省略可能なコンテキスト |

**PipelineRunResult** — パイプライン実行結果。

| Field | Type | Description |
|---|---|---|
| `queries` | `list[str]` | MQEで展開されたクエリ群 |
| `search_results` | `list[list[RawHit]]` | クエリごとの検索結果 |
| `merged` | `list[RagHit]` | RRFで統合されたヒット結果 |
| `reranked` | `list[RagHit]` | リランク後のヒット結果 |
| `stage_results` | `list[StageResult]` | 各ステージの実行結果 |
| `diagnostics` | `SearchDiagnostics` | 検索診断情報 |
| `result_source` | `str \| None` | 結果の取得元 (remote/local/fallback) |


## Related Documents

- [03_rag_04_05_dto-types.md](03_rag_04_01_dto-models_data.md)

## Keywords

dto
data-model
