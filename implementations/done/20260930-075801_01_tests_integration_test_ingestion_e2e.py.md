## Goal

Add a chunk-file precondition to `test_ingester_handles_embedding_failure` in `tests/integration/test_ingestion_e2e.py` so the test reaches the mocked `_process_url_groups` failure through `ingest_all()`'s real `*.json` glob guard, instead of passing only when a leftover chunk file from a sibling test happens to still exist (`REQ-001`).

## Scope

- **In scope**: One edit to one test function in `tests/integration/test_ingestion_e2e.py` — insert the ~5-line chunk-file creation step (mirroring `test_ingester_processes_chunk_files`) before the existing mocking/assertion block.
- **Out of scope**: `RagIngester.ingest_all()`'s "no chunk files" short-circuit (correct behavior, unchanged); the file-wide shared `/tmp/crawl-test-chunks` isolation gap (documented in the Plan's Risks, not fixed here); any other test in the file; any change to `scripts/rag/ingestion/ingester.py`.

## Assumptions

- Mirroring `test_ingester_processes_chunk_files`'s existing chunk-file-creation pattern (same path, same minimal JSON payload) is the intended, minimal fix, consistent with the Issue's Implementation Intent ("create a chunk file under rag_src_dir") and Constraints (do not change `ingest_all`'s short-circuit itself).
- The shared, hardcoded `/tmp/crawl-test-chunks` path and its lack of per-test cleanup is a pre-existing convention in this file, not something this Plan changes.

## Design decisions

- Reuse the already-accepted sibling pattern rather than introduce a new fixture, mock, or cleanup mechanism. This keeps the change a small, localized test-data setup (Path A) with no production-code or public-interface impact.
- Place the chunk-file creation immediately after `ingester = RagIngester(mock_cfg)` and before the `_process_url_groups`/`SQLiteHelper` mocking so `ingest_all()` observes a real `*.json` file and proceeds past its guard.

## Alternatives considered

- **Per-test cleanup / `tmp_path` migration**: would fix the file-wide order-dependent false-pass root cause, but redesigns this file's established convention and is explicitly out of scope per the Issue Constraints. Recorded as a future test-hygiene starting point in the Plan's Risks.
- **Fixing `ingest_all()` to not short-circuit**: excluded by the Issue's Constraints; the short-circuit is intentional, correct behavior.
- **Mocking `SQLiteHelper` to force the path**: the current test already does this, but it is insufficient because the glob guard runs before `SQLiteHelper` is constructed — only an actual `*.json` file bypasses it.

## Implementation

### Target file

`tests/integration/test_ingestion_e2e.py` — class `TestFullIngestionPipeline`, method `test_ingester_handles_embedding_failure` (currently lines 92-113).

### Procedure

1. Open `tests/integration/test_ingestion_e2e.py` and locate `def test_ingester_handles_embedding_failure(self):`.
2. Verify `Path` is imported at the top of the file (the sibling `test_ingester_processes_chunk_files` already uses `Path(...)`; confirm the import exists).
3. Insert the following block right after the `ingester = RagIngester(mock_cfg)` line inside `test_ingester_handles_embedding_failure`, i.e. before the `# Mock _process_url_groups to fail` comment and its `with patch.object(ingester, "_process_url_groups")` block:

   ```python
   # Establish the ingest_all() chunk-file precondition explicitly (was previously
   # met only incidentally by a leftover file from test_ingester_processes_chunk_files).
   chunk_dir = Path("/tmp/crawl-test-chunks/chunk")
   chunk_dir.mkdir(parents=True, exist_ok=True)
   (chunk_dir / "dummy-001.json").write_text(
       '{"url":"http://example.com","lang":"en","content":"test content"}'
   )
   ```

4. Leave the existing `_process_url_groups` mock, `SQLiteHelper` mock, and `pytest.raises(Exception, match="Embedding API unavailable")` assertion unchanged.
5. Do not touch `test_ingester_processes_chunk_files`, `test_ingester_moves_processed_files`, or any other function.

### Method

- Confirm the root cause empirically before editing: `rm -f /tmp/crawl-test-chunks/chunk/*.json`, then run the target test in isolation to reproduce `Failed: DID NOT RAISE <class 'Exception'>` with the `"No chunk files to process"` log line.
- Copy the exact chunk-file creation statements from `test_ingester_processes_chunk_files` (lines 64-70) so the path, filename (`dummy-001.json`), and payload shape match the accepted pattern.
- Use an editor/`sed`/`apply_patch` insertion anchored on the unique string `# Mock _process_url_groups to fail` to avoid ambiguity.
- After editing, re-run the reproduction command to confirm the isolated test now passes.

### Details

- `RagIngester.ingest_all()` (`scripts/rag/ingestion/ingester.py:141-154`) computes `chunk_files = sorted(self._chunk_dir.glob("*.json"))` (line 151) and returns `None` with a `"No chunk files to process"` log when the list is empty (lines 152-154), BEFORE constructing `SQLiteHelper` (line 158) or calling `_process_url_groups` (line 166). `self._chunk_dir` is `rag_src_dir / "chunk"` (line 104).
- Because the test never creates a `*.json` file under that directory, `ingest_all()` returns `None` early, the mocked `side_effect` never fires, and `pytest.raises` reports `DID NOT RAISE`. When a polluting sibling leaves `dummy-001.json` behind, the test passes by accident — an order-dependent false pass, not a genuine assertion.
- Creating the dummy file makes the test reach the mocked `_process_url_groups` `side_effect = Exception("Embedding API unavailable")` and exercise the real propagation path the docstring claims to verify.

## Compatibility considerations

- Test-only data change; no production code, no public/runtime interface change, no DB schema change. `deploy.sh` rsyncs `scripts/` only, so no `deploy.sh` update is required.
- Does not alter the behavior or assertions of the other five tests in `test_ingestion_e2e.py`.

## Security considerations

N/A: the added statement writes a throwaway JSON file under a test-only `/tmp` path using the identical pattern already present in the sibling test. No credentials, network, or persistent-filesystem exposure is introduced.

## Rollback considerations

Revert the inserted block (or `git checkout -- tests/integration/test_ingestion_e2e.py`) restores the prior state exactly. This is a test golden/setup constant with no config or database component, so no additional rollback steps are needed.

## Validation plan

| Target | Strategy | Command | Expected Outcome |
|---|---|---|---|
| `test_ingester_handles_embedding_failure` (isolation) | Unit | `rm -f /tmp/crawl-test-chunks/chunk/*.json && uv run pytest "tests/integration/test_ingestion_e2e.py::TestFullIngestionPipeline::test_ingester_handles_embedding_failure" -v` | Passes without any leftover chunk file; genuinely reaches the mocked `_process_url_groups` `side_effect` |
| `test_ingestion_e2e.py` (full file) | Integration | `uv run pytest tests/integration/test_ingestion_e2e.py -v` | All 6 tests in the file pass |
| Full suite | Regression | `uv run pytest -q` | No new failures |

## Completion criteria

- `test_ingester_handles_embedding_failure` passes in ISOLATION after clearing `/tmp/crawl-test-chunks/chunk/*.json` (Plan AC-1) — proving the fix does not depend on sibling-test pollution.
- The inserted chunk-file block is the only addition; the existing mocks, the `pytest.raises` assertion, and the other five tests are unchanged.
- The full-suite run shows no new failures.

## Out of scope

- `RagIngester.ingest_all()`'s no-chunk-files short-circuit (`scripts/rag/ingestion/ingester.py:151-154`) — intentional, correct behavior; not modified.
- The file-wide shared hardcoded `/tmp/crawl-test-chunks` path and absence of per-test cleanup — documented in the Plan's Risks as a future test-hygiene item, not fixed here.
- Any test other than `test_ingester_handles_embedding_failure`.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Add chunk-file precondition to `test_ingester_handles_embedding_failure` | Completed | 20260930-141925 | 20260930-141925 | REQ-001 REQ-001; isolated+full-file pass; ruff+mypy clean; full-suite 12 fails are pre-existing/unrelated (reproduced on clean tree) |
| 2 | Run isolation-check, full-file, and full-suite validation | Completed | 20260930-141925 | 20260930-141925 | REQ-001, AC-1 REQ-001, AC-1; isolation pass w/o leftover; full file 6 passed; full-suite 12 fails pre-existing/unrelated |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| — | — | N/A: none | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| — | — | — | — | — | — |

## Traceability
- **Workflow phase**: plan-to-implementation-procedure
- **Requirement ID**: `REQ-001` — add chunk-file setup so `ingest_all()` passes its "no chunk files" guard and the test genuinely reaches the mocked `_process_url_groups`.
- **Source issue**: `issues/20260928-124754_int002_ingester-embedding-failure-short-circuits-on-no-chunk-files.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20260929-174904_plan.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260930-075801
- **Related target files**: `tests/integration/test_ingestion_e2e.py`