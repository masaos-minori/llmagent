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

### Verification (issue-to-plan cycle 20261106-101742)
- Confirmed at HEAD `bdb9bed66`: substring test at `file_routing.py:80`; `retry/` is
  created unconditionally on every `route()` call (`file_routing.py:36-37`), even with zero
  failures; the only writer of `retry/` is `FileRouter`; a repository-wide scan of
  `scripts/`, `deploy/`, `tools/` finds no reader.
- Correction: `deploy/setup_services.sh` contains no `registered/` cleanup — the claim is
  wrong. `deploy/deploy.sh:59` only creates `registered/`; `docs/21_rag/
  rag_02_01_ingestion_pipeline-overview.md:36-38` correctly states no automated retention.
- Correction: `EmbeddingService`'s HTTP retry key is `embed_retry`
  (`config/ingester.toml:18`, `embedding.py:44-67`), not `retry_count`.
- New finding: a second copy of the same substring test exists in
  `chunk_preparation.py:56-60` (the `embed_failed` metric counter), and exception-path
  reasons are raw `str(e)` (`chunk_preparation.py:73`) — httpx error strings include the
  embed endpoint URL (`/v1/embeddings`), so network errors already land in `retry/` today
  via a non-enum reason, concretely demonstrating the classification hazard.
- New finding: split state today — `.error.json` metadata for embedding-failed chunks is
  written to `failed/` (`file_routing.py:67-71`) while the chunk body moves to `retry/`
  (`:80-81`).
- Tests pinning the `retry/` destination (must flip under design 2): `tests/rag/ingestion/
  test_ingester.py` `test_embedding_failure_moves_to_retry_not_registered` (`:736-767`),
  `test_mixed_success_and_failure_routes_correctly` (`:769-819`),
  `test_retry_directory_created_for_embedding_failures` (`:857+`).
- Production observation: `/opt/llm/rag-src/` contains only `chunk/` and `registered/` — no
  `retry/` exists, so no stranded files need migration.

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
  Resolved in `plans/20261106-101742_raging005_retry-dir-no-consumer.md` as a plan-level
  recommendation: design 2 (remove the retry tier), because embedding HTTP retry already
  lives in `EmbeddingService` (`embed_retry`) and design 1 would require an attempt-budget
  mechanism that does not exist. The Plan's Implementation Target Files are frozen for
  design 2 only; choosing design 1 instead unfreezes the table and requires a revised Plan.
  Implementation must not start until the operator approves the recommended design.

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
