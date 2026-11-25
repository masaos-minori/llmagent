## Goal
- Prove the GitHub MCP security contract at the HTTP boundary: authorization, Pydantic validation, schema publication, and deduplication verified through the real FastAPI application with only the GitHub API client mocked, plus the reusable HTTP-level test fixture and the characterization-versus-contract convention the sibling MCP issues reuse.

## Priority
Medium

## Scope
- **In-Scope**: new HTTP-level test files `tests/mcp_servers/github/test_github_tool_schema.py` and `tests/mcp_servers/github/test_github_security_compliance.py`; the reusable HTTP fixture in `tests/mcp_servers/conftest.py` (real server boundary, mocked upstream client, authentication headers, `/v1/tools` schema assertions); the characterization-versus-security-contract convention as the `security_contract` pytest marker registered in `pyproject.toml`; authenticated and unauthenticated endpoint access; same-key concurrent write executing once through the injected dedup store.
- **Out-of-Scope**: implementing the behavior under test (tests only; a test that exposes a missing behavior is reported against the owning issue); the CI/CD, Web Search, and MDQ test files that reuse this fixture (their own issues); existing characterization tests, which are not weakened.
- **Dependencies**: mcpai001, mcpai002, mcpai003, mcpai005, mcpai006 are all closed — their Plans are archived with only deploy-hand-off rows Pending, which is the user's decision; the behaviors under test are implemented (confirmed in Step 2), so no ordering dependency remains. Blocks mcpai012 and mcpai013 per the Issue.

## Background
Source: consolidated review backlog (`memo-issue.md`, Issue 10). Step 2 verification against current source: the listed existing tests under `tests/mcp_servers/github/` are present, and the review's two new files do not exist. The `Needs confirmation` claim that endpoint tests use a fake handler is confirmed in part — `tests/mcp_servers/github/test_github_server_endpoints.py` has a `fake_service` fixture (line 108) that bypasses request-model validation, but the same file also has `real_service` (line 244), the real service boundary with only the GitHub layer stubbed; the new fixture generalizes `real_service` at the shared conftest level. The behaviors under test are already implemented: allowlist boundary (`scripts/mcp_servers/github/github_service_security.py:307`), search scoping (`:271-273`), oversized refusal (`:456`), binary refusal via UTF-8 decode failure (`github_service_file.py:57-60`), strict request models (`github_models_file.py:18`, `request_contract.py`), schemas generated from models (`tools_file.py:69`), `dedup_state` in responses (`dispatch.py:236`), and the injection-only dedup store (`conftest.py:111` `isolated_dedup`). The Issue's `Unresolved Question` — how the same-key concurrent test reaches the real dedup store — resolves to the existing `isolated_dedup` fixture, which the new HTTP fixture composes. The conditional documentation row resolves to N/A: the repository has no testing documentation (`Needs confirmation` checked in Step 2).

## Problem
Characterization tests built on a fake service can pass while runtime authorization and validation are absent, so they do not prove the security contract. The current HTTP tests mix a validation-bypassing fake handler with the real boundary, and there is no shared convention or fixture that separates characterization tests from authoritative security-contract tests for the MCP servers.

## Reason for Change
It is the integration gate for the GitHub and MCP changes and prevents future refactoring from bypassing guards.

## Implementation Intent
Keep characterization tests and security-contract tests clearly separated; run the latter through the deployed HTTP contract against the real service with mocked external API calls, on a fixture and convention the CI/CD, Web Search, and MDQ issues reuse instead of building their own.

