## Goal

- Make a document's chunk set all-or-nothing: write every chunk under a temporary name, publish with `os.replace` in descending index order so the sentinel `-0000` appears last, remove all this-run outputs on any `OSError`, and clear leftover temporary files before writing (`REQ-001`..`REQ-005`: atomic chunk publish).

## Scope
**Release unit**: N/A: not part of a release unit

- `_write_chunk_files` and `process_file` in `scripts/rag/ingestion/chunk_splitter.py`, plus its companion test file.

## Assumptions

- Overlap check (Step 2 tool): no other Frozen Plan targets `chunk_splitter.py`; independent of the ragrev015/016 ingest-side plans (splitter stage runs before the ingester per the execution guide).
- The sentinel has no reader other than `process_file` (verified `is_already_processed` `pipeline_utils.py` L254-256 and `ingester.py` L158 globbing only `*.json`, so `*.json.tmp` is invisible to the ingester — Plan Background fact 3).
- Cleanup of leftover `{stem}-*.json.tmp` happens when the source is about to be written (skip path leaves the directory untouched), matching the REQ-004 wording "removed before writing".

## Design decisions

- Two small private helpers keep `_write_chunk_files` at radon A/B (Plan Design): a publish helper and a cleanup helper; `process_file` only gains the leftover-temp removal line.
- Publish order is descending index (`-0004` first, `-0000` last): a crash mid-publish can never show a sentinel with a gap (REQ-003).
- On failure: unlink every temp file and every final file published in this call, then re-raise so `process_all` logs one error per source (Plan Assumptions; `process_all` already catches `OSError` at L99-100).

## Alternatives considered

- Delete-everything-after-failed-direct-writes, temp-directory rename, separate completion marker: all rejected by the Plan Design Alternatives.

## Implementation
### Target file
- `scripts/rag/ingestion/chunk_splitter.py`

### Procedure
- Replace the direct per-chunk write loop with a two-phase write: all temp writes, then ordered publish; add cleanup on failure and leftover removal before writing.

### Method
- In `_write_chunk_files`: build all payloads as today; for each index write to `self._chunk_dir / f"{src_path.stem}-{idx:04d}.json.tmp"` (temp lives in the same directory, so `os.replace` is metadata-only — Plan Risks); collect `(temp_path, final_path)` pairs.
- Add private helper `publish_chunk_files` (new): iterate the pairs sorted by descending `idx` and `os.replace(temp, final)` each; return the count (replaces today's `written` counter, keeping the success-path return value = chunk count, REQ-005).
- Add private helper `cleanup_chunk_files` (new): unlink any still-present temp paths and any final paths this call published; used from a single `except OSError` around the write and publish phases, which calls it and then re-raises.
- In `process_file`: after the sentinel skip check and before reading the source, remove leftover files matching `f"{src_path.stem}-*.json.tmp"` in `chunk_dir` (REQ-004).

### Details
- No change to payload content, final names, `_prune_stale_chunk_files`, `--force` semantics, or the log lines on success (REQ-005).
- The success-path chunk count equals `len(chunks)` because publish failure never returns (cleanup + raise).

### Companion test files
- `tests/rag/ingestion/test_chunk_splitter.py`
  - Procedure: add one new test class (e.g. `TestAtomicChunkWrite` (new)) reusing `_make_prune_splitter` (L879): (1) `Path.write_bytes` patched to raise `OSError` on the third chunk of a five-chunk document → no `*.json`/`*.json.tmp` for that stem remains, exactly one error logged, then `process_file(src, force=False)` regenerates all 5 chunks and returns 5 (AC-1, AC-2); (2) `os.replace` instrumented to record call order → `-0000` last, and a publish-step `OSError` cleanup variant (AC-3); (3) seeded leftover `{stem}-0002.json.tmp` removed by the next run (AC-4); (4) a success-path case asserting names/contents/return value unchanged (AC-5).
  - Validation: `uv run pytest tests/rag/ingestion/test_chunk_splitter.py -q` — new tests fail on HEAD where behavior-dependent and pass after; `TestForceRechunkPrune` and `tests/rag/ingestion/test_rag_ingestion_pipeline.py` stay green unmodified.

## Compatibility considerations

- The chunk file format and final names are unchanged, so the ingester and every existing test that reads `chunk/*.json` by name is unaffected (AC-5).
- Documents briefly hold double entries (temp + final) during publish; `chunk/*.json` globbers never see `.json.tmp` names.

## Security considerations
N/A: file-system write protocol on an existing directory; cleanup only unlinks this run's own outputs.

## Rollback considerations
N/A: revert the single commit; leftover `*.json.tmp` files from new-code runs are invisible to the old code and are harmless, but can be deleted manually after a revert.

## Validation plan

- `uv run pytest tests/rag/ingestion/test_chunk_splitter.py -q` — new tests fail on HEAD, pass after.
- `uv run pytest tests/rag/ingestion -q` regression (AC-5).
- `uv run ruff check`, `uv run mypy`, `PYTHONPATH=scripts uv run lint-imports`.

## Completion criteria

- AC-1..AC-5 hold: a write or publish error leaves no partial or temp output and logs one error; a non-forced rerun regenerates the full set; the sentinel is published last; leftover temps are removed; success-path names, contents, and return value are unchanged.

## Out of Scope

- Serializing splitter/ingester stages, group-validation rules in the ingester, `--force` pruning, final file names (Plan Out-of-Scope).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | |
| 2 | Add companion tests per Companion test files | Pending | — | — | Companion: `tests/rag/ingestion/test_chunk_splitter.py` |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| — | — | — | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| — | — | — | — | — | — |

## Traceability
- **Workflow phase**: plan-to-implementation-procedure
- **Requirement ID**: `REQ-001`..`REQ-005` (atomic chunk write, rerun recovery, sentinel-last publish, leftover cleanup, unchanged success path)
- **Source issue**: issues/20261108-131236_ragrev017_partial-chunk-write-gap.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261108-170859_ragrev017_partial-chunk-write-gap.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261109-234702
- **Related target files**: `scripts/rag/ingestion/chunk_splitter.py`, `tests/rag/ingestion/test_chunk_splitter.py`
