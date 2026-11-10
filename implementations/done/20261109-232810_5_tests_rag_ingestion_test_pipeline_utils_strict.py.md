## Goal

- Cover the new strict `chunk_type` domain in `read_chunk_json` with rejection and acceptance cases (AC-2), so the closed domain enforced by `scripts/db/schema_sql.py` L45 `CHECK (chunk_type IN ('text','code'))` is pinned at read time (`REQ-002`).

## Scope
**Release unit**: ragrev015-core (Plan `### Release units`; owner-declared batch unit 20261110)

- `tests/rag/ingestion/test_pipeline_utils_strict.py`, `TestReadChunkJson` only.

## Assumptions

- Measured at HEAD `02f3143e2` in a scratch worktree: this file has 0 failures under either ragrev015 patch (chunk_type-domain patch, embedding-size patch), so no fixture realignment is needed here; the work is purely additive.
- The module fixture `CHUNK_PAYLOAD` already carries `"chunk_type": "text"` (current L53), which stays valid under the stricter rule.

## Design decisions

- Use `pytest.mark.parametrize` over the invalid values `""`, `"chunk"`, `"foo"` and the valid values `"text"`, `"code"` in one test, so the domain boundary is a single readable table rather than four near-duplicate tests.
- Assert the exception type (`ChunkFormatError`) and that its message names both the field and the offending value, so a later message refactor that drops the value still fails the test.

## Alternatives considered

- Testing the domain only through `ingest_url_group`: rejected — the end-to-end path hides which validation rejected the payload, and the Plan's AC-2 is stated at the `read_chunk_json` level.

## Implementation
### Target file
- `tests/rag/ingestion/test_pipeline_utils_strict.py`

### Procedure
- Add a parametrized rejection/acceptance test for `chunk_type` to `TestReadChunkJson`.

### Method
- Measured current shape: `CHUNK_PAYLOAD` fixture at L42-53 (`"chunk_type": "text"`), `TestReadChunkJson` at L137 with existing per-field cases built from `dict(CHUNK_PAYLOAD)` (L156-214).
- Add to `TestReadChunkJson`:
  - `@pytest.mark.parametrize("bad", ["", "chunk", "foo"])` → build `data = dict(CHUNK_PAYLOAD)`, set `data["chunk_type"] = bad`, assert `read_chunk_json(...)` raises `ChunkFormatError` and `"chunk_type"` appears in `str(excinfo.value)`.
  - `@pytest.mark.parametrize("good", ["text", "code"])` → assert the returned `ChunkDocument.chunk_type == good`.
- Keep using the existing `_make_tmp_file` helper so no new fixture plumbing is introduced.

### Details
- The existing "missing key" case (L156-157, `del data["chunk_type"]`) is unchanged: a missing key is still a `Missing keys` rejection, distinct from the new domain rejection.
- No change to `TestReadCrawlJson` (L61): the crawl payload path builds `chunk_type=""` internally in `pipeline_utils.py` (crawl read helper, current L138 region) and is not governed by the chunk-payload domain.

## Compatibility considerations

- Additive only; no existing assertion is relaxed or removed.

## Security considerations
N/A: test data only.

## Rollback considerations
N/A: revert the single commit.

## Validation plan

- `uv run pytest tests/rag/ingestion/test_pipeline_utils_strict.py -q` — each new rejection case fails on HEAD (where `""` and unknown values are accepted) and passes after the seq-2 change; both acceptance cases pass before and after.
- `uv run pytest tests/rag/ingestion -q` regression.

## Completion criteria

- The parametrized rejection cases for `""`, `"chunk"`, `"foo"` and the acceptance cases for `"text"`, `"code"` all pass (AC-2).

## Out of Scope

- Changing any production validation (seq-2 document owns it).
- Crawl-payload `chunk_type` handling.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 20261110-114644 | 20261110-114644 | Test-only procedure: no production change |
| 2 | Add or update tests per Validation plan | Completed | 20261110-114644 | 20261110-114644 |  |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | — | 20261110-120906 | end-of-unit gate: tests/rag/ingestion 337 passed; full suite 12133 passed; diff-cover 100%; ruff/mypy/lint-imports pass |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Completed | — | — | N/A: not in scope N/A: not in scope |

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
- **Requirement ID**: `REQ-002` (reject out-of-schema `chunk_type` at read time)
- **Source issue**: issues/20261108-131234_ragrev015_poison-chunk-groups-retried.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261108-170534_ragrev015_poison-chunk-groups-retried.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261109-232810
- **Related target files**: `tests/rag/ingestion/test_pipeline_utils_strict.py`