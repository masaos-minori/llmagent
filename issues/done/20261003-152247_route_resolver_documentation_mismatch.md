# MEDIUM: ToolRouteResolver ドキュメントと実装の不一致

## Priority
Medium

## Summary
`ToolRouteResolver.resolve()` のドキュメントでは「`strict_mode=True` causes `resolve()` to raise `ValueError` directly」とあるが、実際には `strict_mode=False` でも最終的に `ValueError` を送出する。

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
ドキュメントと実装の不一致。`strict_mode=True` の場合は `_raise_strict_error()` を呼び出して即座に `ValueError` を送出し、`strict_mode=False` の場合はまず `warn_on_missing` チェックを行い、その後 `ValueError` を送出。両者の違いはエラーメッセージのみ。

## Evidence
- `route_resolver.py` line 44-52 のコードフロー
- ドキュメントとの比較

## Impact
- 開発者がドキュメントを信頼して `strict_mode=False` の場合に `ValueError` が送出されないと思い込む可能性がある
- ドキュメントの信頼性低下

## Acceptance Criteria
- [ ] ドキュメントを更新して「`strict_mode` はエラーメッセージの厳密さの違いのみ。両モードとも未解決ツールに対して `ValueError` を送出する」旨を明記
- [ ] または実装をドキュメントに合わせて修正

## Related Files
- `scripts/shared/route_resolver.py`
