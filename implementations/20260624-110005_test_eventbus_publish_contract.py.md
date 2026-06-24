# Implementation Procedure: scripts/eventbus/app.py + tests/test_eventbus_publish_contract.py

## Goal

JSONL 追記失敗時も SQLite コミット済みなら `/publish` は成功 (201) を返すことを保証する。

## Scope

**In:**
- `scripts/eventbus/app.py` — JSONL 失敗を WARNING ログに変更 (publish エラーにしない)
- `tests/test_eventbus_publish_contract.py` — 新規; "JSONL append失敗 → 201" テスト

**Out:** JSONL サポートの削除、ストレージモデルの変更

## Assumptions

1. `/publish` は SQLite コミット後に JSONL 追記する
2. SQLite コミット成功 = publish 成功 (JSONL は補完的)

## Implementation

### app.py — JSONL failure handling

```python
# /publish handler 内: SQLite commit 後の JSONL 追記
try:
    _append_to_jsonl(event)
except OSError as exc:
    logger.warning("eventbus: JSONL append failed (event still committed): %s", exc)
    # Do NOT raise — SQLite is source of truth
```

### tests/test_eventbus_publish_contract.py

```python
"""tests/test_eventbus_publish_contract.py
Event Bus publish persistence contract tests.
"""
from __future__ import annotations
from unittest.mock import patch
import pytest
from httpx import AsyncClient


class TestPublishContract:
    async def test_publish_succeeds_if_jsonl_append_fails(
        self, client: AsyncClient
    ) -> None:
        """JSONL append 失敗後も SQLite commit 済みなら 201 を返す。"""
        with patch("eventbus.app._append_to_jsonl", side_effect=OSError("disk full")):
            resp = await client.post(
                "/publish",
                json={"type": "test.event", "payload": {"key": "value"}},
            )
        assert resp.status_code == 201
        # Event should be retrievable from SQLite
        replay_resp = await client.get("/replay", params={"seq_from": 0})
        assert replay_resp.status_code == 200
        events = replay_resp.json().get("events", [])
        assert len(events) >= 1
```

## Validation plan

| Check | Command | Expected |
|---|---|---|
| Lint | `uv run ruff check scripts/eventbus/app.py tests/test_eventbus_publish_contract.py` | 0 errors |
| New test | `uv run pytest tests/test_eventbus_publish_contract.py -v` | pass |
