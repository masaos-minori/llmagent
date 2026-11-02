## Goal
- Add tests to `tests/tools/test_stale_detector.py` for companion-aware detection and a no-companion regression (`REQ-004`: `(new)` marks and line citations per companion; unchanged behavior without companions).

## Scope
- Modify only `tests/tools/test_stale_detector.py`: new test classes beside `TestCheckLineRefsScoping`. Test-only; Low blast radius.

## Assumptions
- A1: Step 3a: the module imports `StaleResult` and helpers from `tools.stale_detector`, builds procedures as text written under `tmp_path`, and calls `StaleResult.from_procedure(path, source_dir)` (verified by Read, 2026-11-02). New classes follow that style.
- A2: The behavior under test is created by the `seq` 07 procedure of this Plan; the sibling-resolution tests of flowimp007 (`implementations/20261102-085029_02_*`) edit the same file in other classes (Plan A9). Judged compatible: new classes only, whichever lands later rebases.
- A3: Fixtures create a small source tree under `tmp_path`: a target `scripts/mod.py`, an existing companion `tests/test_mod.py`, and a `tests/` directory for a `(new)` companion.

## Design decisions
- Classes `TestCompanionStaleDetection` (new) and `TestNoCompanionRegression` (new); a helper `_procedure(target, companions_block, body)` assembles the document text.
- The regression test runs one document without a companion section through `from_procedure` and compares `summary` and `mismatches` with a hand-written expected value, not with a recomputation.

## Alternatives considered
- Golden-file comparison against stored output: rejected; an inline expected value is easier to review.

## Implementation
### Target file
`tests/tools/test_stale_detector.py`

### Procedure
1. `TestCompanionStaleDetection` (new): a clean document with an existing companion passes; a `(new)` companion with an existing directory and no file passes; a `(new)` companion whose file exists reports `new_target_exists`; a `(new)` companion in a missing directory reports `new_target_dir_missing`; an existing companion that is absent reports `source_missing` naming the companion; a line citation scoped to the companion resolves against the companion's length (in bounds passes, out of bounds reports `line_out_of_bounds` with the companion suffix); a `(new)` companion's unscoped line citation is skipped; a symbol cited under the companion and absent repository-wide reports `symbol_missing` with the suffix and keeps the `Symbol '<name>' not found in source` phrase.
2. `TestNoCompanionRegression` (new): a document without the companion section yields the same `summary`, `target_file`, and `mismatches` as before, for one clean and one stale example.
3. Run `tests/tools/test_mark_procedure_new_symbols.py` unchanged as the consumer regression.

### Method
- Write fixtures with `tmp_path`, pass `source_dir=tmp_path`, and assert on `result.mismatches[i]["type"]` and the detail text.

### Details
- Companion block used in fixtures: the `### Companion test files` heading, a top-level bullet with the backticked path, and indented `Procedure:` and `Validation:` lines.

## Compatibility considerations
- N/A: tests only; existing cases are not edited.

## Security considerations
- N/A: tests write only under `tmp_path`.

## Rollback considerations
- N/A: revert the commit.

## Validation plan
- `uv run pytest tests/tools/test_stale_detector.py tests/tools/test_mark_procedure_new_symbols.py -v`: all pass.
- `uv run ruff format tests/tools/test_stale_detector.py` and `uv run ruff check tests/tools/test_stale_detector.py`: clean.

## Completion criteria
- Companion `(new)` marks, existing-companion checks, and companion line citations are tested, the no-companion regression passes, and the consumer tests pass (AC-4).

## Out of Scope
- Sibling-resolution tests (flowimp007) and changes to `tests/tools/test_mark_procedure_new_symbols.py`.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Add `TestCompanionStaleDetection` (new) and `TestNoCompanionRegression` (new) | Pending | — | — | |
| 2 | Run the new tests, the consumer regression, and the lint commands in the Validation plan | Pending | — | — | |

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
- **Requirement ID**: REQ-004 (companion and no-companion stale tests)
- **Source issue**: issues/20261030-191615_flowimp009_test-row-grouping.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261102-080828_flowimp009_test-row-grouping.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261102-085649
- **Related target files**: `tests/tools/test_stale_detector.py`
