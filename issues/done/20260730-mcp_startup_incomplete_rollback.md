# MCPサーバー起動処理 — シャットダウンロールバックの不備

**重大度:** MEDIUM
**関連ファイル:** `scripts/agent/startup.py:75-85`

## 概要

`_start_servers()` が成功したが、その後の `_verify_mcp_health()` や `_check_services()` で失敗した場合、`shutdown_all()` のみが呼ばれる。stdioモードのMCPサーバーは追跡されていないため、ゾンビ化する可能性がある。

## 詳細

```python
except Exception as setup_err:
    if _servers_started:
        try:
            await self._ctx.services_required.lifecycle.shutdown_all()
```

`shutdown_all()` はHTTPサブプロセスのみをシャットダウンする。stdioモードのMCPサーバーは別の経路で開始される可能性があるが、このロールバックでは追跡されない。

## 影響

- stdioモードMCPサーバーのゾンビ化
- リソースリーク

## 修正案

1. 開始したすべてのサーバー（stdio含む）を追跡するリストを持つ
2. ロールバック時にすべてのサーバーをシャットダウンする

## 関連ファイル

- `scripts/agent/startup.py:75-85`
