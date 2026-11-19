## Goal

Add the `ChunkRunResult` (new) aggregate and a private per-file outcome iterator to `chunk_splitter.py`, narrow `process_all`'s `except` tuple to the specific classes each failure path raises, map failures to the existing `IngestionFailureReason` vocabulary, add a `run_all` (new) entry point returning the aggregate, and switch `main()` to `run_all` (new) with a non-zero exit code on failure (`REQ-001`, `REQ-002`, `REQ-003`, `REQ-004`, `REQ-006`).

## Scope
**Release unit**: N/A: not part of a release unit

## Assumptions
- `process_all(self, target, force) -> int` (lines 140–153) sums `process_file` returns inside `except (OSError, RuntimeError, ValueError)` (line 150) and logs once via `logger.exception` (line 151); it must keep returning the integer total (`REQ-005`).
- The failure-bearing paths reaching the handler are exactly: `OSError` re-raised from `_write_chunk_files` on a write/publish failure, and `TokenizationError` (`RuntimeError`) raised by the Japanese normalization path. `_read_source_data` already catches `FileNotFoundError`/`ChunkFormatError` and returns `None` (a skip, not a failure) — those never reach the handler.
- `main() -> None` (lines 499–522) calls `splitter.process_all(target, args.force)` and discards the return; the `__main__` guard (lines 525–527) calls `main()` without `sys.exit`, so the process always exits `0`.
- `IngestionFailureReason` (a `StrEnum` in `scripts/rag/exceptions.py`) already exposes `PARSE_FAILED`, `VALIDATION_FAILED`, `STORAGE_FAILED`, `UNEXPECTED_FAILURE` (and `GROUP_VALIDATION_FAILED`) — enough to map the chunk-stage classes without editing `exceptions.py` (Out-of-Scope).
- `UNK-02`: no wrapper script exists in the repo, so the default non-zero exit code is `1`.
- Cross-plan overlap: `chunk_splitter.py` is also targeted by `ragcrv006` (settings value object + tokenizer `Protocol` in `__init__`; sequencing dependency, verified compatible — disjoint regions: construction vs. `process_all`/`main`). Verify at implementation that ragcrv006's `__init__` edits do not disturb `process_all`/`main`.

## Design decisions
- Refactor `process_all` to drive a private `_iter_file_outcomes(paths) -> Iterator[FileOutcome]` that classifies each file as `processed` (≥1 chunk written), `skipped` (returned 0 legitimately: already-chunked, unreadable, below-`min_chunk`), or `failed` (exception raised); on failure it maps the exception class to an `IngestionFailureReason` and logs the class distinctly via `logger.exception`.
- `process_all` keeps summing the `processed` chunk counts from the iterator and returns the `int` total — signature and contract unchanged (`REQ-005`).
- Add `run_all(self, target, force) -> ChunkRunResult` consuming the same iterator to build the aggregate and log a run-level summary line.
- Define `ChunkRunResult` (new) and `FileOutcome` (new) as small dataclasses in `chunk_splitter.py` (importable; `UNK-01` resolved here to inline dataclasses).
- `main()` calls `run_all` (new), returns `1` when `result.failed > 0` else `0`, and the `__main__` guard becomes `sys.exit(main())` (`REQ-003`).

### Exception-class → reason mapping (UNK-03)
| Exception reaching `process_all` | `IngestionFailureReason` |
|---|---|
| `OSError` (write/publish) | `STORAGE_FAILED` |
| `ChunkFormatError` (if it ever reaches the handler) | `PARSE_FAILED` |
| `PipelineValidationError` | `VALIDATION_FAILED` |
| `TokenizationError` and any other | `UNEXPECTED_FAILURE` |

## Alternatives considered
- Changing `process_all`'s return type directly (cleaner API) vs. a new `run_all` (new) entry point: the plan sanctions either (`UNK-01`), but keeping the integer contract avoids rewriting the 12 existing test assertions (`REQ-005`); chosen.
- Inline dataclasses vs. moving `ChunkRunResult` (new) to `models_data.py`: the plan constrains only importability; `UNK-02` resolved to inline in `chunk_splitter.py`.

## Implementation
### Target file
`scripts/rag/ingestion/chunk_splitter.py`

