---
title: "ChunkSplitter Detail"
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
  - 03_rag_02_01_ingestion_pipeline-overview.md
---

# RAG インジェクションパイプライン

- システム概要 → [03_rag_01_system_overview.md](03_rag_01_system_overview.md)
- 設定 → [03_rag_05_1-configuration-reference.md](03_rag_05_1-configuration-reference.md)

---

## 3. ChunkSplitter (`scripts/rag/ingestion/chunk_splitter.py`)

### 3.1 クラス概要

`ChunkSplitter` — `rag-src/*.json` ファイルを言語とコンテンツタイプに応じてチャンクに分割し、
`rag-src/chunk/` に保存する。冪等性あり: `{stem}-0000.json` センチネルが存在する場合はスキップする（`--force` で上書き可能）。

**モジュールレベルの定数**

| 定数 | 値 | 説明 |
|---|---|---|
| `MIN_HEADING_LINES_FOR_MARKDOWN` | 2 | .md以外のファイルでヒューリスティックなMarkdown判定を発動させるための最小見出し行数 |
| `MARKDOWN_HEADING_RE` | `r"^#{1,6}"` | Markdown見出し（1〜6レベル）にマッチする正規表現パターン |

**Typed dict**

| TypedDict | 用途 |
|---|---|
| `CrawlFilePayload` | クロール出力JSONファイル用の型付きdict（url, title, lang, content, code_blocksは必須；etag, last_modifiedはNotRequiredで任意） |
| `ChunkOutputPayload` | チャンク出力JSONファイル用の型付きdict（schema_version, artifact_type, created_by, url, title, lang, source_file, chunk_index, chunk_type, contentは必須；normalized_contentはNotRequiredで任意） |
| `ChunkMetadata` | 出力ペイロードに ** で展開するための任意メタデータdict（total=False）。url、title、lang、etag、last_modified、source_file、chunking_strategyを含む全フィールドが任意 |

**継承**

`ChunkSplitter` は多重継承により `ChunkEnglishMixin` と `ChunkJapaneseMixin` の両方を継承する。
メソッド解決順序: `ChunkSplitter → ChunkEnglishMixin → ChunkJapaneseMixin → object`。

**公開メソッド**

| メソッド | シグネチャ | 説明 |
|---|---|---|
| `__init__` | `(config: dict \| None = None) -> None` | `chunk_splitter.toml` をロードし、Sudachiトークナイザ（SplitMode.C、`core` 辞書）を初期化する |
| `process_all` | `(target: Path \| None = None, force: bool = False) -> int` | rag-src/内の全 *.json ファイル（またはターゲット単体）を処理する。書き込んだチャンクの総数を返す |
| `process_file` | `(src_path: Path, force: bool = False) -> int` | クローラのJSONファイルを読み込みチャンクに分割してchunk_dirへ書き込む。チャンク数を返す。force=Falseの場合、既にチャンク済みのファイルはスキップする |

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
| `en_stopwords` | — | チャンク化から除外する英語のストップワード（config/rag_pipeline.tomlを参照） |
| `ja_stop_pos` | — | 日本語でストップワードとして扱うSudachiの品詞カテゴリ（config/rag_pipeline.tomlを参照） |

### 3.1.3 Markdownソース判定の挙動

`.md`、`.markdown`、`.mdx` で終わるURLは、`md_index_enable` に関わらず常に見出しチャンク化を使用する。
.md以外のファイルは、`md_index_enable=true` の場合のみヒューリスティック判定（内容に見出し行が2行以上）を使用する。

### 3.1.4 Markdown見出しチャンク化の挙動

Markdownの見出し（# から ######）でテキストを分割する。`md_snippet_max_chars` 文字を超えるセクションは、さらに文単位のチャンク化で分割される。

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

### 3.3 CLI引数

| 引数 | 説明 | デフォルト |
|---|---|---|
| `--file PATH` | 単一ファイルのみ処理する（パスはrag_src_dirからの相対パス） | rag-src/内の未処理の `.json` すべて |
| `--force` | 既存チャンクを再生成する（センチネルチェックを上書き） | false |

### 3.4 出力JSON形式（`rag-src/chunk/{stem}-{idx:04d}.json`）

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

`source_file` フィールドには、クローラの出力ファイル名の元の `.json` 拡張子がそのまま保持される。
`ChunkMetadata` TypedDict（total=False）のすべてのフィールドが `**metadata` の展開によって含まれる。

### 3.5 エラーハンドリング

| ケース | 対応 |
|---|---|
| Sudachiのトークナイズエラー | 捕捉し `""` を返す；そのチャンクをスキップ |
| ファイル単位の失敗 | `ERROR` ログ（トレースバック付き）；次のファイルへ継続 |
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

## Keywords

chunk-splitter
chunking-strategies
sudachi
markdown-heading
crawler
rag
