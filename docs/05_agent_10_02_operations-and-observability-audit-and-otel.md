---
title: "Agent Operations and Observability - Audit Log and OTel"
category: agent
tags:
  - agent
  - operations
  - audit-log
  - otel
  - observability
related:
  - 05_agent_00_document-guide.md
  - 05_agent_10_01_operations-and-observability-startup-and-health.md
  - 05_agent_10_03_operations-and-observability-workflow-observability.md
  - 05_agent_10_04_operations-and-observability-validation-and-troubleshooting-part1.md
  - 05_agent_10_05_operations-and-observability-monitoring.md
  - 05_agent_10_06_operations-and-observability-rag-diagnostics-and-memory.md
source:
  - 05_agent_10_01_operations-and-observability-startup-and-health.md
---

# エージェントの運用と可観測性

- 設定 → [05_agent_08_04_configuration-mcp-approval-obs.md](05_agent_08_04_configuration-mcp-approval-obs.md)

## Health Probes(ヘルスプローブ)

`agent/repl_health.py` の `check_readiness()` は、起動時に必須サービスをプローブする:

| Service | Probe |
|---|---|
| LLMエンドポイント | `GET {llm_url}/health` |
| Embedエンドポイント | `GET {embed_url}/health` |

**起動時のレディネスポリシー:**

| Mode | Behavior |
|---|---|
| `security_profile = "local"`(デフォルト) | 警告のみ — LLM/Embedに到達できなくてもREPLは継続する |
| `security_profile = "production"` | Fail-fast — 到達不能なサービスをすべて列挙した `RuntimeError` を発生させ、REPLは起動しない |

エラーメッセージの形式: `Startup readiness check failed (required services unavailable): <label>: <detail>; ...`

**戻り値の型:** `ServiceWarning` の `warnings`/`errors` リストを持つ `HealthCheckResult`。`has_issues` プロパティは、いずれかのリストが空でない場合に `True` を返す。`warning_messages()` / `error_messages()` はフラットな文字列リストを返す。

`/mcp` コマンドは、すべてのMCP HTTPサーバの `/health` エンドポイントをプローブする(タイムアウト5秒)。`probe_mcp_health()` を通じて `bool` を返すか、構造化された `McpHealthProbeResult` を返す。

### Shared health models (`agent/shared/health_models.py`)(共有ヘルスモデル)

| Class | Fields |
|---|---|
| `ServiceWarning` | `label: str`, `url: str`, `message: str` — frozen dataclass |
| `HealthCheckResult` | `warnings: list[ServiceWarning]`, `errors: list[ServiceWarning]`; `has_issues` (property), `warning_messages()`, `error_messages()` — frozen dataclass |
| `McpHealthProbeResult` | `reachable: bool`, `status_code: int \| None`, `restart_recommended: bool`, `operator_action_required: bool`, `body: dict[str, object]` — frozen dataclass; body is empty dict if parse failed or unreachable |
| `StartupCheckStatus` | `StrEnum`: `OK`, `WARNING`, `FATAL`, `SKIPPED` |
| `StartupCheckOutcome` | `source: str`, `status: StartupCheckStatus`, `message: str`, `remediation: str` — frozen dataclass |
| `StartupValidationResult` | mutable; `add_fatal/add_warning/add_ok/add_skipped()`, `has_fatal` (property), `fatal_messages()`, `warning_messages()` — collects all startup check outcomes before raising |

---

## Audit Log(監査ログ)

形式: `cfg.obs.audit_log_file`(デフォルト `/opt/llm/logs/audit.log`)にJSON-lines形式で出力

各ターンごとに2つのイベントが生成される:

**`turn_start` イベント:**
```json
{
  "event": "turn_start",
  "task_id": "<uuid4>",
  "worker_id": "<session_id>",
  "event_id": "<uuid4>",
  "ts": 1718600000.123
}
```

**`turn_end` イベント:**
```json
{
  "event": "turn_end",
  "task_id": "<uuid4>",
  "elapsed_ms": 1234.5,
  "input_tokens": 512,
  "output_tokens": 128,
  "parse_error_count": 0,
  "heartbeat_timeout_count": 0,
  "reconnect_count": 0,
  "partial_completion": false,
  "error_kind": null
}
```

### Reading audit logs(監査ログの読み方)