## Design decisions (Path B)
- **Convention**: the `security_contract` pytest marker registered in `pyproject.toml`'s `markers` list defines the separation (plan default, 20261126; the Issue allows marker or directory). Characterization tests stay unmarked; security-contract tests carry the marker. Alternative considered: directory separation — rejected because the existing `tests/mcp_servers/github/` layout keeps both kinds per server directory and the sibling issues reuse files in the same directories.
- **Fixture**: a shared fixture in `tests/mcp_servers/conftest.py` that composes the real FastAPI app, the real service boundary with the upstream GitHub client mocked, `MCP_TEST_AUTH_HEADERS`, and the `isolated_dedup` store injection; the per-server files consume it and supply their own upstream mock. `test_github_server_endpoints.py`'s local `real_service` is the pattern the fixture generalizes; that file is not modified.
- **Test placement**: `test_github_tool_schema.py` asserts `/v1/tools` schema publication (generated strict schemas, `dry_run`); `test_github_security_compliance.py` asserts runtime enforcement at `/v1/call_tool` (allowlist, search scoping, denied/oversized/binary reads, unknown-argument rejection, `dedup_state`, same-key concurrency, authenticated and unauthenticated access).
- **Tests only**: if a test exposes a missing behavior, report it against the owning issue; do not fix the behavior here.

## Requirements
- `REQ-001`: HTTP-level tests run through the real GitHub FastAPI application with only the GitHub API client mocked, covering out-of-allowlist reads, constrained global search, denied, oversized, and binary file reads, unknown-argument rejection, `/v1/tools` schemas including `dry_run`, `dedup_state` in responses, and same-key concurrent write executing once.
- `REQ-002`: Authenticated and unauthenticated endpoint access are covered.
- `REQ-003`: A reusable HTTP-level MCP test fixture (real server boundary, mocked upstream client, authentication headers, `/v1/tools` schema assertions) is provided in `tests/mcp_servers/conftest.py`.
- `REQ-004`: The characterization-versus-authoritative-contract convention is defined as the `security_contract` marker registered in `pyproject.toml`; existing characterization tests are not weakened.
- `REQ-005`: A test that exposes a missing behavior is reported against the owning issue, not fixed here.

## Implementation Target Files
**Freeze status**: Frozen — `issue-to-plan` Step 8's Implementation Target Files
Validation passed for every row on 20261126; see `rules/workflow-lifecycle.md`
Implementation Target Files Validation (Plan Freeze).

This table is the canonical, frozen source of implementation scope for this Plan. Once
`Frozen`, `Implementation steps`, `Acceptance criteria`, and every downstream
`plan-to-implementation-procedure` document MUST reference file paths only from this table — no other file may be treated as a modification target.

| File Path | Change Responsibility | Reason for Modification | Related Requirement / Acceptance Criterion | Repository Evidence | Related Tests | Validation Status |
|---|---|---|---|---|---|---|
| `tests/mcp_servers/conftest.py` | Modify | Add the reusable HTTP-level MCP fixture (real app boundary, mocked upstream client, auth headers, schema-assertion helpers) composing the existing `isolated_dedup` fixture | REQ-003, AC-5 | `isolated_dedup` fixture at line 111 already injects the dedup store through the dispatch seam; no HTTP fixture exists in this file (checked in Step 2) | `uv run python tools/check_conftest_integrity.py` | Verified |
| `pyproject.toml` | Modify | Register the `security_contract` marker in the pytest `markers` list | REQ-004, AC-5 | `markers` list at lines 145-148 currently has `integration` and `repo_scan` only (checked in Step 2) | `uv run python tools/check_conftest_integrity.py` | Verified |
| `tests/mcp_servers/github/test_github_tool_schema.py` | Create | New file: `/v1/tools` schema-publication contract tests — generated strict schemas, `dry_run` present, marked `security_contract` | REQ-001, AC-3 | New file; schemas are generated from models at `scripts/mcp_servers/github/tools_file.py:69` (checked in Step 2) | itself | Verified |
| `tests/mcp_servers/github/test_github_security_compliance.py` | Create | New file: runtime-enforcement contract tests at `/v1/call_tool` — out-of-allowlist reads, constrained global search, denied/oversized/binary file reads, unknown-argument rejection, `dedup_state`, same-key concurrent write executing once, authenticated and unauthenticated access, marked `security_contract` | REQ-001, REQ-002, AC-1, AC-2, AC-4 | New file; the behaviors under test are implemented (Step 2 evidence in Background) | itself | Verified |

