# Implementation Procedure: scripts/eventbus/app.py (polling interval observability)

## Goal

`poll_interval_ms` を起動時にログ出力し、subscribe ループ内にデバッグログを追加する。

## Scope

**In:**
- `scripts/eventbus/app.py` — lifespan に `poll_interval_ms` ログ追加; subscribe ループ内に DEBUG ログ追加

**Out:** ポーリングからプッシュへの置き換え

## Assumptions

1. `_cfg.poll_interval_ms` は `app.py:140` 付近でロード済み

## Implementation

### app.py — lifespan startup log

```python
logger.info("eventbus: subscribe polling interval: %dms", _cfg.poll_interval_ms)
```

### app.py — per-poll debug log (subscribe loop 内)

```python
logger.debug(
    "eventbus: subscribe poll: consumer=%s seq=%d",
    consumer_id,
    current_seq,
)
```

## Validation plan

| Check | Command | Expected |
|---|---|---|
| Lint | `uv run ruff check scripts/eventbus/app.py` | 0 errors |
| Regression | `uv run pytest tests/test_eventbus*.py -x -q` | all pass |
