# Implementation Procedure: scripts/eventbus/config.py + app.py + tests/test_eventbus_offsets.py

## Goal

subscribe ループ内でN件ごとに `write_offset()` を呼び出してオフセット耐障害性を向上させる。

## Scope

**In:**
- `scripts/eventbus/config.py` — `offset_checkpoint_interval: int = 10` を追加
- `scripts/eventbus/app.py` — subscribe ループ内にカウンタ追加; N件ごとに `write_offset()` 呼び出し
- `tests/test_eventbus_offsets.py` — 新規/追記; N件配信後のオフセット書き込みテスト

**Out:** ファイルベースオフセットの置き換え

## Assumptions

1. `write_offset()` は `app.py:173-176` 付近でインポート済み
2. per-event チェックポイントは高コスト; デフォルト10件が妥当

## Implementation

### config.py

```python
offset_checkpoint_interval: int = 10  # checkpoint write_offset() every N delivered events
```

### app.py — subscribe loop

```python
events_since_checkpoint = 0

# ... per-event delivery loop ...
yield_event(event)
events_since_checkpoint += 1
if events_since_checkpoint >= _cfg.offset_checkpoint_interval:
    write_offset(consumer_id, event.seq)
    events_since_checkpoint = 0
```

### tests/test_eventbus_offsets.py

```python
async def test_offset_written_after_n_events(client: AsyncClient) -> None:
    """N件配信後、disconnect前にオフセットが書き込まれる。"""
    N = 3  # use small N for test
    # Publish N events
    for i in range(N):
        await client.post("/publish", json={"type": "test", "payload": {"i": i}})
    # Subscribe and consume N events
    # Verify offset file / DB contains seq >= N-1
    offset_resp = await client.get("/offsets/test-consumer")
    assert offset_resp.status_code == 200
    assert offset_resp.json()["seq"] >= N - 1
```

## Validation plan

| Check | Command | Expected |
|---|---|---|
| Lint | `uv run ruff check scripts/eventbus/config.py scripts/eventbus/app.py` | 0 errors |
| Offset tests | `uv run pytest tests/test_eventbus_offsets.py -v` | pass |
