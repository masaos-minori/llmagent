## Goal
Add tests to `tests/tools/test_rename_doc.py` for front matter `related:` rewriting (REQ-002: lock the new rename behavior).

## Scope
- In: new test cases and fixtures.
- Out: changes to existing link-rewrite tests.

## Assumptions
- Verified: the file has no front matter fixtures today, so new fixtures are needed.
- Existing tests build a temporary `docs/` tree and a git repository context; new tests reuse that setup.

## Design decisions
- Reuse the existing fixture builder; extend it only as needed to emit front matter.
- Assert on planned rewrites in dry-run and on file contents after `--apply`.

## Alternatives considered
- Test only through the real `docs/` tree: rejected; depends on current content.

## Implementation
### Target file
`tests/tools/test_rename_doc.py`

### Procedure
1. Add fixtures with a front matter `related:` block holding bare, `../`, and unrelated entries.
2. Add tests for bare rewrite, `../` rewrite, unrelated entries untouched, unsupported shape fail-closed, dry-run writes nothing, and no duplicate prose-mention report.

### Method
- Bare entry equal to the old basename becomes the new basename.
- A `../` entry becomes the new relative path from that file.
- An entry pointing elsewhere is unchanged.
- A quoted entry that resolves to the old path appears under unresolved and the file is not modified.
- The rewritten entry does not also appear among prose findings.

### Details
- Name tests after observable behavior.
- Keep each fixture to the smallest tree that shows the behavior.

## Compatibility considerations
- Test-only change.

## Security considerations
- Tests write only inside `tmp_path`.

## Rollback considerations
- Revert the commit; no other file depends on these tests.

## Validation plan
- `uv run pytest tests/tools/test_rename_doc.py`.
- `uv run ruff format` and `uv run ruff check` on the file, and `uv run mypy tests/tools/test_rename_doc.py`.

## Completion criteria
- Every behavior in row 003's Completion criteria has at least one test.
- New tests fail without the row 003 change and pass with it.

## Out of scope
- Tests for unrelated rename behavior.
- Any production code change.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Add front matter fixtures and the new test cases | Completed | 20261004-123103 | 20261004-123103 | changed: tests/tools/test_rename_doc.py (7 tests added) |
| 2 | Run the new tests against the implementation from row 003 | Completed | 20261004-123103 | 20261004-123103 | 12 passed; diff coverage of tools/rename_doc.py 97% |
| 3 | Run ruff and mypy on the test file | Completed | 20261004-123103 | 20261004-123103 | ruff, mypy clean; full suite 8080 passed, 6 failed (same unrelated baseline) |
| 4 | N/A: no documentation change for a test file | Completed | 20261004-123103 | 20261004-123103 | N/A: no documentation change for a test file |

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
- **Requirement ID**: `REQ-002` (test front matter rewriting on rename)
- **Source issue**: issues/done/20261004-111518_relateddocsmerge_consolidate-front-matter-related-and-body-related-documents.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261004-111806_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261004-112553
- **Related target files**: tests/tools/test_rename_doc.py