---
title: "6.1 models_data.py (`scripts/rag/models_data.py`)"
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

# 6.1 models_data.py (`scripts/rag/models_data.py`)

**EmbeddingResponse** — 埋め込みAPIからのレスポンス。

| Field | Type | Description |
|---|---|---|
| `embedding` | `list[float]` | 埋め込みベクトル |
| `model` | `str \| None` | モデル名 (省略可) |

**CrawlTarget** — WebCrawlerのクロール操作の対象。

| Field | Type | Description |
|---|---|---|
| `url` | `str` | クロール対象のURL |
| `lang` | `LanguageCode` | 言語ヒント (`"en"` / `"ja"`) |

**ChunkDocument** — パイプラインステージ間で受け渡されるチャンクデータ。

| Field | Type | Default | Description |
|---|---|---|---|
| `url` | `str` | (required) | ソースドキュメントのURL |
| `title` | `str` | (required) | ソースドキュメントのタイトル |
| `lang` | `str` | (required) | 言語コード (`"ja"` / `"en"`) |
| `content` | `str` | (required) | チャンクのテキスト |
| `code_blocks` | `list[str]` | `[]` | コードブロックの内容 |
| `etag` | `str \| None` | `None` | 更新検知用のETag |
| `last_modified` | `str \| None` | `None` | Last-Modifiedタイムスタンプ |
| `chunking_strategy` | `str` | `"text"` | チャンク分割ストラテジー |
| `normalized_content` | `str \| None` | `None` | Sudachiで正規化されたテキスト (日本語のみ) |
| `chunk_index` | `int` | `0` | ドキュメント内での位置 |
| `source_file` | `str` | `""` | 元のクローラー出力ファイル名 |
| `chunk_type` | `str` | `""` | `"text"` または `"code"` |

**ChunkRecord** — 埋め込みベクトルを持つチャンクデータ (クエリパイプラインで使用)。

| Field | Type | Default | Description |
|---|---|---|---|
| `chunk_id` | `str` | (required) | チャンク識別子 |
| `url` | `str` | (required) | ソースドキュメントのURL |
| `title` | `str` | (required) | ソースドキュメントのタイトル |
| `lang` | `str` | (required) | 言語コード |
| `content` | `str` | (required) | チャンクのテキスト |
| `embedding` | `list[float]` | `[]` | 埋め込みベクトル |

**RegisteredDocument** — ドキュメント登録レコード。

| Field | Type | Description |
|---|---|---|
| `url` | `str` | ソースURL |
| `lang` | `str` | 言語コード |
| `chunk_count` | `int` | チャンク数 |

**CacheEntry** — セマンティックキャッシュエントリ。

| Field | Type | Default | Description |
|---|---|---|---|
| `embedding` | `list[float]` | (required) | キャッシュされた埋め込みベクトル |
| `context_str` | `str` | (required) | キャッシュされたコンテキスト文字列 |
| `history_context` | `str` | `""` | 関連する会話履歴 |
| `generation` | `int` | `0` | キャッシュ無効化用の世代カウンタ |

**TwoStageFetchResult** — HTTP RAGサービス呼び出しの結果。

| Field | Type | Description |
|---|---|---|
| `hits` | `list[Any]` | ヒット結果 (インプロセス時はRagHit、HTTPモード時はdict) |
| `min_score_applied` | `float` | フィルタリングに使用されたrag_min_score |
| `max_chunks_per_doc` | `int` | 適用されたドキュメント単位の重複排除上限 |

## 実装意図 (Implementation note)

- `scripts/rag/models_data.py` の全DTOは `@dataclass(frozen=True)` として定義されている(Explicit in code)。生成後の書き換えを禁止し、パイプラインステージ間で受け渡す際の意図しない変更を防ぐ設計と読み取れる(Strongly implied by code)。
- `CrawlTarget.lang` の型は `str` ではなく `rag.enums.LanguageCode`(`StrEnum`、値は `"en"`/`"ja"`)。他のDTO(`ChunkDocument.lang` 等)は素の `str` のままであり、DTO間で言語表現の型が統一されていない(Explicit in code)。
- `TwoStageFetchResult.hits` は `list[Any]` で、インプロセス実行時は `RagHit`、HTTPモード時は `dict` が格納される。呼び出しモードによって要素の実体型が変わることはコード中のコメントに明記されている(Explicit in code、`scripts/rag/models_data.py` の型注釈コメント)。実際の利用箇所は `scripts/rag/pipeline.py`・`scripts/rag/pipeline_service.py`・`scripts/rag/http_augment.py`。

## Related Documents

- [03_rag_04_05_dto-types.md](03_rag_04_05_dto-types.md)
- [03_rag_00_document-guide.md](03_rag_00_document-guide.md)

## Keywords

dto
data-model
frozen-dataclass
LanguageCode
