# Signal handler と asyncio event loop の競合状態

## Priority

Medium

## Summary

シグナルハンドラが `asyncio.wait()` のブロック中にシグナルを受信した場合、イベントは設定されるが、現在の wait が完了するまで認識されない。信号が逃げる可能性がある。

## Problem

`repl.py:353-365`:

```python
done, pending = await asyncio.wait(
    {input_coro, shutdown_coro},
    return_when=asyncio.FIRST_COMPLETED,
)
```

`shutdown_coro` は `shutdown_event.wait()` を待機している。シグナルが届くと `shutdown_event.set()` が呼ばれるが、`asyncio.wait()` の結果が返ってくるまでに遅延がある。

`repl.py:491-504`:

```python
def _sigterm_handler() -> None:
    self._ctx.conv.shutdown_requested = True
    if self._shutdown_event is not None:
        self._shutdown_event.set()
```

## Root Cause

シグナルハンドラと asyncio の非同期イベントが異なるタイムスケールで動作するため、競合状態が発生する。

## Fix Direction

`asyncio.wait_for()` と `asyncio.Event` を組み合わせて、シグネルされたイベントを即座に検知する。または、シグナル受信時に pending な future をキャンセルする。

## Acceptance Criteria

- [ ] シグナル受信後、即時にシャットダウンが開始される
- [ ] `asyncio.wait()` のブロック中でもシグナルが逃げない
- [ ] シグナルハンドラと asyncio イベントの競合状態が発生しない
