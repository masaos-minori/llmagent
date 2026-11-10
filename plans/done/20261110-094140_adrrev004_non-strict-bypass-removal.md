## Goal
- Make strict behavior the only behavior: remove the `tool_definitions_strict` and `routing_drift_strict` toggles and their WARNING branches, make every empty safety setting (`allowed_tools`, `allowed_root`, `protected_branches`) deny or fail at load, remove `accept_all_for_tests` and the unused `MCPServer` helpers, and delete the single-valued `security_profile` key, with `path_denylist` empty recorded as an ADR-004 exception.

## Priority
High

## Scope
- **In-Scope**: Remove the two strict keys and non-strict branches (`startup_validation.py`, `mcp_tool_discovery.py`, builders, registry, validator, display, `config/agent.toml`); deny-all on an empty `allowed_tools` at runtime and a load error on an empty `allowed_root`, `protected_branches` (git and github); remove `accept_all_for_tests`, `list_tools()`, `list_tools_with_server_key()`, and the base `health()`; remove `security_profile` and `SecurityProfile`; derive the empty-token test's server list from `config/agent.toml`; register the `path_denylist` exception in ADR-004; update the tests and documents.
- **Out-of-Scope**: Server-side audit and the MCP authentication ADR (`issues/20261109-113023_adrrev011_mcp-audit-auth-adr.md`); posture-failure handling; the decision on server mandatoriness; renaming `mcp_06_09_startup-validation-behavior-tool_definitions_strict.md`; the Agent-side `startup_validation` rule that rejects an empty `auth_token` (unchanged).
- **Dependencies**: Depends on none. Blocks `issues/20261109-113023_adrrev011_mcp-audit-auth-adr.md`. Sequencing: `tests/agent/test_production_config_validator.py`, `scripts/agent/production_config_validator.py`, and `config/agent.toml` are also targets of `plans/20261110-091327_adrrev002_agent-eventbus-coupling.md` and `plans/20261110-092546_adrrev003_rag-http-delegation.md`; the edits are to different keys and compatible in any order.
  - **Depends on**: N/A: none

## Background
- Source: `memo-issue.md` items H-06, H-07, H-13, re-verified on 2026-11-10.
- Re-verified against the working tree at HEAD `cf8ff9ada` on 2026-11-10 (adversarial re-check of every frozen row): all 79 target-table paths exist; the cited line numbers below were re-read and are accurate except the two corrected below (`config/agent.toml` strict keys are at lines 47-48 in the current tree, `allowed_root` at line 218); the strict keys are referenced in 15 documents including all the document rows of this Plan; `security_profile` appears in no shipped config under `config/`; `accept_all_for_tests` is passed only from `tests/mcp_servers/test_mcp_server_base.py`, never from production code; ADR-004 has Decision Groups 1-10 (no Group 11) and its `## Exceptions` section currently holds only the MCP subprocess-spawn exception, so the `path_denylist` exception is not yet registered.
- `Confirmed by repository evidence` (strict toggles): `config/agent.toml:47,48` set both keys; the builder defaults and dataclass defaults are False (`config_section_builders.py:185-189`, `config_dataclasses.py:164,166`). Non-strict branches: `startup_validation.py:151-156` (drift check with `strict=` and `_record_drift_check_failure(..., strict=...)`) and `services/mcp_tool_discovery.py:16-30,157` (`_is_strict` picks FATAL or WARNING). The ADR-003 branch the memo names was not found separately in code; the ADR text is updated through the documents rows.
- `Confirmed by repository evidence` (bypass): `attach_auth_middleware(app, token, *, accept_all_for_tests=False)` in `scripts/mcp_servers/server.py:96-124` returns the flag for an empty token. No production call passes it; every server module routes its token through `require_auth_token()` (`tests/mcp_servers/test_require_auth_token.py::test_every_server_routes_through_shared_enforcement_point` globs the server sources). A parametrized per-server empty-token test already exists (`test_empty_token_prevents_every_server_from_importing`), but its server list is hard-coded (`_SERVERS`, 10 entries), which the Issue asks to replace with an enumeration from `config/agent.toml`.
- `Confirmed by repository evidence` (allowed_tools): `tool_policy.py:513` applies the allowlist only when it is non-empty (empty means allow all at runtime). `ProductionConfigValidator` already records `allowed_tools=[]` as an error (`production_config_validator.py:303`, and `_format_error_or_warning` always returns an error), reached through `build_agent_config()` (`config_builders.py:108`). The reload path (`services/config_section_reload.py::prepare_validated_section`, which uses `dataclasses.replace` and section validators) does not call `ProductionConfigValidator` (its only users are `config_builders.py` and `startup_validation.py`), so an empty list entering through `/reload` is not rejected (re-verified 2026-11-10: that module contains no `ProductionConfigValidator` call, and the tool-section validators do not test `allowed_tools` emptiness; the key appears only as `config_field_registry.py:80`); the runtime allow-all branch is therefore the live gap.
- `Confirmed by repository evidence` (introspection helpers): `list_tools()`, `list_tools_with_server_key()`, and the base `health()` of `MCPServer` (`server.py:194-235`) have no production caller; their docstrings say so; the two `MCPServer` subclasses are `CiCdMCPServer` and `MdqMCPServer`, and the servers' `/health` and `/v1/tools` handlers are module-level functions. Only `tests/mcp_servers/mdq/test_mdq_routing.py` and `test_mcp_server_base.py` call them.
- `Confirmed by repository evidence` (`security_profile`): `SecurityProfile` has the single member `PRODUCTION` (`scripts/shared/mcp_config.py:66-70`); `security_profile` is read in five modules (`production_config_validator.py`, `config_dataclasses.py`, `config_field_registry.py`, `config_builders.py`, `shared/mcp_config.py`) and is absent from `config/agent.toml`.
- `Refuted`/narrowed (`allowed_root`): it is an `agent.toml` approval setting (`config/agent.toml:218`, read by `tool_policy.py:276,466`; empty skips the path check), not a setting of the file servers, which do not read it (`delete_service.py` only has an unrelated "do not delete the root" check).
- `Confirmed by repository evidence` (`protected_branches`/`path_denylist`): an empty `protected_branches` removes the restriction in github (`github_service_security.py:172`) and in git (`repository_state.py:256-262`); both shipped configs set it non-empty (`config/git_mcp_server.toml:36`, `config/github_mcp_server.toml:19`). `config/github_mcp_server.toml:28` ships `path_denylist = []`, so rejecting an empty `path_denylist` would make the shipped configuration unstartable.
- Owner decision (maintainer, 2026-11-10): register an ADR-004 exception for an empty `path_denylist`; require non-empty `protected_branches` and `allowed_root`.
- `Needs confirmation`: the rationale text of the ADR-004 exception is the maintainer's (UNK-01); production callers of the removed helpers outside `scripts/` and `tests/` cannot be seen (UNK-03).

## Problem
- Unreachable non-strict branches and documents describing them as supported modes; "empty means allow all" for `allowed_tools` (runtime), `allowed_root`, and `protected_branches` removes a safety boundary through a typo or an unresolved variable, which ADR-004 Decision Group 1 forbids; a test-only authentication bypass in a production module; unused helpers and a single-valued profile key.

## Reason for Change
- Safety boundaries must not depend on a value being non-empty by luck; the validator covers only the initial load of `allowed_tools`. The MCP security Issue builds on a strict-only baseline. No external deadline.

## Implementation Intent
- Strict is the only behavior; drift and mismatch are always fatal. An empty safety list means deny or a load error on every path. Production modules contain only production behavior; tests inject non-empty dummy tokens. No currently enforced production check is weakened.

## Requirements
- `REQ-001`: Remove `tool_definitions_strict` and `routing_drift_strict` from the config schema, builders, registry, validator, display, and `config/agent.toml`; tool-definition mismatch and routing drift are always FATAL; config load rejects the removed keys as unknown.
- `REQ-002`: An empty `allowed_tools` denies every tool at runtime (`tool_policy.py` and `RuntimeToolRegistry.apply_policy`, which `/reload` uses via `config_service_sync.py`), including after `/reload`; the initial-load error stays; test fixtures that relied on the empty default supply a non-empty list.
- `REQ-003`: An empty `allowed_root` is rejected at config load and `tool_policy.py` no longer skips the path check for it.
- `REQ-004`: An empty `protected_branches` is rejected at config load for the git and github servers (in `GitConfig.load()` and `GitHubConfig.load()`, the production entry points, not in `from_dict()`, which stays a pure parser; measured: rejecting in `from_dict()` fails 202 tests in 9 files outside the target table); the skip-when-empty branches are removed; an empty `path_denylist` stays permitted and is recorded as an ADR-004 exception with the maintainer's rationale (pending) and a marker in `config/github_mcp_server.toml`.
- `REQ-005`: Remove `accept_all_for_tests`; tests inject non-empty dummy tokens; the empty-token test enumerates the MCP servers from `config/agent.toml` `[mcp_servers.*]` instead of the hard-coded list.
- `REQ-006`: Delete `list_tools()`, `list_tools_with_server_key()`, and the base `health()` (no production caller) and the tests that use them.
- `REQ-007`: Remove `security_profile` and `SecurityProfile` from the schema, builders, validator, registry, and `mcp_06_01`, and delete the "non-production mode is rejected" regression test.
- `REQ-008`: Update the listed MCP, agent, ADR, and overview documents to strict-only behavior and fail-closed safety lists.
- `REQ-009`: Verification: greps for the removed names return nothing, the documentation checkers pass, and the validation sequence passes.

## Implementation Target Files
**Freeze status**: Frozen
Amended 2026-11-10 (fallout): added scripts/shared/runtime_tool_registry.py — apply_policy (the /reload path via config_service_sync) re-enables every tool for an empty allowed_tools, so REQ-002 'including after /reload' needs this change
Amended 2026-11-10 (fallout): added tests/agent/commands/test_cmd_config_char.py — Asserts the removed `tool_def_strict` display row (line 144)
Amended 2026-11-10 (fallout): added tests/agent/commands/test_agent_cmd_config.py — Sets the removed `tool_definitions_strict` attribute (line 199)
Amended 2026-11-10 (fallout): added tests/tools/test_check_docs_quality.py — A docs-quality fixture line contains `SecurityProfile` (line 477), which AC-07 requires to be absent from tests/
Amended 2026-11-10 (fallout): added tests/mcp_servers/github/test_github_mcp_service.py — Removing the skip-when-empty branch fails test_empty_protected_branches_skips_check_with_empty_branch (measured by experiment)
Amended 2026-11-10 (fallout): added tests/agent/test_tool_approval_repos.py — Fails under deny-on-empty allowed_tools (measured by experiment)
Amended 2026-11-10 (fallout): added tests/agent/test_tool_approval_risk.py — Fails under deny-on-empty allowed_tools (measured by experiment)
Amended 2026-11-10 (fallout): added tests/agent/test_tool_runner.py — Fails under deny-on-empty allowed_tools (measured by experiment)
Amended 2026-11-10 (fallout): added tests/integration/test_rag_turn_integration.py — Fails under deny-on-empty allowed_tools (measured by experiment)
Amended 2026-11-10 (fallout): added docs/40_shared/shared_01_overview.md — shared_01_overview.md:142 names `SecurityProfile` (AC-07/REQ-008 grep or fail-closed statement)
Amended 2026-11-10 (fallout): added docs/40_shared/shared_03_03_runtime_and_execution-llm-and-mcp-clients.md — shared_03_03:65 names `SecurityProfile` (AC-07/REQ-008 grep or fail-closed statement)
Amended 2026-11-10 (fallout): added docs/91_security/security_01_architecture-and-trust-boundaries.md — security_01:128 names `SecurityProfile` (AC-07/REQ-008 grep or fail-closed statement)
Amended 2026-11-10 (fallout): added docs/91_security/security_02_high-risk-tool-common-policy.md — security_02:142 names `SecurityProfile`; :174 calls protected_branches fail-open (AC-07/REQ-008 grep or fail-closed statement)
Amended 2026-11-10 (fallout): added docs/23_agent/agent_06_02_tool-execution-and-approval-approval.md — agent_06_02:33-34 describes the empty allowed_tools and allowed_root skips (AC-07/REQ-008 grep or fail-closed statement)
Amended 2026-11-10 (fallout): added docs/23_agent/agent_06_03_tool-execution-and-approval-concurrency-safety.md — agent_06_03:33-34 states empty allowed_tools allows all and empty allowed_root disables the jail (AC-07/REQ-008 grep or fail-closed statement)
Amended 2026-11-10 (fallout): added docs/22_mcp/mcp_04_05_git.md — mcp_04_05_git.md:48 states an empty protected_branches protects none (AC-07/REQ-008 grep or fail-closed statement)
Amended 2026-11-10 (fallout): added docs/22_mcp/mcp_05_01_access-control-and-allowlists.md — mcp_05_01:78,83 state empty protected_branches/path_denylist allow all (AC-07/REQ-008 grep or fail-closed statement)
Amended 2026-11-10 (fallout): added tests/agent/test_repository_gateway.py — Imports STRICT_PRODUCTION_OVERRIDES, which is removed from tests/agent/_config_test_defaults.py
Amended 2026-11-10 (fallout): added tests/agent/test_tool_audit.py — Imports STRICT_PRODUCTION_OVERRIDES, which is removed from tests/agent/_config_test_defaults.py

This table is the canonical, frozen source of implementation scope for this Plan. Once
`Frozen`, `Implementation steps`, `Acceptance criteria`, and every downstream
`plan-to-implementation-procedure` document MUST reference file paths only from this
table — no other file may be treated as a modification target.

