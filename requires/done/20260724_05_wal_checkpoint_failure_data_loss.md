# シャットダウン時の WAL チェックポイント失敗でデータ損失リスクがある

## Priority

High

## Summary

シャットダウン時に WAL チェックポイントに失敗した場合、エラーは警告として記録されるが、コネクションはチェックポイントなしで閉じられる。これにより、チェックポイント前の未反映データが失われる可能性がある。

## Problem

`repl.py:261-271`:

```python
try:
    with SQLiteHelper("session").open(write_mode=True) as db:
        wal_mode = db.execute("PRAGMA journal_mode").fetchone()[0]
        if wal_mode.lower() == "wal":
            db.checkpoint("TRUNCATE")
            logger.info("WAL checkpoint completed on shutdown")
        else:
            logger.debug("WAL checkpoint skipped: journal mode is %r", wal_mode)
except sqlite3.Error as e:
    errors.append(("wal_checkpoint", f"{type(e).__name__}: {e}"))
    logger.warning("WAL checkpoint failed on shutdown: %s", e)
```

チェックポイントに失敗してもコネクションは閉じられるため、WAL ファイル内の未コミットデータが失われる。

## Root Cause

チェックポイント失敗時にロールバックや再試行のロジックがない。

## Fix Direction

チェックポイント失敗時に再度試行するか、少なくとも WAL ファイルの内容を保存する。または、チェックポイント失敗を致命的エラーとして扱う。

## Acceptance Criteria

- [ ] WAL チェックポイント失敗時にデータ損失が発生しない
- [ ] チェックポイント失敗時に適切な対応（再試行またはエラー処理）が行われる
- [ ] WAL ファイルの内容が保持される
