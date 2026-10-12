## Goal
- Add tests for both false-positive classes and for the behavior that must not change, including an end-to-end check on the mock001 text (`REQ-003`).

## Scope
- Only `tests/tools/test_stale_detector.py`: new tests in `TestCheckImportRefs` and `TestCheckSymbolRefs`, and one new class for end-to-end tests of `from_procedure`. Existing tests are not edited.

## Assumptions
- The private helpers are already imported by this module and are called directly with strings, as the existing tests do; the end-to-end tests build a temporary source tree and a procedure document under a temporary directory.
- A procedure document needs a Target file section naming a file that exists under the temporary source directory.

## Design decisions
- Test the policy where it lives: unit tests for the import and symbol checks, plus end-to-end tests proving the whole path.
- Assert the unchanged behavior too (line-leading import before a heading still reported; followed by ordinary text still not reported; unmarked missing names still reported) so an accidental widening fails.

## Alternatives considered
N/A: the Plan Design section already fixed the approach for this row.

## Implementation
### Target file
`tests/tools/test_stale_detector.py`

### Procedure
1. In `TestCheckImportRefs` add test_prose_sentence_before_heading_is_not_an_import_reference: a bullet whose prose mentions an import of annotations inside backticks, followed by a blank line and a heading, checked against a source with no such import; expect not stale. Reproduce the bullet from the Issue's Background.
2. Add test_line_leading_import_before_heading_is_still_checked: a bulleted statement for a module that is absent from the source, followed by a heading; expect an import_missing mismatch. Add a variant with the statement wrapped in backticks.
3. Add test_backtick_wrapped_existing_import_is_not_reported: the existing statement wrapped in backticks, followed by a heading, with the statement present in the source; expect not stale.
4. Add test_line_leading_import_followed_by_text_stays_unreported: a missing statement on its own line followed by ordinary text; expect not stale (this pins the unchanged coverage).
5. Add test_mid_sentence_import_phrase_is_not_checked: a sentence containing an import phrase in the middle, followed by a heading; expect not stale.
6. Add test_new_marked_import_is_exempt: a wrapped statement followed by (new), then a heading; expect not stale; assert the same text without (new) is stale.
7. In `TestCheckSymbolRefs` add test_new_marked_symbol_is_exempt (parametrized over the marker with one space and with none): a backticked name absent from the source followed by (new); expect not stale.
8. Add test_new_marker_applies_only_to_its_own_token: two names in one sentence, the first marked, the second not and absent; expect exactly one symbol_missing mismatch naming the second.
9. Add a class for end-to-end tests that writes a small source file and a procedure document into a temporary directory and calls `from_procedure` with that directory: one test with the mock001 procedure 01 sentence, one with the three mock001 procedure 02 test names each followed by (new), and one with the same three names without the marker asserting three symbol_missing mismatches.
10. Run the new tests against the unmodified detector and confirm the cases about prose, wrapped statements, mid-sentence mentions, the marker, and the end-to-end marked cases fail, while the cases that pin unchanged behavior pass.

### Method
- Follow the existing style: plain test functions grouped by class, `tmp_path` for the source directory, and the module's existing imports.
- For the end-to-end tests write the procedure text as a Python string; the Target file section must name the temporary source file.

### Details
- The mock001 text to reproduce is quoted in the Issue (the prose bullet) and in the Plan Problem section (the test names).
- Use only plain names for the new tests; no new helper beyond a small local function for building the temporary tree is needed.
- Do not modify existing tests.

## Compatibility considerations
N/A: test-only change.

## Security considerations
N/A: no input handling, credentials, or trust boundary is touched.

## Rollback considerations
N/A: revert the commit.

## Validation plan
- `uv run pytest tests/tools/test_stale_detector.py -v`; before procedure 01 the new-policy cases fail and the unchanged-behavior cases pass; after it all pass together with the 60 existing tests.
- `uv run ruff format --check tests/tools/test_stale_detector.py`, `uv run ruff check tests/tools/test_stale_detector.py`.
- Execution order for the whole plan: procedure 02 (tests) first, then 01 (code), then 03, 04 and 05 (documentation); the new-policy tests must be seen failing before the code is edited.

## Completion criteria
- The new tests exist; the new-policy cases fail on the old detector and pass after procedure 01; the unchanged-behavior cases pass both before and after; existing tests are unchanged and pass.

## Out of scope
- The detector itself, other test files, and any change to what existing tests assert.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Add the unit and end-to-end tests and confirm the new-policy cases fail on the unmodified detector | Completed | 20261012-171218 | 20261012-171302 | stale_detector clean; baseline of 60 procedure verdicts saved (42 clean, 18 stale); applied first changed: tests/tools/test_stale_detector.py (+13 test cases, +pytest import); on the unmodified detector 9 fail (prose, wrapped, mid-sentence, marker, e2e marked) and 4 new + 60 existing pass (unchanged-behavior pins) |
| 2 | Run the validation sequence (`rules/toolchain.md`) for the touched file | Completed | 20261012-171404 | 20261012-171404 | ruff format/check pass; 9 new-policy cases fail on the old detector and all 13 pass after procedure 01; 60 existing tests unchanged |

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
- **Requirement ID**: `REQ-003` (regression and true-positive tests)
- **Source issue**: issues/20261012-132457_stale001_fix-stale-detector-false-positives.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261012-132739_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261012-170854
- **Related target files**: tests/tools/test_stale_detector.py