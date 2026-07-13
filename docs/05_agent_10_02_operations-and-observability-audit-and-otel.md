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
| `audit_tool_exec(ctx, tool_name, args, is_error, mcp_request_id, error_type, artifact_uri=None, source="")` | tool_execイベントを監査ログに書き込む。ガード条件は `if not mcp_request_id and not source: return`(`mcp_request_id` と `source` が両方とも空の場合のみ書き込みをスキップする)。プラグインツールは `source="plugin"` を渡すことでこのガードを回避する。根拠: `agent/tool_audit.py` の `audit_tool_exec()`(Explicit in code) |

### Plugin tool audit events(プラグインツールの監査イベント)

プラグインツールは、`source="plugin"`、`mcp_request_id=""`、空の `server_key` を伴う `tool_exec` イベントを発行する。MCPツールのイベントとは異なり、プラグインイベントはHTTP転送層を経由しないため `X-Request-Id` による関連付けを持たない。これは、プラグインツールの監査イベントがMCPサーバのアクセスログと関連付けできないことを意味する。

プラグインツールの監査イベントの例:
```json
{"event":"tool_exec","task_id":"...","tool":"my_plugin_tool","operation_type":"","resource_scope":{},"mcp_request_id":"","is_error":false,"args_preview":{},"ts":1718600000.1,"source":"plugin","error_type":"","workflow_id":"","session_id":""}
```

---

## OTel Tracing(OTelトレーシング)

### 設定

| 設定キー(`cfg.obs.*`) | デフォルト | 説明 |
|---|---|---|
| `otel_enabled` | `False` | `True` の場合のみ実トレーサーを構築。`False` ならNoOpトレーサーを使用する |
| `otel_endpoint` | `""`(空文字) | OTLPエクスポータのエンドポイントURL。空の場合はConsoleSpanExporterにフォールバック |
| `otel_service_name` | `"llm-agent"` | `Resource` に設定する `service.name` |

根拠: `agent/config_dataclasses.py`(`otel_enabled`/`otel_endpoint`/`otel_service_name` フィールド定義)、`agent/config_builders.py`(TOML→dataclass変換)(Explicit in code)。

### 初期化フロー

`agent/factory.py` の `init_tracer(ctx)` が `shared/otel_tracer.py` の `build_tracer(enabled, service_name, otlp_endpoint)` を呼び出す。

- `enabled=False` の場合、SDKをインポートせずに `otel_noop.NoOpTracer` を返す(`opentelemetry-sdk` が未インストールの環境でも動作する設計)。
- `enabled=True` かつ `opentelemetry-sdk` が未インストールの場合、警告ログを出して `NoOpTracer` にフォールバックする。
- `enabled=True` かつSDK利用可能な場合、`TracerProvider` を新規構築して返す。`trace.set_tracer_provider()`(グローバル登録)は**呼ばない**設計(コード内コメント "Design (R10)" 参照)。テスト間のプロバイダ汚染防止と、プロセス内での複数トレーサーインスタンス共存を意図している。
- エクスポータは `otlp_endpoint` が空なら `ConsoleSpanExporter`、指定があれば `OTLPSpanExporter`(`opentelemetry-exporter-otlp` 未インストール時は警告を出してConsoleSpanExporterにフォールバック)。

根拠: `shared/otel_tracer.py` の `build_tracer()`/`_attach_exporter()`/docstring(Explicit in code)。

### Why this exists / What this component intentionally does NOT do

- OTel SDKは任意依存(optional dependency)として扱われ、未インストール環境でもエージェントが起動できるよう、NoOp実装(`shared/otel_noop.py` の `NoOpTracer`/`NoOpSpan`)へ常にフォールバックする。根拠: `otel_tracer.py` モジュールdocstring(Explicit in code)。
- グローバルな `TracerProvider` を意図的に設定しない(プライベートインスタンスとして保持)。他プロセス/他テストのトレーサー状態に影響を与えない境界を意図している。根拠: `build_tracer()` docstring "Design (R10)"(Explicit in code)。

### スパン生成箇所

`agent/llm_turn_runner.py` はターン処理中に `self._tracer.start_as_current_span(name, attributes=attrs or None)` でスパンを生成する。`_tracer` が `None`(未初期化)の場合は `nullcontext(_NoOpSpan())` を返す。付与されるカスタム属性(いずれも該当値が非空の場合のみ設定):

| 属性キー | 内容 |
|---|---|
| `workflow.task_id` | ターンのタスクID |
| `workflow.session_id` | セッションID |
| `llm.model_url` | LLMエンドポイントURL |
| `workflow.workflow_id` | ワークフローID |
| `workflow.stage_id` | ステージID |
| `workflow.attempt_id` | 試行ID |

根拠: `agent/llm_turn_runner.py`(Explicit in code)。

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
otel tracer
otel_enabled
otlp exporter
noop tracer
tracer provider
