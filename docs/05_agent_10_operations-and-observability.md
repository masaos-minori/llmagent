# Agent Operations and Observability

- Configuration → [05_agent_08_configuration.md](05_agent_08_configuration.md)

## Purpose

Document startup procedure, operational verification, health checks, audit logging,
OTel tracing, `/context` and `/stats` interpretation, and troubleshooting.

---

## Startup Procedure

```bash
# 1. Deploy files (if changed)
cp -r scripts/agent   /opt/llm/scripts/agent
cp -r scripts/shared  /opt/llm/scripts/shared

# 2. Activate venv
source /opt/llm/venv/bin/activate

# 3. Start agent
cd /opt/llm/scripts && python -m agent
```

Expected startup banner:
```
DB: 12,345 chunks | Tools: 14
Memory: disabled
Type /help for commands, Ctrl-C or Ctrl-D to exit.

agent[:#1]>
```

**Memory line:** Present only when `write_startup_banner()` receives `memory_enabled != None`. Since `repl.py` always passes `ctx.cfg.memory.use_memory_layer`, this line is always shown — `disabled` by default, `enabled` when `use_memory_layer=True`.

---

### Workflow Pending Approval Recovery

When the agent starts and a previous session had an approval gate that was not resolved (i.e., `/approve` or `/reject` was never issued), `startup.py` recovers the pending approval state:

- **When:** During startup, if `ctx.workflow is not None`
- **What is recovered:** The latest global pending approval from `workflow.sqlite` via `StateStore.find_latest_pending_approval()`
- **Multi-session behavior:** Only one pending approval is tracked at a time; the latest record across all sessions is restored (not session-specific)
- **Startup warning format:** `[workflow] Pending approval from previous session — task=<task_id> approval=<approval_id> reason=<reason>. Use /approve [reason] or /reject [reason].`
- **How to inspect:** `sqlite3 /opt/llm/db/workflow.sqlite "SELECT * FROM approvals WHERE status='pending' ORDER BY created_at DESC LIMIT 1;"`

---

## Operational Verification

### LLM service check

```bash
curl -s http://127.0.0.1:8001/v1/chat/completions -d '{"messages":[{"role":"user","content":"hi"}],"max_tokens":5}' -H 'Content-Type: application/json'
```

### Embedding service check

```bash
curl -s http://127.0.0.1:8003/health
```

### MCP server status

```
agent[:#1]> /mcp
```

Expected: all servers listed with `OK` status.

### Minimal Agent DB Initialization

#### When to use

- First-time local development: session.sqlite and workflow.sqlite do not exist yet.
- After wiping either database file: the agent raises `OperationalError: no such table: sessions` on startup if the schema is absent.

#### Initialize session.sqlite

```bash
PYTHONPATH=scripts uv run python - <<PY
from db.create_schema import create_session_schema
create_session_schema()
print("session schema OK")
PY
```

Creates tables: `sessions`, `messages`, `tool_results`, `memories`, `memories_fts`, `memories_vec`, `session_diagnostics`.

#### Initialize workflow.sqlite

Only required when `workflow_db_path` is configured in the agent config.

```bash
PYTHONPATH=scripts uv run python - <<PY
from db.create_schema import create_workflow_schema
create_workflow_schema()
print("workflow schema OK")
PY
```

Creates tables: `tasks`, `attempts`, `processed_events`, `artifacts`, `approvals`.

#### Verify tables

```bash
sqlite3 /opt/llm/db/session.sqlite  ".tables"
# Expected: memories  memories_fts  memories_vec  messages  session_diagnostics  sessions  tool_results

sqlite3 /opt/llm/db/workflow.sqlite ".tables"
# Expected: approvals  artifacts  attempts  processed_events  tasks
```

#### Re-run safety

Both functions use `CREATE TABLE IF NOT EXISTS` — re-running against an existing DB is safe and applies only additive migration patches.

#### Error context

`sqlite3.OperationalError: no such table: sessions` on agent startup means session.sqlite schema has not been initialized. Run the `create_session_schema()` command above.

