## Goal
Regenerate `EXPECTED_WITHIN_FILE_PAIRS` in `tests/tools/test_check_docs_quality.py` after the Related sections are removed (REQ-007: the exact-equality test must pass again).

## Scope
- In: the `EXPECTED_WITHIN_FILE_PAIRS` set and its "last refreshed" comment.
- Out: test logic, thresholds, and the checker.

## Assumptions
- Verified: the test asserts `current_pairs == EXPECTED_WITHIN_FILE_PAIRS` exactly, and seven baseline entries name 'Related Documents'.
- Run this row after the migration rows so the regenerated set reflects the final documents.
- Other documents may also have changed in the working tree; only differences explained by this migration are acceptable.

## Design decisions
- Regenerate from checker output rather than editing entries by hand, as the baseline comment instructs.
- Review the diff: the expected change is removal of entries involving the removed sections only.

## Alternatives considered
- Loosen the assertion to a subset check: rejected; weakens the guard for unrelated drift.

## Implementation
### Target file
`tests/tools/test_check_docs_quality.py`

### Procedure
1. Run `uv run python -m tools.check_docs_quality` and collect the within-file pairs.
2. Replace the set contents with the regenerated pairs.
3. Inspect the diff of the set: every removed entry must involve a removed Related section; any other difference is investigated, not accepted.
4. Update the "last refreshed" date in the comment.

### Method
- Compare old and new sets as sets; list added and removed entries.
- Added entries are unexpected for this change and require explanation before acceptance.

### Details
- Keep the file's existing formatting and sort order of entries.
- Do not change the cross-file assertion that follows.

## Compatibility considerations
- Test-data change only.

## Security considerations
- None: no I/O beyond reading documents.

## Rollback considerations
- Revert the commit together with the migration commits it follows.

## Validation plan
- `uv run pytest tests/tools/test_check_docs_quality.py`.
- `uv run ruff format tests/tools/test_check_docs_quality.py` and `uv run ruff check` on it.

## Completion criteria
- The test passes with the regenerated set.
- The set diff contains only removals explained by removed Related sections.

## Out of scope
- Any change to what the checker reports.
- Other baseline files.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Regenerate the pair set from checker output | Completed | 20261004-125204 | 20261004-125204 | N/A: already satisfied; the baseline holds no 'Related Documents' pairs since commit 974e13f10 |
| 2 | Review the set diff and explain every difference | Completed | 20261004-125204 | 20261004-125204 | N/A: no set diff; baseline equals current pairs before and after the migration |
| 3 | Run `tests/tools/test_check_docs_quality.py` | Completed | 20261004-125204 | 20261004-125204 | tests/tools/test_check_docs_quality.py passes against the migrated docs |
| 4 | Update the comment's refresh date | Completed | 20261004-125204 | 20261004-125204 | N/A: no change to the file, so its refresh-date comment stays |

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
- **Requirement ID**: `REQ-007` (regenerate the within-file similarity baseline)
- **Source issue**: issues/done/20261004-111518_relateddocsmerge_consolidate-front-matter-related-and-body-related-documents.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261004-111806_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261004-112553
- **Related target files**: tests/tools/test_check_docs_quality.py