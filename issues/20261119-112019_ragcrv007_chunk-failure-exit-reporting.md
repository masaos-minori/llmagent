# Chunk splitter failures are invisible to the run result

## Priority
Medium

## Summary
`ChunkSplitter.process_all` catches a broad exception set per file and `main()` returns no status, so a run
in which every file failed looks identical to a successful run: exit code 0 and a single total count.

## Background
- `process_all` wraps each `process_file` in `except (OSError, RuntimeError, ValueError)` and logs
  `logger.exception`, then returns the sum of chunks written.
- `scripts/rag/exceptions.py` derives every rag error from those two builtins: `ChunkFormatError(ValueError)`,
  `PipelineValidationError(RuntimeError)`, `TokenizationError(RuntimeError)`, `EmbeddingSchemaError(ValueError)`,
  `SearchQueryError(ValueError)`, `UnknownMetadataError(ValueError)`. One handler therefore absorbs every
  failure class with no distinction in the return value.
- `main()` calls `process_all` and returns `None`, so the process exits 0 regardless of failures.
- The file-level skip policy itself is documented and intended:
  `docs/10_adr/adr_02_06_009_rag-fts5-text-separation.md` INV-05 and
  `docs/21_rag/rag_05_04-error-handling-reference.md` ("the entire file is aborted; ERROR; continue to next
  file"), which the code matches.
- `docs/21_rag/rag_05_02-execution-guide.md` shows the three pipeline stages run as separate commands, so a
  chunk-stage failure does not stop the ingester stage from running on stale or missing chunks.

## Problem
Failures are recorded only in `chunk.log`. The stage result, exit status, and the following pipeline step
give no signal that the chunk stage produced nothing usable.

## Reason for Change
The pipeline is run as a sequence of manual or scripted stages, and the chunk stage is the one whose failure
mode is a silent empty corpus.

## Implementation Intent
Make the per-file outcome explicit and typed: classify each file as processed, skipped, or failed with a
reason, return an aggregate result, and exit non-zero when any file failed while keeping the documented
file-level continue policy.

## Target Files or Areas
- `scripts/rag/ingestion/chunk_splitter.py` (`process_all`, `main`)
- `scripts/rag/exceptions.py` (only if a failure-reason mapping is needed)
- `docs/21_rag/rag_05_02-execution-guide.md`, `docs/21_rag/rag_05_04-error-handling-reference.md`

## Required Changes
- Replace the broad tuple with the specific exception classes each failure path can raise, keeping each
  class distinguishable in the log.
- Return a structured aggregate (processed / skipped / failed counts with per-file reasons) instead of only
  a chunk total.
- Exit non-zero when one or more files failed.
- Reuse the existing `IngestionFailureReason` vocabulary where a reason maps to it.

## Constraints
- Must not turn the documented file-level skip into an abort of the whole run (ADR-009 INV-05).
- `process_all`'s existing return type is used by tests and by callers that expect an int chunk count; keep a
  compatible path or update those callers in the same change.
- Exit codes must stay compatible with how the stages are invoked in `deploy/setup_services.sh` and the
  execution guide.

## Acceptance Criteria
- A run where every file fails exits non-zero and reports the failure count.
- A run where files were legitimately skipped exits 0 and reports the skip count.
- Log records distinguish exception class per failed file.

## Testing Expectations
- Unit: `process_all` with one failing and one valid file returns distinct skip/fail counts.
- Unit: `main` exit status for the all-failed and all-skipped cases.
- Regression: existing `process_all` tests that assert the chunk total keep passing or are updated in the
  same commit.

## Documentation Impact
- `docs/21_rag/rag_05_04-error-handling-reference.md`: state the exit-status contract and the failure aggregate.
- `docs/21_rag/rag_05_02-execution-guide.md`: state what a non-zero chunk stage means for the ingester stage.

## Out of Scope
- Retrying failed files.
- Routing chunk-stage failures into the ingestion quarantine directories.

## Dependencies
- Related: issues/20261119-112016_ragcrv004_silent-chunk-discard-logging.md (the zero-chunk case the aggregate must distinguish from a failure).

## Unresolved Questions
- Which exit codes the operator's wrapper treats as failure — `Needs confirmation`; no wrapper script was
  found in the repository.

## AI Implementation Instruction
Keep the continue-on-error policy. Do not widen the except tuple further; enumerate the classes each path
actually raises and handle them separately.

## Traceability
- **Workflow phase**: `python-code-review` (finding `F-007`)
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20261119-112019
- **Related target files**: `scripts/rag/ingestion/chunk_splitter.py`, `scripts/rag/exceptions.py`, `docs/21_rag/rag_05_04-error-handling-reference.md`, `docs/21_rag/rag_05_02-execution-guide.md`