## Reference Files
Files that must be read to implement the targets above, but MUST NOT be modified. Same
one-file-per-row discipline as `Implementation Target Files` above — no directories, glob
patterns, components, file groups, or vague phrases.

| File Path | Why It Must Be Read | Related Target File or Requirement |
|---|---|---|
| `tests/mcp_servers/github/test_github_server_endpoints.py` | The characterization baseline and the `real_service` pattern the shared fixture generalizes; must keep passing unweakened | REQ-004 |
| `tests/mcp_servers/_auth_headers.py` | The shared authentication headers the fixture uses | REQ-003 |
| `scripts/mcp_servers/github/github_server.py` | The real FastAPI application the HTTP tests drive (`/v1/tools`, `/v1/call_tool`, `/health`) | REQ-001 |
| `scripts/mcp_servers/dispatch.py` | The dedup decision path the same-key concurrency test observes (`dedup_state`, line 236) | REQ-001 |
| `scripts/mcp_servers/github/github_service_security.py` | The authorization boundary the compliance tests assert (allowlist line 307, search scoping lines 271-273) | REQ-001 |

## Acceptance Criteria
- AC-1: HTTP tests reject out-of-allowlist reads and constrain global search (REQ-001).
- AC-2: HTTP tests reject denied, oversized, and binary file reads and unknown arguments (REQ-001).
- AC-3: `/v1/tools` exposes the generated strict schemas, including `dry_run` (REQ-001).
- AC-4: `dedup_state` is preserved in responses; a same-key concurrent write executes once (REQ-001).
- AC-5: Characterization and security-contract tests are clearly separated by the `security_contract` marker, and the shared fixture is reusable by the sibling MCP issues (REQ-003, REQ-004).

## Tests
- The new test files are the deliverable (REQ-001, REQ-002); run ruff, mypy, the full suite, and check the diff-cover threshold per `rules/toolchain.md`.
- `uv run python tools/check_conftest_integrity.py` after the conftest change (`rules/tool-gates.md`).
- Run the new tests by marker: `uv run pytest tests/mcp_servers/github/test_github_tool_schema.py tests/mcp_servers/github/test_github_security_compliance.py -v`; the existing GitHub suite and `tests/mcp_servers/test_mcp_dispatch_concurrency.py` must keep passing.

## Documentation Impact
N/A: the repository has no testing documentation, so the Issue's conditional test-layout note does not apply (checked in Step 2). No `docs/` file is a modification target.

## Assumptions
- The `security_contract` marker is the plan-proposed convention default (20261126); the Issue permits marker or directory, and the user can override it before implementation.
- The behaviors under test are already implemented (Step 2), so the new tests are expected to pass; a failure is a behavior gap reported against the owning issue per REQ-005, not fixed here.
- The fixture composes the existing `isolated_dedup` fixture rather than adding a new dedup mechanism; the Issue's `Unresolved Question` is resolved by this existing seam.

## Unknowns
| ID | Unknown Description | Evidence Missing | Resolution Path | Blocking? (True/False) |
|---|---|---|---|---|
| — | N/A: the Issue's `Unresolved Question` (dedup-store access from the HTTP fixture) resolves to the existing `isolated_dedup` fixture; the conditional documentation row resolves to N/A | — | — | — |

## Affected areas
`skills/DESIGN.md` Change-impact table, extended with `Churn (30d)` and `Bus Factor`
columns. The `File` column here MUST be a subset of `Implementation Target Files`'
rows — this table analyzes change-impact risk for those same files; it is not a
separate scope-of-record.

