## Goal
- Add regression tests pinning the unmatched-glob failure semantics of `main()` (`REQ-004`: zero-match, one valid file, mixed valid/invalid).

## Scope
- Add one test class to `tests/tools/test_check_docs_structure.py`; existing tests stay untouched.

## Assumptions
- No existing test calls `main()` (grep 2026-10-24: no `main`/`capsys`/`monkeypatch` use), so the class adds its own invocation helper.
- `ROOT_DIR` and `DOCS_DIR` are module constants of `tools.check_docs_structure` (lines 30-31); patching both to a `tmp_path` tree isolates the tests from the real `docs/`.
- `_build_basename_index` uses `rglob`, so an empty or absent docs directory does not raise.
- `_COMPLIANT_DOC` (file top) is a valid document for the default schema; confirm this when running the pass case.
- These tests are written before the `tools/check_docs_structure.py` change (row 01) and fail against the current tool by design.

## Design decisions
- Drive `main()` through `monkeypatch.setattr("sys.argv", [...])` plus `capsys`; no subprocess.
- Use `tmp_path` trees, not repository files, so the tests do not depend on `docs/` content.

## Alternatives considered
N/A: single-function test addition following the file's class-per-behavior layout.

## Implementation
### Target file
`tests/tools/test_check_docs_structure.py`

### Procedure
1. Add the test class `TestUnmatchedGlobs` (new) after `TestDefaultGlobIsRecursive`; import `main` from `tools.check_docs_structure` in the existing import block.
2. Add a helper that patches `ROOT_DIR`, `DOCS_DIR` (to `tmp_path / "docs"`) and `sys.argv`, calls `main()`, and returns `(exit_code, captured)`.
3. Test A, zero-match: argument `nope/*.md` returns 1 and stderr contains `no files matched the given glob(s): nope/*.md`; stderr does not contain `All checks passed`.
4. Test B, one valid file: write `_COMPLIANT_DOC` to `docs/ok.md`, argument `docs/ok.md` returns 0 and stderr contains `All checks passed`.
5. Test C, mixed: a valid-glob file with a structural finding (for example a document with no `## Keywords`) plus `nope/*.md` returns 1, stdout contains the finding, stderr names `nope/*.md`.

### Method
- Assert on exit code and the message substring only; do not assert full output text.

### Details
- Keep type annotations (`-> None`, `tmp_path: Path`, `capsys: pytest.CaptureFixture[str]`, `monkeypatch: pytest.MonkeyPatch`) as the file does.

## Compatibility considerations
N/A: test-only addition.

## Security considerations
N/A: tests write only under `tmp_path`.

## Rollback considerations
N/A: revert the commit.

## Validation plan
- Before row 01: `uv run pytest tests/tools/test_check_docs_structure.py -q -k UnmatchedGlobs` shows tests A and C failing, B passing.
- After row 01: the whole file passes, `TestCheckSizeExceptions` included.
- `uv run ruff format`, `uv run ruff check`, `uv run mypy tests/tools/test_check_docs_structure.py` on the file.

## Completion criteria
- Three new tests exist, fail without the `main()` change, and pass with it; no existing test changed.

## Out of Scope
- Tests for any other `main()` behavior, and edits to existing test classes.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Add `TestUnmatchedGlobs` (new) with the invocation helper and three tests | Completed | — | 20261025-001537 |  |
| 2 | Run the new tests before and after the row 01 change | Completed | — | 20261025-001537 |  |
| 3 | Run ruff and mypy on the file | Completed | — | 20261025-001537 |  |

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
- **Requirement ID**: `REQ-004` (regression tests for empty and mixed globs)
- **Source issue**: `issues/20261024-124138_docs010_check_docs_structure-glob-matching-no-files-passes-silently.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261024-214856_check_docs_structure-glob-matching-no-files-passes-silently.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261024-234854
- **Related target files**: `tests/tools/test_check_docs_structure.py`