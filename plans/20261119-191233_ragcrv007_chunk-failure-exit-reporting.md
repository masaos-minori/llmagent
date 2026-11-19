## Goal
Make the chunk stage's per-file outcome explicit and observable: classify each source file as processed, skipped, or failed with a typed reason, return a structured aggregate instead of only a chunk total, and exit non-zero when one or more files failed — while preserving the documented per-file continue policy and the existing `process_all` integer chunk-count contract.

## Priority
Medium

## Scope
- **In-Scope**:
  - Add a structured `ChunkRunResult` aggregate (`processed` / `skipped` / `failed` counts plus per-file reasons) produced by a new run entry point on `ChunkSplitter`.
  - Replace the broad `except (OSError, RuntimeError, ValueError)` tuple in `process_all` with the specific exception classes each failure path actually raises, logging the class distinctly per failed file.
  - Map each failure class to the existing `IngestionFailureReason` vocabulary.
  - Have `main()` return a non-zero exit code when one or more files failed and `sys.exit(main())` in the `__main__` guard.
  - Keep `process_all` returning the integer chunk count so all existing callers and tests stay green.
  - Document the exit-status contract and the failure aggregate in the two rag error-handling / execution docs.
- **Out-of-Scope**:
  - Retrying failed files.
  - Routing chunk-stage failures into the ingestion quarantine directories.
  - Changing which files are skipped vs processed (the read-skip and already-chunked skip rules are unchanged).
  - Modifying `scripts/rag/exceptions.py` — the `IngestionFailureReason` enum already supplies the needed values.
- **Dependencies**:
  - **Depends on**: `issues/20261119-112016_ragcrv004_silent-chunk-discard-logging.md` | phase `all` | the zero-chunk (below-`min_chunk`) case the aggregate must distinguish from a real failure; the `failed` count must not include files that were processed but emitted zero chunks.

## Background
- `ChunkSplitter.process_all(target, force)` iterates source files, calls `process_file` per file inside `except (OSError, RuntimeError, ValueError)`, logs `logger.exception(...)`, and returns the sum of chunks written. `main()` calls `process_all` and returns `None`, so the process exits `0` regardless of failures.
- `scripts/rag/exceptions.py` derives every rag error from those two builtins: `ChunkFormatError(ValueError)`, `PipelineValidationError(RuntimeError)`, `TokenizationError(RuntimeError)`, `EmbeddingSchemaError(ValueError)`, `SearchQueryError(ValueError)`, `UnknownMetadataError(ValueError)`. One handler therefore absorbs every failure class with no distinction in the return value.
- The failure paths that reach `process_all`'s handler are: `OSError` re-raised from `_write_chunk_files` on a write/publish failure, and `TokenizationError` (RuntimeError) raised by the Japanese normalization path. `_read_source_data` already catches `FileNotFoundError` / `ChunkFormatError` and returns `None` (a skip, not a failure).
- The per-file skip/continue policy is documented and intended: `docs/21_rag/rag_05_04-error-handling-reference.md` states "the entire file is aborted; ERROR; continue to next file". NOTE: the issue cites `adr_02_06_009_rag-fts5-text-separation.md` INV-05 for this policy, but INV-05 actually governs content preservation ("a normalization failure never alters `content`"), not the continue-to-next-file rule; the continue policy's source of truth is `rag_05_04`. The ADR body is not reworded (ADR-preservation rule); the plan documents the exit-status contract against the correct source.
- `docs/21_rag/rag_05_02-execution-guide.md` shows the three pipeline stages running as separate commands, so a non-zero chunk-stage exit does not stop the ingester stage from running on stale or missing chunks.
- `IngestionFailureReason` (a `StrEnum`) already exposes `PARSE_FAILED`, `VALIDATION_FAILED`, `STORAGE_FAILED`, `UNEXPECTED_FAILURE`, and others — enough to map the chunk-stage failure classes without editing `exceptions.py`.
- `process_all` currently returns an `int`; `tests/rag/ingestion/test_chunk_splitter.py` has 12 call sites, several asserting on that integer (`assert splitter.process_all(force=True) >= 1`; `result == 0` after a write failure). Changing the return type would break them, so the aggregate is delivered through a new entry point and `process_all` keeps its integer contract.

## Problem
Failures are recorded only in `chunk.log`. The stage result, exit status, and the following pipeline step give no signal that the chunk stage produced nothing usable; an all-files-failed run is indistinguishable from a successful one.

