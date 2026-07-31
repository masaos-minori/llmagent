# Windows環境でシグナルハンドラーの競合により SIGINT が消失する

## Summary

Windows環境で Ctrl-C を押すと、シグナルハンドラーが登録されていないためデフォルトの KeyboardInterrupt が発生。asyncioイベントループが中断され、MCPサブプロセスがクリーンアップされずに残る。また、`shutdown_all()` 内で `signal.signal()` を変更すると、他のスレッドからのシグナル通知が上書きされる可能性がある。

## Severity

High

## Confidence

Medium

## Evidence

- `agent/repl.py:743-745` — `loop.add_signal_handler(sig, _sigterm_handler)` は asyncio イベントループスレッド上で動作するが、Windows では `NotImplementedError` が発生し `except Exception: pass` で無視される
- `agent/repl.py:749-785` — Windows fallback で `pywin32` のコンソール制御ハンドラーを登録するが、`sys.stdout.isatty()` チェックが False の場合にスキップされる
- `agent/http_lifecycle.py:421-437` — `shutdown_all()` で `signal.signal(signal.SIGINT, ...)` をインストールするが、これはイベントループスレッドとは別のスレッドから呼ばれる可能性がある
- `agent/repl.py:753` — `sys.stdout.isatty()` チェックが False の場合、シグナルハンドラーが登録されない

## Current behavior

Windows環境で Ctrl-C を押すと、シグナルハンドラーが登録されていないためデフォルトの KeyboardInterrupt が発生。asyncioイベントループが中断され、MCPサブプロセスがクリーンアップされずに残る。

## Impact

- Windows環境でのシャットダウン時のプロセスリーク
- `shutdown_all()` 内で `signal.signal()` を変更すると、他のスレッドからのシグナル通知が上書きされる可能性
- パイプ接続時などにシグナルハンドラーが登録されない

## Recommended action

Windowsでも `pywin32` のコンソール制御ハンドラー経由でシグナルをイベントループに転送するコードを `repl.py:749-785` に実装済みだが、`sys.stdout.isatty()` チェックが False の場合（パイプ接続時など）にスキップされる。`sys.stdin.isatty()` もチェックすべき。

## Suggested Tests

- **Test target:** `agent/repl.py::AgentREPL.run()`
- **Behavior to verify:** Windows環境で Ctrl-C を押すと MCPサブプロセスがすべて terminate されること
- **Failure mode:** subprocess が残存する
