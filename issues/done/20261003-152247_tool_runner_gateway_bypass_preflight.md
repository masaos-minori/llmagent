# HIGH: Gateway bypass 時の preflight チェックの二重適用とガード漏れ

## Priority
High

## Summary
`tool_runner.execute_one_tool_call()` で Gateway が存在しない場合、`RepositoryGateway` の他のガード（pending approval チェック、監査ログ）がスキップされる。

## Background
`scripts/agent/tool_runner.py` line 122-141:
```python
if ctx.services_required.gateway is not None:
    result = await ctx.services_required.gateway.execute(ctx, name, args)
else:
    # Gateway-bypass safety justification:
    op = classify_operation_type(name, ctx.services_required.runtime_tools)
    if op != OperationType.READ:
        try:
            check_preflight(ctx.cfg, name, args)
        except PolicyViolationError as exc:
            logger.warning("tool_runner.policy_denied tool=%r reason=%s", name, exc)
            raise  # Re-raise to prevent unauthorized execution
    result = await ctx.services_required.tools.execute(name, args)
```

## Problem
1. Gateway bypass 時は `RepositoryGateway` の pending approval チェックがスキップされる
2. Gateway bypass 時は監査ログが記録されない
3. `check_preflight()` は直接呼び出すが、`RepositoryGateway` は batch-level gate を経由するため、二重適用の可能性がある

## Evidence
- `tool_runner.py` line 122-141 のコードフロー
- `repository_gateway.py` docstring: "Precondition: this gateway does not itself prompt for interactive approval. Callers must route write/risky tool calls through tool_runner.execute_all_tool_calls()'s batch-level gate"

## Impact
- Gateway bypass 時に承認チェックがスキップされる可能性
- 監査ログの欠落により、セキュリティ監査で問題

## Acceptance Criteria
- [ ] Gateway bypass 時も pending approval チェックを実行
- [ ] Gateway bypass 時も監査ログを記録
- [ ] または bypass 時の動作をドキュメントに明記

## Related Files
- `scripts/agent/tool_runner.py`
- `scripts/agent/repository_gateway.py`
- `scripts/agent/tool_policy.py`
