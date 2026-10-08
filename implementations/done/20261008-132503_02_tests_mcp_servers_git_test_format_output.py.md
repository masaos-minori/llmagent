## Goal
Replace the push rejection-marker test with tests of the post-change contract of the push formatter (REQ-002 of the Plan).

## Scope
- Rewrite one test in the formatter test module; add one companion test.

## Assumptions
- The owner confirmed the removal of the output-marker check was intended: a failing push is reported through the error path, and output text alone does not fail the call.
- The formatter does not wrap exceptions; the pipeline does.

## Design decisions
- Test that a command error raised by the push call propagates unchanged out of the formatter, and that a clean push output is returned as is.

## Alternatives considered
- Deleting the test: rejected; keep coverage of the push path.

## Implementation
### Target file
tests/mcp_servers/git/test_format_output.py

### Procedure
1. Read the rejection-marker test and the neighboring push tests.
2. Replace it with a test asserting that a command error from the mocked push propagates, and a companion test asserting that output containing a rejection-like text is returned as normal output (documenting the intended removal).
3. Run the module.

### Method
Reuse the module's helpers for a mocked repository, state, request, and authorized configuration.

### Details
Mock the repository's push call with a side effect of the repository library's command error; assert it propagates with pytest.raises. For the companion test, set the push return value to a rejection-like string and assert the formatter returns it.

## Compatibility considerations
- Test only; no production change.

## Security considerations
- Fake values only; no secrets.

## Rollback considerations
- Revert the commit.

## Validation plan
- `uv run ruff format` and `ruff check` on the file; `uv run pytest tests/mcp_servers/git/test_format_output.py -q --timeout=60`.

## Completion criteria
- The old marker expectation is gone; the two new tests pass (REQ-002).

## Out of scope
- Production formatter code.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Rewrite the marker test and add the companion test | Completed | 20261008-134340 | 20261008-134340 |  |
| 2 | Run the module | Completed | 20261008-134340 | 20261008-134340 |  |

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
- **Requirement ID**: REQ-002 (rewrite to the new contract)
- **Source issue**: issues/20261008-125417_gitmcptest01_fix-failing-git-mcp-tests-after-the-audit-record-emission-change.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261008-131516_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261008-132503
- **Related target files**: tests/mcp_servers/git/test_format_output.py