## Reason for Change
The pipeline runs as a sequence of manual or scripted stages, and the chunk stage is the one whose failure mode is a silent empty corpus.

## Implementation Intent
Introduce a `ChunkRunResult` aggregate and a new `run_all` entry point that classifies each file as processed / skipped / failed, maps each failure to an `IngestionFailureReason`, and logs the exception class distinctly per file. `process_all` keeps returning the integer chunk count for existing callers. `main()` switches to `run_all`, returns a non-zero code when any file failed, and `sys.exit(main())` propagates it. Execute under `python-implementation`: preserve the existing integer contract, add behavior-locking regression coverage, and gate the exit-code change behind the new entry point.

## Requirements
- `REQ-001`: A structured `ChunkRunResult` aggregate exposes `processed`, `skipped`, and `failed` counts plus per-file reasons, produced by a new run entry point on `ChunkSplitter`.
- `REQ-002`: Each failure path catches the specific exception class it raises rather than the broad `(OSError, RuntimeError, ValueError)` tuple; the class is logged distinctly per failed file.
- `REQ-003`: `main()` returns a non-zero exit code when one or more files failed and `0` when only legitimate skips occurred; `sys.exit(main())` propagates the code.
- `REQ-004`: The documented per-file continue policy is preserved — a per-file failure aborts only that file and does not abort the whole run (`REQ-004`).
- `REQ-005`: `process_all` keeps returning the integer chunk count so all existing callers and tests stay green (`REQ-005`).
- `REQ-006`: Per-file failure reasons reuse the existing `IngestionFailureReason` vocabulary (`REQ-006`).
- `REQ-007`: The execution guide and error-handling reference document the exit-status contract and the failure aggregate (`REQ-007`).

## Implementation Target Files
**Freeze status**: Frozen (Step 8: all four rows `Verified`, `audit_plan_target_paths.py` reports 0 findings).

This table is the canonical, frozen source of implementation scope for this Plan. Once `Frozen`, `Implementation steps`, `Acceptance criteria`, and every downstream `plan-to-implementation-procedure` document MUST reference file paths only from this table — no other file may be treated as a modification target.

| File Path | Change Responsibility | Reason for Modification | Related Requirement / Acceptance Criterion | Repository Evidence | Related Tests | Validation Status |
|---|---|---|---|---|---|---|
| `scripts/rag/ingestion/chunk_splitter.py` | Modify | Add `ChunkRunResult` + `run_all`; narrow `process_all`'s except to the specific classes each path raises; map failures to `IngestionFailureReason`; switch `main` to `run_all` and return a non-zero code on failure | REQ-001, REQ-002, REQ-003, REQ-004, REQ-006 | `process_all` `except (OSError, RuntimeError, ValueError)` at line 150; `main` returns `None` at line 522; `IngestionFailureReason` enum complete in Step 2 | `test_chunk_splitter.py` | Verified |
| `tests/rag/ingestion/test_chunk_splitter.py` | Modify | Preserve existing `process_all` integer assertions; add `run_all` skip/fail-count unit tests and `main` exit-status tests for the all-failed and all-skipped cases | REQ-001, REQ-003, REQ-005 | 12 `process_all` call sites assert on the int return (lines 740–824, 1391, 1457, 1513); `test_process_all_logs_one_error_on_write_failure` asserts `result == 0` | `test_chunk_splitter.py` | Verified |
| `docs/21_rag/rag_05_04-error-handling-reference.md` | Modify | State the exit-status contract and the failure aggregate alongside the existing continue-to-next-file policy | REQ-003, REQ-006 | Documents "entire file aborted; ERROR; continue to next file" (lines 36–39); no exit-status section today | N/A | Verified |
| `docs/21_rag/rag_05_02-execution-guide.md` | Modify | State what a non-zero chunk-stage exit means for the following ingester stage | REQ-003 | Shows the three stages as separate commands (line ~282 in setup_services.sh) | N/A | Verified |

Rules (see `rules/workflow-lifecycle.md` Implementation Target Files Validation (Plan Freeze) for the full validation procedure):
- One row per file. A directory, glob pattern (`*`, `**`), component/module name, file group, or a vague phrase (e.g. "related files", "as necessary", "etc.") MUST NOT appear as a row — list each file individually by its exact repository-relative path.
- Record a test, configuration, schema, migration, deployment, or documentation file as its own row when it requires modification — do not fold it into the row for the source file it accompanies.
- `Validation Status` is `Verified` or `Needs confirmation` per row; every row must be `Verified` before this section may be marked `Frozen`.

