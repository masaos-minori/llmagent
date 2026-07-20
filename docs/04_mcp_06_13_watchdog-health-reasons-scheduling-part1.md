---
title: "MCP Health Reasons and Scheduling (Part 1)"
category: mcp
tags:
  - mcp
  - health-reasons
related:
  - 04_mcp_00_document-guide.md
  - 04_mcp_06_02_configuration-file-inventory.md
  - 04_mcp_06_12_watchdog-configuration-monitoring.md
source:
  - 04_mcp_06_13_watchdog-health-reasons-scheduling-part1.md
---

# MCP Health Reasons and Scheduling


## ヘルス理由の優先順位

`/health`経由でHTTP MCPサーバーをプローブすると、LIFECYCLEのアクションと表示用の理由の両方を決定する構造化フィールドが返される。

```python
# From McpProbeResult model
restart_recommended: bool       # True if health endpoint says so OR lifecycle_state == FAILED
operator_action_required: bool  # True only if health endpoint sets this flag
health_reason: str              # Derived priority: operator_action > restart_recommended
```

`health_reason`導出の優先順位:

| 条件 | 結果 |
|-----------|--------|
| `operator_action_required=true` かつ reachable+HTTP_OK | `"operator_action_required"` |
| `restart_recommended=true` かつ reachable+HTTP_OK | `"restart_recommended"` |
| サーバーが到達不能/失敗中 | ボディが提供する理由文字列(`details.reason`、なければ`message`にフォールバック) |
| それ以外のすべてのケース | 空文字列 |

`restart_recommended`フィールドには、異なるセマンティクスを持つ2つの発生源がある。

1. **`/health`エンドポイントから**: サーバー自身によるプロアクティブな推奨を示す
2. **LifecycleProtocol.ensure_ready()から**: `lifecycle_state == FAILED`のときに設定される — トランスポート層の障害に基づくリアクティブな検出を示す

両者は表示レベルでは同等に扱われる。

### プローブチェーン全体でのボディ理由の追跡

HTTP MCPサーバーの`/health`をプローブする際、bodyフィールドは次のように伝播する。

```python
# Step 1: Probe returns raw body
probe_result.body["reason"] or probe_result.body["message"]

# Step 2: Resolved to endpoint string  
_resolve_endpoint() returns tuple including body_reason

# Step 3: HealthRegistry receives it via record_failure(record_success())
registry.record_failure(reason=str(body_reason))

# Step 4: Displayed at two levels
# - Per-server degraded reason: registry.get_degraded_reason(key)
# - Global table column: McpProbeResult.health_reason derived below
```

#### degraded の理由一覧

`McpServerHealthRegistry.get_degraded_reason()` が返す値:

| 理由 | 設定元 | 発生条件 |
|------|--------|----------|
| ボディ理由 (`details.reason` / `message`) | `record_failure()` / `record_degraded()` | `/health` レスポンスのボディから抽出 |

- すべての degraded 理由は、`record_success()` によってクリアされる。

---

### Related Documents

- `04_mcp_00_document-guide.md`
- `04_mcp_06_02_configuration-file-inventory.md`
- `04_mcp_06_13_watchdog-health-reasons-scheduling-part2.md`
- `04_mcp_06_12_watchdog-configuration-monitoring.md`

### Keywords

health-reasons
scheduling
