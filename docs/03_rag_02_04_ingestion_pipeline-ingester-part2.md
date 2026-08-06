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
Content-Type: application/json

{"content": "passage: {text}"}
```

応答: `{"embedding": [float, ...]}` — 384次元（multilingual-E5-small）

- `embedding_dims`: `config/ingester.toml` で指定（デフォルト384）
- docstringの `common.toml::embedding_dims` は古い記述（`common.toml` は存在しない）

### 4.5 データベース更新

現在のDBスキーマ定義 → [RAG schema reference document](03_rag_02_06_ingestion_pipeline-supporting-components.md)

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
- 詳細なログメッセージ形式 → `scripts/rag/ingestion/ingester.py`

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