## Reference Files
Files that must be read to implement the targets above, but MUST NOT be modified. Same one-file-per-row discipline as `Implementation Target Files` above — no directories, glob patterns, components, file groups, or vague phrases.

| File Path | Why It Must Be Read | Related Target File or Requirement |
|---|---|---|
| `scripts/rag/exceptions.py` | Source of the `RagLayerError` hierarchy and the `IngestionFailureReason` `StrEnum`; read to build the exception-class → reason mapping without editing the enum | REQ-006 |
| `scripts/rag/ingestion/file_routing.py` | Existing consumer of `IngestionFailureReason`; read to keep the reason vocabulary usage consistent across the ingestion layer | REQ-006 |
| `deploy/setup_services.sh` | Documents how the chunk stage is invoked (separate manual command) to confirm a non-zero exit does not break the following stages | REQ-003 |

## Acceptance Criteria
- `run_all` returns a `ChunkRunResult` whose `failed` count is greater than zero when a file raises, and `skipped` is counted separately from `failed` (`REQ-001`; AC: `test_chunk_splitter.py` `run_all` unit test).
- A run where every file fails exits non-zero and reports the failure count (`REQ-003`; AC: `main` exit-status test).
- A run where files were legitimately skipped exits `0` and reports the skip count (`REQ-003`; AC: `main` exit-status test).
- Log records distinguish exception class per failed file (`REQ-002`; AC: log-capture unit test).
- `process_all` still returns the integer chunk count; existing assertions stay green (`REQ-005`; AC: `test_process_all_logs_one_error_on_write_failure` and the `>= 1` cases).
- The per-file continue policy is intact: one failing file does not stop the remaining files from processing (`REQ-004`; AC: mixed pass/fail unit test).
- The exit-status contract and failure aggregate are documented (`REQ-007`; AC: doc review).

## Tests
- Behavior lock: the existing `process_all` assertions (`test_process_all_logs_one_error_on_write_failure` asserting `result == 0`; the `>= 1` cases) stay unchanged and green (`REQ-005`).
- Unit: `run_all` with one failing and one valid file returns distinct `skipped`/`failed` counts; the failing file's logged exception class is asserted (`REQ-001`, `REQ-002`).
- Unit: `main` exit status for the all-failed (non-zero) and all-skipped (`0`) cases, via monkeypatched `sys.argv` / `ConfigLoader` (`REQ-003`).
- Regression: the whole `tests/rag/ingestion/` chunk suite stays green (`REQ-004`, `REQ-005`).

