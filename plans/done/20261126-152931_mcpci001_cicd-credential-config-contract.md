# Unify CI/CD GitHub credential, configuration, schema, and HTTP client lifecycle

## Goal
- Give cicd-mcp one effective GitHub credential contract, one strict request-model source for its published schemas, one canonical workflow-identifier form, pre-bind configuration validation, and a lifespan-owned shared HTTP client, so service construction, startup posture, and health cannot disagree.

## Priority
High

## Scope
- **In-Scope**:
  - Effective-credential resolution with documented precedence (environment variable wins, config value is the fallback), used by service construction, startup posture, and health.
  - Fail-closed startup for write-capable mode when no effective credential exists.
  - Side-effect-free read-permission and API-reachability probe; dispatch permission reported as `not_applicable`.
  - Published tool `inputSchema` generated from the shared strict request base model (`extra="forbid"`) plus the CI/CD constraints `run_id >= 1`, `limit` 1..50, non-empty `repo`/`workflow`/`ref`.
  - Canonical workflow identifier applied identically to request values and allowlist entries; URL-encoded as one path segment.
  - Repository allowlist entries validated with the shared `owner/repo` helper; wildcard and oversized-value rejection; hard maximum for allowlist size.
  - `max_log_size_kb >= 1` with a hard maximum using the shared strict numeric parsing.
  - `httpx.AsyncClient` created and closed in the FastAPI lifespan; import-time construction removed; test injection kept.
  - Configuration errors fail before bind.
- **Out-of-Scope**: dispatch reconciliation (mcpci002), log streaming bounds (mcpci003), error and audit mapping (mcpci004).
- **Dependencies**: Closed dependencies already implemented in source — mcpai002 (shared strict numeric parsing, `owner/repo` normalization) and mcpai003 (shared strict request base and schema generator). This Plan does not wait on them. It blocks mcpci002, mcpci003, and the final state of mcpci004.

## Background
The Issue comes from the consolidated Web Search and CI/CD MCP backlog (`memo-issue.md`, Issue 5) and names two archived issues to re-verify: cicdallow01 (workflow allowlist file-name form) and mcpstart003 (empty `auth_token` startup). Both are implemented: `config/cicd_mcp_server.toml` now carries a file-name value (`workflow_allowlist = ["ci.yml"]`), and `scripts/mcp_servers/server.py:250-260` `require_auth_token()` refuses an empty token at import, which `cicd_server.py:124-128` uses. The remaining gap is the credential, schema, identifier, and client-lifecycle contract.

## Problem
`scripts/mcp_servers/cicd/cicd_service_init.py:26` resolves the credential as `os.environ.get("GITHUB_TOKEN", cfg.github_token)` and only warns when it is empty, while `scripts/mcp_servers/cicd/cicd_server.py:200` health reads only the environment variable, so service and health can disagree. A tokenless, write-capable server binds its HTTP port. `scripts/mcp_servers/cicd/cicd_tools.py` publishes hand-written schemas that carry no runtime constraints, while `scripts/mcp_servers/cicd/cicd_models.py` request models carry some constraints and no `extra="forbid"`, so the contract a client discovers at `/v1/tools` is not the contract enforced at call time. Workflow values are accepted as either a file name or a numeric id with no canonicalization, and `scripts/mcp_servers/cicd/cicd_service_github_actions.py:111` interpolates the raw value into a URL path. Allowlists are validated only as lists. The shared `httpx.AsyncClient` is created inside `build_service()` with no shutdown path.

## Reason for Change
Startup and credential behavior is security-sensitive, and this Plan is the prerequisite for workflow-dispatch reconciliation and log retrieval, which both depend on a stable credential and identifier contract.

## Implementation Intent
One credential-resolution policy function is the single source of the effective token for service construction, posture, and health. Strict request models are the source of the published schemas. Identifiers are canonicalized by one function used by both the request path and the allowlist comparison, and encoded as a single path segment. Configuration bounds fail before bind. The shared HTTP client is created and closed in the FastAPI lifespan while remaining injectable in tests.

## Requirements
- `REQ-001`: One effective-credential resolution function with documented precedence — the environment variable wins, the config value is the fallback — used by service construction, startup posture, and health.
- `REQ-002`: Write-capable startup refuses to bind when no effective credential exists (posture `FAILED`, existing gate reads `validated`).
- `REQ-003`: A side-effect-free probe reports credential validity, API reachability, and Actions read permission; workflow-dispatch permission is reported `not_applicable` because no side-effect-free GitHub endpoint exposes write permission. Rate-limit status is reported without exposing the token.
- `REQ-004`: Published tool schemas are generated from the strict request models (`extra="forbid"`) with the CI/CD constraints `run_id >= 1`, `limit` 1..50, and non-empty `repo`, `workflow`, `ref`.
- `REQ-005`: The workflow identifier is a validated file name or a positive numeric id, canonicalized identically for request values and allowlist entries, and URL-encoded as one path segment.
- `REQ-006`: Repository allowlist entries are validated with the shared `owner/repo` normalization policy; wildcard entries and oversized values are rejected; the allowlist carries a hard maximum size.
- `REQ-007`: `max_log_size_kb` must be `>= 1` and at most its hard maximum, using the shared strict numeric parsing.
- `REQ-008`: The shared `httpx.AsyncClient` is created and closed in the FastAPI lifespan; import-time construction is removed and test injection is kept.
- `REQ-009`: Malformed configuration fails before HTTP bind.
- `REQ-010`: Documentation records the credential precedence, the required GitHub Actions permissions, empty-allowlist behavior, the workflow-identifier terminology and both identifier forms, and the module layout including the composite and job backends.

## Implementation Target Files
**Freeze status**: Frozen — `issue-to-plan` Step 8's Implementation Target Files
Validation passed for every row on 20261126; see `rules/workflow-lifecycle.md`
Implementation Target Files Validation (Plan Freeze).

This table is the canonical, frozen source of implementation scope for this Plan. Once
`Frozen`, `Implementation steps`, `Acceptance criteria`, and every downstream
`plan-to-implementation-procedure` document MUST reference file paths only from this
table — no other file may be treated as a modification target.