| File Path | Change Responsibility | Reason for Modification | Related Requirement / Acceptance Criterion | Repository Evidence | Related Tests | Validation Status |
|---|---|---|---|---|---|---|
| `scripts/agent/production_config_validator.py` | Modify: Drop the `*_strict` and `security_profile` keys and the profile check | Drop the `*_strict` and `security_profile` keys and the profile check; reject an empty `allowed_root`; keep the `allowed_tools=[]` error | REQ-001, REQ-003, REQ-007 / AC-01, AC-03, AC-07 | `production_config_validator.py:24-34,187,231-246,303` (checked in Step 3) | `tests/agent/test_production_config_validator.py` | Verified |
| `scripts/agent/startup_validation.py` | Modify: Routing drift is always FATAL | Routing drift is always FATAL; remove the `routing_drift_strict` branch and the non-strict failure classification | REQ-001 / AC-01 | `startup_validation.py:62,151-156` (checked in Step 3) | `tests/agent/test_startup_validation.py`, `tests/agent/shared/test_startup_validation_pipeline.py` | Verified |
| `scripts/agent/services/mcp_tool_discovery.py` | Modify: Tool-definition mismatch is always FATAL | Tool-definition mismatch is always FATAL; remove `_is_strict` and the WARNING severity | REQ-001 / AC-01 | `mcp_tool_discovery.py:16-30,157` (checked in Step 3) | `tests/agent/services/test_mcp_tool_discovery.py` | Verified |
| `scripts/agent/services/config_field_registry.py` | Modify: Remove the two strict entries and the `security_profile` entry | Remove the two strict entries and the `security_profile` entry | REQ-001, REQ-007 / AC-01, AC-07 | `config_field_registry.py:75,81,100` (checked in Step 3) | `tests/agent/test_config_builders.py` | Verified |
| `scripts/agent/config_builders.py` | Modify: Remove `security_profile_val` plumbing through `_run_production_validation` and `build_agent_config` | Remove `security_profile_val` plumbing through `_run_production_validation` and `build_agent_config` | REQ-007 / AC-07 | `config_builders.py:102-168` (checked in Step 3) | `tests/agent/test_config_builders.py` | Verified |
| `scripts/agent/config_dataclasses.py` | Modify: Remove the two strict fields and `AgentConfig.security_profile` with its coercion | Remove the two strict fields and `AgentConfig.security_profile` with its coercion | REQ-001, REQ-007 / AC-01, AC-07 | `config_dataclasses.py:164,166,273-278` (checked in Step 3) | `tests/agent/test_config_dataclasses.py` | Verified |
| `scripts/agent/config_section_builders.py` | Modify: Remove the strict builders | Remove the strict builders; make an empty `allowed_root` a load error | REQ-001, REQ-003 / AC-01, AC-03 | `config_section_builders.py:185-189,304-318` (checked in Step 3) | `tests/agent/test_config_builders.py` | Verified |
| `scripts/agent/commands/cmd_config_display.py` | Modify: Remove the `tool_def_strict` display row | Remove the `tool_def_strict` display row | REQ-001 / AC-01 | `cmd_config_display.py:81` (checked in Step 3) | `tests/agent/commands/test_cmd_config_char.py`, `tests/agent/commands/test_agent_cmd_config.py` | Verified |
| `scripts/agent/tool_policy.py` | Modify: An empty `allowed_tools` denies every tool | An empty `allowed_tools` denies every tool; an empty `allowed_root` no longer skips the path check | REQ-002, REQ-003 / AC-02, AC-03 | `tool_policy.py:276,466,513` (checked in Step 3) | `tests/agent/test_tool_policy.py`, `tests/agent/test_tool_policy_comprehensive.py` | Verified |
| `scripts/shared/mcp_config.py` | Modify: Delete the single-valued `SecurityProfile` enum and its users | Delete the single-valued `SecurityProfile` enum and its users | REQ-007 / AC-07 | `scripts/shared/mcp_config.py:66-70` (checked in Step 3) | `tests/shared/test_mcp_config.py` | Verified |
| `scripts/mcp_servers/server.py` | Modify: Remove `accept_all_for_tests`, `list_tools`, `list_tools_with_server_key`, and the base `health()` | Remove `accept_all_for_tests`, `list_tools`, `list_tools_with_server_key`, and the base `health()` | REQ-005, REQ-006 / AC-05, AC-06 | `scripts/mcp_servers/server.py:100-124,194-235` (checked in Step 3) | `tests/mcp_servers/test_mcp_server_base.py`, `tests/mcp_servers/mdq/test_mdq_routing.py` | Verified |
| `scripts/mcp_servers/mdq/mdq_server.py` | Modify: Reword the docstring that cites `list_tools_with_server_key()` | Reword the docstring that cites `list_tools_with_server_key()` | REQ-006 / AC-06 | `mdq_server.py:461` (checked in Step 3) | `tests/mcp_servers/mdq/test_mdq_routing.py` | Verified |
| `scripts/mcp_servers/git/git_models.py` | Modify: Reject an empty `protected_branches` at config load | Reject an empty `protected_branches` at config load | REQ-004 / AC-04 | `git_models.py:53,76-77` (`default=[]`) (checked in Step 3) | `tests/mcp_servers/git/test_git_models.py` | Verified |
| `scripts/mcp_servers/git/repository_state.py` | Modify: Remove the empty-list "never protected" branch | Remove the empty-list "never protected" branch | REQ-004 / AC-04 | `repository_state.py:256-262` (checked in Step 3) | `tests/mcp_servers/git/test_repository_state.py` | Verified |
| `scripts/mcp_servers/github/github_models_config.py` | Modify: Reject an empty `protected_branches` at config load | Reject an empty `protected_branches` at config load; keep `path_denylist` empty permitted under the ADR-004 exception | REQ-004 / AC-04 | `github_models_config.py:32-33,49-50` (checked in Step 3) | `tests/mcp_servers/github/test_service_security.py` | Verified |
| `scripts/mcp_servers/github/github_service_security.py` | Modify: Remove the skip-when-empty branch and the posture text for an empty `protected_branches` | Remove the skip-when-empty branch and the posture text for an empty `protected_branches` | REQ-004 / AC-04 | `github_service_security.py:172,318-345` (checked in Step 3) | `tests/mcp_servers/github/test_github_security_validation.py`, `tests/mcp_servers/github/test_github_health_posture.py` | Verified |
| `config/agent.toml` | Modify: Delete `tool_definitions_strict` and `routing_drift_strict` | Delete `tool_definitions_strict` and `routing_drift_strict` | REQ-001 / AC-01 | `config/agent.toml:47,48` (re-verified 2026-11-10 against the current tree) | `tests/agent/test_production_config_validator.py` | Verified |
| `config/github_mcp_server.toml` | Modify: Annotate `path_denylist = []` as the registered ADR-004 exception | Annotate `path_denylist = []` as the registered ADR-004 exception | REQ-004 / AC-04 | `config/github_mcp_server.toml:27-28` (checked in Step 3) | `tests/mcp_servers/github/test_github_security_validation.py` | Verified |
| `tests/agent/test_production_config_validator.py` | Modify: Remove strict/profile cases | Remove strict/profile cases; add rejection cases for the removed keys and an empty `allowed_root` | REQ-001, REQ-003, REQ-007 / AC-01, AC-03, AC-07 | 61 hits (rg count) (checked in Step 3) | `uv run pytest tests/agent/test_production_config_validator.py -v` | Verified |
| `tests/agent/test_config_builders.py` | Modify: Remove strict/profile cases | Remove strict/profile cases | REQ-001, REQ-007 / AC-01, AC-07 | 32 hits (rg count) (checked in Step 3) | `uv run pytest tests/agent/test_config_builders.py -v` | Verified |
| `tests/agent/services/test_mcp_tool_discovery.py` | Modify: Drop non-strict (WARNING) cases | Drop non-strict (WARNING) cases; mismatch is always FATAL | REQ-001 / AC-01 | 24 hits (rg count) (checked in Step 3) | `uv run pytest tests/agent/services/test_mcp_tool_discovery.py -v` | Verified |
| `tests/agent/test_startup_mcp_lifecycle.py` | Modify: Drop the strict toggles from fixtures | Drop the strict toggles from fixtures | REQ-001 / AC-01 | 21 hits (rg count) (checked in Step 3) | `uv run pytest tests/agent/test_startup_mcp_lifecycle.py -v` | Verified |
| `tests/integration/test_production_security_regression.py` | Modify: Delete the "non-production mode is rejected" regression | Delete the "non-production mode is rejected" regression; keep the production-only checks | REQ-001 / AC-01 | 16 hits (rg count) (checked in Step 3) | `uv run pytest tests/integration/test_production_security_regression.py -v` | Verified |
| `tests/agent/test_startup_severity_classification.py` | Modify: Drop non-strict severity cases | Drop non-strict severity cases | REQ-001 / AC-01 | 15 hits (rg count) (checked in Step 3) | `uv run pytest tests/agent/test_startup_severity_classification.py -v` | Verified |
| `tests/agent/test_startup.py` | Modify: Drop the strict toggles from fixtures | Drop the strict toggles from fixtures | REQ-001 / AC-01 | 13 hits (rg count) (checked in Step 3) | `uv run pytest tests/agent/test_startup.py -v` | Verified |
| `tests/agent/shared/test_startup_validation_pipeline.py` | Modify: Drop non-strict drift cases | Drop non-strict drift cases | REQ-001 / AC-01 | 13 hits (rg count) (checked in Step 3) | `uv run pytest tests/agent/shared/test_startup_validation_pipeline.py -v` | Verified |
| `tests/agent/test_agent_negative_paths.py` | Modify: Drop the strict toggles from fixtures | Drop the strict toggles from fixtures | REQ-001 / AC-01 | 11 hits (rg count) (checked in Step 3) | `uv run pytest tests/agent/test_agent_negative_paths.py -v` | Verified |
| `tests/mcp_servers/test_mcp_server_base.py` | Modify: Remove `accept_all_for_tests` and `list_tools` cases | Remove `accept_all_for_tests` and `list_tools` cases; inject dummy tokens | REQ-005, REQ-006 / AC-05, AC-06 | 9 hits (rg count) (checked in Step 3) | `uv run pytest tests/mcp_servers/test_mcp_server_base.py -v` | Verified |
| `tests/agent/test_startup_memory_failures.py` | Modify: Drop the strict toggles from fixtures | Drop the strict toggles from fixtures | REQ-001 / AC-01 | 8 hits (rg count) (checked in Step 3) | `uv run pytest tests/agent/test_startup_memory_failures.py -v` | Verified |
| `tests/shared/test_mcp_config.py` | Modify: Remove `SecurityProfile` cases | Remove `SecurityProfile` cases | REQ-001, REQ-007 / AC-01, AC-07 | 5 hits (rg count) (checked in Step 3) | `uv run pytest tests/shared/test_mcp_config.py -v` | Verified |
| `tests/agent/test_startup_validation.py` | Modify: Drop non-strict cases | Drop non-strict cases | REQ-001 / AC-01 | 5 hits (rg count) (checked in Step 3) | `uv run pytest tests/agent/test_startup_validation.py -v` | Verified |
| `tests/agent/test_config_dataclasses.py` | Modify: Remove the strict and profile field cases | Remove the strict and profile field cases | REQ-001, REQ-007 / AC-01, AC-07 | 5 hits (rg count) (checked in Step 3) | `uv run pytest tests/agent/test_config_dataclasses.py -v` | Verified |
| `tests/agent/test_startup_mcp_starter.py` | Modify: Drop the strict toggles from fixtures | Drop the strict toggles from fixtures | REQ-001 / AC-01 | 4 hits (rg count) (checked in Step 3) | `uv run pytest tests/agent/test_startup_mcp_starter.py -v` | Verified |
| `tests/shared/test_config_loader.py` | Modify: Drop the removed keys from fixtures | Drop the removed keys from fixtures | REQ-001 / AC-01 | 3 hits (rg count) (checked in Step 3) | `uv run pytest tests/shared/test_config_loader.py -v` | Verified |
| `tests/mcp_servers/mdq/test_mdq_routing.py` | Modify: Remove the `list_tools*` and base `health()` cases | Remove the `list_tools*` and base `health()` cases | REQ-006 / AC-06 | 3 hits (rg count) (checked in Step 3) | `uv run pytest tests/mcp_servers/mdq/test_mdq_routing.py -v` | Verified |
| `tests/agent/services/test_config_reload.py` | Modify: Drop the removed keys | Drop the removed keys; add a reload case for an empty `allowed_tools` | REQ-002, REQ-003 / AC-02, AC-03 | 3 hits (rg count) (checked in Step 3) | `uv run pytest tests/agent/services/test_config_reload.py -v` | Verified |
| `tests/agent/_config_test_defaults.py` | Modify: Drop the removed keys | Drop the removed keys; give the default fixture a non-empty `allowed_tools` and `allowed_root` | REQ-002, REQ-003 / AC-02, AC-03 | 3 hits (rg count) (checked in Step 3) | `uv run pytest tests/agent/_config_test_defaults.py -v` | Verified |
| `tests/shared/test_shared_boundary_conditions.py` | Modify: Drop the removed keys | Drop the removed keys | REQ-001 / AC-01 | 2 hits (rg count) (checked in Step 3) | `uv run pytest tests/shared/test_shared_boundary_conditions.py -v` | Verified |
| `tests/agent/test_tool_policy_comprehensive.py` | Modify: Replace the empty-list allow-all cases with deny-all | Replace the empty-list allow-all cases with deny-all | REQ-001 / AC-01 | 2 hits (rg count) (checked in Step 3) | `uv run pytest tests/agent/test_tool_policy_comprehensive.py -v` | Verified |
| `tests/agent/test_startup_rollback.py` | Modify: Drop the strict toggles from fixtures | Drop the strict toggles from fixtures | REQ-001 / AC-01 | 2 hits (rg count) (checked in Step 3) | `uv run pytest tests/agent/test_startup_rollback.py -v` | Verified |
| `tests/agent/test_startup_config_error.py` | Modify: Drop the strict toggles from fixtures | Drop the strict toggles from fixtures | REQ-001 / AC-01 | 2 hits (rg count) (checked in Step 3) | `uv run pytest tests/agent/test_startup_config_error.py -v` | Verified |
| `tests/agent/services/test_runtime_tool_routing_integration.py` | Modify: Drop the strict toggles from fixtures | Drop the strict toggles from fixtures | REQ-001 / AC-01 | 2 hits (rg count) (checked in Step 3) | `uv run pytest tests/agent/services/test_runtime_tool_routing_integration.py -v` | Verified |
| `tests/integration/test_agent_integration.py` | Modify: Drop the removed keys | Drop the removed keys | REQ-001 / AC-01 | 1 hit (rg count) (checked in Step 3) | `uv run pytest tests/integration/test_agent_integration.py -v` | Verified |
| `tests/agent/services/test_mcp_tool_discovery_posture_gate.py` | Modify: Drop the strict toggle | Drop the strict toggle | REQ-001 / AC-01 | 1 hit (rg count) (checked in Step 3) | `uv run pytest tests/agent/services/test_mcp_tool_discovery_posture_gate.py -v` | Verified |
| `tests/agent/test_tool_policy.py` | Modify: Replace the empty-list allow-all cases with deny-all | Replace the empty-list allow-all cases with deny-all | REQ-002, REQ-003 / AC-02, AC-03 | allowed_tools empty-list cases (rg) (checked in Step 3) | `uv run pytest tests/agent/test_tool_policy.py -v` | Verified |
| `tests/agent/test_tool_approval_preflight.py` | Modify: Supply a non-empty `allowed_tools` where the default empty list was relied on | Supply a non-empty `allowed_tools` where the default empty list was relied on | REQ-002, REQ-003 / AC-02, AC-03 | empty `allowed_tools`/`allowed_root` fixtures (rg) (checked in Step 3) | `uv run pytest tests/agent/test_tool_approval_preflight.py -v` | Verified |
| `tests/agent/test_tool_approval_paths.py` | Modify: Supply a non-empty `allowed_tools`/`allowed_root` where the default was relied on | Supply a non-empty `allowed_tools`/`allowed_root` where the default was relied on | REQ-002, REQ-003 / AC-02, AC-03 | empty-list fixtures (rg) (checked in Step 3) | `uv run pytest tests/agent/test_tool_approval_paths.py -v` | Verified |
| `tests/agent/test_agent_repl_tool_exec.py` | Modify: Supply a non-empty `allowed_tools` where the default was relied on | Supply a non-empty `allowed_tools` where the default was relied on | REQ-002, REQ-003 / AC-02, AC-03 | empty-list fixtures (rg) (checked in Step 3) | `uv run pytest tests/agent/test_agent_repl_tool_exec.py -v` | Verified |
| `tests/shared/test_runtime_tool_registry.py` | Modify: Supply a non-empty `allowed_tools` where the default was relied on | Supply a non-empty `allowed_tools` where the default was relied on | REQ-002, REQ-003 / AC-02, AC-03 | empty-list fixtures (rg) (checked in Step 3) | `uv run pytest tests/shared/test_runtime_tool_registry.py -v` | Verified |
| `tests/shared/test_tool_routing_validation.py` | Modify: Supply a non-empty `allowed_tools` where the default was relied on | Supply a non-empty `allowed_tools` where the default was relied on | REQ-002, REQ-003 / AC-02, AC-03 | empty-list fixtures (rg) (checked in Step 3) | `uv run pytest tests/shared/test_tool_routing_validation.py -v` | Verified |
| `tests/mcp_servers/test_require_auth_token.py` | Modify: Derive the server list for the empty-token test from `config/agent.toml` `[mcp_servers.*]` instead of the hard-coded `_SERVERS` | Derive the server list for the empty-token test from `config/agent.toml` `[mcp_servers.*]` instead of the hard-coded `_SERVERS` | REQ-005 / AC-05 | `test_require_auth_token.py:20-32,70` (checked in Step 3) | `uv run pytest tests/mcp_servers/test_require_auth_token.py -v` | Verified |
| `tests/mcp_servers/git/test_git_models.py` | Modify: Add the empty `protected_branches` rejection case | Add the empty `protected_branches` rejection case | REQ-004 / AC-04 | protected_branches hits (rg) (checked in Step 3) | `uv run pytest tests/mcp_servers/git/test_git_models.py -v` | Verified |
| `tests/mcp_servers/git/test_repository_state.py` | Modify: Replace the empty-list "never protected" cases | Replace the empty-list "never protected" cases | REQ-001 / AC-01 | protected_branches hits (rg) (checked in Step 3) | `uv run pytest tests/mcp_servers/git/test_repository_state.py -v` | Verified |
| `tests/mcp_servers/github/test_service_security.py` | Modify: Replace the empty `protected_branches` cases with rejection | Replace the empty `protected_branches` cases with rejection | REQ-004 / AC-04 | protected_branches hits (rg) (checked in Step 3) | `uv run pytest tests/mcp_servers/github/test_service_security.py -v` | Verified |
| `tests/mcp_servers/github/test_github_security_validation.py` | Modify: Align with the removed skip branch and the path_denylist exception | Align with the removed skip branch and the path_denylist exception | REQ-001 / AC-01 | protected_branches hits (rg) (checked in Step 3) | `uv run pytest tests/mcp_servers/github/test_github_security_validation.py -v` | Verified |
| `tests/mcp_servers/github/test_github_health_posture.py` | Modify: Align the posture text expectations | Align the posture text expectations | REQ-001 / AC-01 | protected_branches hits (rg) (checked in Step 3) | `uv run pytest tests/mcp_servers/github/test_github_health_posture.py -v` | Verified |
| `docs/22_mcp/mcp_06_09_startup-validation-behavior-tool_definitions_strict.md` | Modify: Describe strict-only startup validation | Describe strict-only startup validation; no toggle (the file name keeps the old key; renaming is out of scope) | REQ-008 / AC-08 | 5 hits (rg) (checked in Step 3) | `uv run python tools/check_docs_consistency.py --domain mcp` | Verified |
| `docs/22_mcp/mcp_06_01_configuration-file-inventory.md` | Modify: Remove `security_profile` and the strict keys from the inventory | Remove `security_profile` and the strict keys from the inventory | REQ-008 / AC-08 | 2 hits (rg) (checked in Step 3) | `uv run python tools/check_docs_consistency.py --domain mcp` | Verified |
| `docs/22_mcp/mcp_05_03_fail-open-fail-closed-and-risk-tiers.md` | Modify: State fail-closed defaults for safety lists | State fail-closed defaults for safety lists | REQ-008 / AC-08 | hit (rg) (checked in Step 3) | `uv run python tools/check_docs_consistency.py --domain mcp` | Verified |
| `docs/22_mcp/mcp_06_13_pre-production-fail-open-checklist.md` | Modify: Remove checklist items for removed toggles | Remove checklist items for removed toggles | REQ-008 / AC-08 | 3 hits (rg) (checked in Step 3) | `uv run python tools/check_docs_consistency.py --domain mcp` | Verified |
| `docs/22_mcp/mcp_06_03_long-running-http-operation-startup_modesubprocess.md` | Modify: Remove the strict-mode reference | Remove the strict-mode reference | REQ-008 / AC-08 | 3 hits (rg) (checked in Step 3) | `uv run python tools/check_docs_consistency.py --domain mcp` | Verified |
| `docs/22_mcp/mcp_05_02_auth-profiles-and-sandboxing.md` | Modify: Remove `accept_all_for_tests` and profile references | Remove `accept_all_for_tests` and profile references | REQ-008 / AC-08 | 3 hits (rg) (checked in Step 3) | `uv run python tools/check_docs_consistency.py --domain mcp` | Verified |
| `docs/22_mcp/mcp_03_02_tool-registry.md` | Modify: Remove `list_tools*` and strict references | Remove `list_tools*` and strict references | REQ-008 / AC-08 | 3 hits (rg) (checked in Step 3) | `uv run python tools/check_docs_consistency.py --domain mcp` | Verified |
| `docs/22_mcp/mcp_06_11_new-tool-registration-procedure.md` | Modify: Remove the strict reference | Remove the strict reference | REQ-008 / AC-08 | 1 hit (rg) (checked in Step 3) | `uv run python tools/check_docs_consistency.py --domain mcp` | Verified |
| `docs/22_mcp/mcp_06_08_settings-with-high-operational-impact.md` | Modify: Remove the removed settings | Remove the removed settings | REQ-008 / AC-08 | 1 hit (rg) (checked in Step 3) | `uv run python tools/check_docs_consistency.py --domain mcp` | Verified |
| `docs/22_mcp/mcp_02_01_endpoints-and-transport.md` | Modify: Remove the `list_tools*` reference | Remove the `list_tools*` reference | REQ-008 / AC-08 | 1 hit (rg) (checked in Step 3) | `uv run python tools/check_docs_consistency.py --domain mcp` | Verified |
| `docs/23_agent/agent_10_01_operations-and-observability-startup-and-health.md` | Modify: State strict-only startup behavior | State strict-only startup behavior | REQ-008 / AC-08 | 4 hits (rg) (checked in Step 3) | `uv run python tools/check_docs_consistency.py --domain agent` | Verified |
| `docs/23_agent/agent_08_04_configuration-mcp-approval-obs.md` | Modify: Describe `allowed_root` as required and remove `security_profile` | Describe `allowed_root` as required and remove `security_profile` | REQ-008 / AC-08 | named by the Issue (rg) (checked in Step 3) | `uv run python tools/check_docs_consistency.py --domain agent` | Verified |
| `docs/23_agent/agent_08_03_configuration-tools-memory.md` | Modify: Remove the strict keys | Remove the strict keys; state empty `allowed_tools` denies | REQ-008 / AC-08 | 3 hits (rg) (checked in Step 3) | `uv run python tools/check_docs_consistency.py --domain agent` | Verified |
| `docs/23_agent/agent_08_01_configuration-loading-agent-config.md` | Modify: Remove the removed keys | Remove the removed keys | REQ-008 / AC-08 | 1 hit (rg) (checked in Step 3) | `uv run python tools/check_docs_consistency.py --domain agent` | Verified |
| `docs/10_adr/adr_02_02_003_agent-runtime-tool-registry-routing-authority.md` | Modify: State routing drift as always fatal in the startup validation description | State routing drift as always fatal in the startup validation description | REQ-008 / AC-08 | 2 hits (rg) (checked in Step 3) | `uv run python tools/check_adr_preservation.py`, `check_adr_authority.py` | Verified |
| `docs/10_adr/adr_02_01_004_platform-environment-failure-handling-policy.md` | Modify: Register the `path_denylist` empty-list exception with the maintainer's rationale (pending) | Register the `path_denylist` empty-list exception with the maintainer's rationale (pending) | REQ-008 / AC-08 | 1 hit (rg); Decision Group 1 (checked in Step 3) | `uv run python tools/check_adr_preservation.py`, `check_adr_authority.py` | Verified |
| `docs/10_adr/adr_02_01_002_platform-config-isolation.md` | Modify: Remove the removed-key reference | Remove the removed-key reference | REQ-008 / AC-08 | 1 hit (rg) (checked in Step 3) | `uv run python tools/check_adr_preservation.py`, `check_adr_authority.py` | Verified |
| `docs/01_overview/overview_02_files.md` | Modify: Remove the removed-key reference | Remove the removed-key reference | REQ-008 / AC-08 | 1 hit (rg) (checked in Step 3) | `uv run python tools/check_docs_consistency.py --domain overview` | Verified |
| `scripts/shared/runtime_tool_registry.py` | Modify: apply_policy denies every tool for an empty allowed_tools | apply_policy (the /reload path via config_service_sync) re-enables every tool for an empty allowed_tools, so REQ-002 'including after /reload' needs this change | REQ-002 / AC-02 | runtime_tool_registry.py:209-232 (`not allowed_tools or name in allowed_tools`); config_service_sync.py:76-81 | `tests/shared/test_runtime_tool_registry.py` | Verified |
| `tests/agent/commands/test_cmd_config_char.py` | Modify: Drop the tool_def_strict display expectation | Asserts the removed `tool_def_strict` display row (line 144) | REQ-001 / AC-01 | test_cmd_config_char.py:144 | uv run pytest tests/agent/commands/test_cmd_config_char.py -v | Verified |
| `tests/agent/commands/test_agent_cmd_config.py` | Modify: Drop the tool_definitions_strict fixture assignment | Sets the removed `tool_definitions_strict` attribute (line 199) | REQ-001 / AC-01 | test_agent_cmd_config.py:199 | uv run pytest tests/agent/commands/test_agent_cmd_config.py -v | Verified |
| `tests/tools/test_check_docs_quality.py` | Modify: Reword the fixture line that names SecurityProfile | A docs-quality fixture line contains `SecurityProfile` (line 477), which AC-07 requires to be absent from tests/ | REQ-007 / AC-07 | test_check_docs_quality.py:477 | uv run pytest tests/tools/test_check_docs_quality.py -v | Verified |
| `tests/mcp_servers/github/test_github_mcp_service.py` | Modify: Replace the empty-protected_branches skip test | Removing the skip-when-empty branch fails test_empty_protected_branches_skips_check_with_empty_branch (measured by experiment) | REQ-004 / AC-04 | test_github_mcp_service.py TestResolveAndCheckBranch (1 failing test measured) | uv run pytest tests/mcp_servers/github/test_github_mcp_service.py -v | Verified |
| `tests/agent/test_tool_approval_repos.py` | Modify: Supply a non-empty allowed_tools where the default was relied on | Fails under deny-on-empty allowed_tools (measured by experiment) | REQ-002 / AC-02 | experiment: deny-on-empty fails this file | uv run pytest tests/agent/test_tool_approval_repos.py -v | Verified |
| `tests/agent/test_tool_approval_risk.py` | Modify: Supply a non-empty allowed_tools where the default was relied on | Fails under deny-on-empty allowed_tools (measured by experiment) | REQ-002 / AC-02 | experiment: deny-on-empty fails this file | uv run pytest tests/agent/test_tool_approval_risk.py -v | Verified |
| `tests/agent/test_tool_runner.py` | Modify: Supply a non-empty allowed_tools where the default was relied on | Fails under deny-on-empty allowed_tools (measured by experiment) | REQ-002 / AC-02 | experiment: deny-on-empty fails this file | uv run pytest tests/agent/test_tool_runner.py -v | Verified |
| `tests/integration/test_rag_turn_integration.py` | Modify: Supply a non-empty allowed_tools where the default was relied on | Fails under deny-on-empty allowed_tools (measured by experiment) | REQ-002 / AC-02 | experiment: deny-on-empty fails this file | uv run pytest tests/integration/test_rag_turn_integration.py -v | Verified |
| `docs/40_shared/shared_01_overview.md` | Modify: Update SecurityProfile wording | shared_01_overview.md:142 names `SecurityProfile` (AC-07/REQ-008 grep or fail-closed statement) | REQ-008 / AC-08 | shared_01_overview.md:142 names `SecurityProfile` | uv run python tools/check_docs_consistency.py --domain overview | Verified |
| `docs/40_shared/shared_03_03_runtime_and_execution-llm-and-mcp-clients.md` | Modify: Update SecurityProfile wording | shared_03_03:65 names `SecurityProfile` (AC-07/REQ-008 grep or fail-closed statement) | REQ-008 / AC-08 | shared_03_03:65 names `SecurityProfile` | uv run python tools/check_docs_consistency.py --domain overview | Verified |
| `docs/91_security/security_01_architecture-and-trust-boundaries.md` | Modify: Update SecurityProfile wording | security_01:128 names `SecurityProfile` (AC-07/REQ-008 grep or fail-closed statement) | REQ-008 / AC-08 | security_01:128 names `SecurityProfile` | uv run python tools/check_docs_consistency.py --domain overview | Verified |
| `docs/91_security/security_02_high-risk-tool-common-policy.md` | Modify: Update SecurityProfile and protected_branches fail-open wording | security_02:142 names `SecurityProfile`; :174 calls protected_branches fail-open (AC-07/REQ-008 grep or fail-closed statement) | REQ-008 / AC-08 | security_02:142 names `SecurityProfile`; :174 calls protected_branches fail-open | uv run python tools/check_docs_consistency.py --domain overview | Verified |
| `docs/23_agent/agent_06_02_tool-execution-and-approval-approval.md` | Modify: Update empty allowed_tools/allowed_root wording | agent_06_02:33-34 describes the empty allowed_tools and allowed_root skips (AC-07/REQ-008 grep or fail-closed statement) | REQ-008 / AC-08 | agent_06_02:33-34 describes the empty allowed_tools and allowed_root skips | uv run python tools/check_docs_consistency.py --domain agent | Verified |
| `docs/23_agent/agent_06_03_tool-execution-and-approval-concurrency-safety.md` | Modify: Update empty allowed_tools/allowed_root wording | agent_06_03:33-34 states empty allowed_tools allows all and empty allowed_root disables the jail (AC-07/REQ-008 grep or fail-closed statement) | REQ-008 / AC-08 | agent_06_03:33-34 states empty allowed_tools allows all and empty allowed_root disables the jail | uv run python tools/check_docs_consistency.py --domain agent | Verified |
| `docs/22_mcp/mcp_04_05_git.md` | Modify: Update empty protected_branches wording | mcp_04_05_git.md:48 states an empty protected_branches protects none (AC-07/REQ-008 grep or fail-closed statement) | REQ-008 / AC-08 | mcp_04_05_git.md:48 states an empty protected_branches protects none | uv run python tools/check_docs_consistency.py --domain mcp | Verified |
| `docs/22_mcp/mcp_05_01_access-control-and-allowlists.md` | Modify: Update empty protected_branches and the path_denylist exception wording | mcp_05_01:78,83 state empty protected_branches/path_denylist allow all (AC-07/REQ-008 grep or fail-closed statement) | REQ-008 / AC-08 | mcp_05_01:78,83 state empty protected_branches/path_denylist allow all | uv run python tools/check_docs_consistency.py --domain mcp | Verified |
| `tests/agent/test_repository_gateway.py` | Modify: Stop importing STRICT_PRODUCTION_OVERRIDES | Imports STRICT_PRODUCTION_OVERRIDES, which is removed from tests/agent/_config_test_defaults.py | REQ-001 / AC-01 | tests/agent/test_repository_gateway.py imports the constant (rg) | uv run pytest tests/agent/test_repository_gateway.py -v | Verified |
| `tests/agent/test_tool_audit.py` | Modify: Stop importing STRICT_PRODUCTION_OVERRIDES | Imports STRICT_PRODUCTION_OVERRIDES, which is removed from tests/agent/_config_test_defaults.py | REQ-001 / AC-01 | tests/agent/test_tool_audit.py imports the constant (rg) | uv run pytest tests/agent/test_tool_audit.py -v | Verified |

