## Goal
- Add tests for valid, malformed, and absent release-unit declarations (`REQ-004`).

## Scope
- In scope: new test functions appended to the module. Out of scope: changes to existing tests and helpers.

## Assumptions
- Step 3a: the module already has `_write`, `_install_templates`, and monkeypatches `tools.check_workitem_structure.ROOT_DIR` to a `tmp_path` tree for path-handling tests; `test_end_to_end_missing_section_with_real_templates` shows the pattern.
- No overlap (Step 2): no other Frozen Plan targets this file.
- Depends on row 06: the tests call `find_release_unit_findings` (new, defined by row 06) and the `collect_*` functions, and use category `release-unit`.

## Design decisions
- Test through `collect_single_file_findings` on a Plan written under `tmp_path/plans/` for end-to-end cases, and call `find_release_unit_findings` directly for the parsing edge cases; filter findings by category so heading findings do not mask the result.
- Build the valid Plan from a minimal body containing `## Implementation steps` with numbered phases plus the block, rather than the full template.

## Alternatives considered
N/A: follows the module's existing style.

## Implementation
### Target file
`tests/tools/test_check_workitem_structure.py`

### Procedure
- Append tests, each using `monkeypatch.setattr(cwis, "ROOT_DIR", tmp_path)` and `_install_templates(tmp_path)`:
  - valid single-unit and two-unit declarations: no `release-unit` finding;
  - default `N/A: no release unit` text: none;
  - no block at all (a Plan without a unit): none, and the existing heading result is unchanged;
  - malformed: missing name, missing `Phases`, missing `Reason`, non-numeric phase, phase number not in `Implementation steps`, block outside `Implementation steps`: one `release-unit` finding each;
  - the real `templates/plan.md` skeleton used as a Plan body: the default block yields no `release-unit` finding.

### Method
- Parametrize the malformed cases with the bad line text and the expected detail fragment.
- Assert on `category` and a stable detail fragment, not the whole string.

### Details
- Type-annotate every test as the module does (`-> None`, `tmp_path: Path`, `monkeypatch: pytest.MonkeyPatch`).

## Compatibility considerations
N/A: additive tests.

## Security considerations
N/A: tests write only under `tmp_path`.

## Rollback considerations
N/A: revert the commit.

## Validation plan
- `uv run pytest tests/tools/test_check_workitem_structure.py -v` collects the new tests and all pass.
- Tool lint sequence on the test file per `rules/toolchain.md` (`ruff format`, `ruff check`, `mypy`).

## Completion criteria
- Valid, each malformed variant, and absent declarations are covered and pass (AC-3).

## Out of Scope
- Tests for `manage_workitem_stage.py` (row 09).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the declaration tests in the existing module | Pending | — | — |  |
| 2 | Run `tests/tools/test_check_workitem_structure.py` and confirm new tests are collected | Pending | — | — | A 0-collected run is not a pass |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | `ruff`, `mypy` on the test file |

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
- **Source issue**: issues/20261030-191057_flowimp002_plan-release-units.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261102-080336_flowimp002_plan-release-units.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261102-085047
- **Related target files**: tests/tools/test_check_workitem_structure.py
