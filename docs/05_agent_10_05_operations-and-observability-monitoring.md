---
title: "Agent Operations and Observability - Runtime Diagnostics"
category: agent
tags:
  - agent
  - operations
  - runtime-diagnostics
  - session-end-summary
related:
  - 05_agent_00_document-guide.md
  - 05_agent_10_01_operations-and-observability-startup-and-health.md
  - 05_agent_10_02_operations-and-observability-audit-and-otel.md
  - 05_agent_10_03_operations-and-observability-workflow-observability.md
  - 05_agent_10_04_operations-and-observability-validation-and-troubleshooting.md
  - 05_agent_10_06_operations-and-observability-rag-diagnostics-and-memory.md
source:
  - 05_agent_10_01_operations-and-observability-startup-and-health.md
---

# Agent Operations and Observability

- Configuration → [05_agent_08_04_configuration-mcp-approval-obs.md](05_agent_08_04_configuration-mcp-approval-obs.md)

## Partial Completion and Truncation Monitoring

| Condition | How to detect | Action |
|---|---|---|
| LLM stream interrupted (partial completion) | `/stats` shows `partials > 0`; agent log: `WARNING Partial LLM completion saved: {kind}` | Check `session_diagnostics` (`kind=partial_completion`) for details; check LLM endpoint stability |
| Context compression (HistoryManager) | `/stats` shows `Compress: N > 0`; agent log: `INFO Compressed history` | Increase `compression_char_threshold` or reduce context size |
| Max tool turns hit | Agent log: `WARNING max_tool_turns=N reached` | Increase `max_tool_turns` in `config/agent.toml` |

For the canonical partial-completion model → [05_agent_03 §Partial-Completion Model](05_agent_03_01_turn-processing-flow-overview.md).

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
| `/mcp` shows UNAVAILABLE server | Health registry marked server unavailable | Check watchdog logs for auto-restart attempts; if the server *definition* (URL, auth, transport, etc.) changed, a full agent restart is required — `/reload` does not apply MCP config changes |

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

## Related Documents

- `05_agent_00_document-guide.md`
- `05_agent_10_01_operations-and-observability-startup-and-health.md`
- `05_agent_10_02_operations-and-observability-audit-and-otel.md`
- `05_agent_10_03_operations-and-observability-workflow-observability.md`
- `05_agent_10_04_operations-and-observability-validation-and-troubleshooting.md`
- `05_agent_10_06_operations-and-observability-rag-diagnostics-and-memory.md`

## Keywords

runtime diagnostics
session-end summary
diagnostic events
