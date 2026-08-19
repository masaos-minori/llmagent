
title: "ChunkSplitter Detail (Part 1)"
category: rag
tags:
  - chunk-splitter
  - chunking-strategies
  - sudachi
  - markdown-heading
  - crawler
  - rag
related:
  - 03_rag_00_document-guide.md
  - 03_rag_01_system_overview.md
  - 03_rag_02_01_ingestion_pipeline-overview.md
  - 03_rag_02_02_ingestion_pipeline-crawler.md
  - 03_rag_02_04_ingestion_pipeline-ingester.md
  - 03_rag_02_07_ingestion_pipeline-utils.md
  - 03_rag_05_1-configuration-reference.md
source:
  - 03_rag_02_03_ingestion_pipeline-chunksplitter.md


# RAG インジェクションパイプライン

- システム概要 → [03_rag_01_system_overview.md](03_rag_01_system_overview.md)
- 設定 → [03_rag_05_1-configuration-reference.md](03_rag_05_1-configuration-reference.md)

---

## 3. ChunkSplitter (`scripts/rag/ingestion/chunk_splitter.py`)

### 3.1 クラス概要

`ChunkSplitter` — `rag-src/*.json` ファイルを言語とコンテンツタイプに応じてチャンクに分割し、
`rag-src/chunk/` に保存する。冪等性あり: `{stem}-0000.json` センチネルが存在する場合はスキップする（`--force` で上書き可能）。

**モジュールレベルの定数**

このモジュールは以下の定数を定義しています。詳細はソースコードを参照してください。特に、`MIN_HEADING_LINES_FOR_MARKDOWN = 2` の根拠は未確認です（Needs Confirmation）。

**Typed dict**

| TypedDict | 用途 |
|---|---|
| `CrawlFilePayload` | クロール出力JSONファイル用の型付きdict（url, title, lang, content, code_blocksは必須；etag, last_modifiedはNotRequiredで任意） |
| `ChunkOutputPayload` | チャンク出力JSONファイル用の型付きdict（schema_version, artifact_type, created_by, url, title, lang, source_file, chunk_index, chunk_type, contentは必須；normalized_contentはNotRequiredで任意） |
| `ChunkMetadata` | 出力ペイロードに ** で展開するための任意メタデータdict（total=False）。url、title、lang、etag、last_modified、source_file、chunking_strategyを含む全フィールドが任意 |

> 根拠: Explicit in code — `CrawlFilePayload` と `ChunkOutputPayload` は `chunk_splitter.py` 内で型として宣言されているが、同ファイル内の実処理では型注釈として参照されていない（実際の入出力は `ChunkJsonRaw`（`pipeline_utils.py`）や `dict[str, object]` 経由で扱われる）。

**継承**

`ChunkSplitter` は多重継承により `ChunkEnglishMixin` と `ChunkJapaneseMixin` の両方を継承する。
メソッド解決順序: `ChunkSplitter → ChunkEnglishMixin → ChunkJapaneseMixin → object`。

**公開メソッド**

このモジュールは以下の公開メソッドを提供します。詳細はソースコードを参照してください。

### 3.1.1 Markdown見出しチャンク化の設定

| パラメータ | デフォルト | 説明 |
|---|---|---|
| `md_index_enable` | False | .md以外のファイルに対するヒューリスティックなMarkdown判定を有効化する |
| `md_snippet_max_chars` | 600 | 文単位のチャンク化にフォールバックする前の、1つのMarkdown見出しセクションあたりの最大文字数 |

### 3.1.2 チャンク化パラメータ（crawlerと共有）

| パラメータ | デフォルト | 説明 |
|---|---|---|
| `min_chunk` | 40 | チャンクの最小文字数。これ未満のチャンクはノイズとして破棄される |
| `max_chunk` | 500 | チャンクの最大文字数。これを超えるテキストは分割される |
| `chunk_overlap` | 50 | スライディングウィンドウのチャンク重複（文字数）。直前のチャンク末尾からこの文字数を先頭に付加する；0は無効化を意味する |
| `en_stopwords` | — | チャンク化から除外する英語のストップワード（`config/chunk_splitter.toml`で定義。旧docs記載の`rag_pipeline.toml`は存在しないため訂正） |
| `ja_stop_pos` | — | 日本語でストップワードとして扱うSudachiの品詞カテゴリ。デフォルト値: `["助詞", "助動詞", "補助記号", "空白", "感動詞", "接続詞"]`（`config/chunk_splitter.toml`で定義） |