| File | Change | Blast Radius | Churn (30d) | Bus Factor | deploy.sh Impact |
|---|---|---|---|---|---|
| `tests/mcp_servers/conftest.py` | Modify | Medium (fixture consumed by all MCP server tests; the sibling issues reuse it) | 4 | High (single author) | not applicable (tests not deployed) |
| `pyproject.toml` | Modify | Medium (pytest configuration for the whole suite) | 6 | High (single author) | not applicable |
| `tests/mcp_servers/github/test_github_tool_schema.py` | Create | Low | N/A (new file) | High (single author) | not applicable (tests not deployed) |
| `tests/mcp_servers/github/test_github_security_compliance.py` | Create | Low | N/A (new file) | High (single author) | not applicable (tests not deployed) |

## Design
- **Real boundary, mocked upstream**: the fixture keeps the FastAPI app, the service, the validation, and the dedup gate real; only the GitHub API client is mocked, so a request that fails authorization or validation is detectable as a refusal rather than a stubbed response (REQ-001).
- **Convention as marker**: `security_contract` marks authoritative tests; characterization tests remain unmarked, so fast runs and CI selection stay unchanged (`pyproject.toml` markers list, `tests/conftest.py` registration pattern at line 301 is the precedent for marker registration).
- **Predictable fallout**: the consumer scan for `conftest` (run in Step 3) returned only `tools/check_conftest_integrity.py` as candidates — the gate itself; no test imports the fixture yet because it is new, and the sibling issues' files are not targets of this Plan. No module crosses the 24576 B module-size gate at current size (largest target: `pyproject.toml` 6218 B). No tool is added or removed, so `tools/TOOL_DESCRIPTIONS.md` is not affected. No generated-reference domain is touched. No pinned counts change: the marker addition is additive to the `markers` list.
- **Validation quality baseline**: the new tests must reach the `rules/toolchain.md` diff-cover threshold of 90% on changed lines; ruff and the conftest-integrity gate apply per `rules/tool-gates.md`.

## Implementation steps
Each step description MUST cite the exact file path(s) it touches by referencing rows
of `Implementation Target Files` above — do not restate file-level detail
independently of that frozen table.

1. **Phase 1: Convention and shared fixture**
   - [ ] Register the `security_contract` marker in `pyproject.toml` (REQ-004, AC-5; `pyproject.toml`)
   - [ ] Add the reusable HTTP-level fixture to `tests/mcp_servers/conftest.py` composing the real app boundary, mocked upstream client, auth headers, and `isolated_dedup` (REQ-003, AC-5; `tests/mcp_servers/conftest.py`)
2. **Phase 2: Schema-publication contract tests**
   - [ ] Write `test_github_tool_schema.py`: `/v1/tools` generated strict schemas including `dry_run`, marked `security_contract` (REQ-001, AC-3; `tests/mcp_servers/github/test_github_tool_schema.py`)
3. **Phase 3: Runtime-enforcement contract tests**
   - [ ] Write `test_github_security_compliance.py`: out-of-allowlist reads, constrained global search, denied/oversized/binary file reads, unknown-argument rejection, `dedup_state`, same-key concurrent write executing once, authenticated and unauthenticated access, marked `security_contract` (REQ-001, REQ-002, AC-1, AC-2, AC-4; `tests/mcp_servers/github/test_github_security_compliance.py`)
4. **Phase 4: Validation and reporting**
   - [ ] Run the new tests, the existing GitHub suite, `tests/mcp_servers/test_mcp_dispatch_concurrency.py`, `check_conftest_integrity.py`, ruff, mypy, the full suite, and diff-cover (REQ-001..REQ-004)
   - [ ] Report any behavior gap a test exposes against its owning issue; do not fix it here (REQ-005)

### Release units
N/A: no release unit — each phase can be validated alone.

