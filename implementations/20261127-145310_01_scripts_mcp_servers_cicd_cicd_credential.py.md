# Implementation Procedure — scripts/mcp_servers/cicd/cicd_credential.py

## Goal

Own the effective-credential resolution as one pure policy function with the documented precedence (environment variable wins, config value is the fallback), used by service construction, startup posture, and health.

## Scope
**Release unit**: N/A: not part of a release unit

Requirements implemented: REQ-001 (one effective-credential resolution function with documented precedence). Acceptance criterion: AC-1.

## Assumptions
- The precedence is the user decision recorded on 20261126 (UNK-01): environment wins, config is the fallback; this document keeps the existing order, it does not change it.
- The module is policy-only: no I/O, no logging, no config access (Plan row 1).

## Design decisions
- Plan D1: the resolution lives in a new leaf module inside `scripts/mcp_servers/cicd/`, not in `cicd_models.py` (config parsing and models) or `cicd_service_defs.py` (constants and protocol layer).
- The function is pure and synchronous so both the pre-bind posture stage and health can call it without a network.

## Alternatives considered
- Put the function in `cicd_models.py`: rejected per Plan D1 — that module owns config parsing, not environment policy.
- Put it in `cicd_service_defs.py`: rejected per Plan D1 — defs is the cycle-breaking constants layer.

## Implementation
### Target file
`scripts/mcp_servers/cicd/cicd_credential.py` (new)

### Procedure
- Define `resolve_effective_credential(cfg: CicdConfig) -> str` (new): return `os.environ.get("GITHUB_TOKEN")` when it is non-empty, otherwise `cfg.github_token`.
- Import only the standard library (`os`) and `CicdConfig` from `mcp_servers.cicd.cicd_models`; no logging, no config access.

### Method
- One function, no state. The sibling procedures (`cicd_service_init.py`, `cicd_server.py`, `cicd_service_guards.py`) read the effective value only through this function.

### Details
- Replaces the inline resolution at `scripts/mcp_servers/cicd/cicd_service_init.py:26` (`os.environ.get("GITHUB_TOKEN", cfg.github_token)`), which is removed by the sibling procedure for that row.
- `scripts/agent/` must not import this module; `tests/agent/test_security_audit_config_isolation.py:11` pins the forbidden Agent import list.

### Companion test files
- `tests/mcp_servers/cicd/test_cicd_credential.py` (new)
  - Procedure: add the credential matrix (environment only, config only, both, neither) asserting the same effective value, and the startup-refusal case: no effective credential produces a FAILED posture check.
  - Validation: `uv run pytest tests/mcp_servers/cicd/test_cicd_credential.py`.

## Compatibility considerations
- Values that already resolve to the same effective token are unchanged; only the call sites move to this function.

## Security considerations
- Never log or echo the token; the function returns the value without recording it, mirroring `require_auth_token()` in `scripts/mcp_servers/server.py` which names only the server and the variable.

## Rollback considerations
- N/A: revert the commit (one new file).

## Validation plan
- Unit: pure resolution matrix, no I/O — `uv run pytest tests/mcp_servers/cicd/test_cicd_credential.py`.
- Full sequence per `rules/toolchain.md`: ruff, mypy, bandit, targeted pytest, then the full suite.

## Completion criteria
- All four matrix cases produce the documented effective value; the module imports only the standard library plus `cicd_models`; no `scripts/agent/` import exists.

## Out of Scope
- Startup refusal (implemented in the `cicd_service_guards.py` and `cicd_server.py` rows) and the network probe (REQ-003).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | |
| 2 | Add or update tests per Validation plan (companion test file) | Pending | — | — | |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | N/A | — | — | documentation is covered by the Plan's docs rows |

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
- **Requirement ID**: REQ-001 (one effective-credential resolution function with documented precedence)
- **Source issue**: issues/20261119-141106_mcpci001_cicd-credential-config-contract.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261126-152931_mcpci001_cicd-credential-config-contract.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261127-145310
- **Related target files**: `scripts/mcp_servers/cicd/cicd_credential.py`, `tests/mcp_servers/cicd/test_cicd_credential.py`
