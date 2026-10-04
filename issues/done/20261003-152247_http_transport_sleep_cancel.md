# MEDIUM: HttpTransport リトライ間の asyncio.sleep がキャンセルされない

## Priority
Medium

## Summary
`HttpTransport.call()` でリトライ間に `asyncio.sleep` で待機するが、タスクがキャンセルされた場合、`sleep` が中断されず、キャンセル例外が `sleep` から送出されない。

## Background
`scripts/shared/http_transport.py` line 139-140:
```python
if attempt < self._RETRY_MAX - 1:
    await asyncio.sleep(wait_sec)
```

## Problem
`asyncio.sleep()` はタスクがキャンセルされると `CancelledError` を送出するが、`wait_sec` が長い場合、キャンセルまで長時間待機する必要がある。

## Evidence
- `http_transport.py` line 139-140 のコードフロー
- Python の `asyncio.sleep()` の仕様

## Impact
- タスクキャンセル時にリトライが完了するまでブロックされる
- 長時間の待機後にキャンセル例外が送出されるため、レスポンス性が低下

## Acceptance Criteria
- [ ] `asyncio.wait_for(asyncio.sleep(wait_sec), timeout=...)` または `asyncio.shield()` を使用して、キャンセル時の挙動を制御
- [ ] キャンセル時のタイムアウト値をドキュメントに明記

## Related Files
- `scripts/shared/http_transport.py`
