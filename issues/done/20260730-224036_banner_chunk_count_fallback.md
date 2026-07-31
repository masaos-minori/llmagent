# エージェント起動バナーのチャンクカウントが失敗時に "?" を表示

## Summary

RAGチャンク数の取得に失敗すると、起動バナーに "?" が表示される。これはユーザーが RAG の状態を把握できなくなるが、機能には影響しない。

## Severity

Low

## Confidence

High

## Evidence

- `agent/repl.py:117-124` — `_get_chunk_count()` が SQLite/OSError/RuntimeError をキャッチして "?" を返す

## Current behavior

RAGチャンク数の取得に失敗すると、起動バナーに "?" が表示される。

## Impact

- ユーザーが RAG の状態を把握できなくなる
- ただし、機能には影響しない

## Recommended action

改善不要（既存のフォールバック挙動で十分）。

## Suggested Tests

- **Test target:** `agent/repl.py::_get_chunk_count()`
- **Behavior to verify:** RAGチャンク数の取得に失敗した場合、"?" が表示されること
- **Failure mode:** 機能に影響はないが、ユーザーが RAG の状態を把握できない
