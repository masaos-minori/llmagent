## Goal
- Make a document's chunk set all-or-nothing: `ChunkSplitter` writes every chunk of a document under a temporary name, publishes the final names only after all writes succeeded (the `{stem}-0000.json` sentinel last), and removes partial output on any failure, so a disk error never leaves a gapped set that the next non-forced run skips.

## Priority
Medium

## Scope
- **In-Scope**:
  - `ChunkSplitter._write_chunk_files` and `process_file` in `scripts/rag/ingestion/chunk_splitter.py`: temp-name writes, publish with the sentinel last, cleanup of partial and leftover temporary files, and a single clear error report on failure.
  - A test that injects an `OSError` for one chunk (and one for the publish step), asserting no partial set remains and a non-forced rerun regenerates the document.
  - The `ChunkSplitter` description of the sentinel in the RAG docs.
- **Out-of-Scope**:
  - Serializing the splitter and ingester stages, ingester group-validation rules, the chunk file format and final names, `--force` semantics (`_prune_stale_chunk_files` stays as is).
- **Dependencies**: N/A: none.

## Background
Review finding F-017 (Confidence Low in the Issue; not reproduced there, and not reproduced here). `_write_chunk_files` (`scripts/rag/ingestion/chunk_splitter.py:276-300`) writes `{stem}-{idx:04d}.json` in index order and, on an `OSError`, logs and continues, so index `k` can be missing while the sentinel `{stem}-0000.json` (index 0, written first) exists; `process_file` (L104-135) skips the source when the sentinel exists and `force` is false (`is_already_processed`, `pipeline_utils.py:254-256`), so the gap is never regenerated, and the ingester rejects the group with `GROUP_VALIDATION_FAILED` because the indices are not the contiguous range. Facts verified while reading (checked in Step 3): (1) the stages are run sequentially by the operator (`docs/21_rag/rag_05_02-execution-guide.md` Steps 1-3; `deploy/setup_services.sh` only prints the commands); no repository automation runs the splitter and the ingester concurrently, so the Issue's truncation race requires overlapping manual runs, and serialization stays out of scope; (2) the sentinel is only used by `process_file` (no other reader of `-0000` besides tests that create chunk files); (3) the ingester globs `chunk/*.json` (`ingester.py:158`), so files named `*.json.tmp` are invisible to it; (4) `write_bytes` is a plain non-atomic write, so a crash can also leave a truncated single file, which the temp-name-then-`os.replace` publish avoids.

## Problem
A transient disk error produces a permanently invalid chunk group that needs `--force` to repair, and overlapping stage runs could ingest a truncated document.

## Reason for Change
Partial output should either be completed or removed so the next run recovers without a forced re-chunk.

## Implementation Intent
Write all chunk files as `{name}.json.tmp`, then publish with `os.replace` in descending index order so the sentinel (`-0000`) becomes visible last; on any `OSError` remove the temporary files and any final files already published for this stem in this call, and re-raise so `process_all` logs one error. At the start of a document's processing remove leftover `{stem}-*.json.tmp` files from a crashed earlier run.

## Requirements
- `REQ-001`: A write error for any chunk leaves no chunk file (temporary or final) of that document from this run, and the failure is logged once at error level.
- `REQ-002`: After such a failure, a non-forced rerun regenerates the full chunk set (no sentinel exists, so the source is not skipped).
- `REQ-003`: Final files are published only after every temporary write succeeded; the sentinel `{stem}-0000.json` is published last.
- `REQ-004`: Leftover `{stem}-*.json.tmp` files from an interrupted run are removed before writing.
- `REQ-005`: The chunk file format, final names, `--force` pruning, and the success-path return value (number of chunks written) are unchanged.
- `REQ-006`: The ChunkSplitter documentation states that the sentinel is published last and therefore marks a complete set.

## Implementation Target Files
**Freeze status**: Frozen

