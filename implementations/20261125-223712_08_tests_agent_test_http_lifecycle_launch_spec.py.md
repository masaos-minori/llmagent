## Goal

Cover the `LaunchSpec` contract, the fixed process options, the minimal per-server environment, and the key-names-only audit line (REQ-001 launch-spec contract, REQ-006 minimal environment, REQ-007 audit names only, REQ-009 tests written before the implementation).

## Scope
**Release unit**: N/A: not part of a release unit

## Assumptions

- The file does not exist yet; the module it tests is created by row 2, so these cases are written against the contract the Plan states and are expected to fail (import error) until row 2 lands (Plan Phase 1).
- Tests import from `agent.http_lifecycle_launch_spec` (the agent-layer import style used by the sibling test files under `tests/agent/`).

## Design decisions

- Assert the contract by attempting the forbidden construction rather than by reading the source: `dataclasses.replace` on a frozen spec, and a `popen_kwargs()` key-set comparison, so a future field that reopens an override channel fails the test (AC-2).
- Cross-server isolation is proven with a two-server fixture in one parent environment, which is the only way to show that server A's child lacks server B's tokens (AC-3).

## Alternatives considered

Asserting through the launcher with a mocked `Popen` was rejected for this file: the launcher has its own test file (row 10), and the spec contract must be provable without a spawn.

## Implementation
### Target file
`tests/agent/test_http_lifecycle_launch_spec.py` (new)
### Procedure
Write the spec-contract, option, environment, isolation, and audit cases.

### Method
- Spec immutability: build a spec through `build_launch_spec` and assert `dataclasses.replace` raises, and that `argv[0]` is the validated absolute path while a relative or non-string argument is rejected.
- Fixed options: assert `popen_kwargs()` keys are exactly `start_new_session`, `stdout`, `stderr`, `env`, with `start_new_session is True` and `stdout` equal to `subprocess.DEVNULL`, and that no `shell`, `preexec_fn`, or `cwd` key ever appears (REQ-001, REQ-002).
- Minimal environment: assert `build_child_env` returns a `dict` when `cfg.env` is empty, contains the REQ-006 fixed runtime set, and drops a denylisted or protected-variable override from the configured `env`.
- Credential isolation: with MCP_GITHUB_AUTH_TOKEN, MCP_GITHUB_CONTROL_TOKEN, MCP_CICD_AUTH_TOKEN, MCP_CICD_CONTROL_TOKEN, and `GITHUB_TOKEN` all present in the parent, assert the `github` spec holds its own two tokens plus `GITHUB_TOKEN` (declared) and none of `cicd`'s, and the `cicd` spec holds the reverse with no `GITHUB_TOKEN` (AC-3).
- Audit: capture `caplog` and assert the launch line contains the environment key names and none of their values.
- Identity: assert `verify_identity` (new) reports a mismatch after the file behind the validated path is replaced.

### Details
- Use `monkeypatch.setenv` for the parent environment and `monkeypatch.delenv` for the fixed-set variables that must be absent, so the assertions do not depend on the developer's shell.
- Point `LLMAGENT_BINARY_DIR` at a tmp directory with an executable fixture, matching the validator tests' existing style.

## Compatibility considerations

New file; no existing test depends on it. It imports only row 2's module and `shared.mcp_config`.

## Security considerations

N/A: this row only asserts the guarantees rows 1-3 implement.

## Rollback considerations

N/A: revert the commit.

## Validation plan

- `uv run pytest tests/agent/test_http_lifecycle_launch_spec.py`
- Expected outcome before row 2 lands: the file fails to import (Plan Phase 1)

## Completion criteria

- A spec cannot be constructed or mutated to carry `shell`, `env` override, `stdout`, `stderr` override, `start_new_session=False`, or `preexec_fn`.
- The isolation cases prove each server's environment holds its own two tokens and no other server's.
- The audit case proves no environment value reaches a log line.

## Out of Scope

- Implementing `LaunchSpec` (row 2).
- The shipped-config loop over every server (row 11).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Add the test cases described in Implementation > Procedure/Method/Details | Pending | — | — | Plan Phase 1: expected to fail until row 2 lands |
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
- **Requirement ID**: REQ-001 (launch-spec contract), REQ-006 (minimal environment), REQ-007 (audit key names only), REQ-009 (tests written before the implementation)
- **Source issue**: issues/20261119-145304_cliplc006_mcp-launch-spec-credentials.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261125-111909_cliplc006_mcp-launch-spec-credentials.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261125-223712
- **Related target files**: `tests/agent/test_http_lifecycle_launch_spec.py`
