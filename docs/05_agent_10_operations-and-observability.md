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

```bash
sqlite3 /opt/llm/db/rag.sqlite "SELECT lang, COUNT(*) AS docs FROM documents GROUP BY lang;"
sqlite3 /opt/llm/db/rag.sqlite "SELECT COUNT(*) AS chunks FROM chunks;"
sqlite3 /opt/llm/db/rag.sqlite "SELECT chunk_id, LENGTH(embedding) AS bytes FROM chunks_vec LIMIT 3;"
# Expected bytes: 1536 (384 dimensions × 4 bytes)
```

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
{"event": "turn_start", "task_id": "<uuid>", "session_id": "<id>", "input_preview": "..."}
```

**`turn_end` event:**
```json
{
  "event": "turn_end",
  "task_id": "<uuid>",
  "elapsed_ms": 1234.5,
  "input_tokens": 512,
  "output_tokens": 128,
  "reconnect_count": 0,
  "tool_calls": 2
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

## Graceful Shutdown

- `SIGTERM` → converted to `SystemExit(0)` by `agent.py`
- `_shutdown_requested` flag set → REPL loop exits after current input wait
- `finally` block in `_run_repl_loop()`:
  - `memory.on_session_stop()` → extract + persist memories
  - `watchdog_task.cancel()`
  - `_close_resources()` → readline history save, `lifecycle.shutdown_all()`, HTTP client close
