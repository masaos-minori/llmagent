---
title: "Agent Operations and Observability"
category: agent
tags:
  - agent
  - agent
  - operations
  - observability
  - monitoring
related:
  - 05_agent_00_document-guide.md
---

# Agent Operations and Observability

 `config/agent.toml`:

```toml
otel_enabled = true
otel_endpoint = ""          # "" = ConsoleSpanExporter (logs to agent.log)
otel_service_name = "llm-agent"
```

With `otel_endpoint = ""`: spans written to stdout / `agent.log`.

```bash
# Extract span names from agent.log
tail -f /opt/llm/logs/agent.log | grep '"name":'
```

Expected spans:
```json
{"name": "compress", ...}
{"name": "llm", "attributes": {"model_url": "http://127.0.0.1:8001/..."}, ...}
{"name": "workflow.run", "attributes": {"workflow.task_id": "...", "workflow.version": "1.0"}, ...}
{"name": "workflow.stage", "attributes": {"workflow.stage_id": "execute", "workflow.attempt": 1}, ...}
```

---

## Workflow Observability

### OTel S

pans

`WorkflowEngine` emits four span types when a tracer is configured:

| Span name | Emitted by | Attributes |
|---|---|---|
| `workflow.run` | `WorkflowEngine.run()` | `workflow.task_id`, `workflow.version`, `workflow.workflow_id`, `workflow.session_id` |

The tracer is propagated from `Orchestrator` → `WorkflowEngine` so all workflow spans share the same trace context as the enclosing `llm` span.

### Workflow Identifiers

Each turn in workflow mode generates a unique `workflow_id` (UUID4) in addition to the existing `task_id`. Both IDs propagate through:
- OTel span attributes
- All audit log events (`workflow_start`, `stage_completed`, `approval_requested`)
- `ToolApprovalEvent`, `ApprovalDecisionEvent`, `ToolExecEvent` DTOs
- `turn_end` audit event
- `WorkflowState` in `AgentContext` (`ctx.workflow.workflow_id`)
- `tasks` table in `workflow.sqlite`

### Audit Events

Three workflow-specific events are appended to `audit.log` per turn:

**`workflow_start` event** (emitted when a task is created):
```json
{"event": "workflow_start", "task_id": "...", "workflow_id": "...", "session_id": "...", "workflow_version": "1.0", "ts": 1718600000.1}
```

**`stage_completed` event** (emitted after the execute stage):
```json
{"event": "stage_completed", "task_id": "...", "workflow_id": "...", "session_id": "...", "stage_id": "execute", "elapsed_ms": 1234.5, "ts": 1718600001.4}
```

**`approval_requested` event** (emitted when human approval is required):
```json
{"event": "approval_requested", "task_id": "...", "workflow_id": "...", "session_id": "...", "approval_id": "...", "ts": 1718600001.5}
```

**`turn_end` event** (updated to include workflow context):
```json
{"event": "turn_end", "task_id": "...", "workflow_id": "...", "session_id": "...", "elapsed_ms": 1234.5, ...}
```

### Reading workflow audit events

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

### Session Diagnostics

Diagnostics are persisted in the `session_diagnostics` table via `DiagnosticStore.save()`. The session summary is written at session end:

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

These counts are derived from `workflow.sqlite` at session end.

Querying session diagnostics:

```bash
sqlite3 /opt/llm/db/session.sqlite "SELECT kind, json(content) FROM session_diagnostics WHERE session_id = ? ORDER BY created_at DESC LIMIT 10;"
```

Retrieving a specific diagnostic entry:

```bash
sqlite3 /opt/llm/db/session.sqlite "SELECT kind, content FROM session_diagnostics WHERE session_id = ? AND kind = 'session_summary' ORDER BY created_at DESC LIMIT 1;" | jq .content
```

Listing all diagnostic kinds for a session:

```bash
sqlite3 /opt/llm/db/session.sqlite "SELECT DISTINCT kind FROM session_diagnostics WHERE session_id = ? ORDER BY kind;"
```

---

## Workflow Startup Validation

The a

gent unconditionally validates that a workflow definition file exists before
initializing the orchestrator — there is no config setting to disable or degrade this
(verified 2026-07-09: `workflow_mode` is not a valid config key — see
[Configuration: AgentConfig Structure](05_agent_08_configuration.md#agentconfig-structure)).
If the file is missing, a `RuntimeError` is raised with actionable guidance.

**Expected path:** `config/workflows/default.json`

**Remediation:** Deploy the workflow definition to the expected path. There is no config
toggle to skip this check — a config file that previously set `workflow_mode = "disabled"`
or `"auto"` will now fail to load entirely (`ConfigLoadError`, since `workflow_mode` is a
rejected key), rather than reaching the workflow check at all.

The preflight check (`StartupOrchestrator._check_workflow_definition()` in
`agent/startup.py`, wrapping `check_workflow_definition()` in `agent/repl_health.py`) runs
before `Orchestrator.__init__()` and produces a clear error message rather than a cryptic
`WorkflowLoadError` that may not include the expected file path. `Orchestrator.__init__()`
itself also unconditionally raises `RuntimeError` if `WorkflowLoader().load()` fails for any
other reason once past the preflight check.

**Note:** This validation always runs once at agent boot — it is not a config setting and
cannot be changed via `/reload`. Any fix requires deploying the workflow definition file and
restarting the agent.

---

## MCP Server Reload and Restart Sema

## Related Documents

- `agent`
- `operations`
- `observability`

## Keywords

agent
operations
observability
monitoring
