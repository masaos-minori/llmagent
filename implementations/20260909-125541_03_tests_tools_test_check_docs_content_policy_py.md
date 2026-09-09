# Implementation Procedure: Add unit test for auto-generated block exemption

## Goal

Add a unit test confirming that `check_literal_port_number()` exempts content between `<!-- AUTO-GENERATED -->` / `<!-- END AUTO-GENERATED -->` guard comments while still flagging hand-written port mentions elsewhere.

## Scope

- **In-Scope**: Add one unit test to `tests/tools/test_check_docs_content_policy.py`
- **Out-of-Scope**: Modifying existing tests; adding tests for other functions

## Assumptions

- The exemption logic in `check_docs_content_policy.py` has already been implemented (see related target file)
- The test uses mock DocFile objects with content containing both auto-generated and hand-written port numbers

## Design decisions

- Single test covering both exemption (auto-generated block) and non-exemption (hand-written mention) in one assertion
- Use inline string content rather than reading actual files to avoid filesystem dependencies

## Alternatives considered

- Two separate tests (one for exemption, one for non-exemption) — rejected because they share the same input structure and can be verified together
- Reading actual `docs/*.md` files — rejected because it introduces filesystem coupling and requires knowing which files have auto-generated sections

## Implementation

### Target file

`tests/tools/test_check_docs_content_policy.py`

### Procedure

Add a unit test for the auto-generated block exemption.

### Method

Append a new test function to `tests/tools/test_check_docs_content_policy.py`.

### Details

1. Read `tests/tools/test_check_docs_content_policy.py` to find the existing test patterns for `check_literal_port_number()`.
2. Create a new test function named something like `test_check_literal_port_number_auto_generated_exemption()`.
3. Construct mock DocFile objects with:
   - Content containing `<!-- AUTO-GENERATED -->` / `<!-- END AUTO-GENERATED -->` with port numbers inside
   - Content containing hand-written port numbers outside those guard comments
4. Call `check_literal_port_number([doc])` and assert:
   - No findings are returned for port numbers within the auto-generated block
   - Findings ARE returned for port numbers outside the auto-generated block

## Compatibility considerations

- Test must use the same mock infrastructure as existing tests in this file
- Should not break existing test assertions

## Security considerations

N/A: Test-only change

## Rollback considerations

- Remove the added test if it fails due to incorrect exemption logic assumptions

## Validation plan

Run `uv run pytest tests/tools/test_check_docs_content_policy.py` and confirm the new test passes alongside existing tests.

## Completion criteria

- New test exists in `tests/tools/test_check_docs_content_policy.py`
- Test asserts auto-generated block exemption works correctly
- Test asserts hand-written port mentions are still flagged
- All tests pass after adding the new test

## Out of scope

- Modifying existing tests
- Tests for other functions in `check_docs_content_policy.py`
- Integration/corpus-level validation (covered by corpus run)

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Locate existing test patterns | Pending | — | — | |
| 2 | Write test for auto-generated exemption | Pending | — | — | |
| 3 | Run tests to verify | Pending | — | — | |

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
- **Requirement ID**: REQ-002
- **Source issue**: issues/20260905-153715_dcp001_port_number_exemption_policy_decision.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260908-210115_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260909-125541
- **Related target files**: tests/tools/test_check_docs_content_policy.py
