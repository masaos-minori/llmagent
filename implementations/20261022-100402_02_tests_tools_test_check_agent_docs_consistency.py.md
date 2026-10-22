## Goal
Update the two tests that assert the old anchor behavior and add anchor unit tests for the new contract (REQ-005: update the old tests, add tests for valid, stale, same-page, and duplicate-heading anchors).

## Scope
- Edit `TestCheckBrokenInternalLinks` only; other test classes are untouched.

## Assumptions
- `_mk_file(rel, lines)` builds a `DocFile` with fake path and given lines, so same-page anchors are resolved from `lines`; cross-document anchors read real files written under `tmp_path`.
- The anchor Warning is emitted by `check_broken_internal_links` with severity `WARNING` and a message containing the anchor.

## Design decisions
- Replace the two old tests (they encode "anchors are ignored") instead of keeping them, as the Plan states (REQ-005).
- One behavior per test, using synthetic content only (the file's stated convention).

## Alternatives considered
N/A: contract change; no alternative keeps the old assertions valid.

## Implementation
### Target file
`tests/tools/test_check_agent_docs_consistency.py`

### Procedure
1. Replace `test_anchor_only_link_skipped` with two tests: a same-page anchor with no matching heading yields one WARNING; a same-page anchor matching a `## Section` heading in the doc's own lines yields none.
2. Replace `test_link_with_anchor_to_existing_file_no_issue` with: a target file containing `## Some Heading` and a link `#some-heading` yields none.
3. Add tests: stale cross-document anchor yields one WARNING mentioning the anchor; duplicate headings resolve `#setup`, `#setup-1` and flag `#setup-2`; a heading inside a fenced code block is not an anchor; a missing target file with an anchor is still exactly one ERROR.

### Method
- Write target files with `(tmp_path / name).write_text(...)` and assert on `len(issues)`, `issues[0].severity`, and message content.
- Keep module-level imports unchanged (`check_broken_internal_links` is already imported).

### Details
- The fenced-code test writes a target file with a ```` ``` ```` block containing `## Hidden` and links `#hidden`, expecting one WARNING.
- Keep all other tests in the class (missing file, external link, subdirectory) unchanged.

## Compatibility considerations
N/A: test-only change; it follows the library contract change of the sibling procedure.

## Security considerations
N/A: temporary files only.

## Rollback considerations
N/A: revert the commit together with the library change.

## Validation plan
- `uv run pytest tests/tools/test_check_agent_docs_consistency.py -q`, then `uv run pytest tests/tools -q`.
- `uv run ruff format`/`check` on the file.

## Completion criteria
- The two replaced tests and the new tests pass; they fail if anchor resolution is removed from the library.
- No other test in the file changed.

## Out of Scope
- Tests for the structure checker and other domains.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Replace the two old anchor tests | Pending | — | — | |
| 2 | Add the valid, stale, same-page, duplicate, fenced, and missing-file tests | Pending | — | — | |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |

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
- **Requirement ID**: `REQ-005` (update and add anchor tests)
- **Source issue**: `issues/20261021-101812_anchorcheck_add-a-dedicated-anchor-validation-check-for-docs-links.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261022-093452_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261022-100402
- **Related target files**: tests/tools/test_check_agent_docs_consistency.py