> 根拠: Explicit in code — `scripts/rag/ingestion/chunk_splitter.py::__init__` は `ConfigLoader().load("chunk_splitter.toml")` を使用し、`config/chunk_splitter.toml` に `en_stopwords`/`ja_stop_pos` が定義されている。`config/rag_pipeline.toml` というファイルは本リポジトリに存在しない。

## Related Documents

- `03_rag_00_document-guide.md`
- `03_rag_01_system_overview.md`
- `03_rag_02_01_ingestion_pipeline-overview.md`
- `03_rag_02_02_ingestion_pipeline-crawler.md`
- `03_rag_02_04_ingestion_pipeline-ingester.md`
- `03_rag_02_07_ingestion_pipeline-utils.md`
- `03_rag_05_1-configuration-reference.md`
- `03_rag_02_03_ingestion_pipeline-chunksplitter.md`

## Keywords

chunk-splitter
chunking-strategies
sudachi
markdown-heading
crawler
rag

# RAG インジェクションパイプライン

- システム概要 → [03_rag_01_system_overview.md](03_rag_01_system_overview.md)
- 設定 → [03_rag_05_1-configuration-reference.md](03_rag_05_1-configuration-reference.md)

---

## 3a. ChunkSplitter (`scripts/rag/ingestion/chunk_splitter.py`)

### 3.1 クラス概要

`ChunkSplitter` — `rag-src/*.json` ファイルを言語とコンテンツタイプに応じてチャンクに分割し、
`rag-src/chunk/` に保存する。冪等性あり: `{stem}-0000.json` センチネルが存在する場合はスキップする（`--force` で上書き可能）。

**モジュールレベルの定数**

このモジュールは以下の定数を定義しています。詳細はソースコードを参照してください。特に、`MIN_HEADING_LINES_FOR_MARKDOWN = 2` の根拠は未確認です（Needs Confirmation）。

**Typed dict**

| TypedDict | 用途 |
|---|---|
| `CrawlFilePayload` | クロール出力JSONファイル用の型付きdict（url, title, lang, content, code_blocksは必須；etag, last_modifiedはNotRequiredで任意） |
| `ChunkOutputPayload` | チャンク出力JSONファイル用の型付きdict（schema_version, artifact_type, created_by, url, title, lang, source_file, chunk_index, chunk_type, contentは必須；normalized_contentはNotRequiredで任意） |
| `ChunkMetadata` | 出力ペイロードに ** で展開するための任意メタデータdict（total=False）。url、title、lang、etag、last_modified、source_file、chunking_strategyを含む全フィールドが任意 |

> 根拠: Explicit in code — `CrawlFilePayload` と `ChunkOutputPayload` は `chunk_splitter.py` 内で型として宣言されているが、同ファイル内の実処理では型注釈として参照されていない（実際の入出力は `ChunkJsonRaw`（`pipeline_utils.py`）や `dict[str, object]` 経由で扱われる）。

**継承**

`ChunkSplitter` は多重継承により `ChunkEnglishMixin` と `ChunkJapaneseMixin` の両方を継承する。
メソッド解決順序: `ChunkSplitter → ChunkEnglishMixin → ChunkJapaneseMixin → object`。

**公開メソッド**

このモジュールは以下の公開メソッドを提供します。詳細はソースコードを参照してください。

### 3.1.1 Markdown見出しチャンク化の設定

| パラメータ | デフォルト | 説明 |
|---|---|---|
| `md_index_enable` | False | .md以外のファイルに対するヒューリスティックなMarkdown判定を有効化する |
| `md_snippet_max_chars` | 600 | 文単位のチャンク化にフォールバックする前の、1つのMarkdown見出しセクションあたりの最大文字数 |

### 3.1.2 チャンク化パラメータ（crawlerと共有）

| パラメータ | デフォルト | 説明 |
|---|---|---|
| `min_chunk` | 40 | チャンクの最小文字数。これ未満のチャンクはノイズとして破棄される |
| `max_chunk` | 500 | チャンクの最大文字数。これを超えるテキストは分割される |
| `chunk_overlap` | 50 | スライディングウィンドウのチャンク重複（文字数）。直前のチャンク末尾からこの文字数を先頭に付加する；0は無効化を意味する |
| `en_stopwords` | — | チャンク化から除外する英語のストップワード（`config/chunk_splitter.toml`で定義。旧docs記載の`rag_pipeline.toml`は存在しないため訂正） |
| `ja_stop_pos` | — | 日本語でストップワードとして扱うSudachiの品詞カテゴリ。デフォルト値: `["助詞", "助動詞", "補助記号", "空白", "感動詞", "接続詞"]`（`config/chunk_splitter.toml`で定義） |

