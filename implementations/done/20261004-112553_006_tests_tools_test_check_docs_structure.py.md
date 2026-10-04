## Goal
Update and extend `tests/tools/test_check_docs_structure.py` for the new Related section rules (REQ-003: keep tests aligned with the checker).

## Scope
- In: fixtures that embed `## Related Documents`, plus new cases.
- Out: tests for size, H1, links, and front matter fields.

## Assumptions
- Verified: several fixtures in this file contain `## Related Documents`; those that represent non-ADR documents would now produce a finding and must be updated.
- Fixtures meant to be clean must stay clean under the new rules.

## Design decisions
- Remove the section from non-ADR fixtures; keep it in ADR fixtures; add new cases rather than reshaping existing assertions.

## Alternatives considered
- Leave fixtures and filter findings in assertions: rejected; hides the new behavior.

## Implementation
### Target file
`tests/tools/test_check_docs_structure.py`

### Procedure
1. Update non-ADR fixtures to drop the Related section while keeping `## Keywords`.
2. Add cases: ADR without the section is reported; non-ADR without it passes; non-ADR with any of the three headings is reported; ADR front matter missing a body reference is reported; a covered ADR passes.

### Method
- Build ADR fixtures under a path containing `10_adr`.
- Assert on the exact finding text prefix for each new rule.

### Details
- Keep existing assertions for unrelated checks unchanged.
- Fixtures remain minimal.

## Compatibility considerations
- Test-only change.

## Security considerations
- Tests write only inside `tmp_path`.

## Rollback considerations
- Revert the commit together with row 005.

## Validation plan
- `uv run pytest tests/tools/test_check_docs_structure.py`.
- `uv run ruff format` and `uv run ruff check` on the file, and `uv run mypy tests/tools/test_check_docs_structure.py`.

## Completion criteria
- Every rule in row 005's Completion criteria has at least one test.
- No fixture for a non-ADR document still carries a Related section.

## Out of scope
- Tests for checks this Plan does not change.
- Any production code change.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Update non-ADR fixtures and add the new cases | Completed | 20261004-125157 | 20261004-125157 | changed: tests/tools/test_check_docs_structure.py (6 fixtures updated, new cases added) |
| 2 | Run the tests against the implementation from row 005 | Completed | 20261004-125157 | 20261004-125157 | 59 passed; diff coverage of tools/check_docs_structure.py 100% |
| 3 | Run ruff and mypy on the test file | Completed | 20261004-125157 | 20261004-125157 | ruff, mypy clean; full suite 8092 passed, 6 failed (same unrelated baseline) |
| 4 | N/A: no documentation change for a test file | Completed | 20261004-125157 | 20261004-125157 | N/A: no documentation change for a test file |

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
- **Requirement ID**: `REQ-003` (test the new Related section rules)
- **Source issue**: issues/done/20261004-111518_relateddocsmerge_consolidate-front-matter-related-and-body-related-documents.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261004-111806_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261004-112553
- **Related target files**: tests/tools/test_check_docs_structure.py