## Reference Files
Files that must be read to implement the targets above, but MUST NOT be modified.

| File Path | Why It Must Be Read | Related Target File or Requirement |
|---|---|---|
| `scripts/agent/services/config_section_reload.py` | Reload path that bypasses `ProductionConfigValidator` | REQ-002 |
| `config/git_mcp_server.toml` | Shipped non-empty `protected_branches` (must keep loading) | REQ-004 |
| `tests/mcp_servers/mdq/test_mdq_rag_boundary.py` | Boundary test required in final validation | REQ-009 |
| `tools/check_compat_shims.py` | No-compatibility-shim rule for the key removal | REQ-001 |
| `rules/toolchain.md` | Impact-radius check commands | REQ-009 |

## Acceptance Criteria
- `AC-01` (REQ-001): `rg -n "tool_definitions_strict|routing_drift_strict" scripts/ tests/ config/` returns only removed-key rejection tests; config load rejects both keys.
- `AC-02` (REQ-002): tests show an empty `allowed_tools` denies a tool call and is rejected at load and after `/reload`.
- `AC-03` (REQ-003): tests show an empty `allowed_root` fails config load.
- `AC-04` (REQ-004): tests show an empty `protected_branches` fails config load for git and github; ADR-004 carries the `path_denylist` exception with a marked pending rationale; the shipped configs still load.
- `AC-05` (REQ-005): `rg -n accept_all_for_tests scripts tests` returns nothing; the empty-token test covers every server found in `config/agent.toml` `[mcp_servers.*]`.
- `AC-06` (REQ-006): `rg -n "list_tools_with_server_key|def list_tools\(self" scripts tests` returns nothing.
- `AC-07` (REQ-007): `rg -n "security_profile|SecurityProfile" scripts tests config docs` returns nothing.
- `AC-08` (REQ-008): `check_docs_consistency.py --domain mcp` and `--domain agent`, `check_docs_quality.py`, `check_docs_structure.py`, `check_docs_content_policy.py --strict`, `check_adr_authority.py` pass.
- `AC-09` (REQ-009): the full validation sequence passes, including `tests/mcp_servers/mdq/test_mdq_rag_boundary.py`.