> 根拠: Explicit in code — `scripts/rag/ingestion/chunk_splitter.py::__init__` は `ConfigLoader().load("chunk_splitter.toml")` を使用し、`config/chunk_splitter.toml` に `en_stopwords`/`ja_stop_pos` が定義されている。`config/rag_pipeline.toml` というファイルは本リポジトリに存在しない。

## Related Documents

- `03_rag_00_document-guide.md`
- `03_rag_01_system_overview.md`
- `03_rag_02_01_ingestion_pipeline-overview.md`
- `03_rag_02_02_ingestion_pipeline-crawler.md`
- `03_rag_02_04_ingestion_pipeline-ingester.md`
- `03_rag_02_07_ingestion_pipeline-utils.md`
- `03_rag_05_1-configuration-reference.md`
- `03_rag_02_03_ingestion_pipeline-chunksplitter.md`

## Keywords

chunk-splitter
chunking-strategies
sudachi
markdown-heading
crawler
rag



# RAG インジェクションパイプライン

- システム概要 → [03_rag_01_system_overview.md](03_rag_01_system_overview.md)
- 設定 → [03_rag_05_1-configuration-reference.md](03_rag_05_1-configuration-reference.md)

---

## 3b. ChunkSplitter (`scripts/rag/ingestion/chunk_splitter.py`)

### 3.1.3 Markdownソース判定の挙動

`.md`、`.markdown`、`.mdx` で終わるURLは、`md_index_enable` に関わらず常に見出しチャンク化を使用する。
.md以外のファイルは、`md_index_enable=true` の場合のみヒューリスティック判定（内容に見出し行が2行以上）を使用する。

### 3.1.4 Markdown見出しチャンク化の挙動

Markdownの見出し（# から ######）でテキストを分割する。`md_snippet_max_chars` 文字を超えるセクションは、さらに文単位のチャンク化で分割される。

> 根拠: Explicit in code — Markdown見出しチャンク化は超過セクションを英語の文境界分割にフォールバックする。`lang` が `"ja"` であっても日本語形態素解析（Sudachi）は適用されず、`normalized_content` は生成されない（見出しチャンク全体で `normalized_content` は常に空扱い、後述の通り）。

### 3.2 分割戦略

| コンテンツタイプ | 戦略 |
|---|---|
| 日本語テキスト | Sudachi SplitMode.Cによる形態素解析；`(元の文, 正規化形をスペース結合したもの)` のペア |
| 英語テキスト | 正規表現による文境界分割（`(?<=[.!?])\s+`）；短い段落を結合し、ストップワード除去後にmin_chunk未満のチャンクは破棄 |
| `.md`/`.markdown`/`.mdx` のURL | 見出し境界分割（`#`/`##`/`###`）；`md_index_enable` に関わらず常に適用される |
| .md以外で見出し行が2行以上の内容 | 見出し境界分割；`md_index_enable=true` の場合のみ適用 |
| コードブロック | 空行分割（言語に依存しない）；ストップワード除去や形態素解析の対象外 |

- 日本語チャンク: `content` = 元のテキスト、`normalized_content` = Sudachiによる正規化形
- 英語/コードチャンク: `normalized_content = null`
- `chunk_type`: `"text"` または `"code"`
- `chunking_strategy`: `"text"` または `"heading"`

> 根拠: Explicit in code — 見出しチャンク化（`chunking_strategy="heading"`）は `lang` に関わらず `normalized_content` を常に `null` にする。すなわち日本語のMarkdownソースは見出しチャンク化が優先され、Sudachi正規化はスキップされる。FTS5は `COALESCE(normalized_content, content)` により元テキスト（`content`）をそのままインデックス化する。

### 3.3 CLI引数

| 引数 | 説明 | デフォルト |
|---|---|---|
| `--file PATH` | 単一ファイルのみ処理する（パスはrag_src_dirからの相対パス） | rag-src/内の未処理の `.json` すべて |
| `--force` | センチネルチェックを無視してチャンクを再生成する | false |