| File Path | Change Responsibility | Reason for Modification | Related Requirement / Acceptance Criterion | Repository Evidence | Related Tests | Validation Status |
|---|---|---|---|---|---|---|
| `scripts/rag/ingestion/chunk_splitter.py` | Modify | Temp-name writes, sentinel-last publish, cleanup, leftover removal in `_write_chunk_files` and `process_file` | `REQ-001`..`REQ-005` / AC-1..AC-5 | `OSError` is logged and skipped at L299-300; sentinel semantics at L104-117 (checked in Step 3) | `tests/rag/ingestion/test_chunk_splitter.py` | Verified |
| `tests/rag/ingestion/test_chunk_splitter.py` | Modify | New test class: injected write error, injected publish error, rerun regeneration, leftover temp removal, success-path unchanged | `REQ-001`..`REQ-005` / AC-1..AC-5 | Existing helpers `_make_prune_splitter` (L879) and prune tests (L923+) (checked in Step 3) | self | Verified |
| `docs/21_rag/rag_02_03_ingestion_pipeline-chunksplitter.md` | Modify | Idempotency sentence (L33): the sentinel is published last and marks a complete set | `REQ-006` / AC-6 | L33 states "if a `{stem}-0000.json` sentinel exists, processing is skipped" without completeness (checked in Step 3) | docs gates | Verified |

## Reference Files
| File Path | Why It Must Be Read | Related Target File or Requirement |
|---|---|---|
| `scripts/rag/ingestion/pipeline_utils.py` | `is_already_processed` (L254-256) and `collect_source_files` | `REQ-002` |
| `scripts/rag/ingestion/ingester.py` | `chunk_dir.glob("*.json")` (L158) and the contiguous-index group validation; unchanged | `REQ-003`, `REQ-005` |
| `docs/21_rag/rag_05_02-execution-guide.md` | Documents the sequential operator steps | Scope |
| `tests/rag/ingestion/test_rag_ingestion_pipeline.py` | End-to-end tests that create chunk files by name; must stay green | `REQ-005` |

## Acceptance Criteria
- AC-1 (`REQ-001`): with `Path.write_bytes` (or the replace step) failing for the third chunk of a five-chunk document, no `*.json` or `*.json.tmp` file for that stem remains in the chunk directory and one error is logged.
- AC-2 (`REQ-002`): the following `process_file(src, force=False)` writes all five chunks and returns 5.
- AC-3 (`REQ-003`): during publish, the `-0000` file is the last to appear (asserted with an instrumented replace order).
- AC-4 (`REQ-004`): a pre-existing `{stem}-0002.json.tmp` is removed by the next run and does not appear after a successful run.
- AC-5 (`REQ-005`): existing `TestForceRechunkPrune`, end-to-end, and pipeline tests pass unmodified; the success-path return value and file contents are unchanged.
- AC-6 (`REQ-006`): the doc names the publish order; docs checkers pass.

## Tests
- `REQ-001`/`REQ-002`: patched writer raising `OSError` for one chunk, then a clean rerun.
- `REQ-003`: instrumented `os.replace` order; publish-step `OSError` cleanup.
- `REQ-004`: seeded leftover temp file.
- `REQ-005`: existing suites unmodified.
- Static: `uv run ruff check`, `uv run mypy`; `uv run pytest tests/rag/ingestion -q`.

## Documentation Impact
Yes (`REQ-006`): `docs/21_rag/rag_02_03_ingestion_pipeline-chunksplitter.md` (located via `docs/00_index.md` RAG rows), intent and failure behavior only. Run `check_docs_quality`, `check_docs_structure`, `check_docs_content_policy`, `check_docs_consistency --domain rag`, `check_docs_japanese`.

## Assumptions
- The operator runs the splitter and the ingester one after the other (execution guide); concurrent runs are not supported and are not made worse. The sentinel-last order narrows the visible window of a partially published set but does not make the publish phase atomic across files.
- A re-raise after cleanup is acceptable for the caller: `process_all` already catches `OSError` and logs it per source (`chunk_splitter.py:99-100`), and a direct `process_file` caller sees the error instead of a silent short count.