## Tests
- `REQ-001`: updated startup and discovery tests (always FATAL) and a removed-key rejection test in `tests/agent/test_production_config_validator.py`.
- `REQ-002`, `REQ-003`: `tests/agent/test_tool_policy.py`, `tests/agent/test_tool_policy_comprehensive.py`, `tests/agent/services/test_config_reload.py`, the validator tests.
- `REQ-004`: `tests/mcp_servers/git/test_git_models.py`, `tests/mcp_servers/github/test_service_security.py` and the posture tests.
- `REQ-005`: `tests/mcp_servers/test_require_auth_token.py` (enumerated from `config/agent.toml`), `tests/mcp_servers/test_mcp_server_base.py`.
- `REQ-006`, `REQ-007`: remaining `tests/mcp_servers/mdq/test_mdq_routing.py`, `tests/shared/test_mcp_config.py`, and the config-builder tests; deletion of the profile regression.

## Documentation Impact
- Required (REQ-008): `mcp_06_09`, `mcp_06_01`, `mcp_05_03`, `agent_10_01`, `agent_08_04`, ADR-003, ADR-004 (path_denylist exception), and the other MCP, agent, and overview documents in the target table. State strict-only behavior, fail-closed defaults for safety lists, and failure behavior; do not copy concrete config values (`skills/DESIGN.md` Docs content policy).

## Assumptions
- Deleting the base `MCPServer.health()` (instead of making it abstract) is acceptable because it has no production caller and each server serves `/health` from a module-level handler; the Issue allows "abstract or derived". Confirmed by the maintainer on 2026-11-10 (UNK-02 resolved: delete).
- `tests/rag/ingestion/test_pipeline_utils_strict.py` matched `_strict` text but is unrelated to the removed keys and is not a target. `tests/tools/test_check_docs_quality.py` is a target only for its `SecurityProfile` fixture line (REQ-007), not for `_strict`.
- Step 3a verification (2026-11-10, plan-to-implementation-procedure): the first-order consumers were re-checked with `rg` and with throwaway experiments reverted by `git checkout`. Findings: (1) the strict keys sit at `config/agent.toml:47,48`, not 49,50; (2) rejecting an empty `protected_branches` in `from_dict()` fails 202 tests in 9 files outside the table, so REQ-004 is implemented in `load()`; (3) removing the github skip-when-empty branch fails one test in `test_github_mcp_service.py`; (4) deny-on-empty `allowed_tools` fails four test files outside the table (`test_tool_approval_repos.py`, `test_tool_approval_risk.py`, `test_tool_runner.py`, `tests/integration/test_rag_turn_integration.py`); (5) `RuntimeToolRegistry.apply_policy` re-enables every tool for an empty `allowed_tools` on `/reload`; (6) consumers of the removed names missing from the table: two `tests/agent/commands/` files, `tests/tools/test_check_docs_quality.py`, and eight documents. Each was added as a `fallout` row by `tools/amend_plan.py`.
- Not changed, by decision: `scripts/agent/wal_checkpoint_manager.py::_is_db_path_allowed` returns True for an empty `allowed_root`. No REQ covers it; it becomes unreachable at load once REQ-003 holds and is left as is. Falsifiable by the maintainer; changing it is a scope amendment. `tests/agent/test_tool_policy.py` fixtures and `scripts/shared/security/posture_contract.py` need no change (the posture text change is in `github_service_security.py`).
- `tools/plan_dependency_order.py` reports this Plan `gated` on `issues/20261109-113023_adrrev011_mcp-audit-auth-adr.md`, but the Plan's Scope says that Issue is blocked by this Plan (a prose misreading); `Depends on` is none, and the two sibling Plans named there are already archived.
- The renamed-file question for `mcp_06_09_startup-validation-behavior-tool_definitions_strict.md` is left out of scope; its content is updated and a later rename uses `tools/rename_doc.py`.
- Overlap with other Frozen Plans (`tools/check_plan_target_overlaps.py`, Step 8b), judged compatible: `config/agent.toml`, `scripts/agent/production_config_validator.py`, and `tests/agent/test_production_config_validator.py` are shared with the adrrev002 and adrrev003 Plans and edited at different keys (`eventbus_db_path`, `rag_identity_mismatch_policy`, versus the strict keys and `security_profile`); `docs/10_adr/adr_02_01_004_platform-environment-failure-handling-policy.md` is shared with adrrev003 and edited in different sections (Decision Group 10 fallback there, Decision Group 1 `path_denylist` exception here); `docs/23_agent/agent_10_01_operations-and-observability-startup-and-health.md` is shared with adrrev002 and edited in different paragraphs (archive retention note there, startup strictness here). Any order works.
- Re-verified 2026-11-10 against the procedure batches that already exist in `implementations/` and are not yet executed: `20261110-143149_*` (adrrev003) shares `config/agent.toml`, `scripts/agent/production_config_validator.py`, and `tests/agent/test_production_config_validator.py`, matching the statement above; its generated procedures contain no `docs/10_adr/adr_02_01_004_platform-environment-failure-handling-policy.md` row, so the ADR-004 sharing noted above no longer has a live counterpart. `20261110-135353_*` (adrrev006) shares two more targets this Plan had not listed: `docs/10_adr/adr_02_01_004_platform-environment-failure-handling-policy.md` (its Decision Group 7 / INV-09 row) and `docs/23_agent/agent_08_04_configuration-mcp-approval-obs.md` (its component-mandatoriness table). The edits are in different sections of both files (`## Exceptions` and the strict-key rows here), so the batches remain compatible in any order; running the adrrev006 batch first avoids rewriting the same ADR-004 file twice.

## Unknowns
| ID | Unknown Description | Evidence Missing | Resolution Path | Blocking? (True/False) |
|---|---|---|---|---|
| UNK-01 | The rationale text of the ADR-004 exception for an empty `path_denylist` | A maintainer statement | Phase 6 writes a marked pending exception record; the maintainer states the rationale, then the record is completed; the implementer does not write it | False |
| UNK-02 | Whether the base `MCPServer.health()` is deleted or made abstract | ~~A maintainer preference~~ | **Resolved 2026-11-10 (maintainer decision):** delete the base `health()` as the Plan assumes; no abstract method is introduced, and the servers keep their module-level `/health` handlers | False |
| UNK-03 | Production callers of `list_tools()`, `list_tools_with_server_key()`, and `health()` outside `scripts/` and `tests/` (operator tools, notebooks) | Out-of-repository usage | `rg` found none in the repository; the Issue's stop rule applies if one is reported | False |
| UNK-04 | Whether the reload path rejects an empty `allowed_tools` through any other check | ~~Only `prepare_validated_section` was read at the call level~~ | **Resolved 2026-11-10:** `scripts/agent/services/config_section_reload.py` contains no `ProductionConfigValidator` call and no tool-section validator tests `allowed_tools` emptiness (the key appears only as `config_field_registry.py:80`), so the reload path does not fail closed today and the runtime deny-all of REQ-002 is the enforcement point; the Phase 4 reload test stays as regression coverage | False |
| UNK-05 | How many test fixtures rely on the empty default `allowed_tools`/`allowed_root` | A full run after the change | Phase 4 runs `uv run pytest tests/agent tests/shared tests/integration` and updates the fixtures listed in the target table; new fixture files are a Plan amendment | False |

## Affected areas
| File | Change | Blast Radius | Churn (30d) | Bus Factor | deploy.sh Impact |
|---|---|---|---|---|---|
| `scripts/agent/production_config_validator.py` | modify | High | N/A | N/A | not applicable (rsynced) |
| `scripts/agent/startup_validation.py` | modify | High | N/A | N/A | not applicable (rsynced) |
| `scripts/agent/services/mcp_tool_discovery.py` | modify | High | N/A | N/A | not applicable (rsynced) |
| `scripts/agent/services/config_field_registry.py` | modify | Medium | N/A | N/A | not applicable (rsynced) |
| `scripts/agent/config_builders.py` | modify | High | N/A | N/A | not applicable (rsynced) |
| `scripts/agent/config_dataclasses.py` | modify | High | N/A | N/A | not applicable (rsynced) |
| `scripts/agent/config_section_builders.py` | modify | Medium | N/A | N/A | not applicable (rsynced) |
| `scripts/agent/commands/cmd_config_display.py` | modify | Low | N/A | N/A | not applicable (rsynced) |
| `scripts/agent/tool_policy.py` | modify | High | N/A | N/A | not applicable (rsynced) |
| `scripts/shared/mcp_config.py` | modify | Medium | N/A | N/A | not applicable (rsynced) |
| `scripts/mcp_servers/server.py` | modify | High | N/A | N/A | not applicable (rsynced) |
| `scripts/mcp_servers/mdq/mdq_server.py` | modify | Low | N/A | N/A | not applicable (rsynced) |
| `scripts/mcp_servers/git/git_models.py` | modify | Medium | N/A | N/A | not applicable (rsynced) |
| `scripts/mcp_servers/git/repository_state.py` | modify | Medium | N/A | N/A | not applicable (rsynced) |
| `scripts/mcp_servers/github/github_models_config.py` | modify | Medium | N/A | N/A | not applicable (rsynced) |
| `scripts/mcp_servers/github/github_service_security.py` | modify | Medium | N/A | N/A | not applicable (rsynced) |
| `config/agent.toml` | modify | Medium | N/A | N/A | not applicable (rsynced) |
| `config/github_mcp_server.toml` | modify | Low | N/A | N/A | not applicable (rsynced) |
| `tests/agent/test_production_config_validator.py` | modify | High | N/A | N/A | not applicable (rsynced) |
| `tests/agent/test_config_builders.py` | modify | Medium | N/A | N/A | not applicable (rsynced) |
| `tests/agent/services/test_mcp_tool_discovery.py` | modify | Medium | N/A | N/A | not applicable (rsynced) |
| `tests/agent/test_startup_mcp_lifecycle.py` | modify | Low | N/A | N/A | not applicable (rsynced) |
| `tests/integration/test_production_security_regression.py` | modify | Medium | N/A | N/A | not applicable (rsynced) |
| `tests/agent/test_startup_severity_classification.py` | modify | Low | N/A | N/A | not applicable (rsynced) |
| `tests/agent/test_startup.py` | modify | Low | N/A | N/A | not applicable (rsynced) |
| `tests/agent/shared/test_startup_validation_pipeline.py` | modify | Low | N/A | N/A | not applicable (rsynced) |
| `tests/agent/test_agent_negative_paths.py` | modify | Low | N/A | N/A | not applicable (rsynced) |
| `tests/mcp_servers/test_mcp_server_base.py` | modify | Low | N/A | N/A | not applicable (rsynced) |
| `tests/agent/test_startup_memory_failures.py` | modify | Low | N/A | N/A | not applicable (rsynced) |
| `tests/shared/test_mcp_config.py` | modify | Low | N/A | N/A | not applicable (rsynced) |
| `tests/agent/test_startup_validation.py` | modify | Low | N/A | N/A | not applicable (rsynced) |
| `tests/agent/test_config_dataclasses.py` | modify | Low | N/A | N/A | not applicable (rsynced) |
| `tests/agent/test_startup_mcp_starter.py` | modify | Low | N/A | N/A | not applicable (rsynced) |
| `tests/shared/test_config_loader.py` | modify | Low | N/A | N/A | not applicable (rsynced) |
| `tests/mcp_servers/mdq/test_mdq_routing.py` | modify | Low | N/A | N/A | not applicable (rsynced) |
| `tests/agent/services/test_config_reload.py` | modify | Medium | N/A | N/A | not applicable (rsynced) |
| `tests/agent/_config_test_defaults.py` | modify | Medium | N/A | N/A | not applicable (rsynced) |
| `tests/shared/test_shared_boundary_conditions.py` | modify | Low | N/A | N/A | not applicable (rsynced) |
| `tests/agent/test_tool_policy_comprehensive.py` | modify | Low | N/A | N/A | not applicable (rsynced) |
| `tests/agent/test_startup_rollback.py` | modify | Low | N/A | N/A | not applicable (rsynced) |
| `tests/agent/test_startup_config_error.py` | modify | Low | N/A | N/A | not applicable (rsynced) |
| `tests/agent/services/test_runtime_tool_routing_integration.py` | modify | Low | N/A | N/A | not applicable (rsynced) |
| `tests/integration/test_agent_integration.py` | modify | Low | N/A | N/A | not applicable (rsynced) |
| `tests/agent/services/test_mcp_tool_discovery_posture_gate.py` | modify | Low | N/A | N/A | not applicable (rsynced) |
| `tests/agent/test_tool_policy.py` | modify | Medium | N/A | N/A | not applicable (rsynced) |
| `tests/agent/test_tool_approval_preflight.py` | modify | Low | N/A | N/A | not applicable (rsynced) |
| `tests/agent/test_tool_approval_paths.py` | modify | Low | N/A | N/A | not applicable (rsynced) |
| `tests/agent/test_agent_repl_tool_exec.py` | modify | Low | N/A | N/A | not applicable (rsynced) |
| `tests/shared/test_runtime_tool_registry.py` | modify | Low | N/A | N/A | not applicable (rsynced) |
| `tests/shared/test_tool_routing_validation.py` | modify | Low | N/A | N/A | not applicable (rsynced) |
| `tests/mcp_servers/test_require_auth_token.py` | modify | Low | N/A | N/A | not applicable (rsynced) |
| `tests/mcp_servers/git/test_git_models.py` | modify | Low | N/A | N/A | not applicable (rsynced) |
| `tests/mcp_servers/git/test_repository_state.py` | modify | Low | N/A | N/A | not applicable (rsynced) |
| `tests/mcp_servers/github/test_service_security.py` | modify | Low | N/A | N/A | not applicable (rsynced) |
| `tests/mcp_servers/github/test_github_security_validation.py` | modify | Low | N/A | N/A | not applicable (rsynced) |
| `tests/mcp_servers/github/test_github_health_posture.py` | modify | Low | N/A | N/A | not applicable (rsynced) |
| `docs/22_mcp/mcp_06_09_startup-validation-behavior-tool_definitions_strict.md` | modify | Low | N/A | N/A | not applicable (rsynced) |
| `docs/22_mcp/mcp_06_01_configuration-file-inventory.md` | modify | Low | N/A | N/A | not applicable (rsynced) |
| `docs/22_mcp/mcp_05_03_fail-open-fail-closed-and-risk-tiers.md` | modify | Low | N/A | N/A | not applicable (rsynced) |
| `docs/22_mcp/mcp_06_13_pre-production-fail-open-checklist.md` | modify | Low | N/A | N/A | not applicable (rsynced) |
| `docs/22_mcp/mcp_06_03_long-running-http-operation-startup_modesubprocess.md` | modify | Low | N/A | N/A | not applicable (rsynced) |
| `docs/22_mcp/mcp_05_02_auth-profiles-and-sandboxing.md` | modify | Low | N/A | N/A | not applicable (rsynced) |
| `docs/22_mcp/mcp_03_02_tool-registry.md` | modify | Low | N/A | N/A | not applicable (rsynced) |
| `docs/22_mcp/mcp_06_11_new-tool-registration-procedure.md` | modify | Low | N/A | N/A | not applicable (rsynced) |
| `docs/22_mcp/mcp_06_08_settings-with-high-operational-impact.md` | modify | Low | N/A | N/A | not applicable (rsynced) |
| `docs/22_mcp/mcp_02_01_endpoints-and-transport.md` | modify | Low | N/A | N/A | not applicable (rsynced) |
| `docs/23_agent/agent_10_01_operations-and-observability-startup-and-health.md` | modify | Low | N/A | N/A | not applicable (rsynced) |
| `docs/23_agent/agent_08_04_configuration-mcp-approval-obs.md` | modify | Low | N/A | N/A | not applicable (rsynced) |
| `docs/23_agent/agent_08_03_configuration-tools-memory.md` | modify | Low | N/A | N/A | not applicable (rsynced) |
| `docs/23_agent/agent_08_01_configuration-loading-agent-config.md` | modify | Low | N/A | N/A | not applicable (rsynced) |
| `docs/10_adr/adr_02_02_003_agent-runtime-tool-registry-routing-authority.md` | modify | Low | N/A | N/A | not applicable (rsynced) |
| `docs/10_adr/adr_02_01_004_platform-environment-failure-handling-policy.md` | modify | Low | N/A | N/A | not applicable (rsynced) |
| `docs/10_adr/adr_02_01_002_platform-config-isolation.md` | modify | Low | N/A | N/A | not applicable (rsynced) |
| `docs/01_overview/overview_02_files.md` | modify | Low | N/A | N/A | not applicable (rsynced) |
| `scripts/shared/runtime_tool_registry.py` | Modify | Not assessed (amendment 2026-11-10) | N/A | N/A | Not assessed (amendment 2026-11-10) |
| `tests/agent/commands/test_cmd_config_char.py` | Modify | Not assessed (amendment 2026-11-10) | N/A | N/A | Not assessed (amendment 2026-11-10) |
| `tests/agent/commands/test_agent_cmd_config.py` | Modify | Not assessed (amendment 2026-11-10) | N/A | N/A | Not assessed (amendment 2026-11-10) |
| `tests/tools/test_check_docs_quality.py` | Modify | Not assessed (amendment 2026-11-10) | N/A | N/A | Not assessed (amendment 2026-11-10) |
| `tests/mcp_servers/github/test_github_mcp_service.py` | Modify | Not assessed (amendment 2026-11-10) | N/A | N/A | Not assessed (amendment 2026-11-10) |
| `tests/agent/test_tool_approval_repos.py` | Modify | Not assessed (amendment 2026-11-10) | N/A | N/A | Not assessed (amendment 2026-11-10) |
| `tests/agent/test_tool_approval_risk.py` | Modify | Not assessed (amendment 2026-11-10) | N/A | N/A | Not assessed (amendment 2026-11-10) |
| `tests/agent/test_tool_runner.py` | Modify | Not assessed (amendment 2026-11-10) | N/A | N/A | Not assessed (amendment 2026-11-10) |
| `tests/integration/test_rag_turn_integration.py` | Modify | Not assessed (amendment 2026-11-10) | N/A | N/A | Not assessed (amendment 2026-11-10) |
| `docs/40_shared/shared_01_overview.md` | Modify | Not assessed (amendment 2026-11-10) | N/A | N/A | Not assessed (amendment 2026-11-10) |
| `docs/40_shared/shared_03_03_runtime_and_execution-llm-and-mcp-clients.md` | Modify | Not assessed (amendment 2026-11-10) | N/A | N/A | Not assessed (amendment 2026-11-10) |
| `docs/91_security/security_01_architecture-and-trust-boundaries.md` | Modify | Not assessed (amendment 2026-11-10) | N/A | N/A | Not assessed (amendment 2026-11-10) |
| `docs/91_security/security_02_high-risk-tool-common-policy.md` | Modify | Not assessed (amendment 2026-11-10) | N/A | N/A | Not assessed (amendment 2026-11-10) |
| `docs/23_agent/agent_06_02_tool-execution-and-approval-approval.md` | Modify | Not assessed (amendment 2026-11-10) | N/A | N/A | Not assessed (amendment 2026-11-10) |
| `docs/23_agent/agent_06_03_tool-execution-and-approval-concurrency-safety.md` | Modify | Not assessed (amendment 2026-11-10) | N/A | N/A | Not assessed (amendment 2026-11-10) |
| `docs/22_mcp/mcp_04_05_git.md` | Modify | Not assessed (amendment 2026-11-10) | N/A | N/A | Not assessed (amendment 2026-11-10) |
| `docs/22_mcp/mcp_05_01_access-control-and-allowlists.md` | Modify | Not assessed (amendment 2026-11-10) | N/A | N/A | Not assessed (amendment 2026-11-10) |
| `tests/agent/test_repository_gateway.py` | Modify | Not assessed (amendment 2026-11-10) | N/A | N/A | Not assessed (amendment 2026-11-10) |
| `tests/agent/test_tool_audit.py` | Modify | Not assessed (amendment 2026-11-10) | N/A | N/A | Not assessed (amendment 2026-11-10) |