### 3.4 出力JSON形式

```json
{
  "schema_version": "1",
  "artifact_type": "chunk",
  "created_by": "chunk_splitter",
  "url": "https://example.com/page",
  "title": "Page title",
  "lang": "ja",
  "source_file": "20240101120000-example.json",
  "chunk_index": 0,
  "chunk_type": "text",
  "chunking_strategy": "text",
  "content": "original chunk text",
  "normalized_content": "normalized form (JA only; null for EN/code)",
  "etag": "optional-etag",
  "last_modified": "optional-http-date"
}
```

- `chunk_type`: `text` / `code`
- `chunking_strategy`: `text` / `heading`
- `normalized_content`: 日本語のみ（Sudachi正規化）、英語・コードはnull
- `source_file`: クローラ出力ファイル名から`.json`拡張子を除いたもの

### 3.5 エラーハンドリング

| ケース | 対応 |
|---|---|
| Sudachiのトークナイズエラー | `_normalize_ja_sentence()` が `TokenizationError`（`RagLayerError`/`RuntimeError`のサブクラス）を送出する。個別チャンク単位のtry/exceptは存在せず、`process_all()` のファイル単位ループの `except (OSError, RuntimeError, ValueError)` まで伝播する。結果として当該チャンクのみでなく **ファイル全体** の処理が失敗扱いになる |
| ファイル単位の失敗 | `ERROR` ログ（トレースバック付き、`logger.exception`）；次のファイルへ継続 |
| 既存チャンク（`{stem}-0000.json`） | `--force` がない限りスキップ |

### 3.6 ロギング

- **ファイル:** `/opt/llm/logs/chunk.log` + stderr
- **フォーマット:** `%(asctime)s %(levelname)s [%(funcName)s] %(message)s`

| レベル | タイミング |
|---|---|
| `INFO` | 処理済みファイル、生成されたチャンク、スキップされたファイル（URL付き） |
| `WARNING` | Sudachiエラー |
| `ERROR` | ファイル読み込みエラー、ファイル単位の失敗（トレースバック付き） |

### 3.7 設定

[03_rag_05_1-configuration-reference.md §1.1](03_rag_05_1-configuration-reference.md) を参照。

---

## Related Documents

- `03_rag_00_document-guide.md`
- `03_rag_01_system_overview.md`
- `03_rag_02_01_ingestion_pipeline-overview.md`
- `03_rag_02_02_ingestion_pipeline-crawler.md`
- `03_rag_02_04_ingestion_pipeline-ingester.md`
- `03_rag_02_07_ingestion_pipeline-utils.md`
- `03_rag_05_1-configuration-reference.md`
- `03_rag_02_03_ingestion_pipeline-chunksplitter.md`

## Keywords

chunk-splitter
chunking-strategies
sudachi
markdown-heading
crawler
rag

# RAG インジェクションパイプライン

- システム概要 → [03_rag_01_system_overview.md](03_rag_01_system_overview.md)
- 設定 → [03_rag_05_1-configuration-reference.md](03_rag_05_1-configuration-reference.md)

---

## 3c. ChunkSplitter (`scripts/rag/ingestion/chunk_splitter.py`)

### 3.1.3 Markdownソース判定の挙動

`.md`、`.markdown`、`.mdx` で終わるURLは、`md_index_enable` に関わらず常に見出しチャンク化を使用する。
.md以外のファイルは、`md_index_enable=true` の場合のみヒューリスティック判定（内容に見出し行が2行以上）を使用する。

### 3.1.4 Markdown見出しチャンク化の挙動

Markdownの見出し（# から ######）でテキストを分割する。`md_snippet_max_chars` 文字を超えるセクションは、さらに文単位のチャンク化で分割される。

> 根拠: Explicit in code — Markdown見出しチャンク化は超過セクションを英語の文境界分割にフォールバックする。`lang` が `"ja"` であっても日本語形態素解析（Sudachi）は適用されず、`normalized_content` は生成されない（見出しチャンク全体で `normalized_content` は常に空扱い、後述の通り）。

### 3.2 分割戦略

