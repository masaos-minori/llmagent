# Agent Operations and Observability

- Configuration → [05_agent_08_04_configuration-mcp-approval-obs.md](05_agent_08_04_configuration-mcp-approval-obs.md)

## Monitoring Partial Completions and Truncation

| Status | Detection Method | Action |
|---|---|---|
| LLM Stream Interruption (Partial Completion) | `/stats` shows `partials > 0`. Agent log: `WARNING Partial LLM completion saved: {kind}` | Check details in `session_diagnostics` (`kind=partial_completion`). Verify LLM endpoint stability. |
| Context Compression (HistoryManager) | `/stats` shows `Compress: N > 0`. Agent log: `INFO History compressed: %s messages summarized` | Increase `context_char_limit` or reduce context size. |
| Max Tool Turns Reached | Agent log: `WARNING Reached max_tool_turns=%s` | Increase `max_tool_turns` in `config/agent.toml`. |

For the formal partial completion model, see [05_agent_03 Partial-Completion Model](05_agent_03_01_turn-processing-flow-overview.md).

**Implementation Notes:**
- The actual display label for `/stats` is `Partial compl : N` (or `Partial compl : 0` when zero), not exactly `partials > 0`. If there is at least one, it appends `(stored in session_diagnostics)`.
- The log message for compression is actually `"History compressed: %s messages summarized"`, which does not match the string `Compressed history` used in this table.
- There is no configuration key named `compression_char_threshold`. The actual threshold key is `context_char_limit` (default 8000); compression is triggered when the total character count of the history exceeds this value.
- If the character limit is exceeded without compression occurring, `HistoryManager` performs fallback truncation (deleting low-priority messages) and increments `stat_fallback_truncate_count`. This is displayed as `Fallback trunc: N` in `/stats`. This behavior is a failsafe implemented if compression fails.

## Troubleshooting

| Symptom | Cause | Action |
|---|---|---|
| All `embedding attempt 3/3` fail | embed-llm is not running or overloaded | Run `curl -s http://127.0.0.1:8081/health` and wait for the model to load |
| `AttributeError: enable_load_extension` | Python was built without sqlite extension support | Rebuild Python with sqlite support |
| `no such table: chunks_vec` | Failure to load `sqlite-vec` extension | Verify `ls /opt/llm/sqlite-vec/vec0.so` |
| FTS search returns 0 results | `chunks_fts` is in an asynchronous state | Run `/session rag-rebuild-fts` |
| `blob_bytes` ≠ expected | Embedding dimension mismatch | Verify the BLOB byte count matches `scripts/db/store_protocols.py::get_embedding_dims()` (returns a fixed code constant, not a config value) |
| Frequent `Sudachi tokenize error` | `sudachidict-core` is not installed | Run `pip install sudachidict-core` |
| `llama-server` fails to start | Path or permission issue with model files | Check `ls -lh /opt/llm/models/` |
| Extremely high latency | RAM exhausted due to multiple models loaded | Adjust `--threads` and keep the total $\le$ 4 |
| Server shows UNAVAILABLE in `/mcp` | Health registry marks server as unavailable | Check watchdog logs regarding auto-restart attempts. Note that changing the server *definition* (URL, auth, transport, etc.) requires a full agent restart — `/reload` does not apply MCP configuration changes. |

## Runtime Diagnostics (Session End Summary)

At the end of a session, a lightweight diagnostic summary is persisted to the `session_diagnostics` table via `DiagnosticStore.save(kind="session_summary")`. This persists across REPL sessions and can be used for post-mortem analysis.

### Querying Session Diagnostics

```bash
# View all diagnostic events (newest first)
sqlite3 /opt/llm/db/session.sqlite "SELECT id, session_id, kind, created_at FROM session_diagnostics ORDER BY created_at DESC LIMIT 50;"

# Aggregate by kind
sqlite3 /opt/llm/db/session.sqlite "SELECT kind, COUNT(*) AS n FROM session_diagnostics GROUP BY kind ORDER BY n DESC;"

# Diagnostics for a specific session
sqlite3 /opt/llm/db/session.sqlite "SELECT id, kind, content, created_at FROM session_diagnostics WHERE session_id = ? ORDER BY created_at DESC;"

# View all session summaries
sqlite3 /opt/llm/db/session.sqlite "SELECT kind, json(content) FROM session_diagnostics WHERE kind = 'session_summary' ORDER BY created_at DESC;" | jq .

# Filter sessions with high error rates
sqlite3 /opt/llm/db/session.sqlite "SELECT kind, content FROM session_diagnostics WHERE kind = 'session_summary' AND json_extract(content, '$.tool_errors') > 0 ORDER BY created_at DESC LIMIT 10;" | jq -r '.content'

# Cross-session statistical aggregation
sqlite3 /opt/llm/db/session.sqlite "SELECT COUNT(*) as total_sessions, AVG(json_extract(content, '$.turns')) as avg_turns, SUM(json_extract(content, '$.tool_errors')) as total_tool_errors FROM session_diagnostics WHERE kind = 'session_summary';"
```

