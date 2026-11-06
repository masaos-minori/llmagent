## Goal
Make a `force=True` run of `ChunkSplitter.process_file` authoritative for its source's chunk series: after the run, `chunk/` holds exactly the newly produced series for that source stem, including when the new series is empty, so obsolete chunks cannot be re-ingested with fresh ones (`REQ-001`: prune on a forced run; `REQ-002`: exact stem scope and logging; `REQ-003`: regression tests).

## Scope
**Release unit**: force-prune-fix

- In scope: a private helper `_prune_stale_chunk_files` (new) in `scripts/rag/ingestion/chunk_splitter.py`, its call from `process_file`'s forced path, and the new test class in the companion test file.
- Out of scope: the `code_blocks` payload mismatch (`issues/20261106-110845_ragfix001_chunk-payload-code-blocks.md`), `registered/` retention, group validation routing, removing already-ingested database rows, and the documentation paragraph (the second procedure).

## Assumptions
- Verified on 2026-11-06 (Step 3a, HEAD `97b8f4f6b`): `process_file` skips when `is_already_processed(sentinel, force)` is true, otherwise reads the source with `_read_source_data` (returning `None` on failure), builds the chunk list with `_build_chunk_list`, and calls `_write_chunk_files`, whose first statement returns `0` for an empty list and whose loop writes `{stem}-{idx:04d}.json` without deleting anything. `re` and `logger` are already available in the module. `is_already_processed` is `not force and sentinel_path.exists()`.
- Plan correction applied here (Step 3a): pruning is placed after `_build_chunk_list` succeeds, because chunking can raise (the Japanese merge crash of the `raging001` Plan is such a case) and a raised error must not destroy the existing series; it is placed before `_write_chunk_files`, which cannot prune the empty-list case.
- Companion test file `tests/rag/ingestion/test_chunk_splitter.py`: a valid companion because it is a row of the Plan under `tests/`, only the code row names it in `Related Tests`, and the Plan prescribes its test list. Existing helpers `_CRAWL_CONFIG`, `_make_io_splitter`, and `_make_crawl_json` are reused; existing tests assert written counts only, and none pins the presence or absence of stale files.
- The Plan's release unit `force-prune-fix` (phases 1 and 2) is covered entirely by this document, because the failing tests and the fix are executed in one cycle (red, then green).
- Importers of `ChunkSplitter` are two test files (`tests/rag/ingestion/test_chunk_splitter.py` and `tests/rag/ingestion/test_rag_ingestion_pipeline.py`); it has no production importer apart from its own `main` entry.
- Sequencing: the `raging001` procedure (`implementations/done/20261106-114129_01_scripts_rag_ingestion_chunk_japanese.py.md`) edits `_make_ja_mixin` and the Japanese end-to-end test of the same test file; this procedure adds a separate test class, so the edits are compatible and `raging001` goes first (Plan Design). Re-verified 2026-11-06: `raging001` has been executed and archived (commit `d1afb6a28`); `TestJapaneseMergeRegression` and the Japanese end-to-end test now exist in the companion file, so this prerequisite is satisfied. `issues/20261106-110845_ragfix001_chunk-payload-code-blocks.md` will change `_build_chunk_payload` of the same module, a different function, so there is no ordering requirement. The `raging007` Plan is gated on this one.

## Design decisions
- Prune only on `force=True`, after the chunk list is built, before writing; non-forced behavior (the sentinel skip) is unchanged.
- Match files with `re.compile(rf"^{re.escape(stem)}-\d{{4,}}\.json$")` against the names in `chunk_dir`, not with a glob: a glob for a stem would also match another stem that ends in a numeric suffix. `\d{{4,}}` mirrors the writer's `:04d` format including indices above 9999.
- Log the number of removed files at `INFO` when it is greater than zero; an `OSError` on one file is logged at `ERROR` and does not stop the run.

## Alternatives considered
- Pruning inside `_write_chunk_files`: rejected, its empty-list early return would miss the zero-chunk case, and `process_file` is where `force` is known.
- `glob(f"{stem}-*.json")`: rejected, it crosses stems with numeric suffixes.

## Implementation
### Target file
`scripts/rag/ingestion/chunk_splitter.py`

### Procedure
1. Add the new test class to the companion test file first and run it: the shrink and zero-chunk cases must fail against the current code; the grow, stem-isolation, broken-source, chunking-error, and non-forced cases pass (characterization). Correction recorded here (re-verification 2026-11-06): the chunking-error case is a characterization test, not a red test — without the prune there is nothing to destroy the series, so the exception propagates and the series is preserved both before and after the fix.
2. Add the private method `_prune_stale_chunk_files(stem)` (new) to `ChunkSplitter` after `process_file`; it returns the number of removed files.
3. In `process_file`, after `chunks = self._build_chunk_list(chunk_doc)` and before the call to `_write_chunk_files`, add `if force:` followed by the call of `_prune_stale_chunk_files(src_path.stem)`.
4. Re-run the new class and the whole companion file; then `uv run pytest tests/rag/ingestion`.

