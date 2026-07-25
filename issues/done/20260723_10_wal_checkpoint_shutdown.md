---
title: "WAL checkpoint at shutdown may fail silently if DB connection is already closed"
severity: Low
confidence: Medium
status: new
created: 20260723-200000
---

## Title

WAL checkpoint at shutdown may fail silently if DB connection is already closed

## Severity

Low

## Confidence

Medium

## Evidence

- `repl.py:259-266` — AgentREPL._close_resources() WAL checkpoint

## Current Behavior

`_close_resources()`でWALチェックポイントが実行されるが、`SQLiteHelper("session").open(write_mode=True)`で新しい接続が開かれる。この時点で既存のセッションDB接続がすでに閉じている場合、**新しい接続は古いWALファイルを読み取る必要があるが、WALファイルが破損している可能性がある**。

## Impact

シャットダウン時のWALチェックポイントが失敗し、データ損失の可能性。

## Recommended Action

シャットダウン前に既存のDB接続のWALチェックポイントを確実に実行する。

## Related Files

- scripts/agent/repl.py
