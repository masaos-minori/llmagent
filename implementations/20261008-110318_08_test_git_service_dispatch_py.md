# Implementation Procedure: Additive-schema, postcondition-message, config-injection tests

## Goal

Add three tests to `tests/mcp_servers/git/test_git_service_dispatch.py`:
1. Additive-schema test: `AuditRecord` / `_build_audit_record()` accept `requested_target`/`canonical_target`; eventbus consumers still type-check (REQ-001).
2. Postcondition-message test: checkout postcondition failure message contains the resulting state (REQ-006).
3. Config-injection test: `format_pull()` / `format_push()` use the passed `_cfg` and ignore a divergent config (REQ-007).

## Scope

- Modify `tests/mcp_servers/git/test_git_service_dispatch.py`:
  - Add additive-schema test for new audit fields.
  - Add postcondition-message test.
  - Add config-injection test.

## Assumptions

- `test_git_service_dispatch.py` already has fixtures for creating temporary repos and GitService instances.
- The additive-schema test can use a controlled `GitServiceError` to trigger the audit path.
- The config-injection test can pass a mock `GitConfig` and verify it is used instead of `GitConfig.load()`.

## Design decisions

- **Additive-schema test**: Call `_build_audit_record()` directly with `requested_target`/`canonical_target` and assert the returned dict contains both fields.
- **Postcondition-message test**: Trigger a checkout postcondition failure and assert the error message includes "state already changed" and the resulting branch name.
- **Config-injection test**: Pass a mock `GitConfig` to `format_pull()`/`format_push()` and verify it is used (not `GitConfig.load()`).

## Alternatives considered

- Using a single test class for all three tests: rejected because each test has different setup requirements and should be independently runnable.
- Testing via the HTTP dispatch path: rejected because the plan requires dispatch-level tests that don't depend on the full server stack.

## Implementation
### Target file
`tests/mcp_servers/git/test_git_service_dispatch.py`

### Procedure
1. Add additive-schema test confirming `AuditRecord` accepts `requested_target`/`canonical_target` (REQ-001).
2. Add postcondition-message test confirming resulting state in error message (REQ-006).
3. Add config-injection test confirming `format_pull()`/`format_push()` use passed `_cfg` (REQ-007).

### Method
Edit `tests/mcp_servers/git/test_git_service_dispatch.py`:
- Add additive-schema test: Call `_build_audit_record()` directly with `requested_target`/`canonical_target` and assert returned dict contains both fields.
- Add postcondition-message test: Trigger checkout postcondition failure and assert error message includes "state already changed" and resulting branch name.
- Add config-injection test: Pass mock `GitConfig` to `format_pull()`/`format_push()` and verify it is used (not `GitConfig.load()`).

### Details
- Each test has different setup requirements and should be independently runnable.
- The additive-schema test must confirm eventbus consumers still type-check against the modified `AuditRecord`.
- The config-injection test must verify a divergent config file does not affect the operation.

## Compatibility considerations

- The additive-schema test must confirm that eventbus consumers (`scripts/eventbus/audit.py`, `scripts/eventbus/auth.py`) still type-check against the modified `AuditRecord`.
- The config-injection test must verify that a divergent config file does not affect the operation.

## Security considerations

- No security impact: these are integration tests, not production code changes.

## Rollback considerations

- Revert the test additions — acceptable because they are additive and do not affect production behavior.

## Validation plan

- **Run tests**: `uv run pytest tests/mcp_servers/git/test_git_service_dispatch.py` — confirm all pass.
- **Static check**: `rg 'GitConfig\.load' scripts/mcp_servers/git/format_output.py` should return 0 after the change (covers REQ-007).

## Completion criteria

- Additive-schema test confirms `AuditRecord` accepts `requested_target`/`canonical_target`.
- Postcondition-message test confirms the resulting state is included in the error message.
- Config-injection test confirms `format_pull()`/`format_push()` use the passed `_cfg`.
- All three tests are independently runnable.

## Out of scope

- Modifying `audit.py` (adds `requested_target`/`canonical_target` — covered in its own document).
- Modifying `git_server.py` (outcome unification, try/except/finally, health counter — covered in its own document).
- Modifying `errors.py` (adds `GitPolicyError` — covered in its own document).
- Modifying `format_output.py` (raises `GitPolicyError`, enriches message, drops `GitConfig.load()` — covered in its own document).
- Modifying `git_service.py` (passes `_cfg` — covered in its own document).
- Modifying `repository_state.py` (removes git_push stdout check — covered in its own document).
- Modifying `test_git_security_compliance.py` (real-audit tests — covered in its own document).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Add additive-schema test (`tests/mcp_servers/git/test_git_service_dispatch.py`) | Pending | — | — | REQ-001 |
| 2 | Add postcondition-message test (`tests/mcp_servers/git/test_git_service_dispatch.py`) | Pending | — | — | REQ-006 |
| 3 | Add config-injection test (`tests/mcp_servers/git/test_git_service_dispatch.py`) | Pending | — | — | REQ-007 |
| 4 | Run validation sequence (ruff, mypy, pytest) | Pending | — | — | REQ-001, REQ-006, REQ-007 |

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
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | |
| 2 | Add or update tests per Validation plan | Pending | — | — | |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Pending | — | — | |

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
- **Requirement ID**: REQ-001, REQ-006, REQ-007
- **Source issue**: issues/20261007-153904_gitaudit01_fix-git-mcp-audit-records-and-policy-rejection-error-path.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261007-191952_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261008-110318
- **Related target files**: tests/mcp_servers/git/test_git_service_dispatch.py
