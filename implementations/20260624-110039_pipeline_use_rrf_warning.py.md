# Implementation Procedure: scripts/rag/pipeline.py

## Goal

`use_rrf=False` 検出時に WARNING ログを出力し、ドキュメントで診断専用モードと明記する。

## Scope

**In:**
- `scripts/rag/pipeline.py` — `__init__` で WARNING ログ追加
- docs 更新

**Out:** 設定削除、dedup-only 動作の変更

## Implementation

### pipeline.py — __init__ WARNING ログ

```python
# 既存 logger.info("RagPipeline init: use_rrf=%s ...") の直後:
if not self._cfg.use_rrf:
    logger.warning(
        "use_rrf=False: RRF fusion disabled — retrieval quality degraded; "
        "use only for diagnostics or single-query testing"
    )
```

## Validation plan

| Check | Command | Expected |
|---|---|---|
| WARNING 追加 | `grep -n "use_rrf=False.*warning\|WARNING.*use_rrf\|use_rrf.*degraded" scripts/rag/pipeline.py` | found |
| Tests | `uv run pytest tests/ -k "pipeline" -x -q` | all pass |
