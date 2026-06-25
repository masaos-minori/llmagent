# Implementation: High-load integration tests for SSE continuity and publish latency

Source plan: `plans/20260625-135700_plan.md` (req #17)

## Goal

Create `tests/test_eventbus_load.py` with concurrent load tests that verify SSE delivery continuity, publish latency bounds, and DLQ loop non-interference under concurrent publisher/subscriber workloads.

## Scope

- New test file: `tests/test_eventbus_load.py`
- Four test scenarios: concurrent publish, SSE continuity, DLQ interference, latency regression
- May extend `tests/eventbus_helpers.py` with async/concurrent test utilities if they do not already exist
- Out of scope: changes to application code

## Assumptions

1. Tests use `httpx.AsyncClient` with `ASGITransport` for in-process ASGI app testing
2. `anyio` or `asyncio` backend is configured in `conftest.py`; use `@pytest.mark.anyio` or `pytest.mark.asyncio`
3. Each test uses a `tmp_path`-based SQLite DB to prevent state leakage
4. Latency thresholds: publish P99 < 200 ms, SSE first-event delivery < 500 ms
5. req #14-#16 are implemented before running load tests (offload must be in place)

## Implementation

### Target file

`tests/test_eventbus_load.py`

### Procedure

1. Create the file with `pytest` imports and an ASGI client fixture using `tmp_path`
2. Implement `test_concurrent_publish` — 10 concurrent publishes, assert all 200 and unique seqs
3. Implement `test_sse_continuity` — subscribe in background, publish 20 events, assert all received within timeout
4. Implement `test_dlq_loop_noninterference` — DLQ-eligible events present, measure publish latency during DLQ processing
5. Implement `test_publish_latency_regression` — publish 20 events sequentially, assert P99 < 200 ms

### Method

Use `asyncio.gather` for concurrent publish. Use `asyncio.wait_for` with a timeout for SSE stream consumption. Measure latency with `time.monotonic()` before/after each publish call.

### Details

```python
import asyncio
import time
import pytest
from httpx import AsyncClient, ASGITransport
from eventbus.app import app


def make_event(i: int) -> dict:
    return {
        "event_id": f"load-test-{i:04d}",
        "topic": "load.test",
        "payload": {"index": i},
        "producer": "test",
        "published_at": "2026-06-25T00:00:00Z",
    }


@pytest.fixture
async def client(tmp_path):
    # Override config to use tmp_path DB
    import os
    os.environ["EVENTBUS_CONFIG_PATH"] = str(tmp_path / "eventbus.toml")
    # Write minimal config TOML
    config_content = f"""
port = 8010
db_path = "{tmp_path}/events.db"
storage_dir = "{tmp_path}/storage"
offsets_dir = "{tmp_path}/offsets"
deadletter_dir = "{tmp_path}/dlq"
max_retry = 3
"""
    (tmp_path / "eventbus.toml").write_text(config_content)
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        yield c


@pytest.mark.anyio
async def test_concurrent_publish(client):
    tasks = [client.post("/publish", json=make_event(i)) for i in range(10)]
    results = await asyncio.gather(*tasks)
    assert all(r.status_code == 200 for r in results)
    seqs = [r.json()["seq"] for r in results]
    assert len(set(seqs)) == 10  # all unique


@pytest.mark.anyio
async def test_sse_continuity(client):
    received = []
    async def consume():
        async with client.stream("GET", "/subscribe?since_seq=0") as stream:
            async for line in stream.aiter_lines():
                if line.startswith("data: "):
                    received.append(line)
                if len(received) >= 20:
                    break

    consumer = asyncio.create_task(consume())
    await asyncio.sleep(0.1)
    for i in range(20):
        await client.post("/publish", json=make_event(100 + i))

    await asyncio.wait_for(consumer, timeout=10.0)
    assert len(received) >= 20


@pytest.mark.anyio
async def test_publish_latency_regression(client):
    latencies = []
    for i in range(20):
        t0 = time.monotonic()
        r = await client.post("/publish", json=make_event(200 + i))
        latencies.append((time.monotonic() - t0) * 1000)
        assert r.status_code == 200
    p99 = sorted(latencies)[int(len(latencies) * 0.99)]
    assert p99 < 200, f"publish P99 latency {p99:.1f}ms exceeds 200ms threshold"
```

## Validation plan

| Check | Command | Expected |
|---|---|---|
| Tests discovered | `uv run pytest tests/test_eventbus_load.py --collect-only` | 3-4 tests collected |
| Lint | `uv run ruff check tests/test_eventbus_load.py` | 0 errors |
| Type check | `uv run mypy tests/test_eventbus_load.py` | no errors |
| All load tests pass | `uv run pytest tests/test_eventbus_load.py -v --timeout=30` | all pass |
| No timeout | No test exceeds 30 s | pass |