## Design
- **Approach**: remove optionality leaf-first, in testable steps. Phase 1 removes the strict toggles; Phase 2 the `MCPServer` bypass and helpers; Phase 3 `security_profile`; Phase 4 the empty-list denials (the largest fixture blast, so it runs after the removals shrink the surface); Phase 5 the shared empty-token test and server-config rejections are folded into Phases 2 and 4; Phase 6 ADRs and documents; Phase 7 verification and deploy hand-off. Alternatives rejected: keeping `*_strict` as always-true flags (still optionality in the schema) and rejecting empty `allowed_tools` only at load (the reload path would stay open).
- **Compatibility impact**: an `agent.toml` containing `tool_definitions_strict`, `routing_drift_strict`, `security_profile`, or an empty `allowed_root` fails to load; the shipped `config/agent.toml` loses the two strict keys in the same change and keeps `allowed_root = "/opt/llm"`. A git or github config with an empty `protected_branches` fails to load; both shipped configs are non-empty. `path_denylist = []` stays valid under the exception.
- **Consumer scan** (`tools/scan_change_consumers.py` over `tool_definitions_strict`, `routing_drift_strict`, `security_profile`, `accept_all_for_tests`, `list_tools_with_server_key`): reconciled with `rg` counts (tests: 30 files; scripts: 12 files; docs: 17 files); every consumer found is a target row; `not affected`: `tests/rag/ingestion/test_pipeline_utils_strict.py` and `tests/tools/test_check_docs_quality.py` (unrelated `_strict` text). The scan lists candidates only (text search).
- **Path B analysis** (Step 5): architecture: `PYTHONPATH=scripts uv run lint-imports` (6 contracts kept); removing members does not add imports. Dependency graph: `attach_auth_middleware` callers are the ten server modules and three test files; `SecurityProfile` is defined in `shared/mcp_config.py` and used in four `scripts/agent/` modules. Historical: churn not measured (`N/A`). Operational: no port change; the MCP servers and the Agent restart on deploy; `ss`, `fuser`, `pip-audit` not run (no dependency change). Persisted schema check: not applicable.
- **Validation quality baseline**: `vulture scripts/ --min-confidence 80` reports nothing in the target modules; `bandit`: 3 High pre-existing in `scripts/eventbus`; `radon` and diff-cover `N/A: no code diff yet`; implementation raises diff coverage to the `rules/toolchain.md` threshold.
- **Path classification**: Path B (more than 3 files; changes runtime configuration and a shared interface).

## Implementation steps
1. **Phase 1: Remove the strict toggles**
   - [ ] Remove the two keys and every non-strict branch from `scripts/agent/startup_validation.py`, `scripts/agent/services/mcp_tool_discovery.py`, `scripts/agent/config_dataclasses.py`, `scripts/agent/config_section_builders.py`, `scripts/agent/services/config_field_registry.py`, `scripts/agent/production_config_validator.py`, `scripts/agent/commands/cmd_config_display.py`, `config/agent.toml`, and update the strict-related tests of the target table (REQ-001).
   - [ ] Modify: Drop the tool_def_strict display expectation (REQ-001; `tests/agent/commands/test_cmd_config_char.py`) — amendment 2026-11-10
   - [ ] Modify: Drop the tool_definitions_strict fixture assignment (REQ-001; `tests/agent/commands/test_agent_cmd_config.py`) — amendment 2026-11-10
   - [ ] Modify: Stop importing STRICT_PRODUCTION_OVERRIDES (REQ-001; `tests/agent/test_repository_gateway.py`) — amendment 2026-11-10
   - [ ] Modify: Stop importing STRICT_PRODUCTION_OVERRIDES (REQ-001; `tests/agent/test_tool_audit.py`) — amendment 2026-11-10
2. **Phase 2: Remove the test-only bypass and unused helpers**
   - [ ] Remove `accept_all_for_tests`, `list_tools`, `list_tools_with_server_key`, and `health()` from `scripts/mcp_servers/server.py`; reword `scripts/mcp_servers/mdq/mdq_server.py`; update `tests/mcp_servers/test_mcp_server_base.py`, `tests/mcp_servers/mdq/test_mdq_routing.py`; derive the server list in `tests/mcp_servers/test_require_auth_token.py` from `config/agent.toml` (REQ-005, REQ-006).
3. **Phase 3: Remove `security_profile`**
   - [ ] Remove it from `scripts/shared/mcp_config.py`, `scripts/agent/config_builders.py`, `scripts/agent/config_dataclasses.py`, `scripts/agent/services/config_field_registry.py`, `scripts/agent/production_config_validator.py`; delete the profile regression in `tests/integration/test_production_security_regression.py`; update `tests/shared/test_mcp_config.py` and the builder tests (REQ-007).
   - [ ] Modify: Reword the fixture line that names SecurityProfile (REQ-007; `tests/tools/test_check_docs_quality.py`) — amendment 2026-11-10
4. **Phase 4: Fail-closed safety lists**
   - [ ] Add the reload test, then make `scripts/agent/tool_policy.py` deny on an empty `allowed_tools` and stop skipping the path check for an empty `allowed_root`; reject an empty `allowed_root` in `scripts/agent/config_section_builders.py`/`scripts/agent/production_config_validator.py`; reject an empty `protected_branches` in `scripts/mcp_servers/git/git_models.py` and `scripts/mcp_servers/github/github_models_config.py` and remove the skip branches in `scripts/mcp_servers/git/repository_state.py` and `scripts/mcp_servers/github/github_service_security.py`; mark `config/github_mcp_server.toml`; update the fixtures and tests of the target table (REQ-002, REQ-003, REQ-004). Run `uv run pytest tests/agent tests/shared tests/integration tests/mcp_servers -v`.
   - [ ] Modify: apply_policy denies every tool for an empty allowed_tools (REQ-002; `scripts/shared/runtime_tool_registry.py`) — amendment 2026-11-10
   - [ ] Modify: Replace the empty-protected_branches skip test (REQ-004; `tests/mcp_servers/github/test_github_mcp_service.py`) — amendment 2026-11-10
   - [ ] Modify: Supply a non-empty allowed_tools where the default was relied on (REQ-002; `tests/agent/test_tool_approval_repos.py`) — amendment 2026-11-10
   - [ ] Modify: Supply a non-empty allowed_tools where the default was relied on (REQ-002; `tests/agent/test_tool_approval_risk.py`) — amendment 2026-11-10
   - [ ] Modify: Supply a non-empty allowed_tools where the default was relied on (REQ-002; `tests/agent/test_tool_runner.py`) — amendment 2026-11-10
   - [ ] Modify: Supply a non-empty allowed_tools where the default was relied on (REQ-002; `tests/integration/test_rag_turn_integration.py`) — amendment 2026-11-10
5. **Phase 5: Consolidated test pass**
   - [ ] Run the whole affected test set once and fix remaining fixtures in the files of the target table only; any other file is a Plan amendment (UNK-05) (REQ-009).