## Validation plan
| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| `tests/mcp_servers/github/test_github_tool_schema.py` | Integration at the HTTP boundary (TestClient on the real app, mocked GitHub client) | `uv run pytest tests/mcp_servers/github/test_github_tool_schema.py -v` | Generated strict schemas published, `dry_run` present |
| `tests/mcp_servers/github/test_github_security_compliance.py` | Integration at the HTTP boundary with the injected dedup store | `uv run pytest tests/mcp_servers/github/test_github_security_compliance.py -v` | Authorization, validation, dedup, and auth coverage pass; same-key concurrent write executes once |
| `tests/mcp_servers/conftest.py` | Gate | `uv run python tools/check_conftest_integrity.py` | Required autouse fixtures intact |
| `pyproject.toml` | Marker registration | `uv run pytest tests/mcp_servers/github/ -m security_contract -v` | Marker selects the contract tests |
| Changed lines | Coverage | `uv run diff-cover coverage.xml --compare-branch=master` | ≥ 90% on changed lines |

## Risks
- **Risk**: a contract test exposes a behavior gap owned by a dependency issue → **Mitigation**: report against the owning issue per REQ-005; the Step 2 baseline shows the behaviors are implemented, so gaps are unexpected.
- **Risk**: the shared fixture changes behavior for existing MCP tests → **Mitigation**: the fixture is additive (new fixture, new marker); existing characterization tests are not modified, and the conftest-integrity gate is a target-row validation.
- **Risk**: the same-key concurrency test depends on the dedup store injection seam → **Mitigation**: it composes the existing `isolated_dedup` fixture, already used by `tests/mcp_servers/test_mcp_dispatch_concurrency.py`.
- **Risk**: `Bus Factor` is high for every target (single author) → **Mitigation**: keep each phase independently revertable.

## Execution Status

Table structure, status/type vocabulary, and general guidance: see
`templates/execution-status.md`.

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Convention and shared fixture | Pending | — | — | — |
| 2 | Schema-publication contract tests | Pending | — | — | — |
| 3 | Runtime-enforcement contract tests | Pending | — | — | — |
| 4 | Validation and reporting | Pending | — | — | — |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| — | N/A: no blocker recorded at Plan creation | N/A: no blocker recorded | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| — | — | — | — | — | — |

## Traceability
- **Workflow phase**: issue-to-plan
- **Source issue**: issues/20261119-140517_mcpai010_github-http-contract-tests.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: this document is the generated plan
- **Source implementation procedure**: N/A: not applicable in this phase
- **Generated at**: 20261126-070112
- **Related target files**: `tests/mcp_servers/conftest.py`, `pyproject.toml`, `tests/mcp_servers/github/test_github_tool_schema.py`, `tests/mcp_servers/github/test_github_security_compliance.py`

### Requirement Traceability
See `templates/requirement-traceability.md` for the canonical column format.

| Requirement ID | Source Issue section or evidence | Target file | Implementation step | Acceptance criterion | Test or validation item | Status |
|---|---|---|---|---|---|---|
| REQ-001 | Required Changes; Step 2 implementation evidence (`github_service_security.py:271-273,307,456`, `github_service_file.py:57-60`, `tools_file.py:69`, `dispatch.py:236`) | `tests/mcp_servers/github/test_github_tool_schema.py`, `tests/mcp_servers/github/test_github_security_compliance.py` | Phase 2, Phase 3 | AC-1, AC-2, AC-3, AC-4 | the new test files themselves | Confirmed by repository evidence |
| REQ-002 | Required Changes | `tests/mcp_servers/github/test_github_security_compliance.py` | Phase 3 | AC-2 | itself | Confirmed by repository evidence |
| REQ-003 | Required Changes; `conftest.py:111` `isolated_dedup` | `tests/mcp_servers/conftest.py` | Phase 1 | AC-5 | `check_conftest_integrity.py` | Confirmed by repository evidence |
| REQ-004 | Required Changes; `pyproject.toml:145-148` markers | `pyproject.toml` | Phase 1 | AC-5 | `uv run pytest -m security_contract` | Confirmed by repository evidence |
| REQ-005 | AI Implementation Instruction | — (reporting rule, no file) | Phase 4 | — | report against owning issue | Confirmed by issue text |