| File Path | Change Responsibility | Reason for Modification | Related Requirement / Acceptance Criterion | Repository Evidence | Related Tests | Validation Status |
|---|---|---|---|---|---|---|
| `scripts/mcp_servers/cicd/cicd_credential.py` | Create | New policy-only module owning the effective-credential resolution with documented precedence; no I/O, no logging, no config access | REQ-001, AC-1 | Does not exist; `scripts/mcp_servers/cicd/` holds 15 files and none owns credential policy (checked in Step 3) | `tests/mcp_servers/cicd/test_cicd_credential.py` | Verified |
| `scripts/mcp_servers/cicd/cicd_models.py` | Modify | Adopt `StrictRequestModel`, add the CI/CD constraints, the canonical workflow-identifier function, the hard maximum constants, and shared `owner/repo` normalization for allowlist entries | REQ-004, REQ-005, REQ-006, REQ-007, AC-3, AC-5 | Request models at lines 88-137 have no `model_config` and no shared strict base (re-verified 20261127, file is 137 lines); `limit` already `ge=1, le=50`, `run_id` `gt=0`; `from_dict()` uses `get_typed` for lists and `max_log_size_kb` with no positivity or size bound (checked in Step 2) | `tests/mcp_servers/cicd/test_cicd_models.py` | Verified |
| `scripts/mcp_servers/cicd/cicd_tools.py` | Modify | Publish `inputSchema` built from the strict request models instead of hand-written property dicts | REQ-004, AC-3 | `TOOL_LIST` entries build `inputSchema` from module-level property dicts with `type` and `description` only; no `build_input_schema` import (checked in Step 2) | `tests/mcp_servers/cicd/test_tool_server_layer_consistency.py` | Verified |
| `scripts/mcp_servers/cicd/cicd_service_guards.py` | Modify | Compare canonical identifier values, reject wildcard and oversized allowlist entries, add the credential posture check, and expose the read-permission probe result as a posture check | REQ-003, REQ-005, REQ-006, AC-2, AC-4, AC-5 | `_assert_allowed_repo()` compares raw strings against the allowlist; `_assert_allowed_workflow()` rejects separators but performs no canonicalization; `validate_cicd_security()` reports four check ids and treats an awaitable probe as `not_applicable` (checked in Step 2) | `tests/mcp_servers/cicd/test_cicd_security_validation.py` | Verified |
| `scripts/mcp_servers/cicd/cicd_service_init.py` | Modify | Use the resolved effective credential and stop constructing `httpx.AsyncClient` at service-init time; accept an injected client | REQ-001, REQ-008, AC-1, AC-6 | Lines 24-41 resolve the token inline, warn only, and create `httpx.AsyncClient(timeout=30.0)` inside `build_service()` (checked in Step 2) | `tests/mcp_servers/cicd/test_cicd_lifecycle.py` | Verified |
| `scripts/mcp_servers/cicd/cicd_server.py` | Modify | Add the FastAPI lifespan that owns the shared client, make health report the effective credential and the probe outcome, and keep the pre-bind gate fail-closed for a missing credential | REQ-001, REQ-002, REQ-003, REQ-008, AC-1, AC-2, AC-4, AC-6 | `health()` at lines 195-212 reads `os.environ.get("GITHUB_TOKEN", "")` only; the module has no lifespan and builds the service at import time; `_enforce_posture_gate()` at lines 238-254 already refuses bind on an unvalidated posture (checked in Step 2) | `tests/mcp_servers/cicd/test_cicd_health_posture.py`, `tests/mcp_servers/cicd/test_mcp_server_health_status.py`, `tests/mcp_servers/cicd/test_cicd_server_endpoints.py` | Verified |
| `scripts/mcp_servers/cicd/cicd_service_business.py` | Modify | Canonicalize the request identifier before the guard and the backend call | REQ-005, AC-4 | `_parse_repo()` raises on a bad slug but does not normalize it; `handle_trigger_workflow()` passes `req.workflow` unchanged to the guard and the backend (checked in Step 3) | `tests/mcp_servers/cicd/test_cicd_mcp_service.py` | Verified |
| `scripts/mcp_servers/cicd/cicd_service_github_actions.py` | Modify | Encode the canonical workflow identifier as one URL path segment | REQ-005, AC-4 | Line 111 interpolates `workflow` into the dispatch URL with `f"{_GITHUB_API_BASE}/repos/{owner}/{repo}/actions/workflows/{workflow}/dispatches"` and no quoting (checked in Step 3) | `tests/mcp_servers/cicd/test_service_github_actions_error_edges.py` | Verified |
| `config/cicd_mcp_server.toml` | Modify | Document the effective-credential precedence and the hard maximum values the new validation enforces | REQ-001, REQ-006, REQ-007, AC-5 | File exists; `github_token = ""` is commented as a fallback when `GITHUB_TOKEN` is unset; `max_log_size_kb = 256` has no stated maximum (checked in Step 2) | `tests/mcp_servers/cicd/test_cicd_models.py` | Verified |
| `tests/mcp_servers/cicd/test_cicd_models.py` | Modify | Re-pin the schema shape after `extra="forbid"`, the new constraints, canonicalization, and the hard maximums | REQ-004, REQ-005, REQ-006, REQ-007, AC-3, AC-5 | Characterization tests at lines 34-45 and 153-170 pin the current schema shape, descriptions, and config parsing (checked in Step 3) | this file | Verified |
| `tests/mcp_servers/cicd/test_cicd_security_validation.py` | Modify | Extend the pinned check-id inventory with the credential check and add wildcard, oversized, and probe cases | REQ-003, REQ-006, AC-2, AC-4, AC-5 | `CICD_SERVER_CHECK_IDS` at lines 25-30 pins exactly four check ids; lines 206-233 assert the produced list equals it (checked in Step 3) | this file | Verified |
| `tests/mcp_servers/cicd/test_cicd_health_posture.py` | Modify | Assert health uses the effective credential and carries the probe outcome; correct the stale empty-token docstring | REQ-001, REQ-003, AC-1, AC-4 | Line 36 docstring says cicd-mcp keeps the empty-token accept-all path, which `require_auth_token()` (`scripts/mcp_servers/server.py:250-260`) no longer does; line 113 builds the posture from `cfg.github_token` (checked in Step 3) | this file | Verified |
| `tests/mcp_servers/cicd/test_mcp_server_health_status.py` | Modify | Update the 503-when-token-not-set case to the fail-closed startup rule and the effective-credential source | REQ-001, REQ-002, AC-1, AC-2 | Lines 60-80 pop `GITHUB_TOKEN` from the environment and assert a degraded response, which only reproduces while startup still binds without a credential (checked in Step 3) | this file | Verified |
| `tests/mcp_servers/cicd/test_cicd_server_endpoints.py` | Modify | Update the health endpoint characterization to the effective credential and the probe block | REQ-001, REQ-003, AC-1, AC-4 | Lines 268-285 assert `dependencies == {}` after setting only the environment variable (checked in Step 3) | this file | Verified |
| `tests/mcp_servers/cicd/test_cicd_credential.py` | Create | New tests for the credential matrix (environment only, config only, both, neither), startup refusal, and the read-permission probe cases | REQ-001, REQ-002, REQ-003, AC-1, AC-2, AC-4 | Does not exist; `tests/mcp_servers/cicd/` holds 11 test files and none covers credential resolution or the probe (checked in Step 3) | this file | Verified |
| `tests/mcp_servers/cicd/test_cicd_lifecycle.py` | Create | New tests for lifespan startup and shutdown, repeated construction, and test injection of the client | REQ-008, AC-6 | Does not exist; no cicd test drives a lifespan, and `tests/mcp_servers/cicd/test_mcp_cicd_edge_cases.py` injects a client directly (checked in Step 3) | this file | Verified |
| `tests/mcp_servers/cicd/test_cicd_mcp_service.py` | Modify | Add canonicalization cases to the guard tests that pin the current raw-string matching | REQ-005, AC-4 | Lines 131-173 assert guard behavior for `ci.yml`, `deploy.yml`, `../ci.yml`, and `..\ci.yml` against raw allowlist values (checked in Step 3) | this file | Verified |
| `docs/22_mcp/mcp_04_03_rag-pipeline-and-cicd.md` | Modify | Record credential precedence, required GitHub Actions permissions, empty-allowlist behavior, workflow-identifier terminology, and the module layout | REQ-010 | Lines 56-72 document the current config keys, `GITHUB_TOKEN` authentication, health dependency values, and the guard behavior (checked in Step 3) | `uv run python tools/check_docs_structure.py` | Verified |
| `docs/22_mcp/mcp_05_01_access-control-and-allowlists.md` | Modify | Record the CI/CD allowlist normalization, wildcard and oversized-value rejection, and the new credential posture check | REQ-006, REQ-010 | Lines 39, 88, 133-142 document the cicd allowlists and the posture check that refuses bind (checked in Step 3) | `uv run python tools/check_docs_structure.py` | Verified |

