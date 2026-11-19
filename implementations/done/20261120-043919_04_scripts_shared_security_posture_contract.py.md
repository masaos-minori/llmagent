## Goal

Remove `"server.auth_token_configured"` from `REQUIRED_CHECK_IDS["mdq"]` in
`scripts/shared/security/posture_contract.py` so every MCP server carries exactly one auth
posture check (`common.auth_token`) and MDQ no longer duplicates it server-side (REQ-006,
AC-05).

## Scope
**Release unit**: mdq-auth-check-removal (with procedures 05, 06 and both companion tests)

## Assumptions

- `mdq_server.py` refuses to start without a token (`require_auth_token("mdq-mcp", ...
  _AUTH_TOKEN)` at line 484 raises `RuntimeError` on an empty token, independent of the
  posture gate; `_load_auth_token()` at line 87 itself returns `""` on config failure) and
  `check_auth_token_present` (`scripts/shared/security/startup_flow.py:132-144`,
  WARNING semantics) remains the single auth posture fact — verified in Plan Step 2; neither
  may change (Plan Out-of-Scope).
- `common.auth_token` remains in `COMMON_CHECK_IDS` and therefore in MDQ's posture — the removal
  is server-scoped only.

## Design decisions

- Delete the mdq-scoped id from the contract rather than mark it deprecated: the contract is a
  live tuple set consumed by posture builders and the health-contracts manifest generator, and no
  consumer depends on the removed id (Plan Design decision 2).

## Alternatives considered

- Keeping the id with a no-op check: rejected — it keeps the duplicate-posture fact the Plan
  removes (Plan Goal).

## Implementation
### Target file
`scripts/shared/security/posture_contract.py`

### Procedure
1. In `REQUIRED_CHECK_IDS["mdq"]` (lines 99–107), delete the `"server.auth_token_configured"`
   entry. The mdq tuple keeps exactly: `server.allowed_dirs_configured`,
   `server.allowed_dirs_exist`, `server.db_path_valid`, `server.schema_valid`,
   `server.index_available`.
2. Change nothing else: no other server tuple, `COMMON_CHECK_IDS`, reason-code constants, or
   posture-builder logic.

### Method
- Single-line deletion inside the mdq block. Ruff/mypy must stay clean (a dangling trailing comma
  or reformat is fixed by the formatter, not hand-adjusted).

### Details
- `tools/generate_reference_table.py` derives `registry/manifests/health_contracts.yaml` from
  this file (source mapping, line 497): the manifest regeneration is the sibling procedure
  `implementations/20261120-043919_06_registry_manifests_health_contracts.yaml.md` in the same
  release unit.
- MDQ's own self-validation consumes this contract (sibling procedure 05).

### Companion test files
- `tests/shared/test_security_posture_contract.py`
  - Procedure: drop the mdq `"server.auth_token_configured"` entry from the `SERVER_CHECK_IDS` mirror dict (starts line 33; id at line 90) and update any mdq check-count assertion to the 5-check server-scoped contract.
  - Validation: `uv run pytest tests/shared/test_security_posture_contract.py` passes; `rg "server.auth_token_configured" tests/shared/test_security_posture_contract.py` returns nothing.

## Compatibility considerations

- Downstream consumers: MDQ self-validation (procedure 05 removes the duplicate call), the
  health-contracts manifest (procedure 06 regenerates it), and the two contract-mirror tests.
  No other server's tuple changes, so all other servers' posture is byte-identical.

## Security considerations

- The auth enforcement path is untouched: `mdq_server.py` still requires a token at startup and
  `common.auth_token` still reports the token posture for every server. Removing a duplicate
  report does not weaken enforcement (Plan Risk 2 mitigation A-1).

## Rollback considerations

- Revert the whole release unit commit (contract + MDQ validation + manifest + both test files)
  together; partial reverts leave the drift gate or contract-mirror tests failing.

## Validation plan

- `uv run pytest tests/shared/test_security_posture_contract.py tests/mcp_servers/mdq/`
- `uv run python tools/generate_reference_table.py --check` exit 0 after procedure 06
  regeneration.
- `rg "server.auth_token_configured" scripts/ tests/ registry/` returns no mdq-scoped match after
  the unit completes (common-scope `common.auth_token` matches are expected and fine).

## Completion criteria

- `REQUIRED_CHECK_IDS["mdq"]` has exactly the 5 server-scoped ids listed above; the companion
  mirror agrees; no mdq-scoped `server.auth_token_configured` remains anywhere in `scripts/`,
  `tests/`, or `registry/` (Plan AC-05, AC-08).

## Out of Scope

- `scripts/shared/security/startup_flow.py` `check_auth_token_present` (must not change).
- `scripts/mcp_servers/mdq/mdq_server.py` token loading (must not change).
- Other servers' check tuples.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Remove server.auth_token_configured from REQUIRED_CHECK_IDS["mdq"] | Completed | 2026-11-20 | 2026-11-20 | Release unit mdq-auth-check-removal mdq tuple now 5 ids |
| 2 | Update companion test mirror SERVER_CHECK_IDS | Completed | 2026-11-20 | 2026-11-20 | Same commit; mirror updated, rg empty |
| 3 | Run targeted tests + drift gate with procedures 05/06 | Completed | 2026-11-20 | 2026-11-20 | 503 targeted passed; --check exit 0; full suite 13091 passed |

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
- **Requirement ID**: `REQ-006` (remove server.auth_token_configured from the MDQ posture contract)
- **Source issue**: issues/20261117-123020_adrchk020_mandatoriness-registry-posture.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261120-001311_adrchk020_mandatoriness-registry-posture.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261120-043919
- **Related target files**: `scripts/shared/security/posture_contract.py`, `tests/shared/test_security_posture_contract.py`