6. **Phase 6: ADRs and documents (ADR-004 rationale after the maintainer's statement)**
   - [ ] Update the documents of the target table and register the pending ADR-004 `path_denylist` exception (REQ-004, REQ-008).
   - [ ] Modify: Update SecurityProfile wording (REQ-008; `docs/40_shared/shared_01_overview.md`) — amendment 2026-11-10
   - [ ] Modify: Update SecurityProfile wording (REQ-008; `docs/40_shared/shared_03_03_runtime_and_execution-llm-and-mcp-clients.md`) — amendment 2026-11-10
   - [ ] Modify: Update SecurityProfile wording (REQ-008; `docs/91_security/security_01_architecture-and-trust-boundaries.md`) — amendment 2026-11-10
   - [ ] Modify: Update SecurityProfile and protected_branches fail-open wording (REQ-008; `docs/91_security/security_02_high-risk-tool-common-policy.md`) — amendment 2026-11-10
   - [ ] Modify: Update empty allowed_tools/allowed_root wording (REQ-008; `docs/23_agent/agent_06_02_tool-execution-and-approval-approval.md`) — amendment 2026-11-10
   - [ ] Modify: Update empty allowed_tools/allowed_root wording (REQ-008; `docs/23_agent/agent_06_03_tool-execution-and-approval-concurrency-safety.md`) — amendment 2026-11-10
   - [ ] Modify: Update empty protected_branches wording (REQ-008; `docs/22_mcp/mcp_04_05_git.md`) — amendment 2026-11-10
   - [ ] Modify: Update empty protected_branches and the path_denylist exception wording (REQ-008; `docs/22_mcp/mcp_05_01_access-control-and-allowlists.md`) — amendment 2026-11-10
7. **Phase 7: Deployment and verification**
   - [ ] Run the full validation sequence in `rules/toolchain.md`; after the change is committed and pushed (the user's decision), hand off to `skills/deploy/SKILL.md` because `scripts/` and `config/` changed (REQ-009; `config/agent.toml`, `config/github_mcp_server.toml`).

### Release units
**Unit**: strict-only-startup | **Phases**: 1 | **Reason**: removing the dataclass fields and builder reads breaks every fixture and test that sets the keys until the matching test updates land in the same change; the sub-tasks of Phase 1 cannot be validated alone.

## Validation plan
| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| `scripts/agent/`, `scripts/shared/`, `scripts/mcp_servers/` | Unit, integration, regression | `uv run pytest tests/agent tests/shared tests/integration tests/mcp_servers -v` | All pass |
| Removed-key and empty-list rejection | Unit | the tests listed under Tests | Rejected / denied as specified |
| Whole repository | Full validation sequence | `rules/toolchain.md`: ruff format/check, `uv run mypy --no-namespace-packages scripts/ tests/eventbus tools`, `PYTHONPATH=scripts uv run lint-imports`, bandit, full `uv run pytest`, `tests/mcp_servers/mdq/test_mdq_rag_boundary.py` | No new findings; all pass |
| Impact radius | Search | `rg -l 'security_profile|SecurityProfile|_strict|attach_auth_middleware' tests/ scripts/` before removal; AC-01, AC-05..07 greps after | Every hit reviewed; none remain |
| Compat shims | Repository check | `uv run python tools/check_compat_shims.py` | Passes |
| Documents | Documentation checks | `check_docs_quality.py`, `check_docs_structure.py`, `check_docs_content_policy.py --strict`, `check_docs_consistency.py --domain mcp|agent`, `check_adr_authority.py`, `check_adr_preservation.py` | Pass |
| Diff coverage | Coverage | `rules/toolchain.md` section 7 sequence | At or above the Completion checklist threshold |

## Risks
- **Risk**: A deployed `/opt/llm/config/agent.toml` still has a removed key, so the Agent refuses to start → **Mitigation**: deploy copies the repository `agent.toml` with the scripts; `git revert` rollback; confirm before deploy.
- **Risk**: Denying on an empty `allowed_tools` breaks fixtures and tools that relied on the empty default → **Mitigation**: Phase 4 reload test first, fixtures listed in the target table, UNK-05 full-run bound.
- **Risk**: Rejecting an empty `allowed_root` or `protected_branches` makes an operator's local config unstartable → **Mitigation**: both shipped configs are non-empty; the error names the key; documented in `mcp_06_01`.
- **Risk**: The ADR-004 exception is written without the maintainer's rationale → **Mitigation**: Phase 6 gate; pending marker; no text invented.
- **Risk**: `check_adr_preservation.py` reports a change on the ADR-004 amendment → **Mitigation**: the exception is the approved intent; record the finding.
- **Risk**: Removing `health()` from the base class breaks an unseen caller → **Mitigation**: UNK-02 and UNK-03; the base class is restored as abstract if the maintainer prefers.
- **Risk**: 74 target files make the change large and hard to review → **Mitigation**: each phase leaves the suite green and is independently revertable; the release unit is limited to Phase 1.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Remove the strict toggles | In Progress | — | — |  |
| 2 | Remove the test-only bypass and unused helpers | In Progress | — | — |  |
| 3 | Remove `security_profile` | In Progress | — | — |  |
| 4 | Fail-closed safety lists | In Progress | — | — |  |
| 5 | Consolidated test pass | Pending | — | — |  |
| 6 | ADRs and documents (ADR-004 rationale after the maintainer's statement) | In Progress | — | — |  |
| 7 | Deployment and verification | Pending | — | — |  |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| — | — | — | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| `implementations/20261110-154603_01_scripts_agent_production_config_validator.py.md` | 1,3,4 | Procedure | Pending | — | — |
| `implementations/20261110-154603_02_scripts_agent_startup_validation.py.md` | 1 | Procedure | Pending | — | — |
| `implementations/20261110-154603_03_scripts_agent_services_mcp_tool_discovery.py.md` | 1 | Procedure | Pending | — | — |
| `implementations/20261110-154603_04_scripts_agent_services_config_field_registry.py.md` | 1,3 | Procedure | Pending | — | — |
| `implementations/20261110-154603_05_scripts_agent_config_builders.py.md` | 3 | Procedure | Pending | — | — |
| `implementations/20261110-154603_06_scripts_agent_config_dataclasses.py.md` | 1,3 | Procedure | Pending | — | — |
| `implementations/20261110-154603_07_scripts_agent_config_section_builders.py.md` | 1,4 | Procedure | Pending | — | — |
| `implementations/20261110-154603_08_scripts_agent_commands_cmd_config_display.py.md` | 1 | Procedure | Pending | — | — |
| `implementations/20261110-154603_09_scripts_agent_tool_policy.py.md` | 4 | Procedure | Pending | — | — |
| `implementations/20261110-154603_10_scripts_shared_mcp_config.py.md` | 3 | Procedure | Pending | — | — |
| `implementations/20261110-154603_11_scripts_mcp_servers_server.py.md` | 2 | Procedure | Pending | — | — |
| `implementations/20261110-154603_12_scripts_mcp_servers_mdq_mdq_server.py.md` | 2 | Procedure | Pending | — | — |
| `implementations/20261110-154603_13_scripts_mcp_servers_git_git_models.py.md` | 4 | Procedure | Pending | — | — |
| `implementations/20261110-154603_14_scripts_mcp_servers_git_repository_state.py.md` | 4 | Procedure | Pending | — | — |
| `implementations/20261110-154603_15_scripts_mcp_servers_github_github_models_config.py.md` | 4 | Procedure | Pending | — | — |
| `implementations/20261110-154603_16_scripts_mcp_servers_github_github_service_security.py.md` | 4 | Procedure | Pending | — | — |
| `implementations/20261110-154603_17_config_agent.toml.md` | 1,2,7 | Procedure | Pending | — | — |
| `implementations/20261110-154603_18_config_github_mcp_server.toml.md` | 4,7 | Procedure | Pending | — | — |
| `implementations/20261110-154603_19_tests_agent_test_production_config_validator.py.md` | 1 | Procedure | Pending | — | — |
| `implementations/20261110-154603_20_tests_agent_test_config_builders.py.md` | 1 | Procedure | Pending | — | — |
| `implementations/20261110-154603_22_tests_agent_test_startup_mcp_lifecycle.py.md` | 1 | Procedure | Pending | — | — |
| `implementations/20261110-154603_23_tests_integration_test_production_security_regression.py.md` | 3 | Procedure | Pending | — | — |
| `implementations/20261110-154603_24_tests_agent_test_startup_severity_classification.py.md` | 1 | Procedure | Pending | — | — |
| `implementations/20261110-154603_25_tests_agent_test_startup.py.md` | 1 | Procedure | Pending | — | — |
| `implementations/20261110-154603_27_tests_agent_test_agent_negative_paths.py.md` | 1 | Procedure | Pending | — | — |
| `implementations/20261110-154603_29_tests_agent_test_startup_memory_failures.py.md` | 1 | Procedure | Pending | — | — |
| `implementations/20261110-154603_33_tests_agent_test_startup_mcp_starter.py.md` | 1 | Procedure | Pending | — | — |
| `implementations/20261110-154603_34_tests_shared_test_config_loader.py.md` | 1 | Procedure | Pending | — | — |
| `implementations/20261110-154603_35_tests_mcp_servers_mdq_test_mdq_routing.py.md` | 2 | Procedure | Pending | — | — |
| `implementations/20261110-154603_36_tests_agent_services_test_config_reload.py.md` | 1 | Procedure | Pending | — | — |
| `implementations/20261110-154603_37_tests_agent__config_test_defaults.py.md` | 1 | Procedure | Pending | — | — |
| `implementations/20261110-154603_38_tests_shared_test_shared_boundary_conditions.py.md` | 1 | Procedure | Pending | — | — |
| `implementations/20261110-154603_40_tests_agent_test_startup_rollback.py.md` | 1 | Procedure | Pending | — | — |
| `implementations/20261110-154603_41_tests_agent_test_startup_config_error.py.md` | 1 | Procedure | Pending | — | — |
| `implementations/20261110-154603_42_tests_agent_services_test_runtime_tool_routing_integration.py.md` | 1 | Procedure | Pending | — | — |
| `implementations/20261110-154603_43_tests_integration_test_agent_integration.py.md` | 1 | Procedure | Pending | — | — |
| `implementations/20261110-154603_44_tests_agent_services_test_mcp_tool_discovery_posture_gate.py.md` | 1 | Procedure | Pending | — | — |
| `implementations/20261110-154603_46_tests_agent_test_tool_approval_preflight.py.md` | 1 | Procedure | Pending | — | — |
| `implementations/20261110-154603_47_tests_agent_test_tool_approval_paths.py.md` | 1 | Procedure | Pending | — | — |
| `implementations/20261110-154603_48_tests_agent_test_agent_repl_tool_exec.py.md` | 1 | Procedure | Pending | — | — |
| `implementations/20261110-154603_50_tests_shared_test_tool_routing_validation.py.md` | 1 | Procedure | Pending | — | — |
| `implementations/20261110-154603_51_tests_mcp_servers_test_require_auth_token.py.md` | 2 | Procedure | Pending | — | — |
| `implementations/20261110-154603_55_tests_mcp_servers_github_test_github_security_validation.py.md` | 1 | Procedure | Pending | — | — |
| `implementations/20261110-154603_57_docs_22_mcp_mcp_06_09_startup-validation-behavior-tool_definitions_strict.md.md` | 6 | Procedure | Pending | — | — |
| `implementations/20261110-154603_58_docs_22_mcp_mcp_06_01_configuration-file-inventory.md.md` | 6 | Procedure | Pending | — | — |
| `implementations/20261110-154603_59_docs_22_mcp_mcp_05_03_fail-open-fail-closed-and-risk-tiers.md.md` | 6 | Procedure | Pending | — | — |
| `implementations/20261110-154603_60_docs_22_mcp_mcp_06_13_pre-production-fail-open-checklist.md.md` | 6 | Procedure | Pending | — | — |
| `implementations/20261110-154603_61_docs_22_mcp_mcp_06_03_long-running-http-operation-startup_modesubprocess.md.md` | 6 | Procedure | Pending | — | — |
| `implementations/20261110-154603_62_docs_22_mcp_mcp_05_02_auth-profiles-and-sandboxing.md.md` | 6 | Procedure | Pending | — | — |
| `implementations/20261110-154603_63_docs_22_mcp_mcp_03_02_tool-registry.md.md` | 6 | Procedure | Pending | — | — |
| `implementations/20261110-154603_64_docs_22_mcp_mcp_06_11_new-tool-registration-procedure.md.md` | 6 | Procedure | Pending | — | — |
| `implementations/20261110-154603_65_docs_22_mcp_mcp_06_08_settings-with-high-operational-impact.md.md` | 6 | Procedure | Pending | — | — |
| `implementations/20261110-154603_66_docs_22_mcp_mcp_02_01_endpoints-and-transport.md.md` | 6 | Procedure | Pending | — | — |
| `implementations/20261110-154603_67_docs_23_agent_agent_10_01_operations-and-observability-startup-and-health.md.md` | 6 | Procedure | Pending | — | — |
| `implementations/20261110-154603_68_docs_23_agent_agent_08_04_configuration-mcp-approval-obs.md.md` | 6 | Procedure | Pending | — | — |
| `implementations/20261110-154603_69_docs_23_agent_agent_08_03_configuration-tools-memory.md.md` | 6 | Procedure | Pending | — | — |
| `implementations/20261110-154603_70_docs_23_agent_agent_08_01_configuration-loading-agent-config.md.md` | 6 | Procedure | Pending | — | — |
| `implementations/20261110-154603_71_docs_10_adr_adr_02_02_003_agent-runtime-tool-registry-routing-authority.md.md` | 6 | Procedure | Pending | — | — |
| `implementations/20261110-154603_72_docs_10_adr_adr_02_01_004_platform-environment-failure-handling-policy.md.md` | 6 | Procedure | Pending | — | — |
| `implementations/20261110-154603_73_docs_10_adr_adr_02_01_002_platform-config-isolation.md.md` | 6 | Procedure | Pending | — | — |
| `implementations/20261110-154603_74_docs_01_overview_overview_02_files.md.md` | 6 | Procedure | Pending | — | — |
| `implementations/20261110-154603_75_scripts_shared_runtime_tool_registry.py.md` | 4 | Procedure | Pending | — | — |
| `implementations/20261110-154603_78_tests_tools_test_check_docs_quality.py.md` | 3 | Procedure | Pending | — | — |
| `implementations/20261110-154603_79_tests_mcp_servers_github_test_github_mcp_service.py.md` | 4 | Procedure | Pending | — | — |
| `implementations/20261110-154603_80_tests_agent_test_tool_approval_repos.py.md` | 4 | Procedure | Pending | — | — |
| `implementations/20261110-154603_81_tests_agent_test_tool_approval_risk.py.md` | 4 | Procedure | Pending | — | — |
| `implementations/20261110-154603_82_tests_agent_test_tool_runner.py.md` | 4 | Procedure | Pending | — | — |
| `implementations/20261110-154603_83_tests_integration_test_rag_turn_integration.py.md` | 4 | Procedure | Pending | — | — |
| `implementations/20261110-154603_84_docs_40_shared_shared_01_overview.md.md` | 6 | Procedure | Pending | — | — |
| `implementations/20261110-154603_85_docs_40_shared_shared_03_03_runtime_and_execution-llm-and-mcp-clients.md.md` | 6 | Procedure | Pending | — | — |
| `implementations/20261110-154603_86_docs_91_security_security_01_architecture-and-trust-boundaries.md.md` | 6 | Procedure | Pending | — | — |
| `implementations/20261110-154603_87_docs_91_security_security_02_high-risk-tool-common-policy.md.md` | 6 | Procedure | Pending | — | — |
| `implementations/20261110-154603_88_docs_23_agent_agent_06_02_tool-execution-and-approval-approval.md.md` | 6 | Procedure | Pending | — | — |
| `implementations/20261110-154603_89_docs_23_agent_agent_06_03_tool-execution-and-approval-concurrency-safety.md.md` | 6 | Procedure | Pending | — | — |
| `implementations/20261110-154603_90_docs_22_mcp_mcp_04_05_git.md.md` | 6 | Procedure | Pending | — | — |
| `implementations/20261110-154603_91_docs_22_mcp_mcp_05_01_access-control-and-allowlists.md.md` | 6 | Procedure | Pending | — | — |
| `implementations/20261110-154603_92_tests_agent_test_repository_gateway.py.md` | 1 | Procedure | Pending | — | — |
| `implementations/20261110-154603_93_tests_agent_test_tool_audit.py.md` | 1 | Procedure | Pending | — | — |

## Traceability
- **Workflow phase**: issue-to-plan
- **Source issue**: issues/20261109-112640_adrrev004_non-strict-bypass-removal.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: this document is the generated plan
- **Source implementation procedure**: N/A: not applicable in this phase
- **Generated at**: 20261110-094140
- **Related target files**: `scripts/agent/production_config_validator.py`, `scripts/agent/startup_validation.py`, `scripts/agent/services/mcp_tool_discovery.py`, `scripts/agent/services/config_field_registry.py`, `scripts/agent/config_builders.py`, `scripts/agent/config_dataclasses.py`, `scripts/agent/config_section_builders.py`, `scripts/agent/commands/cmd_config_display.py`, `scripts/agent/tool_policy.py`, `scripts/shared/mcp_config.py`, `scripts/mcp_servers/server.py`, `scripts/mcp_servers/mdq/mdq_server.py`, `scripts/mcp_servers/git/git_models.py`, `scripts/mcp_servers/git/repository_state.py`, `scripts/mcp_servers/github/github_models_config.py`, `scripts/mcp_servers/github/github_service_security.py`, `config/agent.toml`, `config/github_mcp_server.toml`, `tests/agent/test_production_config_validator.py`, `tests/agent/test_config_builders.py`, `tests/agent/services/test_mcp_tool_discovery.py`, `tests/agent/test_startup_mcp_lifecycle.py`, `tests/integration/test_production_security_regression.py`, `tests/agent/test_startup_severity_classification.py`, `tests/agent/test_startup.py`, `tests/agent/shared/test_startup_validation_pipeline.py`, `tests/agent/test_agent_negative_paths.py`, `tests/mcp_servers/test_mcp_server_base.py`, `tests/agent/test_startup_memory_failures.py`, `tests/shared/test_mcp_config.py`, `tests/agent/test_startup_validation.py`, `tests/agent/test_config_dataclasses.py`, `tests/agent/test_startup_mcp_starter.py`, `tests/shared/test_config_loader.py`, `tests/mcp_servers/mdq/test_mdq_routing.py`, `tests/agent/services/test_config_reload.py`, `tests/agent/_config_test_defaults.py`, `tests/shared/test_shared_boundary_conditions.py`, `tests/agent/test_tool_policy_comprehensive.py`, `tests/agent/test_startup_rollback.py`, `tests/agent/test_startup_config_error.py`, `tests/agent/services/test_runtime_tool_routing_integration.py`, `tests/integration/test_agent_integration.py`, `tests/agent/services/test_mcp_tool_discovery_posture_gate.py`, `tests/agent/test_tool_policy.py`, `tests/agent/test_tool_approval_preflight.py`, `tests/agent/test_tool_approval_paths.py`, `tests/agent/test_agent_repl_tool_exec.py`, `tests/shared/test_runtime_tool_registry.py`, `tests/shared/test_tool_routing_validation.py`, `tests/mcp_servers/test_require_auth_token.py`, `tests/mcp_servers/git/test_git_models.py`, `tests/mcp_servers/git/test_repository_state.py`, `tests/mcp_servers/github/test_service_security.py`, `tests/mcp_servers/github/test_github_security_validation.py`, `tests/mcp_servers/github/test_github_health_posture.py`, `docs/22_mcp/mcp_06_09_startup-validation-behavior-tool_definitions_strict.md`, `docs/22_mcp/mcp_06_01_configuration-file-inventory.md`, `docs/22_mcp/mcp_05_03_fail-open-fail-closed-and-risk-tiers.md`, `docs/22_mcp/mcp_06_13_pre-production-fail-open-checklist.md`, `docs/22_mcp/mcp_06_03_long-running-http-operation-startup_modesubprocess.md`, `docs/22_mcp/mcp_05_02_auth-profiles-and-sandboxing.md`, `docs/22_mcp/mcp_03_02_tool-registry.md`, `docs/22_mcp/mcp_06_11_new-tool-registration-procedure.md`, `docs/22_mcp/mcp_06_08_settings-with-high-operational-impact.md`, `docs/22_mcp/mcp_02_01_endpoints-and-transport.md`, `docs/23_agent/agent_10_01_operations-and-observability-startup-and-health.md`, `docs/23_agent/agent_08_04_configuration-mcp-approval-obs.md`, `docs/23_agent/agent_08_03_configuration-tools-memory.md`, `docs/23_agent/agent_08_01_configuration-loading-agent-config.md`, `docs/10_adr/adr_02_02_003_agent-runtime-tool-registry-routing-authority.md`, `docs/10_adr/adr_02_01_004_platform-environment-failure-handling-policy.md`, `docs/10_adr/adr_02_01_002_platform-config-isolation.md`, `docs/01_overview/overview_02_files.md`, `scripts/shared/runtime_tool_registry.py`, `tests/agent/commands/test_cmd_config_char.py`, `tests/agent/commands/test_agent_cmd_config.py`, `tests/tools/test_check_docs_quality.py`, `tests/mcp_servers/github/test_github_mcp_service.py`, `tests/agent/test_tool_approval_repos.py`, `tests/agent/test_tool_approval_risk.py`, `tests/agent/test_tool_runner.py`, `tests/integration/test_rag_turn_integration.py`, `docs/40_shared/shared_01_overview.md`, `docs/40_shared/shared_03_03_runtime_and_execution-llm-and-mcp-clients.md`, `docs/91_security/security_01_architecture-and-trust-boundaries.md`, `docs/91_security/security_02_high-risk-tool-common-policy.md`, `docs/23_agent/agent_06_02_tool-execution-and-approval-approval.md`, `docs/23_agent/agent_06_03_tool-execution-and-approval-concurrency-safety.md`, `docs/22_mcp/mcp_04_05_git.md`, `docs/22_mcp/mcp_05_01_access-control-and-allowlists.md`, `tests/agent/test_repository_gateway.py`, `tests/agent/test_tool_audit.py`

### Requirement Traceability
| Requirement ID | Source Issue section or evidence | Target file | Implementation step | Acceptance criterion | Test or validation item | Status |
|---|---|---|---|---|---|---|
| REQ-001 | Required Changes / repository evidence | `scripts/agent/production_config_validator.py` | 1, 3, 5 | AC-01 | `tests/agent/test_production_config_validator.py` | Confirmed by repository evidence |
| REQ-003 | Required Changes / repository evidence | `scripts/agent/production_config_validator.py` | 1, 3, 5 | AC-03 | `tests/agent/test_production_config_validator.py` | Confirmed by repository evidence |
| REQ-007 | Required Changes / repository evidence | `scripts/agent/production_config_validator.py` | 1, 3, 5 | AC-07 | `tests/agent/test_production_config_validator.py` | Confirmed by repository evidence |
| REQ-001 | Required Changes / repository evidence | `scripts/agent/startup_validation.py` | 1 | AC-01 | `tests/agent/test_startup_validation.py`, `tests/agent/shared/test_startup_validation_pipeline.py` | Confirmed by repository evidence |
| REQ-001 | Required Changes / repository evidence | `scripts/agent/services/mcp_tool_discovery.py` | 1 | AC-01 | `tests/agent/services/test_mcp_tool_discovery.py` | Confirmed by repository evidence |
| REQ-001 | Required Changes / repository evidence | `scripts/agent/services/config_field_registry.py` | 1, 3 | AC-01 | `tests/agent/test_config_builders.py` | Confirmed by repository evidence |
| REQ-007 | Required Changes / repository evidence | `scripts/agent/services/config_field_registry.py` | 1, 3 | AC-07 | `tests/agent/test_config_builders.py` | Confirmed by repository evidence |
| REQ-007 | Required Changes / repository evidence | `scripts/agent/config_builders.py` | 3 | AC-07 | `tests/agent/test_config_builders.py` | Confirmed by repository evidence |
| REQ-001 | Required Changes / repository evidence | `scripts/agent/config_dataclasses.py` | 1, 3 | AC-01 | `tests/agent/test_config_dataclasses.py` | Confirmed by repository evidence |
| REQ-007 | Required Changes / repository evidence | `scripts/agent/config_dataclasses.py` | 1, 3 | AC-07 | `tests/agent/test_config_dataclasses.py` | Confirmed by repository evidence |
| REQ-001 | Required Changes / repository evidence | `scripts/agent/config_section_builders.py` | 1, 4 | AC-01 | `tests/agent/test_config_builders.py` | Confirmed by repository evidence |
| REQ-003 | Required Changes / repository evidence | `scripts/agent/config_section_builders.py` | 1, 4 | AC-03 | `tests/agent/test_config_builders.py` | Confirmed by repository evidence |
| REQ-001 | Required Changes / repository evidence | `scripts/agent/commands/cmd_config_display.py` | 1 | AC-01 | `tests/agent/commands/test_cmd_config_char.py`, `tests/agent/commands/test_agent_cmd_config.py` | Confirmed by repository evidence |
| REQ-002 | Required Changes / repository evidence | `scripts/agent/tool_policy.py` | 4 | AC-02 | `tests/agent/test_tool_policy.py`, `tests/agent/test_tool_policy_comprehensive.py` | Confirmed by repository evidence |
| REQ-003 | Required Changes / repository evidence | `scripts/agent/tool_policy.py` | 4 | AC-03 | `tests/agent/test_tool_policy.py`, `tests/agent/test_tool_policy_comprehensive.py` | Confirmed by repository evidence |
| REQ-007 | Required Changes / repository evidence | `scripts/shared/mcp_config.py` | 3 | AC-07 | `tests/shared/test_mcp_config.py` | Confirmed by repository evidence |
| REQ-005 | Required Changes / repository evidence | `scripts/mcp_servers/server.py` | 2 | AC-05 | `tests/mcp_servers/test_mcp_server_base.py`, `tests/mcp_servers/mdq/test_mdq_routing.py` | Confirmed by repository evidence |
| REQ-006 | Required Changes / repository evidence | `scripts/mcp_servers/server.py` | 2 | AC-06 | `tests/mcp_servers/test_mcp_server_base.py`, `tests/mcp_servers/mdq/test_mdq_routing.py` | Confirmed by repository evidence |
| REQ-006 | Required Changes / repository evidence | `scripts/mcp_servers/mdq/mdq_server.py` | 2 | AC-06 | `tests/mcp_servers/mdq/test_mdq_routing.py` | Confirmed by repository evidence |
| REQ-004 | Required Changes / repository evidence | `scripts/mcp_servers/git/git_models.py` | 4 | AC-04 | `tests/mcp_servers/git/test_git_models.py` | Confirmed by repository evidence |
| REQ-004 | Required Changes / repository evidence | `scripts/mcp_servers/git/repository_state.py` | 4 | AC-04 | `tests/mcp_servers/git/test_repository_state.py` | Confirmed by repository evidence |
| REQ-004 | Required Changes / repository evidence | `scripts/mcp_servers/github/github_models_config.py` | 4 | AC-04 | `tests/mcp_servers/github/test_service_security.py` | Confirmed by repository evidence |
| REQ-004 | Required Changes / repository evidence | `scripts/mcp_servers/github/github_service_security.py` | 4 | AC-04 | `tests/mcp_servers/github/test_github_security_validation.py`, `tests/mcp_servers/github/test_github_health_posture.py` | Confirmed by repository evidence |
| REQ-001 | Required Changes / repository evidence | `config/agent.toml` | 1 | AC-01 | `tests/agent/test_production_config_validator.py` | Confirmed by repository evidence |
| REQ-004 | Required Changes / repository evidence | `config/github_mcp_server.toml` | 4 | AC-04 | `tests/mcp_servers/github/test_github_security_validation.py` | Confirmed by repository evidence |
| REQ-001 | Required Changes / repository evidence | `tests/agent/test_production_config_validator.py` | 1-4 | AC-01 | `uv run pytest tests/agent/test_production_config_validator.py -v` | Confirmed by repository evidence |
| REQ-003 | Required Changes / repository evidence | `tests/agent/test_production_config_validator.py` | 1-4 | AC-03 | `uv run pytest tests/agent/test_production_config_validator.py -v` | Confirmed by repository evidence |
| REQ-007 | Required Changes / repository evidence | `tests/agent/test_production_config_validator.py` | 1-4 | AC-07 | `uv run pytest tests/agent/test_production_config_validator.py -v` | Confirmed by repository evidence |
| REQ-001 | Required Changes / repository evidence | `tests/agent/test_config_builders.py` | 1-4 | AC-01 | `uv run pytest tests/agent/test_config_builders.py -v` | Confirmed by repository evidence |
| REQ-007 | Required Changes / repository evidence | `tests/agent/test_config_builders.py` | 1-4 | AC-07 | `uv run pytest tests/agent/test_config_builders.py -v` | Confirmed by repository evidence |
| REQ-001 | Required Changes / repository evidence | `tests/agent/services/test_mcp_tool_discovery.py` | 1-4 | AC-01 | `uv run pytest tests/agent/services/test_mcp_tool_discovery.py -v` | Confirmed by repository evidence |
| REQ-001 | Required Changes / repository evidence | `tests/agent/test_startup_mcp_lifecycle.py` | 1-4 | AC-01 | `uv run pytest tests/agent/test_startup_mcp_lifecycle.py -v` | Confirmed by repository evidence |
| REQ-001 | Required Changes / repository evidence | `tests/integration/test_production_security_regression.py` | 1-4 | AC-01 | `uv run pytest tests/integration/test_production_security_regression.py -v` | Confirmed by repository evidence |
| REQ-001 | Required Changes / repository evidence | `tests/agent/test_startup_severity_classification.py` | 1-4 | AC-01 | `uv run pytest tests/agent/test_startup_severity_classification.py -v` | Confirmed by repository evidence |
| REQ-001 | Required Changes / repository evidence | `tests/agent/test_startup.py` | 1-4 | AC-01 | `uv run pytest tests/agent/test_startup.py -v` | Confirmed by repository evidence |
| REQ-001 | Required Changes / repository evidence | `tests/agent/shared/test_startup_validation_pipeline.py` | 1-4 | AC-01 | `uv run pytest tests/agent/shared/test_startup_validation_pipeline.py -v` | Confirmed by repository evidence |
| REQ-001 | Required Changes / repository evidence | `tests/agent/test_agent_negative_paths.py` | 1-4 | AC-01 | `uv run pytest tests/agent/test_agent_negative_paths.py -v` | Confirmed by repository evidence |
| REQ-005 | Required Changes / repository evidence | `tests/mcp_servers/test_mcp_server_base.py` | 1-4 | AC-05 | `uv run pytest tests/mcp_servers/test_mcp_server_base.py -v` | Confirmed by repository evidence |
| REQ-006 | Required Changes / repository evidence | `tests/mcp_servers/test_mcp_server_base.py` | 1-4 | AC-06 | `uv run pytest tests/mcp_servers/test_mcp_server_base.py -v` | Confirmed by repository evidence |
| REQ-001 | Required Changes / repository evidence | `tests/agent/test_startup_memory_failures.py` | 1-4 | AC-01 | `uv run pytest tests/agent/test_startup_memory_failures.py -v` | Confirmed by repository evidence |
| REQ-001 | Required Changes / repository evidence | `tests/shared/test_mcp_config.py` | 1-4 | AC-01 | `uv run pytest tests/shared/test_mcp_config.py -v` | Confirmed by repository evidence |
| REQ-007 | Required Changes / repository evidence | `tests/shared/test_mcp_config.py` | 1-4 | AC-07 | `uv run pytest tests/shared/test_mcp_config.py -v` | Confirmed by repository evidence |
| REQ-001 | Required Changes / repository evidence | `tests/agent/test_startup_validation.py` | 1-4 | AC-01 | `uv run pytest tests/agent/test_startup_validation.py -v` | Confirmed by repository evidence |
| REQ-001 | Required Changes / repository evidence | `tests/agent/test_config_dataclasses.py` | 1-4 | AC-01 | `uv run pytest tests/agent/test_config_dataclasses.py -v` | Confirmed by repository evidence |
| REQ-007 | Required Changes / repository evidence | `tests/agent/test_config_dataclasses.py` | 1-4 | AC-07 | `uv run pytest tests/agent/test_config_dataclasses.py -v` | Confirmed by repository evidence |
| REQ-001 | Required Changes / repository evidence | `tests/agent/test_startup_mcp_starter.py` | 1-4 | AC-01 | `uv run pytest tests/agent/test_startup_mcp_starter.py -v` | Confirmed by repository evidence |
| REQ-001 | Required Changes / repository evidence | `tests/shared/test_config_loader.py` | 1-4 | AC-01 | `uv run pytest tests/shared/test_config_loader.py -v` | Confirmed by repository evidence |
| REQ-006 | Required Changes / repository evidence | `tests/mcp_servers/mdq/test_mdq_routing.py` | 1-4 | AC-06 | `uv run pytest tests/mcp_servers/mdq/test_mdq_routing.py -v` | Confirmed by repository evidence |
| REQ-002 | Required Changes / repository evidence | `tests/agent/services/test_config_reload.py` | 1-4 | AC-02 | `uv run pytest tests/agent/services/test_config_reload.py -v` | Confirmed by repository evidence |
| REQ-003 | Required Changes / repository evidence | `tests/agent/services/test_config_reload.py` | 1-4 | AC-03 | `uv run pytest tests/agent/services/test_config_reload.py -v` | Confirmed by repository evidence |
| REQ-002 | Required Changes / repository evidence | `tests/agent/_config_test_defaults.py` | 1-4 | AC-02 | `uv run pytest tests/agent/_config_test_defaults.py -v` | Confirmed by repository evidence |
| REQ-003 | Required Changes / repository evidence | `tests/agent/_config_test_defaults.py` | 1-4 | AC-03 | `uv run pytest tests/agent/_config_test_defaults.py -v` | Confirmed by repository evidence |
| REQ-001 | Required Changes / repository evidence | `tests/shared/test_shared_boundary_conditions.py` | 1-4 | AC-01 | `uv run pytest tests/shared/test_shared_boundary_conditions.py -v` | Confirmed by repository evidence |
| REQ-001 | Required Changes / repository evidence | `tests/agent/test_tool_policy_comprehensive.py` | 1-4 | AC-01 | `uv run pytest tests/agent/test_tool_policy_comprehensive.py -v` | Confirmed by repository evidence |
| REQ-001 | Required Changes / repository evidence | `tests/agent/test_startup_rollback.py` | 1-4 | AC-01 | `uv run pytest tests/agent/test_startup_rollback.py -v` | Confirmed by repository evidence |
| REQ-001 | Required Changes / repository evidence | `tests/agent/test_startup_config_error.py` | 1-4 | AC-01 | `uv run pytest tests/agent/test_startup_config_error.py -v` | Confirmed by repository evidence |
| REQ-001 | Required Changes / repository evidence | `tests/agent/services/test_runtime_tool_routing_integration.py` | 1-4 | AC-01 | `uv run pytest tests/agent/services/test_runtime_tool_routing_integration.py -v` | Confirmed by repository evidence |
| REQ-001 | Required Changes / repository evidence | `tests/integration/test_agent_integration.py` | 1-4 | AC-01 | `uv run pytest tests/integration/test_agent_integration.py -v` | Confirmed by repository evidence |
| REQ-001 | Required Changes / repository evidence | `tests/agent/services/test_mcp_tool_discovery_posture_gate.py` | 1-4 | AC-01 | `uv run pytest tests/agent/services/test_mcp_tool_discovery_posture_gate.py -v` | Confirmed by repository evidence |
| REQ-002 | Required Changes / repository evidence | `tests/agent/test_tool_policy.py` | 1-4 | AC-02 | `uv run pytest tests/agent/test_tool_policy.py -v` | Confirmed by repository evidence |
| REQ-003 | Required Changes / repository evidence | `tests/agent/test_tool_policy.py` | 1-4 | AC-03 | `uv run pytest tests/agent/test_tool_policy.py -v` | Confirmed by repository evidence |
| REQ-002 | Required Changes / repository evidence | `tests/agent/test_tool_approval_preflight.py` | 1-4 | AC-02 | `uv run pytest tests/agent/test_tool_approval_preflight.py -v` | Confirmed by repository evidence |
| REQ-003 | Required Changes / repository evidence | `tests/agent/test_tool_approval_preflight.py` | 1-4 | AC-03 | `uv run pytest tests/agent/test_tool_approval_preflight.py -v` | Confirmed by repository evidence |
| REQ-002 | Required Changes / repository evidence | `tests/agent/test_tool_approval_paths.py` | 1-4 | AC-02 | `uv run pytest tests/agent/test_tool_approval_paths.py -v` | Confirmed by repository evidence |
| REQ-003 | Required Changes / repository evidence | `tests/agent/test_tool_approval_paths.py` | 1-4 | AC-03 | `uv run pytest tests/agent/test_tool_approval_paths.py -v` | Confirmed by repository evidence |
| REQ-002 | Required Changes / repository evidence | `tests/agent/test_agent_repl_tool_exec.py` | 1-4 | AC-02 | `uv run pytest tests/agent/test_agent_repl_tool_exec.py -v` | Confirmed by repository evidence |
| REQ-003 | Required Changes / repository evidence | `tests/agent/test_agent_repl_tool_exec.py` | 1-4 | AC-03 | `uv run pytest tests/agent/test_agent_repl_tool_exec.py -v` | Confirmed by repository evidence |
| REQ-002 | Required Changes / repository evidence | `tests/shared/test_runtime_tool_registry.py` | 1-4 | AC-02 | `uv run pytest tests/shared/test_runtime_tool_registry.py -v` | Confirmed by repository evidence |
| REQ-003 | Required Changes / repository evidence | `tests/shared/test_runtime_tool_registry.py` | 1-4 | AC-03 | `uv run pytest tests/shared/test_runtime_tool_registry.py -v` | Confirmed by repository evidence |
| REQ-002 | Required Changes / repository evidence | `tests/shared/test_tool_routing_validation.py` | 1-4 | AC-02 | `uv run pytest tests/shared/test_tool_routing_validation.py -v` | Confirmed by repository evidence |
| REQ-003 | Required Changes / repository evidence | `tests/shared/test_tool_routing_validation.py` | 1-4 | AC-03 | `uv run pytest tests/shared/test_tool_routing_validation.py -v` | Confirmed by repository evidence |
| REQ-005 | Required Changes / repository evidence | `tests/mcp_servers/test_require_auth_token.py` | 1-4 | AC-05 | `uv run pytest tests/mcp_servers/test_require_auth_token.py -v` | Confirmed by repository evidence |
| REQ-004 | Required Changes / repository evidence | `tests/mcp_servers/git/test_git_models.py` | 1-4 | AC-04 | `uv run pytest tests/mcp_servers/git/test_git_models.py -v` | Confirmed by repository evidence |
| REQ-001 | Required Changes / repository evidence | `tests/mcp_servers/git/test_repository_state.py` | 1-4 | AC-01 | `uv run pytest tests/mcp_servers/git/test_repository_state.py -v` | Confirmed by repository evidence |
| REQ-004 | Required Changes / repository evidence | `tests/mcp_servers/github/test_service_security.py` | 1-4 | AC-04 | `uv run pytest tests/mcp_servers/github/test_service_security.py -v` | Confirmed by repository evidence |
| REQ-001 | Required Changes / repository evidence | `tests/mcp_servers/github/test_github_security_validation.py` | 1-4 | AC-01 | `uv run pytest tests/mcp_servers/github/test_github_security_validation.py -v` | Confirmed by repository evidence |
| REQ-001 | Required Changes / repository evidence | `tests/mcp_servers/github/test_github_health_posture.py` | 1-4 | AC-01 | `uv run pytest tests/mcp_servers/github/test_github_health_posture.py -v` | Confirmed by repository evidence |
| REQ-008 | Required Changes / repository evidence | `docs/22_mcp/mcp_06_09_startup-validation-behavior-tool_definitions_strict.md` | 6 | AC-08 | `uv run python tools/check_docs_consistency.py --domain mcp` | Confirmed by repository evidence |
| REQ-008 | Required Changes / repository evidence | `docs/22_mcp/mcp_06_01_configuration-file-inventory.md` | 6 | AC-08 | `uv run python tools/check_docs_consistency.py --domain mcp` | Confirmed by repository evidence |
| REQ-008 | Required Changes / repository evidence | `docs/22_mcp/mcp_05_03_fail-open-fail-closed-and-risk-tiers.md` | 6 | AC-08 | `uv run python tools/check_docs_consistency.py --domain mcp` | Confirmed by repository evidence |
| REQ-008 | Required Changes / repository evidence | `docs/22_mcp/mcp_06_13_pre-production-fail-open-checklist.md` | 6 | AC-08 | `uv run python tools/check_docs_consistency.py --domain mcp` | Confirmed by repository evidence |
| REQ-008 | Required Changes / repository evidence | `docs/22_mcp/mcp_06_03_long-running-http-operation-startup_modesubprocess.md` | 6 | AC-08 | `uv run python tools/check_docs_consistency.py --domain mcp` | Confirmed by repository evidence |
| REQ-008 | Required Changes / repository evidence | `docs/22_mcp/mcp_05_02_auth-profiles-and-sandboxing.md` | 6 | AC-08 | `uv run python tools/check_docs_consistency.py --domain mcp` | Confirmed by repository evidence |
| REQ-008 | Required Changes / repository evidence | `docs/22_mcp/mcp_03_02_tool-registry.md` | 6 | AC-08 | `uv run python tools/check_docs_consistency.py --domain mcp` | Confirmed by repository evidence |
| REQ-008 | Required Changes / repository evidence | `docs/22_mcp/mcp_06_11_new-tool-registration-procedure.md` | 6 | AC-08 | `uv run python tools/check_docs_consistency.py --domain mcp` | Confirmed by repository evidence |
| REQ-008 | Required Changes / repository evidence | `docs/22_mcp/mcp_06_08_settings-with-high-operational-impact.md` | 6 | AC-08 | `uv run python tools/check_docs_consistency.py --domain mcp` | Confirmed by repository evidence |
| REQ-008 | Required Changes / repository evidence | `docs/22_mcp/mcp_02_01_endpoints-and-transport.md` | 6 | AC-08 | `uv run python tools/check_docs_consistency.py --domain mcp` | Confirmed by repository evidence |
| REQ-008 | Required Changes / repository evidence | `docs/23_agent/agent_10_01_operations-and-observability-startup-and-health.md` | 6 | AC-08 | `uv run python tools/check_docs_consistency.py --domain agent` | Confirmed by repository evidence |
| REQ-008 | Required Changes / repository evidence | `docs/23_agent/agent_08_04_configuration-mcp-approval-obs.md` | 6 | AC-08 | `uv run python tools/check_docs_consistency.py --domain agent` | Confirmed by repository evidence |
| REQ-008 | Required Changes / repository evidence | `docs/23_agent/agent_08_03_configuration-tools-memory.md` | 6 | AC-08 | `uv run python tools/check_docs_consistency.py --domain agent` | Confirmed by repository evidence |
| REQ-008 | Required Changes / repository evidence | `docs/23_agent/agent_08_01_configuration-loading-agent-config.md` | 6 | AC-08 | `uv run python tools/check_docs_consistency.py --domain agent` | Confirmed by repository evidence |
| REQ-008 | Required Changes / repository evidence | `docs/10_adr/adr_02_02_003_agent-runtime-tool-registry-routing-authority.md` | 6 | AC-08 | `uv run python tools/check_adr_preservation.py`, `check_adr_authority.py` | Confirmed by repository evidence |
| REQ-008 | Required Changes / repository evidence | `docs/10_adr/adr_02_01_004_platform-environment-failure-handling-policy.md` | 6 | AC-08 | `uv run python tools/check_adr_preservation.py`, `check_adr_authority.py` | Confirmed by repository evidence |
| REQ-008 | Required Changes / repository evidence | `docs/10_adr/adr_02_01_002_platform-config-isolation.md` | 6 | AC-08 | `uv run python tools/check_adr_preservation.py`, `check_adr_authority.py` | Confirmed by repository evidence |
| REQ-008 | Required Changes / repository evidence | `docs/01_overview/overview_02_files.md` | 6 | AC-08 | `uv run python tools/check_docs_consistency.py --domain overview` | Confirmed by repository evidence |
| REQ-002 | Amendment 2026-11-10: apply_policy (the /reload path via config_service_sync) re-enables every tool for an empty allowed_tools, so REQ-002 'including after /reload' needs this change | scripts/shared/runtime_tool_registry.py | Phase 4 | N/A: none cites REQ-002 | tests/shared/test_runtime_tool_registry.py | Confirmed by repository evidence |
| REQ-001 | Amendment 2026-11-10: Asserts the removed `tool_def_strict` display row (line 144) | tests/agent/commands/test_cmd_config_char.py | Phase 1 | N/A: none cites REQ-001 | uv run pytest tests/agent/commands/test_cmd_config_char.py -v | Confirmed by repository evidence |
| REQ-001 | Amendment 2026-11-10: Sets the removed `tool_definitions_strict` attribute (line 199) | tests/agent/commands/test_agent_cmd_config.py | Phase 1 | N/A: none cites REQ-001 | uv run pytest tests/agent/commands/test_agent_cmd_config.py -v | Confirmed by repository evidence |
| REQ-007 | Amendment 2026-11-10: A docs-quality fixture line contains `SecurityProfile` (line 477), which AC-07 requires to be absent from tests/ | tests/tools/test_check_docs_quality.py | Phase 3 | N/A: none cites REQ-007 | uv run pytest tests/tools/test_check_docs_quality.py -v | Confirmed by repository evidence |
| REQ-004 | Amendment 2026-11-10: Removing the skip-when-empty branch fails test_empty_protected_branches_skips_check_with_empty_branch (measured by experiment) | tests/mcp_servers/github/test_github_mcp_service.py | Phase 4 | N/A: none cites REQ-004 | uv run pytest tests/mcp_servers/github/test_github_mcp_service.py -v | Confirmed by repository evidence |
| REQ-002 | Amendment 2026-11-10: Fails under deny-on-empty allowed_tools (measured by experiment) | tests/agent/test_tool_approval_repos.py | Phase 4 | N/A: none cites REQ-002 | uv run pytest tests/agent/test_tool_approval_repos.py -v | Confirmed by repository evidence |
| REQ-002 | Amendment 2026-11-10: Fails under deny-on-empty allowed_tools (measured by experiment) | tests/agent/test_tool_approval_risk.py | Phase 4 | N/A: none cites REQ-002 | uv run pytest tests/agent/test_tool_approval_risk.py -v | Confirmed by repository evidence |
| REQ-002 | Amendment 2026-11-10: Fails under deny-on-empty allowed_tools (measured by experiment) | tests/agent/test_tool_runner.py | Phase 4 | N/A: none cites REQ-002 | uv run pytest tests/agent/test_tool_runner.py -v | Confirmed by repository evidence |
| REQ-002 | Amendment 2026-11-10: Fails under deny-on-empty allowed_tools (measured by experiment) | tests/integration/test_rag_turn_integration.py | Phase 4 | N/A: none cites REQ-002 | uv run pytest tests/integration/test_rag_turn_integration.py -v | Confirmed by repository evidence |
| REQ-008 | Amendment 2026-11-10: shared_01_overview.md:142 names `SecurityProfile` (AC-07/REQ-008 grep or fail-closed statement) | docs/40_shared/shared_01_overview.md | Phase 6 | N/A: none cites REQ-008 | uv run python tools/check_docs_consistency.py --domain overview | Confirmed by repository evidence |
| REQ-008 | Amendment 2026-11-10: shared_03_03:65 names `SecurityProfile` (AC-07/REQ-008 grep or fail-closed statement) | docs/40_shared/shared_03_03_runtime_and_execution-llm-and-mcp-clients.md | Phase 6 | N/A: none cites REQ-008 | uv run python tools/check_docs_consistency.py --domain overview | Confirmed by repository evidence |
| REQ-008 | Amendment 2026-11-10: security_01:128 names `SecurityProfile` (AC-07/REQ-008 grep or fail-closed statement) | docs/91_security/security_01_architecture-and-trust-boundaries.md | Phase 6 | N/A: none cites REQ-008 | uv run python tools/check_docs_consistency.py --domain overview | Confirmed by repository evidence |
| REQ-008 | Amendment 2026-11-10: security_02:142 names `SecurityProfile`; :174 calls protected_branches fail-open (AC-07/REQ-008 grep or fail-closed statement) | docs/91_security/security_02_high-risk-tool-common-policy.md | Phase 6 | N/A: none cites REQ-008 | uv run python tools/check_docs_consistency.py --domain overview | Confirmed by repository evidence |
| REQ-008 | Amendment 2026-11-10: agent_06_02:33-34 describes the empty allowed_tools and allowed_root skips (AC-07/REQ-008 grep or fail-closed statement) | docs/23_agent/agent_06_02_tool-execution-and-approval-approval.md | Phase 6 | N/A: none cites REQ-008 | uv run python tools/check_docs_consistency.py --domain agent | Confirmed by repository evidence |
| REQ-008 | Amendment 2026-11-10: agent_06_03:33-34 states empty allowed_tools allows all and empty allowed_root disables the jail (AC-07/REQ-008 grep or fail-closed statement) | docs/23_agent/agent_06_03_tool-execution-and-approval-concurrency-safety.md | Phase 6 | N/A: none cites REQ-008 | uv run python tools/check_docs_consistency.py --domain agent | Confirmed by repository evidence |
| REQ-008 | Amendment 2026-11-10: mcp_04_05_git.md:48 states an empty protected_branches protects none (AC-07/REQ-008 grep or fail-closed statement) | docs/22_mcp/mcp_04_05_git.md | Phase 6 | N/A: none cites REQ-008 | uv run python tools/check_docs_consistency.py --domain mcp | Confirmed by repository evidence |
| REQ-008 | Amendment 2026-11-10: mcp_05_01:78,83 state empty protected_branches/path_denylist allow all (AC-07/REQ-008 grep or fail-closed statement) | docs/22_mcp/mcp_05_01_access-control-and-allowlists.md | Phase 6 | N/A: none cites REQ-008 | uv run python tools/check_docs_consistency.py --domain mcp | Confirmed by repository evidence |
| REQ-001 | Amendment 2026-11-10: Imports STRICT_PRODUCTION_OVERRIDES, which is removed from tests/agent/_config_test_defaults.py | tests/agent/test_repository_gateway.py | Phase 1 | N/A: none cites REQ-001 | uv run pytest tests/agent/test_repository_gateway.py -v | Confirmed by repository evidence |
| REQ-001 | Amendment 2026-11-10: Imports STRICT_PRODUCTION_OVERRIDES, which is removed from tests/agent/_config_test_defaults.py | tests/agent/test_tool_audit.py | Phase 1 | N/A: none cites REQ-001 | uv run pytest tests/agent/test_tool_audit.py -v | Confirmed by repository evidence |

<!-- tools/generate_workitem.py implementation-procedure-pass timestamp: 20261110-154603 -->