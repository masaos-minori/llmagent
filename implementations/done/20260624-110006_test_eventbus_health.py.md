# Implementation Procedure: scripts/eventbus/app.py + tests/test_eventbus_health.py

## Goal

`/health` を DB 疎通確認・DLQ タスク死活確認付きに拡張する。

## Scope

**In:**
- `scripts/eventbus/app.py` — `health()` を拡張; DB SELECT 1 と `_dlq_task.done()` チェック
- `tests/test_eventbus_health.py` — 新規; healthy / degraded の両状態テスト

**Out:** 完全な監視統合、readiness/liveness 分割

## Assumptions

1. 軽量 DB チェック: `_db.execute("SELECT 1")` (非破壊)
2. DLQ タスクチェック: `_dlq_task is not None and not _dlq_task.done()`
3. レスポンス形式: `{"status": "ok"|"degraded", "db": "ok"|"unavailable", "dlq_task": "running"|"stopped"}`
4. 劣化状態でも HTTP 200 を返す (HTTP 503 は将来の検討事項)

## Implementation

### app.py — health() 拡張

```python
@app.get("/health")
async def health() -> dict[str, str]:
    db_status = "ok"
    try:
        _db.execute("SELECT 1")
    except Exception:
        db_status = "unavailable"

    dlq_task_status = "running" if (_dlq_task is not None and not _dlq_task.done()) else "stopped"
    overall = "ok" if (db_status == "ok" and dlq_task_status == "running") else "degraded"
    return {"status": overall, "db": db_status, "dlq_task": dlq_task_status}
```

### tests/test_eventbus_health.py

```python
"""tests/test_eventbus_health.py"""
from __future__ import annotations
from unittest.mock import AsyncMock, patch
import pytest
from httpx import AsyncClient


class TestHealth:
    async def test_health_ok(self, client: AsyncClient) -> None:
        resp = await client.get("/health")
        assert resp.status_code == 200
        body = resp.json()
        assert body["status"] == "ok"
        assert body["db"] == "ok"
        assert body["dlq_task"] == "running"

    async def test_health_degraded_when_db_unavailable(self, client: AsyncClient) -> None:
        with patch("eventbus.app._db") as mock_db:
            mock_db.execute.side_effect = Exception("DB gone")
            resp = await client.get("/health")
        assert resp.status_code == 200
        body = resp.json()
        assert body["status"] == "degraded"
        assert body["db"] == "unavailable"
```

## Validation plan

| Check | Command | Expected |
|---|---|---|
| Lint | `uv run ruff check scripts/eventbus/app.py` | 0 errors |
| Health tests | `uv run pytest tests/test_eventbus_health.py -v` | pass |
