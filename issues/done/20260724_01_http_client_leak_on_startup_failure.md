# StartupOrchestrator.run() 失敗時に HTTP クライアントが解放されない

## Priority

Critical

## Summary

StartupOrchestrator.run() が例外を送出して起動に失敗した場合、AgentREPL._run_repl_loop() の finally ブロック（`svc.http.aclose()` を呼び出す）が実行されず、HTTP クライアントがリークする。

## Problem

`repl.py:506-511`:

```python
startup = StartupOrchestrator(self._ctx, self._view)
try:
    self._cmds, self._orchestrator = await startup.run()
except Exception as e:
    self._view.write_fatal(f"Startup failed: {e}")
    raise
await self._run_repl_loop()
```

`StartupOrchestrator.run()` が例外を送出すると、`_run_repl_loop()` は決して実行されない。つまり `_run_repl_loop()` の finally ブロック（`svc.http.aclose()` を含む）も実行されない。

`StartupOrchestrator._start_servers()` で HTTP プロセスが生成されている場合、それらのプロセスも同時にクリーンアップされない可能性がある。

## Root Cause

`startup.run()` の成功/失敗によって `_run_repl_loop()` の実行有無が決まるため、finally ブロックによるリソース解放が条件付きになっている。

## Fix Direction

`_close_resources()` を `AgentREPL.run()` の finally ブロックに移動し、起動フェーズでのリソース解放を確実にする。または、`StartupOrchestrator.run()` が例外を送出した場合にも明示的にリソースを解放するパスを追加する。

## Acceptance Criteria

- [ ] StartupOrchestrator.run() が例外を送出しても HTTP クライアントが閉じられる
- [ ] MCP subprocess が生成された後のエラーでも subprocess が終了する
- [ ] リソース解放が条件付きではなく常に実行される
