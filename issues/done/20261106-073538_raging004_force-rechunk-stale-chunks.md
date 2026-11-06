# Prune stale chunk files when force re-chunking reduces chunk count

## Priority
High

## Summary
`ChunkSplitter.process_file(force=True)` overwrites chunk files for indices below the new
chunk count but never removes leftover files from a previous run with a higher count. The
stale files pass the ingester's group validation (contiguous indices, identical shared
metadata) and are re-ingested alongside the new chunks, inserting obsolete content into
the RAG index.

## Background
- Sentinel skip is `chunk/{stem}-0000.json` only; the write loop writes
  `{stem}-{idx:04d}.json` for `idx` in the new chunk list and deletes nothing.
- Verified by reproduction: with `min_chunk = 40`, one run with `max_chunk = 200` wrote 16
  chunk files; a `force=True` rerun with `max_chunk = 600` wrote 4 files and left the 12
  stale files (indices 4-15) in `chunk/`. The merged group's `chunk_index` set was exactly
  `range(16)`, so `ingest_url_group`'s contiguity check passes and all 16 chunks — 12 of
  them stale — would be ingested.

### Verification (issue-to-plan cycle 20261106-101103)
- Reproduction re-run at HEAD `bdb9bed66` (`/tmp/opencode/raging004/repro.py`): run 1
  (`max_chunk=200`) wrote 20 files; forced run 2 (`max_chunk=600`) wrote 10 files and left
  all 20 files in `chunk/`; merged index set was exactly `range(20)` with uniform 9-field
  metadata — the merged group passes `ingest_url_group` validation. Stale-residue mechanism
  confirmed.
- Correction: at HEAD the stale group is currently unreachable by the ingester.
  `ChunkSplitter._build_chunk_payload` (`chunk_splitter.py:278-296`) omits `code_blocks`,
  while `read_chunk_json` requires it (`pipeline_utils.py:164-182`);
  `ChunkGroupingStrategy.group` silently skips every such file (`except ChunkFormatError:
  continue`, `chunk_grouping.py:30-31`) — empirically 0 groups formed from 20 real
  ChunkSplitter files. The corruption path this issue describes becomes live again as soon
  as that payload/validator mismatch is fixed; the mismatch itself is a new defect outside
  this issue's scope (new issue candidate, reported in the plan).
- New finding: the zero-chunk edge — a forced run whose new series is empty early-returns
  in `_write_chunk_files` (`chunk_splitter.py:244-245`) and must still prune the old series
  for the forced run to be authoritative.
- No existing test masks this: `rg force tests/rag/ingestion/test_chunk_splitter.py` shows
  force tests assert only written counts; nothing pins stale-file presence or absence.
- Production observation: `/opt/llm/rag-src/chunk/` was empty at verification time (no live
  residue to migrate).

## Problem
Any config change (or code change) that reduces chunk count for an already-chunked
document silently re-ingests obsolete chunks on the next ingestion; the DB then mixes
current and stale chunks under one document.

## Reason for Change
Silent data corruption path in a supported operational flow (`--force` is the documented
re-processing mechanism).

## Implementation Intent
Make force re-chunking authoritative for the document's chunk set: when a forced run
writes a new chunk series, remove leftover `{stem}-*.json` files in `chunk/` whose index
is outside the new series (or clear the stem's series before writing). Keep
non-forced behavior unchanged.

## Target Files or Areas
- `scripts/rag/ingestion/chunk_splitter.py`
- `tests/rag/ingestion/test_chunk_splitter.py`

## Required Changes
- On `force=True`, delete existing chunk files matching the source stem before (or after)
  writing the new series, so the on-disk series exactly matches the produced chunks.
- Add a regression test: chunk count shrinks under `force=True`; assert only the new
  series remains in `chunk/` and the ingester-visible index set equals the new count.

## Constraints
- Only files with the exact `{stem}-NNNN.json` pattern of the re-processed source may be
  removed; never touch other stems' files.
- Non-forced runs must keep the sentinel skip behavior unchanged.
- Files already moved to `registered/` are out of this issue's reach.

## Acceptance Criteria
- After a force re-chunk that produces fewer chunks, `chunk/` contains exactly the new
  series (verified by test).
- Group validation contiguity reflects only current-series files.
- No behavior change for non-forced runs or other sources' files.

## Testing Expectations
- Regression test for count-shrink and count-grow force runs.
- Integration check through `ChunkGroupingStrategy` + group validation on a forced rerun.
- `uv run pytest tests/rag/ingestion`.

## Documentation Impact
State in the ingestion docs that force re-chunking replaces the document's full chunk
series in `chunk/` (operational note level).

## Out of Scope
- Removing already-ingested stale rows from the DB (a separate data-repair concern).
- Group-validation routing changes (`20261106-073538_raging003_recrawled-chunk-group-poisoning.md`).

## Dependencies
- N/A: none

## Unresolved Questions
- Whether `registered/` copies from the earlier run should be flagged or archived when a
  forced re-chunk supersedes them.
  Resolved in the plan: out of scope. `registered/` accumulation is a separately documented
  retention concern (`docs/21_rag/rag_02_01_ingestion_pipeline-overview.md` Retention note);
  the ingester's replace path already makes the DB state reflect the new series, and no
  flagging mechanism is added by this fix.

## AI Implementation Instruction
Limit cleanup to the exact stem pattern of the forced source file; do not add a general
directory sweep. Keep the deletion inside the chunk-writing responsibility of
`ChunkSplitter`.

## Traceability
- **Workflow phase**: python-code-review
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20261106-073538
- **Related target files**: `scripts/rag/ingestion/chunk_splitter.py`, `tests/rag/ingestion/test_chunk_splitter.py`
