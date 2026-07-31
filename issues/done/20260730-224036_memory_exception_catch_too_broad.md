# メモリエイジェクションの例外キャッチ範囲が広すぎる

## Summary

`ctx.services_required.memory.on_session_start()` の例外を `except Exception as exc:` でキャッチし、メモリ機能を無効化して続行する。ただし、DB接続エラーのような致命的なエラーと埋め込みAPIエラーのような一時的なエラーが同じ処理になるため、適切なフォールバックができない。

## Severity

Medium

## Confidence

High

## Evidence

- `agent/startup.py:573-581` — `ctx.services_required.memory.on_session_start()` の例外を `except Exception as exc:` でキャッチ
- `agent/startup.py:576` — `ctx.conv.memory_disabled = True` がセットされるので、以降のターンで警告が表示される

## Current behavior

メモリエイジェクションに失敗してもセッションは継続される。ただし、`ctx.conv.memory_disabled = True` がセットされるので、以降のターンで警告が表示される。

## Impact

- メモリエイジェクションが失敗した場合、ユーザーはセッション中に警告を見るまで気づかない
- 重要なコンテキストが失われる可能性
- DB接続エラーと埋め込みAPIエラーが同じ処理になるため、適切な対応ができない

## Recommended action

例外の種類ごとに異なる対応（例: DB接続エラーは致命的、埋め込みAPIエラーは警告のみ）を分ける。

## Suggested Tests

- **Test target:** `agent/startup.py::StartupOrchestrator._setup_prompt()`
- **Behavior to verify:** メモリエイジェクションの例外種類ごとに異なるフォールバックが適用されること
- **Failure mode:** すべての例外が同じ処理（メモリ無効化）になる
