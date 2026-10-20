---
title: "Agent Operations and Observability"
area: agent
tags:
  - agent
  - operations
  - observability
related:
  - agent_10_01_operations-and-observability-startup-and-health.md
  - agent_10_02_operations-and-observability-audit-and-otel.md
  - agent_10_03_operations-and-observability-workflow-observability.md
  - agent_10_04_operations-and-observability-validation-and-troubleshooting.md
  - agent_10_06_operations-and-observability-rag-diagnostics-and-memory.md
  - agent_00_document-guide.md
  - agent_03_03_turn-processing-flow-workflow-engine.md
  - agent_08_04_configuration-mcp-approval-obs.md
  - deployment_01_deployment.md
---
# Agent Operations and Observability

- Configuration → [agent_08_04_configuration-mcp-approval-obs.md](agent_08_04_configuration-mcp-approval-obs.md)

## Monitoring Partial Completions and Truncation

| Status | Detection Method | Action |
|---|---|---|
| LLM Stream Interruption (Partial Completion) | `/stats` shows `partials > 0`. Agent log: `WARNING Partial LLM completion saved: {kind}` | Check details in `session_diagnostics` (`kind=partial_completion`). Verify LLM endpoint stability. |
| Context Compression (HistoryManager) | `/stats` shows `Compress: N > 0`. Agent log: `INFO History compressed: %s messages summarized` | Increase `context_char_limit` or reduce context size. |
| Max Tool Turns Reached | Agent log: `WARNING Reached max_tool_turns=%s` | Increase `max_tool_turns` in `config/agent.toml`. |

For the formal partial completion model, see [agent_03 Partial-Completion Model](agent_03_03_turn-processing-flow-workflow-engine.md).

**Implementation Notes:**
- When the character limit is exceeded and compression fails, `HistoryManager` performs fallback truncation (deleting low-priority messages) as a failsafe and increments `stat_fallback_truncate_count`, shown as `Fallback trunc: N` in `/stats`.

## Troubleshooting

| Symptom | Cause | Action |
|---|---|---|
| All `embedding attempt 3/3` fail | embed-llm is not running or overloaded | Run `curl -s <embed-llm-endpoint>/health` (endpoint from the embedding settings in `config/agent.toml`) and wait for the model to load |
| `AttributeError: enable_load_extension` | Python was built without sqlite extension support | Rebuild Python with sqlite support |
| `no such table: chunks_vec` | Failure to load `sqlite-vec` extension | Verify `ls <sqlite-vec library path>` (path from the configured extension setting) |
| FTS search returns 0 results | `chunks_fts` is in an asynchronous state | Run `/session rag-rebuild-fts` |
| `blob_bytes` ≠ expected | Embedding dimension mismatch | Verify the BLOB byte count matches `scripts/db/store_protocols.py::get_embedding_dims()` (returns a fixed code constant, not a config value) |
| Frequent `Sudachi tokenize error` | `sudachidict-core` is not installed | Run `uv sync` (`sudachipy` and `sudachidict-core` are declared in `pyproject.toml`; see `docs/90_deployment/deployment_01_deployment.md`) |
| `llama-server` fails to start | Path or permission issue with model files | Check `ls -lh <model directory>` |
| Extremely high latency | RAM exhausted due to multiple models loaded | Adjust `--threads` and keep the total within the available CPU cores |
| Server shows UNAVAILABLE in `/mcp` | Health registry marks server as unavailable | There is no background watchdog; a crashed subprocess-mode server is retried only on the next tool dispatch (`ensure_ready()`), so check the agent logs for lifecycle start/restart messages and cooldown rejections. Note that changing the server *definition* (URL, auth, transport, etc.) requires a full agent restart — `/reload` does not apply MCP configuration changes. |

## Runtime Diagnostics (Session End Summary)

At the end of a session, a lightweight diagnostic summary is persisted to the `session_diagnostics` table via `DiagnosticStore.save(kind="session_summary")`. This persists across REPL sessions and can be used for post-mortem analysis.

### Querying Session Diagnostics

```bash
# Aggregate by kind
sqlite3 <session_db_path> "SELECT kind, COUNT(*) AS n FROM session_diagnostics GROUP BY kind ORDER BY n DESC;"

# Session summaries with tool errors
sqlite3 <session_db_path> "SELECT kind, content FROM session_diagnostics WHERE kind = 'session_summary' AND json_extract(content, '$.tool_errors') > 0 ORDER BY created_at DESC LIMIT 10;"
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


### Session Summary

`session_summary` is a JSON document of per-session counters: turns, tool calls and errors, LLM transport counters (partial completions, parse errors, heartbeat timeouts, reconnects), token totals, compression and fallback-truncation counts, latency, workflow counts (workflows, tasks, retries, artifact URIs) and RAG query aggregates (`rag_query_count`, `rag_stage_outcomes`). The field set is defined by the summary builder in code, not here.

- The workflow fields fall back to zero or an empty list if querying the workflow DB fails.
- A failure to persist diagnostics is logged at DEBUG level and never blocks conversation continuation or session shutdown.

## Keywords

- agent
- operations
- observability
