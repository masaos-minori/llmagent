# Implementation: Phase 2 — Test-mocking in tests/test_lifecycle.py

## Goal

Eliminate real subprocess spawning and signal delivery in `TestHttpLifecycleStderrLog` (3 tests) by mocking `subprocess.Popen`, `os.killpg`/`os.getpgid`, and `httpx.AsyncClient`. Provide synthetic stderr content to preserve assertion validity.

## Scope

- `tests/test_lifecycle.py` only.
- Three tests in `TestHttpLifecycleStderrLog` (L476-553).
- Helper `_patch_open_to_tmp` is already used; no change needed.

## Assumptions

1. The `_make_mock_proc(exit_code=...)` helper at L36-41 is sufficient for creating mock process objects.
2. Pre-writing synthetic stderr to the temp file before `mgr.start()` correctly simulates a real subprocess's stderr output, because `_read_stderr_tail` reads from the same file path stored in `self._stderr_log_paths`.

## Implementation

### Target file

`tests/test_lifecycle.py`

### Procedure

1. Modify `test_start_large_stderr_does_not_block` — mock Popen + AsyncClient, pre-populate stderr.
2. Modify `test_start_early_exit_stderr_from_log` — same pattern.
3. Modify `test_start_timeout_stderr_from_log` — mock Popen + AsyncClient + os.killpg/os.getpgid, pre-populate stderr.

### Method

Use `patch` context managers for `subprocess.Popen` and `httpx.AsyncClient`. Use `monkeypatch.setattr` for `os.killpg`/`os.getpgid` (imported via `from agent import http_lifecycle as mod`). Pre-populate stderr log file right after `_patch_open_to_tmp`.

### Details

#### Test 1: `test_start_large_stderr_does_not_block` (L479-494)

Add mocking:

```python
    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_start_large_stderr_does_not_block(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        _patch_open_to_tmp(monkeypatch, tmp_path)
        # Pre-populate stderr log with 200K chars
        stderr_path = tmp_path / "test_server.stderr.log"
        stderr_path.write_text("x" * 200_000)
        mgr = HttpServerLifecycleManager()
        cfg = _make_test_cfg(
            cmd=[sys.executable, "-c", "import sys; sys.stderr.write('x' * 200_000); sys.exit(1)"],
            startup_timeout_sec=5,
        )
        mock_proc = _make_mock_proc(exit_code=1)
        with (
            patch("agent.http_lifecycle.subprocess.Popen", return_value=mock_proc),
            patch("agent.http_lifecycle.httpx.AsyncClient") as MockClient,
            pytest.raises(HttpStartupError) as exc_info,
        ):
            client_instance, _ = _wire_http_client(MockClient)
            await mgr.start("test_server", cfg)
        assert len(exc_info.value.failure.stderr_full) <= 64 * 1024 + 10
```

Note: `pytest.mark.integration` should be kept to indicate this test exercises the `HttpServerLifecycleManager` class end-to-end, even though subprocess is mocked.

#### Test 2: `test_start_early_exit_stderr_from_log` (L498-513)

```python
    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_start_early_exit_stderr_from_log(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        _patch_open_to_tmp(monkeypatch, tmp_path)
        stderr_path = tmp_path / "test_server.stderr.log"
        stderr_path.write_text("BOOT_FAIL")
        mgr = HttpServerLifecycleManager()
        cfg = _make_test_cfg(
            cmd=[sys.executable, "-c", "import sys; sys.stderr.write('BOOT_FAIL'); sys.exit(1)"],
            startup_timeout_sec=5,
        )
        mock_proc = _make_mock_proc(exit_code=1)
        with (
            patch("agent.http_lifecycle.subprocess.Popen", return_value=mock_proc),
            patch("agent.http_lifecycle.httpx.AsyncClient") as MockClient,
            pytest.raises(HttpStartupError) as exc_info,
        ):
            client_instance, _ = _wire_http_client(MockClient)
            await mgr.start("test_server", cfg)
        assert "BOOT_FAIL" in exc_info.value.failure.stderr_full
```

#### Test 3: `test_start_timeout_stderr_from_log` (L515-532)

This test requires special handling because the health loop must time out (not detect early exit). Mock `killpg`/`getpgid` to prevent real signal delivery.

```python
    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_start_timeout_stderr_from_log(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        from agent import http_lifecycle as mod

        _patch_open_to_tmp(monkeypatch, tmp_path)
        stderr_path = tmp_path / "test_server.stderr.log"
        stderr_path.write_text("NEVER_READY")
        mgr = HttpServerLifecycleManager()
        cfg = _make_test_cfg(
            cmd=[sys.executable, "-c", "import sys, time; sys.stderr.write('NEVER_READY'); sys.stderr.flush(); time.sleep(60)"],
            startup_timeout_sec=1,
        )
        mock_proc = _make_mock_proc(exit_code=None)  # stays alive
        monkeypatch.setattr(mod.os, "killpg", MagicMock())
        monkeypatch.setattr(mod.os, "getpgid", lambda pid: 9999)
        with (
            patch("agent.http_lifecycle.subprocess.Popen", return_value=mock_proc),
            patch("agent.http_lifecycle.httpx.AsyncClient") as MockClient,
            pytest.raises(HttpStartupError) as exc_info,
        ):
            client_instance = AsyncMock()
            client_instance.get = AsyncMock(side_effect=Exception("connect refused"))
            MockClient.return_value.__aenter__ = AsyncMock(return_value=client_instance)
            MockClient.return_value.__aexit__ = AsyncMock(return_value=False)
            await mgr.start("test_server", cfg)
        assert "NEVER_READY" in exc_info.value.failure.stderr_full
```

Note: `monkeypatch` changes are scoped to this test only and are automatically reverted after the test completes.

## Validation plan

| Check | Tool / Command | Target |
|---|---|---|
| Phase 2 tests | `uv run pytest tests/test_lifecycle.py -k TestHttpLifecycleStderrLog -v` | all pass without real subprocess |
| Lifecycle full suite | `uv run pytest tests/test_lifecycle.py -v` | all pass |
| Lint | `uv run ruff check tests/test_lifecycle.py` | 0 errors |
| Safety: no real subprocess | Verify no `subprocess.Popen` calls reach OS during test run (strace or /proc inspection is optional) | — |
