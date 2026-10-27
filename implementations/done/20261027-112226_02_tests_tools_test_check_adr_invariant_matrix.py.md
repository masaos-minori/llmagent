## Goal

Add tests for the two new rules of `tools/check_adr_invariant_matrix.py` (`REQ-005`: empty cell without marker, empty cell with marker, matching and disagreeing citations, first and last rows of a table).

## Scope

- Edit only `tests/tools/test_check_adr_invariant_matrix.py`: add test classes; keep the six existing classes and the `_matrix`/`_HEADER`/`_SEPARATOR` helpers unchanged.

## Assumptions

- Row 01 is applied first; it creates `check_adr_body_evidence_cells` (new) and `check_body_index_agreement` (new), which this row imports. `tools/stale_detector.py` accepts names created by an earlier-`seq` row.
- Both functions are pure over lines and a mapping (row 01 Design decisions), so the new tests use in-memory lines and need no real files and no production state.
- The marker is a cell beginning with `Not verified` (confirm against the implemented text, as in row 01).
- Plan overlap check: no other Frozen Plan targets this file.

## Design decisions

- One class per behavior: `TestBodyEmptyCellWithoutMarker` (new), `TestBodyEmptyCellWithMarker` (new), `TestBodyIndexAgreement` (new), `TestBodyIndexDisagreement` (new), `TestBodyTableBoundaries` (new), each with small builder helpers for an ADR body table.
- Assert on `severity == "WARNING"` for new findings, and add one regression test that the existing rule still reports `ERROR` for a missing path.

## Alternatives considered

N/A: follows the structure of the existing test module.

## Implementation
### Target file

`tests/tools/test_check_adr_invariant_matrix.py`

### Procedure

1. Extend the import from `tools.check_adr_invariant_matrix` with the two new function names.
2. Add a helper that builds an ADR body with a `### Automated Tests` table (`| Test | Verifies | Type | Blocking | Implementation |`) from rows.
3. Add the five classes of Design decisions: an empty `-` cell without marker yields one finding naming the invariant; a cell `Not verified (...)` yields none; equal path unions yield none; different unions yield one `WARNING`; the first and the last table rows are both parsed (an empty cell in each is reported).
4. Add cases for an index row that names two ADRs (`ADR-002 INV-01, INV-02 and ADR-004 INV-07, INV-10`), a body table without an `Implementation` column (skipped, no finding), and a path cited as bare `file.py` versus `file.py::test` (equal).

### Method

Plain pytest functions and classes with type annotations; cited paths in fixtures may be strings only, because the new rules do not check file existence.

### Details

- Follow the existing style: `from __future__ import annotations`, English docstrings, line length 88.
- Do not patch module symbols; no `patch("module.Symbol")` is needed.

## Compatibility considerations

N/A: test-only change; existing tests keep their imports and behavior.

## Security considerations

N/A: tests use in-memory data only.

## Rollback considerations

N/A: revert the commit.

## Validation plan

- `uv run pytest tests/tools/test_check_adr_invariant_matrix.py -v` (new and existing tests pass).
- `uv run ruff format` and `uv run ruff check` on this file; `uv run mypy tools/check_adr_invariant_matrix.py` for the module under test.
- `uv run python tools/check_mock_patch_targets.py` only if a `patch(` call is added (none expected).

## Completion criteria

- The five cases of `REQ-005` are covered and pass, and all existing tests still pass.
- ruff reports no finding for the file.

## Out of Scope

- Changing the six existing test classes.
- Tests for `.github/run_cited_adr_tests.py`.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Add the new test classes and helpers | Completed | 20261027-122508 | 20261027-123400 | After row 01 Changed: tests/tools/test_check_adr_invariant_matrix.py (new classes TestBodyEmptyCellWithoutMarker, TestBodyEmptyCellWithMarker, TestBodyIndexAgreement, TestBodyIndexDisagreement, TestBodyTableBoundaries, TestExistingRuleUnchanged, TestCollectIssues; imports extended; existing six classes and helpers unchanged). One failing new test fixed by creating the cited file in the fixture (existing rule correctly reported ERROR for a missing path); expectations not loosened. |
| 2 | Run pytest, ruff format and ruff check for this file | Completed | 20261027-123400 | 20261027-123400 | 28 passed (random and fixed order); ruff format/check clean; mypy clean for the test file and the module; check_mock_patch_targets: no findings (no patch() call added). Full suite once: 10175 passed, 9 failed, all pre-existing and unrelated (8 stale-reference eventbus auth tests; test_live_docs_have_no_drift caused by an untouched eventbus_08_reference_api.md generated block). |

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
- **Requirement ID**: `REQ-005` (tests for the new rules)
- **Source issue**: issues/20261027-102002_govrev005_adr-matrix-checker-extension.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261027-105004_govrev005_adr-matrix-checker-extension.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261027-112226
- **Related target files**: tests/tools/test_check_adr_invariant_matrix.py