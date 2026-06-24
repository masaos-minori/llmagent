# Implementation Procedure: scripts/rag/ingestion/{crawler,chunk_splitter,ingester}.py

## Goal

crawler と chunk_splitter が書き出す JSON ペイロードに `schema_version`, `artifact_type`, `created_by` を追加する。ingester の読み込みパスにバリデーションを追加する。

## Scope

**In:**
- `scripts/rag/ingestion/crawler.py` — crawl ペイロードにメタデータ追加
- `scripts/rag/ingestion/chunk_splitter.py` — chunk ペイロードにメタデータ追加
- `scripts/rag/ingestion/ingester.py` — `_validate_artifact()` 読み込み前バリデーション
- docs 更新

**Out:** `.txt` → `.json` 拡張子変更 (別 req 46)

## Implementation

### 共通定数

```python
# scripts/rag/ingestion/_constants.py (新規) or ファイル先頭
CRAWL_SCHEMA_VERSION = "1"
CHUNK_SCHEMA_VERSION = "1"
```

### crawler.py ペイロード追加

```python
payload: dict = {
    "schema_version": CRAWL_SCHEMA_VERSION,
    "artifact_type": "crawl",
    "created_by": "crawler",
    "url": url,
    # ... 既存フィールド
}
```

### chunk_splitter.py ペイロード追加

```python
chunk_payload = {
    "schema_version": CHUNK_SCHEMA_VERSION,
    "artifact_type": "chunk",
    "created_by": "chunk_splitter",
    # ... 既存フィールド
}
```

### ingester.py バリデーション

```python
def _validate_artifact(payload: dict, expected_type: str) -> None:
    actual = payload.get("artifact_type")
    if actual != expected_type:
        raise ValueError(
            f"Expected artifact_type={expected_type!r}, got {actual!r}"
        )

# 各ファイル読み込み後:
_validate_artifact(payload, "chunk")
```

## Validation plan

| Check | Command | Expected |
|---|---|---|
| フィールド存在 | `grep -n "schema_version\|artifact_type\|created_by" scripts/rag/ingestion/crawler.py` | found |
| Tests | `uv run pytest tests/ -k "crawler or chunk or ingest" -x -q` | all pass |
