# MCPサブプロセスのシャットダウン時にプロセスグループがリークする

## Summary

MCPサーバーのHTTPサブプロセス終了時、`getpgid()` が失敗した場合のプロセスグループがシャットダウンされず、ゾンビプロセスとして残る。`agent/http_lifecycle.py:290` で `os.getpgid(proc.pid)` に失敗すると `_http_pgids` に登録されず、`shutdown_all()` で `os.killpg()` が呼ばれないため、親プロセスだけが terminate され子プロセスが残存する。

## Severity

Critical

## Confidence

High

## Evidence

- `agent/http_lifecycle.py:290` — `os.getpgid(proc.pid)` が成功しない場合、`_http_pgids` に登録されない
- `agent/http_lifecycle.py:321-323` — 失敗時のクリーンアップで `_http_procs.pop(server_key, None)` と `_http_pgids.pop(server_key, None)` が呼ばれるが、`_http_pgids` は空のまま
- `agent/repl.py:797-799` — finally ブロックでの subprocess terminate は `proc.terminate()` のみでプロセスグループを殺さない
- `agent/http_lifecycle.py:130-137` — `_terminate_with_timeout()` は `pgid` が存在する場合のみ `os.killpg()` を呼び出す

## Current behavior

`getpgid()` が失敗したサブプロセスは、エージェント終了時にプロセスグループ単位で殺されない。親プロセスだけが terminate され、子プロセス（例: node subprocess → child node process）がゾンビとして残る。

## Impact

- リソースリーク（PIDリーク）、意図しないプロセスの継続実行
- 複数回の起動でシステムリソース枯渇の可能性
- システムのセキュリティポリシー違反（予期しないプロセスの実行）

## Recommended action

`getpgid()` 失敗時に `start_new_session=True` を設定しているため、`os.killpg(os.getpid(), signal.SIGTERM)` でエージェント自身のプロセスグループを殺すか、または `psutil` を使ってプロセスツリーを再帰的に探索してすべて terminate する。

## Suggested Tests

- **Test target:** `agent/http_lifecycle.py::HttpServerLifecycleManager.start()`
- **Behavior to verify:** `getpgid()` が失敗した場合のプロセスグループがリークしないこと
- **Failure mode:** プロセスが残存し、次回起動でポート競合が発生する
