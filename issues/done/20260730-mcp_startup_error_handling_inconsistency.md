# MCPサーバー起動処理 — `_start_servers` と `_verify_mcp_health` のエラーハンドリング不整合

**重大度:** LOW
**関連ファイル:** `scripts/agent/startup.py:143-169`; `scripts/agent/startup.py:171-217`

## 概要

`_start_servers()` ではヘルスチェック失敗時に再試行がないが、`_verify_mcp_health()` では1回だけ再試行する。一貫性がない。

## 詳細

`_start_servers()`:
```python
try:
    async with httpx.AsyncClient(timeout=5.0) as client:
        resp = await client.get(url)
        if resp.status_code != httpx.codes.OK:
            raise RuntimeError(f"HTTP {resp.status_code}")
```

`_verify_mcp_health()`:
```python
try:
    async with httpx.AsyncClient(timeout=5.0) as client:
        resp = await client.get(url)
        ...
except Exception:
    try:
        await asyncio.sleep(1.0)
        async with httpx.AsyncClient(timeout=5.0) as client:
            resp = await client.get(url)
            ...
```

起動中は即座に失敗するが、起動後の検証では猶予がある。

## 影響

- 一時的なネットワーク障害に対する扱いの違い
- 開発環境と本番環境での挙動の違い

## 修正案

1. 両方のメソッドで一貫した再試行ポリシーを適用
2. または、起動中は厳格に、起動後は寛容に、という意図をドキュメント化する

## 関連ファイル

- `scripts/agent/startup.py:143-169`
- `scripts/agent/startup.py:171-217`
