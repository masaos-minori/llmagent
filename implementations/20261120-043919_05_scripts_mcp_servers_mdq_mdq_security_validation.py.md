## Goal

Delete `_auth_token_check()` and its call in `validate_mdq_security()` from
`scripts/mcp_servers/mdq/mdq_security_validation.py`, so MDQ's self-validation reports the same
single auth posture fact (`common.auth_token`) as every other MCP server (REQ-007, AC-06).

## Scope
**Release unit**: mdq-auth-check-removal (with procedures 04, 06 and both companion tests)

## Assumptions

- The auth decision is a duplicate report, not an enforcement point: `mdq_server.py` startup
  token loading and `startup_flow.check_auth_token_present` are untouched (Plan A-1, verified in
  Plan Step 2).
- `_mdq_config_view()`'s `auth_token_present` key (line 81) is a redacted config-view fact, not a
  posture check, and stays unchanged (`TestConfigView` depends on it).

## Design decisions

- Full deletion of the check function and its reason code rather than leaving dead code: an
  unused private check and reason constant would fail ruff VLD/unused-code checks and mislead
  readers into thinking MDQ has a special auth posture (Plan Design decision 2).

## Alternatives considered

- Keep `_auth_token_check` unused for rollback convenience: rejected — dead code violates the
  repository lint contract and the removal is the point of the release unit.

## Implementation
### Target file
`scripts/mcp_servers/mdq/mdq_security_validation.py`

### Procedure
1. Delete the `_auth_token_check(mdq_cfg)` entry from the check tuple inside
   `validate_mdq_security()` (call at line 108).
2. Delete the `_auth_token_check()` function definition (lines 117–131).
3. If `REASON_AUTH_TOKEN_MISSING` is defined in this module and no longer referenced anywhere
   (`rg REASON_AUTH_TOKEN_MISSING scripts/ tests/` after the deletion), delete its definition;
   if it lives in a shared module and other servers use it, leave it.
4. Remove imports that become unused (run ruff; remove only what ruff flags).

### Method
- The remaining MDQ server-scoped checks are the 5 from the contract sibling (procedure 04):
  allowed dirs configured/exist, db path valid, schema valid, index available, plus the shared
  common checks from `build_mdq_posture` composition.

### Details
- Do not touch the module docstring sentence "auth_token is never carried by value" (line 76) or
  the `auth_token_present` key in `_mdq_config_view` (line 81): both describe the config-view
  redaction contract, which is unchanged.
- `scripts/mcp_servers/mdq/health_check.py` exposes the posture built by this module; its check
  list follows the contract automatically — no direct edit needed there (verify with
  `TestHealthEndpointPosture`).

### Companion test files
- `tests/mcp_servers/mdq/test_mdq_security_validation.py`
  - Procedure: drop `"server.auth_token_configured"` from `MDQ_CHECK_IDS` (lines 47–48), delete `class TestAuthTokenConfigured` (lines 168–190), remove the unused `REASON_AUTH_TOKEN_MISSING` import (line 35), and fix any residual mdq check-count assertions to the 5-check contract.
  - Validation: `uv run pytest tests/mcp_servers/mdq/test_mdq_security_validation.py` passes; `rg "auth_token_configured|REASON_AUTH_TOKEN_MISSING" tests/mcp_servers/mdq/test_mdq_security_validation.py` returns nothing.

## Compatibility considerations

- Consumers of `validate_mdq_security`/`build_mdq_posture`: MDQ `health_check.py` and the MDQ
  server startup path — both read the check list from the contract, no hardcoded 6-check
  expectation outside the test file (verified: `rg validate_mdq_security|build_mdq_posture` hits
  only this module, `mdq_server.py`, `health_check.py`, and the test).

## Security considerations

- Enforcement unchanged: an empty token still fails MDQ startup (`mdq_server.py`), and
  `common.auth_token` still reports the posture WARNING via `startup_flow` — the removal does not
  create an unauthenticated MDQ path (Plan Risk 2).

## Rollback considerations

- Revert the whole release unit commit; a partial revert breaks the contract-mirror or
  health-contracts drift gate.

## Validation plan

- `uv run pytest tests/mcp_servers/mdq/`
- `rg "REASON_AUTH_TOKEN_MISSING" scripts/ tests/` — no dangling reference after the deletion.
- Full `rules/toolchain.md` sequence at unit completion (ruff, mypy, pytest).

## Completion criteria

- `validate_mdq_security()` returns exactly the 5 server-scoped checks + common checks; no auth
  check function or reason-code import remains for mdq; the companion test file passes with the
  5-check contract (Plan AC-06, AC-08).

## Out of Scope

- `_mdq_config_view` and its `auth_token_present` key.
- `mdq_server.py` and `health_check.py` (no edit; behavior verified via tests).
- The posture contract itself (procedure 04).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Delete _auth_token_check call, function, dead constant/imports | Pending | — | — | Release unit mdq-auth-check-removal |
| 2 | Update companion test MDQ_CHECK_IDS and remove TestAuthTokenConfigured | Pending | — | — | Same commit |
| 3 | Run tests/mcp_servers/mdq and full toolchain with the unit | Pending | — | — | |

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
- **Requirement ID**: `REQ-007` (remove the MDQ self-validation auth check)
- **Source issue**: issues/20261117-123020_adrchk020_mandatoriness-registry-posture.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261120-001311_adrchk020_mandatoriness-registry-posture.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261120-043919
- **Related target files**: `scripts/mcp_servers/mdq/mdq_security_validation.py`, `tests/mcp_servers/mdq/test_mdq_security_validation.py`