### Method
- `_prune_stale_chunk_files(stem)` (new) returns `0` when `self._chunk_dir` does not exist; otherwise it compiles the pattern once, iterates `self._chunk_dir.iterdir()`, unlinks each matching file, counts successes, and logs the count.
- The early return of `_write_chunk_files` for an empty list is left as it is: a forced run with an empty new series has already pruned, so the directory holds no file of the stem.

### Details
- Do not change `_write_chunk_files`, `_build_chunk_payload`, or `is_already_processed`.
- Do not touch files whose names do not match the pattern, including `*-0000.json` files of other stems and non-JSON files.
- No new import is needed (`re`, `Path`, and `logger` exist).

### Companion test files
- `tests/rag/ingestion/test_chunk_splitter.py`
  - Procedure: add a class `TestForceRechunkPrune` (new) built on `ChunkSplitter(config=...)` with `rag_src_dir` set to `tmp_path` and the existing `_make_crawl_json` helper: (a) shrink: chunk one source with `max_chunk=200`, force-rerun with `max_chunk=600`, assert the files on disk are exactly the new series and the `chunk_index` values equal `range(new_count)`; (b) grow: the reverse order, assert no gaps and the on-disk set equals the new series; (c) zero-chunk: force-rerun with `min_chunk` raised above the content size, assert no file of the stem remains; (d) stem isolation: chunk stems `page` and `page-1234`, force-rerun `page`, assert the other stem's files are byte-identical; (e) broken source: replace the source with invalid JSON, run with `force=True`, assert the existing series is preserved; (f) chunking error: patch `_build_chunk_list` to raise, run with `force=True`, assert the exception propagates and the existing series is preserved; (g) non-forced rerun still skips and leaves the files untouched (characterization).
  - Validation: `uv run pytest tests/rag/ingestion/test_chunk_splitter.py -v`: (a) and (c) fail before step 3 and pass after it; (b), (d), (e), (f), and (g) pass throughout (characterization); every other test of the file, and `uv run pytest tests/rag/ingestion`, pass.

## Compatibility considerations
- Non-forced runs are unchanged. A forced run now deletes the previous chunk files of that source before writing, which is the intended contract; no caller outside the CLI `--force` option and the tests passes `force=True`.

## Security considerations
- The deletion is confined to files of `self._chunk_dir` whose full name matches the escaped stem pattern; `src_path.stem` comes from the crawler's own file names, and `re.escape` prevents the stem from acting as a pattern.

## Rollback considerations
- Revert the commit; the removed chunk files are regenerated by re-running the splitter on the same source files. No data outside `chunk/` is touched.

## Validation plan
- `uv run pytest tests/rag/ingestion/test_chunk_splitter.py -v`, then `uv run pytest tests/rag/ingestion`.
- `uv run ruff format`, `uv run ruff check scripts/ tests/rag/ingestion`, `uv run mypy --no-namespace-packages scripts/ tests/eventbus tools`, `PYTHONPATH=scripts uv run lint-imports`, `uv run bandit -r scripts/ -c pyproject.toml -ll`.
- Live check on a copy: chunk a real crawl file twice into a temporary `rag_src_dir` with different `max_chunk` values and compare the files on disk with the second series.
- Full suite once with coverage, then `uv run diff-cover coverage.xml --compare-branch=master --fail-under=90` (`rules/toolchain.md`).
- `uv run python tools/run_validation_gates.py`.

## Completion criteria
- After a forced run the on-disk series of the stem equals the new output in the shrink, grow, and zero-chunk cases; other stems are untouched; a broken source and a chunking error preserve the existing series; non-forced behavior is unchanged; the whole ingestion test directory passes; changed lines reach the diff-cover threshold.

## Out of Scope
- The `code_blocks` payload mismatch, `registered/` retention, group routing, database cleanup, the documentation paragraph.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Add the new test class and confirm the failing cases | Completed | 2026-11-06 | 2026-11-06 | Red as corrected: shrink and zero-chunk fail; grow, stem-isolation, broken-source, chunking-error, non-forced pass as characterization |
| 2 | Add `_prune_stale_chunk_files` (new) and call it from the forced path | Completed | 2026-11-06 | 2026-11-06 |  |
| 3 | Run the validation sequence (`rules/toolchain.md`), the live copy check, and the single full-suite run with coverage | Completed | — | 2026-11-06 | All static gates pass; bandit findings unchanged vs baseline (0 on changed file); diff-cover reports no coverable lines because chunk_splitter.py is in the pyproject coverage omit list (project policy: ingestion scripts integration-tested separately); live copy check 39->26 chunks, exact new series |
| 4 | N/A: documentation is the second procedure of this Plan | Completed | — | 2026-11-06 | N/A row: documentation is procedure 131606_03 of the same Plan |

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
- **Requirement ID**: `REQ-001` (prune on a forced run), `REQ-002` (exact stem scope, logging), `REQ-003` (regression tests)
- **Source issue**: issues/20261106-073538_raging004_force-rechunk-stale-chunks.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261106-101257_raging004_force-rechunk-stale-chunks.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261106-131606
- **Related target files**: `scripts/rag/ingestion/chunk_splitter.py`, `tests/rag/ingestion/test_chunk_splitter.py`