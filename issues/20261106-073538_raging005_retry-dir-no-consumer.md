# Give retry/ a consumer or remove the embedding-failure retry routing

## Priority
Medium

## Summary
`FileRouter.route` moves chunks whose failure reason string contains "embedding" to
`rag-src/retry/`, but no code in the repository ever reads, re-processes, or cleans up
that directory. Embedding-failed chunks are moved out of the processing queue and then
forgotten. Either implement a consumer for `retry/` or stop routing files there.

## Problem
- `scripts/rag/ingestion/file_routing.py` `route()` classifies failed chunks by the
  substring test `if "embedding" in reason.lower()`: matching reasons go to `retry/`,
  all others to `failed/`.
- The only failure reason that matches is `IngestionFailureReason.EMBEDDING_FAILED`,
  produced by `scripts/rag/ingestion/embedding.py` when the embedding HTTP request fails
  (after `EmbeddingService`'s own HTTP retries).
- A repository-wide search finds no reader of `retry/`: references to the retry directory
  exist only inside `file_routing.py` and its tests. `deploy/setup_services.sh`'s
  post-ingestion cleanup clears only `registered/`.
- Consequence: files in `retry/` are neither retried nor archived. They accumulate on
  disk and vanish from pipeline metrics because they no longer exist in `chunk/`, while
  embedding HTTP retry already exists inside `EmbeddingService` (`retry_count` in
  `config/ingester.toml`), so the file-level retry tier adds no actual retry.
- Secondary: the classification is a loose substring match on the reason string rather
  than a decision over `IngestionFailureReason` members, so any future reason containing
  "embedding" (e.g. `embedding_schema_error`) silently changes destination.

## Background
The retry tier was introduced when ingestion failure reasons were classified
(`issues/done/20260913-183170_missing_ingestion_pipeline_chunkformaterror_classification.md`),
but no consumption path was defined then or since. The documented pipeline is a linear
three-stage flow (`rag.ingestion.crawler` → `rag.ingestion.chunk_splitter` →
`rag.ingestion.ingester` per `deploy/setup_services.sh`), so nothing re-feeds `retry/`
back into `chunk/`.

## Reason for Change
Broken workflow: an operator following the routing design expects automatic retry; today
the only recovery is undocumented manual file movement back to `chunk/`.

## Implementation Intent
Decide one of two coherent designs during planning:
1. Implement a consumer: the ingester (or a scheduled stage) re-feeds `retry/` files into
   the next run with an attempt budget and eventual promotion to `failed/`.
2. Remove the retry tier: route embedding failures to `failed/` like every other failure
   (or leave them in `chunk/` for the next run), delete the substring test, and classify
   explicitly over `IngestionFailureReason` members.
Design 2 is the smaller change and matches the fact that embedding HTTP retry already
lives in `EmbeddingService`; design 1 requires an attempt counter that does not exist.

## Target Files or Areas
- `scripts/rag/ingestion/file_routing.py`
- `scripts/rag/ingestion/embedding.py` (reason production context only)
- `deploy/setup_services.sh` (cleanup list, only under design 1)

## Required Changes
- Choose and implement one of the two designs.
- Under design 2: remove the `retry_dir` branch from `route()`, replace the substring
  test with explicit enum-based classification, and update tests asserting the retry
  destination.
- Under design 1: add the consumption path, an attempt limit, promotion to `failed/`, and
  document `retry/` in the deployment cleanup list.

## Constraints
- Do not introduce a parallel retry mechanism for embedding failures; `EmbeddingService`
  already retries HTTP via `retry_count` (`config/ingester.toml`).
- Keep `failed/` as the terminal state; do not create new top-level stage directories.

## Acceptance Criteria
- After an ingester run, every chunk file that left `chunk/` is in a directory with a
  defined consumer or documented terminal meaning.
- No chunk file is stranded in a directory nothing reads.
- Routing decisions are expressed over `IngestionFailureReason` members, not substring
  matches.

## Testing Expectations
- Unit tests for the chosen routing behavior (design 2: embedding-failed chunks land in
  `failed/`; design 1: retry files are consumed with an attempt budget and eventually
  promoted to `failed/`).
- `uv run pytest tests/rag/ingestion`.

## Documentation Impact
Update the RAG ingestion pipeline docs to describe the chosen file lifecycle (`chunk/` →
`registered/` / `failed/`, with or without `retry/`).

## Out of Scope
- Group-validation routing changes (`20261106-073538_raging003_recrawled-chunk-group-poisoning.md`).
- Embedding service retry-count tuning.

## Dependencies
- Ordering note: this issue should land together with
  `20261106-073538_raging003_recrawled-chunk-group-poisoning.md` so failure routing is
  decided once.

## Unresolved Questions
- Which design (consumer vs. removal) the project prefers — needs an operator decision.

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
- **Related target files**: `scripts/rag/ingestion/file_routing.py`, `scripts/rag/ingestion/embedding.py`, `deploy/setup_services.sh`
