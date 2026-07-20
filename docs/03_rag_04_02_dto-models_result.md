---
title: "6.2 models_result.py (`scripts/rag/models_result.py`)"
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

# 6.2 models_result.py (`scripts/rag/models_result.py`)

**ResultSource** — RAG結果の取得元。

| Value | Description |
|---|---|
| `"remote"` | HTTP RAGサービス |
| `"local"` | インプロセスパイプライン |
| `"fallback"` | HTTP失敗時のインプロセスフォールバック |

**HttpResultKind** — HTTP RAG結果の分類。

| Value | Description |
|---|---|
| `"success"` | 空でないコンテキストが返された |
| `"empty"` | 空のコンテキスト (正当な空結果) |
| `"error"` | HTTPエラー経路 |
| `"not_used"` | HTTPモードが非アクティブ |

**ExpandedQuerySet** — MQE展開結果。

| Field | Type | Description |
|---|---|---|
| `status` | `MqeStatus` | 展開のステータス |
| `queries` | `list[str]` | 展開後のクエリ群 |

**SkipInfo** — チャンク処理のスキップ記録。

| Field | Type | Description |
|---|---|---|
| `path` | `str` | スキップされたファイルパス |
| `reason` | `str` | スキップの理由 |

**RagSearchRequest** — 検索リクエストDTO。

| Field | Type | Default | Description |
|---|---|---|---|
| `query` | `str` | (required) | 検索クエリ |
| `top_k` | `int` | `5` | 返却する結果数 |

**RagSearchResult** — 検索結果DTO。

| Field | Type | Description |
|---|---|---|
| `query` | `str` | 元のクエリ |
| `hits` | `list[Any]` | ランク付けされたヒット結果 (Phase 3-1以降は`list[RankedHit]`型) |
| `context_str` | `str` | コンテキスト文字列 |

**PipelineExecutionResult** — パイプライン実行結果。

| Field | Type | Default | Description |
|---|---|---|---|
| `success` | `bool` | (required) | 実行が成功したか |
| `processed` | `int` | (required) | 処理されたチャンク数 |
| `failed` | `int` | (required) | 失敗数 |
| `errors` | `list[str]` | `[]` | エラーメッセージ |

**SearchDocsResult** — ドキュメント検索結果。

| Field | Type | Description |
|---|---|---|
| `query` | `str` | 元のクエリ |
| `results` | `list[str]` | 結果文字列 |
| `total` | `int` | 結果の総数 |

**SanitizeResult** — プロンプトインジェクションのサニタイズ結果。

| Field | Type | Description |
|---|---|---|
| `text` | `str` | サニタイズ後のテキスト |
| `was_sanitized` | `bool` | テキストが変更されたか |
| `patterns_detected` | `list[str]` | 検出されたインジェクションパターン |

**SearchDiagnostics** — 単一の検索呼び出しに対する診断カウンタ。

| Field | Type | Default | Description |
|---|---|---|---|
| `embed_ok` | `int` | `0` | 成功した埋め込み呼び出し数 |
| `embed_failed` | `int` | `0` | 失敗した埋め込み呼び出し数 |
| `fts_errors` | `int` | `0` | FTS5クエリエラー数 |
| `result_source` | `ResultSource` | `LOCAL` | 結果の取得元 (remoteモード) |
| `http_result_kind` | `HttpResultKind` | `NOT_USED` | HTTP結果の分類 (remoteモード) |
| `remote_status_code` | `int \| None` | `None` | リモートRAGサービスからのHTTPステータスコード |
| `remote_latency_ms` | `float \| None` | `None` | リモート呼び出しのレイテンシ (ミリ秒) |
| `fallback_reason` | `str \| None` | `None` | インプロセスフォールバックが発生した理由 (該当する場合) |

### 実装意図 (Implementation note)

- `ResultSource`・`HttpResultKind` は `StrEnum` として定義され、他のDTO(`ExpandedQuerySet` 以下)は全て `@dataclass(frozen=True)`。`03_rag_04_01_dto-models_data.md` と同様、DTO層全体で不変性を統一する設計方針が読み取れる(Explicit in code / Strongly implied by code)。
- `SearchDiagnostics` の `result_source` / `http_result_kind` / `remote_status_code` / `remote_latency_ms` / `fallback_reason` は、コード内コメントで "Remote mode fields (new)" と区分されている(Explicit in code、`scripts/rag/models_result.py`)。`embed_ok` / `embed_failed` / `fts_errors` がローカル実行時からの既存カウンタで、remote系フィールドはHTTP RAGサービス導入後に追加されたことが示唆される(Strongly implied by code)。
- `fallback_reason` は `scripts/rag/pipeline.py` と `scripts/rag/http_augment.py` でHTTP呼び出し失敗時のインプロセスフォールバック理由を記録するために設定される(Explicit in code)。

## Related Documents

- [03_rag_04_01_dto-models_data.md](03_rag_04_01_dto-models_data.md)
- [03_rag_00_document-guide.md](03_rag_00_document-guide.md)

## Keywords

dto
data-model
frozen-dataclass
SearchDiagnostics
