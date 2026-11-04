## Goal
- Make the `mcp_auth` step of `StartupValidationPipeline.check_services` consistent with the configuration contract and with the other startup steps: a disabled MCP server (`startup_mode` none) with an empty `auth_token` no longer aborts startup, while an enabled server with an empty token stays a fatal outcome.

## Priority
High

## Scope
- **In-Scope**:
  - Exclude disabled servers from the `missing_auth` computation of the "MCP authentication check"; keep the `mcp_auth` source name, the message shape, and the remediation wording shape.
  - Add tests for the disabled/empty-token, enabled/empty-token, and enabled-offenders-only-message cases.
  - Adjust the existing `MagicMock`-based `mcp_auth` tests that the filter would otherwise break, and correct the comment that says an empty-token config cannot be constructed.
  - Correct the documentation statements that call the check unreachable or applicable to every configured server.
- **Out-of-Scope**:
  - Whether the `mcp_auth` check should exist at all for enabled servers.
  - Changes to config-layer validation in `scripts/shared/mcp_config.py` and to token resolution from environment references.
  - Any other startup validation step, including `_check_component_mandatoriness` handling of disabled servers (tracked as UNK-01).
- **Dependencies**: Related to the separate issue about configuration-only validation running after MCP subprocess spawn (id validorder001), which may move the `mcp_auth` check into an earlier stage. Both touch `check_services`; this Plan is applied first and the other change is rebased on it. Sequencing only, no `Depends on` line.

## Background
`McpServerConfig._validate_auth_token` requires a non-empty token only when the server is not disabled, with the comment that disabled servers do not require unused connection credentials (REQ-004 of an earlier plan). `_build_single_server` defaults `startup_mode` to none and resolves the token from an environment reference, so an unset variable yields an empty token. `mcp_health`, `McpToolDiscoveryService`, `tool_validation`, and `mcp_status` already skip or distinguish disabled servers through `is_disabled`.

## Problem
`check_services` builds `missing_auth` from every server with a bare `not srv.auth_token` test and records `add_fatal("mcp_auth", ...)`, after which `StartupOrchestrator._check_services` raises. One disabled server with an unset token variable aborts the whole agent startup, and the remediation text asks for a credential the configuration layer says is not needed (checked in Step 2).

