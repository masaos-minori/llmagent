# HistoryMessage への変換で予期せぬキーが静かに破棄される

## Priority

Low

## Summary

`_persist_session_memories()` で `ctx.conv.history` の dict を `HistoryMessage` dataclass に変換する際、予期せぬキーが含まれている場合、それらは silent に破棄される。バリデーションや警告がない。

## Problem

`repl.py:120-123`:

```python
history = [
    HistoryMessage(role=m["role"], content=m.get("content") or "")
    for m in ctx.conv.history
]
```

`HistoryMessage` は dataclass であり、予期せぬキーワード引数は TypeError を送出する可能性がある。ただし、dict が追加のキーを持っていても、dataclass コンストラクタはそれらを無視する（Python の仕様）。

## Root Cause

dict-to-dataclass 変換で追加のキーの処理が明示的に行われていない。

## Fix Direction

変換前に追加のキーを検出し、警告を出力するか、エラーとする。または、`**m` のように展開して予期せぬキーによる問題を早期に検知する。

## Acceptance Criteria

- [ ] 予期せぬキーが含まれている場合に警告またはエラーが出力される
- [ ] Silent なデータ損失が発生しない
- [ ] 変換前の検証が行われる