Rules (see `rules/workflow-lifecycle.md` Implementation Target Files Validation (Plan
Freeze) for the full validation procedure): one row per file; test, configuration, and
documentation files carry their own rows; `Validation Status` is `Verified` for every row.

## Reference Files
Files that must be read to implement the targets above, but MUST NOT be modified.

| File Path | Why It Must Be Read | Related Target File or Requirement |
|---|---|---|
| `scripts/mcp_servers/request_contract.py` | `StrictRequestModel` and `build_input_schema()` are the shared strict base and schema generator the CI/CD models must adopt | REQ-004 |
| `scripts/shared/repo_identity.py` | `normalize_repo_key()` and `is_canonical_repo_key()` are the shared normalization policy the allowlist must reuse | REQ-006 |
| `scripts/shared/config_utils.py` | `get_typed()` and `get_non_negative_number()` are the shared strict numeric parsing the `max_log_size_kb` bound must use | REQ-007 |
| `scripts/shared/security/posture_contract.py` | `REQUIRED_CHECK_IDS["cicd"]` lists the four required ids and states that extra checks are allowed, so the new credential check needs no contract change | REQ-002, REQ-003 |
| `scripts/shared/security/result_dto.py` | Reason codes including `REASON_DEPENDENCY_UNREACHABLE` and `REASON_NOT_APPLICABLE` are the vocabulary the probe result must use | REQ-003 |
| `scripts/shared/security/startup_flow.py` | The `SERVER_SECURITY_VALIDATION` stage calls a synchronous callable, which is why the network probe cannot run in the pre-bind stage | REQ-003, REQ-009 |
| `scripts/mcp_servers/health_response.py` | `make_health_response()` derives `ready` from `deps` plus `security.validated`; the Plan must not invent its own ready rule | REQ-002, REQ-003 |
| `scripts/mcp_servers/server.py` | `run_http()` runs the loopback, config-isolation, and posture gates before any socket, and `require_auth_token()` already refuses an empty inbound token | REQ-002 |
| `scripts/mcp_servers/cicd/cicd_service_defs.py` | `CiBackend` protocol, `_GITHUB_API_BASE`, and `build_auth_headers()`; the protocol stays unchanged so the probe is not added to it | REQ-003, REQ-005 |
| `scripts/mcp_servers/cicd/cicd_service_github_actions_composite.py` | Shows how the injected client reaches the workflow and job backends; the lifespan client must reach the same path | REQ-008 |
| `scripts/mcp_servers/cicd/cicd_service_github_actions_job.py` | Consumes the injected client and `max_log_size_kb`; must keep working with a lifespan-owned client | REQ-007, REQ-008 |
| `scripts/mcp_servers/rag_pipeline/rag_pipeline_server.py` | The existing FastAPI `lifespan` precedent that cicd-mcp must follow | REQ-008 |
| `tests/mcp_servers/cicd/test_tool_server_layer_consistency.py` | Guardrail that compares each server's `TOOL_LIST` schema with its dispatch table; it must still pass after schemas are generated from models | REQ-004 |
| `tests/agent/test_security_audit_config_isolation.py` | Pins the forbidden Agent import list that includes `from mcp_servers.cicd.cicd_models`; the new credential module must not be imported from `scripts/agent/` | REQ-001 |
| `tests/conftest.py` | Sets `MCP_CICD_AUTH_TOKEN` for the test suite; the credential tests must not depend on a real secret | REQ-001 |
| `docs/22_mcp/mcp_07_tool_schema_export_policy.md` | The `TOOL_LIST` export policy the schema change must stay consistent with | REQ-004 |
| `config/agent.toml` | `[mcp_servers.cicd]` declares `credential_env = ["GITHUB_TOKEN"]`, the Agent-side view of the credential contract | REQ-001 |
| `conf.d/cicd-mcp` | The deployment environment file that supplies `GITHUB_TOKEN`; the documented precedence must match what it sets | REQ-001 |

## Acceptance Criteria
- `AC-1`: Service construction, startup posture, and health read the same effective credential through one resolution function (REQ-001).
- `AC-2`: A write-capable start with no effective credential refuses to bind; the gate reports the failed check id and reason code only (REQ-002).
- `AC-3`: The published `inputSchema` and the runtime request models enforce the same contract, including `extra="forbid"` and the CI/CD numeric and non-empty constraints (REQ-004).
- `AC-4`: Numeric workflow ids and file names are canonicalized by the same function, and URL construction cannot be altered by separators or unsafe encoding (REQ-005).
- `AC-5`: Malformed configuration — empty allowlist, wildcard entry, oversized value, `max_log_size_kb` below 1 or above its hard maximum — fails before bind (REQ-006, REQ-007, REQ-009).
- `AC-6`: Application shutdown closes the lifespan-owned shared HTTP client, and tests can still inject their own client (REQ-008).
- `AC-7`: The probe reports permission, reachability, and rate-limit status without exposing the token, and reports dispatch permission as `not_applicable` (REQ-003).
- `AC-8`: Documentation states the precedence, the required Actions permissions, the empty-allowlist behavior, both identifier forms, and the module layout (REQ-010).

## Tests
- Credential matrix: environment only, config only, both, and neither; each case asserts the same effective value in service, posture, and health (REQ-001, AC-1; `tests/mcp_servers/cicd/test_cicd_credential.py`).
- Startup refusal: no effective credential produces a `FAILED` posture check and a refused bind (REQ-002, AC-2; `tests/mcp_servers/cicd/test_cicd_credential.py`, `tests/mcp_servers/cicd/test_cicd_security_validation.py`).
- Probe cases: invalid credential, read-permitted, read-denied, rate-limited, and timeout, all against a mocked transport; dispatch permission asserted as `not_applicable` (REQ-003, AC-7; `tests/mcp_servers/cicd/test_cicd_credential.py`).
- Model and schema parity: strict base, `run_id >= 1`, `limit` 1..50, non-empty `repo`/`workflow`/`ref`, and the published schema equals the model schema (REQ-004, AC-3; `tests/mcp_servers/cicd/test_cicd_models.py`, `tests/mcp_servers/cicd/test_tool_server_layer_consistency.py`).
- Identifier cases: file name, numeric id, path separator, percent-encoding, wildcard, duplicate, blank, and invalid repository forms, asserted identically for request values and allowlist entries (REQ-005, REQ-006, AC-4, AC-5; `tests/mcp_servers/cicd/test_cicd_models.py`, `tests/mcp_servers/cicd/test_cicd_mcp_service.py`, `tests/mcp_servers/cicd/test_cicd_security_validation.py`).
- Lifespan: startup creates the client, shutdown closes it, repeated construction does not leak a client, and an injected client is used unchanged (REQ-008, AC-6; `tests/mcp_servers/cicd/test_cicd_lifecycle.py`).
- Newly rejected inputs are listed in the change record: extra request fields, blank `repo`/`workflow`/`ref`, `limit` outside 1..50, `run_id` below 1, wildcard allowlist entries, allowlist entries above the hard maximum, `max_log_size_kb` below 1 or above its hard maximum (REQ-004, REQ-006, REQ-007, AC-3, AC-5).
- Full validation sequence per `rules/toolchain.md`: ruff, mypy, bandit, targeted pytest, then the full suite (all Requirements).