## Documentation Impact
`docs/21_rag/rag_05_04-error-handling-reference.md` and `docs/21_rag/rag_05_02-execution-guide.md` (index task "Ingestion pipeline run"; these two files are not yet listed in `docs/00_index.md`'s Document References by Task table — confirm they are the current filenames before editing). State the exit-status contract and the failure aggregate in `rag_05_04`; state what a non-zero chunk-stage exit means for the ingester stage in `rag_05_02`. Driven by `REQ-007`. Do not reword `adr_02_06_009_rag-fts5-text-separation.md` INV-05 (ADR-preservation rule); the continue-policy citation belongs to `rag_05_04`.

## Assumptions
- The `ChunkRunResult` aggregate is a small dataclass (or `TypedDict`) defined in `chunk_splitter.py`; if the next phase prefers it elsewhere, it moves — the plan constrains only that it is importable and returned by `run_all`.
- `process_all` is refactored to share a per-file outcome iterator with `run_all`, so both observe identical classification and no logic diverges.
- The exact non-zero exit code is `1` unless an operator wrapper dictates otherwise; no wrapper script exists in the repository, so `1` is the default.
- The existing integer contract of `process_all` can be preserved because the issue sanctions "keep a compatible path or update those callers in the same change," and keeping the contract avoids rewriting 12 test assertions.
- The `IngestionFailureReason` values already cover the chunk-stage failure classes (a proposed mapping is recorded in `Design`); if a class needs a dedicated value, that is reported, not silently added.

## Unknowns
| ID | Unknown Description | Evidence Missing | Resolution Path | Blocking? (True/False) |
|---|---|---|---|---|
| UNK-01 | Whether to change `process_all`'s return type directly (cleaner API, requires updating the 12 test call sites) or keep the integer contract and deliver the aggregate through a new `run_all` entry point (backward-compatible, no test rewrites) | Issue constraint explicitly permits either; backward-compat minimizes regression risk | Recommend `run_all` + preserved `process_all`; record choice in the implementation procedure | False |
| UNK-02 | Exact non-zero exit code the operator's wrapper treats as failure (`1` vs another code) | No wrapper script found in the repository (`issues/..._ragcrv007` Unresolved Questions) | Default to `1`; confirm with operator at implementation | False |
| UNK-03 | Exception-class → `IngestionFailureReason` mapping details (e.g. `TokenizationError` has no dedicated value) | Which reason best represents a tokenization failure | Map `OSError→STORAGE_FAILED`, `ChunkFormatError→PARSE_FAILED`, `PipelineValidationError→VALIDATION_FAILED`, others→`UNEXPECTED_FAILURE`; confirm in procedure | False |

## Affected areas
`skills/DESIGN.md` Change-impact table, extended with `Churn (30d)` and `Bus Factor` columns. The `File` column here MUST be a subset of `Implementation Target Files`' rows — this table analyzes change-impact risk for those same files; it is not a separate scope-of-record.

| File | Change | Blast Radius | Churn (30d) | Bus Factor | deploy.sh Impact |
|---|---|---|---|---|---|
| `scripts/rag/ingestion/chunk_splitter.py` | Modify | CLI entry / `process_all` callers | 14 (90d) | N/A: tool unavailable (single-owner layer) | non-zero exit is compatible: stage runs as a separate command in `setup_services.sh` |
| `tests/rag/ingestion/test_chunk_splitter.py` | Modify | chunker unit suite | N/A | N/A | not applicable (rsynced) |
| `docs/21_rag/rag_05_04-error-handling-reference.md` | Modify | readers of the error-handling reference | N/A | N/A | not applicable (rsynced) |
| `docs/21_rag/rag_05_02-execution-guide.md` | Modify | readers of the execution guide | N/A | N/A | not applicable (rsynced) |

## Design
This is a runtime-interface change on the chunk stage (Path B: four target files including tests and docs). Execute under `python-implementation`: preserve the existing integer contract, add behavior-locking regression coverage, and gate the new exit-code behavior behind a new entry point so no observable behavior of `process_all` changes.

### Evidence: the silent-failure shape
`process_all` (line 140) sums `process_file` returns inside `except (OSError, RuntimeError, ValueError)` and returns the total; `main` (line 499) discards that return and returns `None`, so the interpreter exits `0`. The three failure-bearing builtins collapse every rag error class into one handler and one numeric total, and `main` contributes no status at all. That is exactly the all-files-failed-looks-like-success shape the issue reports.

### Backward-compatible run entry point (UNK-01)
Refactor `process_all` to drive a private per-file outcome iterator, and add `run_all` that consumes the same iterator to build a `ChunkRunResult`:
- `_iter_file_outcomes(paths) -> Iterator[FileOutcome]`: for each path, classify `processed` (≥1 chunk written), `skipped` (returned 0 legitimately: already-chunked, unreadable, below-`min_chunk`), or `failed` (exception raised); on failure, map the exception class to an `IngestionFailureReason` and log the class distinctly.
- `process_all` sums the `processed` chunks from the iterator and returns the `int` total — contract unchanged.
- `run_all` returns the `ChunkRunResult` aggregate and logs a run-level summary line.
- `main` calls `run_all`, returns `1` when `result.failed > 0` else `0`, and `__main__` does `sys.exit(main())`.

This delivers the aggregate and exit status without changing `process_all`'s public signature or return type, so the 12 existing test assertions stay green (`REQ-005`). The alternative (changing `process_all`'s return type directly) is cleaner API-wise but requires updating every int assertion; it is recorded as `UNK-01` for the owner to choose.

### Failure-class → reason mapping (UNK-03)
Proposed mapping, using only existing `IngestionFailureReason` values:
| Exception reaching `process_all` | `IngestionFailureReason` |
|---|---|
| `OSError` (write/publish) | `STORAGE_FAILED` |
| `ChunkFormatError` (if it ever reaches the handler) | `PARSE_FAILED` |
| `PipelineValidationError` | `VALIDATION_FAILED` |
| `TokenizationError` and any other | `UNEXPECTED_FAILURE` |