### Procedure
1. Add `FileOutcome` (new) and `ChunkRunResult` (new) dataclasses near the top (after imports) exposing `processed`/`skipped`/`failed` counts plus per-file reasons.
2. Add the private `_iter_file_outcomes(self, paths)` iterator: for each path, call `process_file`; on success classify `processed` with the returned count; on legitimate zero-return classify `skipped`; on exception map the class via the table above, record the reason, and `logger.exception(...)` with the class distinctly. Never raise out of the loop (continue policy, `REQ-004`).
3. Rewrite `process_all` (lines 140–153) to iterate `_iter_file_outcomes(self._collect_targets(target))` and sum the `processed` counts; keep the `No source files` early return and the final `done` log line; keep the `int` return.
4. Add `run_all(self, target=None, force=False) -> ChunkRunResult` building the aggregate from `_iter_file_outcomes` (new) and logging a run-level summary.
5. Change `main()` (lines 499–522): call `result = splitter.run_all(target, args.force)`, `return 1 if result.failed > 0 else 0`.
6. Change the `__main__` guard (lines 525–527) to `sys.exit(main())` (ensure `import sys`).

### Method
- Preserve `process_all`'s observable behavior byte-for-byte: same `logger.exception` call shape, same integer total, same continue-on-failure semantics. The iterator is shared so `process_all` and `run_all` (new) cannot diverge.
- Keep `ChunkSplitter`'s public API (`process_all`, `process_file`, …) unchanged; `run_all` (new) is purely additive.

### Details
- Confirm `sys` is imported (add `import sys` if absent) before using `sys.exit`.
- The zero-chunk (below-`min_chunk`) case must be classified `skipped`/`processed`, NOT `failed` — it returns 0 legitimately, it does not raise (`REQ-004`; depends on `ragcrv004`).
- Do not touch `exceptions.py` (Out-of-Scope); do not add retry or quarantine routing (Out-of-Scope).

## Compatibility considerations
- `process_all`'s signature and `int` return are unchanged; all 12 existing callers/tests stay valid (`REQ-005`).
- `main()` now returns an `int` instead of `None`; its return was previously discarded, so no caller observes a change except the new `sys.exit(main())` propagation (`REQ-003`).
- Cross-plan: verify ragcrv006's `__init__` edits do not disturb `process_all`/`main` regions.

## Security considerations
N/A: failure classification and exit code only.

## Rollback considerations
N/A: revert the commit.

## Validation plan
- Regression: `uv run pytest tests/rag/ingestion/test_chunk_splitter.py` — existing `result == 0` (`test_process_all_logs_one_error_on_write_failure`) and `>= 1` assertions pass unchanged (`REQ-005`).
- Unit: `run_all` (new) with one failing + one valid file returns distinct `skipped`/`failed` counts; the failing file's logged exception class is asserted (`REQ-001`, `REQ-002`).
- Unit: `main` exit status for all-failed (non-zero) and all-skipped (`0`) via monkeypatched `sys.argv`/`ConfigLoader` (`REQ-003`).
- Regression: whole `tests/rag/ingestion/` suite green (`REQ-004`).

## Completion criteria
- `ChunkRunResult` (new)/`FileOutcome` (new) present; `process_all` narrowed to the specific raised classes and still returns the `int`; `run_all` (new) returns the aggregate; `main` returns `1` on failure / `0` otherwise with `sys.exit(main())`; continue policy intact.

## Out of Scope
- Editing `scripts/rag/exceptions.py` — `IngestionFailureReason` already supplies the values.
- Retrying failed files; routing failures into ingestion quarantine.
- Changing which files are skipped vs processed.
- The ragcrv006 settings-value-object / tokenizer `Protocol` work in `__init__`.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 20261120-000445 | 20261120-000445 |  |
| 2 | Add or update tests per Validation plan | N/A | — | — | N/A: no test change in this procedure; run_all/main unit tests belong to seq 02 |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20261120-000445 | 20261120-000445 | ruff format/check, mypy, and tests/rag/ingestion/test_chunk_splitter.py (76 passed incl. test_process_all_logs_one_error_on_write_failure) |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | N/A | — | — | N/A: no doc change in this procedure; docs owned by seq 03 and 04 |

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
- **Requirement ID**: `REQ-001` (`ChunkRunResult` (new) + `run_all` (new)), `REQ-002` (narrowed except), `REQ-003` (exit code), `REQ-004` (continue policy), `REQ-006` (`IngestionFailureReason` mapping)
- **Source issue**: `issues/20261119-112019_ragcrv007_chunk-failure-exit-reporting.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261119-191233_ragcrv007_chunk-failure-exit-reporting.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261119-201415
- **Related target files**: `scripts/rag/ingestion/chunk_splitter.py`