# Issue: orchestrator.py - Background task exception silently swallowed

## 概要

最初のターンで生成されたバックグラウンドタスク（セッションタイトル生成など）が例外を投げた場合、asyncioのデフォルト動作により例外がログ出力されず、静かに消える。

## 該当コード

`scripts/agent/orchestrator.py:543-546`

```python
if ctx.stats.stat_turns == 1 and self._on_first_turn is not None:
    _task = asyncio.create_task(self._on_first_turn(line))
    self._background_tasks.add(_task)
    _task.add_done_callback(self._background_tasks.discard)
```

## 問題点

- `asyncio.create_task()` で生成されたタスクが例外を投げた場合、`add_done_callback` は実行されるが、例外はキャッチされない
- asyncioのデフォルトでは、未処理の例外は `Task.__del__()` でログ出力されるが、これは非同期イベントループの終了時にのみ発生
- タスクの実行中に例外が発生しても、現在のイベントループでは検知されない
- `self._background_tasks` からタスクが削除されるだけなので、例外の内容は失われる

## 再現シナリオ

1. 最初のユーザーメッセージを送信
2. `_on_first_turn` がセッションタイトル生成のためにバックグラウンドタスクを開始
3. タスク内で `sqlite3.Error` や `RuntimeError` が発生
4. 例外は `Task.__del__()` でのみログ出力される（イベントループ終了時）
5. オペレーターはタイトルが生成されないことに気づくが、理由がわからない

## 改善案

- `add_done_callback` で例外をキャッチし、ログ出力する

```python
def _discard_and_log(task: asyncio.Task) -> None:
    self._background_tasks.discard(task)
    if task.exception():
        logger.exception("Background task failed: %s", task.exception())

_task = asyncio.create_task(self._on_first_turn(line))
self._background_tasks.add(_task)
_task.add_done_callback(_discard_and_log)
```

## 優先度

中 - バックグラウンドタスクの失敗が検知できない