## Unknowns
| ID | Unknown Description | Evidence Missing | Resolution Path | Blocking? (True/False) |
|---|---|---|---|---|
| UNK-01 | Whether any tool or operator script relies on the sentinel being written first | Search found no other code reader (only `process_file` and tests); operator scripts outside the repo are not visible | Non-blocking; the doc update states the new meaning | False |
| UNK-02 | Whether overlapping stage runs occur in practice | Production operation not inspected | Out of scope (serialization); the Plan reduces the partial-set window only | False |

## Affected areas
| File | Change | Blast Radius | Churn (30d) | Bus Factor | deploy.sh Impact |
|---|---|---|---|---|---|
| `scripts/rag/ingestion/chunk_splitter.py` | Modify | Medium (every chunked document; `radon`: `process_file` B (7), `_write_chunk_files` A (4)) | 5 | N/A | not applicable (rsynced) |
| `tests/rag/ingestion/test_chunk_splitter.py` | Modify | Low | N/A | N/A | not applicable (rsynced) |
| `docs/21_rag/rag_02_03_ingestion_pipeline-chunksplitter.md` | Modify | Low | N/A | N/A | not applicable (rsynced) |

## Design
Path A (3 target files, no public interface or schema change: final file names and payload format are unchanged, only the write protocol is). Complexity: the publish and cleanup logic goes into two small private helpers so `_write_chunk_files` stays at A or B.

Alternatives: (a) write finals directly and delete everything on error, rejected (a crash mid-way still leaves a sentinel plus a gap); (b) a temporary directory renamed as a whole, rejected (the ingester reads one flat directory and the per-file names must stay in `chunk/`); (c) a separate completion marker file, rejected (adds a new artifact the ingester would have to understand). Chosen: temp names, sentinel published last, cleanup on failure.

Persisted schema check: not applicable.

Validation baseline: `radon cc` recorded above; `vulture`/`bandit` pre-existing findings recorded in `plans/20261108-164302_ragrev001_mqe-malformed-response-abort.md` (source unchanged); `diff-cover`: no changed lines at plan time, 90 percent at implementation.

## Implementation steps
1. **Phase 1: Tests first**
   - [ ] Injected write error and rerun, injected publish error, publish order, leftover temp, and success-path tests (`REQ-001`..`REQ-005`; `tests/rag/ingestion/test_chunk_splitter.py`)
2. **Phase 2: Atomic publish**
   - [ ] Temp writes, sentinel-last publish, cleanup, leftover removal (`REQ-001`..`REQ-005`; `scripts/rag/ingestion/chunk_splitter.py`)
3. **Phase 3: Documentation**
   - [ ] State the sentinel-last rule (`REQ-006`; `docs/21_rag/rag_02_03_ingestion_pipeline-chunksplitter.md`)
4. **Phase 4: Deployment & Verification**
   - [ ] `uv run pytest tests/rag/ingestion -q`, lint/type gates, docs gates; deploy hand-off to `skills/deploy/SKILL.md` after commit and push, at the user's decision (all requirements; `scripts/rag/ingestion/chunk_splitter.py`)

### Release units
N/A: no release unit

## Validation plan
| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| `scripts/rag/ingestion/chunk_splitter.py` | Unit (temp dir, injected `OSError`) | `uv run pytest tests/rag/ingestion/test_chunk_splitter.py -q` | new tests fail on HEAD, pass after |
| chunk pipeline | Regression | `uv run pytest tests/rag/ingestion -q` | green |
| touched code | Static | `uv run ruff check`, `uv run mypy`, `PYTHONPATH=scripts uv run lint-imports` | clean |
| docs | Docs gates | `uv run python tools/check_docs_quality.py`, `check_docs_structure.py`, `check_docs_content_policy.py`, `check_docs_consistency.py --domain rag`, `check_docs_japanese.py` | no findings |

