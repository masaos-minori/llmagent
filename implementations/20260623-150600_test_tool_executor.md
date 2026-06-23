# Implementation: tests/test_tool_executor.py — MCP インフラ品質テスト

**Plan:** `plans/20260623-231000_plan.md` (Phase 9)
**Target:** `tests/test_tool_executor.py`

---

## 追加テストケース

### 1. `test_stop_no_zombie` — kill() 後に returncode が設定されること

```python
class TestStdioTransportStop:
    @pytest.mark.asyncio
    async def test_stop_no_zombie_after_kill(self, monkeypatch) -> None:
        """stop() must await wait() after kill() to prevent zombie processes."""
        from shared.tool_executor import StdioTransport
        transport = StdioTransport(cmd=["cat"], server_key="test")

        waited = []

        class _FakeProc:
            returncode = None
            stdin = None

            def kill(self):
                self.returncode = -9

            async def wait(self):
                waited.append(True)
                self.returncode = -9

            def is_alive(self):
                return self.returncode is None

        transport._proc = _FakeProc()
        # Simulate the path where stop() reaches kill() (graceful wait times out)
        # then waits again
        monkeypatch.setattr(
            "asyncio.wait_for",
            lambda coro, timeout: (
                coro if isinstance(coro, type(None)) else _raise_timeout(coro, timeout, waited)
            )
        )
        # Just verify that after kill() the wait is called
        # Actual zombie prevention is tested by ensuring returncode != None
```

**注意:** テストの mock パターンは既存の `test_tool_executor.py` のパターンに合わせる。ファイルの先頭 import と既存 fixture を確認してから実装する。

### 2. `test_stdio_response_id_mismatch` — ID 不一致で TransportError

```python
class TestStdioTransportResponseId:
    def test_response_id_mismatch_raises(self) -> None:
        from shared.tool_executor import StdioTransport
        import orjson, pytest
        from shared.tool_executor import TransportError

        resp_bytes = orjson.dumps({"id": 99, "result": "ok", "is_error": False})
        with pytest.raises(ValueError, match="Response ID mismatch"):
            StdioTransport._parse_stdio_response(resp_bytes, expected_id=1)

    def test_response_id_match_succeeds(self) -> None:
        from shared.tool_executor import StdioTransport
        import orjson

        resp_bytes = orjson.dumps({"id": 1, "result": "ok", "is_error": False})
        result = StdioTransport._parse_stdio_response(resp_bytes, expected_id=1)
        assert result.output == "ok"
        assert not result.is_error
```

### 3. `test_cache_stampede` — 並行呼び出しで `_raw_execute` が 1 回のみ

```python
class TestCacheStampede:
    @pytest.mark.asyncio
    async def test_concurrent_calls_share_inflight_future(self) -> None:
        """Three concurrent calls to _execute_with_cache use one _raw_execute."""
        from shared.tool_executor import ToolExecutor
        import asyncio

        call_count = 0

        async def _fake_raw_execute(tool_name, args):
            nonlocal call_count
            call_count += 1
            await asyncio.sleep(0.01)
            from shared.tool_executor import ToolCallResult
            return ToolCallResult(output="ok", is_error=False, request_id="", server_key="")

        executor = ToolExecutor.__new__(ToolExecutor)
        executor._cache = {}
        executor._cache_ttl = 60.0
        executor._cache_max_size = 100
        executor._inflight = {}
        executor.stat_cache_hits = 0
        executor._raw_execute = _fake_raw_execute

        results = await asyncio.gather(
            executor._execute_with_cache("write_file", {"path": "a"}),
            executor._execute_with_cache("write_file", {"path": "a"}),
            executor._execute_with_cache("write_file", {"path": "a"}),
        )
        assert call_count == 1  # only one actual execution
        assert all(r.output == "ok" for r in results)
```

### 4. `test_http_retry_on_429` — 429 で 2 回失敗後に 200 成功

```python
class TestHttpTransportRetry:
    @pytest.mark.asyncio
    async def test_retries_on_429_and_succeeds(self) -> None:
        import httpx
        from shared.tool_executor import HttpTransport

        call_count = 0

        class _FakeClient:
            async def post(self, url, **kw):
                nonlocal call_count
                call_count += 1
                if call_count < 3:
                    return httpx.Response(429, json={"result": "", "is_error": False})
                return httpx.Response(200, json={"result": "ok", "is_error": False})

        transport = HttpTransport(
            http=_FakeClient(),  # type: ignore
            base_url="http://localhost:8001",
            server_key="test",
        )
        # Patch sleep to avoid actual delay
        import unittest.mock
        with unittest.mock.patch("asyncio.sleep", return_value=None):
            result = await transport.call("write_file", {"path": "a"})
        assert result.output == "ok"
        assert call_count == 3
```

---

## 完了条件

```bash
uv run pytest tests/test_tool_executor.py::TestStdioTransportResponseId -v
# → 2件 PASSED

uv run pytest tests/test_tool_executor.py::TestCacheStampede -v
# → 1件 PASSED

uv run pytest tests/test_tool_executor.py::TestHttpTransportRetry -v
# → 1件 PASSED

uv run pytest tests/test_tool_executor.py -v
# → 全件通過 (既存テスト含む)
```
