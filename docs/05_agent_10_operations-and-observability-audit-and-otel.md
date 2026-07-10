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
  - 05_agent_10_operations-and-observability-startup-and-health.md
  - 05_agent_10_operations-and-observability-workflow-observability.md
  - 05_agent_10_operations-and-observability-validation-and-troubleshooting.md
  - 05_agent_10_operations-and-observability-monitoring.md
  - 05_agent_10_operations-and-observability-rag-diagnostics-and-memory.md
source:
  - 05_agent_10_operations-and-observability-startup-and-health.md
---

# Agent Operations and Observability

- Configuration → [05_agent_08_configuration-mcp-approval-obs.md](05_agent_08_configuration-mcp-approval-obs.md)

## Health Probes

`check_readiness()` in `agent/repl_health.py` probes required services at startup:

| Service | Probe |
|---|---|
| LLM endpoint | `GET {llm_url}/health` |
| Embed endpoint | `GET {embed_url}/health` |

**Startup readiness policy:**

| Mode | Behavior |
|---|---|
| `security_profile = "local"` (default) | Warning only — REPL continues even if LLM/Embed are unreachable |
| `security_profile = "production"` | Fail-fast — raises `RuntimeError` listing all unavailable services; REPL does not start |

Error message format: `Startup readiness check failed (required services unavailable): <label>: <detail>; ...`

**Return type:** `HealthCheckResult` with `warnings`/`errors` lists of `ServiceWarning`. The `has_issues` property returns `True` if either list is non-empty. `warning_messages()` / `error_messages()` return flat string lists.

`/mcp` command probes all MCP HTTP servers at `/health` endpoint (5 second timeout). Returns `bool` via `probe_mcp_health()`, or structured `McpHealthProbeResult`.

### Shared health models (`agent/shared/health_models.py`)

| Class | Fields |
|---|---|
| `ServiceWarning` | `label: str`, `url: str`, `message: str` — frozen dataclass |
| `HealthCheckResult` | `warnings: list[ServiceWarning]`, `errors: list[ServiceWarning]`; `has_issues` (property), `warning_messages()`, `error_messages()` — frozen dataclass |
| `McpHealthProbeResult` | `reachable: bool`, `status_code: int \| None`, `restart_recommended: bool`, `operator_action_required: bool`, `body: dict[str, object]` — frozen dataclass; body is empty dict if parse failed or unreachable |
| `StartupCheckStatus` | `StrEnum`: `OK`, `WARNING`, `FATAL`, `SKIPPED` |
| `StartupCheckOutcome` | `source: str`, `status: StartupCheckStatus`, `message: str`, `remediation: str` — frozen dataclass |
| `StartupValidationResult` | mutable; `add_fatal/add_warning/add_ok/add_skipped()`, `has_fatal` (property), `fatal_messages()`, `warning_messages()` — collects all startup check outcomes before raising |

---

## Audit Log

Format: JSON-lines at `cfg.obs.audit_log_file` (default `/opt/llm/logs/audit.log`)

Each turn produces two events:

**`turn_start` event:**
```json
{
  "event": "turn_start",
  "task_id": "<uuid4>",
  "worker_id": "<session_id>",
  "event_id": "<uuid4>",
  "ts": 1718600000.123
}
```

**`turn_end` event:**
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

### Reading audit logs

```bash
# Tail all events
tail -f /opt/llm/logs/audit.log | jq .

# Filter turn_end events for elapsed time
tail -f /opt/llm/logs/audit.log | jq 'select(.event == "turn_end") | {turn_id: .task_id, elapsed_ms}'

# Filter token counts
tail -f /opt/llm/logs/audit.log \
  | jq 'select(.input_tokens != null) | {input: .input_tokens, output: .output_tokens}'
```

Via REPL: `/audit [tail N | turn <id> | tool <name>]`

### Audit event DTOs (`agent/shared/models.py`)

Three structured audit event dataclasses are used for workflow-specific log entries. All are frozen dataclasses with `ts: float` timestamps and optional `workflow_id: str = ""`, `session_id: str = ""` fields.

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

### Audit writers (`agent/tool_audit.py`)

| Function | Responsibility |
|---|---|
| `log_approval_decision(ctx, outcome)` | Write a structured approval_decision event to the audit log |
| `write_round_exec(ctx, round_id, tool_count, mode, has_side_effect, trigger_tool, elapsed_ms, affected_tools, serial_reason, estimated_parallel_ms, scheduling_mode)` | Log a round-wide execution event, capturing serialization impact |
| `audit_tool_exec(ctx, tool_name, args, is_error, mcp_request_id, error_type, artifact_uri=None, source="")` | Write a tool_exec event to the audit log. Plugin tools pass `source="plugin"` which bypasses the `mcp_request_id` guard that suppresses events without a request ID. |

### Plugin tool audit events

Plugin tools emit `tool_exec` events with `source="plugin"`, `mcp_request_id=""`, and empty `server_key`. Unlike MCP tool events, plugin events lack an `X-Request-Id` correlation because they do not go through the HTTP transport layer. This means plugin tool audit events cannot be correlated with MCP server access logs.

Example plugin tool audit event:
```json
{"event":"tool_exec","task_id":"...","tool":"my_plugin_tool","operation_type":"","resource_scope":{},"mcp_request_id":"","is_error":false,"args_preview":{},"ts":1718600000.1,"source":"plugin","error_type":"","workflow_id":"","session_id":""}
```

---

## Related Documents

- `05_agent_00_document-guide.md`
- `05_agent_10_operations-and-observability-startup-and-health.md`
- `05_agent_10_operations-and-observability-workflow-observability.md`
- `05_agent_10_operations-and-observability-validation-and-troubleshooting.md`
- `05_agent_10_operations-and-observability-monitoring.md`
- `05_agent_10_operations-and-observability-rag-diagnostics-and-memory.md`

## Keywords

audit log
reading audit logs
audit event dtos
audit writers
OpenTelemetry
