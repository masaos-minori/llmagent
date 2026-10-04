# LOW: ToolRouteResolver strict_mode ドキュメントの正確性

## Priority
Low

## Summary
`ToolRouteResolver.resolve()` のドキュメントでは「`strict_mode=True` causes `resolve()` to raise `ValueError` directly via `_raise_strict_error()` before reaching the `warn_on_missing` check」とあるが、実際には `strict_mode=False` でも最終的に `ValueError` を送出する。

## Background
`scripts/shared/route_resolver.py` line 44-52:
```python
def resolve(self, tool_name: str) -> str:
    if (key := self._lookup_runtime_registry(tool_name)) is not None:
        return key
    if self._strict_mode:
        self._raise_strict_error(tool_name)
    if self._warn_on_missing:
        logger.warning(...)
    raise ValueError(f"Unknown tool: {tool_name!r}")
```

## Problem
ドキュメントでは `strict_mode=True` の場合にのみ `ValueError` が送出されるように読めるが、実際には両モードとも `ValueError` を送出する。違いはエラーメッセージのみ。

## Evidence
- `route_resolver.py` line 44-52 のコードフロー
- ドキュメントとの比較

## Impact
- 開発者がドキュメントを信頼して `strict_mode=False` の場合に `ValueError` が送出されないと思い込む可能性がある
- ドキュメントの信頼性低下

## Acceptance Criteria
- [ ] ドキュメントを更新して、両モードとも `ValueError` を送出すること、違いはエラーメッセージのみであることを明記
- [ ] または実装をドキュメントに合わせて修正

## Related Files
- `scripts/shared/route_resolver.py`
