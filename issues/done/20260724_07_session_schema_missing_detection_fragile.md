# Session schema missing エラー検出がテキストマッチングに依存している

## Priority

High

## Summary

`"no such table" in msg.lower()` というテキストベースのエラー判定は、SQLite のエラーメッセージがローカライズされるかフォーマットが変わると機能しなくなる。

## Problem

`repl.py:446-448`:

```python
if "no such table" in msg.lower():
    self._view.write_fatal(
        "Session schema missing. Run: bash deploy/init_db.sh to initialize the database."
    )
```

SQLite のエラーメッセージが日本語や他の言語にローカライズされると、この判定は false negative になる。また、SQLite のバージョンアップでエラーメッセージのフォーマットが変わる可能性もある。

## Root Cause

エラータイプをテキストマッチングで判定している。

## Fix Direction

`sqlite3.OperationalError` のサブクラスや特定の error code で判定する。または、スキーマ存在チェックを明示的に行う。

## Acceptance Criteria

- [ ] ローカライズされた SQLite エラーメッセージでも正しく検出される
- [ ] SQLite バージョンアップでエラーメッセージが変わっても機能する
- [ ] テキストマッチングではなく構造的なエラー判定を行う
