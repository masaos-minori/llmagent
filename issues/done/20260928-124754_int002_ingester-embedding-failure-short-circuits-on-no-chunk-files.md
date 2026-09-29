# RagIngester embedding-failure test short-circuits before reaching the mocked failure

## Priority
Medium

## Summary
`tests/integration/test_ingestion_e2e.py::TestFullIngestionPipeline::test_ingester_handles_embedding_failure` fails: the test mocks `_process_url_groups` to raise `Exception("Embedding API unavailable")` and expects `ingester.ingest_all()` to propagate it, but no exception is raised — the captured log shows `"No chunk files to process"`, indicating `ingest_all` returns early before ever calling the mocked method.

## Background
Discovered during the post-docs-reorg full-suite validation re-check (`implementations/20260925-111411_04_tests___full_suite_.md`, Execution Status Step 3). A prior run of this same procedure (20260927) filed `rag001` for a related RAG config-validation failure, since resolved (`issues/done/`); a re-run today found 4 remaining failures, of which this is one — likely a fixture/environment gap rather than a related regression.

## Problem
The test configures `mock_cfg = {"rag_src_dir": "/tmp/crawl-test-chunks", ...}` (`tests/integration/test_ingestion_e2e.py:96-99`) but does not appear to create any chunk files under that directory. `RagIngester.ingest_all()` (`scripts/rag/ingestion/ingester.py:141`) logs `"No chunk files to process"` and returns before reaching `_process_url_groups` (line ~166), so the mocked `side_effect=Exception("Embedding API unavailable")` on `_process_url_groups` is never triggered, and `pytest.raises(Exception, match="Embedding API unavailable")` fails with "DID NOT RAISE".

## Reason for Change
The test's own docstring states its intent is "Ingestion handles embedding API failure gracefully" — as currently written it does not actually exercise that path, since `ingest_all` never reaches the embedding call. Left as-is, a real regression in embedding-failure handling would not be caught by this test.

## Implementation Intent
Confirm the exact precondition `ingest_all` requires before it proceeds to `_process_url_groups` (i.e. what makes it consider "chunk files to process" present) and adjust the test fixture to satisfy that precondition (e.g. create a chunk file under `rag_src_dir`, or mock the chunk-discovery step) so the mocked `_process_url_groups` failure is actually reached.

## Target Files or Areas
- `tests/integration/test_ingestion_e2e.py` (`test_ingester_handles_embedding_failure`, line ~91)
- `scripts/rag/ingestion/ingester.py` (`ingest_all`, lines ~141-166 — the "no chunk files" short-circuit)

## Required Changes
- Update the test fixture/setup so `ingest_all` finds at least one chunk file (or otherwise passes the pre-`_process_url_groups` guard) before mocking `_process_url_groups` to fail.
- Confirm the test then actually exercises the embedding-failure propagation path end-to-end.

## Constraints
Do not change `ingest_all`'s "no chunk files" short-circuit behavior itself — this is a test-setup gap, not a claim that the short-circuit is wrong.

## Acceptance Criteria
- The listed test passes, and does so by genuinely reaching `_process_url_groups` (not by weakening the assertion).

## Testing Expectations
Run `uv run pytest tests/integration/test_ingestion_e2e.py -v -k test_ingester_handles_embedding_failure`; run full suite once after the fix.

## Documentation Impact
N/A: no `docs/*.md` task-scope mapping identified for this test-fixture-only gap.

## Out of Scope
The other 3 failures found in the same full-suite re-check (docs-quality golden pairs, eventbus ack ownership, orchestrator config restore) — tracked as separate issues.

## Dependencies
N/A: none

## Unresolved Questions
Needs confirmation: the exact mechanism `ingest_all` uses to detect "chunk files to process" (file glob under `rag_src_dir`, a manifest, or something else) — determines the minimal fixture fix.

## AI Implementation Instruction
Fix the test fixture to genuinely reach the mocked failure path; do not simply remove or loosen the `pytest.raises` assertion.

## Traceability
- **Workflow phase**: issue-creator
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: implementations/20260925-111411_04_tests___full_suite_.md
- **Generated at**: 20260928-124754
- **Related target files**: tests/integration/test_ingestion_e2e.py, scripts/rag/ingestion/ingester.py
