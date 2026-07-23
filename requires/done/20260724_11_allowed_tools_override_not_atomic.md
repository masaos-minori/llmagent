# Allowed tools override が finally ブロック外で例外発生すると永久的に上書きされる

## Priority

Medium

## Summary

`_process_turn()` で `ctx.cfg.tool.allowed_tools` を一時的にオーバーライドし、finally で元に戻す。しかし、try/finally の外で例外が発生した場合、元の値は永久に上書きされたままになる。

## Problem

`orchestrator.py:461-482`:

```python
original_allowed = ctx.cfg.tool.allowed_tools
if self._allowed_tools is not None:
    ctx.cfg.tool.allowed_tools = self._allowed_tools
try:
    ...
finally:
    ctx.cfg.tool.allowed_tools = original_allowed  # always restore
```

もし `try` ブロック内で例外が発生せず、`finally` が正常に実行されても、その後の処理（例：`_handle_turn_end`）で例外が発生した場合、`original_allowed` の値はすでに失われている。

また、`_process_turn()` から戻った後に `ctx.cfg.tool.allowed_tools` が変更される可能性もある。

## Root Cause

`original_allowed` のスコープが `_process_turn()` のみで、finally ブロックの外の例外では復元できない。

## Fix Direction

`original_allowed` をインスタンス変数として保持し、finally ブロックの外でも復元できるようにする。または、`_process_turn()` の呼び出し前後で値を復元する。

## Acceptance Criteria

- [ ] `_process_turn()` の呼び出し前後で allowed_tools の値が常に復元される
- [ ] finally ブロックの外の例外でも値が上書きされない
- [ ] 並列ターン実行時の競合が発生しない
