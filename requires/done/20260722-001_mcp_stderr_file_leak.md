# MCPサーバープロセス起動時のstderrファイルリーク

## 深刻度: 中程度

## 概要

`McpServerLifecycle.start_server()` でPopen()成功後、`os.getpgid()` が失敗した場合、
_stderr_files_ と _stderr_log_paths_ がクリーンアップされない。

## 該当コード

`scripts/agent/http_lifecycle.py:235-243`

```python
except Exception:
    stderr_fh.close()
    self._stderr_files.pop(server_key, None)
    self._stderr_log_paths.pop(server_key, None)
    raise
```

## 問題の詳細

1. `Popen()` が成功し、`self._http_procs[server_key] = proc` が実行される
2. その直後の `os.getpgid(proc.pid)` が OSError を発生（プロセスが既に終了している可能性）
3. この場合、上記 except ブロックは実行されない（OSErrorはexcept Exceptionでキャッチされない）
4. `_stderr_files` と `_stderr_log_paths` にエントリが残ったまま
5. `_terminate_with_timeout()` で `proc.terminate()` が呼ばれるが、stderrファイルはリークする

## 影響

- サーバー再起動時に `_stderr_files` エントリが累積
- 長時間稼働でファイルディスクリプタが枯渇する可能性がある
- 一時的なプロセス終了の競合条件で発生

## 修正案

```python
try:
    self._http_pgids[server_key] = os.getpgid(proc.pid)
except OSError:
    # Process may have already exited; clean up stderr resources
    stderr_fh.close()
    self._stderr_files.pop(server_key, None)
    self._stderr_log_paths.pop(server_key, None)
    logger.warning(
        "Failed to get pgid for %s (pid=%d); process may have exited",
        server_key, proc.pid
    )
```
