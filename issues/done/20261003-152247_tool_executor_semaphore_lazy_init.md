# LOW: ToolExecutor セマフォ lazy initialization の将来拡張リスク

## Priority
Low

## Summary
`ToolExecutor._ensure_semaphores()` は lazy initialization で、`concurrency_limits` が設定されていない場合は `None` のまま。現在の設計では `concurrency_limits` は起動時固定なので、実際のリスクは低い。

## Background
`scripts/shared/tool_executor.py` line 122:
```python
self._ensure_semaphores()
sem = (self._semaphores or {}).get(server_key)
return await self._invoke_and_record(
    server_key, transport, tool_name, args, sem
)
```

## Problem
一見問題ないが、`concurrency_limits` が動的に変更される可能性があり、その場合既存の semaphore は更新されない。ただし、現在の設計では `concurrency_limits` は起動時固定なので、実際のリスクは低い。

## Evidence
- `tool_executor.py` line 122 のコードフロー
- `mcp_config.py` の `concurrency_limits` 定義

## Impact
- 将来の拡張で `concurrency_limits` が動的に変更される場合、予期せぬ挙動の可能性
- 現在のリスクは低い

## Acceptance Criteria
- [ ] 現状のままでも問題なし
- [ ] ただし、将来の拡張を見据えて、`concurrency_limits` の変更検知ロジックを追加することを検討

## Related Files
- `scripts/shared/tool_executor.py`
- `scripts/shared/mcp_config.py`
