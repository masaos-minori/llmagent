## Goal

Add an explicit non-`NONE` `startup_mode` to `test_auth_token_empty_string_raises`'s `_http_cfg(auth_token="")` call, so the built config is genuinely "enabled" and `McpServerConfig._validate_auth_token`'s empty-string check actually fires (REQ-001).

## Scope

In scope: this one test's `_http_cfg(...)` call. Out of scope: `scripts/shared/mcp_config.py::_validate_auth_token`'s `is_disabled` gate (confirmed already correct and intentional); `_http_cfg`'s own default `startup_mode` omission for other, currently-passing tests (not touched — scoped to this one test's call).

## Assumptions

- `StartupMode.PERSISTENT` is an appropriate, minimal choice — `_http_cfg`'s existing defaults already include `url`, satisfying `PERSISTENT`'s own requirement (per `StartupMode`'s docstring: "PERSISTENT: url (enforced via HTTP-transport check)"), without needing to also supply `cmd` (which `SUBPROCESS` would require).

## Design decisions

- Add `startup_mode=StartupMode.PERSISTENT` as a kwarg to this one test's `_http_cfg(auth_token="")` call, rather than changing `_http_cfg`'s shared `defaults` dict (which could affect other, currently-passing tests using the same helper with different assumptions).

## Alternatives considered

- Changing `_http_cfg`'s shared `defaults` dict to include `startup_mode=StartupMode.PERSISTENT` by default: rejected — broader blast radius than necessary; only this one test currently needs an enabled-server scenario for this specific check.

## Implementation

### Target file

`tests/shared/test_mcp_config_validation.py`

### Procedure

1. Re-confirm `test_auth_token_empty_string_raises`'s exact current call via Read (`_http_cfg(auth_token="")`) — confirm `startup_mode` is still not passed (adversarial re-verification).
2. Change the call to `_http_cfg(auth_token="", startup_mode=StartupMode.PERSISTENT)`.
3. Confirm `StartupMode` is already imported in this file (via `rg -n "^from.*StartupMode\|^import.*StartupMode"`) — add the import if missing.

### Method

Direct kwarg addition to a single test's fixture-helper call — no structural change to `_http_cfg` itself.

### Details

- Before: `_http_cfg(auth_token="")`.
- After: `_http_cfg(auth_token="", startup_mode=StartupMode.PERSISTENT)`.
- `_validate_auth_token`'s confirmed logic (`scripts/shared/mcp_config.py:188-196`): `if not self.auth_token and not self.is_disabled: raise ValueError(...)` — with `startup_mode=StartupMode.PERSISTENT`, `is_disabled` (`startup_mode == StartupMode.NONE`) is `False`, so the empty-`auth_token` check now fires as intended.

## Compatibility considerations

- No production code changes; test-only fix confined to one test's fixture call.

## Security considerations

N/A: test-only fixture fix; restores coverage of an existing security-relevant validation (empty `auth_token` rejection for enabled servers).

## Rollback considerations

- `git revert` the commit, or manually remove the added `startup_mode` kwarg.

## Validation plan

| Target | Strategy | Command | Expected |
|---|---|---|---|
| `tests/shared/test_mcp_config_validation.py` | Unit | `uv run pytest tests/shared/test_mcp_config_validation.py -q` | All tests pass, including the previously-failing one |

## Completion criteria

- `uv run pytest tests/shared/test_mcp_config_validation.py::test_auth_token_empty_string_raises -q` passes.
- `uv run pytest tests/shared/test_mcp_config_validation.py -q` (full file) passes with no regression.

## Out of scope

- Other config-validation tests in this file (unaffected).
- `scripts/shared/mcp_config.py` (confirmed already correct).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | |
| 2 | Add or update tests per Validation plan | Pending | — | — | N/A: fixing the existing test's fixture call is itself the fix |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Pending | — | — | N/A: no docs/00_index.md task-scope mapping for this test file |

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
- **Requirement ID**: REQ-001: add explicit `startup_mode` to the test's fixture call
- **Source issue**: issues/20260927-075251_shared001_mcp-config-validation-does-not-raise-on-empty-auth_token.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260927-084512_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260927-092938
- **Related target files**: tests/shared/test_mcp_config_validation.py
