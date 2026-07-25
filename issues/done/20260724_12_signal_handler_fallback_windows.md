# Windows 環境でシグナルハンドラのフォールバックが asyncio と統合されない

## Priority

Low

## Summary

Windows では `loop.add_signal_handler()` がサポートされていないため、`_signal.signal(sig, lambda *_: _sigterm_handler())` がフォールバックとして使われる。これは asyncio のイベントループと統合されず、シグナルのタイミングによって挙動が不安定になる。

## Problem

`repl.py:500-504`:

```python
for sig in (signal.SIGTERM, signal.SIGINT):
    try:
        loop.add_signal_handler(sig, _sigterm_handler)
    except NotImplementedError:
        _signal.signal(sig, lambda *_: _sigterm_handler())
```

`NotImplementedError` は Windows で発生する。`_signal.signal()` はプロセス全体のシグナルハンドラを設定するため、asyncio のイベントループとは独立して動作する。

## Root Cause

Windows では `add_signal_handler()` がサポートされていない。

## Fix Direction

Windows 用のシグナルハンドラ実装を別途用意する（例：`msvcrt.set_signal_handler()` や asyncio-proactor-event-loop のシグナル対応）。または、Windows では graceful shutdown を別のメカニズム（ファイル監視など）で実現する。

## Acceptance Criteria

- [ ] Windows でも SIGTERM/SIGINT が正しく受信される
- [ ] asyncio イベントループとシグナルハンドラが統合される
- [ ] Windows 固有のシグナル処理が安定して動作する
