## Goal
Find and remove the shared state that makes two compliance tests pass alone but fail inside the full run (REQ-003 of the Plan).

## Scope
- Fixtures or setup of the two failing tests and of the tests that precede them; no assertion is weakened.

## Assumptions
- Both tests pass when run alone; the dry-run test also passed in one subset run and failed in the full run, so the dependence is on which tests ran earlier.

## Design decisions
- Reproduce first, bisect by running the module with preceding modules, then fix the leaking scope (module-scope fixture, global registry, or monkeypatch outside a fixture).

## Alternatives considered
- Marking the tests as serial or retrying: rejected; it hides the leak.

## Implementation
### Target file
tests/mcp_servers/git/test_git_security_compliance.py

### Procedure
1. Run each failing test alone, then the module, then the git test directory, then the full suite, recording which pass.
2. Bisect the preceding tests to find the one whose state leaks (inspect the module's autouse fixture, module-scope fixtures, and any module-level patches).
3. Fix the scope or cleanup of that state, and record the cause for the commit message.
4. Re-run in the same orders.

### Method
Use pytest's ordering and selection options to bisect without editing tests; change fixtures to function scope or add teardown, preferring monkeypatch fixtures over manual patching.

### Details
If the leak is in production code (for example a module-level cache), stop and report it as an additional target file instead of patching around it in the test.

## Compatibility considerations
- Test only; no production change.

## Security considerations
- Fake values only; no secrets.

## Rollback considerations
- Revert the commit.

## Validation plan
- `uv run pytest tests/mcp_servers/git/test_git_security_compliance.py -q --timeout=60`, `uv run pytest tests/mcp_servers/git -q`, and the full suite once; repeat the two tests inside the full run.

## Completion criteria
- Both tests pass alone and in the full run, and the leaking state is identified and fixed (REQ-003).

## Out of scope
- Production code and other test modules.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Reproduce and bisect the order dependence | Completed | 20261008-134340 | 20261008-134340 |  |
| 2 | Fix the leaking state | Completed | 20261008-134340 | 20261008-134340 |  |
| 3 | Re-run alone, per module, and in the full suite | Completed | 20261008-134340 | 20261008-134340 |  |

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
- **Requirement ID**: REQ-003 (order dependence)
- **Source issue**: issues/20261008-125417_gitmcptest01_fix-failing-git-mcp-tests-after-the-audit-record-emission-change.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261008-131516_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261008-132503
- **Related target files**: tests/mcp_servers/git/test_git_security_compliance.py