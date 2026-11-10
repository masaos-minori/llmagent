## Goal

- Keep the chunk-grouping suite aligned with the strict `chunk_type` domain: grouping fixtures must use an in-domain value, and one new case must pin that an out-of-domain payload is reported rejected while the rest of the group is still grouped (`REQ-002`).

## Scope
**Release unit**: ragrev015-core (Plan `### Release units`; owner-declared batch unit 20261110)

- `tests/rag/ingestion/test_chunk_grouping.py` only. No production change: the rejection path already exists in `scripts/rag/ingestion/chunk_grouping.py` `group()` L64-110, which catches `ChunkFormatError` and appends `(path, IngestionFailureReason.PARSE_FAILED)` (L80-88).

## Assumptions

- Measured at HEAD `02f3143e2` in a scratch worktree: applying only the `read_chunk_json` `chunk_type` domain check makes 9 tests in this file fail; the full-suite failure count is unchanged outside `tests/rag/ingestion`.
- All 9 measured failures come from one fixture value, not from grouping logic. Failing names (measured): `TestGenerationSafeKey::test_group_key_carries_url_and_fetched_at`, `TestGenerationSafeKey::test_same_generation_files_share_one_group`, `TestGenerationSafeKey::test_two_generations_form_distinct_groups`, `TestGenerationSafeKey::test_generation_distinguished_by_etag`, `TestRejectedReporting::test_file_url_is_accepted`, `TestRejectedReporting::test_invalid_url_reports_validation_failed`, `TestRejectedReporting::test_malformed_payload_reports_parse_failed`, `TestSkipWarnings::test_invalid_url_logs_warning`, `TestSkipWarnings::test_no_warning_for_accepted_files`.

## Design decisions

- Fix the fixture, not the assertions: `_payload()` (current L42-55) uses `"chunk_type": "paragraph"`, which is out of the schema domain, so every group built from it becomes rejected. The tests themselves assert grouping behavior that is still correct for in-domain payloads.
- Express the new domain case as a grouping-level test (one valid file plus one out-of-domain file) rather than a `read_chunk_json` unit test, because the `read_chunk_json` domain itself is covered by the seq-5 document; what must be pinned here is the reason code and that the group survives.

## Alternatives considered

- Changing the out-of-domain fixtures to assert rejection instead of fixing them: rejected — those tests exist to prove grouping and warning behavior for valid payloads; rewriting them to expect rejection would delete that coverage.

## Implementation
### Target file
- `tests/rag/ingestion/test_chunk_grouping.py`

### Procedure
- Align the grouping payload fixture with the schema domain, then add one rejected-member case.

### Method
- In `_payload()`, change the fixture default (current L50) `"chunk_type": "paragraph"` to `"chunk_type": "text"`.
- Add to `TestRejectedReporting`: build two chunk files, one with the default payload and one with `_payload(chunk_type="chunk")`; assert `rejected == [(<bad name>, IngestionFailureReason.PARSE_FAILED)]` and that the valid file is the only member of exactly one group.
- Leave `test_chunk_generation_dataclass_is_hashable_and_frozen` (current L222-238) unchanged: it constructs `ChunkGeneration` directly (current L232 `chunk_type="paragraph"`), which does not pass through `read_chunk_json`, so the domain rule does not apply. Measured: it does not fail under either patch.

### Details
- `group()` classifies an out-of-domain `chunk_type` as `PARSE_FAILED` because the rejection arrives as `ChunkFormatError` from `read_chunk_json` (chunk_grouping L78-88); `VALIDATION_FAILED` is reserved for the empty-URL and invalid-URL branches (L89-109). The new case must assert `PARSE_FAILED`, not `VALIDATION_FAILED`.
- The file-level `rejected` list is consumed by `ingester.py` L162-163 and routed by `_route_group_failed` (L396-400); no change to that path is in scope here.

## Compatibility considerations

- Fixture-only change plus one added test; no assertion is weakened.

## Security considerations
N/A: test data only.

## Rollback considerations
N/A: revert the single commit.

## Validation plan

- `uv run pytest tests/rag/ingestion/test_chunk_grouping.py -q` — the 9 measured failures are green after the fixture change, before the production change lands.
- The new rejected-member case fails on HEAD (an out-of-domain payload is grouped, not rejected) and passes after the seq-2 change.
- `uv run pytest tests/rag/ingestion -q` regression.

## Completion criteria

- The 9 measured fixture-caused failures pass, and a payload with `chunk_type="chunk"` is reported as `PARSE_FAILED` while its group's other file is still grouped (AC-2 at the grouping boundary).

## Out of Scope

- `scripts/rag/ingestion/chunk_grouping.py` behavior (already rejects and reports; verified, unchanged).
- `ChunkGeneration` value-object validation.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 20261110-115136 | 20261110-115136 | Test-only procedure: no production change |
| 2 | Add or update tests per Validation plan | Completed | 20261110-115136 | 20261110-115136 |  |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | — | 20261110-120906 | end-of-unit gate: tests/rag/ingestion 337 passed; full suite 12133 passed; diff-cover 100%; ruff/mypy/lint-imports pass |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Completed | — | 20261110-120924 | N/A: not in scope |

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
- **Related target files**: `tests/rag/ingestion/test_chunk_grouping.py`