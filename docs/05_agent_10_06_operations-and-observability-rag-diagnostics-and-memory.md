---
title: "Agent Operations and Observability - RAG Diagnostics and Memory"
category: agent
tags:
  - agent
  - operations
  - rag-diagnostics
  - memory-status
  - graceful-shutdown
related:
  - 05_agent_00_document-guide.md
  - 05_agent_10_01_operations-and-observability-startup-and-health.md
  - 05_agent_10_02_operations-and-observability-audit-and-otel.md
  - 05_agent_10_03_operations-and-observability-workflow-observability.md
  - 05_agent_10_04_operations-and-observability-validation-and-troubleshooting.md
  - 05_agent_10_05_operations-and-observability-monitoring.md
source:
  - 05_agent_10_01_operations-and-observability-startup-and-health.md
---

# Agent Operations and Observability

- Configuration → [05_agent_08_04_configuration-mcp-approval-obs.md](05_agent_08_04_configuration-mcp-approval-obs.md)

## RAG Pipeline Diagnostics

### Interpreting Stage Results

| Stage | `"success"` | `"fallback"` | `"failure"` |
|---|---|---|---|
| `MqeStage` | MQE queries generated | `use_mqe=False`; original query used | LLM call failed |
| `SearchStage` | Results returned | No matching chunks (empty result) | DB error or embedding failure |
| `FusionStage` | RRF merge applied | `use_rrf=False`; raw results used | Merge error |
| `RerankStage` | Cross-encoder rerank applied | `use_rerank=False`; RRF scores used | LLM call failed |
| `HttpAugment` | Remote RAG service returned result | `http_result_kind`: `"remote_nonempty"` (success) / `"remote_empty"` (valid empty) / `"in_process_fallback"` (failure) | HTTP error / no context |
| `Refiner` | Refiner compressed chunks | `"refiner_returned_empty"` (empty output) or `"refiner_exception: {e}"` (LLM error) | LLM call failed |

### Status Values

| Status | Meaning |
|---|---|
| `success` | Stage completed successfully |
| `fallback` | Stage bypassed due to configuration flag (e.g., `use_rrf=False`) |
| `failure` | Stage raised an exception; pipeline continues with degraded output |

### Refiner and HTTP Fallback Stages

When applicable, two additional entries appear in `last_stage_results`.

| stage_name | Appears when | fallback_reason on fallback |
|---|---|---|
| `HttpAugment` | `rag_service_url` is configured | `http_result_kind`: `"remote_nonempty"` / `"remote_empty"` / `"in_process_fallback"` |
| `Refiner` | `use_refiner=True` | `"refiner_returned_empty"` (empty output) or `"refiner_exception: {e}"` (LLM error) |

## RAG Ingestion Diagnostics

The standalone RAG ingestion pipeline outputs progress and a summary line per URL.

``` text
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
| `inserted N/M chunks: <url>` | N chunks were embedded; M is the total number in the crawl JSON. 0/M means the URL was skipped (already exists in DB without `--force`). |
| `done: X URLs processed` | Aggregation of all URL groups in this execution |
| `success` | Chunks successfully embedded and saved |
| `failed` | Chunks that failed embedding or DB write |
| `skipped` | URL groups skipped because they already exist in `documents` (use `--force` to re-embed) |

## Memory Status (`/memory status`)

Example output:

``` text
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

- **Mode** label: `Hybrid mode (semantic + FTS)` | `Memory enabled, embedding disabled (FTS-only)` | `Degraded mode (circuit open, FTS fallback)` | `Memory layer disabled`
- **Local-only**: `enabled` if `memory_local_only = true` in `config/agent.toml`
- **FTS fallback count**: Number of sessions where embedding was unavailable and only FTS was used
- **Embed skip count**: Number of entries saved without embedding (due to circuit open or embedding disabled)

## Graceful Shutdown

- `SIGTERM` $\rightarrow$ converted to `SystemExit(0)` by `agent.py`
- Shutdown flag set $\rightarrow$ REPL input competes between blocking `input()` calls and `_shutdown_event.wait()` (using `asyncio.wait(FIRST_COMPLETED)`). If the shutdown event completes first, `input()` returns `None` immediately without waiting for next keypress. The executor thread for the remaining `input()` is not interrupted and terminates upon process exit.
- `finally` block:
  - Session diagnostics persistence $\rightarrow$ writes runtime summary to `session_diagnostics` table via `DiagnosticStore.save(kind="session_summary")`
  - `memory.on_session_stop()` $\rightarrow$ extraction and persistence of memory
  - Resource cleanup $\rightarrow$ saving readline history, `lifecycle.shutdown_all()`, closing HTTP clients
- `shutdown_all()` temporarily absorbs additional `SIGINT` (e.g., second Ctrl-C) during execution to ensure all MCP subprocesses complete their shutdown processing without interruption (returns to normal interrupt handling after completion).

## Related Docs

- [05_agent_10_01_operations-and-observability-startup-and-health.md](05_agent_10_01_operations-and-observability-startup-and-health.md) — Startup and Health Checks
- [05_agent_10_02_operations-and-observability-audit-and-otel.md](05_agent_10_02_operations-and-observability-audit-and-otel.md) — Audit Logs and OTel
- [05_agent_10_03_operations-and-observability-workflow-observability.md](05_agent_10_03_operations-and-observability-workflow-observability.md) — Workflow Observability
- [05_agent_10_04_operations-and-observability-validation-and-troubleshooting.md](05_agent_10_04_operations-and-observability-validation-and-troubleshooting.md) — Validation and Troubleshooting
- [05_agent_10_05_operations-and-observability-monitoring.md](05_agent_10_05_operations-and-observability-monitoring.md) — Monitoring
