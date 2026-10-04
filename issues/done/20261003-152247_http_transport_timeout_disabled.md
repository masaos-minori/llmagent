# LOW: HttpTransport タイムアウト設定の無効化

## Priority
Low

## Summary
`HttpTransport.__init__()` で `self._timeout <= 0` の場合、`timeout=None` になり、httpx のデフォルトタイムアウト（10秒）が適用される。設定ファイルで `call_timeout_sec` を 0 や負の数に設定した場合、意図せずデフォルトタイムアウトが適用される。

## Background
`scripts/shared/http_transport.py` line 117:
```python
timeout = httpx.Timeout(self._timeout) if self._timeout > 0 else None
```

## Problem
タイムアウト設定のドキュメントに明記されていない。0 または負の数はデフォルトタイムアウト（10秒）を意味するが、これが意図的な動作かどうか不明。

## Evidence
- `http_transport.py` line 117 のコードフロー
- httpx のデフォルトタイムアウト仕様

## Impact
- 設定ファイルでタイムアウトを無効化しようとした場合、意図せずデフォルトタイムアウトが適用される
- 設定の意図と実際の挙動の不一致

## Acceptance Criteria
- [ ] タイムアウト設定のドキュメントを更新
- [ ] 「0 または負の数はデフォルトタイムアウト（10秒）を意味する」旨を明記
- [ ] または 0/負数の設定を禁止し、エラーを送出するように変更

## Related Files
- `scripts/shared/http_transport.py`
