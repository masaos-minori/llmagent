## Goal
- Add a positive and a negative test for every recognized class, built from the measured tokens, so the new rules and the unchanged reporting of stale Python names are both pinned (`REQ-004`).

## Scope
- Only `tests/tools/test_stale_detector.py`: one new test class using `_check_symbol_refs` directly (as `TestCheckSymbolRefsRepoWideFallback` does) and one end-to-end test through `StaleResult.from_procedure`. Existing tests are not edited.

## Assumptions
- The module already imports `StaleResult`, `Path`, and `_check_symbol_refs`; each case builds an isolated temporary tree so the repository-wide search cannot see the rest of the repository.
- The helper call shape is: a result object, the procedure text, the target source text, the source directory, a target path string, and an empty file cache.

## Design decisions
- Cite the measured tokens exactly (built-in, dunder, rule-code, sibling-number, chapter-id, configuration-key names) so a regression on real text fails.
- Pin the negatives per class: an unmatched chapter id, a chapter id that shares text without the separator, a comment-only configuration mention, and stale Python names of each shape.

## Alternatives considered
N/A: the Plan Design section already fixed the approach for this row.

## Implementation
### Target file
`tests/tools/test_stale_detector.py`

### Procedure
1. Add a new test class after `TestFromProcedureDeclaredNewTarget`, with a small static helper that runs the symbol check for a procedure text against an empty target text in a given temporary directory and returns the list of names reported (parsed from the mismatch details), and a helper that writes a file given a directory, a relative path, and text, creating parents.
2. Add test_builtin_and_dunder_names_are_not_reported, parametrized over LookupError, DeprecationWarning, __slots__, and __init_subclass__ written in backticks in a sentence; expect no names reported.
3. Add test_rule_codes_are_not_reported over RUF100, F841, and I001; and test_sibling_numbers_are_not_reported over _01 and _10; expect no names reported.
4. Add test_chapter_id_that_prefixes_a_docs_file_is_not_reported: write a docs file named agent_04_01_state-model.md under a docs subdirectory; cite agent_04; expect nothing reported. Add test_unmatched_chapter_id_is_reported: cite agent_90 with the same tree; expect it reported. Add test_chapter_id_without_separator_is_reported: a docs file named agent_040_x.md and the citation agent_04; expect it reported.
5. Add test_configuration_keys_are_not_reported: write a settings file with a comment line mentioning healthcheck_mode, an assignment concurrency_enabled_flag, and a table header with a dotted name whose last part is alpha_server; a project settings file with an assignment asyncio_mode; a deploy script with an assignment MISSING_TABLES; a schema file with a create-table statement naming session_notes; and a JSON schema file with a key event_name. Cite the six real keys; expect nothing reported.
6. Add test_comment_only_configuration_mention_is_reported: cite healthcheck_mode with the same tree; expect it reported. Add test_name_absent_from_configuration_is_reported: cite a snake_case name that is in none of the files; expect it reported.
7. Add test_stale_python_names_are_still_reported: cite removed_helper_function, RemovedClassName, and _removed_private; expect all three reported.
8. Add an end-to-end test through `from_procedure`: a temporary tree with an existing target file, a docs file, and a settings file; a procedure whose body cites LookupError, RUF100, _01, agent_04 and one stale name; expect exactly one symbol_missing mismatch naming the stale name.
9. Run the new tests against the unmodified detector and confirm the positive cases fail while the negatives (unmatched id, no-separator id, comment-only mention, absent name, stale Python names) pass.

### Method
- Follow the existing style: plain test functions in a class, `tmp_path` for the source directory, `pytest.mark.parametrize` for the token lists, and the module's existing imports.

### Details
- Use plain names for new tests and keep absent names in prose unquoted unless the case needs them checked.
- Do not modify existing tests.

## Compatibility considerations
N/A: test-only change.

## Security considerations
N/A: no input handling, credentials, or trust boundary is touched.

## Rollback considerations
N/A: revert the commit.

## Validation plan
- `uv run pytest tests/tools/test_stale_detector.py -v`; before procedure 01 the positive cases fail and the negatives pass; after it all pass together with the 82 existing tests.
- `uv run ruff format --check tests/tools/test_stale_detector.py`, `uv run ruff check tests/tools/test_stale_detector.py`.
- Execution order for the whole plan: procedure 02 (tests) first, then 01 (code), then 03 (documentation); the new-class tests must be seen failing before the code is edited.

## Completion criteria
- The new tests exist; the positive cases fail on the old detector and pass after procedure 01; the negatives pass before and after; existing tests are unchanged and pass.

## Out of scope
- Tests for the documentation row and for other false-positive classes.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Add the per-class and stale-Python-name tests | Completed | 20261012-180706 | 20261012-180706 | stale_detector clean; changed: tests/tools/test_stale_detector.py (TestSymbolCheckNonPythonNames, 17 cases); 12 positives failed on old code, 5 negatives passed as expected |
| 2 | Run the validation sequence (`rules/toolchain.md`) for the touched file | Completed | 20261012-180706 | 20261012-180706 | ruff format and check pass; 99 passed |

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
- **Source issue**: issues/done/20261012-172959_stale003_stop-flagging-non-python-names-as-missing.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/done/20261012-175722_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261012-175907
- **Related target files**: tests/tools/test_stale_detector.py