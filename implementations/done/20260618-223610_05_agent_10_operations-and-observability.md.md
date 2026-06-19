# Implementation: Improve Ingestion and Query Diagnostics — Operations Doc

## Goal

Document diagnostic output format for RAG pipeline diagnostics in `docs/05_agent_10_operations-and-observability.md`.

## Scope

- `docs/05_agent_10_operations-and-observability.md` — new section documenting `/rag search --debug` output, ingestion stats, and stage result interpretation

## Assumptions

1. The code changes in the other impl docs (pipeline.py, cli_view.py, cmd_ingest.py, pipeline_service.py, ingester.py) are approved before this doc is written.
2. This doc describes the OUTPUT FORMAT that operators will see after those changes are implemented.

## Current State

### Operations doc (§6 Runtime Diagnostics, lines 287-326)

Documents session-end diagnostics written to `diagnostics.jsonl`:
- Fields: `session_id`, `timestamp`, `turns`, `tool_calls`, `tool_errors`, etc.
- Reading queries shown for filtering/error analysis

**Gap:** NO documentation of RAG pipeline diagnostics:
- `/rag search --debug` output format (timings, stage results, fallback reasons)
- Ingestion stats (success/fail/skip counts per URL group)
- Stage result interpretation (`"success"` vs `"fallback"` vs `"failure"`)

### Existing RAG documentation

- `docs/03_rag_03_query_pipeline.md` §2.1: `last_stage_results` field documented but output format not shown
- `docs/03_rag_04_data_model_and_interfaces.md`: `TwoStageFetchResult` fields documented but no diagnostic examples

## Proposed New Section

Add a new section "RAG Pipeline Diagnostics" after "Runtime Diagnostics (session-end summary)":

### `/rag search --debug` output format

```
--- Stage timings ---
  MqeStage: 45.2 ms
  SearchStage: 123.7 ms
  FusionStage: 8.1 ms
  RerankStage: 234.5 ms
  AugmentStage: 67.3 ms

--- Stage results ---
  ✓ MqeStage: success (45.2 ms)
  ✓ SearchStage: success (123.7 ms)
  ~ FusionStage: fallback (8.1 ms) — use_rrf=False
  ✓ RerankStage: success (234.5 ms)
  ✓ AugmentStage: success (67.3 ms)
```

**Field descriptions:**

| Field | Description | Example values |
|---|---|---|
| `✓` / `~` / `✗` | Status icon | `✓` = success, `~` = fallback (intentional), `✗` = failure (error) |
| `stage_name` | Stage class name | `MqeStage`, `SearchStage`, `FusionStage`, `RerankStage`, `AugmentStage` |
| `status` | Outcome string | `"success"`, `"fallback"`, `"failure"` |
| `elapsed` | Wall-clock time in ms | `45.2` |
| `fallback_reason` | Reason for fallback/failure (optional) | `"use_rrf=False"`, `"no search results"`, `"TypeError: ..."`, `"refiner_exception: HTTP 503"` |

### Ingestion diagnostic output

```
[ingest] crawling https://example.com/docs (lang=en)...
[ingest] crawl done
[ingest] splitting chunks...
[ingest] 12 chunks written
[ingest] ingesting to DB...
inserted 10/12 chunks: https://example.com/docs/page1
inserted 8/8 chunks: https://example.com/docs/page2
inserted 0/5 chunks: https://example.com/docs/page3  ← skipped (already registered)
=== done: 3 URLs processed (18 success, 0 failed, 1 skipped) ===
```

**Log message format:** `inserted {success}/{total} chunks: {url}`

**Aggregate summary:** `done: {N} URLs processed ({success} success, {failed} failed, {skipped} skipped)`

### Interpreting stage results

| Stage | `"success"` meaning | `"fallback"` meaning | `"failure"` meaning |
|---|---|---|---|
| `MqeStage` | MQE queries generated | `use_mqe=False` in config; original query used as-is | LLM call failed, exception details in reason |
| `SearchStage` | Vector + FTS5 search returned results | No search results (empty DB or no matching chunks) | DB error, embedding failure |
| `FusionStage` | RRF merge applied | `use_rrf=False`; raw search results used | Merge computation error |
| `RerankStage` | Cross-encoder rerank applied | `use_rerank=False`; RRF scores used as final | LLM call failed, exception details in reason |
| `AugmentStage` | Context blocks formatted | N/A (always success) | Chunk formatting error |

### HTTP mode diagnostics

When `rag_service_url` is configured:
- HTTP fallback reasons appear in stage results if the external service fails
- `min_score_applied` and `max_chunks_per_doc` are now populated from HTTP response body
- Fallback chain: HTTP → in-process pipeline → raw chunks (if refiner also fails)

## Implementation Steps (for future code implementation)

1. Add "RAG Pipeline Diagnostics" section to operations doc
2. Document `/rag search --debug` output format with example
3. Document ingestion diagnostic log format with example
4. Add stage result interpretation table
5. Cross-reference with `03_rag_03_query_pipeline.md` and `03_rag_04_data_model_and_interfaces.md`

## Validation plan

| Check | Tool | Target |
|---|---|---|
| Manual review | Read updated doc | Output format examples are accurate, actionable |
| Consistency check | Cross-reference with `03_rag_03_query_pipeline.md` §2.1 | No contradictions with existing docs |