| コンテンツタイプ | 戦略 |
|---|---|
| 日本語テキスト | Sudachi SplitMode.Cによる形態素解析；`(元の文, 正規化形をスペース結合したもの)` のペア |
| 英語テキスト | 正規表現による文境界分割（`(?<=[.!?])\s+`）；短い段落を結合し、ストップワード除去後にmin_chunk未満のチャンクは破棄 |
| `.md`/`.markdown`/`.mdx` のURL | 見出し境界分割（`#`/`##`/`###`）；`md_index_enable` に関わらず常に適用される |
| .md以外で見出し行が2行以上の内容 | 見出し境界分割；`md_index_enable=true` の場合のみ適用 |
| コードブロック | 空行分割（言語に依存しない）；ストップワード除去や形態素解析の対象外 |

- 日本語チャンク: `content` = 元のテキスト、`normalized_content` = Sudachiによる正規化形
- 英語/コードチャンク: `normalized_content = null`
- `chunk_type`: `"text"` または `"code"`
- `chunking_strategy`: `"text"` または `"heading"`

> 根拠: Explicit in code — 見出しチャンク化（`chunking_strategy="heading"`）は `lang` に関わらず `normalized_content` を常に `null` にする。すなわち日本語のMarkdownソースは見出しチャンク化が優先され、Sudachi正規化はスキップされる。FTS5は `COALESCE(normalized_content, content)` により元テキスト（`content`）をそのままインデックス化する。

### 3.3 CLI引数

| 引数 | 説明 | デフォルト |
|---|---|---|
| `--file PATH` | 単一ファイルのみ処理する（パスはrag_src_dirからの相対パス） | rag-src/内の未処理の `.json` すべて |
| `--force` | センチネルチェックを無視してチャンクを再生成する | false |

### 3.4 出力JSON形式

```json
{
  "schema_version": "1",
  "artifact_type": "chunk",
  "created_by": "chunk_splitter",
  "url": "https://example.com/page",
  "title": "Page title",
  "lang": "ja",
  "source_file": "20240101120000-example.json",
  "chunk_index": 0,
  "chunk_type": "text",
  "chunking_strategy": "text",
  "content": "original chunk text",
  "normalized_content": "normalized form (JA only; null for EN/code)",
  "etag": "optional-etag",
  "last_modified": "optional-http-date"
}
```

- `chunk_type`: `text` / `code`
- `chunking_strategy`: `text` / `heading`
- `normalized_content`: 日本語のみ（Sudachi正規化）、英語・コードはnull
- `source_file`: クローラ出力ファイル名から`.json`拡張子を除いたもの

### 3.5 エラーハンドリング

| ケース | 対応 |
|---|---|
| Sudachiのトークナイズエラー | `_normalize_ja_sentence()` が `TokenizationError`（`RagLayerError`/`RuntimeError`のサブクラス）を送出する。個別チャンク単位のtry/exceptは存在せず、`process_all()` のファイル単位ループの `except (OSError, RuntimeError, ValueError)` まで伝播する。結果として当該チャンクのみでなく **ファイル全体** の処理が失敗扱いになる |
| ファイル単位の失敗 | `ERROR` ログ（トレースバック付き、`logger.exception`）；次のファイルへ継続 |
| 既存チャンク（`{stem}-0000.json`） | `--force` がない限りスキップ |

### 3.6 ロギング

- **ファイル:** `/opt/llm/logs/chunk.log` + stderr
- **フォーマット:** `%(asctime)s %(levelname)s [%(funcName)s] %(message)s`

| レベル | タイミング |
|---|---|
| `INFO` | 処理済みファイル、生成されたチャンク、スキップされたファイル（URL付き） |
| `WARNING` | Sudachiエラー |
| `ERROR` | ファイル読み込みエラー、ファイル単位の失敗（トレースバック付き） |

### 3.7 設定

[03_rag_05_1-configuration-reference.md §1.1](03_rag_05_1-configuration-reference.md) を参照。

---

## Related Documents

- `03_rag_00_document-guide.md`
- `03_rag_01_system_overview.md`
- `03_rag_02_01_ingestion_pipeline-overview.md`
- `03_rag_02_02_ingestion_pipeline-crawler.md`
- `03_rag_02_04_ingestion_pipeline-ingester.md`
- `03_rag_02_07_ingestion_pipeline-utils.md`
- `03_rag_05_1-configuration-reference.md`
- `03_rag_02_03_ingestion_pipeline-chunksplitter.md`

## Keywords

chunk-splitter
chunking-strategies
sudachi
markdown-heading
crawler
rag