## Documentation Impact
Yes. Per `docs/00_index.md` "Document References by Task" (MCP server spec), the MCP domain docs are the reference set; the concrete targets named by the Issue are `docs/22_mcp/mcp_04_03_rag-pipeline-and-cicd.md` (credential precedence, required GitHub Actions permissions, empty-allowlist behavior, workflow-identifier terminology and both identifier forms, module layout including the composite and job backends) and `docs/22_mcp/mcp_05_01_access-control-and-allowlists.md` (CI/CD allowlist normalization, wildcard and oversized-value rejection, the new credential posture check). Driven by REQ-010.

## Assumptions
- The documented precedence already exists in `config/cicd_mcp_server.toml` ("fallback when GITHUB_TOKEN env var is unset") and in the current code, so the Plan keeps environment-over-config as the contract rather than changing it (user decision, 20261126).
- The hard maximum values are the user-approved constants recorded in Design: `max_log_size_kb` 1..1024, allowlist size 1..100 entries. No repository convention exists for hard maximums, so these are Plan decisions, not derived values.
- `REQUIRED_CHECK_IDS` allows extra checks, so adding the credential check does not require modifying `scripts/shared/security/posture_contract.py`.
- The `CiBackend` protocol stays unchanged; the probe is a separate policy function, so existing backends and their tests are not affected.
- Sibling open issues mcpci002, mcpci003, and mcpci004 are compatible overlaps: mcpci002 targets the dispatch backends, mcpci003 the job backend, and mcpci004 `exception_handlers.py` plus `cicd_server.py`. This Plan changes `cicd_server.py` only in the health, lifespan, and gate paths, which mcpci004's error-mapping design does not contradict.
- `docs/22_mcp/mcp_01_tool_ownership_matrix.md` is generated from `registry/manifests/mcp_endpoints.yaml`; tool names do not change, so it is not affected.
- Cross-plan target overlap reported by `tools/check_plan_target_overlaps.py` on `docs/22_mcp/mcp_04_03_rag-pipeline-and-cicd.md`: open Plan `plans/20261126-072155_mcpai012_mcp-design-docs-update.md` also targets it as a consistency sweep against current source. The designs do not contradict — this Plan adds the credential, permission, and identifier contract statements, while mcpai012 corrects existing statements. Sequencing: run mcpai012's CI/CD sweep after this Plan's Phase 10 lands, otherwise the sweep rewrites the section against the pre-change source.

## Unknowns
| ID | Unknown Description | Evidence Missing | Resolution Path | Blocking? (True/False) |
|---|---|---|---|---|
| UNK-01 | Environment-versus-config precedence for the GitHub credential | None; `config/cicd_mcp_server.toml` documents config as the fallback and `cicd_service_init.py:26` implements that order | Resolved by user decision on 20261126: environment variable wins; the Plan records it as the contract | False |
| UNK-02 | How a token's Actions permissions can be probed without side effects | GitHub exposes no side-effect-free endpoint for write permission; read permission is probeable with `GET /repos/{owner}/{repo}/actions/workflows` | Resolved by user decision on 20261126: probe read permission only; dispatch permission is reported `not_applicable` | False |
| UNK-03 | Hard maximum for `max_log_size_kb` and allowlist size | No repository convention or constant exists (`rules/coding.md`, `rules/toolchain.md`, `scripts/shared/` searched) | Resolved by user decision on 20261126: `max_log_size_kb` 1..1024, allowlist size 1..100; recorded as Plan constants | False |
| UNK-04 | Whether the network probe can run in the pre-bind posture stage | `scripts/shared/security/startup_flow.py` runs the server stage through a synchronous callable, and `validate_cicd_security()` is documented as a pure function | Resolved by evidence: the probe runs in the lifespan after bind; the pre-bind stage keeps a config-only credential check | False |
| UNK-05 | Whether a process holds the shared dedup store lock | `fuser` is not installed on this host, so the check could not be run; `ss` shows no listener on port 8012 | Re-check on the deployment host before the deploy hand-off | False |

## Affected areas
`skills/DESIGN.md` Change-impact table, extended with `Churn (30d)` and `Bus Factor`.

| File | Change | Blast Radius | Churn (30d) | Bus Factor | deploy.sh Impact |
|---|---|---|---|---|---|
| `scripts/mcp_servers/cicd/cicd_credential.py` | Create | Medium | N/A: new file | N/A: new file | not applicable (rsynced) |
| `scripts/mcp_servers/cicd/cicd_models.py` | Modify | High — 11 direct consumers plus 25 test references, including `cicd_server.py`, `cicd_service_business.py`, and the Agent config-isolation test | 1 | High (single author) | not applicable (rsynced) |
| `scripts/mcp_servers/cicd/cicd_tools.py` | Modify | Medium — `TOOL_LIST` is read by `cicd_server.py`, the layer-consistency guard, and the registry | 1 | High (single author) | not applicable (rsynced) |
| `scripts/mcp_servers/cicd/cicd_service_guards.py` | Modify | Medium — 4 consumers; the check-id inventory is pinned by `tests/mcp_servers/cicd/test_cicd_security_validation.py` | 0 | High (single author) | not applicable (rsynced) |
| `scripts/mcp_servers/cicd/cicd_service_init.py` | Modify | Low — one importer (`cicd_service.py`) plus `cicd_server.py` | 0 | High (single author) | not applicable (rsynced) |
| `scripts/mcp_servers/cicd/cicd_server.py` | Modify | High — module-level service and posture construction, health, gate, and the shared `MCPServer` contract | 3 | High (single author) | not applicable (rsynced) |
| `scripts/mcp_servers/cicd/cicd_service_business.py` | Modify | Low — dispatch handlers and the guard mixin | 0 | High (single author) | not applicable (rsynced) |
| `scripts/mcp_servers/cicd/cicd_service_github_actions.py` | Modify | Medium — shared by the composite backend and the error-edge tests | 0 | High (single author) | not applicable (rsynced) |
| `config/cicd_mcp_server.toml` | Modify | Low — read by `CicdConfig.load()` and the Agent entry for `cicd` | 3 | High (single author) | existing cp line at `deploy/deploy.sh:164`; no change needed |
| `tests/mcp_servers/cicd/test_cicd_models.py` | Modify | Low | 1 | High (single author) | not applicable (tests are not deployed) |
| `tests/mcp_servers/cicd/test_cicd_security_validation.py` | Modify | Low — pins the four-check inventory | 0 | High (single author) | not applicable (tests are not deployed) |
| `tests/mcp_servers/cicd/test_cicd_health_posture.py` | Modify | Low | 0 | High (single author) | not applicable (tests are not deployed) |
| `tests/mcp_servers/cicd/test_mcp_server_health_status.py` | Modify | Low | 0 | High (single author) | not applicable (tests are not deployed) |
| `tests/mcp_servers/cicd/test_cicd_server_endpoints.py` | Modify | Medium — highest-churn test file in the area | 5 | High (single author) | not applicable (tests are not deployed) |
| `tests/mcp_servers/cicd/test_cicd_credential.py` | Create | Low | N/A: new file | N/A: new file | not applicable (tests are not deployed) |
| `tests/mcp_servers/cicd/test_cicd_lifecycle.py` | Create | Low | N/A: new file | N/A: new file | not applicable (tests are not deployed) |
| `tests/mcp_servers/cicd/test_cicd_mcp_service.py` | Modify | Medium — 28 recorded tests execute `cicd_service_business.py` through this file | 0 | High (single author) | not applicable (tests are not deployed) |
| `docs/22_mcp/mcp_04_03_rag-pipeline-and-cicd.md` | Modify | Medium — cross-checked by `check_docs_consistency.py --domain mcp` | 4 | High (single author) | not applicable (docs are not deployed) |
| `docs/22_mcp/mcp_05_01_access-control-and-allowlists.md` | Modify | Medium | 3 | High (single author) | not applicable (docs are not deployed) |

