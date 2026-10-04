# MEDIUM: HttpTransport HTTPStatusError と RETRYABLE_STATUS の重複チェック

## Priority
Medium

## Summary
`HttpTransport.call()` で `resp.raise_for_status()` が `_RETRYABLE_STATUS` のステータスを返すことはあり得ないため、`except httpx.HTTPStatusError` ブロック内の `_RETRYABLE_STATUS` チェックは不要なコードパス。

## Background
`scripts/shared/http_transport.py` line 128-161:
```python
if resp.status_code in self._RETRYABLE_STATUS:
    last_retryable_status = resp.status_code
    # ... retry logic ...
    continue
resp.raise_for_status()
# ...
except httpx.HTTPStatusError as e:
    # ...
    if e.response.status_code in self._RETRYABLE_STATUS:
        last_retryable_status = e.response.status_code
```

## Problem
`httpx.Response.raise_for_status()` は 4xx/5xx のみ `HTTPStatusError` を送出する。`_RETRYABLE_STATUS` は通常 429, 500, 502, 503, 504 などの一時的なエラーであるため、`raise_for_status()` が `_RETRYABLE_STATUS` のステータスを返すことはあり得るが、その場合は `HTTPStatusError` として捕捉される。この重複チェックは将来のリファクタリングで混乱を招く可能性がある。

## Evidence
- `http_transport.py` line 128-161 のコードフロー
- `httpx.HTTPStatusError` の仕様

## Impact
- コードの保守性低下
- 将来のリファクタリングで誤解を招く可能性

## Acceptance Criteria
- [ ] `except httpx.HTTPStatusError` ブロック内の `_RETRYABLE_STATUS` チェックを削除
- [ ] またはコメントで「これは理論的に到達しないが、安全のため残す」旨を明記

## Related Files
- `scripts/shared/http_transport.py`
