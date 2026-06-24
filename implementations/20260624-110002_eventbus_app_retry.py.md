# Implementation Procedure: scripts/eventbus/app.py + tests/test_eventbus_phase3.py

## Goal

`/dlq/{event_id}/requeue` の requeue 時に `retry_count` を加算して DLQ 昇格をリーチャブルにする。

## Scope

**In:**
- `scripts/eventbus/app.py` — requeue SQL を `retry_count = retry_count + 1, dlq_at = NULL` に変更
- `tests/test_eventbus_phase3.py` (または `tests/test_eventbus_dlq.py`) — retry exhaustion → DLQ テスト追加

**Out:** DLQ ストレージ形式の変更、SQLite の置き換え

## Assumptions

1. 現状 requeue SQL: `UPDATE events SET retry_count = 0, dlq_at = NULL WHERE event_id = ?`
2. `max_retry` は `EventBusConfig` で設定される整数

## Implementation

### app.py — requeue SQL 変更

```python
# /dlq/{event_id}/requeue ハンドラ内
# Before:
# db.execute("UPDATE events SET retry_count = 0, dlq_at = NULL WHERE event_id = ?", (event_id,))
# After:
db.execute(
    "UPDATE events SET retry_count = retry_count + 1, dlq_at = NULL WHERE event_id = ?",
    (event_id,),
)
```

### tests — retry exhaustion → DLQ test

```python
async def test_retry_exhausted_leads_to_dlq(client: AsyncClient) -> None:
    """N回requeueするとmax_retryに達してDLQ昇格する。"""
    # Publish and exhaust retries
    await client.post("/publish", json={"type": "test", "payload": {}})
    event_id = ...  # get from publish response
    max_retry = 3  # EventBusConfig default

    # Promote to DLQ first time
    await _run_dlq_loop(client)
    # Requeue max_retry times to increment retry_count
    for _ in range(max_retry):
        await client.post(f"/dlq/{event_id}/requeue")
    # DLQ loop should re-promote
    await _run_dlq_loop(client)
    resp = await client.get("/dlq")
    assert any(e["event_id"] == event_id for e in resp.json()["events"])
```

## Validation plan

| Check | Command | Expected |
|---|---|---|
| Lint | `uv run ruff check scripts/eventbus/app.py` | 0 errors |
| Tests | `uv run pytest tests/test_eventbus_phase3.py -x -q` | all pass |
