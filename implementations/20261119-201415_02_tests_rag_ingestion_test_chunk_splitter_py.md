## Goal

Preserve the existing `process_all` integer assertions and add `run_all` skip/fail-count + distinct-exception-log unit tests and `main` exit-status tests for the all-failed and all-skipped cases (`REQ-001`, `REQ-003`, `REQ-005`).

## Scope
**Release unit**: N/A: not part of a release unit

## Assumptions
- `process_all` has 12 call sites in this file (e.g. lines 740, 755, 768, 780, 798, 824, 873, 927, 967, 1391, 1457, 1513 in the plan's evidence); several assert on the integer return (`total >= 2`, `total == 1`, `result >= 1`). These must stay unchanged (`REQ-005`).
- `test_process_all_logs_one_error_on_write_failure` (line 1501) builds a real splitter via `_make_prune_splitter(tmp_path)`, patches `_build_chunk_list` to return 5 chunks, applies `_patch_write_bytes(fail_on=3)`, and asserts `result == 0` and `mock_logger.exception.assert_called_once()`. This is the regression anchor: the narrowed `except` must still log once and `process_all` must still return `0`.
- `_make_splitter` (line 25) and `_make_ja_mixin` (line 175) use `object.__new__` + private-attr assignment; these are reworked by `ragcrv006` (Phase 5). For ragcrv007, keep them as-is unless a new test needs a different construction — do not fold in the broader `ragcrv009` cleanup (`UNK-03`).
- Cross-plan overlap: `test_chunk_splitter.py` is also targeted by `ragcrv006` (construction-seam rework; sequencing dependency, verified compatible — different concerns). Coordinate so ragcrv006's `_make_splitter`/`_make_ja_mixin` changes do not break ragcrv007's new `run_all`/`main` tests.

## Design decisions
- Keep every existing `process_all` assertion byte-for-byte; the new `_iter_file_outcomes` iterator (row 1) preserves `process_all`'s exact behavior, so these stay green (`REQ-005`).
- Add a `run_all` unit test: one failing file + one valid file → `result.failed == 1`, `result.processed == 1` (or the correct split), and the failing file's logged exception class is asserted via a captured logger (`REQ-001`, `REQ-002`).
- Add `main` exit-status tests via monkeypatched `sys.argv` / `ConfigLoader`: all-failed run exits non-zero (`1`) reporting the failure count; all-skipped run exits `0` reporting the skip count (`REQ-003`).
- Add a mixed pass/fail test asserting the continue policy: one failing file does not stop the remaining files from processing (`REQ-004`).

## Alternatives considered
- Reusing `_make_prune_splitter`/`_patch_write_bytes` helpers for the new tests vs. new fixtures: reuse existing helpers to minimize new scaffolding; chosen.
- Testing `main`'s exit code via `sys.exit` raising `SystemExit` vs. asserting the returned int: assert the returned int from `main()` directly (cleaner than capturing `SystemExit`); record the choice in the procedure's Method.

## Implementation
### Target file
`tests/rag/ingestion/test_chunk_splitter.py`

### Procedure
1. Do not modify any existing `process_all` assertion (lines 740–824, 873, 927, 967, 1391, 1457, 1513).
2. Add a `run_all` skip/fail-count test using `_make_prune_splitter` + `_patch_write_bytes` for the failing file and a valid source for the processed file; assert distinct `processed`/`skipped`/`failed` counts and capture the logger to assert the failing file's exception class was logged (`REQ-001`, `REQ-002`).
3. Add `main` exit-status tests for the all-failed (non-zero) and all-skipped (`0`) cases via monkeypatched `sys.argv` / `ConfigLoader` (`REQ-003`).
4. Add a mixed pass/fail test asserting the continue policy (`REQ-004`).

### Method
- Model the new tests on `test_process_all_logs_one_error_on_write_failure` (line 1501): same splitter construction, same write-failure patching, same logger-capture pattern.
- For `main` tests, monkeypatch `sys.argv` and `ConfigLoader` so no real TOML/dictionary is required.

### Details
- Grep the file for all `process_all` call sites before editing to confirm the full list; ensure the new tests do not accidentally alter an existing assertion.
- Keep changes scoped to the construction seam and the new tests; do not touch unrelated fragility cleanup (`ragcrv009`).

## Compatibility considerations
- Test-only change; production code untouched by this row (`REQ-005`).
- Must remain compatible with `ragcrv006`'s `_make_splitter`/`_make_ja_mixin` rework (sequencing dependency).

## Security considerations
N/A: test construction only.

## Rollback considerations
N/A: revert the commit.

## Validation plan
- Regression: `uv run pytest tests/rag/ingestion/test_chunk_splitter.py` — existing `result == 0` / `>= 1` assertions pass (`REQ-005`).
- Unit: `run_all` skip/fail counts distinct; exception class logged per file (`REQ-001`, `REQ-002`).
- Unit: `main` exit status all-failed → non-zero; all-skipped → `0` (`REQ-003`).
- Regression: whole `tests/rag/ingestion/` suite green (`REQ-004`).

## Completion criteria
- Existing `process_all` assertions unchanged and green; `run_all` skip/fail-count + distinct-exception-log tests present; `main` exit-status tests for all-failed/all-skipped present; continue-policy test present.

## Out of Scope
- Narrowing `process_all`'s except and adding `run_all` in source — row 1.
- The ragcrv006 construction-seam rework and the broader `ragcrv009` cleanup.
- Editing `scripts/rag/exceptions.py`.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | |
| 2 | Add or update tests per Validation plan | Pending | — | — | |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Pending | — | — | |

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
- **Requirement ID**: `REQ-001` (`run_all` tests), `REQ-003` (`main` exit-status tests), `REQ-005` (preserve integer assertions)
- **Source issue**: `issues/20261119-112019_ragcrv007_chunk-failure-exit-reporting.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261119-191233_ragcrv007_chunk-failure-exit-reporting.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261119-201415
- **Related target files**: `tests/rag/ingestion/test_chunk_splitter.py`
