## Goal
Add 8 routing-outcome test cases to `tests/tools/test_check_canonical_source_conflicts.py`,
one per required routing outcome, per REQ-009.

## Scope
- **In-Scope**: adding 8 new test cases covering all 8 required routing outcomes.
- **Out-of-Scope**: every other change to this file; modifying existing test cases.

## Assumptions
- M-01-05's existing validator interface and test framework are known from
  `plans/20260905-165817_plan.md`; this Plan extends them rather than replacing them.
- The 8 test cases correspond to the 8 routing rules from REQ-001.
- The test file does not exist yet (M-01-05 not implemented), so it must be created from
  scratch following the same pattern as other test files in `tests/tools/`.

## Design decisions
(per `skills/python-design/SKILL.md` Final Output §7, narrow bullet only)
- Create the test file from scratch since M-01-05's test infrastructure does not exist.
- Use pytest fixtures for shared setup (finding inputs, expected routing results).
- Each test case verifies both the routing destination AND the correct field set for
  that destination.

## Alternatives considered
N/A: straightforward addition of test cases; no alternative approach applies.

## Implementation
### Target file
`tests/tools/test_check_canonical_source_conflicts.py`

### Procedure
1. Create the test file with 8 test functions, one per routing outcome:
   - `test_route_design_vs_code_to_known_issue`
   - `test_route_functional_requirement_vs_implementation_to_known_issue`
   - `test_route_specification_vs_acceptance_test_to_blocking_conflict`
   - `test_route_deployed_vs_approved_config_to_configuration_drift`
   - `test_route_undetermined_intent_to_needs_confirmation`
   - `test_route_missing_canonical_source_to_design_governance_gap`
   - `test_route_multiple_normative_sources_to_blocking_canonical_source_conflict`
   - `test_route_stale_non_canonical_wording_only_to_documentation_correction_task`
2. Each test verifies:
   - The routing destination matches the expected category.
   - The 12 required record fields are present where the destination is Canonical Source
     Conflict; the lighter field set for other destinations.
3. Add any necessary fixtures/helpers for shared test setup.

### Method
Create via Write tool using pytest conventions consistent with other test files in
`tests/tools/`.

### Details
- Test naming follows the existing convention in `tests/tools/`: `test_<description>`.
- Each test uses a minimal finding input that triggers exactly one routing rule.
- Assertions verify both the routing destination string and the presence of required
  fields in the output.

## Compatibility considerations
N/A: test file; exercised only by `pytest`.

## Security considerations
N/A.

## Rollback considerations
- Delete the test file to revert.

## Validation plan
- `uv run pytest tests/tools/test_check_canonical_source_conflicts.py -v` passes —
  all 8 routing-outcome cases pass alongside M-01-05's existing cases (AC11).
- Manual diff review confirming changes scoped to canonical-source declarations only (AC9).
- Confirm exactly 8 test functions are present, one per routing outcome.

## Completion criteria
- 8 new test cases, one per required routing outcome (AC11).
- `uv run pytest tests/tools/test_check_canonical_source_conflicts.py -v` passes (AC12).

## Out of scope
- Every other change to this file.
- Modifying existing test cases.
- Updating `tools/check_canonical_source_conflicts.py` (REQ-008, separate procedure).
- Updating the Governance Verification Matrix (REQ-010, separate procedure).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | |
| 2 | Add or update tests per Validation plan | Pending | — | — | |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Pending | — | — | N/A |

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
- **Requirement ID**: `REQ-009` (add 8 routing-outcome test cases)
- **Source issue**: issues/20260903-103030_m0107_integrate-canonical-source-conflicts-with-issue-workflows.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260905-185612_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260905-185612
- **Related target files**: tests/tools/test_check_canonical_source_conflicts.py
