# CRITICAL: ToolTransportInvoker セマフォ解放漏れ

## Priority
Critical

## Summary
`ToolTransportInvoker._execute_with_semaphore()` で `nullcontext` を `async with` として使用する場合、型チェッカー警告およびセマフォ解放意図の不明確さ。

## Background
`scripts/shared/tool_transport_invoker.py` line 182-183:
```python
async with self._maybe_semaphore(sem):
    return await transport.call(tool_name, args)
```

`_maybe_semaphore()` は `sem` が `None` の場合 `nullcontext` を返す。

## Problem
1. `nullcontext` は `AbstractAsyncContextManager` を実装していないため、型チェッカーが警告を出力する可能性がある
2. `nullcontext` の `__aexit__` は何もせず、セマフォ解放の意図が不明確になる

## Evidence
- `contextlib.nullcontext` は同期コンテキストマネージャーのみ実装
- Python 3.7+ で `async with nullcontext:` は動作するが、型チェッカー警告の原因となる

## Impact
- 型チェッカー警告により、実際の型ミスマッチの見落としリスク
- コードレビュー時、セマフォ解放の意図が不明確

## Acceptance Criteria
- [ ] `nullcontext` の代わりに `contextlib.nullcontext()` を明示的にインポート
- [ ] 型ヒントを `contextlib.AbstractAsyncContextManager[None]` に統一
- [ ] セマフォ解放の意図が明確なコメントを追加

## Related Files
- `scripts/shared/tool_transport_invoker.py`
- `scripts/shared/mcp_config.py`
