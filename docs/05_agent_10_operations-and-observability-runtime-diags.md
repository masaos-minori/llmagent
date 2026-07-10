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

 | Action |
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

## Runtime Diagnostics (session-end s

ummary)

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

## RAG Pipeline Diagnostics

### /rag

 search --debug output

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
Mode                    Hybrid mode (semantic + FTS)
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

- **Mode** labels: `Hybrid mode (semantic + FTS)` | `Memory enabled, embedding disabled (FTS-only)` | `Degraded mode (circuit open, FTS fallback)` | `Memory layer disabled`
- **Local-only**: `enabled` when `memory_local_only = true` in `config/agent.toml`
- **FTS fallback count**: sessions where embedding was unavailable and FTS-only was used
- **Embed skip count**: entries stored without embedding (circuit open or embed disabled)

---

## Graceful Shutdown

- `SIGTERM` → c

onverted to `SystemExit(0)` by `agent.py`
- Shutdown flag set → `AgentREPL._read_input()` races the blocking `input()` call
  against `_shutdown_event.wait()` (`asyncio.wait(FIRST_COMPLETED)`); if the shutdown
  event wins, `_read_input()` returns `None` immediately without waiting for the next
  keystroke. The orphaned `input()` executor thread is not interrupted — it terminates
  when the process exits.
- `finally` block:
  - Session diagnostics persistence → write runtime summary to `session_diagnostics` table via `DiagnosticStore.save(kind="session_summary")`
  - `memory.on_session_stop()` → extract + persist memories
  - `watchdog_task.cancel()`
  - Resource cleanup → readline history save, `lifecycle.shutdown_all()`, HTTP client close

## Related Documents

- `agent`
- `operations`
- `observability`

## Keywords

agent
operations
observability
monitoring
