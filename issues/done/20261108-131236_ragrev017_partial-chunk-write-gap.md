# A chunk file write error leaves an index gap that is never regenerated

## Priority
Medium

## Summary
`ChunkSplitter._write_chunk_files` logs and skips an `OSError` on one chunk, which leaves a hole in the chunk indices, while `process_file` skips a source whenever the first chunk file exists and `force` is false, so the missing chunk is not regenerated.

## Background
Review finding F-017 (Confidence Low: not reproduced; the interaction with a concurrently running ingester was not verified). Evidence: `scripts/rag/ingestion/chunk_splitter.py` `_write_chunk_files` continues after a write `OSError`; `process_file` uses the `{stem}-0000.json` file as its sentinel; the ingester rejects a group whose `chunk_indices` differ from the expected contiguous range (`GROUP_VALIDATION_FAILED`). If the ingester runs while the splitter is still writing, indices 0..k can look contiguous and a truncated document could be committed as complete; whether the stages are serialized was not checked.

## Problem
A transient disk error produces a permanently invalid chunk group, and a race could ingest a truncated document.

## Reason for Change
Partial output should either be completed or removed so the next run can recover without a forced re-chunk.

## Implementation Intent
Write each document's chunk files atomically (write to a temporary name and rename, or write all then publish the sentinel last), and remove partial output on failure.

## Target Files or Areas
- `scripts/rag/ingestion/chunk_splitter.py` (`_write_chunk_files`, `process_file`)
- `scripts/rag/ingestion/ingester.py` (group validation)
- `tests/rag/ingestion/`

## Required Changes
- Publish a document's chunk files only when all were written (sentinel last or temp directory then rename).
- Clean up partial files on error.
- Add a test that injects an `OSError` for one chunk.

## Constraints
- Keep the chunk file format and naming.
- Do not change the ingester validation rules.

## Acceptance Criteria
- After an injected write error, no partial chunk set remains and the next run regenerates the document without `--force`.
- The ingester never sees a partially written document.

## Testing Expectations
- Unit test with a patched writer raising `OSError` mid-document.
- ruff and mypy.

## Documentation Impact
N/A: no documentation change expected.

## Out of Scope
- Serializing the splitter and ingester stages.

## Dependencies
N/A: none

## Unresolved Questions
Whether the pipeline serializes the splitter and the ingester, and whether the sentinel-first behavior is relied on elsewhere, is `Needs confirmation`.

## AI Implementation Instruction
Keep the change minimal and confined to the Target Files or Areas. Do not rewrite unrelated files, keep public behavior unchanged unless Required Changes says otherwise, and do not implement items listed under Out of Scope. Add the tests named in Testing Expectations before or with the fix. If a requirement is unclear, stop and report the open question instead of guessing.

## Traceability
- **Workflow phase**: python-code-review
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20261108-131236
- **Related target files**: `scripts/rag/ingestion/chunk_splitter.py`, `scripts/rag/ingestion/ingester.py`, `tests/rag/ingestion/`
