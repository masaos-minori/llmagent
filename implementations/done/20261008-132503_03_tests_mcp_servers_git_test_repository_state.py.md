## Goal
Rewrite the two push postcondition tests and add a pipeline-level test for the execution-error path (REQ-002 of the Plan).

## Scope
- Replace two tests in the postcondition test class and add one test next to the pipeline tests.

## Assumptions
- The postcondition check no longer has a push branch (removed upstream, confirmed intended); the pipeline converts any exception raised by the operation into a service error whose message names the tool.

## Design decisions
- Assert the new contract: a push postcondition always passes for any result text; an operation that raises is reported as a service error naming the push tool.

## Alternatives considered
- Keeping the old assertions behind an expected-failure marker: rejected; they describe removed behavior.

## Implementation
### Target file
tests/mcp_servers/git/test_repository_state.py

### Procedure
1. Read the two push postcondition tests and the pipeline tests.
2. Replace the two tests with tests asserting the postcondition passes for rejection-like and error-like result text.
3. Add a pipeline test whose operation raises a generic exception for the push tool and assert a service error is raised with the tool name in its message.
4. Run the module.

### Method
Use the existing working-repository fixture and the pipeline class as the nearby tests do.

### Details
Postcondition tests call the verification with the same inputs as before and assert a passing result with an empty message. The pipeline test builds the pipeline on a snapshot, runs the push tool name with an operation that raises, and expects the service error.

## Compatibility considerations
- Test only; no production change.

## Security considerations
- Fake values only; no secrets.

## Rollback considerations
- Revert the commit.

## Validation plan
- `uv run ruff format` and `ruff check` on the file; `uv run pytest tests/mcp_servers/git/test_repository_state.py -q --timeout=60`.

## Completion criteria
- The two old tests are replaced and the new pipeline test passes (REQ-002).

## Out of scope
- Production pipeline or postcondition code.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Replace the two postcondition tests | Completed | 20261008-134340 | 20261008-134340 |  |
| 2 | Add the execution-error pipeline test | Completed | 20261008-134340 | 20261008-134340 |  |
| 3 | Run the module | Completed | 20261008-134340 | 20261008-134340 |  |

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
- **Related target files**: tests/mcp_servers/git/test_repository_state.py