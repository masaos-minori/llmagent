# MCPサーバー起動処理 — 起動時のヘルスチェックレート制限なし

**重大度:** MEDIUM
**関連ファイル:** `scripts/agent/http_lifecycle.py:326-364`

## 概要

複数のMCPサーバーが同時に起動する場合、すべてが `/health` エンドポイントを同時に叩く。0.5秒のスリープはあるが、バースト負荷がかかる可能性がある。

## 詳細

```python
while time.monotonic() < deadline:
    ...
    resp = await client.get(health_url)
    ...
await asyncio.sleep(0.5)
```

全サーバーが同じタイミングで起動するため、 `/health` エンドポイントにバーストがかかる。

## 影響

- 健康エンドポイントの一時的な過負荷
- サーバーの再起動ループの誘発

## 修正案

1. サーバーごとに起動タイミングを staggering する
2. レートリミッターを実装する

## 関連ファイル

- `scripts/agent/http_lifecycle.py:326-364`
