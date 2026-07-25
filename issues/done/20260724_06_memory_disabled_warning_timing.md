# Memory injection 失敗時にユーザーが警告を見るタイミングが制限される

## Priority

High

## Summary

`memory_disabled` フラグは startup フェーズで設定されるが、警告メッセージはユーザーが入力ラインを送信するまで表示されない。セッション直後に終了する場合、ユーザーはメモリ無効化に気づかない。

## Problem

`context.py:69`:

```python
memory_disabled: bool = False  # True when memory injection failed during startup
```

`repl.py:309-313`:

```python
if ctx.conv.memory_disabled and not ctx.conv.memory_warning_shown:
    ctx.conv.memory_warning_shown = True
    self._view.write_warning(
        f"{OutputTag.NON_FATAL} Memory is disabled for this session."
    )
```

この警告は `_repl_loop` のループ内でのみ表示される。ユーザーが何も入力せずにセッションを終了する場合、警告は表示されない。

## Root Cause

警告の表示が「ユーザー入力のトリガー」に依存している。

## Fix Direction

startup フェーズで `memory_disabled` が設定された場合、即座に警告を表示する。または、セッション終了時に必ずチェックする。

## Acceptance Criteria

- [ ] Memory injection 失敗時にユーザーが即座に警告を見る
- [ ] セッション終了前に必ず警告が表示される
- [ ] 既に警告が表示されている場合は重複して表示されない
