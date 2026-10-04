## Goal
Add unit tests for `merge-related` in `tests/tools/test_manage_frontmatter.py` (REQ-001: lock the merge behavior before documents are rewritten).

## Scope
- In: new test cases and fixtures for `merge-related`.
- Out: changes to existing test classes for other subcommands.

## Assumptions
- Existing tests redirect `DOCS_DIR` to a temporary directory; new tests follow the same pattern.
- Test classes in this file group one behavior each (for example the no-flag, dry-run, and fix paths).

## Design decisions
- One new test class per behavior group, using small fixture documents written to the temporary `docs/` tree.
- Assert on file contents after `--fix` and on file bytes for dry-run (unchanged).

## Alternatives considered
- Snapshot a copy of the real `docs/` tree: rejected; slow, brittle, and mixes unrelated content.

## Implementation
### Target file
`tests/tools/test_manage_frontmatter.py`

### Procedure
1. Add a fixture helper that writes a document with a given front matter block and body.
2. Add test classes for default dry-run, `--fix`, input forms, `related:` shapes, edge cases, ADR handling, and idempotence.
3. Add a recursion test: a document in a subdirectory is processed.

### Method
- Dry-run: no file changes, report lists additions.
- `--fix`: front matter merged in order with new entries appended; body section removed for link-only sections.
- Forms: backtick entry, Markdown link with anchor, `## Related Docs`, `## Related Chapters`, two sections in one file.
- Shapes: block list, empty `related:`, inline `related: []`; unsupported inline non-empty list is reported and skipped.
- Edge cases: self-reference dropped, duplicate dropped, unresolved target reported and not merged, non-link line keeps the section and is reported.
- ADR: front matter extended, body bytes identical.
- Idempotence: second `--fix` changes nothing.

### Details
- Name tests after the behavior, not the implementation.
- Keep fixtures minimal; do not copy production documents.
- Use `tmp_path` and monkeypatch of the tool's `DOCS_DIR` constant as existing tests do.

## Compatibility considerations
- Test-only change; no production behavior is touched.

## Security considerations
- Tests write only inside `tmp_path`.

## Rollback considerations
- Revert the commit; no other file depends on these tests.

## Validation plan
- `uv run pytest tests/tools/test_manage_frontmatter.py`.
- `uv run ruff format tests/tools/test_manage_frontmatter.py` and `uv run ruff check tests/tools/test_manage_frontmatter.py`.
- `uv run mypy tests/tools/test_manage_frontmatter.py` (pre-commit runs mypy on `tests/`).

## Completion criteria
- Every behavior in row 001's Completion criteria has at least one test.
- Tests fail against a build without the subcommand and pass with it.
- Ruff and mypy are clean for the file.

## Out of scope
- Tests for other subcommands.
- Any production code change.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Add fixture helper and test classes for `merge-related` | Completed | 20261004-121203 | 20261004-121203 | stale check clean; changed: tests/tools/test_manage_frontmatter.py; tests exposed an EOF blank-line defect, fixed in tools/manage_frontmatter.py (row 001 scope) |
| 2 | Run the new tests against the implementation from row 001 | Completed | 20261004-121203 | 20261004-121203 | 51 passed; diff coverage of tools/manage_frontmatter.py 100% |
| 3 | Run ruff and mypy on the test file | Completed | 20261004-121203 | 20261004-121203 | ruff, mypy clean; full suite 8072 passed, 7 failed (unrelated, same as known baseline) |
| 4 | N/A: no documentation change for a test file | Completed | 20261004-121203 | 20261004-121203 | N/A: no documentation change for a test file |

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
- **Requirement ID**: `REQ-001` (test the `merge-related` subcommand)
- **Source issue**: issues/done/20261004-111518_relateddocsmerge_consolidate-front-matter-related-and-body-related-documents.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261004-111806_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261004-112553
- **Related target files**: tests/tools/test_manage_frontmatter.py