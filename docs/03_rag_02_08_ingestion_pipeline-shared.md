---
title: "Chunk Japanese Mixin, Pipeline Utils, and FTS5 Notes"
category: rag
tags:
  - chunk-japanese
  - pipeline-utils
  - fts5
related:
  - 03_rag_00_document-guide.md
  - 03_rag_01_system_overview.md
  - 03_rag_02_01_ingestion_pipeline-overview.md
  - 03_rag_02_02_ingestion_pipeline-crawler.md
  - 03_rag_02_03_ingestion_pipeline-chunksplitter.md
  - 03_rag_02_04_ingestion_pipeline-ingester.md
  - 03_rag_02_07_ingestion_pipeline-utils.md
  - 03_rag_02_09_ingestion_pipeline-shared-utilities.md
  - 03_rag_05_1-configuration-reference.md
source:
  - 03_rag_02_01_ingestion_pipeline-overview.md
---

# RAG インジェクションパイプライン

- システム概要 → [03_rag_01_system_overview.md](03_rag_01_system_overview.md)
- 設定 → [03_rag_05_1-configuration-reference.md](03_rag_05_1-configuration-reference.md)

---

## 8. Chunk Japanese Mixin (`scripts/rag/ingestion/chunk_japanese.py`)

### 8.1 モジュール概要

`chunk_japanese.py` — `ChunkJapaneseMixin`: Sudachi SplitMode.Cを用いた、日本語テキストのための形態素解析ベースのチャンク化。NFKC正規化、句境界分割、重複を伴うバッファベースの蓄積を含む。多重継承により `ChunkSplitter` にミックスインされる。

**クラス: `ChunkJapaneseMixin`**

---

## 9. Pipeline Utils (`scripts/rag/ingestion/pipeline_utils.py`)

### 9.1 モジュール概要

`pipeline_utils.py` — RAGインジェクションパイプライン用の共有I/Oユーティリティ: 検証付きのチャンクJSON読み込み、ソースファイル収集、処理済みセンチネルのチェック。生のチャンク/クロールJSONペイロードフィールド用の `ChunkJsonRaw` dataclassを提供する。

**モジュールレベルの定数**

| 定数 | 値 | 説明 |
|---|---|---|
| `logger` | `Logger(__name__, "/opt/llm/logs/pipeline.log")` | パイプラインのロギングインスタンス |

**TypedDict**

| TypedDict | 用途 |
|---|---|
| `ChunkJsonRaw` | 生のチャンクJSONペイロードフィールド；必須: `url`、`content`；任意: `title`、`lang`、`code_blocks`、`etag`、`last_modified`、`fetched_at`、`chunking_strategy`、`normalized_content`、`chunk_index`、`source_file`、`chunk_type`、`artifact_type`、`schema_version`、`created_by` |

**公開関数**

| 関数 | シグネチャ | 説明 |
|---|---|---|
| `read_json_file` | `(path: Path) -> ChunkDocument` | JSONファイルを読み込んでパースし、ChunkDocumentに変換する；失敗時はChunkFormatErrorを発生させる |
| `collect_source_files` | `(rag_src_dir: Path, target: Path \| None = None) -> tuple[list[Path], list[SkipInfo]]` | (処理対象ファイル, スキップ情報) を返す；targetが指定され存在する場合は[target]を返す；targetが存在しない場合はSkipInfo付きの空リストを返す；それ以外の場合はrag_src_dirから*.jsonをglobする |
| `is_already_processed` | `(sentinel_path: Path, force: bool) -> bool` | センチネルファイルが存在しforce=Falseの場合にTrueを返す（chunk_splitterに対するスキップ信号） |

**read_json_fileのフィールド対応**

| JSONフィールド | ChunkDocumentフィールド | フォールバック |
|---|---|---|
| `url` | `url` | （必須、フォールバックなし） |
| `title` | `title` | `""` |
| `lang` | `lang` | `"en"` |
| `content` | `content` | （必須、フォールバックなし） |
| `code_blocks` | `code_blocks` | `[]` |
| `etag` | `etag` | `None` |
| `last_modified` | `last_modified` | `None` |
| `chunking_strategy` | `chunking_strategy` | `"text"` |
| `normalized_content` | `normalized_content` | `None` |
| `chunk_index` | `chunk_index` | `0` |
| `source_file` | `source_file` | `""` |
| `chunk_type` | `chunk_type` | `""` |

---

## 10. Shared Utilities (`scripts/rag/utils.py`)

詳細は → [03_rag_02_09_ingestion_pipeline-shared-utilities.md](03_rag_02_09_ingestion_pipeline-shared-utilities.md)

```python
from rag.utils import (
    cosine_sim,
    floats_to_blob,
    normalize_unicode,
    sanitize_document,
    sanitize_document_full,
    validate_url,
)
```

**利用元:**

| スクリプト | 使用される関数 |
|---|---|
| `scripts/rag/ingestion/chunk_splitter.py` | `normalize_unicode` |
| `scripts/rag/ingestion/chunk_japanese.py` | `normalize_unicode` |
| `scripts/rag/ingestion/ingester.py` | `floats_to_blob`, `validate_url` |
| `scripts/rag/ingestion/crawler.py` | `validate_url` |
| `scripts/rag/pipeline.py` | `sanitize_document`, `floats_to_blob` |
| `scripts/rag/cache.py` | `cosine_sim` |

---

## 11. FTS5実装に関する注記

### FTS5 / LLMコンテンツの分離

日本語チャンクは2つのバージョンを格納する。
- `chunks.content` — 元のテキスト（LLMへコンテキストとして渡される）
- `chunks.normalized_content` — Sudachiの `normalized_form()` をスペース結合したもの（FTS5インデックス用）

`chunks_ai` / `chunks_au` / `chunks_ad` トリガーは `COALESCE(normalized_content, content)` を
`chunks_fts` に書き込む。英語とコードのチャンクは `normalized_content = NULL` であるため、FTS5は `content` を直接使用する。

### FTS5クエリのトークン化

日本語クエリはSudachiトークナイザを使い、名詞・動詞・形容詞のみ（助詞・助動詞は除外）の `normalized_form()` を抽出する。
英語クエリは正規表現 `[a-zA-Z0-9]+` によるトークン化を使用する。Sudachiトークナイザは遅延初期化され、importの時点では副作用がない。

### FTS5クエリのトークン数上限

FTS5クエリ内のトークン数の上限: 20（`repository.py:29`）。
上限を超えるトークンはクエリの爆発を防ぐため黙って切り捨てられる。各トークンからは二重引用符（FTS5のメタ文字）
と空白が除去され、空になったトークンは破棄される。有効なトークンが1つも残らない場合は
`'""'`（空のFTS5クエリ）を返す。

---

## Related Documents

- `03_rag_00_document-guide.md`
- `03_rag_01_system_overview.md`
- `03_rag_02_01_ingestion_pipeline-overview.md`
- `03_rag_02_02_ingestion_pipeline-crawler.md`
- `03_rag_02_03_ingestion_pipeline-chunksplitter.md`
- `03_rag_02_04_ingestion_pipeline-ingester.md`
- `03_rag_02_07_ingestion_pipeline-utils.md`
- `03_rag_02_09_ingestion_pipeline-shared-utilities.md`
- `03_rag_05_1-configuration-reference.md`

## Keywords

chunk-japanese
pipeline-utils
fts5
rag
