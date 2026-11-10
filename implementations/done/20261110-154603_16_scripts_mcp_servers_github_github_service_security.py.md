## Goal
Remove the "empty `protected_branches` means no restriction" behavior from the github security guards and posture: the config load now rejects it, so an empty list reaching the service must not silently pass (`REQ-004`).

## Scope
**Release unit**: N/A: not part of a release unit


## Assumptions
- Measured (Plan Step 3a): deleting the `if not self._cfg.protected_branches: return` skip at `scripts/mcp_servers/github/github_service_security.py:172-173` fails exactly one test, `tests/mcp_servers/github/test_github_mcp_service.py::TestResolveAndCheckBranch::test_empty_protected_branches_skips_check_with_empty_branch`, which has its own document (row 79). Every other github test passes.
- A posture check set to FAILED makes the posture unvalidated, so the server refuses to bind and `/health` returns 503 (`tests/mcp_servers/github/test_github_health_posture.py:170-200` shows the mechanism for `server.repo_allowlist`).
- `path_denylist` empty keeps `NOT_APPLICABLE` (ADR-004 exception).

## Design decisions
- `_resolve_and_check_branch()` loses the early return; with a branch supplied it runs `_assert_allowed_branch()` (an empty pattern list matches nothing), with `branch=""` it resolves the default branch via the API and checks it.
- Posture: an empty `protected_branches` becomes `SecurityCheckStatus.FAILED` with `REASON_CONFIG_INVALID` (already imported at line 22) and detail `protected_branches is empty; at least one protected branch pattern is required`; the check id `server.protected_branches` is unchanged. The minimal fail-closed form: it cannot occur after the load rejection, but a mutated config (tests patch `github_server._cfg`) is reported, not passed.

## Alternatives considered
Keeping the posture as `NOT_APPLICABLE` was rejected: it would keep describing an empty list as a valid setting. A new reason code was rejected: `REASON_CONFIG_INVALID` already fits.

## Implementation
### Target file
`scripts/mcp_servers/github/github_service_security.py`

### Procedure
- `_resolve_and_check_branch()` (`github_service_security.py:164-185`): delete the `if not self._cfg.protected_branches: return` guard and the docstring sentence "Skips entirely when protected_branches is empty (no restrictions configured)."
- `_assert_allowed_branch()` docstring (line 148): remove "An empty list means no branch restrictions."
- `validate_github_security()` (the `if cfg.protected_branches:` / `else:` block at lines 318-333): replace the `else` branch with the FAILED check described above.

### Method
- Reuse `_check(...)`, `SecurityCheckStatus.FAILED`, and `REASON_CONFIG_INVALID`; no new import.

### Details
- `posture_contract.py:55` lists `server.protected_branches` as a required github check id; the id stays, so the contract is unchanged.
- Module size gate: confirm `uv run python tools/check_module_size.py` still passes (the file is near the limit if it is baselined).

### Companion test files
- `tests/mcp_servers/github/test_github_health_posture.py`
  - Procedure: Add `test_empty_protected_branches_makes_the_posture_unvalidated` (new) next to `test_empty_repo_allowlist_makes_the_posture_unvalidated` (around line 173): `_posture_with(monkeypatch, protected_branches=[])`, assert `posture.validated is False` and `server.protected_branches` in the failed check ids; extend the gate test to assert `server.protected_branches:config_invalid` in the log.
  - Validation: `uv run pytest tests/mcp_servers/github/test_github_health_posture.py -v`

## Compatibility considerations
A running github server whose config was loaded non-empty is unaffected. Only a patched or hand-built empty config now reports a failed posture and an extra default-branch API call on write paths.

## Security considerations
Removes the last in-code allow-all path for protected branches and reports the unreachable case as a failed posture instead of OK or not-applicable.

## Rollback considerations
Revert the commit that carries this change; no persisted state is touched.

## Validation plan
- `uv run pytest tests/mcp_servers/github -v` (the `test_github_mcp_service.py` skip test is handled by its own row)
- `uv run ruff format` and `uv run ruff check` on the two files; `uv run mypy --no-namespace-packages scripts/ tests/eventbus tools`
- `uv run python tools/check_module_size.py`

## Completion criteria
- No guard in `github_service_security.py` skips or describes an empty `protected_branches` as no restriction; posture reports it FAILED/`config_invalid`; empty `path_denylist` is still `NOT_APPLICABLE`.
- The companion posture test passes.

## Out of Scope
- `tests/mcp_servers/github/test_github_security_validation.py` (`test_empty_protected_branches` expects NOT_APPLICABLE, row 55) and `test_github_mcp_service.py` (row 79) have their own documents.
- Docs (`mcp_05_03`, `mcp_05_01`, `security_02`) are separate rows.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Remove the skip branch and the stale docstring sentences, and change the empty `protected_branches` posture check to FAILED | Done | 20261110-172551 | 20261110-172551 | FAILED + REASON_CONFIG_INVALID |
| 2 | Add the empty-list posture and gate cases in `tests/mcp_servers/github/test_github_health_posture.py` (companion) | Done | 20261110-172551 | 20261110-172551 | New test added next to the allowlist case; gate test extended with `server.protected_branches:config_invalid` |
| 3 | Run the validation sequence (`rules/toolchain.md`) and `check_module_size.py` | Done | 20261110-172551 | 20261110-172551 | 332 passed; 2 allowed reds pending their own rows: test_github_security_validation.py::test_empty_protected_branches (row 55), test_github_mcp_service.py::test_empty_protected_branches_skips_check_with_empty_branch (row 79); module size OK; mypy deferred to batch end gate |

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
- **Requirement ID**: `REQ-004` (remove the skip-when-empty branch and the posture text for an empty `protected_branches`)
- **Source issue**: issues/20261109-112640_adrrev004_non-strict-bypass-removal.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261110-094140_adrrev004_non-strict-bypass-removal.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261110-154603
- **Related target files**: `scripts/mcp_servers/github/github_service_security.py`, `tests/mcp_servers/github/test_github_health_posture.py`
