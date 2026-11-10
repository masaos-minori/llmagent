## Goal
Reword the fixture line in `tests/tools/test_check_docs_quality.py` that names `SecurityProfile`, so `rg SecurityProfile tests` is clean (`REQ-007`, AC-07) while the history-marker rule is still tested.

## Scope
**Release unit**: N/A: not part of a release unit

## Assumptions
- Lands in the same change as, or after, the code rows it exercises (Plan rows 01-16 and 75); a test edit alone leaves the suite red until the code row lands.
- The line is a fixture for `history_marker_in_active_doc` (`test_current_state_wording_is_not_reported`, line 475): current-state wording must not be flagged. The class name is incidental; any other current-state sentence tests the same rule.
- This row was added to the Plan by the Step 3a amendment (fallout); the original Plan did not list this file.

## Design decisions
- Pick a current-state sentence without a removed identifier, keeping the same shape (a statement of present behavior with no history marker).

## Alternatives considered
N/A: test-only change

## Implementation
### Target file
`tests/tools/test_check_docs_quality.py`

### Procedure
- In `test_current_state_wording_is_not_reported` replace `"`SecurityProfile` holds only PRODUCTION."` with `"`StartupMode` has three members."` (`StartupMode` has the members none, persistent and subprocess; any real identifier that states a present fact works).

### Method
- One string literal; the second line of the list and the assertion stay.

### Details
- `rg -n SecurityProfile tests` returns nothing after rows 06, 10, 30, 40, 42 and this one.

## Compatibility considerations
N/A: test-only change

## Security considerations
N/A: test-only change

## Rollback considerations
N/A: revert the commit

## Validation plan
- `uv run pytest tests/tools/test_check_docs_quality.py -v`

## Completion criteria
- `SecurityProfile` no longer appears in the file.
- The test still asserts no issues for current-state wording and passes.

## Out of Scope
- Changing the docs-quality rule.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Edit `tests/tools/test_check_docs_quality.py` per Procedure/Method/Details | Done | 20261110-232758 | 20261110-232758 | fixture line 477 replaced with '`StartupMode` has three members.'; no other SecurityProfile fixture remained in the file |
| 2 | Run `uv run pytest tests/tools/test_check_docs_quality.py -v` and fix remaining fixtures in this file only | Done | 20261110-232758 | 20261110-232758 | pytest tests/tools/test_check_docs_quality.py: 67 passed; rg SecurityProfile tests returns nothing |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Done | 20261110-232758 | 20261110-232758 | targeted test pass; full toolchain gate (pytest/coverage/mypy/lint-imports/bandit) re-runs at the batch-end docs-wave gate which includes this change |

### Verification Findings
| Item | Finding | Action taken |
|------|---------|--------------|
| VF-1 | No mismatches: fixture anchor line 477 verified; replacement identifier StartupMode exists with members none/persistent/subprocess | Applied single-literal replacement as specified |

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
- **Requirement ID**: `REQ-007` (`SecurityProfile` removed; AC-07 greps tests/)
- **Source issue**: issues/20261109-112640_adrrev004_non-strict-bypass-removal.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261110-094140_adrrev004_non-strict-bypass-removal.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261110-154603
- **Related target files**: `tests/tools/test_check_docs_quality.py`
