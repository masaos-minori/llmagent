# Issue: startup.py - MCP subprocess orphaned on dual failure during rollback

## 概要

`StartupOrchestrator.run()` で起動中に例外が発生し、MCPサブプロセスのロールバックを試みる際、ロールバック自体も失敗するとサブプロセスがオーファン化する。

## 該当コード

`scripts/agent/startup.py:64-72`

```python
except Exception:
    if _servers_started:
        try:
            await self._ctx.services_required.lifecycle.shutdown_all()
        except Exception as shutdown_err:
            logger.warning(
                "Startup rollback: shutdown_all() failed: %s", shutdown_err
            )
    raise
```

## 問題点

- `_servers_started=True` の後に例外が発生した場合、`shutdown_all()` が呼び出される
- `shutdown_all()` がさらに例外を投げた場合、警告ログのみ出力され、元の例外が再送出される
- この場合、MCPサブプロセスはシャットダウンされず、プロセスとして残存する
- 警告ログは非同期に出力されるため、運用者が目にする可能性が低い

## 再現シナリオ

1. HTTP subprocess MCP server A を起動成功
2. HTTP subprocess MCP server B の起動に失敗（startup_timeout_sec超過など）
3. `shutdown_all()` を呼び出す
4. `shutdown_all()` 内で SIGINT ハンドラの復元に失敗（`ValueError`）
5. サーバーAのプロセスが残ったままになる

## 改善案

- ロールバック失敗時も FATAL レベルでログ出力し、運用者に明示的に通知
- ロールバック後のプロセス状態を検証し、オーファン化したプロセスがある場合は警告
- または、ロールバック失敗時は RuntimeError を再送出して起動全体を失敗させる

## 優先度

高 - プロセスのオーファン化により、ポートの競合やリソースリークの原因となる