```bash
# Tail all events
tail -f /opt/llm/logs/audit.log | jq .

# Filter turn_end events for elapsed time
tail -f /opt/llm/logs/audit.log | jq 'select(.event == "turn_end") | {turn_id: .task_id, elapsed_ms}'

# Filter token counts
tail -f /opt/llm/logs/audit.log \
  | jq 'select(.input_tokens != null) | {input: .input_tokens, output: .output_tokens}'
```

REPL経由: `/audit [tail N | turn <id> | tool <name>]`

### Audit event DTOs (`agent/shared/models.py`)(監査イベントDTO)

ワークフロー固有のログエントリには、3つの構造化された監査イベントデータクラスが使用される。すべて不変(frozen)データクラスであり、`ts: float` タイムスタンプと、任意の `workflow_id: str = ""`、`session_id: str = ""` フィールドを持つ。

| Class | Required fields |
|---|---|
| `ToolApprovalEvent` | `event: Literal["tool_approval"]`, `task_id: str`, `tool: str`, `operation_type: str`, `resource_scope: dict[str, str]`, `risk: str`, `decision: str`, `args_preview: dict[str, object]` |
| `ApprovalDecisionEvent` | `event: Literal["approval_decision"]`, `task_id: str`, `tool: str`, `risk_level: str`, `decision: str`, `escalation_reason: str` |
| `ToolExecEvent` | `event: Literal["tool_exec"]`, `task_id: str`, `tool: str`, `operation_type: str`, `resource_scope: dict[str, str]`, `mcp_request_id: str`, `is_error: bool`, `args_preview: dict[str, object]` |

| Class | Optional fields |
|---|---|
| `ToolApprovalEvent` | `workflow_id: str = ""`, `session_id: str = ""` |
| `ApprovalDecisionEvent` | `workflow_id: str = ""`, `session_id: str = ""` |
| `ToolExecEvent` | `source: str = "agent"` (tool source: `"agent"` for MCP tools, `"plugin"` for plugin tools), `error_type: str = ""`, `workflow_id: str = ""`, `session_id: str = ""`, `artifact_uri: str \| None = None` |

### Audit writers (`agent/tool_audit.py`)(監査ライター)

| Function | Responsibility |
|---|---|
| `log_approval_decision(ctx, outcome)` | 構造化されたapproval_decisionイベントを監査ログに書き込む |
| `write_round_exec(ctx, round_id, tool_count, mode, has_side_effect, trigger_tool, elapsed_ms, affected_tools, serial_reason, estimated_parallel_ms, scheduling_mode)` | ラウンド全体の実行イベントを記録し、直列化による影響を捕捉する |
| `audit_tool_exec(ctx, tool_name, args, is_error, mcp_request_id, error_type, artifact_uri=None, source="")` | tool_execイベントを監査ログに書き込む。プラグインツールは `source="plugin"` を渡すことで、リクエストIDがないイベントを抑制する `mcp_request_id` ガードを回避する。 |

### Plugin tool audit events(プラグインツールの監査イベント)

プラグインツールは、`source="plugin"`、`mcp_request_id=""`、空の `server_key` を伴う `tool_exec` イベントを発行する。MCPツールのイベントとは異なり、プラグインイベントはHTTP転送層を経由しないため `X-Request-Id` による関連付けを持たない。これは、プラグインツールの監査イベントがMCPサーバのアクセスログと関連付けできないことを意味する。

プラグインツールの監査イベントの例:
```json
{"event":"tool_exec","task_id":"...","tool":"my_plugin_tool","operation_type":"","resource_scope":{},"mcp_request_id":"","is_error":false,"args_preview":{},"ts":1718600000.1,"source":"plugin","error_type":"","workflow_id":"","session_id":""}
```

---

## Related Documents

- `05_agent_00_document-guide.md`
- `05_agent_10_01_operations-and-observability-startup-and-health.md`
- `05_agent_10_03_operations-and-observability-workflow-observability.md`
- `05_agent_10_04_operations-and-observability-validation-and-troubleshooting-part1.md`
- `05_agent_10_05_operations-and-observability-monitoring.md`
- `05_agent_10_06_operations-and-observability-rag-diagnostics-and-memory.md`

## Keywords

audit log
reading audit logs
audit event dtos
audit writers
OpenTelemetry
