# First-turn background task の例外がユーザーに通知されない

## Priority

Critical

## Summary

最初のターンで生成される background task (`_on_first_turn`) の例外がログ出力のみで、ユーザーには一切通知されない。`_consecutive_bg_failures` カウンターは5回連続で初めて警告を出力する。

## Problem

`orchestrator.py:558-561`:

```python
_task = asyncio.create_task(self._on_first_turn(line))
self._background_tasks.add(_task)
_task.add_done_callback(self._discard_and_log)
```

`_discard_and_log` は `orchestrator.py:564-589`:

```python
def _discard_and_log(self, task: asyncio.Task[Any]) -> None:
    exc = task.exception()
    if exc is not None:
        if isinstance(exc, asyncio.CancelledError):
            self._consecutive_bg_failures = 0
        else:
            self._consecutive_bg_failures += 1
            if self._consecutive_bg_failures == 1:
                logger.warning("First background task failure: %s", exc)
            elif self._consecutive_bg_failures >= BG_FAILURE_THRESHOLD:
                logger.error("Consecutive background task failures (%d): %s", ...)
            else:
                logger.warning("Background task failure #%d: %s", ...)
```

1回目の失敗は warning レベルのみ。ユーザーはログを見ない限り異常に気づかない。

## Root Cause

背景タスクの例外を silent に処理する設計だが、最初のターンのセットアップ失敗はユーザーに影響が大きいため、silent にすべきではない。

## Fix Direction

1回目の失敗でもユーザーに通知する（warning メッセージを出力または UI に表示）。または、第一ターン用の特別なフォールバックパスを用意する。

## Acceptance Criteria

- [ ] First-turn background task の例外が1回目でもユーザーに通知される
- [ ] ログに記録される
- [ ] ターン処理自体は継続できる（または明確なエラーメッセージが表示される）