The mapping lives in `chunk_splitter.py`; `exceptions.py` is not modified. If a class needs a dedicated enum value, report it rather than adding one silently.

### Continue-policy guard (REQ-004)
The iterator must never raise out of the per-file loop on a caught failure; each failure is recorded and iteration continues. A mixed run (one failing file plus valid files) must still process the valid files and report the correct `processed`/`failed` split. This preserves the `rag_05_04` continue-to-next-file policy; the whole run is not aborted.

### Exit code (UNK-02)
Default non-zero code is `1`. `deploy/setup_services.sh` documents the chunk stage as a separate manual command, so a non-zero exit does not prevent the ingester stage from running; the execution guide states this explicitly (`REQ-003`).

### importlinter
The `rag` package forbids importing `agent`/`mcp_servers`; `ChunkRunResult` and the iterator stay within `rag.ingestion`, so no package-boundary contract changes.

## Implementation steps
Each step description MUST cite the exact file path(s) it touches by referencing rows of `Implementation Target Files` above — do not restate file-level detail independently of that frozen table. A step is a top-level numbered item (a Phase); its checklist items are sub-tasks, and the Execution Status table has one row per step. Declare a release unit when a phase breaks existing callers or tests until another phase lands.

1. **Phase 1: Aggregate + outcome iterator**
   - [ ] Add `ChunkRunResult` and the per-file `FileOutcome` types to `scripts/rag/ingestion/chunk_splitter.py` (`REQ-001`).
   - [ ] Add the private `_iter_file_outcomes` iterator that classifies processed/skipped/failed and maps failures to `IngestionFailureReason` (`REQ-001`, `REQ-006`).
2. **Phase 2: Narrow the except + `run_all`**
   - [ ] Replace the `(OSError, RuntimeError, ValueError)` tuple in `process_all` with the specific classes each path raises; log the class distinctly per failed file (`REQ-002`).
   - [ ] Drive `process_all` off `_iter_file_outcomes` and return the integer total; add `run_all` returning the aggregate (`REQ-001`, `REQ-005`).
3. **Phase 3: Exit code**
   - [ ] Switch `main` to `run_all`, return `1` when `failed > 0` else `0`, and `sys.exit(main())` in the `__main__` guard (`REQ-003`).
4. **Phase 4: Tests**
   - [ ] Preserve existing `process_all` integer assertions unchanged (`REQ-005`).
   - [ ] Add `run_all` skip/fail-count + distinct-exception-log unit tests (`REQ-001`, `REQ-002`).
   - [ ] Add `main` exit-status tests for the all-failed and all-skipped cases via monkeypatched `sys.argv` / `ConfigLoader` (`REQ-003`).
   - [ ] Add a mixed pass/fail test asserting the continue policy (`REQ-004`).
5. **Phase 5: Docs**
   - [ ] Document the exit-status contract and failure aggregate in `docs/21_rag/rag_05_04-error-handling-reference.md` (`REQ-007`).
   - [ ] State what a non-zero chunk-stage exit means for the ingester stage in `docs/21_rag/rag_05_02-execution-guide.md` (`REQ-007`).
6. **Phase 6: Verify**
   - [ ] Run the full `tests/rag/ingestion/` suite; assert zero regressions (`REQ-004`, `REQ-005`).
   - [ ] Confirm `deploy/setup_services.sh` invocation remains compatible with a non-zero chunk-stage exit (`REQ-003`).

### Release units
N/A: no release unit — each phase lands in a testable state (iterator + types after Phase 1; `process_all` contract preserved after Phase 2; exit code after Phase 3; full regression green after Phase 6).

## Validation plan
| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| `process_all` contract | Regression: integer chunk count unchanged | `uv run pytest tests/rag/ingestion/test_chunk_splitter.py` | Existing `result == 0` / `>= 1` assertions pass |
| `run_all` aggregate | Unit: skip/fail counts, distinct exception log | `uv run pytest tests/rag/ingestion/test_chunk_splitter.py` | `failed`/`skipped` distinct; exception class logged per file |
| Continue policy | Unit: mixed pass/fail run | `uv run pytest tests/rag/ingestion/test_chunk_splitter.py` | Valid files still processed; `failed` counted |
| Exit code | Unit: `main` exit status | `uv run pytest tests/rag/ingestion/test_chunk_splitter.py` | All-failed → non-zero; all-skipped → `0` |
| Docs | Review: exit-status contract present | read `docs/21_rag/rag_05_04-error-handling-reference.md`, `docs/21_rag/rag_05_02-execution-guide.md` | Contract + aggregate documented |

