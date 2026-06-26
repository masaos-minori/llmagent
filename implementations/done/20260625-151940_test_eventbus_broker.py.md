# Implementation: tests/test_eventbus_broker.py — EventBroker unit tests (req #38)

## Goal

Unit-test the `EventBroker` class in isolation: fan-out, topic filtering, unsubscribe, queue full drop, and shutdown sentinel.

## Scope

- New file `tests/test_eventbus_broker.py`
- Uses `pytest` with `anyio` for async tests
- No FastAPI TestClient — tests broker in isolation
- 6 test cases

## Assumptions

- req #35 broker.py is implemented
- `pytest-anyio` or `anyio` is available in the project (check `pyproject.toml` if needed; add if missing)
- Tests run with `uv run pytest tests/test_eventbus_broker.py`

## Implementation

### Target file

`tests/test_eventbus_broker.py` (new)

### Procedure

1. Create file with imports and 6 test functions

### Method

New file.

### Details

```python
from __future__ import annotations

import asyncio

import pytest

from eventbus.broker import EventBroker


@pytest.mark.anyio
async def test_fan_out_all_subscribers():
    broker = EventBroker()
    sub1 = broker.subscribe([])
    sub2 = broker.subscribe([])
    broker.publish({"seq": 1, "topic": "t", "event_id": "a"})
    assert sub1.queue.qsize() == 1
    assert sub2.queue.qsize() == 1


@pytest.mark.anyio
async def test_topic_filter_excludes_non_matching():
    broker = EventBroker()
    sub_t = broker.subscribe(["target"])
    sub_all = broker.subscribe([])
    broker.publish({"seq": 1, "topic": "other", "event_id": "a"})
    assert sub_t.queue.empty()      # filtered out
    assert sub_all.queue.qsize() == 1  # all-topics subscriber receives it


@pytest.mark.anyio
async def test_topic_filter_delivers_matching():
    broker = EventBroker()
    sub = broker.subscribe(["target"])
    broker.publish({"seq": 1, "topic": "target", "event_id": "a"})
    assert sub.queue.qsize() == 1


@pytest.mark.anyio
async def test_unsubscribe_stops_delivery():
    broker = EventBroker()
    sub = broker.subscribe([])
    broker.unsubscribe(sub)
    broker.publish({"seq": 1, "topic": "t", "event_id": "a"})
    assert sub.queue.empty()


@pytest.mark.anyio
async def test_unsubscribe_idempotent():
    broker = EventBroker()
    sub = broker.subscribe([])
    broker.unsubscribe(sub)
    broker.unsubscribe(sub)  # should not raise


@pytest.mark.anyio
async def test_shutdown_sends_sentinel():
    broker = EventBroker()
    sub = broker.subscribe([])
    broker.shutdown()
    sentinel = await asyncio.wait_for(sub.queue.get(), timeout=1.0)
    assert sentinel is None
```

Note on `anyio` setup: if not yet in `pyproject.toml`, add `anyio[trio]` to dev deps and `pytest.ini_options` with `anyio_mode = "asyncio"`. Check existing async test patterns in the project first.

## Validation plan

| Check | Command | Target |
|---|---|---|
| Test collection | `uv run pytest tests/test_eventbus_broker.py --collect-only` | 6 tests |
| All pass | `uv run pytest tests/test_eventbus_broker.py -v` | all pass |
| Lint | `ruff check tests/test_eventbus_broker.py` | 0 errors |
| Type check | `mypy tests/test_eventbus_broker.py` | no errors |
