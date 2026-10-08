# Implementation Procedure: Add real-audit integration tests + update mocked-audit test

## Goal

Add tests that exercise the REAL `_audit_log()` (no mocking) asserting exactly one record per outcome: success, path rejection, remote rejection, protected-branch rejection, postcondition failure. Update the existing mocked-audit test at `test_git_security_compliance.py` line 673 to the new signature (REQ-009).

## Scope

- Modify `tests/mcp_servers/git/test_git_security_compliance.py`:
  - Add real-audit integration tests for every outcome (success, path rejection, remote rejection, protected-branch rejection, postcondition failure).
  - Add remote-rejection HTTP test (HTTP 200 with `is_error=True`).
  - Add health-counter test (force `_audit_log` to raise; assert counter appears in `/health` details).
  - Update the mocked-audit test at line 673 to the new `_audit_log` signature (with `requested_target`/`canonical_target`).
- Modify `tests/mcp_servers/git/test_git_service_dispatch.py`:
  - Add additive-schema test for new audit fields.
  - Add postcondition-message test.
  - Add config-injection test.

## Assumptions

- A temporary bare remote can be created for testing push rejection scenarios (or a test double raising `GitServiceError` from the op).
- The real `_audit_log()` writes JSON-lines to the logger — tests can capture this via `caplog` or by patching the logger's handler.
- The `/health` endpoint returns a `JSONResponse` — tests can assert the body contains the counter key.

## Design decisions

- **Real-audit tests**: Use `caplog` to capture the logger output and assert the exact record shape and outcome value.
- **HTTP test**: Use `TestClient` to make an HTTP request and assert the response status code and body.
- **Health-counter test**: Force `_audit_log` to raise in `_audit_log_safe()` and assert the counter appears in `/health` details.
- **Mocked-audit update**: Change the mock target from `mcp_servers.git.git_server._audit_log` to `mcp_servers.audit._audit_log` (the actual function being called).

## Alternatives considered

- Using a custom logging handler to capture records: rejected because `caplog` is simpler and sufficient for this purpose.
- Creating a separate test file for real-audit tests: rejected because the plan groups all audit tests together.

## Implementation
### Target file
`tests/mcp_servers/git/test_git_security_compliance.py`, `tests/mcp_servers/git/test_git_service_dispatch.py`

### Procedure
1. Add real-audit integration tests for every outcome (REQ-009).
2. Add remote-rejection HTTP test (REQ-009).
3. Add health-counter test (REQ-009).
4. Update mocked-audit test at line 673 to new signature (REQ-009).
5. Add additive-schema test (REQ-001).
6. Add postcondition-message test (REQ-006).
7. Add config-injection test (REQ-007).

### Method
Edit `tests/mcp_servers/git/test_git_security_compliance.py`:
- Add real-audit integration tests using `caplog` to capture logger output.
- Add remote-rejection HTTP test using `TestClient`.
- Add health-counter test forcing `_audit_log` to raise.
- Update mock target at line 673 from `mcp_servers.git.git_server._audit_log` to `mcp_servers.audit._audit_log`.

Edit `tests/mcp_servers/git/test_git_service_dispatch.py`:
- Add additive-schema test calling `_build_audit_record()` directly.
- Add postcondition-message test triggering checkout postcondition failure.
- Add config-injection test passing mock `GitConfig`.

### Details
- Real-audit tests use `caplog` to capture logger output and assert record shape.
- HTTP test uses `TestClient` to assert response status code and body.
- Health-counter test forces `_audit_log` to raise and asserts counter in `/health` details.
- Mocked-audit update must use the new `_audit_log` signature (with `requested_target`/`canonical_target` params).

## Compatibility considerations

- The updated mocked-audit test must use the new `_audit_log` signature (with `requested_target`/`canonical_target` params).
- Real-audit tests require a live git repository — use `tempfile.TemporaryDirectory` for isolation.

## Security considerations

- No security impact: these are integration tests, not production code changes.

## Rollback considerations

- Revert the test additions — acceptable because they are additive and do not affect production behavior.

## Validation plan

- **Run tests**: `uv run pytest tests/mcp_servers/git/test_git_security_compliance.py tests/mcp_servers/git/test_git_service_dispatch.py` — confirm all pass.
- **Mutation testing**: Confirm the new tests would catch a regression (e.g., removing the `GitPolicyError` raise would cause the remote-rejection test to fail).

## Completion criteria

- Real-audit integration tests exist for every outcome (success, path rejection, remote rejection, protected-branch rejection, postcondition failure).
- Remote-rejection HTTP test asserts HTTP 200 with `is_error=True`.
- Health-counter test asserts the counter appears in `/health` details.
- Mocked-audit test at line 673 uses the new `_audit_log` signature.
- Additive-schema test confirms `AuditRecord` accepts `requested_target`/`canonical_target`.
- Postcondition-message test confirms the resulting state is included in the error message.
- Config-injection test confirms `format_pull()`/`format_push()` use the passed `_cfg`.

## Out of scope

- Modifying `audit.py` (adds `requested_target`/`canonical_target` — covered in its own document).
- Modifying `git_server.py` (outcome unification, try/except/finally, health counter — covered in its own document).
- Modifying `errors.py` (adds `GitPolicyError` — covered in its own document).
- Modifying `format_output.py` (raises `GitPolicyError`, enriches message, drops `GitConfig.load()` — covered in its own document).
- Modifying `git_service.py` (passes `_cfg` — covered in its own document).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Add real-audit integration tests for every outcome (`tests/mcp_servers/git/test_git_security_compliance.py`) | Done | — | — | REQ-009 |
| 2 | Add remote-rejection HTTP test (`tests/mcp_servers/git/test_git_security_compliance.py`) | Done | — | — | REQ-009 |
| 3 | Add health-counter test (`tests/mcp_servers/git/test_git_security_compliance.py`) | Done | — | — | REQ-009 |
| 4 | Update mocked-audit test at line 673 to new signature (`tests/mcp_servers/git/test_git_security_compliance.py`) | Done | — | — | REQ-009 |
| 5 | Add additive-schema test (`tests/mcp_servers/git/test_git_service_dispatch.py`) | Done | — | — | REQ-001 |
| 6 | Add postcondition-message test (`tests/mcp_servers/git/test_git_service_dispatch.py`) | Done | — | — | REQ-006 |
| 7 | Add config-injection test (`tests/mcp_servers/git/test_git_service_dispatch.py`) | Done | — | — | REQ-007 |
| 8 | Run validation sequence (ruff, mypy, pytest) | Done | — | — | REQ-009 |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| — | — | — | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| — | — | — | — | — | — |

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Done | — | — | |
| 2 | Add or update tests per Validation plan | Done | — | — | |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Done | — | — | |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Done | — | — | |

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
- **Requirement ID**: REQ-009
- **Source issue**: issues/20261007-153904_gitaudit01_fix-git-mcp-audit-records-and-policy-rejection-error-path.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261007-191952_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261008-110318
- **Related target files**: tests/mcp_servers/git/test_git_security_compliance.py, tests/mcp_servers/git/test_git_service_dispatch.py