## Risks
- **Risk**: Changing `process_all`'s return type breaks the 12 int assertions. → **Mitigation**: deliver the aggregate through `run_all`; keep `process_all` returning the `int` total (`REQ-005`, `UNK-01`).
- **Risk**: The `failed` count wrongly includes below-`min_chunk` zero-chunk files, conflating a size discard with a failure. → **Mitigation**: classify by exception vs. legitimate zero-return; the zero-chunk case is `skipped`/`processed`, not `failed` (`REQ-004`; depends on `ragcrv004`).
- **Risk**: Over-narrowing the except tuple drops a class a path actually raises, letting an exception escape `process_all`. → **Mitigation**: enumerate only the classes verified in Step 2 evidence (`OSError`, `TokenizationError`, and the read-skip classes handled earlier); let the mixed-run test catch escapes.
- **Risk**: Editing the two docs violates doc-quality gates (front matter, related-doc headings). → **Mitigation**: run the docs checkers after editing (see `rules/toolchain.md`) before freeze.

## Execution Status

Table structure, status/type vocabulary, and general guidance: see `templates/execution-status.md`. Default rows for a freshly generated Plan (replace with the Plan's actual steps once Implementation steps are broken down):

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Phase 1: Aggregate + outcome iterator | Pending | — | — | |
| 2 | Phase 2: Narrow except + `run_all` | Pending | — | — | |
| 3 | Phase 3: Exit code | Pending | — | — | |
| 4 | Phase 4: Tests | Pending | — | — | |
| 5 | Phase 5: Docs | Pending | — | — | |
| 6 | Phase 6: Verify | Pending | — | — | |

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
- **Source issue**: `issues/20261119-112019_ragcrv007_chunk-failure-exit-reporting.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: this document is the generated plan
- **Source implementation procedure**: N/A: not applicable in this phase
- **Generated at**: 20261119-191233
- **Related target files**: `scripts/rag/ingestion/chunk_splitter.py`, `tests/rag/ingestion/test_chunk_splitter.py`, `docs/21_rag/rag_05_04-error-handling-reference.md`, `docs/21_rag/rag_05_02-execution-guide.md` — the full list of `File Path` values from `Implementation Target Files` above, once `Frozen`

### Requirement Traceability
See `templates/requirement-traceability.md` for the canonical column format.

| Requirement ID | Source Issue section or evidence | Target file | Implementation step | Acceptance criterion | Test or validation item | Status |
|---|---|---|---|---|---|---|
| REQ-001 | Implementation Intent / Required Changes (structured aggregate) | `scripts/rag/ingestion/chunk_splitter.py` | Step 1 | `processed`/`skipped`/`failed` counts + reasons | `run_all` unit test | Confirmed by repository evidence |
| REQ-002 | Required Changes (specific exception classes) / AI Implementation Instruction | `scripts/rag/ingestion/chunk_splitter.py` | Step 2 | Exception class logged per failed file | log-capture unit test | Confirmed by repository evidence |
| REQ-003 | Required Changes (exit non-zero) / Unresolved Questions | `scripts/rag/ingestion/chunk_splitter.py` | Step 3 | Non-zero on failure, 0 on skip | `main` exit-status test | Confirmed by repository evidence |
| REQ-004 | Constraints (do not abort whole run) | `scripts/rag/ingestion/chunk_splitter.py` | Steps 2, 4 | Continue policy intact | mixed pass/fail test | Confirmed by repository evidence |
| REQ-005 | Constraints (compatible return type) | `scripts/rag/ingestion/chunk_splitter.py`, `tests/rag/ingestion/test_chunk_splitter.py` | Steps 2, 4 | Integer contract preserved | existing assertions green | Confirmed by repository evidence |
| REQ-006 | Required Changes (reuse IngestionFailureReason) | `scripts/rag/ingestion/chunk_splitter.py` | Step 2 | Reasons map to enum | unit test | Confirmed by repository evidence |
| REQ-007 | Documentation Impact | `docs/21_rag/rag_05_04-error-handling-reference.md`, `docs/21_rag/rag_05_02-execution-guide.md` | Step 5 | Contract documented | doc review | Needs confirmation |
