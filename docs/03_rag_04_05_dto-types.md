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
| `result_source` | `str \| None` | 結果の取得元 (remote/local/fallback)。デフォルト`None` |

## 実装上の補足

- `RagPipeline.run()` (`scripts/rag/pipeline.py`) の `PipelineRunResult` 生成箇所
  (同ファイル351行目付近) では `result_source` 引数を渡していない。そのため
  `run()` が返す `PipelineRunResult.result_source` は常に既定値 `None` のままとなる。
  [Explicit in code] — コンストラクタ呼び出しに当該キーワード引数が存在しない。
- 実際に「remote/local/fallback」の結果取得元を保持しているのは
  `PipelineRunResult` ではなく `rag/models_result.py` の `SearchDiagnostics.result_source`
  (`ResultSource` enum) であり、`RagPipeline.augment()` の内部でHTTPモードの成否に応じて設定される。
  [Explicit in code]
- したがって `PipelineRunResult.result_source` フィールド自体は、現状の呼び出し経路では
  実質的に未使用 (常にNone) である可能性が高い。
  [Needs confirmation] — `run()` を呼ぶ他の経路 (プラグイン等) で明示的に設定される
  ケースがあるかは未確認。

## Related Documents

- [03_rag_04_05_dto-types.md](03_rag_04_01_dto-models_data.md)
- [03_rag_04_04_dto-models_config.md](03_rag_04_04_dto-models_config.md)

## Keywords

dto
data-model
pipeline-result
