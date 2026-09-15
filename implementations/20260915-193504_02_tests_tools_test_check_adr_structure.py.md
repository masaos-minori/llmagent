## Goal
Create `tests/tools/test_check_adr_structure.py`, covering the four scenarios
specified in `REQ-004`: missing-heading (ERROR), Notes-path-absent-from-References
(WARNING), path-present-in-both (no finding), and Notes-has-zero-paths (no
finding regardless of References content).

## Scope
- In scope: unit tests calling `tools/check_adr_structure.py`'s
  `check_known_deviations_heading()`/`check_notes_references_drift()`
  functions directly (not via CLI subprocess), following
  `tests/tools/test_check_adr_reference.py`'s pattern.
- Out of scope: CLI/`--format json` end-to-end testing, `main()` testing —
  not required by `REQ-004` and not covered by the cited precedent test file
  either.

## Assumptions
- `tools/check_adr_structure.py` (sibling procedure 01) already exists with
  the function names/signatures specified in that procedure's Design
  decisions before this procedure's Step 3a re-verification runs; if the
  actual names differ, this procedure's Method section is updated to match
  before writing the test file (Step 3a discipline, not a blind copy).
- `DocFile` construction for test fixtures mirrors
  `test_check_adr_reference.py`'s own fixture-construction pattern (either
  direct `DocFile(path=..., rel_path=..., lines=...)` instantiation or a
  `tmp_path`-based file write + `discover_md_files()` call — confirmed by
  reading the precedent file's actual fixture style before writing, per Step
  3a).

## Design decisions
- Follow `test_check_adr_reference.py`'s structure: one test class per
  function under test (`TestCheckKnownDeviationsHeading`,
  `TestCheckNotesReferencesDrift`), each test constructing minimal in-memory
  `DocFile` instances (or `tmp_path`-backed files, matching whichever the
  precedent file actually uses) rather than reading live repo ADRs — keeps
  tests independent of `docs/adr/`'s live content drifting over time.
- Four required scenarios map to four test methods:
  1. `test_missing_known_deviations_heading_flagged_error` — a `DocFile`
     with no `## Known Deviations` line anywhere; assert one `Issue` with
     `severity == "ERROR"`.
  2. `test_notes_path_absent_from_references_flagged_warning` — a `DocFile`
     whose `## Implementation Notes` cites `` `scripts/foo.py` `` and whose
     `### Implementation References` does not; assert one `Issue` with
     `severity == "WARNING"`.
  3. `test_notes_path_present_in_references_not_flagged` — same shape but
     References also cites `` `scripts/foo.py` ``; assert zero `Issue`s.
  4. `test_notes_with_zero_paths_not_flagged_regardless_of_references` —
     Notes contains only prose (no backtick path), References citing
     something unrelated or nothing; assert zero `Issue`s (this is the
     "skip entirely" branch from `REQ-002`).

## Alternatives considered
- Parametrize all four scenarios into one `pytest.mark.parametrize` test —
  rejected to match `test_check_adr_reference.py`'s existing per-scenario
  method style, keeping intent-revealing test names for future debugging.

## Implementation
### Target file
`tests/tools/test_check_adr_structure.py`

### Procedure
1. Re-read `tools/check_adr_structure.py` (per sibling procedure 01, now
   implemented) to confirm actual function names/signatures/`Issue` field
   names before writing assertions against them.
2. Re-read `tests/tools/test_check_adr_reference.py` in full to copy its
   exact fixture-construction idiom.
3. Write module docstring, imports (`from tools.check_adr_structure import
   check_known_deviations_heading, check_notes_references_drift`, plus
   whatever `DocFile`/`tools._docs_consistency_lib` import the fixture
   pattern requires).
4. Write the two test classes with their four test methods per Design
   decisions.
5. Run `uv run pytest tests/tools/test_check_adr_structure.py -v` and fix
   any mismatch against the actual implementation.

### Method
Direct function-call testing, no subprocess/CLI invocation, no filesystem
I/O beyond what the copied fixture idiom itself requires (`tmp_path` if that
is what the precedent uses).

### Details
- Test names must describe scenario + expected outcome, matching the existing
  file's naming convention exactly (e.g. `test_<condition>_<expected>`).
- Assert on `Issue.severity`/`Issue.message`/`Issue.file` fields precisely
  (not just truthiness of the returned list) to catch severity-level
  regressions specifically, since ERROR vs WARNING is the core distinguishing
  behavior between the two checks.

## Compatibility considerations
N/A: new test file; no other code depends on it.

## Security considerations
N/A: pure unit tests, no I/O beyond fixture construction.

## Rollback considerations
New file — delete if it cannot be made to pass without weakening the
production code's correctness.

## Validation plan
- `uv run pytest tests/tools/test_check_adr_structure.py -v` — all four (or
  more, if edge cases surface during writing) tests pass.
- `uv run ruff format tests/tools/test_check_adr_structure.py && uv run ruff check tests/tools/test_check_adr_structure.py` — clean.
- `uv run mypy tests/tools/test_check_adr_structure.py` — no errors.
- Full `uv run pytest tests/tools/` run — no regressions in sibling test files.

## Completion criteria
- All four `REQ-004` scenarios are covered by a passing, independently
  readable test method.
- Tests exercise the production functions directly, not the CLI.

## Out of scope
- CLI/JSON-output testing, `.pre-commit-config.yaml`/documentation
  registration — covered by sibling procedures.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 20260915-194559 | 20260915-194559 |  |
| 2 | Add or update tests per Validation plan | Completed | 20260915-194559 | 20260915-194559 | This row's target file IS the test file 5 tests written (2 for check (a), 3 for check (b)) — all pass; full tests/tools/ suite (350 passed, 2 pre-existing skips) shows no regression |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20260915-194559 | 20260915-194559 | `tools/` addition's test — use the lighter `routing.md` sequence per sibling procedure 01 ruff format/check, mypy clean; pytest 5/5 passed |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Completed | 20260915-194559 | 20260915-194559 | N/A N/A: docs/00_index.md's only tools/-scope row points to tools/01_overview.md, a pre-existing nonexistent file (confirmed stale reference per prior cycles e.g. implementations/done/20260901-114312_03_..., ...115359_01_...); that row also targets tools/ scripts themselves, not their test files |

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
- **Requirement ID**: REQ-004 — test coverage for the four scenarios
- **Source issue**: issues/done/20260914-124634_docqa05_adr-implementation-notes-lint-tool.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260915-192743_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260915-193504
- **Related target files**: tests/tools/test_check_adr_structure.py