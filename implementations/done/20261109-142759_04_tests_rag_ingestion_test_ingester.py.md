## Goal

Keep `test_skips_already_registered_url` proving the skip path after the absence rule lands, by giving its chunk specs non-null validators and asserting the skipped content (`REQ-004`: existing skip behavior for validated pages is unchanged; fallout row added to the Plan).

## Scope
**Release unit**: N/A: not part of a release unit

- In scope: the test `test_skips_already_registered_url` in `tests/rag/ingestion/test_ingester.py`.
- Out of scope: every other test in the file, `_ChunkSpec` defaults, and production code.
- Plan: `plans/20261108-165741_ragrev010_pages-without-validators-skipped.md` (Plan step 1, fallout amendment 2026-11-09); apply together with document `01`.

## Assumptions

- Re-verified at generation time: `_ChunkSpec` defaults `etag=None` and `last_modified=None`; the test ingests the default spec twice for `https://example.com/doc` with `force=False` and asserts one document and one chunk. After document `01`, the second ingest replaces instead of skipping, and the assertion would still pass (one chunk either way) while no longer proving a skip.
- No other test in this file ingests the same validator-less URL twice without `force` (the other double-ingest tests use `force`, failure paths, or retries).
- Overlap: `tests/rag/ingestion/test_ingester.py` is also a target of `plans/20261108-170534_ragrev015_poison-chunk-groups-retried.md` and `plans/20261108-170725_ragrev016_stale-recrawl-replaces-content.md`; compatible (this edits one existing test body; those add tests elsewhere). Locate the test by name, not line number.

## Design decisions

- Change the specs used by this one test, not the `_ChunkSpec` defaults, so every other test keeps its validator-less data and now exercises the re-ingest path as before.
- Make the second spec's content differ from the first, so asserting the stored chunk content equals the first ingest proves the second ingest was skipped.

## Alternatives considered

- Change `_ChunkSpec` defaults to carry validators: rejected; it alters the data of every test in the file.

## Implementation
### Target file
`tests/rag/ingestion/test_ingester.py`

### Procedure
1. In `test_skips_already_registered_url`, build `first = _ChunkSpec(etag='"e1"', last_modified="lm1")` and `second = _ChunkSpec(etag='"e1"', last_modified="lm1", content="別本文")`.
2. Pass `first` to the first `_write_chunk` call and `second` to the `c2.json` call.
3. After the existing count assertions, assert the stored chunk content is still the first ingest's (`"本文"`), comparing a `SELECT content FROM chunks` result.
4. Update the trailing comment (`only from first ingest`) only if it no longer matches.

### Method
- Edit the one test body; reuse `_ChunkSpec` and `_write_chunk` as they are.

### Details
- Content uses the file's existing Japanese default text style; the value is test data, not documentation.
- Confirm once, after document `01` is applied, that the test fails if `second` carries differing validators (a differing etag must replace); this is a manual check, not a new test.

## Compatibility considerations

N/A: test-only change to one test.

## Security considerations

N/A: test-only change.

## Rollback considerations

N/A: revert the commit.

## Validation plan

- `uv run pytest tests/rag/ingestion/test_ingester.py -q`, then `uv run pytest tests/rag -q`.
- `uv run ruff format` and `uv run ruff check` on the file; `uv run mypy`; `uv run python tools/check_mock_patch_targets.py`.

## Completion criteria

- `test_skips_already_registered_url` uses non-null validators on both ingests and asserts the first ingest's content is retained.
- The test passes with document `01` applied, and `uv run pytest tests/rag -q` is green.

## Out of Scope

- Production code, other tests, `_ChunkSpec` defaults, and the HTTP-branch matrix (document `01` companion).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Give the two specs non-null validators and assert the retained content | Completed | 20261109-182406 | 20261109-182406 | skip path verified via negative etag case (e2 -> replace -> assertion fails) |
| 2 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20261109-182406 | 20261109-182406 | skip path verified via negative etag case (e2 -> replace -> assertion fails) |

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
- **Requirement ID**: `REQ-004` (existing skip behavior for validated pages unchanged)
- **Source issue**: issues/20261108-131124_ragrev010_pages-without-validators-skipped.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261108-165741_ragrev010_pages-without-validators-skipped.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261109-142759
- **Related target files**: `tests/rag/ingestion/test_ingester.py`
