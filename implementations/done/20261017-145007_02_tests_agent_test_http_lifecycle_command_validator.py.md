## Goal

Bring `tests/agent/test_http_lifecycle_command_validator.py` in line with the default-deny
`filter_env` contract, and add unit coverage for the allowlist, key-only redaction, the denylist
applied to the server `env`, and the `None` passthrough.

## Scope

- `tests/agent/test_http_lifecycle_command_validator.py` only (row 2 of the Plan's
  `Implementation Target Files`): rewrite the three tests in `TestCommandValidatorFilterEnv`
  (lines 248-288) and add the new cases listed below.
- The integration gate lives in row 3's file, not here.

## Assumptions

- The three existing tests assert the old contract and are inconsistent with default-deny:
  `test_inherited_denylist_keys_stripped_when_cfg_env_empty` (line 264) and
  `test_benign_inherited_vars_preserved` (line 276) assert that arbitrary parent variables are
  inherited; `test_config_non_protected_var_merges_and_protected_override_logged` (line 288)
  asserts the warning text contains the secret value `HOME=hacked`.
- `patch.dict(os.environ, {...}, clear=False)` is the existing pattern for parent-environment
  control in this file; keep it.

## Design decisions

- Assert absence by name, not by counting keys: a test must not depend on which variables happen
  to exist on the developer's or CI's machine, so each test names the variable it expects to be
  dropped or kept.
- Redaction is asserted in both directions: the key appears in the warning and the value does not
  appear anywhere in `caplog.text`.

## Alternatives considered

- Replace the class with a new class: rejected, the existing class name and docstring are already
  referenced by the Plan's Validation plan and by `-k` selection; keeping it preserves the diff
  review signal.
- Assert the exact allowlist contents here: rejected, that is row 3's job against the shipped
  config; here the allowlist is exercised through representative names only.

## Implementation
### Target file
`tests/agent/test_http_lifecycle_command_validator.py`
### Procedure
1. Rewrite `test_inherited_denylist_keys_stripped_when_cfg_env_empty` so the parent contains a
   fake secret (`FAKE_PARENT_SECRET`) and an allowlisted name (`PATH`), and assert the secret is
   absent while `PATH` is present.
2. Replace `test_benign_inherited_vars_preserved` with `test_unlisted_parent_vars_are_not_inherited`
   (`BENIGN_A`, `BENIGN_B` dropped) and `test_allowlisted_parent_vars_are_inherited`
   (`PATH`, `HOME`, `MCP_SHELL_AUTH_TOKEN` present — proves the `MCP_*_AUTH_TOKEN` pattern works).
3. Rewrite the protected-override test as `test_protected_override_warning_logs_key_only`:
   assert `"HOME"` is named in the warning and `"hacked"` is not in `caplog.text`.
4. Add `test_denylisted_key_in_server_env_is_blocked` (`env={"PYTHONPATH": "/z"}` → key absent
   from the result) and `test_none_passthrough` (`filter_env(None) is None`).
### Method
Edit the existing class in place; keep the module's existing imports (`os`, `logging`, `patch`).
### Details
- Use a distinctive fake value (for example `"fake-secret-value"`) for the dropped secret so the
  redaction assertion cannot pass by accident.
- Do not hard-code the whole allowlist in assertions; name only the variables each test is about.

## Compatibility considerations

- Test-only change; no runtime blast radius. The three rewritten tests are the Plan's regression
  items (`REQ-001`..`REQ-004`).

## Security considerations

- The tests are the guard that keeps the secret value out of logs (`AC-002`) and unrelated parent
  credentials out of the child (`AC-001`).

## Rollback considerations

N/A: revert the commit — test-only file, no runtime state.

## Validation plan

- `uv run pytest tests/agent/test_http_lifecycle_command_validator.py -v` — all pass.
- `uv run pytest tests/agent/test_http_lifecycle_command_validator.py -k "none or redact or denylist"`
  — the Plan's targeted selection passes.
- Mutation check: temporarily removing `PATH` from `_DEFAULT_ALLOWED_ENV_VARS` must fail
  `test_allowlisted_parent_vars_are_inherited` (run locally, then revert).

## Completion criteria

- No test in the file asserts default-ALLOW inheritance or a value-bearing warning.
- The new cases for allowlist drop, allowlist keep, key-only redaction, server-`env` denylist, and
  `None` passthrough exist and pass (`AC-001`..`AC-005`).

## Out of scope

- The real-child startup gate and config `${ENV:...}` alignment (row 3).
- Any change to `scripts/agent/http_lifecycle_command_validator.py` (row 1) or to
  `scripts/agent/http_lifecycle.py` (Reference File).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Rewrite the three obsolete `TestCommandValidatorFilterEnv` tests | Completed | 20261017-145927 | 20261017-152000 |  |
| 2 | Add allowlist-drop, allowlist-keep, redaction, denylist-in-server-env, `None` tests | Completed | 20261017-145927 | 20261017-152000 |  |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20261017-145927 | 20261017-152000 |  |

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
- **Requirement ID**: `REQ-001`, `REQ-002`, `REQ-003`, `REQ-004`, `REQ-005`
- **Source issue**: `issues/20261016-093044_mcp004_filter_env_secret_logging_env_leak.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261016-110959_plan.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261017-145007
- **Related target files**: `tests/agent/test_http_lifecycle_command_validator.py`