## Goal

Extend `tests/agent/test_http_lifecycle_command_validator.py` with the accept/reject matrix for the new allowed-binary-directory rule (AC-06), while keeping the existing allowlist test cases passing unchanged. Implements `REQ-004` / AC-06.

## Scope

Modifies `tests/agent/test_http_lifecycle_command_validator.py`: add cases for the binary-directory acceptance and reject matrix, and preserve the existing allowlist cases.

## Assumptions

- `CommandValidator.validate(server_key, cmd_name)` now accepts a command whose resolved real path is a regular file directly inside an allowed, non group/world-writable binary directory (default `/opt/llm/bin`), in addition to the existing basename allowlist (see the validator row).
- The reject matrix (AC-06): reject a symlink in that directory pointing elsewhere, a file in a writable directory, a non-regular file, and any basename outside the allowlist and outside the directory.

## Design decisions

- Build the matrix using temporary directories (`tmp_path`) so the allowed binary directory, a writable variant, and symlink targets are isolated per test.
- Keep the existing allowlist cases untouched so they continue to pass unchanged.

## Alternatives considered

- Hard-coding `/opt/llm/bin` in the tests: rejected — tests must not depend on the production layout; use temporary directories and the overridable `LLMAGENT_BINARY_DIR` env var.

## Implementation

### Target file

`tests/agent/test_http_lifecycle_command_validator.py`

### Procedure

Add the binary-directory accept/reject cases; preserve the existing allowlist cases.

### Method

1. Accept case: create a temp dir, place a regular file in it, set `LLMAGENT_BINARY_DIR` to it (non-writable), and assert `validate(...)` accepts the resolved path.
2. Reject — symlink: create a symlink inside the allowed directory pointing to a target outside it; assert rejection.
3. Reject — writable directory: make the allowed directory group/world-writable; assert rejection.
4. Reject — non-regular file: place a directory (or special file) in the allowed directory; assert rejection.
5. Reject — outside both controls: use a basename outside the allowlist located outside the allowed directory; assert rejection.
6. Confirm the existing allowlist cases still pass unchanged.

### Details

- Use `monkeypatch` to set/clear `LLMAGENT_BINARY_DIR` and to control directory permissions (`chmod`) between cases.
- For the symlink case, resolve the symlink and confirm the validator rejects the planted link.

## Compatibility considerations

- Existing allowlist cases are preserved; only additive cases are added.

## Security considerations

- These tests lock in the security control: they assert the reject matrix from AC-06, including the symlink and writable-directory rejections, so a future relaxation of the rule is caught by the suite.

## Rollback considerations

- N/A: revert the commit.

## Validation plan

- `uv run pytest tests/agent/test_http_lifecycle_command_validator.py` — the accept case passes; all four reject cases fail as expected; the existing allowlist cases pass unchanged.
- `uv run ruff format`, `uv run ruff check`, `uv run mypy` clean.

## Completion criteria

- `test_http_lifecycle_command_validator.py` covers the AC-06 accept/reject matrix; the existing allowlist cases are unmodified and passing.

## Out of scope

- The validator implementation (`scripts/agent/http_lifecycle_command_validator.py`) is its own row.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Add the binary-directory accept case | Pending | — | — | security-critical |
| 2 | Add the four AC-06 reject cases | Pending | — | — | security-critical |
| 3 | Confirm existing allowlist cases still pass | Pending | — | — | |
| 4 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |

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
- **Requirement ID**: REQ-004
- **Source issue**: issues/done/20260717-171259_nuitka_onefile_packaging_proposal.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261006-104451_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261012-183345
- **Related target files**: tests/agent/test_http_lifecycle_command_validator.py
