# Implementation Procedure: scripts/rag/ingestion/{crawler,chunk_splitter,ingester}.py + pipeline.py

## Goal

RAG ライフサイクル全体で構造化ログフィールド (`url`, `doc_id`, `chunk_id`, `source_type`, `stage_name`) を統一する。

## Scope

**In:**
- `scripts/rag/ingestion/crawler.py` — `url=`, `source_type=` を extra に追加
- `scripts/rag/ingestion/chunk_splitter.py` — `url=`, `chunk_id=` を追加
- `scripts/rag/ingestion/ingester.py` — `doc_id=`, `chunk_id=`, `url=` を追加
- `scripts/rag/pipeline.py` — `stage_name=` を追加

**Out:** 完全な可観測性スタック統合

## Design

### 共通フィールド定数 (rag/ingestion/__init__.py または rag/utils.py に追加)

```python
LOG_KEY_URL = "url"
LOG_KEY_DOC_ID = "doc_id"
LOG_KEY_CHUNK_ID = "chunk_id"
LOG_KEY_SOURCE_TYPE = "source_type"
LOG_KEY_STAGE_NAME = "stage_name"
```

### crawler.py ログ更新例

```python
logger.info("crawl: saved result", extra={"url": url, "source_type": "http"})
logger.info("crawl: saved local file", extra={"url": url, "source_type": "file"})
```

### ingester.py ログ更新例

```python
logger.info("ingest: upserted document", extra={"url": url, "doc_id": doc_id})
logger.info("ingest: upserted chunk", extra={"doc_id": doc_id, "chunk_id": chunk_id, "url": url})
```

### pipeline.py ログ更新例

```python
logger.info("pipeline: stage complete", extra={"stage_name": stage.__class__.__name__})
```

## Validation plan

| Check | Command | Expected |
|---|---|---|
| キー一貫 | `grep -n '"url"\|"doc_id"\|"chunk_id"' scripts/rag/ingestion/ingester.py` | ログ文あり |
| 回帰なし | `uv run pytest tests/ -k "ingest or crawl or chunk" -x -q` | all pass |
