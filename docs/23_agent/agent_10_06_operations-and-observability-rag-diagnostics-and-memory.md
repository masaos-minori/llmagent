---
title: "Agent Operations and Observability - RAG Diagnostics and Memory"
area: agent
tags:
  - agent
  - operations
  - rag-diagnostics
  - memory-status
  - graceful-shutdown
related:
  - agent_00_document-guide.md
  - agent_10_01_operations-and-observability-startup-and-health.md
  - agent_10_02_operations-and-observability-audit-and-otel.md
  - agent_10_03_operations-and-observability-workflow-observability.md
  - agent_10_04_operations-and-observability-validation-and-troubleshooting.md
  - agent_10_05_operations-and-observability-monitoring.md
  - agent_08_04_configuration-mcp-approval-obs.md
  - rag_03_03_query_pipeline-context-and-diagnostics.md
---

# Agent Operations and Observability

- Configuration → [agent_08_04_configuration-mcp-approval-obs.md](agent_08_04_configuration-mcp-approval-obs.md)

## RAG Pipeline Diagnostics

### Interpreting Stage Results

| Stage | `"success"` | `"fallback"` | `"failure"` |
|---|---|---|---|
| `MqeStage` | MQE queries generated | `use_mqe=False`, or `RagExpansionError` caught (reason `mqe_exception`); original query used | An exception other than `RagExpansionError` escaped the stage |
| `SearchStage` | Results returned | No matching chunks (empty result) | DB error or embedding failure |
| `FusionStage` | RRF merge applied | `use_rrf=False`; raw results used | Merge error |
| `RerankStage` | Cross-encoder rerank applied | `use_rerank=False`, or `RagRerankError` caught (reason `rerank_exception`); RRF order used | An exception other than `RagRerankError` escaped the stage |
| `HttpAugment` | Remote RAG service returned a result (non-empty or valid empty) | Remote call produced no result: the reason string reported by the HTTP call (default `in-process fallback`) | HTTP error / no context |
| `Refiner` | Refiner compressed chunks | `"refiner_returned_empty"` (empty output) or `"refiner_exception: {e}"` (LLM error) | Not recorded; refiner errors are reported as fallback |

### Status Values

| Status | Meaning |
|---|---|
| `success` | Stage completed successfully |
| `fallback` | Stage bypassed by a configuration flag (e.g., `use_rrf=False`), or an expected error was handled with a lower-quality result (e.g., `rerank_exception`) |
| `failure` | An exception escaped the stage (`RuntimeError`, SQLite operational error, HTTP error, or timeout); pipeline continues with degraded output |

### HTTP Result Classification

`HttpAugment` (present when `rag_service_url` is configured) and `Refiner` (present when `use_refiner=True`) appear as additional entries in `last_stage_results`. The HTTP result classification is exposed separately as `get_diagnostics()["http_result_kind"]` (`HttpResultKind`: `success` / `empty` / `error` / `not_used` / `auth_error`); the internal string literals of `HttpAugment` are not part of any external surface (see [rag_03_03](../21_rag/rag_03_03_query_pipeline-context-and-diagnostics.md)). (Explicit in code — `scripts/rag/http_augment.py`)

## RAG Ingestion Diagnostics

The standalone ingestion pipeline prints progress and one `inserted N/M chunks: <url>` line per URL, then a `done:` summary of success, failed and skipped counts. `N = 0` means the URL was skipped because it already exists in `documents`; use `--force` to re-embed. `failed` counts chunks whose embedding or DB write failed.

## Memory Status (`/memory status`)

- **Mode** label: `Hybrid mode (semantic + FTS)` | `Memory enabled, embedding disabled (FTS-only)` | `Degraded mode (circuit open, FTS fallback)` | `Memory layer disabled`
- **Local-only**: `enabled` if `memory_local_only = true` in `config/agent.toml`
- **FTS fallback count**: Number of searches since process start that used FTS only; reset on restart
- **Pinned**: Number of pinned memories and the limit `memory_max_pinned`
- **Embed skip count**: Number of entries saved without embedding (due to circuit open or embedding disabled)

## Graceful Shutdown

- `SIGTERM` → handled by the signal handler, which sets the shutdown flag and the shutdown event
- Shutdown flag set → REPL input competes between blocking stdin read calls and `_shutdown_event` (using `asyncio.wait(FIRST_COMPLETED)`). If the shutdown event completes first, stdin read returns `None` immediately without waiting for next keypress. The executor thread for the remaining stdin read is not interrupted and terminates upon process exit.
- `finally` block:
  - Session diagnostics persistence → writes runtime summary to `session_diagnostics` table via `DiagnosticStore.save(kind="session_summary")`
  - `memory.on_session_stop()` → extraction and persistence of memory
  - Resource cleanup → saving readline history, `lifecycle.shutdown_all()`, closing HTTP clients
- `shutdown_all()` temporarily absorbs additional `SIGINT` (e.g., second Ctrl-C) during execution to ensure all MCP subprocesses complete their shutdown processing without interruption (returns to normal interrupt handling after completion).

## Keywords

- agent
- operations
- rag-diagnostics
- memory-status
- graceful-shutdown
