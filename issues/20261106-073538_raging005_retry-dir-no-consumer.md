# Give retry/ a consumer or remove the retry routing path

## Priority
Medium

## Summary
`FileRouter` routes `retryable_error` chunks to `rag-src/retry/`, but no code in the
repository ever reads, re-processes, or cleans up that directory. Retry-classified chunks
are moved out of the processing queue and then forgotten, while the pipeline's actual
retry mechanisms (embedding HTTP retries, crawler re-queue) live elsewhere. Either
implement a consumer for `retry/` or stop routing files there.

## Background
Evidence path:
- `scripts/rag/ingestion/file_routing.py` `_classify_destination` maps
  `IngestionFailureReason.RETRYABLE_ERROR` to `retry/`, and `route()` moves those files
  from `chunk/` into `retry/`.
- A repository-wide search for `retry/` consumers (scripts, tools, deploy) finds none: the
  only references to the retry destination are inside `file_routing.py` and its tests.
- `retry/` is not listed in `deploy/setup_services.sh`'s post-ingestion cleanup, which
  only clears `registered/`.
- The documented pipeline is a linear three-stage flow (`rag.ingestion.crawler` →
  `rag.ingestion.chunk_splitter` → `rag.ingestion.ingester`), so nothing re-feeds `retry/`
  back into `chunk/`.
- `RETRYABLE_ERROR` is currently produced only by `scripts/rag/ingestion/embedding.py`
  when the embedding HTTP request errors; its docstring still describes a
  "source-file-exists re-crawl case" that no ingestion code produces.
Related historical issue: `issues/done/20260913-183170_missing_ingestion_pipeline_chunkformaterror_classification.md`
classified failure reasons but did not define retry/ consumption.

## Problem
Files routed to `retry/` are stranded: they are neither retried nor archived, accumulate
on disk, and disappear from every pipeline metric because they no longer exist in
`chunk/`. The name implies behavior the system does not provide.

## Reason for Change
Broken workflow: an operator following the routing design expects automatic retry; today
the only recovery is manual file movement back to `chunk/`, which is undocumented.

## Implementation Intent
Decide one of two coherent designs during planning:
1. Implement a consumer: the ingester (or a scheduled stage) re-feeds `retry/` files into
   the next run with an attempt budget and eventual promotion to `failed/`.
2. Remove the retry tier: route `retryable_error` like `transient_error` (stay in
   `chunk/` for the next run) and delete the dead classification branch.
Design 2 is the smaller change and matches how transient errors are already handled;
design 1 requires an attempt counter that does not exist today.

## Target Files or Areas
- `scripts/rag/ingestion/file_routing.py`
- `scripts/rag/ingestion/ingester.py` (classification call sites)
- `deploy/setup_services.sh` (cleanup list, only under design 1)

## Required Changes
- Choose and implement one of the two designs above.
- Under design 2: remove `retry/` from `_classify_destination`, retire or repurpose
  `IngestionFailureReason.RETRYABLE_ERROR`, and update tests that assert the retry
  destination.
- Under design 1: add the consumption path, an attempt limit, promotion to `failed/`, and
  include `retry/` in the deployment cleanup documentation.
- In both designs: correct the `RETRYABLE_ERROR` docstring so it describes only what the
  code actually produces.

## Constraints
- Do not introduce a parallel retry mechanism for embedding failures; embedding HTTP retry
  already exists in `EmbeddingService` (`retry_count` in `config/ingester.toml`).
- Keep `failed/` as the terminal state; do not create new top-level stage directories.

## Acceptance Criteria
- After an ingester run, every chunk file that left `chunk/` is in a directory with a
  defined consumer or documented terminal meaning.
- No chunk file is permanently stranded in a directory nothing reads.
- Tests covering `FileRouter` classification reflect the chosen design.

## Testing Expectations
- Unit tests for the chosen routing behavior (design 2: retryable errors stay in
  `chunk/`; design 1: retry files are consumed with attempt budget and eventually
  promoted to `failed/`).
- `uv run pytest tests/rag/ingestion`.

## Documentation Impact
Update the RAG ingestion pipeline docs to describe the chosen file lifecycle
(`chunk/` → `registered/` / `failed/`, with or without `retry/`).

## Out of Scope
- Group-validation routing changes (`20261106-073538_raging003_recrawled-chunk-group-poisoning.md`).
- Embedding service retry-count tuning.

## Dependencies
- Ordering note: file after `20261106-073538_raging003_recrawled-chunk-group-poisoning.md`
  so the failure-routing design is decided once.

## Unresolved Questions
- Which design (consumer vs. removal) the project prefers — needs an operator decision.
- Whether `RETRYABLE_ERROR` was intended for a future re-crawl feature that is documented
  somewhere outside the code.

## AI Implementation Instruction
Present both designs in the plan with a recommendation (design 2 unless a retry consumer
is explicitly wanted), then implement the approved one only. Do not leave `retry/` routing
in place without a consumer.

## Traceability
- **Workflow phase**: python-code-review
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20261106-073538
- **Related target files**: `scripts/rag/ingestion/file_routing.py`, `scripts/rag/ingestion/ingester.py`, `deploy/setup_services.sh`
