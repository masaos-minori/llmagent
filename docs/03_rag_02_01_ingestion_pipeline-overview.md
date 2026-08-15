---
title: "Ingestion Pipeline Overview and Execution"
category: rag
tags:
  - ingestion-pipeline
  - execution-guide
  - crawler
  - chunk-splitter
  - ingester
  - rag
related:
  - 03_rag_00_document-guide.md
  - 03_rag_01_system_overview.md
  - 03_rag_03_01_query_pipeline-overview.md
  - 03_rag_05_1-configuration-reference.md
source:
  - 03_rag_02_01_ingestion_pipeline-overview.md
---

# RAG インジェクションパイプライン

- システム概要 → [03_rag_01_system_overview.md](03_rag_01_system_overview.md)
- 設定 → [03_rag_05_1-configuration-reference.md](03_rag_05_1-configuration-reference.md)

---

## 1. 実行ガイド

### 前提条件

```bash
curl -s http://127.0.0.1:8081/health
```

### ステップ1: クロール

```bash
# crawler.tomlの全URLクロール
uv run python scripts/rag/ingestion/crawler.py

# 単一URLクロール
uv run python scripts/rag/ingestion/crawler.py --url "https://example.com/" --lang en
```

- `--lang`: `auto`で言語自動判定、`en`/`ja`で指定
- `--targets-file PATH`: TOMLファイルから対象URLを読み込み

### ステップ2: チャンク分割

```bash
# 未処理ファイル一括分割
uv run python scripts/rag/ingestion/chunk_splitter.py

# 既存チャンクの再生成
uv run python scripts/rag/ingestion/chunk_splitter.py --force
```

### ステップ3: 埋め込みと格納

```bash
# 埋め込みとDB保存
uv run python scripts/rag/ingestion/ingester.py

# 強制再登録
uv run python scripts/rag/ingestion/ingester.py --force
```

### ファイルのライフサイクル

| パス | 作成元 | 内容 |
|---|---|---|
| `{rag_src_dir}/{timestamp}-{slug}.json` | crawler.py | URL, タイトル, 言語, コンテンツ, コードブロック |
| `{rag_src_dir}/chunk/{stem}-{idx:04d}.json` | chunk_splitter.py | チャンク情報, ストラテジ |
| `{rag_src_dir}/registered/{stem}-{idx:04d}.json` | ingester.py | チャンク→登録済み |

> JSONファイルは `orjson.loads()` でパース。確認用: `python -c "import orjson; print(orjson.loads(open('FILE', 'rb').read()))"`

本番設定: `rag_src_dir = "/opt/llm/rag-src"`。デフォルト値 `rag-src` は設定が存在しない場合にのみ使用される。

---

## Related Documents

- `03_rag_00_document-guide.md`
- `03_rag_01_system_overview.md`
- `03_rag_02_02_ingestion_pipeline-crawler.md`
- `03_rag_02_03_ingestion_pipeline-chunksplitter.md`
- `03_rag_02_04_ingestion_pipeline-ingester.md`
- `03_rag_02_07_ingestion_pipeline-utils.md`
- `03_rag_02_08_ingestion_pipeline-shared.md`
- `03_rag_03_01_query_pipeline-overview.md`
- `03_rag_05_1-configuration-reference.md`

## Keywords

ingestion-pipeline
execution-guide
crawler
chunk-splitter
ingester
rag
