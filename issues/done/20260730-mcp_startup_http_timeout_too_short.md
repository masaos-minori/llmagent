# MCPサーバー起動処理 — HTTPクライアントのタイムアウト短すぎ

**重大度:** MEDIUM
**関連ファイル:** `scripts/agent/http_lifecycle.py:329`

## 概要

ヘルスチェック用のHTTPクライアントは5秒のタイムアウトを持つが、`cfg.startup_timeout_sec` がそれより長い場合（例：30秒）、サーバーが正常に起動してもタイムアウトで失敗する可能性がある。

## 詳細

```python
async with httpx.AsyncClient(timeout=httpx.Timeout(timeout=5.0)) as client:
```

サーバーが6秒以上応答する必要がある場合、5秒のタイムアウトで失敗する。これはサーバーの正常な起動状態に対する誤検知。

## 影響

- 正常なサーバーの誤った起動失敗
- 不要な再起動の試行

## 修正案

1. `cfg.startup_timeout_sec` を基準にヘルスチェックのタイムアウトを動的に設定
2. または、ヘルスチェックのタイムアウトをより長くする（例：10秒）

## 関連ファイル

- `scripts/agent/http_lifecycle.py:329`
