# Implementation Procedure — scripts/mcp_servers/cicd/cicd_service_guards.py

## Goal

Compare canonical identifier values in the guards, reject wildcard and oversized allowlist entries, add the credential posture check, and expose the read-permission probe result as a posture check.

## Scope
**Release unit**: N/A: not part of a release unit

Requirements implemented: REQ-003 (probe result reported as a posture check), REQ-005 (canonical identifier comparison), REQ-006 (allowlist normalization, wildcard and oversized rejection). Acceptance criteria: AC-2, AC-4, AC-5.

## Assumptions
- The network probe does not run in the pre-bind stage: `scripts/shared/security/startup_flow.py` runs the server stage through a synchronous callable (verified at line 162), so the pre-bind stage keeps a config-only credential check and the probe runs in the lifespan after bind (Plan D3, UNK-04 resolved by evidence).
- `REQUIRED_CHECK_IDS["cicd"]` allows extra checks (`scripts/shared/security/posture_contract.py:35,63`), so adding the credential check needs no contract change (verified: the comment at line 35 states "Extra checks are allowed").
- Step 3a verification (20261127): `tests/mcp_servers/cicd/test_cicd_security_validation.py:206` compares the produced check ids with the test's own `CICD_SERVER_CHECK_IDS` tuple as an ordered list, so the companion must insert `server.github_credential` at the position `validate_cicd_security()` emits it, not append it.
- Step 3a verification (20261127): `SecurityCheckResult.__post_init__()` calls `assert_non_secret()` on `message` (`scripts/shared/security/result_dto.py:146,106`), so every new check message must stay within `_MAX_PLAIN_TEXT_LEN` (120, line 94) and must not contain a credential-shaped value, an absolute path, or a config section header.
- The `CiBackend` protocol stays unchanged; the probe is a separate policy function (Plan assumption).

## Design decisions
- The credential check `server.github_credential` (new) is config-only and reads the effective credential through `resolve_effective_credential()` from the credential module, so posture, service, and health agree on one value (REQ-001).
- Guard matching compares canonical values produced by `canonical_workflow_id()` and `normalize_repo_key()` from the models row, not raw strings.

## Alternatives considered
- A synchronous `httpx.Client` probe inside the stage: rejected per Plan D3 — it would break the documented pure-function contract of `validate_cicd_security()`.

## Implementation
### Target file
`scripts/mcp_servers/cicd/cicd_service_guards.py`

### Procedure
- In `_assert_allowed_repo()`, compare the canonicalized request value against canonicalized allowlist entries instead of raw strings.
- Reject wildcard entries (`*`) and entries above `MAX_ALLOWLIST_SIZE` at validation time.
- Add `server.github_credential` (new) to `validate_cicd_security()`: FAILED when no effective credential exists for a write-capable start; the existing gate already refuses bind on an unvalidated posture.
- Expose the probe result as a posture check using the reason vocabulary from `scripts/shared/security/result_dto.py` (`REASON_DEPENDENCY_UNREACHABLE`, `REASON_NOT_APPLICABLE`); dispatch permission is reported `not_applicable` (REQ-003).

### Method
- `_assert_allowed_repo()` currently compares raw strings and `_assert_allowed_workflow()` rejects separators but performs no canonicalization (verified in Step 3a); add the canonicalization call before the comparison.
- `validate_cicd_security()` currently reports four check ids and treats an awaitable probe as `not_applicable` (verified); keep it pure and synchronous — the lifespan supplies the probe result separately.

### Details
- Newly rejected inputs are listed in the Plan's change record (wildcard entries, oversized entries).

## Compatibility considerations
- Allowlist entries that are already canonical match unchanged; entries differing only by case or separators are normalized or rejected (Plan Risk, mitigated by the companion tests).

## Security considerations
- The credential check names only the check id and reason code; it never reports the token (AC-2).

## Rollback considerations
- N/A: revert the commit.

## Validation plan
- Unit: guard matching on canonical values, posture check inventory — `uv run pytest tests/mcp_servers/cicd/test_cicd_security_validation.py` (companion).
- Full sequence per `rules/toolchain.md`.

## Completion criteria
- Wildcard and oversized entries fail before bind and the empty allowlist stays fatal (AC-5); the credential check reports FAILED without a credential (AC-2); request and allowlist values canonicalize identically (AC-4).

## Out of Scope
- The canonicalization function itself (`cicd_models.py` row); the network probe execution point (`cicd_server.py` row).

### Companion test files
- `tests/mcp_servers/cicd/test_cicd_security_validation.py`
  - Procedure: extend the pinned `CICD_SERVER_CHECK_IDS` inventory (lines 25-30) with `server.github_credential` (new) and add wildcard, oversized, credential-absence, and probe cases (read-permitted, read-denied, rate-limited, timeout, `not_applicable`).
  - Validation: `uv run pytest tests/mcp_servers/cicd/test_cicd_security_validation.py`.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 20261127-163457 | 20261127-163457 | files: scripts/mcp_servers/cicd/cicd_service_guards.py; call site in cicd_server.py updated for the new argument |
| 2 | Add or update tests per Validation plan (companion test file) | Completed | 20261127-163457 | 20261127-163457 | companion 30 tests pass; oversized-entry case is asserted in test_cicd_models.py (config parse), not duplicated here |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20261127-163457 | — | ruff/mypy/bandit/lint-imports clean; 6 failures in test_cicd_health_posture.py and test_cicd_server_endpoints.py are the new fail-closed credential posture surfacing in pins re-pinned by procedure seq 06; full suite deferred to end of batch the 6 pins that went red were re-pinned in this cycle (test_cicd_health_posture.py, test_cicd_server_endpoints.py); tests/mcp_servers/cicd/ 261 passed end-of-batch full suite: 6 failures all matching tools/known_test_failures_baseline.txt; diff-cover 96% |
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
- **Requirement ID**: REQ-003, REQ-005, REQ-006 (probe posture check, canonical comparison, allowlist normalization and rejection)
- **Source issue**: issues/20261119-141106_mcpci001_cicd-credential-config-contract.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261126-152931_mcpci001_cicd-credential-config-contract.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261127-145310
- **Related target files**: `scripts/mcp_servers/cicd/cicd_service_guards.py`, `tests/mcp_servers/cicd/test_cicd_security_validation.py`