## Design

### Architecture analysis
- Import direction for the target files: `cicd_models.py` → `shared.config_loader`, `shared.config_utils`, pydantic; `cicd_service_guards.py` → `shared.security.result_dto`, `cicd_models`, `cicd_service_defs`; `cicd_service_init.py` → `cicd_models`, `cicd_service_business`, `cicd_service_defs`, httpx; `cicd_server.py` → `cicd_models`, `cicd_service`, `cicd_service_guards`, `cicd_tools`, `shared.security.startup_flow`, `shared.security.posture_contract`, `shared.security.result_dto`, `mcp_servers.*`.
- `lint-imports` reports 6 contracts kept, 0 broken. The new `cicd_credential.py` must stay inside `mcp_servers` and may import only pydantic-free standard library plus `cicd_models`; it must not be imported from `scripts/agent/` (`tests/agent/test_security_audit_config_isolation.py` pins the forbidden import list).
- No cycle is introduced: the credential module is a leaf inside the cicd package, and `cicd_service_defs.py` already exists to break the service_init/service_business cycle.

### Dependency graphing
- `CicdConfig`: 11 direct consumers in `scripts/` and 25 in `tests/` — the widest surface in this Plan, so its validation change is the highest blast-radius row.
- `build_service`: one importer (`cicd_service.py`), plus `cicd_server.py` module-level construction.
- `validate_cicd_security`: 4 consumers in `scripts/`, 7 in `tests/`, 1 documentation citation in `docs/22_mcp/mcp_05_01_access-control-and-allowlists.md`.
- `_assert_allowed_workflow`: 3 consumers in `scripts/`, 6 in `tests/`, 1 documentation citation.
- `_parse_repo`: 3 consumers in `scripts/`, 3 in `tests/`.
- Files that require changes: the 19 rows of `Implementation Target Files`.

### Consumer scan results
- `CicdConfig` candidates: `scripts/mcp_servers/cicd/cicd_models.py`, `cicd_server.py`, `cicd_service_business.py`, `cicd_service_init.py` (all target rows); `tests/agent/test_security_audit_config_isolation.py` is a reference row, not affected because the Plan does not add an Agent-side import.
- `build_service` candidates outside the cicd package are git-server citations for a different `build_service`; not affected.
- `TOOL_LIST` candidates in `docs/22_mcp/mcp_00_document-guide.md`, `mcp_01_tool_ownership_matrix.md`, `mcp_03_01_dispatch-and-routing.md`, `mcp_03_05_lifecycle-and-new-server.md`, `mcp_07_tool_schema_export_policy.md`: not affected, because the export name and tool names do not change, only the schema source.
- `TriggerWorkflowRequest` / `GetWorkflowRunsRequest` candidates: `cicd_service_business.py` (target row), `test_cicd_models.py` (target row), `test_cicd_exception_handlers.py` and `test_cicd_mcp_service.py` — the latter is a target row for its guard tests; `test_cicd_exception_handlers.py` is not affected because it only imports the exception types.

### Predictable fallout check
- Module size: every target file is under the 24576 B gate (largest is `cicd_server.py` at 10056 B); the new `cicd_credential.py` is a small policy module, so no split row is needed.
- Pinned counts: `tests/mcp_servers/cicd/test_cicd_security_validation.py` pins exactly four cicd check ids, so adding the credential check makes that file a target row. `tests/mcp_servers/cicd/test_cicd_models.py` pins the schema shape and field descriptions, so it is a target row. `tests/shared/test_security_posture_contract.py` compares `REQUIRED_CHECK_IDS` with `SERVER_CHECK_IDS` and allows extra checks — not affected.
- Tool inventory: no `tools/*.py` is added or removed — not affected.
- Generated blocks: `docs/22_mcp/mcp_01_tool_ownership_matrix.md` is generated from `registry/manifests/mcp_endpoints.yaml`; tool names and endpoints do not change — not affected.

### Design decisions
1. **Credential resolution home**: a new policy-only module `scripts/mcp_servers/cicd/cicd_credential.py` with one pure function that returns the effective credential. Alternatives: put it in `cicd_models.py` (rejected — that module owns config parsing and models, not environment policy) or in `cicd_service_defs.py` (rejected — defs is the constants and protocol layer and was extracted to break a cycle). Compatibility impact: `scripts/agent/` must not import it.
2. **Probe scope**: read permission only, side-effect-free, via `GET /repos/{owner}/{repo}/actions/workflows`; dispatch permission is reported `not_applicable`. Alternative rejected: a dry-run dispatch probe, which is a side effect. Compatibility impact: no existing check changes status for a token that has read permission but not write permission.
3. **Probe execution point**: the pre-bind stage keeps a config-only credential check (`server.github_credential`), and the network probe runs in the lifespan after bind and feeds `/health`. The startup stage is synchronous and `validate_cicd_security()` is documented as a pure function, so a network probe there would break its contract. Alternative rejected: a synchronous `httpx.Client` probe in the stage.
4. **Client lifecycle**: `build_service()` receives the client as an argument instead of creating it; the FastAPI lifespan creates and closes it, following `scripts/mcp_servers/rag_pipeline/rag_pipeline_server.py`. Test injection is preserved because tests already pass their own client to the backends.
5. **Workflow identifier canonical form**: a validated file name or a positive numeric id, produced by one function used by both the request path and the allowlist comparison, and encoded with `urllib.parse.quote(..., safe="")` as one path segment. Compatibility impact: values that are already canonical are unchanged; values that differ only by case or leading separators are now normalized or rejected.
6. **Hard maximums**: `max_log_size_kb` 1..1024 and allowlist size 1..100, defined as module constants in `cicd_models.py`. These are Plan decisions approved by the user on 20261126; no repository convention exists.
7. **Operational dependency inspection**: `ss` shows no listener on port 8012 on this host; `fuser` is not installed, so the dedup-store lock check is recorded as not run (UNK-05). `pip-audit` reports no finding for `httpx`, `pydantic`, `fastapi`, `uvicorn`, or `orjson`, so no dependency upgrade is planned.

### Validation quality baseline
- `radon cc` (per Python target file): `cicd_models.py` max A(2); `cicd_tools.py` A(1); `cicd_service_guards.py` B(7) at `validate_cicd_security()`; `cicd_service_init.py` A(2); `cicd_server.py` max A(4); `cicd_service_business.py` max A(3); `cicd_service_github_actions.py` max A(5).
- `vulture scripts/mcp_servers/cicd/ --min-confidence 80`: no findings (files scanned).
- `bandit -r scripts/mcp_servers/cicd/ -c pyproject.toml`: 1 Low/Medium finding, `B105` at `cicd_server.py:202` (`deps["github_token"] = "not_set"`). The health change keeps this literal; if the literal moves, the finding must be re-checked rather than suppressed.
- `diff-cover`: no lines with coverage information in the current diff (no code change yet). The Plan must raise diff coverage to the `rules/toolchain.md` Completion checklist threshold of 90% on changed lines.
- Full-suite baseline recorded on 20261126: 26 failed, 15330 passed, 5 skipped, 44 errors, with `NameError: name 'RuntimeToolRegistry'` errors in `tests/agent/` — pre-existing and outside this Plan's scope. `tests/mcp_servers/cicd/` passes 216 tests.

