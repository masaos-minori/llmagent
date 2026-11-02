## Goal
- Add tests for grouped `list`, unit-printing `show`, and the no-unit case (`REQ-005`).

## Scope
- In scope: new tests and a small local fixture helper appended to this module, plus importing `cmd_list` and `cmd_show`. Out of scope: `tests/tools/test_manage_workitem_stage_new.py`, which holds the existing `list` and `show` tests and is only run as regression.

## Assumptions
- Step 3a correction: the existing `list` and `show` tests are in `tests/tools/test_manage_workitem_stage_new.py` (`TestList`, the `show` tests), not in this module; the Plan was corrected (its Assumption A9). This module has none, so the new tests are self-contained.
- Overlap (Step 2): this file is also targeted by the Plan filed from `flowimp003` (tests for its order view). Judged a sequencing dependency (plan Assumption A7): both append tests; whichever lands second rebases. Different test names avoid collision.
- Depends on row 08: tests call `cmd_list`, `cmd_show`, and read `_release_unit_name` (new) behavior only through them.

## Design decisions
- Each test chdirs to `tmp_path` (as `TestList` does) because `_get_workitem_files` uses relative `implementations/` and `plans/`, and writes procedures with a `## Scope` containing the `**Release unit**` line, a `**Source plan**` Traceability line, and an Execution Status table.
- Use `capsys` for output assertions; assert group heading and indentation order, not full-output equality, except for the no-unit case.

## Alternatives considered
- Adding the tests to `_new.py` next to the old ones was rejected: it is not a frozen target (plan Assumption A9).

## Implementation
### Target file
`tests/tools/test_manage_workitem_stage.py`

### Procedure
- Import `cmd_list` and `cmd_show` from `tools.manage_workitem_stage` in the existing import block.
- Add a local helper writing a procedure file with a given status, unit line, and source plan.
- Add tests: two members of one unit grouped under one `Unit:` heading; the same unit name under two Plans yields two groups; a procedure with the default `N/A: not part of a release unit` line prints as an ungrouped line; a list with no units prints exactly the pre-change format; `show` prints `Release unit: {name}` for a member and no extra line for a non-member.

### Method
- Use `monkeypatch.chdir(tmp_path)` and `build_parser().parse_args([...])` like the existing tests; annotate all tests (`-> None`).
- Keep fixtures to the minimum table (`| 1 | Do the thing | Pending | — | — | |`).

### Details
- For the no-unit case compare against the exact lines the current `cmd_list` prints (`Status: ...`, `  [implementation-procedure] path`).

## Compatibility considerations
N/A: additive tests; existing tests are not edited.

## Security considerations
N/A: tests write only under `tmp_path`.

## Rollback considerations
N/A: revert the commit.

## Validation plan
- `uv run pytest tests/tools/test_manage_workitem_stage.py tests/tools/test_manage_workitem_stage_new.py -v` collects the new tests and all pass.
- `uv run ruff format`, `uv run ruff check`, and `uv run mypy` on the test file.

## Completion criteria
- Grouped `list`, unit-printing `show`, and the no-unit regression are covered and pass (AC-4).

## Out of Scope
- The `list`/`show` implementation (row 08).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Write the grouped-display tests | Completed | 20261102-125457 | 20261102-125457 | Stale clean. Changed: tests/tools/test_manage_workitem_stage.py (4 new tests, helper, cmd_list/cmd_show imports) |
| 2 | Run both `manage_workitem_stage` test modules and confirm the new tests are collected | Completed | 20261102-125457 | 20261102-125457 | A 0-collected run is not a pass both modules: 99 passed (4 new collected); ruff/mypy clean; full suite deferred to plan end |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20261102-130434 | 20261102-130434 | `ruff`, `mypy` on the test file ruff/mypy clean on test file; PLAN-END full suite (coverage run): 11069 passed, 13 skipped, 1 failed = known pre-existing mdq_health_posture; diff-cover: no lines with coverage information (changes only in tools/, docs, tests) |

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
- **Requirement ID**: `REQ-005`
- **Source issue**: issues/20261030-191057_flowimp002_plan-release-units.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261102-080336_flowimp002_plan-release-units.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261102-085047
- **Related target files**: tests/tools/test_manage_workitem_stage.py