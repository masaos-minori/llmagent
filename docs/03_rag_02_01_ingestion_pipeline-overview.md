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
curl -s http://127.0.0.1:8003/health   # embed-llmが稼働していることを確認
```

### ステップ1: クロール

```bash
# config/rag_pipeline.tomlのtarget_urlsすべてを対象
nohup uv run python scripts/rag/ingestion/crawler.py > logs/crawl.log 2>&1 &
tail -f logs/crawl.log

# 単一URL（ページごとの言語自動判定付き）
uv run python scripts/rag/ingestion/crawler.py --url "https://ziglang.org/documentation/master/" --lang en

# 複数URL（すべてに同じ--langを適用）
uv run python scripts/rag/ingestion/crawler.py \
    --url "https://ziglang.org/documentation/master/" \
          "https://zig.guide/" \
    --lang en

# ページごとのCJK比率による言語判定
uv run python scripts/rag/ingestion/crawler.py --url "https://example.com/page" --lang auto

# TOMLファイルから対象（http://とfile://）を読み込む
uv run python scripts/rag/ingestion/crawler.py --targets-file /path/to/targets.toml
```

対象を記述するTOMLファイルの形式:
```toml
target_urls = [
    ["https://ziglang.org/documentation/master/", "en"],
    ["file:///opt/llm/scripts/rag/ingestion/crawler.py", "en"],
]
```

**注記:** すべてのファイルパス（`rag_src_dir`）は `config/rag_pipeline.toml` から解決される。本番環境のデフォルトは `/opt/llm/rag-src/`。

### ステップ2: チャンク分割

```bash
# {rag_src_dir}/内の未処理.jsonファイルすべてを対象
uv run python scripts/rag/ingestion/chunk_splitter.py

# 単一ファイルのみ（パスはrag_src_dirからの相対パス）
uv run python scripts/rag/ingestion/chunk_splitter.py --file /opt/llm/rag-src/20240101120000-ziglang.json

# 既存のチャンクを再生成
uv run python scripts/rag/ingestion/chunk_splitter.py --force
```

### ステップ3: 埋め込みと格納

```bash
# embed-llmが稼働していることを確認
curl -s http://127.0.0.1:8003/health

uv run python scripts/rag/ingestion/ingester.py

# 既存URLを強制的に再登録
uv run python scripts/rag/ingestion/ingester.py --force
```

### ファイルのライフサイクル

| パス | 作成元 | 形式 |
|---|---|---|
| `{rag_src_dir}/yyyymmddhhmmss-{slug}.json` | `crawler.py` | JSON（url, title, lang, fetched_at, content, code_blocks, etag, last_modified, schema_version, artifact_type [ingestion-only], created_by） |
| `{rag_src_dir}/chunk/{stem}-{idx:04d}.json` | `chunk_splitter.py` | JSON（url, title, lang, source_file, chunk_index, chunk_type, content, normalized_content, etag, last_modified, schema_version, artifact_type [ingestion-only], created_by, chunking_strategy） |
| `{rag_src_dir}/registered/{stem}-{idx:04d}.json` | `ingester.py`（chunk/から移動） | chunkファイルと同一 |

> **アーティファクト形式についての注記:** 上記に列挙した `.json` ファイルはすべてJSONペイロードを含む。
> 常に `orjson.loads()` または `json.loads()` でパースすること。ファイルを確認するには以下を使う。
> ```
> python -c "import orjson; print(orjson.loads(open('FILE', 'rb').read()))"
> ```

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
- `03_rag_02_ingestion_pipeline-ft5.md`
- `03_rag_03_01_query_pipeline-overview.md`
- `03_rag_05_1-configuration-reference.md`

## Keywords

ingestion-pipeline
execution-guide
crawler
chunk-splitter
ingester
rag