## Implementation steps
1. **Phase 1: Credential contract**
   - [ ] Create the policy-only resolution module with the documented precedence (environment wins, config fallback) and no I/O, logging, or config access (REQ-001; `scripts/mcp_servers/cicd/cicd_credential.py`)
   - [ ] Add the credential matrix and startup-refusal tests (REQ-001, REQ-002; `tests/mcp_servers/cicd/test_cicd_credential.py`)
2. **Phase 2: Strict request models and configuration bounds**
   - [ ] Adopt `StrictRequestModel`, add the non-empty `repo`/`workflow`/`ref` constraints, keep `limit` 1..50 and `run_id >= 1`, add the hard maximum constants, the shared `owner/repo` normalization for allowlist entries, and the single canonical workflow-identifier function (REQ-004, REQ-005, REQ-006, REQ-007; `scripts/mcp_servers/cicd/cicd_models.py`)
   - [ ] Re-pin the schema shape and add the newly rejected input cases (REQ-004, REQ-005, REQ-006, REQ-007; `tests/mcp_servers/cicd/test_cicd_models.py`)
3. **Phase 3: Published schemas from models**
   - [ ] Build each `inputSchema` from the strict request models with `build_input_schema()` (REQ-004; `scripts/mcp_servers/cicd/cicd_tools.py`)
   - [ ] Confirm the schema/model parity assertions still pass (REQ-004; `tests/mcp_servers/cicd/test_cicd_models.py`)
4. **Phase 4: Guard canonicalization and pre-bind validation**
   - [ ] Compare canonical values, reject wildcard and oversized allowlist entries, and add the credential posture check that keeps an empty allowlist fatal (REQ-002, REQ-005, REQ-006, REQ-009; `scripts/mcp_servers/cicd/cicd_service_guards.py`)
   - [ ] Extend the pinned check-id inventory and add the wildcard, oversized, and refusal cases (REQ-002, REQ-006, REQ-009; `tests/mcp_servers/cicd/test_cicd_security_validation.py`)
5. **Phase 5: Canonical identifier at call time and in the URL**
   - [ ] Canonicalize the request identifier before the guard and the backend call (REQ-005; `scripts/mcp_servers/cicd/cicd_service_business.py`)
   - [ ] Encode the canonical identifier as one URL path segment (REQ-005; `scripts/mcp_servers/cicd/cicd_service_github_actions.py`)
   - [ ] Add the separator, percent-encoding, duplicate, blank, and invalid-repository cases to the guard tests (REQ-005, REQ-006; `tests/mcp_servers/cicd/test_cicd_mcp_service.py`)
6. **Phase 6: Lifespan-owned shared client**
   - [ ] Make `build_service()` accept an injected client and remove import-time construction (REQ-008; `scripts/mcp_servers/cicd/cicd_service_init.py`)
   - [ ] Add the FastAPI lifespan that creates and closes the client, following the rag-pipeline precedent (REQ-008; `scripts/mcp_servers/cicd/cicd_server.py`)
   - [ ] Add lifespan startup, shutdown, repeated-construction, and test-injection tests (REQ-008; `tests/mcp_servers/cicd/test_cicd_lifecycle.py`)
7. **Phase 7: Probe and health parity**
   - [ ] Run the side-effect-free read-permission probe in the lifespan and report permission, reachability, and rate-limit status without the token; report dispatch permission as `not_applicable` (REQ-003; `scripts/mcp_servers/cicd/cicd_server.py`)
   - [ ] Make health read the same effective credential as the service (REQ-001; `scripts/mcp_servers/cicd/cicd_server.py`)
   - [ ] Update the health posture assertions and correct the stale empty-token docstring (REQ-001, REQ-003; `tests/mcp_servers/cicd/test_cicd_health_posture.py`)
   - [ ] Update the degraded-response case to the fail-closed startup rule (REQ-001, REQ-002; `tests/mcp_servers/cicd/test_mcp_server_health_status.py`)
8. **Phase 8: Health endpoint characterization**
   - [ ] Update the health endpoint assertions to the effective credential and the probe block (REQ-001, REQ-003; `tests/mcp_servers/cicd/test_cicd_server_endpoints.py`)
9. **Phase 9: Configuration record**
   - [ ] Document the effective-credential precedence and the hard maximum values in the server configuration file (REQ-001, REQ-006, REQ-007; `config/cicd_mcp_server.toml`)
10. **Phase 10: Documentation**
    - [ ] Update the CI/CD server section: credential precedence, required GitHub Actions permissions, empty-allowlist behavior, workflow-identifier terminology and both forms, module layout including the composite and job backends (REQ-010; `docs/22_mcp/mcp_04_03_rag-pipeline-and-cicd.md`)
    - [ ] Update the CI/CD allowlist section: normalization, wildcard and oversized-value rejection, and the new credential posture check (REQ-006, REQ-010; `docs/22_mcp/mcp_05_01_access-control-and-allowlists.md`)
11. **Phase 11: Deployment and verification**
    - [ ] Hand off to `skills/deploy/SKILL.md`: the change must be committed and pushed first, and deploying is the user's decision (approval gate). `config/cicd_mcp_server.toml` already has a `cp` line in `deploy/deploy.sh`; `scripts/` is rsynced. Confirm no process holds the dedup store lock before restart (UNK-05), then restart cicd-mcp and verify `/health` reports the effective credential and the probe outcome (REQ-001, REQ-003, REQ-008; `scripts/mcp_servers/cicd/cicd_server.py`, `config/cicd_mcp_server.toml`)

### Release units
**Unit**: shared client and probe | **Phases**: 6, 7 | **Reason**: Phase 7's probe uses the client created by Phase 6's lifespan, so Phase 7 cannot be validated alone.

