# tests/integration/test_robustness_chaos.py — Chaos injection tests

**Plan:** `plans/20260625-095157_plan.md` (req #71)
**Target:** `tests/integration/test_robustness_chaos.py` (new file)

## Priority: P2 (High)

## Scenarios to implement

### 3A. ToolLoopGuard Chaos

1. **Exact duplicate tool call** — same tool name + same args in consecutive rounds → guard detects and stops
2. **Near-duplicate with different args** — guard does NOT fire
3. **Cycle detection** — A → B → A → B → ... → guard fires on cycle
4. **Error escalation** — N consecutive tool errors → guard fires with `"repeated_errors"` reason
5. **Reset between turns** — guard state clears at turn start; no cross-turn state leakage

Injection method: mock LLM that returns repeated tool calls:
```python
def _make_repeated_tool_response(tool_name, args, count=10):
    """Return a mock LLM stream that calls the same tool N times."""
    ...
```

### 3B. ErrorInjectionService Chaos

1. **Inject transport error at specific round** — error propagates to `stat_transport_errors`
2. **Inject multiple error types in same turn** — correct error type per tool recorded
3. **Inject error during multi-tool batch** — one tool fails, others succeed; partial result handling

### 3C. SQLite Chaos

1. **Busy lock injection** — hold external EXCLUSIVE lock for 1s; verify agent waits up to `busy_timeout`
2. **Disk full simulation** — `patch("sqlite3.connect", side_effect=sqlite3.OperationalError("disk I/O error"))`
3. **WAL checkpoint failure** — simulate WAL file read-only; graceful degradation

### 3D. Network Chaos

1. **Intermittent 502s** — server alternates 502 / 200 → retry handles correctly
2. **Connection reset** — `httpx.RemoteProtocolError` → treated as transport error
3. **Partial response body** — HTTP 200 with truncated JSON → `ValueError` in `_parse_http_response` → `TransportError`

## Run 5× for flakiness check

```
for i in {1..5}; do uv run pytest tests/integration/test_robustness_chaos.py -v --timeout=30; done
```

## Validation

```
uv run pytest tests/integration/test_robustness_chaos.py -v --timeout=30
```