---

### DB verification

Three platform databases to verify:

```bash
# rag.sqlite — RAG documents, chunks, embeddings
sqlite3 /opt/llm/db/rag.sqlite "SELECT lang, COUNT(*) AS docs FROM documents GROUP BY lang;"
sqlite3 /opt/llm/db/rag.sqlite "SELECT COUNT(*) AS chunks FROM chunks;"
sqlite3 /opt/llm/db/rag.sqlite "SELECT chunk_id, LENGTH(embedding) AS bytes FROM chunks_vec LIMIT 3;"
# Expected bytes: 1536 (384 dimensions × 4 bytes)

# session.sqlite — agent sessions and messages
sqlite3 /opt/llm/db/session.sqlite "SELECT session_id, created_at, title FROM sessions ORDER BY session_id DESC LIMIT 5;"
sqlite3 /opt/llm/db/session.sqlite "SELECT COUNT(*) AS messages FROM messages;"

# workflow.sqlite — task tracking and event processing
sqlite3 /opt/llm/db/workflow.sqlite "SELECT COUNT(*) AS tasks FROM tasks;"
sqlite3 /opt/llm/db/workflow.sqlite "SELECT status, COUNT(*) FROM tasks GROUP BY status;"
```

Schema details for all three: `90_shared_04_db_architecture_and_schema.md`.

---

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

`/mcp` command probes all MCP HTTP servers at `/health` endpoint (5 second timeout). Returns `bool` via `probe_mcp_health()`, or structured `McpHealthProbeResult` via `_probe_mcp_health_detail()`.

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
| `ToolExecEvent` | `source: str = "agent"`, `error_type: str = ""`, `workflow_id: str = ""`, `session_id: str = ""`, `artifact_uri: str \| None = None` |

### Audit writers (`agent/tool_audit.py`)

| Function | Responsibility |
|---|---|
| `log_approval_decision(ctx, outcome)` | Write a structured approval_decision event to the audit log |
| `write_round_exec(ctx, round_id, tool_count, mode, has_side_effect, trigger_tool, elapsed_ms, affected_tools, serial_reason, estimated_parallel_ms, scheduling_mode)` | Log a round-wide execution event, capturing serialization impact |

---

## OpenTelemetry (OTel)

Configure in `config/otel.toml`:

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

### OTel Spans

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

When `workflow_mode = "required"` (production default), the agent validates the workflow
definition file exists before initializing the orchestrator. If the file is missing, a
`RuntimeError` is raised with actionable guidance.

**Expected path:** `config/workflows/default.json`

**Remediation options:**
- Deploy the workflow definition to the expected path
- Set `workflow_mode = "disabled"` in config (not recommended for production)
- Set `workflow_mode = "auto"` for degraded operation (warns and falls back to direct LLM)

The preflight check (`_check_workflow_definition()` in `startup.py`) runs before
`Orchestrator.__init__()` and produces a clear error message rather than a cryptic
`WorkflowLoadError` that may not include the expected file path.

**Note:** `workflow_mode` is a startup-only setting — it cannot be changed via `/reload`.
Any change requires a full agent restart.

---

## Interpreting `/context`

```
Context state:
  Messages        : 12
  Total chars     : 4,321
  Compress limit  : 8,000
  Remaining       : 3,679 chars until compression
  Compress count  : 1
  System prompt   : default
  System preview  : '...'
  Token estimate  : 1,080 (chars / 4)
  Token limit     : disabled
  Memory layer    : disabled
Budget breakdown:
  system        :    1,234 chars ( 38%)
  history       :    1,987 chars ( 61%)
  tool_results  :      100 chars (  3%)
```

- **Remaining:** distance from `context_char_limit` → compression trigger
- **Token estimate:** `chars / 4` unless `/tokenize` endpoint is configured
- **Token limit:** `disabled` when `context_token_limit` is not set; shows `200,000 tokens` (or configured value) when `context_token_limit` is configured
- **Memory layer:** `enabled (entries=N)` when `use_memory_layer=True`

---

