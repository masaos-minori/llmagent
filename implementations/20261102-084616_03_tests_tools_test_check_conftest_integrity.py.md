## Goal

Test the new manifest requirement: the checker reports a finding when `_guard_production_db_files` is missing or not autouse, and the real manifest and real `tests/conftest.py` agree (`REQ-003`: removed detection is reported).

## Scope

- Add test cases to `tests/tools/test_check_conftest_integrity.py` only.

## Assumptions

- Plan overlaps: none names this Plan (`tools/check_plan_target_overlaps.py`, 2026-11-02); no sibling Plan targets this file: compatible.
- Verified 2026-11-02: the existing tests pass a local `REQUIRED_FIXTURES` tuple of two names and use `monkeypatch.setattr(cci, "ROOT_DIR", tmp_path)` with a temporary conftest, so they do not exercise the real manifest; the new tests must use `cci.REQUIRED_AUTOUSE_FIXTURES` explicitly.
- The manifest entry and the fixture are created by procedures 02 and 01 (earlier `seq`).
- `tests/tools/` has no `__init__.py`; the module imports `tools.check_conftest_integrity` as the existing tests do.

## Design decisions

- One test pins the manifest content (`_guard_production_db_files in cci.REQUIRED_AUTOUSE_FIXTURES`); one runs `find_conftest_findings` with the real manifest on a temporary conftest that defines the other three fixtures but not the new one; one runs it against the real `tests/conftest.py` and expects no findings.

## Alternatives considered

- N/A: follows the file's existing temporary-conftest pattern.

## Implementation
### Target file
`tests/tools/test_check_conftest_integrity.py`

### Procedure
1. Add class `TestProductionDbGuardRequired` (new) after `TestMissingRequiredFixture`.
2. Add `test_manifest_lists_session_guard` (new): assert the name is in `cci.REQUIRED_AUTOUSE_FIXTURES`.
3. Add `test_removed_session_guard_is_reported` (new): temporary conftest with the three older fixtures as autouse; call `cci.find_conftest_findings(conftest_path, cci.REQUIRED_AUTOUSE_FIXTURES)` with `ROOT_DIR` monkeypatched; expect exactly one finding, category `conftest-missing-fixture`, detail containing the name.
4. Add `test_guard_present_but_not_autouse_is_reported` (new): same with the guard defined `autouse=False`; expect the same finding.
5. Add `test_real_conftest_has_no_findings` (new): call with the real `cci.CONFTEST_PATH` and manifest, without monkeypatching `ROOT_DIR`; expect `[]`.

### Method
- Build the temporary conftest text from small string constants, using the `_write` helper already in the module.

### Details
- Test 5 depends on procedure 01 being applied; it is the cross-row consistency check.

## Compatibility considerations

- N/A: tests only; existing tests keep their local manifest tuple.

## Security considerations

- N/A: tests write only under `tmp_path`.

## Rollback considerations

- N/A: revert the commit.

## Validation plan

- `uv run pytest tests/tools/test_check_conftest_integrity.py -v` (all pass, including after procedures 01 and 02).
- `uv run ruff format`, `uv run ruff check`, and `uv run mypy` on the test file per `rules/toolchain.md`.

## Completion criteria

- The four new tests exist and pass; removing the name from `tests/conftest.py` makes the real-conftest test fail.

## Out of Scope

- Changes to the checker logic; tests of other checker categories.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Add the four checker tests | Pending | — | — | |
| 2 | Run the test file and the validation sequence (`rules/toolchain.md`) | Pending | — | — | |

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
- **Requirement ID**: `REQ-003` (checker tests for the required detection)
- **Source issue**: issues/20261030-191351_flowimp006_suite-production-guard.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261102-075648_flowimp006_suite-production-guard.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261102-084616
- **Related target files**: `tests/tools/test_check_conftest_integrity.py`
