---
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
  - 03_rag_01_system_overview-part1.md
  - 03_rag_02_01_ingestion_pipeline-overview.md
  - 03_rag_02_02_ingestion_pipeline-crawler-part1.md
  - 03_rag_02_04_ingestion_pipeline-ingester-part1.md
  - 03_rag_02_07_ingestion_pipeline-utils.md
  - 03_rag_05_1-configuration-reference.md
source:
  - 03_rag_02_03_ingestion_pipeline-chunksplitter-part1.md
---

# RAG インジェクションパイプライン

- システム概要 → [03_rag_01_system_overview-part1.md](03_rag_01_system_overview-part1.md)
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

> 根拠: Explicit in code — `CrawlFilePayload` と `ChunkOutputPayload` は `chunk_splitter.py` 内で型として宣言されているが、同ファイル内の実処理では型注釈として参照されていない（実際の入出力は `ChunkJsonRaw`（`pipeline_utils.py`）や `dict[str, object]` 経由で扱われる）。ドキュメント目的の宣言と考えられる。

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
| `en_stopwords` | — | チャンク化から除外する英語のストップワード（`config/chunk_splitter.toml`で定義。旧docs記載の`rag_pipeline.toml`は存在しないため訂正） |
| `ja_stop_pos` | — | 日本語でストップワードとして扱うSudachiの品詞カテゴリ。デフォルト値: `["助詞", "助動詞", "補助記号", "空白", "感動詞", "接続詞"]`（`config/chunk_splitter.toml`で定義） |

> 根拠: Explicit in code — `scripts/rag/ingestion/chunk_splitter.py::__init__` は `ConfigLoader().load("chunk_splitter.toml")` を使用し、`config/chunk_splitter.toml` に `en_stopwords`/`ja_stop_pos` が定義されている。`config/rag_pipeline.toml` というファイルは本リポジトリに存在しない。

## Related Documents

- `03_rag_00_document-guide.md`
- `03_rag_01_system_overview-part1.md`
- `03_rag_02_01_ingestion_pipeline-overview.md`
- `03_rag_02_02_ingestion_pipeline-crawler-part1.md`
- `03_rag_02_04_ingestion_pipeline-ingester-part1.md`
- `03_rag_02_07_ingestion_pipeline-utils.md`
- `03_rag_05_1-configuration-reference.md`
- `03_rag_02_03_ingestion_pipeline-chunksplitter-part2.md`

## Keywords

chunk-splitter
chunking-strategies
sudachi
markdown-heading
crawler
rag
