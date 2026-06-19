# Implementation: Document RAG Pipeline Diagnostic Fields

## Goal

Add a RAG pipeline diagnostics section to `docs/05_agent_10_operations-and-observability.md` so operators know what debug fields are available from `/rag search --debug` and `pipeline.last_stage_results`.

## Scope

- `docs/05_agent_10_operations-and-observability.md` — new subsection documenting:
  - `StageResult` fields and status values
  - `/rag search --debug` output format
  - `pipeline.last_stage_results` for programmatic access

Out of scope:
- Code changes
- MCP debug path (already documented or out of scope)

## Assumptions

1. The doc already has a diagnostics section at line 289 covering `diagnostics.jsonl`; the new section complements it with RAG-specific runtime diagnostics.
2. Documentation is written for operators, not developers — focus on what the output means, not how it is implemented.
3. The `StageResult` fields (`stage_name`, `status`, `elapsed_seconds`, `fallback_reason`) are stable after the pipeline.py failure-tracking implementation.
4. The debug output format is determined by `write_debug_rag()` and `_print_rag_timings()` after those are wired in `cmd_ingest.py`.

## Implementation

### Target file

`docs/05_agent_10_operations-and-observability.md`

### Procedure

1. Locate the existing diagnostics section (around line 289).
2. Insert a new `### RAG pipeline diagnostics` subsection before or after the session diagnostics section.
3. Document: `/rag search --debug` output fields, `StageResult` schema, status values, and how to interpret fallback/failure entries.

### Method

New prose subsection with a field table and annotated output example. Match existing doc style (headers, pipe tables, fenced code blocks).

### Details

**Subsection content outline:**

```
### RAG pipeline diagnostics

#### /rag search --debug output

Running `/rag search <query> --debug` prints a structured debug trace after the result.

Example output:

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

#### StageResult fields

Each pipeline run populates `pipeline.last_stage_results` (a list of `StageResult` dicts):

| Field             | Type          | Description                                              |
|-------------------|---------------|----------------------------------------------------------|
| `stage_name`      | str           | Class name of the stage (e.g. `"MqeStage"`)              |
| `status`          | str           | `"success"`, `"fallback"`, or `"failure"`                |
| `elapsed_seconds` | float         | Wall-clock seconds for this stage                        |
| `fallback_reason` | str or None   | Reason string when status is `"fallback"` or `"failure"` |

#### Status values

| Status      | Meaning                                                                 |
|-------------|-------------------------------------------------------------------------|
| `success`   | Stage completed normally                                                |
| `fallback`  | Stage bypassed due to config flag (e.g. `use_rrf=False`)               |
| `failure`   | Stage raised an exception; pipeline continued with degraded output      |

#### Refiner and HTTP fallback stages

Two additional entries appear in `last_stage_results` when applicable:

| stage_name    | Appears when              | fallback_reason on fallback       |
|---------------|---------------------------|-----------------------------------|
| `HttpAugment` | `rag_service_url` is set  | `"in-process fallback"`           |
| `Refiner`     | `use_refiner=True`        | `"refiner returned None"`         |
```

## Validation Plan

| Check | Command | Expected |
|---|---|---|
| Pre-commit | `pre-commit run --all-files` | pass |
| Manual review | Read the new section | operator understands debug output without reading source |
| Accuracy | Cross-check field names against `scripts/rag/stage.py` | `stage_name`, `status`, `elapsed_seconds`, `fallback_reason` confirmed |
