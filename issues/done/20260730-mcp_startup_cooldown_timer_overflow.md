# MCPサーバー起動処理 — クールダウンタイマーの理論的限界

**重大度:** LOW
**関連ファイル:** `scripts/agent/factory.py:97-112`

## 概要

`_failed_starts` に格納される `time.monotonic()` の値は、長時間稼働するプロセスで理論的にオーバーフローする可能性がある。ただし、64ビットシステムでは現実的な時間枠内では問題ない。

## 詳細

```python
def _in_cooldown(self, server_key: str) -> bool:
    last_failure = self._failed_starts.get(server_key, 0)
    if last_failure == 0:
        return False
    elapsed = time.monotonic() - last_failure
```

`time.monotonic()` は64ビットシステムでは約584年分の値を取れるため、実用上の問題はない。

## 影響

- 理論上のみの問題
- 64ビットシステムでは現実的な時間枠内では発生しない

## 修正案

- 現在のところ不要。必要に応じて `time.monotonic_ns()` への移行を検討

## 関連ファイル

- `scripts/agent/factory.py:97-112`