## Interpreting `/stats`

```
Turns: 5 | Tool calls: 12 | Errors: 1
LLM: retries=0, reconnects=0, HB timeouts=0, partials=0, parse_errors=0
Cache hits: 3 | Compress: 1 | Semantic cache hits: 0
Input tokens: 2,048 | Output tokens: 512
Latency (mean/max): llm=1.2s/2.1s, tools=0.3s/0.8s
```

- **Partial completions:** LLM responses interrupted mid-stream; stored in `tool_result_store` (accessible via `/tool show llm_partial_completion`). For the canonical partial-completion model → [05_agent_03 §Partial-Completion Model](05_agent_03_turn-processing-flow.md)
- **HB timeouts:** SSE heartbeat timeouts (possible LLM overload)
- **Cache hits:** tool result cache hits (check `/tool list` for cached content)
- **Approval pending:** `Approval: PENDING — use /approve or /reject` line appears only when `ctx.workflow.approval_pending=True`. Shown when a workflow task is waiting for `/approve` or `/reject`.

---

## Partial Completion and Truncation Monitoring

| Condition | How to detect | Action |
|---|---|---|
| LLM stream interrupted (partial completion) | `/stats` shows `partials > 0`; agent log: `WARNING Partial LLM completion saved: {kind}` | `/tool show llm_partial_completion` to view content; check LLM endpoint stability |
| Context compression (HistoryManager) | `/stats` shows `Compress: N > 0`; agent log: `INFO Compressed history` | Increase `compression_char_threshold` or reduce context size |
| Max tool turns hit | Agent log: `WARNING max_tool_turns=N reached` | Increase `max_tool_turns` in `config/tools.toml` |

For the canonical partial-completion model → [05_agent_03 §Partial-Completion Model](05_agent_03_turn-processing-flow.md).

---

## Troubleshooting

| Symptom | Cause | Action |
|---|---|---|
| `embedding attempt 3/3` all fail | embed-llm not running or overloaded | `curl -s http://127.0.0.1:8003/health`; wait for model load |
| `AttributeError: enable_load_extension` | Python built without sqlite extension support | `echo 'dev-lang/python sqlite' >> /etc/portage/package.use/python && emerge dev-lang/python` |
| `no such table: chunks_vec` | sqlite-vec extension load failed | `ls /opt/llm/sqlite-vec/vec0.so` |
| FTS search returns 0 results | `chunks_fts` out of sync | `/db rag rebuild-fts` |
| `blob_bytes` ≠ 1536 | Embedding dimension mismatch | Verify embed model outputs 384 dimensions |
| `Sudachi tokenize error` frequent | sudachidict-core not installed | `pip install sudachidict-core` |
| llama-server won't start | Model file path or permissions | `ls -lh /opt/llm/models/` |
| Very high latency | Multiple models loaded, RAM exhausted | Adjust `--threads`; keep total ≤ 4 |
| `/mcp` shows UNAVAILABLE server | Health registry marked server unavailable | Restart the MCP server; `/reload` |

---

## Runtime Diagnostics (session-end summary)

At session end, a lightweight diagnostic summary is persisted to the `session_diagnostics` table via `DiagnosticStore.save(kind="session_summary")`. This survives beyond the REPL session for post-mortem analysis.

Querying session diagnostics:

```bash
sqlite3 /opt/llm/db/session.sqlite "SELECT kind, json(content) FROM session_diagnostics WHERE session_id = ? ORDER BY created_at DESC LIMIT 10;"
```

Retrieving a specific diagnostic entry:

```bash
sqlite3 /opt/llm/db/session.sqlite "SELECT kind, content FROM session_diagnostics WHERE session_id = ? AND kind = 'session_summary' ORDER BY created_at DESC LIMIT 1;" | jq .content
```

Filtering by diagnostic kind:

```bash
sqlite3 /opt/llm/db/session.sqlite "SELECT kind, content FROM session_diagnostics WHERE kind = 'mid_turn_error' ORDER BY created_at DESC;" | jq -r '.content'
```

**Fields in each record:**