### Diagnostic Kinds

In addition to `session_summary` and `mid_turn_error`, the following `kind` values are stored via `DiagnosticStore`:

| Kind | Source | Content |
|---|---|---|
| `partial_completion` | `handle_partial_completion` | Turn number, reason, and partial text length for turns where the LLM stream ended partially |
| `llm_transport_error` | Session Management | The partial completion text itself, or generic transport error details |
| `guard_hint` | Tool Loop Guard Function | Hints emitted when tool loop guards (cycle detection, duplicate threshold exceeded) trigger |
| `transport_failure` | Tool Runner | Transport layer failure during tool execution (tool name, server_key, error details) |
| `serialization_event` | Tool Runner | Round-based serialization execution events |
| `rag_query` | RAG Export Command | Pipeline diagnostics (`stage_results`, etc.) for RAG queries. Aggregated into `rag_query_count`/`rag_stage_outcomes` in `session_summary` |

Note: `fetch_by_kind` and `fetch_all` were removed in NC-013 and are no longer called from production code.

### Session Summary Fields

| Field | Description |
|---|---|
| `session_id` | SQLite session row ID |
| `timestamp` | ISO-8601 UTC timestamp of session end |
| `turns` | Total number of turns processed |
| `tool_calls` | Total number of tool calls executed |
| `tool_errors` | Number of tool call failures |
| `partial_completions` | Number of partial LLM completions (interrupted streams) |
| `parse_errors` | Number of SSE parse errors |
| `heartbeat_timeouts` | Number of SSE heartbeat timeouts |
| `reconnects` | Number of LLM transport reconnections |
| `semantic_cache_hits` | Number of semantic cache hits |
| `input_tokens` | Total input tokens (if available) |
| `output_tokens` | Total output tokens (if available) |
| `compress_count` | Number of times history was compressed |
| `latency_summary` | Average/Max latency per step (ms) |
| `fallback_truncate_count` | Number of times fallback truncation occurred (deletion of low-priority messages) |
| `workflow_count` | Number of workflows started during the session |
| `task_count` | Number of tasks generated during the session |
| `approval_events` | Number of approval-related events |
| `retry_count` | Number of retries for task execution (`execute` stage) |
| `artifacts` | List of URIs for artifacts generated during the session |
| `rag_query_count` | Count of `kind=rag_query` diagnostic entries |
| `rag_stage_outcomes` | Aggregated stage results (`stage_results`) from RAG query diagnostics |

**Implementation Notes:**
- `workflow_count`, `task_count`, `approval_events`, `retry_count`, and `artifacts` default to 0 or an empty list if querying the workflow DB fails.
- If persisting diagnostic information fails, it is logged at DEBUG level; this does not affect the main process (e.g., conversation continuation or session shutdown). `DiagnosticStore.save()` is designed so that failures in saving diagnostics do not block primary operations like conversation continuation or session shutdown.

## Related Docs

- [05_agent_10_01_operations-and-observability-startup-and-health.md](05_agent_10_01_operations-and-observability-startup-and-health.md) — Startup and Health Checks
- [05_agent_10_02_operations-and-observability-audit-and-otel.md](05_agent_10_02_operations-and-observability-audit-and-otel.md) — Audit Logs and OTel
- [05_agent_10_03_operations-and-observability-workflow-observability.md](05_agent_10_03_operations-and-observability-workflow-observability.md) — Workflow Observability
- [05_agent_10_04_operations-and-observability-validation-and-troubleshooting.md](05_agent_10_04_operations-and-observability-validation-and-troubleshooting.md) — Validation and Troubleshooting
- [05_agent_10_06_operations-and-observability-rag-diagnostics-and-memory.md](05_agent_10_06_operations-and-observability-rag-diagnostics-and-memory.md) — RAG Diagnostics and Memory