## Validation plan
| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| `scripts/mcp_servers/cicd/cicd_credential.py` | Unit: pure resolution matrix, no I/O | `uv run pytest tests/mcp_servers/cicd/test_cicd_credential.py` | Environment-only, config-only, both, and neither cases produce the same effective value |
| `scripts/mcp_servers/cicd/cicd_models.py` | Unit: model validation and schema shape | `uv run pytest tests/mcp_servers/cicd/test_cicd_models.py` | `extra="forbid"`, `limit` 1..50, `run_id >= 1`, non-empty fields, hard maximums enforced |
| `scripts/mcp_servers/cicd/cicd_tools.py` | Integration: published schema equals the model schema | `uv run pytest tests/mcp_servers/cicd/test_tool_server_layer_consistency.py` | Schema, dispatch table, registry, and write/serial flags stay consistent |
| `scripts/mcp_servers/cicd/cicd_service_guards.py` | Unit: guard matching on canonical values, posture check inventory | `uv run pytest tests/mcp_servers/cicd/test_cicd_security_validation.py` | Wildcard and oversized entries fail before bind; empty allowlist stays fatal |
| `scripts/mcp_servers/cicd/cicd_service_init.py` | Unit: injected client used unchanged | `uv run pytest tests/mcp_servers/cicd/test_cicd_lifecycle.py` | No client is created at service-init time |
| `scripts/mcp_servers/cicd/cicd_server.py` | Integration: lifespan startup/shutdown and health parity | `uv run pytest tests/mcp_servers/cicd/test_cicd_lifecycle.py tests/mcp_servers/cicd/test_cicd_health_posture.py tests/mcp_servers/cicd/test_mcp_server_health_status.py tests/mcp_servers/cicd/test_cicd_server_endpoints.py` | Shutdown closes the client; health reports the effective credential and the probe outcome |
| `scripts/mcp_servers/cicd/cicd_service_business.py` | Unit: canonicalization before guard and backend | `uv run pytest tests/mcp_servers/cicd/test_cicd_mcp_service.py` | Request and allowlist values canonicalize identically |
| `scripts/mcp_servers/cicd/cicd_service_github_actions.py` | Unit: URL path segment encoding | `uv run pytest tests/mcp_servers/cicd/test_service_github_actions_error_edges.py` | Separators and unsafe encoding cannot alter the path |
| `config/cicd_mcp_server.toml` | Cross-check | `uv run python tools/check_docs_consistency.py --domain mcp` | Documented values match the enforced constants |
| `docs/22_mcp/mcp_04_03_rag-pipeline-and-cicd.md` | Structural and content policy | `uv run python tools/check_docs_quality.py` and `uv run python tools/check_docs_structure.py` | No findings |
| `docs/22_mcp/mcp_05_01_access-control-and-allowlists.md` | Structural and content policy | `uv run python tools/check_docs_quality.py` and `uv run python tools/check_docs_structure.py` | No findings |
| Whole change | Full validation sequence | `uv run python tools/run_validation_gates.py`, then `uv run pytest tests/ -n logical --cov=scripts -m "not integration and not production_paths_allowed and not repo_scan" -q` and `uv run diff-cover coverage.xml --compare-branch=master` | ruff, mypy, bandit, module-size, import-linter, and docs gates pass; diff coverage at or above 90% |

## Risks
- **Risk**: Stricter validation rejects inputs accepted today, so existing clients may break → **Mitigation**: list the newly rejected inputs in the change record (extra request fields, blank fields, out-of-range `limit` and `run_id`, wildcard and oversized allowlist entries, `max_log_size_kb` out of range) and keep deny-all behavior unchanged.
- **Risk**: Fail-closed startup changes the behavior of a tokenless deployment that currently binds successfully → **Mitigation**: the change is the Issue's stated intent; the gate already refuses bind on an unvalidated posture, so only the new credential check is added, and the documentation records the new rule.
- **Risk**: A network probe in the pre-bind stage would break `validate_cicd_security()`'s documented pure-function contract and the synchronous stage shape → **Mitigation**: keep the pre-bind stage config-only and run the probe in the lifespan after bind.
- **Risk**: Pinned test inventories break when a check id or schema shape changes → **Mitigation**: `tests/mcp_servers/cicd/test_cicd_security_validation.py` and `tests/mcp_servers/cicd/test_cicd_models.py` are target rows updated in the same phases as the behavior change.
- **Risk**: `tests/mcp_servers/cicd/test_cicd_health_posture.py` still documents the empty-token accept-all path that `require_auth_token()` removed → **Mitigation**: correct the docstring in the same row; the archived mcpstart003 issue confirms the current rule.
- **Risk**: Canonicalization changes allowlist matching semantics for entries that differ only by case or separators → **Mitigation**: canonicalize at config load and at call time through the same function, and add duplicate and case cases to the tests.
- **Risk**: The hard maximum values are Plan decisions with no repository convention, so a later change may contradict them → **Mitigation**: record them as module constants in `scripts/mcp_servers/cicd/cicd_models.py` and state them in `config/cicd_mcp_server.toml` and the MCP docs.
- **Risk**: `CicdConfig` has the widest blast radius in the area (11 direct consumers, 25 test references) → **Mitigation**: run the `rules/toolchain.md` impact-radius check before changing its validation, and keep the validation change inside one phase with its own tests.
- **Risk**: High bus factor — every target file is single-author → **Mitigation**: keep each phase independently revertable and covered by its own tests.
- **Risk**: The dedup-store lock check could not be run because `fuser` is not installed → **Mitigation**: re-check on the deployment host before the restart in Phase 11.
- **Risk**: Overlap with open sibling issues on `cicd_server.py` (mcpci004 error and audit mapping) → **Mitigation**: this Plan touches only the health, lifespan, and gate paths; recorded as a compatible overlap in Assumptions.

## Execution Status

Table structure, status/type vocabulary, and general guidance: see
`templates/execution-status.md`.

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Credential contract module and its tests | In Progress | — | — | — |
| 2 | Strict request models, canonicalization, and configuration bounds | In Progress | — | — | — |
| 3 | Published schemas generated from the strict models | In Progress | — | — | — |
| 4 | Guard canonicalization, wildcard and oversized rejection, credential posture check | In Progress | — | — | — |
| 5 | Canonical identifier at call time and URL path encoding | In Progress | — | — | — |
| 6 | Lifespan-owned shared HTTP client | In Progress | — | — | — |
| 7 | Read-permission probe and health parity | In Progress | — | — | — |
| 8 | Health endpoint characterization update | In Progress | — | — | — |
| 9 | Configuration record | In Progress | — | — | — |
| 10 | Documentation updates | In Progress | — | — | — |
| 11 | Deployment and verification hand-off | Pending | — | — | — |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| — | — | — | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| `implementations/20261127-145310_01_scripts_mcp_servers_cicd_cicd_credential.py.md` | 1 | Procedure | Pending | — | — |
| `implementations/20261127-145310_02_scripts_mcp_servers_cicd_cicd_models.py.md` | 2 | Procedure | Pending | — | — |
| `implementations/20261127-145310_03_scripts_mcp_servers_cicd_cicd_tools.py.md` | 3 | Procedure | Pending | — | — |
| `implementations/20261127-145310_04_scripts_mcp_servers_cicd_cicd_service_guards.py.md` | 4 | Procedure | Pending | — | — |
| `implementations/20261127-145310_05_scripts_mcp_servers_cicd_cicd_service_init.py.md` | 6 | Procedure | Pending | — | — |
| `implementations/20261127-145310_06_scripts_mcp_servers_cicd_cicd_server.py.md` | 6, 7 | Procedure | Pending | — | — |
| `implementations/20261127-145310_07_scripts_mcp_servers_cicd_cicd_service_business.py.md` | 5 | Procedure | Pending | — | — |
| `implementations/20261127-145310_08_scripts_mcp_servers_cicd_cicd_service_github_actions.py.md` | 5 | Procedure | Pending | — | — |
| `implementations/20261127-145310_09_config_cicd_mcp_server.toml.md` | 9 | Procedure | Pending | — | — |
| `implementations/20261127-145310_10_tests_mcp_servers_cicd_test_cicd_models.py.md` | 2, 3 | Procedure | Pending | — | — |
| `implementations/20261127-145310_18_docs_22_mcp_mcp_04_03_rag-pipeline-and-cicd.md.md` | 10 | Procedure | Pending | — | — |
| `implementations/20261127-145310_19_docs_22_mcp_mcp_05_01_access-control-and-allowlists.md.md` | 10 | Procedure | Pending | — | — |

