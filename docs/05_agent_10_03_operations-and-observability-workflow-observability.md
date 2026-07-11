---
title: "Agent Operations and Observability - Workflow Observability"
category: agent
tags:
  - agent
  - operations
  - workflow
  - otel-spans
  - session-diagnostics
related:
  - 05_agent_00_document-guide.md
  - 05_agent_10_01_operations-and-observability-startup-and-health.md
  - 05_agent_10_02_operations-and-observability-audit-and-otel.md
  - 05_agent_10_04_operations-and-observability-validation-and-troubleshooting.md
  - 05_agent_10_05_operations-and-observability-monitoring.md
  - 05_agent_10_06_operations-and-observability-rag-diagnostics-and-memory.md
source:
  - 05_agent_10_01_operations-and-observability-startup-and-health.md
---

# エージェントの運用と可観測性

- 設定 → [05_agent_08_04_configuration-mcp-approval-obs.md](05_agent_08_04_configuration-mcp-approval-obs.md)

## OpenTelemetry (OTel)

`config/agent.toml` で設定する:

```toml
otel_enabled = true
otel_endpoint = ""          # "" = ConsoleSpanExporter (logs to agent.log)
otel_service_name = "llm-agent"
```

`otel_endpoint = ""` の場合: スパンは標準出力 / `agent.log` に書き込まれる。

```bash
# Extract span names from agent.log
tail -f /opt/llm/logs/agent.log | grep '"name":'
```

期待されるスパン:
```json
{"name": "compress", ...}
{"name": "llm", "attributes": {"model_url": "http://127.0.0.1:8001/..."}, ...}
{"name": "workflow.run", "attributes": {"workflow.task_id": "...", "workflow.version": "1.0"}, ...}
{"name": "workflow.stage", "attributes": {"workflow.stage_id": "execute", "workflow.attempt": 1}, ...}
```

---

## Workflow Observability(ワークフローの可観測性)

### OTel Spans(OTelスパン)

`WorkflowEngine` は、トレーサーが設定されている場合に4種類のスパンを発行する:

| Span name | 発行元 | Attributes |
|---|---|---|
| `workflow.run` | `WorkflowEngine.run()` | `workflow.task_id`, `workflow.version`, `workflow.workflow_id`, `workflow.session_id` |

トレーサーは `Orchestrator` → `WorkflowEngine` へと伝播するため、すべてのワークフロースパンは、それを包含する `llm` スパンと同じトレースコンテキストを共有する。

### Workflow Identifiers(ワークフロー識別子)

ワークフローモードの各ターンでは、既存の `task_id` に加えて一意の `workflow_id`(UUID4)が生成される。両IDは以下を通じて伝播する:
- OTelスパン属性
- すべての監査ログイベント(`workflow_start`、`stage_completed`、`approval_requested`)
- `ToolApprovalEvent`、`ApprovalDecisionEvent`、`ToolExecEvent` のDTO
- `turn_end` 監査イベント
- `AgentContext` 内の `WorkflowState`(`ctx.workflow.workflow_id`)
- `workflow.sqlite` の `tasks` テーブル

### Audit Events(監査イベント)

3つのワークフロー固有イベントが、ターンごとに `audit.log` に追記される:

**`workflow_start` イベント**(タスク作成時に発行):
```json
{"event": "workflow_start", "task_id": "...", "workflow_id": "...", "session_id": "...", "workflow_version": "1.0", "ts": 1718600000.1}
```

**`stage_completed` イベント**(executeステージ完了後に発行):
```json
{"event": "stage_completed", "task_id": "...", "workflow_id": "...", "session_id": "...", "stage_id": "execute", "elapsed_ms": 1234.5, "ts": 1718600001.4}
```

**`approval_requested` イベント**(人間の承認が必要な場合に発行):
```json
{"event": "approval_requested", "task_id": "...", "workflow_id": "...", "session_id": "...", "approval_id": "...", "ts": 1718600001.5}
```

**`turn_end` イベント**(ワークフローコンテキストを含むよう更新):
```json
{"event": "turn_end", "task_id": "...", "workflow_id": "...", "session_id": "...", "elapsed_ms": 1234.5, ...}
```

### Reading workflow audit events(ワークフロー監査イベントの読み方)

```bash
# All workflow events
grep -E '"workflow_start"|"stage_completed"|"approval_requested"' /opt/llm/logs/audit.log | jq .

# Execute stage latency grouped by workflow_id
grep '"stage_completed"' /opt/llm/logs/audit.log | jq '{workflow_id, task_id, stage_id, elapsed_ms}'

# Pending approvals with workflow context
grep '"approval_requested"' /opt/llm/logs/audit.log | jq '{workflow_id, task_id, approval_id}'

# All events for a specific workflow_id
grep '"workflow_id":"<id>"' /opt/llm/logs/audit.log | jq .
```

### Session Diagnostics(セッション診断)

診断情報は `DiagnosticStore.save()` を通じて `session_diagnostics` テーブルに永続化される。セッション概要はセッション終了時に書き込まれる:

```json
{
  "session_id": "...",
  "turns": 5,
  "workflow_count": 3,
  "task_count": 3,
  "approval_events": 1,
  "retry_count": 2,
  "artifacts": ["path/to/artifact"],
  ...
}
```

これらの件数は、セッション終了時に `workflow.sqlite` から導出される。

セッション診断のクエリ:

```bash
sqlite3 /opt/llm/db/session.sqlite "SELECT kind, json(content) FROM session_diagnostics WHERE session_id = ? ORDER BY created_at DESC LIMIT 10;"
```

特定の診断エントリの取得:

```bash
sqlite3 /opt/llm/db/session.sqlite "SELECT kind, content FROM session_diagnostics WHERE session_id = ? AND kind = 'session_summary' ORDER BY created_at DESC LIMIT 1;" | jq .content
```

あるセッションの全診断種別の一覧表示:

```bash
sqlite3 /opt/llm/db/session.sqlite "SELECT DISTINCT kind FROM session_diagnostics WHERE session_id = ? ORDER BY kind;"
```

---

## Related Documents

- `05_agent_00_document-guide.md`
- `05_agent_10_01_operations-and-observability-startup-and-health.md`
- `05_agent_10_02_operations-and-observability-audit-and-otel.md`
- `05_agent_10_04_operations-and-observability-validation-and-troubleshooting.md`
- `05_agent_10_05_operations-and-observability-monitoring.md`
- `05_agent_10_06_operations-and-observability-rag-diagnostics-and-memory.md`

## Keywords

OTel spans
workflow identifiers
audit events
session diagnostics
