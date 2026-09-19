## Goal
Add unit tests for the new `classify` subcommand in
`tests/tools/test_manage_frontmatter.py`, covering a confidently-classifiable
case and an ambiguous case (`REQ-007`).

## Scope
In scope: new test functions for `cmd_classify()` only. Out of scope: modifying
existing `cmd_add_missing`/`cmd_rename_category_to_area`/`cmd_dedupe_lists`
tests.

## Assumptions
- File exists (confirmed via `ls tests/tools/test_manage_frontmatter.py`). Read
  its existing test structure (fixture style, `tmp_path` usage) immediately
  before writing new tests, matching whatever pattern `cmd_add_missing`'s tests
  already use.
- Depends on seq 03 (`tools/manage_frontmatter.py`'s `cmd_classify()`) existing.

## Design decisions
Mirror `cmd_add_missing`'s existing test structure exactly (read the file
first) — construct a `tmp_path`-based fake `docs/` directory with 2 files: one
with a clear classification signal (e.g. a filename containing
`-reference-api`) and one without any signal, then assert `cmd_classify()`
reports the first as confident and the second as ambiguous, and that neither
file's content is modified.

## Alternatives considered
N/A: `cmd_add_missing`'s existing test structure is the direct required
precedent — no alternative was considered.

## Implementation
### Target file
tests/tools/test_manage_frontmatter.py

### Procedure
1. Read the existing file in full to identify `cmd_add_missing`'s test fixture
   pattern (how it constructs a temp `docs/` directory and invokes the
   command).
2. Add 2 new test functions: one confidently-classifiable case, one ambiguous
   case, following that exact pattern for `cmd_classify()`.
3. Add an assertion in both new tests that no file's content changed after the
   dry-run/report-only invocation (confirms the "modifies no file" completion
   criterion from seq 03).

### Method
Direct code edit (`Edit` tool), following the file's own existing pattern
exactly (determined by reading it first).

### Details
- Confident case: a temp file named to match one of seq 03's actual inference
  signals (e.g. containing `-reference-api` in its filename) — read seq 03's
  committed implementation to use a signal it actually recognizes, not a
  guessed one.
- Ambiguous case: a temp file with a generic name (e.g. `notes.md`) matching no
  signal.
- Both tests must assert the file's on-disk content is byte-identical
  before/after the `classify` invocation (report-only, no `--fix`).

## Compatibility considerations
Additive test-only change.

## Security considerations
N/A: test code only, uses `tmp_path`.

## Rollback considerations
`git checkout -- tests/tools/test_manage_frontmatter.py` reverts this row
independently.

## Validation plan
- `uv run pytest tests/tools/test_manage_frontmatter.py -v` — all tests
  (existing + new) pass.
- `uv run ruff check tests/tools/test_manage_frontmatter.py`, `uv run mypy
  tests/tools/test_manage_frontmatter.py`.

## Completion criteria
- 2 new tests (confident + ambiguous) exist and pass, both asserting no file
  modification.
- Existing `cmd_add_missing`/`cmd_rename_category_to_area`/`cmd_dedupe_lists`
  tests are unmodified and still pass.

## Out of scope
Modifying existing subcommand test coverage.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | Depends on seq 03 landing first |
| 2 | Add or update tests per Validation plan | Pending | — | — | This document's own Target file IS the test file |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | `uv run pytest tests/tools/test_manage_frontmatter.py -v` |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Pending | — | — | N/A: test file only |

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
- **Requirement ID**: REQ-007 (unit tests for the classify subcommand)
- **Source issue**: issues/done/20260918-130249_docsmeta01_add-class-front-matter-field.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260919-105328_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260919-115041
- **Related target files**: tests/tools/test_manage_frontmatter.py
