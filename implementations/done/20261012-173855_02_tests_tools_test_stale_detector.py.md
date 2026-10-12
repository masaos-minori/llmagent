## Goal
- Add end-to-end tests for every declared-new target case, so the new behavior and the unchanged behavior for unmarked targets are both pinned (`REQ-004`).

## Scope
- Only `tests/tools/test_stale_detector.py`: one new test class that drives `StaleResult.from_procedure` through a temporary source tree. Existing tests are not edited.

## Assumptions
- The module already imports `StaleResult` and `Path`; the new class follows the pattern of `TestFromProcedureFalsePositives`, which writes a small source file and a procedure document under a temporary directory and calls the entry point with that directory.
- Tests build the procedure text as a Python string; a Target file section names the path under test.

## Design decisions
- Test through `from_procedure` only, because the behavior spans target parsing, the directory and existence checks, and the content checks; the private helper is not tested directly.
- Pin the unchanged behavior too (unmarked absent target, existing target) so an accidental widening fails.

## Alternatives considered
N/A: the Plan Design section already fixed the approach for this row.

## Implementation
### Target file
`tests/tools/test_stale_detector.py`

### Procedure
1. Add a new class after `TestFromProcedureFalsePositives`, with a small static helper that writes a procedure document into the temporary directory: a Target file section with the given target text, followed by a body string. The helper also creates an existing directory named tools under the temporary directory, and an existing source file named existing_mod.py in it that defines one function, for the cases that need an existing file or a cross-file symbol.
2. Add test_declared_new_target_in_existing_directory_is_clean: the target is a backticked path to a file that does not exist, in the existing directory, followed by the marker (new); the body has one plain statement; expect not stale.
3. Add test_unmarked_absent_target_is_still_source_missing: the same target without the marker; expect exactly one mismatch of type source_missing.
4. Add test_declared_new_target_with_missing_directory_is_reported: the target is in a directory that does not exist; expect one mismatch of type new_target_dir_missing.
5. Add test_declared_new_target_that_already_exists_is_reported: the target is the existing source file followed by the marker; expect one mismatch of type new_target_exists.
6. Add test_declared_new_target_checks_symbols: in the body, cite the function defined in the existing source file in backticks (expect not reported), cite an unmarked backticked snake_case name that exists nowhere (expect one symbol_missing), and cite another such name followed by the marker (expect not reported).
7. Add test_declared_new_target_reports_before_block: the body contains a code block introduced by a Before marker line per the detector's block format; expect one mismatch of type before_block_missing.
8. Add test_declared_new_target_skips_unscoped_line_citations: the body cites a line number far beyond one line with no other file named in the same citation; expect not stale. Add the same citation for an unmarked absent target only if it adds coverage beyond the source_missing test; otherwise skip it.
9. Add test_declared_new_target_still_checks_scoped_line_citations: the body cites a line number, with the existing source file named in backticks in the same bullet, once within its length (expect not stale) and once beyond it (expect one line_out_of_bounds mismatch naming that file).
10. Add test_marker_text_does_not_change_reported_target_path: for a declared-new target, assert the result's target file is the bare path without the marker.
11. Run the new tests against the unmodified detector and confirm the declared-new cases fail (they are reported source_missing) while the unmarked-target case passes.

### Method
- Follow the existing style: plain test functions in a class, `tmp_path` for the source directory, and the module's existing imports.
- For the Before-block case, reuse the exact marker format shown by the existing Before-block tests in this file.

### Details
- Use plain names for the new tests and for the cited absent names in prose; backtick only the names the case needs to be checked.
- Do not modify existing tests.

## Compatibility considerations
N/A: test-only change.

## Security considerations
N/A: no input handling, credentials, or trust boundary is touched.

## Rollback considerations
N/A: revert the commit.

## Validation plan
- `uv run pytest tests/tools/test_stale_detector.py -v`; before procedure 01 the declared-new cases fail and the unmarked case passes; after it all pass together with the 73 existing tests.
- `uv run ruff format --check tests/tools/test_stale_detector.py`, `uv run ruff check tests/tools/test_stale_detector.py`.
- Execution order for the whole plan: procedure 02 (tests) first, then 01 (code), then 03, 04 and 05 (documentation); the new-policy tests must be seen failing before the code is edited.

## Completion criteria
- The new tests exist; the declared-new cases fail on the old detector and pass after procedure 01; the unmarked-target case passes before and after; existing tests are unchanged and pass.

## Out of scope
- Tests for the documentation rows, for the generator, and for other false-positive classes.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Add the declared-new target tests | Completed | 20261012-174543 | 20261012-174543 | stale_detector clean; changed: tests/tools/test_stale_detector.py (TestFromProcedureDeclaredNewTarget, 9 tests); 7 failed on old code, the unmarked-target and bare-path tests passed as expected (procedure step 11 corrected in wording only: the bare-path test pins unchanged behavior) |
| 2 | Run the validation sequence (`rules/toolchain.md`) for the touched file | Completed | 20261012-174543 | 20261012-174543 | ruff format and check pass; 82 passed |

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
- **Requirement ID**: `REQ-004`
- **Source issue**: issues/done/20261012-172916_stale002_allow-new-target-files-in-stale-detector.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261012-173651_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261012-173855
- **Related target files**: tests/tools/test_stale_detector.py