## Goal

Cover the server-key rule at the log-directory boundary, including traversal and control-character forms (REQ-005 identifier rule at the path boundary, REQ-009 tests written before the implementation).

## Scope
**Release unit**: N/A: not part of a release unit

## Assumptions

- The 216-line file has no key-validity case today; its `server_key` cases (`:16`, `:169`, `:180`) only cover a missing key in the tracking maps, so the new cases are a new group rather than edits.
- The manager raises `HttpStartupError` for path problems (`scripts/agent/http_lifecycle_stderr_log_manager.py:55-58`), which is the exception the new cases assert.

## Design decisions

- Assert both the rejection and the absence of side effects: each case checks the raised error and that no directory or file was created under `{tmp}/mcp_server_logs/` (AC-4).
- Use the same invalid-key table shape as row 7 so the three enforcement points are covered by one consistent set of forms.

## Alternatives considered

N/A: the case set follows the Plan's Tests section directly.

## Implementation
### Target file
`tests/agent/test_http_lifecycle_stderr_log_manager.py`
### Procedure
Add a key-validity group to the existing suite.

### Method
- Add a parametrized group over `..`, `a/b`, `a.b`, `A`, `a b`, `a\n`, a key containing a NUL or other control character, and a 65-character key, each asserting `open_log` raises `HttpStartupError` (REQ-005).
- Add a case asserting the rejected key never appears as a created path: check the tmp log root and the parent directory for a new entry.
- Add a positive case asserting a valid key produces exactly `{tmp}/mcp_server_logs/{key}/stderr.log`, so the log directory name is the validated key.

### Details
- Use the file's existing tmp-directory fixture style and `monkeypatch` `tempfile.gettempdir` so the assertions do not write to the real tmp directory.
- Keep the existing rotation, tail, and forget cases unchanged.

## Compatibility considerations

Additive group only; no existing case changes.

## Security considerations

N/A: this row only asserts the guarantee row 5 implements.

## Rollback considerations

N/A: revert the commit.

## Validation plan

- `uv run pytest tests/agent/test_http_lifecycle_stderr_log_manager.py`
- Expected outcome before row 5 lands: the new cases fail (Plan Phase 1)

## Completion criteria

- Every invalid key form in AC-4 is rejected by `open_log` with no directory created.
- A valid key's log path is exactly the validated key as one directory component.

## Out of Scope

- Implementing the guard (row 5).
- The config-layer key enforcement and its cases (rows 1 and 7).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Add the test cases described in Implementation > Procedure/Method/Details | Pending | — | — | Plan Phase 1: expected to fail until row 5 lands |
| 2 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |

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
- **Requirement ID**: REQ-005 (server identifier at the path boundary), REQ-009 (tests written before the implementation)
- **Source issue**: issues/20261119-145304_cliplc006_mcp-launch-spec-credentials.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261125-111909_cliplc006_mcp-launch-spec-credentials.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261125-223712
- **Related target files**: `tests/agent/test_http_lifecycle_stderr_log_manager.py`
