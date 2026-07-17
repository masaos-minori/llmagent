---
title: "End-to-End Tool Call Tracing"
category: mcp
tags:
  - mcp
  - configuration
related:
  - 04_mcp_00_document-guide.md
  - 04_mcp_06_02_configuration-file-inventory.md
source:
  - 04_mcp_06_02_configuration-file-inventory.md
---

# End-to-End Tool Call Tracing

## End-to-End Tool Call Tracing

失敗したtool callをagent、transport、サーバのログを通じて追跡する手順:

1. agent側のaudit logで `mcp_request_id` を見つける:
    ```bash
    jq 'select(.mcp_request_id == "<id>")' /opt/llm/logs/audit.log
    ```
2. MCPサーバのaudit logで同じ `request_id` フィールドを検索する（JSON-lines形式）:
    ```bash
    jq 'select(.request_id == "<id>")' /opt/llm/logs/audit.log
    ```
3. サーバ別ログで `X-Request-Id` レスポンスヘッダを検索する:
    ```bash
    grep "<id>" /opt/llm/logs/github-mcp.log  # or relevant server log
    ```
4. `/opt/llm/logs/agent.log` で、その時刻の `server_key` のヘルス状態を確認する。
5. ヘルス状態が変化していた場合: `/mcp status` で現在の DEGRADED/UNAVAILABLE 状態と `health_reason` を確認する。自動的な再起動は行われない(subprocessモードのサーバーは次回のtool dispatch時に`ensure_ready()`が再起動を試みるのみ)。

---

### Audit Log内のエラー種別の区別（Agent側）

**クロスレイヤー相関について:** per-server audit logs（github_audit.log, shell_audit.log, delete_audit.log）は X-Session-Id や X-Request-Id のような相関フィールドを持たない。これらのログ間の相関はエージェント側の audit ログを基準として使用する必要がある。

agent側のaudit eventには `error_type` フィールドが含まれる:

| error_type | 意味 | 発生原因の例 |
|---|---|---|
| `transport` | MCPサーバに到達不能（ネットワーク障害、タイムアウト、クラッシュ） | サーバプロセスの停止、ポートがリスニングしていない、HTTP 5xx |
| `tool` | MCPサーバには到達可能だがtoolがis_error=trueを返した | tool検証失敗、database制約違反 |
| _(空)_ | 実行成功 | — |

audit logの行の例:
```json
{"event":"tool_exec","tool":"shell_run","is_error":true,"error_type":"transport",...}
```

エラー種別でフィルタする:
```bash
# Transport failures (server issues)
grep '"error_type":"transport"' /opt/llm/logs/audit.log

# Tool-level failures (business logic errors)
grep '"error_type":"tool"' /opt/llm/logs/audit.log
```

### サーバごとのエラーカウンタ

`ToolExecutor` はサーバごとのエラーカウンタを保持し、`ToolExecutor.get_error_counters()` から参照できる:

```python
{
    "shell-mcp": {"transport": 2, "tool": 5},
    "github-mcp": {"transport": 0, "tool": 1},
}
```

これらのカウンタはメモリ上のみに保持され（永続化されない）、agent再起動時にリセットされる。

### 繰り返し失敗の検出

toolが5分間のスライディングウィンドウ内で3回以上失敗すると、警告がログに出力される:

```
WARNING: Repeated tool failures detected: shell_run failed 3 times in 300s window
```

> **注記:** `McpServerHealthRegistry`（`shared/mcp_health.py`）はtransportの可用性のみを追跡する。tool層のエラー（`error_type=tool`）はHealthRegistryの状態に影響しない — サーバのヘルス状態に影響するのはtransport障害（`error_type=transport`）のみである。

---

### 副作用の直列化

ラウンドに副作用を持つtool（書き込み操作）が含まれる場合、スケジューラはそれらをグループ化して並行的な変更を防ぐ。これは安全性のために意図された挙動であるが、並列度は低下する。

**直列化のトリガー:**

| トリガー | 条件 | 効果 |
|---|---|---|
| `requires_serial` | toolのメタデータに `requires_serial=true` が設定されている | そのtoolは単独で1要素だけのグループとして実行される |
| `resource_scope_conflict` | 同じリソーススコープへの複数の書き込み | そのスコープ内のすべてのtoolが直列実行される |
| `is_write_overlap` | 特定のスコープを持たない複数の書き込み | 書き込み系toolがすべてまとめてグループ化される（write-first） |

**ログ形式:**
```
ROUND_SERIALIZATION: triggered by shell_run (requires_serial) — 1 tools serialized in this round
Serialization impact: 3 tools grouped serially (normally would run in parallel)
```

**統計の確認方法:**
`/mcp` を実行すると、MCPステータス出力の末尾に直列化に関する統計が表示される。

**この情報が重要な理由:**
直列化は並列度を下げるが、共有リソース上での競合状態を防ぐ。並列度の最適化を試みる前に、直列化ログを確認し、どのtoolとスコープが最も頻繁にグループ化を引き起こしているかを把握すること。

---


## Related Documents

- [04_mcp_06_02_configuration-file-inventory.md](04_mcp_06_02_configuration-file-inventory.md)

## Keywords

configuration
