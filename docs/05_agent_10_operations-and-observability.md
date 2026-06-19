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
Type /help for commands, /exit to quit.

agent[:#1]>
```

---

## Operational Verification

### LLM service check

```bash
curl -s http://127.0.0.1:8002/v1/chat/completions -d '{"messages":[{"role":"user","content":"hi"}],"max_tokens":5}' -H 'Content-Type: application/json'
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

Schema details for all three: `06_shared_04_db_architecture_and_schema.md`.

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

`/mcp` command probes all MCP HTTP servers at `/health` endpoint (5 second timeout).

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
{"name": "llm", "attributes": {"model_url": "http://127.0.0.1:8002/..."}, ...}
{"name": "workflow.run", "attributes": {"workflow.task_id": "...", "workflow.version": "1.0"}, ...}
{"name": "workflow.stage", "attributes": {"workflow.stage_id": "execute", "workflow.attempt": 1}, ...}
```

---

## Workflow Observability

### OTel Spans

`WorkflowEngine` emits two span types when a tracer is configured:

| Span name | Emitted by | Attributes |
|---|---|---|
| `workflow.run` | `WorkflowEngine.run()` | `workflow.task_id`, `workflow.version` |
| `workflow.stage` | `WorkflowEngine._run_stage()` | `workflow.stage_id`, `workflow.attempt` |

The tracer is propagated from `Orchestrator` → `WorkflowEngine` so all workflow spans share the same trace context as the enclosing `llm` span.

### Audit Events

Three workflow-specific events are appended to `audit.log` per turn:

**`workflow_start` event** (emitted when a task is created):
```json
{"event": "workflow_start", "task_id": "...", "workflow_version": "1.0", "ts": 1718600000.1}
```

**`stage_completed` event** (emitted after the execute stage):
```json
{"event": "stage_completed", "task_id": "...", "stage_id": "execute", "elapsed_ms": 1234.5, "ts": 1718600001.4}
```

**`approval_requested` event** (emitted when human approval is required):
```json
{"event": "approval_requested", "task_id": "...", "approval_id": "...", "ts": 1718600001.5}
```

### Reading workflow audit events

```bash
# All workflow events
grep -E '"workflow_start"|"stage_completed"|"approval_requested"' /opt/llm/logs/audit.log | jq .

# Execute stage latency
grep '"stage_completed"' /opt/llm/logs/audit.log | jq '{task_id, stage_id, elapsed_ms}'

# Pending approvals
grep '"approval_requested"' /opt/llm/logs/audit.log | jq '{task_id, approval_id}'
```

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

- **Partial completions:** LLM responses interrupted mid-stream (stored in `/tool show`)
- **HB timeouts:** SSE heartbeat timeouts (possible LLM overload)
- **Cache hits:** tool result cache hits (check `/tool list` for cached content)

---

## Troubleshooting

| Symptom | Cause | Action |
|---|---|---|
| `embedding attempt 3/3` all fail | embed-llm not running or overloaded | `curl -s http://127.0.0.1:8003/health`; wait for model load |
| `AttributeError: enable_load_extension` | Python built without sqlite extension support | `echo 'dev-lang/python sqlite' >> /etc/portage/package.use/python && emerge dev-lang/python` |
| `no such table: chunks_vec` | sqlite-vec extension load failed | `ls /opt/llm/sqlite-vec/vec0.so` |
| FTS search returns 0 results | `chunks_fts` out of sync | `/db rebuild-fts` |
| `blob_bytes` ≠ 1536 | Embedding dimension mismatch | Verify embed model outputs 384 dimensions |
| `Sudachi tokenize error` frequent | sudachidict-core not installed | `pip install sudachidict-core` |
| llama-server won't start | Model file path or permissions | `ls -lh /opt/llm/models/` |
| Very high latency | Multiple models loaded, RAM exhausted | Adjust `--threads`; keep total ≤ 4 |
| `/mcp` shows UNAVAILABLE server | Health registry marked server unavailable | Restart the MCP server; `/reload` |

---

## Runtime Diagnostics (session-end summary)

At session end, a lightweight diagnostic summary is persisted to `<session_db_dir>/diagnostics.jsonl` as one JSON-lines record per session. This survives beyond the REPL session for post-mortem analysis.

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
# View all session summaries
cat /opt/llm/db/diagnostics.jsonl | jq .

# Filter sessions with high error rates
cat /opt/llm/db/diagnostics.jsonl \
  | jq 'select(.tool_errors > 0) | {session_id, turns, tool_errors, timestamp}'

# Aggregate stats across sessions
cat /opt/llm/db/diagnostics.jsonl \
  | jq -s '{total_sessions: length, avg_turns: (map(.turns) | add / length), total_tool_errors: (map(.tool_errors) | add)}'
```

The file is appended to on each session end. Diagnostics persistence failures are logged at DEBUG level and do not affect REPL shutdown.

---

## RAG Pipeline Diagnostics

### /rag search --debug output

Running `/rag search <query> --debug` prints a structured debug trace after the result.

Example output:

```
  [debug] fusion: use_rrf=True rrf_k=60
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
| `HttpAugment` | `rag_service_url` is set | `"in-process fallback"` |
| `Refiner` | `use_refiner=True` | `"refiner returned None"` |

---

## Graceful Shutdown

- `SIGTERM` → converted to `SystemExit(0)` by `agent.py`
- `_shutdown_requested` flag set → REPL loop exits after current input wait
- `finally` block in `_run_repl_loop()`:
  - `_persist_session_diagnostics()` → write runtime summary to `diagnostics.jsonl`
  - `memory.on_session_stop()` → extract + persist memories
  - `watchdog_task.cancel()`
  - `_close_resources()` → readline history save, `lifecycle.shutdown_all()`, HTTP client close
