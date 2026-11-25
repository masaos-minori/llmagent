## Goal

Reject a server key that does not match the identifier rule before it becomes a log-directory path component (REQ-005 identifier rule at the path boundary).

## Scope
**Release unit**: R1-launch-spec

## Assumptions

- `open_log` is the only place in this module that builds a path from `server_key` (`:46-47`); the rotation and tail paths reuse the stored `_log_paths` entry, so one guard at the entry point covers them.
- The manager already signals path problems by raising `HttpStartupError(StartupFailure(...))` (`:55-58`), so the guard uses the same shape rather than a new exception type.

## Design decisions

- Defensive re-check: the key is validated here even though `McpServerConfig` and `_build_mcp_servers` already enforce it (row 1), because `open_log` is reachable with a directly constructed config (REQ-005, AC-4).
- The guard calls `validate_server_key` from `shared.mcp_config` (row 1) rather than re-declaring the pattern, so the three enforcement points cannot drift.

## Alternatives considered

Sanitizing the key (replacing unsafe characters) was rejected: REQ-005 requires rejection, and a rewritten directory name would silently merge two distinct servers.

## Implementation
### Target file
`scripts/agent/http_lifecycle_stderr_log_manager.py`
### Procedure
Validate `server_key` at the top of `open_log`, before any directory is created.

### Method
- Import `validate_server_key` from `shared.mcp_config`.
- At the start of `open_log` (`:32-46`), call it and raise `HttpStartupError(StartupFailure(server_key=..., reason=..., stderr_full=""))` when it raises, so no `os.makedirs` (`:50`) runs for an invalid key.
- Keep `log_dir` (`:46`) as the validated key only, with no additional transformation.

### Details
- The reason text names the server key and states that it is not a valid server identifier; it never contains a path built from the rejected value.
- `forget` and the tail-reading helpers need no change: they look up already-validated keys.

## Compatibility considerations

`open_log(server_key, cfg)` keeps its signature. Callers (`scripts/agent/http_lifecycle_subprocess_launcher.py:70`) are unaffected; only a key that was already invalid now fails earlier.

## Security considerations

This is the path-traversal control: `..`, `/`, `\`, control characters, or a 65-character key can no longer create a directory outside `{tmp}/mcp_server_logs/` (AC-4).

## Rollback considerations

N/A: revert the commit.

## Validation plan

- `uv run pytest tests/agent/test_http_lifecycle_stderr_log_manager.py`
- `uv run mypy scripts/agent/http_lifecycle_stderr_log_manager.py`
- `uv run ruff format` and `uv run ruff check`

## Completion criteria

- Every key form listed in AC-4 is rejected by `open_log` and no directory is created for it.
- Valid keys behave exactly as before, including rotation.

## Out of Scope

- Defining `validate_server_key` (row 1).
- The config-layer enforcement (row 1) and its tests (row 7).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | — | 20261126 | Execute after the row 12 Phase 1 tests are in place (REQ-009) Implemented as specified, with the Step 3a verification findings applied. |
| 2 | Confirm the Phase 1 test additions from row 12 fail before this change and pass after it | Completed | — | 20261126 | Tests-first order per Plan Phase 1 Targeted tests plus ruff/mypy/module-size/mock-patch/suppression gates pass. |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | — | 20261126 | Batch-end validation (release unit R1-launch-spec): ruff format+check, mypy 473 files, bandit 0 issues, lint-imports 6 contracts kept, check_module_size, check_mock_patch_targets, check_suppression_justification, check_docstrings. Full suite: 15116 passed, 16 failed (identical to the HEAD baseline: tests/integration/test_call_state_* pre-existing ToolCallState.args_hash failures). diff-cover 100% on changed source lines. |

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
- **Requirement ID**: REQ-005 (server identifier must not become a path component)
- **Source issue**: issues/20261119-145304_cliplc006_mcp-launch-spec-credentials.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261125-111909_cliplc006_mcp-launch-spec-credentials.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261125-223712
- **Related target files**: `scripts/agent/http_lifecycle_stderr_log_manager.py`