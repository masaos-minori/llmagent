# HIGH: HttpTransport リトライ exhausted 時に元の例外コンテキストが消失

## Priority
High

## Summary
`HttpTransport.call()` でリトライが全て失敗した場合、`_build_exhaustion_message` で生成された新しい `TransportError` が送出され、元の例外スタックトレースが失われる。

## Background
`scripts/shared/http_transport.py` line 163-166:
```python
else:
    msg = self._build_exhaustion_message(name, last_retryable_status)
    logger.error(msg)
    raise TransportError(msg)
raise last_exc or TransportError(f"call failed: {name}")
```

## Problem
`for...else` ブロック内で既に `raise TransportError(msg)` しているため、最後の `raise last_exc` は never reached。元の例外チェーンが失われる。

## Evidence
- `http_transport.py` line 163-166 のコードフロー
- Python の例外チェーン (`raise ... from ...`) は元の例外情報を保持するが、新しい例外でラップすると失われる

## Impact
- デバッグ時に問題の原因特定が困難
- 本番環境での障害調査に支障

## Acceptance Criteria
- [ ] `for...else` ブロック内の `raise TransportError(msg)` を削除
- [ ] 常に `raise last_exc` に統一して元の例外チェーンを保持
- [ ] または `raise TransportError(msg) from last_exc` で例外チェーンを明示

## Related Files
- `scripts/shared/http_transport.py`
