## Goal

Cover strict-by-default confinement, the explicit permissive opt-in, ownership and file-mode checks, identity capture across a PATH or symlink change, and the narrowed environment filter (REQ-003 validated path, REQ-004 confinement, REQ-009 tests written before the implementation).

## Scope
**Release unit**: N/A: not part of a release unit

## Assumptions

- The file holds 36 cases today; the strict-mode group (`:431-540`) sets `LLMAGENT_STRICT_COMMAND` and the filter group (`:249-339`) calls `CommandValidator().filter_env({})`, so both groups are retargeted rather than duplicated.
- The trusted-directory fixtures already use `LLMAGENT_BINARY_DIR` pointed at a tmp directory, which is what the new ownership and mode cases extend.

## Design decisions

- Default-strict is asserted by deleting the environment variable, not by setting a new one: `monkeypatch.delenv("LLMAGENT_COMMAND_MODE", raising=False)` plus a rejected binary is the production posture (REQ-004).
- Ownership is asserted with a mocked `os.stat` uid rather than by `chown`, so the suite runs unprivileged (Plan Tests).
- The PATH and symlink change cases assert on the value `validate` returns plus the captured identity, not on a spawn, which keeps the row-3 contract testable without row-4's launcher.

## Alternatives considered

N/A: the case set follows the Plan's Tests section; no alternative fixture was considered.

## Implementation
### Target file
`tests/agent/test_http_lifecycle_command_validator.py`
### Procedure
Retarget the strict-mode group to the new default, add the opt-in permissive group, add ownership and mode cases, add the identity cases, and replace the `filter_env` group.

### Method
- Rewrite the `:431-540` group so the strict expectations hold with no environment variable set, and add a group that sets `LLMAGENT_COMMAND_MODE=permissive` and asserts the basename allowlist behavior is restored, including a falsy-value case that does not opt in.
- Add ownership cases: executable owned by another uid, trusted directory owned by another uid, both accepted when owned by `os.geteuid()` or root (mocked `os.stat`).
- Add mode cases: group-writable executable, world-writable executable, group-writable directory.
- Add the symlink case: a symlink inside the trusted directory pointing outside it is rejected.
- Add the change-after-validation cases: retarget the symlink and change `PATH` between `validate` and the reported path, asserting the returned path is unchanged, and swap the file to assert the captured `(st_dev, st_ino)` pair no longer matches.
- Replace the `:249-339` group: assert the narrowed allowlist admits the REQ-006 runtime set and rejects MCP_OTHER_AUTH_TOKEN, MCP_OTHER_CONTROL_TOKEN, and `GITHUB_TOKEN`, and delete the cases that call `filter_env` or assert `filter_env(None) is None` (`:339`).

### Details
- Keep the existing basename-allowlist cases that describe permissive behavior, moved under the opt-in group so the mode boundary is explicit.
- Assert every rejection raises `HttpStartupError` with a reason naming the server key and the resolved path.

## Compatibility considerations

Removing the `filter_env` cases is required by row 3 deleting the method; the integration gate that also calls it is row 11.

## Security considerations

N/A: this row only asserts the guarantees row 3 implements.

## Rollback considerations

N/A: revert the commit.

## Validation plan

- `uv run pytest tests/agent/test_http_lifecycle_command_validator.py`
- Expected outcome before row 3 lands: the new and retargeted cases fail (Plan Phase 1)

## Completion criteria

- With no environment variable set, an outside-directory, wrong-owner, or group/world-writable binary is rejected; `LLMAGENT_COMMAND_MODE=permissive` restores the basename allowlist.
- A PATH change or symlink retarget after validation does not change the returned path, and a swapped file is detected through the captured identity.
- No case in the file calls `filter_env` or asserts the wildcard token patterns.

## Out of Scope

- Implementing the confinement rules (row 3).
- The spawn-side identity re-check (row 4).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Add the test cases described in Implementation > Procedure/Method/Details | Completed | 20261126 | 20261126 | Plan Phase 1: expected to fail until row 3 lands Changed: tests/agent/test_http_lifecycle_command_validator.py; 47 cases fail as expected (Plan Phase 1) |
| 2 | Run the validation sequence (`rules/toolchain.md`) | Completed | — | 20261126 | ruff format+check pass; targeted pytest red as expected |

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
- **Requirement ID**: REQ-003 (validated path and identity), REQ-004 (strict confinement by default), REQ-009 (tests written before the implementation)
- **Source issue**: issues/20261119-145304_cliplc006_mcp-launch-spec-credentials.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261125-111909_cliplc006_mcp-launch-spec-credentials.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261125-223712
- **Related target files**: `tests/agent/test_http_lifecycle_command_validator.py`