| Field | Description |
|---|---|
| `session_id` | SQLite session row ID |
| `timestamp` | ISO-8601 UTC timestamp of session end |
| `turns` | Total turns processed |
| `tool_calls` | Total tool calls executed |
| `tool_errors` | Tool call failures |
| `partial_completions` | LLM partial completions (interrupted streams) |
| `parse_errors` | SSE parse errors |
| `heartbeat_timeouts` | SSE heartbeat timeouts |
| `reconnects` | LLM transport reconnects |
| `semantic_cache_hits` | Semantic cache lookups that matched |
| `input_tokens` | Total input tokens (if available) |
| `output_tokens` | Total output tokens (if available) |
| `compress_count` | History compression operations |
| `latency_summary` | Per-step mean/max latency in ms |
| `tool_result_summary` | `{total: N, errors: M}` from tool_results table |

**Reading diagnostics:**

```bash
# View all diagnostic events (most recent first)
sqlite3 /opt/llm/db/session.sqlite "SELECT id, session_id, kind, created_at FROM session_diagnostics ORDER BY created_at DESC LIMIT 50;"

# Count diagnostics by kind
sqlite3 /opt/llm/db/session.sqlite "SELECT kind, COUNT(*) AS n FROM session_diagnostics GROUP BY kind ORDER BY n DESC;"

# View diagnostics for one session
sqlite3 /opt/llm/db/session.sqlite "SELECT id, kind, content, created_at FROM session_diagnostics WHERE session_id = ? ORDER BY created_at DESC;"

# View all session summaries
sqlite3 /opt/llm/db/session.sqlite "SELECT kind, json(content) FROM session_diagnostics WHERE kind = 'session_summary' ORDER BY created_at DESC;" | jq .

# Filter sessions with high error rates
sqlite3 /opt/llm/db/session.sqlite "SELECT kind, content FROM session_diagnostics WHERE kind = 'session_summary' AND json_extract(content, '$.tool_errors') > 0 ORDER BY created_at DESC LIMIT 10;" | jq -r '.content'

# Aggregate stats across sessions
sqlite3 /opt/llm/db/session.sqlite "SELECT COUNT(*) as total_sessions, AVG(json_extract(content, '$.turns')) as avg_turns, SUM(json_extract(content, '$.tool_errors')) as total_tool_errors FROM session_diagnostics WHERE kind = 'session_summary';"
```

Diagnostics persistence failures are logged at DEBUG level and do not affect REPL shutdown.

---

## RAG Pipeline Diagnostics

### /rag search --debug output

Running `/rag search <query> --debug` prints a structured debug trace after the result.

Example output:

```
  [debug] RRF config: use_rrf=True rrf_k=60
  [debug] MQE queries (2):
    1: what is the retry policy
    2: retry policy configuration
  [debug] search: 2 result lists, 18 total candidates
  [debug] RRF merge: 12 unique candidates (top 5):
    chunk_id=4821 rrf=0.0312 url=file:///opt/llm/docs/config.md
    ...
  [debug] reranked top-5:
    chunk_id=4821 score=0.9241 url=file:///opt/llm/docs/config.md
    ...

  --- Stage timings ---
    MqeStage: 142.3 ms
    SearchStage: 38.1 ms
    FusionStage: 2.4 ms
    RerankStage: 95.7 ms

  --- Fallbacks / Failures ---
    RerankStage [fallback]: use_rerank=False
```

### Stage result interpretation

| Stage | `"success"` | `"fallback"` | `"failure"` |
|---|---|---|---|
| `MqeStage` | MQE queries generated | `use_mqe=False`; original query used | LLM call failed |
| `SearchStage` | Results returned | No matching chunks (empty result) | DB error or embedding failure |
| `FusionStage` | RRF merge applied | `use_rrf=False`; raw results used | Merge error |
| `RerankStage` | Cross-encoder rerank applied | `use_rerank=False`; RRF scores used | LLM call failed |
| `HttpAugment` | Remote RAG service returned result | `http_result_kind`: `"remote_nonempty"` (success) / `"remote_empty"` (valid empty) / `"in_process_fallback"` (failure) | HTTP error / no context |
| `Refiner` | Refiner compressed chunks | `"refiner_returned_empty"` (empty output) or `"refiner_exception: {e}"` (LLM error) | LLM call failed |