## Risks
- **Risk**: documents with many chunks double their write I/O briefly (temp then rename) → **Mitigation**: rename is metadata-only on the same filesystem; cost is negligible next to chunking.
- **Risk**: temp and final names must be on the same filesystem for atomic `os.replace` → **Mitigation**: temp files live in the same `chunk/` directory.
- **Risk**: cleanup after a failed publish removes finals published in this call but could remove a previous run's final of the same name that was overwritten → **Mitigation**: a failed run leaves no sentinel, so the next run regenerates the whole set anyway; removal of this run's partial finals is the intended state.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Phase 1: tests first | Pending | — | — | |
| 2 | Phase 2: atomic publish | Pending | — | — | |
| 3 | Phase 3: documentation | Pending | — | — | |
| 4 | Phase 4: deployment and verification | Pending | — | — | |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| — | — | — | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| — | — | — | — | — | — |

## Traceability
- **Workflow phase**: issue-to-plan
- **Source issue**: issues/20261108-131236_ragrev017_partial-chunk-write-gap.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: this document is the generated plan
- **Source implementation procedure**: N/A: not applicable in this phase
- **Generated at**: 20261108-170859
- **Related target files**: `scripts/rag/ingestion/chunk_splitter.py`, `tests/rag/ingestion/test_chunk_splitter.py`, `docs/21_rag/rag_02_03_ingestion_pipeline-chunksplitter.md`

### Requirement Traceability
| Requirement ID | Source Issue section or evidence | Target file | Implementation step | Acceptance criterion | Test or validation item | Status |
|---|---|---|---|---|---|---|
| REQ-001 | Required Changes 2; `chunk_splitter.py:299-300` | `scripts/rag/ingestion/chunk_splitter.py` | Phase 2 | AC-1 | injected write-error test | Confirmed by repository evidence |
| REQ-001 | Testing Expectations | `tests/rag/ingestion/test_chunk_splitter.py` | Phase 1 | AC-1 | injected write-error test | Explicit in issue |
| REQ-002 | Acceptance Criteria 1 | `scripts/rag/ingestion/chunk_splitter.py` | Phase 2 | AC-2 | rerun regeneration test | Explicit in issue |
| REQ-002 | Acceptance Criteria 1 | `tests/rag/ingestion/test_chunk_splitter.py` | Phase 1 | AC-2 | rerun regeneration test | Explicit in issue |
| REQ-003 | Required Changes 1 (sentinel last); `process_file` sentinel L104-117 | `scripts/rag/ingestion/chunk_splitter.py` | Phase 2 | AC-3 | publish-order test | Explicit in issue |
| REQ-003 | Required Changes 1 | `tests/rag/ingestion/test_chunk_splitter.py` | Phase 1 | AC-3 | publish-order test | Explicit in issue |
| REQ-004 | Step 3 finding: crashes can leave temp files | `scripts/rag/ingestion/chunk_splitter.py` | Phase 2 | AC-4 | leftover temp test | Derived from confirmed evidence |
| REQ-004 | Step 3 finding | `tests/rag/ingestion/test_chunk_splitter.py` | Phase 1 | AC-4 | leftover temp test | Derived from confirmed evidence |
| REQ-005 | Constraints | `scripts/rag/ingestion/chunk_splitter.py` | Phase 2 | AC-5 | existing chunk splitter suites | Explicit in issue |
| REQ-005 | Constraints | `tests/rag/ingestion/test_chunk_splitter.py` | Phase 1 | AC-5 | existing chunk splitter suites | Explicit in issue |
| REQ-006 | Documentation Impact (corrected: doc L33 describes the sentinel) | `docs/21_rag/rag_02_03_ingestion_pipeline-chunksplitter.md` | Phase 3 | AC-6 | docs gates | Confirmed by repository evidence |
