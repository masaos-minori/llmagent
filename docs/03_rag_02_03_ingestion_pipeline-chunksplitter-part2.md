---
title: "ChunkSplitter Detail (Part 2)"
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

### 3.1.3 Markdownソース判定の挙動

`.md`、`.markdown`、`.mdx` で終わるURLは、`md_index_enable` に関わらず常に見出しチャンク化を使用する。
.md以外のファイルは、`md_index_enable=true` の場合のみヒューリスティック判定（内容に見出し行が2行以上）を使用する。

### 3.1.4 Markdown見出しチャンク化の挙動

Markdownの見出し（# から ######）でテキストを分割する。`md_snippet_max_chars` 文字を超えるセクションは、さらに文単位のチャンク化で分割される。

> 根拠: Explicit in code — `_chunk_markdown_by_heading()`（`chunk_splitter.py`）は超過セクションを常に `_chunk_english()`（英語の文境界分割）にフォールバックする。`lang` が `"ja"` であっても日本語形態素解析（Sudachi）は適用されず、`normalized_content` は生成されない（見出しチャンク全体で `normalized_content` は常に空扱い、後述の通り）。

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

> 根拠: Explicit in code — 見出しチャンク化（`chunking_strategy="heading"`）は `lang` に関わらず `normalized_content` を常に `null` にする（`_build_text_triples()` が見出し分岐で正規化形を生成しない）。すなわち日本語のMarkdownソースは見出しチャンク化が優先され、Sudachi正規化はスキップされる。FTS5は `COALESCE(normalized_content, content)` により元テキスト（`content`）をそのままインデックス化する。

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
| Sudachiのトークナイズエラー | `_normalize_ja_sentence()` が `TokenizationError`（`RagLayerError`/`RuntimeError`のサブクラス）を送出する。個別チャンク単位のtry/exceptは存在せず、`process_all()` のファイル単位ループの `except (OSError, RuntimeError, ValueError)` まで伝播する。結果として当該チャンクのみでなく **ファイル全体** の処理が失敗扱いになる |
| ファイル単位の失敗 | `ERROR` ログ（トレースバック付き、`logger.exception`）；次のファイルへ継続 |
| 既存チャンク（`{stem}-0000.json`） | `--force` がない限りスキップ |

> 根拠: Explicit in code — `scripts/rag/ingestion/chunk_japanese.py::_normalize_ja_sentence()` は Sudachi の `RuntimeError` を捕捉して `TokenizationError` に変換し再送出する（`""` を返す実装にはなっていない）。`scripts/rag/ingestion/chunk_splitter.py::process_all()` は `except (OSError, RuntimeError, ValueError)` でこれを受け止め、`process_file failed: %s: %s` としてログ後、次のファイルへ進む。旧記載「そのチャンクをスキップ」は実装と矛盾するため訂正した。

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
- `03_rag_01_system_overview-part1.md`
- `03_rag_02_01_ingestion_pipeline-overview.md`
- `03_rag_02_02_ingestion_pipeline-crawler-part1.md`
- `03_rag_02_04_ingestion_pipeline-ingester-part1.md`
- `03_rag_02_07_ingestion_pipeline-utils.md`
- `03_rag_05_1-configuration-reference.md`
- `03_rag_02_03_ingestion_pipeline-chunksplitter-part1.md`

## Keywords

chunk-splitter
chunking-strategies
sudachi
markdown-heading
crawler
rag
