# DiagnosticStore が StateStore レイヤをバイパスして直接 DB にクエリする

## Priority

Medium

## Summary

`_persist_session_diagnostics()` は workflow テーブルに対して `SQLiteHelper("workflow")` で直接クエリを実行し、StateStore の抽象レイヤをバイパスしている。StateStore が未コミットの書き込みを持っている場合、診断サマリーは不整合になる。

## Problem

`repl.py:158-194`:

```python
with SQLiteHelper("workflow").open(row_factory=True) as wdb:
    sid = str(session_id)
    rows = wdb.fetchall(
        "SELECT COUNT(*) as cnt FROM tasks WHERE session_id=?",
        (sid,),
    )
    task_count = int(rows[0]["cnt"]) if rows else 0
    ...
```

StateStore は `workflow.sqlite` へのアクセスを一元管理しているはずだが、このコードは StateStore を介さずに直接接続を開いている。

## Root Cause

`_persist_session_diagnostics()` が StateStore の API を使わずに直接 SQL クエリを実行している。

## Fix Direction

StateStore の API を通じてデータを取得する。または、StateStore に diagnostic query メソッドを追加する。

## Acceptance Criteria

- [ ] DiagnosticStore が StateStore の API を使用する
- [ ] StateStore の未コミット書き込みが診断サマリーに含まれる
- [ ] StateStore レイヤのバイパスが解消される
