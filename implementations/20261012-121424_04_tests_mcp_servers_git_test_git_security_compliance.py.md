## Goal
- Make `test_audit_redacts_requested_target` patch the module that performs the lookup and assert unconditionally (`REQ-001`).

## Scope
- Only that one test (around line 696).

## Assumptions
- `_audit_log_safe` forwards only keyword arguments to `_audit_log(logger, **kwargs)`, so every audit value is in `call.kwargs`.
- Probe result: the origin patch left `called=False`; patching `mcp_servers.git.git_server._audit_log` gave `called=True`.

## Design decisions
- Retarget to `mcp_servers.git.git_server._audit_log` (the same target already used near line 2388).
- Do not assert that `requested_target` is present: the containment-rejection branch does not pass it (Plan `UNK-01`). Assert instead that no audit value leaks the raw path.

## Alternatives considered
N/A: the Plan Design section already fixed the approach for this row.

## Implementation
### Target file
`tests/mcp_servers/git/test_git_security_compliance.py`

### Procedure
1. Change the patch target to `"mcp_servers.git.git_server._audit_log"`.
2. Replace `if mock_audit.called:` and its body with `mock_audit.assert_called()`.
3. Collect leaked values: `leaked = [v for c in mock_audit.call_args_list for v in c.kwargs.values() if isinstance(v, str) and "allowed-evil" in v and "***" not in v]` and `assert not leaked`.

### Method
- Keep the request, status, and `is_error` assertions as they are; only the audit part changes.

### Details
- Update the docstring only if it claims `requested_target` is always recorded; it does not need to change otherwise.

## Compatibility considerations
N/A: test-only change; no runtime or public interface is affected.

## Security considerations
N/A: no input handling, credentials, or I/O boundary is touched.

## Rollback considerations
N/A: revert the commit.

## Validation plan
- `uv run pytest tests/mcp_servers/git/test_git_security_compliance.py -v`.
- Mutation check: temporarily make `_audit_log_safe` return before calling `_audit_log`; the test must fail; revert the mutation.

## Completion criteria
- The test passes, fails under the mutation, and no `if mock_audit.called:` guard remains in it.

## Out of scope
- Any `scripts/` change, including adding `requested_target` to the containment branch (Plan `UNK-01`).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Retarget the patch and make the audit assertions unconditional | Pending | — | — | |
| 2 | Run the mutation check and revert the mutation | Pending | — | — | |
| 3 | Run the validation sequence (`rules/toolchain.md`) for the touched files | Pending | — | — | |

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
- **Requirement ID**: `REQ-001` (make the git audit-redaction test effective and unconditional)
- **Source issue**: issues/20261012-120426_mock001_fix-ineffective-mock-patch-targets-in-tests.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261012-120856_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261012-121424
- **Related target files**: tests/mcp_servers/git/test_git_security_compliance.py
