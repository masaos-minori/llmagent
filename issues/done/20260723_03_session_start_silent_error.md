---
title: "Session start fails silently on non-'no such table' sqlite3.Error"
severity: High
confidence: High
status: new
created: 20260723-200000
---

## Title

Session start fails silently on non-"no such table" sqlite3.Error

## Severity

High

## Confidence

High

## Evidence

- `repl.py:432-449` — AgentREPL._run_repl_loop() session start error handling

## Current Behavior

`ctx.session.start()`でsqlite3.Errorが発生した場合、`"no such table"`を含む場合は具体的なエラーメッセージが表示されるが、それ以外のエラー（例：`database is locked`、`disk I/O error`）は`"Database unavailable during session start: {e}"`という一般的なメッセージしか表示されない。さらに、このエラー発生後に`_run_repl_loop()`のfinallyブロックが実行され、`_persist_session_memories()`や`_close_resources()`が呼ばれるが、`ctx.services`はまだ`None`（`build_agent_context()`がまだ呼ばれていないため）。

## Impact

データベースロックやI/Oエラーが発生した場合、ユーザーには「Database unavailable」という曖昧なメッセージしか表示されず、根本原因の特定が困難。

## Recommended Action

sqlite3.Errorの種類ごとに異なるエラーメッセージを表示するか、少なくとも`e.__class__.__name__`を含める。

## Related Files

- scripts/agent/repl.py