Verification corrections to the Issue: (a) `McpServerConfig(` has exactly one production construction site, `_build_single_server` in `scripts/shared/mcp_config.py`, so an enabled server with an empty token cannot come from the normal config path; the check can fire only for disabled servers or for a programmatically assembled `ctx` (this answers the Issue's second unresolved question; whether to keep the check for enabled servers stays out of scope). (b) The `MagicMock` empty-token tests exist in two files, not one: `tests/agent/test_startup_severity_classification.py` and the duplicate block in `tests/agent/test_startup.py`; both need `is_disabled=False`. (c) The documentation is wrong in two places: the startup and health document calls the check unreachable through a real `McpServerConfig`, and the MCP authentication document says startup records a fatal for any entry with an empty token.

## Reason for Change
A server the operator has switched off or has not configured yet blocks startup of the whole agent, contradicting the configuration contract and every other pipeline step.

## Implementation Intent
Filter on `is_disabled` in the `missing_auth` comprehension and leave everything else in the step unchanged, so enabled servers remain fail-closed (ADR-004 Decision 14: safety failures stay unconditional).

## Requirements
- `REQ-001`: A configuration whose only token-less server is disabled MUST pass the `mcp_auth` step (`add_ok("mcp_auth")`), without a fatal.
- `REQ-002`: An enabled server with an empty `auth_token` MUST still produce a fatal `mcp_auth` outcome naming that server; the message MUST list only enabled offenders; the source name and remediation wording shape MUST NOT change.
- `REQ-003`: New tests for REQ-001 and REQ-002 MUST fail on the current code and pass after the change.
- `REQ-004`: Existing `MagicMock`-based `mcp_auth` tests MUST be adjusted (`is_disabled=False` on token-less servers) so they keep exercising the enabled-server path, and the comment claiming an empty-token config cannot be constructed MUST be corrected.
- `REQ-005`: Documentation MUST state that disabled servers are exempt from the `mcp_auth` check and MUST NOT call the check unreachable.

## Implementation Target Files
**Freeze status**: Frozen (Step 8 validation passed: every row `Verified` — exists, requires modification, supporting evidence, linked to a Plan requirement; no path appears in both tables; no directory, glob, or vague row).

This table is the canonical, frozen source of implementation scope for this Plan. Once `Frozen`, `Implementation steps`, `Acceptance criteria`, and every downstream `plan-to-implementation-procedure` document MUST reference file paths only from this table — no other file may be treated as a modification target.

| File Path | Change Responsibility | Reason for Modification | Related Requirement / Acceptance Criterion | Repository Evidence | Related Tests | Validation Status |
|---|---|---|---|---|---|---|
| `scripts/agent/startup_validation.py` | `mcp_auth` filter | Add `not srv.is_disabled` to the `missing_auth` comprehension in `StartupValidationPipeline.check_services` (checked in Step 2) | REQ-001, REQ-002; AC-1, AC-2 | `missing_auth = [key for key, srv in ctx.cfg.mcp.mcp_servers.items() if not srv.auth_token]` under "1b. MCP authentication check"; `McpServerConfig.is_disabled` is `startup_mode == StartupMode.NONE` (checked in Step 2) | `tests/agent/test_startup_validation.py`, `tests/agent/test_startup_severity_classification.py`, `tests/agent/test_startup.py` | Verified |
| `tests/agent/test_startup_validation.py` | New tests | Add the disabled/empty-token, enabled/empty-token, and enabled-offenders-only-message tests using the file's `check_services` harness (checked in Step 2) | REQ-003; AC-3 | File exists with `TestRagConsistencyTimeout` and a posture-gate test; no `mcp_auth` test (rg, checked in Step 2) | `tests/agent/test_startup_validation.py` | Verified |
| `tests/agent/test_startup_severity_classification.py` | Adjust existing tests and comment | Set `is_disabled=False` on the token-less `MagicMock` servers in the three `test_mcp_auth_*` tests; correct the "can no longer be constructed" comment (checked in Step 2) | REQ-004; AC-4 | `test_mcp_auth_fatal_when_any_server_missing_token` and `test_mcp_auth_fatal_lists_all_offending_servers` use `MagicMock(auth_token="")`, whose `is_disabled` is truthy (checked in Step 2) | `tests/agent/test_startup_severity_classification.py` | Verified |
| `tests/agent/test_startup.py` | Adjust duplicate tests and comment | Same adjustment for the duplicate `mcp_auth` test block (checked in Step 2) | REQ-004; AC-4 | Lines of the same three tests with `MagicMock(auth_token="")` (rg, checked in Step 2) | `tests/agent/test_startup.py` | Verified |
| `docs/23_agent/agent_10_01_operations-and-observability-startup-and-health.md` | `mcp_auth` description | Replace "unreachable via a real `McpServerConfig`" and "any entry has an empty `auth_token`" with the disabled-server exemption (checked in Step 2) | REQ-005; AC-5 | The `mcp_auth` bullet in the severity-mapping section states both (checked in Step 2) | N/A: documentation | Verified |
| `docs/22_mcp/mcp_05_02_auth-profiles-and-sandboxing.md` | Enforcement-point wording | The "Enforcement Point" paragraph says startup records a fatal for any `[mcp_servers.*]` entry with an empty token; limit it to enabled entries (checked in Step 2) | REQ-005; AC-5 | The paragraph names the fatal `mcp_auth` outcome; the Authentication section already states the disabled exemption (checked in Step 2) | N/A: documentation | Verified |

## Reference Files
Files that must be read to implement the targets above, but MUST NOT be modified.

| File Path | Why It Must Be Read | Related Target File or Requirement |
|---|---|---|
| `scripts/shared/mcp_config.py` | Defines `is_disabled`, `_validate_auth_token` (disabled exemption), and the single construction site `_build_single_server` | REQ-001, REQ-002 |
| `scripts/agent/services/mcp_health.py` | Readiness step skips disabled servers; the pattern to stay consistent with | REQ-001 |
| `scripts/agent/services/mcp_tool_discovery.py` | Tool discovery skips disabled servers | REQ-001 |
| `scripts/agent/production_config_validator.py` | `validate_against_registry` iterates every configured server including disabled ones (basis of UNK-01) | UNK-01 |
| `docs/22_mcp/mcp_06_01_configuration-file-inventory.md` | Already says an empty value is rejected unless the server is disabled; wording stays true | REQ-005 |
| `docs/10_adr/adr_02_01_004_platform-environment-failure-handling-policy.md` | Decision 14: safety failures stay unconditional, so the enabled-server check must not weaken | REQ-002 |

## Acceptance Criteria
- AC-1 (REQ-001): a configuration whose only token-less server is disabled yields an OK `mcp_auth` outcome and no fatal from that step.
- AC-2 (REQ-002): an enabled server with an empty token yields a fatal `mcp_auth` outcome whose message names that server and omits disabled servers.
- AC-3 (REQ-003): the new tests fail on the pre-change code and pass after it.
- AC-4 (REQ-004): the adjusted existing tests pass and still exercise the enabled-server path; the corrected comment no longer claims an empty-token config cannot be constructed.
- AC-5 (REQ-005): the two documents state the disabled-server exemption, and the docs checkers report no findings.

## Tests
- `REQ-003`: in `tests/agent/test_startup_validation.py`, run `check_services` with (a) a real disabled `McpServerConfig` with an empty token and no other offenders, (b) an enabled `MagicMock` server with `is_disabled=False` and an empty token, (c) a mix of one disabled and one enabled token-less server, asserting the message names only the enabled one.
- `REQ-004`: update the `MagicMock` servers in the two existing `mcp_auth` blocks; keep their assertions.
- Regression: `tests/agent/test_startup_validation.py`, `tests/agent/test_startup_severity_classification.py`, `tests/agent/test_startup.py`, `tests/agent/shared/test_startup_validation_pipeline.py`, `tests/agent/test_startup_rollback.py`, `tests/agent/test_startup_memory_failures.py`.
- No real token or environment value is copied into tests or messages.

## Documentation Impact
Yes. REQ-005 drives updates to the startup and health document and to the MCP authentication document (located through the scan and `docs/00_index.md` "Document References by Task"). Wording only.

## Assumptions
- The check is dead for enabled servers on the normal config path (single construction site), but it is kept and stays fail-closed, as the Issue requires (checked in Step 3).
- `MagicMock` servers in other tests that only set a non-empty `auth_token` stay OK under the filter whether or not `is_disabled` is truthy, so only token-less mocks need `is_disabled=False` (checked in Step 3).
- Overlap with other Frozen Plans is judged by `tools/check_plan_target_overlaps.py` in Step 8b.

## Unknowns
| ID | Unknown Description | Evidence Missing | Resolution Path | Blocking? (True/False) |
|---|---|---|---|---|
| UNK-01 | Whether a disabled server needs an exemption in `_check_component_mandatoriness`, which loops over every configured server and treats one absent from the registry as fatal. | Registry contents versus disabled servers in deployed configuration were not examined. | Separate follow-up issue if confirmed; not part of this Plan. | False |

## Affected areas
| File | Change | Blast Radius | Churn (30d) | Bus Factor | deploy.sh Impact |
|---|---|---|---|---|---|
| `scripts/agent/startup_validation.py` | Modify | Medium: every agent startup passes through `check_services` | 7 | N/A | not applicable (rsynced) |
| `tests/agent/test_startup_validation.py` | Modify | Low | N/A | N/A | not applicable (rsynced) |
| `tests/agent/test_startup_severity_classification.py` | Modify | Low | N/A | N/A | not applicable (rsynced) |
| `tests/agent/test_startup.py` | Modify | Low | N/A | N/A | not applicable (rsynced) |
| `docs/23_agent/agent_10_01_operations-and-observability-startup-and-health.md` | Modify | Low | N/A | N/A | not applicable (rsynced) |
| `docs/22_mcp/mcp_05_02_auth-profiles-and-sandboxing.md` | Modify | Low | N/A | N/A | not applicable (rsynced) |

## Design
Decision: filter in the comprehension (`not srv.is_disabled and not srv.auth_token`). Alternatives: a separate pre-pass, or removing the check. Rejected: the first adds a second code path for no gain, the second is out of scope. Compatibility: outcome source, message format, and remediation wording are unchanged, so reporting consumers need no change. The `MagicMock` truthiness of `is_disabled` is the only test-side compatibility cost (REQ-004).

No persisted schema, public API, or shared constant changes, so no consumer scan is required.

## Implementation steps
1. **Phase 1: Failing tests first**
   - [ ] Add the new `mcp_auth` tests and record that they fail on the current code (REQ-003; `tests/agent/test_startup_validation.py`).
2. **Phase 2: Filter**
   - [ ] Add the `is_disabled` filter (REQ-001, REQ-002; `scripts/agent/startup_validation.py`).
3. **Phase 3: Existing tests**
   - [ ] Set `is_disabled=False` on the token-less mocks and correct the comment (REQ-004; `tests/agent/test_startup_severity_classification.py`, `tests/agent/test_startup.py`).
4. **Phase 4: Documentation**
   - [ ] Update the two documents and run the docs checkers (REQ-005; `docs/23_agent/agent_10_01_operations-and-observability-startup-and-health.md`, `docs/22_mcp/mcp_05_02_auth-profiles-and-sandboxing.md`).
5. **Phase 5: Deployment & Verification**
   - [ ] Hand off to `skills/deploy/SKILL.md` for the `scripts/` change; prerequisite: the change is committed and pushed first, and deploying is the user's decision (approval gate). Run `uv run python tools/generate_reference_table.py --check` (REQ-001; `scripts/agent/startup_validation.py`).

### Release units
**Unit**: mcp-auth-filter | **Phases**: 2, 3 | **Reason**: the filter makes the existing token-less `MagicMock` tests pass for the wrong reason or fail until `is_disabled=False` is set on them.

## Validation plan
| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| `scripts/agent/startup_validation.py` | Unit | `uv run pytest tests/agent/test_startup_validation.py -v` | New tests fail before Phase 2, pass after |
| Existing `mcp_auth` tests | Unit | `uv run pytest tests/agent/test_startup_severity_classification.py tests/agent/test_startup.py tests/agent/shared/test_startup_validation_pipeline.py tests/agent/test_startup_rollback.py tests/agent/test_startup_memory_failures.py -v` | All pass |
| Touched Python files | Static | `uv run ruff format`, `uv run ruff check`, `uv run mypy --no-namespace-packages scripts/ tests/eventbus` | Clean, no new errors |
| `scripts/agent/` | Security / architecture | `uv run bandit -r scripts/ -c pyproject.toml -ll`, `PYTHONPATH=scripts uv run lint-imports`, `uv run python tools/check_module_size.py` | No new findings |
| Changed lines | Coverage | `uv run coverage run -m pytest tests/`, `uv run coverage xml`, `uv run diff-cover coverage.xml --compare-branch=master --fail-under=90` | At least 90 percent |
| Two documents | Docs checkers | `tools/check_docs_quality.py`, `tools/check_docs_structure.py`, `tools/check_docs_content_policy.py`, `tools/check_docs_consistency.py --domain agent`, `--domain mcp` | No findings |

Baseline (Step 5): `radon cc` on `startup_validation.py` reports `StartupValidationPipeline.check_services` at grade D (25) and the class at C (14), so the change MUST add no branch beyond the one filter condition; `vulture` and `bandit` show no finding in the target file; the diff-cover number is recorded at implementation time.

## Risks
- **Risk**: A token-less `MagicMock` server in a test not found by the search becomes silently exempt because `is_disabled` is truthy → **Mitigation**: the search lists only the three blocks above for `check_services`; Phase 3 runs the full startup test set, and any further case is reported through `tools/amend_plan.py`.
- **Risk**: The exemption is read as weakening a safety check → **Mitigation**: only disabled servers are exempt, enabled servers stay unconditional (ADR-004 Decision 14), and REQ-002 has its own test.
- **Risk**: Overlap in `check_services` with the validation-order change → **Mitigation**: this Plan is applied first; the other Plan is rebased on it.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Phase 1: add failing `mcp_auth` tests | Pending | — | — | |
| 2 | Phase 2: add the `is_disabled` filter | Pending | — | — | |
| 3 | Phase 3: adjust existing mocks and comment | Pending | — | — | |
| 4 | Phase 4: documentation updates | Pending | — | — | |
| 5 | Phase 5: deployment hand-off and verification | Pending | — | — | |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| — | — | — | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| — | — | — | — | — | — |

## Traceability
- **Workflow phase**: issue-to-plan
- **Source issue**: issues/20261031-135522_disabledauth001_disabled-server-auth-fatal.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: this document is the generated plan
- **Source implementation procedure**: N/A: not applicable in this phase
- **Generated at**: 20261104-095503
- **Related target files**: scripts/agent/startup_validation.py, tests/agent/test_startup_validation.py, tests/agent/test_startup_severity_classification.py, tests/agent/test_startup.py, docs/23_agent/agent_10_01_operations-and-observability-startup-and-health.md, docs/22_mcp/mcp_05_02_auth-profiles-and-sandboxing.md

### Requirement Traceability
| Requirement ID | Source Issue section or evidence | Target file | Implementation step | Acceptance criterion | Test or validation item | Status |
|---|---|---|---|---|---|---|
| REQ-001 | Required Changes bullet 1; `missing_auth` comprehension | scripts/agent/startup_validation.py | 2 | AC-1 | New disabled/empty-token test | Confirmed by repository evidence |
| REQ-002 | Constraints; Acceptance Criteria bullet 2 | scripts/agent/startup_validation.py | 2 | AC-2 | New enabled/empty-token and message tests | Explicit in issue |
| REQ-003 | Required Changes bullet 2; Acceptance Criteria bullet 3 | tests/agent/test_startup_validation.py | 1 | AC-3 | New tests, failing before Phase 2 | Explicit in issue |
| REQ-004 | Testing Expectations bullet 2; second duplicate test block | tests/agent/test_startup_severity_classification.py | 3 | AC-4 | `tests/agent/test_startup_severity_classification.py` | Explicit in issue |
| REQ-004 | Derived: duplicate `MagicMock` block found in Step 2 | tests/agent/test_startup.py | 3 | AC-4 | `tests/agent/test_startup.py` | Confirmed by repository evidence |
| REQ-005 | Documentation Impact; docs found in Step 2 | docs/23_agent/agent_10_01_operations-and-observability-startup-and-health.md | 4 | AC-5 | `tools/check_docs_*` | Confirmed by repository evidence |
| REQ-005 | Documentation Impact; docs found in Step 2 | docs/22_mcp/mcp_05_02_auth-profiles-and-sandboxing.md | 4 | AC-5 | `tools/check_docs_*` | Confirmed by repository evidence |