### StageResult fields

Each pipeline run populates `pipeline.last_stage_results` (a list of `StageResult` dicts):

| Field | Type | Description |
|---|---|---|
| `stage_name` | str | Class name of the stage (e.g. `"MqeStage"`) |
| `status` | str | `"success"`, `"fallback"`, or `"failure"` |
| `elapsed_seconds` | float | Wall-clock seconds for this stage |
| `fallback_reason` | str or None | Reason string when status is `"fallback"` or `"failure"` |

### Status values

| Status | Meaning |
|---|---|
| `success` | Stage completed normally |
| `fallback` | Stage bypassed due to config flag (e.g. `use_rrf=False`) |
| `failure` | Stage raised an exception; pipeline continued with degraded output |

### Refiner and HTTP fallback stages

Two additional entries appear in `last_stage_results` when applicable:

| stage_name | Appears when | fallback_reason on fallback |
|---|---|---|
| `HttpAugment` | `rag_service_url` is set | `http_result_kind`: `"remote_nonempty"` / `"remote_empty"` / `"in_process_fallback"` |
| `Refiner` | `use_refiner=True` | `"refiner_returned_empty"` (empty output) or `"refiner_exception: {e}"` (LLM error) |

### RAG ingestion diagnostics

The standalone RAG ingestion pipeline (`scripts/rag/ingestion/crawler.py`) prints per-URL progress and a summary line:

```
[ingest] crawling https://example.com/docs (lang=en)...
[ingest] splitting chunks...
[ingest] 12 chunks written
[ingest] ingesting to DB...
inserted 10/12 chunks: https://example.com/docs/page1
inserted 8/8 chunks: https://example.com/docs/page2
inserted 0/5 chunks: https://example.com/docs/page3  <- skipped (already registered)
=== done: 3 URLs processed (18 success, 0 failed, 1 skipped) ===
```

| Field | Description |
|---|---|
| `inserted N/M chunks: <url>` | N chunks embedded, M total in crawl JSON; 0/M means URL was skipped (already in DB without `--force`) |
| `done: X URLs processed` | Aggregate across all URL groups in this run |
| `success` | Chunks successfully embedded and stored |
| `failed` | Chunks where embedding or DB write failed |
| `skipped` | URL groups skipped because the URL already exists in `documents` (use `--force` to re-embed) |

---

## Memory Status (`/memory status`)

Example output:

```
Field                   Value
----------------------  --------------------------------------------------
Mode                    hybrid
Memory layer            enabled
Embedding enabled       Yes
Local-only              enabled
Circuit                 closed
Consecutive failures    0
FTS fallback count      2
Last retrieval mode     hybrid
Entries (total)         142
  semantic              89
  episodic              53
Embed skip count        8
  source:RULE           34
  source:DECISION       22
  source:FAILURE        15
  source:CONVERSATION   71
```

- **Mode**: `hybrid` | `fts-only` | `degraded` | `disabled`
- **Local-only**: `enabled` when `memory_local_only = true` in `memory.toml`
- **FTS fallback count**: sessions where embedding was unavailable and FTS-only was used
- **Embed skip count**: entries stored without embedding (circuit open or embed disabled)

---

## Graceful Shutdown

- `SIGTERM` → converted to `SystemExit(0)` by `agent.py`
- `_shutdown_requested` flag set → REPL loop exits after current input wait
- `finally` block in `_run_repl_loop()`:
  - `_persist_session_diagnostics()` → write runtime summary to `session_diagnostics` table via `DiagnosticStore.save(kind="session_summary")`
  - `memory.on_session_stop()` → extract + persist memories
  - `watchdog_task.cancel()`
  - `_close_resources()` → readline history save, `lifecycle.shutdown_all()`, HTTP client close
