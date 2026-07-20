---
title: "RagIngester Detail (Part 2)"
category: rag
tags:
  - ingester
  - embedding
  - sqlite
  - etag-manager
  - rag
related:
  - 03_rag_00_document-guide.md
  - 03_rag_01_system_overview-part1.md
  - 03_rag_02_01_ingestion_pipeline-overview.md
  - 03_rag_02_02_ingestion_pipeline-crawler-part1.md
  - 03_rag_02_03_ingestion_pipeline-chunksplitter-part1.md
  - 03_rag_02_07_ingestion_pipeline-utils.md
  - 03_rag_02_05_ingestion_pipeline-document-manager.md
  - 03_rag_02_06_ingestion_pipeline-supporting-components.md
  - 03_rag_05_1-configuration-reference.md
source:
  - 03_rag_02_04_ingestion_pipeline-ingester-part1.md
---

# RAG インジェクションパイプライン

- システム概要 → [03_rag_01_system_overview-part1.md](03_rag_01_system_overview-part1.md)
- 設定 → [03_rag_05_1-configuration-reference.md](03_rag_05_1-configuration-reference.md)

---

## 4. RagIngester (`scripts/rag/ingestion/ingester.py`)

### 4.3 CLI引数

| 引数 | 説明 | デフォルト |
|---|---|---|
| `--force` | 既存のdocument/chunks/chunks_vecレコードを削除し再埋め込みする。（`file://` URLの場合）etagに関わらず常に再インジェクションする | false |

### 4.4 埋め込みAPI

``` http
POST http://127.0.0.1:8081/embedding
Request:  {"content": "passage: {text}"}
Response: {"embedding": [float, ...]}   # 384次元（multilingual-E5-small；config/ingester.toml::embedding_dims）
```

### 実装上の補足(embedding_dimsの参照元)

`ingester.py` 内のコード上のdocstringは `common.toml::embedding_dims` と記載しているが、`common.toml` という設定ファイルはリポジトリ内に存在しない。実際には `RagIngester.__init__` に渡される設定辞書(`ingester.toml` をロードしたもの)の `embedding_dims` キー(デフォルト384)を使用する。docstringはプロセス分離方針導入前の記述が残ったものと考えられる(Explicit in code / Needs confirmation — docstringの記述意図そのものは未確認)。

### 4.5 更新されるDBテーブル

| テーブル | 操作 |
|---|---|
| `documents` | 存在確認のためSELECT；DELETE+INSERT（`force=True`）またはスキップ+UPDATE etag（`force=False`）；`url`、`title`、`lang`、`etag`、`last_modified`、`chunking_strategy`、`fetched_at` を格納 |
| `chunks` | INSERT（FK → documents；ON DELETE CASCADE） |
| `chunks_vec` | ベクトルのBLOBをINSERT |
| `chunks_fts` | `chunks_ai` トリガーにより自動同期される（`COALESCE(normalized_content, content)`） |

### 4.6 エラーハンドリング

| ケース | 対応 |
|---|---|
| 埋め込みAPI失敗 | `embed_retry` 回まで指数バックオフでリトライ（上限10秒） |
| リトライ上限到達（単一チャンク） | `WARNING` ログ；そのチャンクをスキップし継続 |
| `lang` 値が不正 | `ValueError`；そのURLグループをスキップ；トレースバック付き `ERROR` ログ |
| `chunks_vec` の削除順序 | `chunks_vec` を最初に削除しなければならない（sqlite-vec仮想テーブルにはFK制約がないため） |
| 埋め込み次元の不一致 | `ValueError`；そのチャンクをスキップ；`WARNING` ログ |
| アーティファクト検証失敗 | `WARNING` ログ；そのチャンクを埋め込み失敗としてスキップ |
| ファイル移動失敗 | url、source_type、stage_nameの構造化フィールドを含む `ERROR` ログ |

### 4.7 ロギング

- **ファイル:** `/opt/llm/logs/ingest.log` + stderr
- **フォーマット:** `%(asctime)s %(levelname)s [%(funcName)s] %(message)s`

| レベル | タイミング | 構造化フィールド |
|---|---|---|
| `INFO` | 処理済みチャンク、DB挿入、ファイル移動、スキップされたURL | `doc_id`、`source_type`、`stage_name`（挿入時）；`url`（スキップ時） |
| `WARNING` | 埋め込みAPIエラー、リトライ、埋め込みスキップ | `source_type`、`stage_name` |
| `ERROR` | チャンクファイル読み込みエラー、ファイル移動エラー、URLグループの失敗（トレースバック付き） | — |

ETagManagerの詳細 → [03_rag_02_06_ingestion_pipeline-supporting-components.md §4.8](03_rag_02_06_ingestion_pipeline-supporting-components.md)
設定の詳細 → [03_rag_02_06_ingestion_pipeline-supporting-components.md §4.9](03_rag_02_06_ingestion_pipeline-supporting-components.md)

---

## Related Documents

- `03_rag_00_document-guide.md`
- `03_rag_01_system_overview-part1.md`
- `03_rag_02_01_ingestion_pipeline-overview.md`
- `03_rag_02_02_ingestion_pipeline-crawler-part1.md`
- `03_rag_02_03_ingestion_pipeline-chunksplitter-part1.md`
- `03_rag_02_07_ingestion_pipeline-utils.md`
- `03_rag_02_05_ingestion_pipeline-document-manager.md`
- `03_rag_02_06_ingestion_pipeline-supporting-components.md`
- `03_rag_05_1-configuration-reference.md`
- `03_rag_02_04_ingestion_pipeline-ingester-part1.md`

## Keywords

ingester
embedding
sqlite
rag