## Traceability
- **Workflow phase**: issue-to-plan
- **Source issue**: issues/20261119-141106_mcpci001_cicd-credential-config-contract.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: this document is the generated plan
- **Source implementation procedure**: N/A: not applicable in this phase
- **Generated at**: 20261126-152931
- **Evidence revision**: 431d80ee328ed91f26c43f27638d21a5b6375d3c
- **Related target files**: `scripts/mcp_servers/cicd/cicd_credential.py`, `scripts/mcp_servers/cicd/cicd_models.py`, `scripts/mcp_servers/cicd/cicd_tools.py`, `scripts/mcp_servers/cicd/cicd_service_guards.py`, `scripts/mcp_servers/cicd/cicd_service_init.py`, `scripts/mcp_servers/cicd/cicd_server.py`, `scripts/mcp_servers/cicd/cicd_service_business.py`, `scripts/mcp_servers/cicd/cicd_service_github_actions.py`, `config/cicd_mcp_server.toml`, `tests/mcp_servers/cicd/test_cicd_models.py`, `tests/mcp_servers/cicd/test_cicd_security_validation.py`, `tests/mcp_servers/cicd/test_cicd_health_posture.py`, `tests/mcp_servers/cicd/test_mcp_server_health_status.py`, `tests/mcp_servers/cicd/test_cicd_server_endpoints.py`, `tests/mcp_servers/cicd/test_cicd_credential.py`, `tests/mcp_servers/cicd/test_cicd_lifecycle.py`, `tests/mcp_servers/cicd/test_cicd_mcp_service.py`, `docs/22_mcp/mcp_04_03_rag-pipeline-and-cicd.md`, `docs/22_mcp/mcp_05_01_access-control-and-allowlists.md`

### Requirement Traceability
See `templates/requirement-traceability.md` for the canonical column format.

| Requirement ID | Source Issue section or evidence | Target file | Implementation step | Acceptance criterion | Test or validation item | Status |
|---|---|---|---|---|---|---|
| REQ-001 | Required Changes; `cicd_service_init.py:26` and `cicd_server.py:200` disagree | `scripts/mcp_servers/cicd/cicd_credential.py` | Phase 1 | AC-1 | `tests/mcp_servers/cicd/test_cicd_credential.py` credential matrix | Confirmed by repository evidence |
| REQ-001 | Required Changes | `scripts/mcp_servers/cicd/cicd_service_init.py` | Phase 6 | AC-1 | `tests/mcp_servers/cicd/test_cicd_lifecycle.py` | Confirmed by repository evidence |
| REQ-001 | Required Changes; health reads only the environment variable | `scripts/mcp_servers/cicd/cicd_server.py` | Phase 7 | AC-1 | `tests/mcp_servers/cicd/test_cicd_health_posture.py` | Confirmed by repository evidence |
| REQ-001 | Required Changes | `config/cicd_mcp_server.toml` | Phase 9 | AC-1 | `tests/mcp_servers/cicd/test_cicd_models.py` config parsing | Confirmed by repository evidence |
| REQ-002 | Acceptance Criteria; `_enforce_posture_gate()` refuses bind | `scripts/mcp_servers/cicd/cicd_service_guards.py` | Phase 4 | AC-2 | `tests/mcp_servers/cicd/test_cicd_security_validation.py` | Confirmed by repository evidence |
| REQ-002 | Implementation Intent | `scripts/mcp_servers/cicd/cicd_server.py` | Phase 7 | AC-2 | `tests/mcp_servers/cicd/test_mcp_server_health_status.py` | Confirmed by repository evidence |
| REQ-003 | Required Changes; `validate_cicd_security()` reports an awaitable probe as `not_applicable` | `scripts/mcp_servers/cicd/cicd_service_guards.py` | Phase 4 | AC-7 | `tests/mcp_servers/cicd/test_cicd_security_validation.py` | Derived from confirmed evidence |
| REQ-003 | Required Changes; user decision 20261126 (read permission only) | `scripts/mcp_servers/cicd/cicd_server.py` | Phase 7 | AC-7 | `tests/mcp_servers/cicd/test_cicd_credential.py` probe cases | Derived from confirmed evidence |
| REQ-004 | Required Changes; `cicd_tools.py` publishes hand-written schemas | `scripts/mcp_servers/cicd/cicd_tools.py` | Phase 3 | AC-3 | `tests/mcp_servers/cicd/test_tool_server_layer_consistency.py` | Confirmed by repository evidence |
| REQ-004 | Required Changes; request models have no `extra="forbid"` | `scripts/mcp_servers/cicd/cicd_models.py` | Phase 2 | AC-3 | `tests/mcp_servers/cicd/test_cicd_models.py` | Confirmed by repository evidence |
| REQ-005 | Required Changes; `cicd_service_github_actions.py:111` interpolates the raw value | `scripts/mcp_servers/cicd/cicd_models.py` | Phase 2 | AC-4 | `tests/mcp_servers/cicd/test_cicd_models.py` | Confirmed by repository evidence |
| REQ-005 | Required Changes | `scripts/mcp_servers/cicd/cicd_service_guards.py` | Phase 4 | AC-4 | `tests/mcp_servers/cicd/test_cicd_security_validation.py` | Confirmed by repository evidence |
| REQ-005 | Required Changes | `scripts/mcp_servers/cicd/cicd_service_business.py` | Phase 5 | AC-4 | `tests/mcp_servers/cicd/test_cicd_mcp_service.py` | Confirmed by repository evidence |
| REQ-005 | Required Changes | `scripts/mcp_servers/cicd/cicd_service_github_actions.py` | Phase 5 | AC-4 | `tests/mcp_servers/cicd/test_service_github_actions_error_edges.py` | Confirmed by repository evidence |
| REQ-006 | Required Changes; allowlists validated only as lists | `scripts/mcp_servers/cicd/cicd_models.py` | Phase 2 | AC-5 | `tests/mcp_servers/cicd/test_cicd_models.py` | Confirmed by repository evidence |
| REQ-006 | Required Changes | `scripts/mcp_servers/cicd/cicd_service_guards.py` | Phase 4 | AC-5 | `tests/mcp_servers/cicd/test_cicd_security_validation.py` | Confirmed by repository evidence |
| REQ-007 | Required Changes; `max_log_size_kb` parsed with `get_typed` and no bound | `scripts/mcp_servers/cicd/cicd_models.py` | Phase 2 | AC-5 | `tests/mcp_servers/cicd/test_cicd_models.py` | Confirmed by repository evidence |
| REQ-007 | Required Changes | `config/cicd_mcp_server.toml` | Phase 9 | AC-5 | `uv run python tools/check_docs_consistency.py --domain mcp` | Confirmed by repository evidence |
| REQ-008 | Required Changes; client created inside `build_service()` | `scripts/mcp_servers/cicd/cicd_service_init.py` | Phase 6 | AC-6 | `tests/mcp_servers/cicd/test_cicd_lifecycle.py` | Confirmed by repository evidence |
| REQ-008 | Required Changes; no lifespan in `cicd_server.py` | `scripts/mcp_servers/cicd/cicd_server.py` | Phase 6 | AC-6 | `tests/mcp_servers/cicd/test_cicd_lifecycle.py` | Confirmed by repository evidence |
| REQ-009 | Acceptance Criteria | `scripts/mcp_servers/cicd/cicd_service_guards.py` | Phase 4 | AC-5 | `tests/mcp_servers/cicd/test_cicd_security_validation.py` | Confirmed by repository evidence |
| REQ-010 | Documentation Impact | `docs/22_mcp/mcp_04_03_rag-pipeline-and-cicd.md` | Phase 10 | AC-8 | `uv run python tools/check_docs_structure.py` | Confirmed by repository evidence |
| REQ-010 | Documentation Impact | `docs/22_mcp/mcp_05_01_access-control-and-allowlists.md` | Phase 10 | AC-8 | `uv run python tools/check_docs_structure.py` | Confirmed by repository evidence |