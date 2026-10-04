# MEDIUM: TransportDTO from_transport() の server_key デフォルト値

## Priority
Medium

## Summary
`ToolCallResult.from_transport()` は `server_key=""` をデフォルトで設定する。`from_transport()` が直接呼ばれる場合（例えばテストや他のコードパス）、`server_key=""` になる。また `error_type="tool"` も同様に、transport レベルのエラーの場合は `"transport"` であるべきだが、`"tool"` になる。

## Background
`scripts/shared/transport_dto.py` line 18-30:
```python
@classmethod
def from_transport(cls, output: str, is_error: bool, request_id: str = "") -> "ToolCallResult":
    return cls(
        output=output,
        is_error=is_error,
        request_id=request_id,
        server_key="",  # ← empty string
        source="mcp",
        error_type="tool" if is_error else "",
    )
```

## Problem
1. `from_transport()` が直接呼ばれる場合、`server_key=""` になる
2. `error_type="tool"` も同様に、transport レベルのエラーの場合は `"transport"` であるべきだが、`"tool"` になる

## Evidence
- `transport_dto.py` line 18-30 のコードフロー
- `HttpTransport._parse_http_response()` は `dataclasses.replace(parsed, server_key=self._server_key)` で上書きする

## Impact
- テストや他のコードパスで `server_key=""` になる可能性
- エラータイプが誤って `"tool"` になる可能性

## Acceptance Criteria
- [ ] `from_transport()` の引数に `server_key` と `error_type` を追加
- [ ] caller が明示的に指定できるようにする
- [ ] またはメソッド名を `from_transport_result` に変更して、transport レベルの結果であることを明確にする

## Related Files
- `scripts/shared/transport_dto.py`
