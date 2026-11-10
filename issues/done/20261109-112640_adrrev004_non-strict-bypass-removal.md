# Remove non-strict branches, the test-only auth bypass, and "empty means unrestricted" settings

## Priority
High

## Summary
Make strict behavior the only behavior: delete the `*_strict` toggles and their WARNING-only branches, make every empty safety setting mean "deny" (or fail at config load), remove the `accept_all_for_tests` bypass from production code, and delete the leftovers of the removed profile switch.

## Background
- Source: `memo-issue.md` items H-06, H-07, and H-13, re-checked against current source on 2026-11-09.
- `Explicit in config`: `config/agent.toml` carries `tool_definitions_strict = true` and `routing_drift_strict = true`. `Explicit in code`: `scripts/agent/production_config_validator.py` validates them, and non-strict branches remain in `scripts/agent/startup_validation.py` and `scripts/agent/services/mcp_tool_discovery.py` (`Needs confirmation`: the exact branch list; the memo also names an ADR-003 startup validation branch).
- `Explicit in code`: `attach_auth_middleware(app, token, *, accept_all_for_tests=False)` in `scripts/mcp_servers/server.py` skips authentication for an empty token only when the argument is True. The default is fail-closed. Under `scripts/` the argument is declared there; the only other references are tests (`tests/mcp_servers/test_mcp_server_base.py`). The memo's claim that production code "can still reach" the bypass is therefore a latent design risk, not a current caller (`Needs confirmation`: no production call site passes True).
- `Explicit in code`: `tool_policy.py` applies `allowed_tools` only when it is non-empty (`if cfg.tool.allowed_tools and tool_name not in ...`), so an empty list means "allow all" at runtime; `production_config_validator.py` already rejects an empty list for production (`Needs confirmation`: whether this check covers every load path, including reload).
- `Explicit in code`: `list_tools_with_server_key()` is defined in `scripts/mcp_servers/server.py` and used only by `tests/mcp_servers/mdq/test_mdq_routing.py`; `list_tools()` is used by tests in `tests/mcp_servers/`. `Needs confirmation`: production callers of either (the base-class `health()` at `scripts/mcp_servers/server.py` is also in scope).
- `Explicit in code`: `security_profile` is referenced by `config_builders.py`, `config_dataclasses.py`, `config_field_registry.py`, `production_config_validator.py`, and several tests; it is not present in `config/agent.toml` (`Needs confirmation` that it is no longer a user-facing key).
- `Needs confirmation` (not yet checked): empty `allowed_root` behavior in the file servers, and empty `path_denylist` / `protected_branches` in github-mcp (`config/github_mcp_server.toml`).
- Related archived issues under `issues/done/`: `start003_startup-routing-drift-check-downgrades-failures-to-warnings-while-safety-tier-check-stays-fail-closed`, `audit001_move-security-validation-to-each-mcp-server`, `mcp007_register-bearer-auth-in-shell-github-file-mcp-servers`. Re-verify against current source; some of this may be done.

## Problem
- Unreachable non-strict branches, and documentation that presents them as supported modes, force readers to reason about behavior that cannot occur in production.
- "Empty means allow all" settings let a typo or an unresolved environment variable silently remove a safety boundary, which ADR-004 Decision Group 1 forbids; none of the cases is a registered exception.
- A test-only authentication bypass lives in a production module; one mistaken call site would expose a server without authentication.
- A base `health()` that always reports ok can mask a broken server, and unused helpers and a single-valued profile key add maintenance cost.

## Reason for Change
- Safety boundaries must not depend on a configuration value being non-empty by luck; the current production validator catches only part of the cases (`allowed_tools`).
- Timing: the MCP security issue and the posture issue in this batch build on a clean strict-only baseline.

## Implementation Intent
- Strict behavior is the only behavior; mismatches and drift are always fatal.
- An empty or missing safety list means deny, or is rejected at config load.
- Production modules contain only production behavior; tests inject non-empty dummy tokens.
- Preserve every currently enforced production behavior; this change removes optionality, not protection.

## Target Files or Areas
- `scripts/agent/production_config_validator.py`, `scripts/agent/startup_validation.py`, `scripts/agent/services/mcp_tool_discovery.py`, `scripts/agent/services/config_field_registry.py`, `scripts/agent/config_builders.py`, `scripts/agent/config_dataclasses.py`, `scripts/agent/config_section_builders.py`, `scripts/agent/commands/cmd_config_display.py`, `scripts/agent/tool_policy.py`
- `scripts/mcp_servers/server.py` and each MCP server entry module that builds on it
- `config/agent.toml` and the per-server `config/*_mcp_server.toml` files (`allowed_root`, `path_denylist`, `protected_branches`)
- Tests: `tests/mcp_servers/test_mcp_server_base.py`, `tests/mcp_servers/mdq/test_mdq_routing.py`, `tests/integration/test_production_security_regression.py`, `tests/agent/test_startup_validation.py`, `tests/shared/test_config_loader.py`, `tests/agent/test_config_dataclasses.py`
- Docs: `docs/22_mcp/mcp_06_09_startup-validation-behavior-tool_definitions_strict.md`, `docs/22_mcp/mcp_06_01_configuration-file-inventory.md`, `docs/22_mcp/mcp_05_03_fail-open-fail-closed-and-risk-tiers.md`, `docs/23_agent/agent_10_01_operations-and-observability-startup-and-health.md`, `docs/23_agent/agent_08_04_configuration-mcp-approval-obs.md`, ADR-003 (`docs/10_adr/adr_02_02_003_agent-runtime-tool-registry-routing-authority.md`)

## Required Changes
- Remove the `*_strict` keys and every non-strict branch; tool-definition mismatch and routing drift are always fatal.
- Make `allowed_tools = []` deny all tools, or reject it at config load, at every load path (initial load and reload).
- Reject an empty `allowed_root` at config load.
- Require non-empty `path_denylist` and `protected_branches`, or register an ADR-004 exception with a written rationale.
- Remove `accept_all_for_tests`; update tests to inject non-empty dummy tokens.
- Delete `list_tools()` and `list_tools_with_server_key()` after confirming they have no production caller; update the tests that use them.
- Remove the `security_profile` key from the config schema, builders, validator, and `mcp_06_01`, and delete the "non-production mode is rejected" regression test.
- Make the base `health()` abstract, or derive it from real checks.
- Add a parametrized test proving every MCP server refuses to start with an empty or unset token (enumerate the servers from `config/agent.toml` `[mcp_servers.*]` rather than hard-coding a count).
- Update the documents listed above so they no longer describe the removed behavior.

## Constraints
- Config load must reject removed keys as unknown; no compatibility shim.
- ADR-004 Decision Group 1: configuration must not relax a safety boundary; any retained empty-list exception must be an approved ADR-004 exception.
- Measure blast radius first (`rules/toolchain.md` Impact-radius check) for `security_profile`, `*_strict`, and the `attach_auth_middleware` signature.
- Do not change the Agent-side `startup_validation` rule that rejects an empty `auth_token`.

## Acceptance Criteria
- No config schema, builder, or validator contains a `*_strict` key or `security_profile`.
- Tests prove: an empty `allowed_tools` denies all tools (or fails load); an empty `allowed_root` fails config load; every configured MCP server refuses an empty token.
- `rg -n accept_all_for_tests scripts tests` returns nothing.
- `rg -n "list_tools_with_server_key" scripts tests` returns nothing (or only a retained, named production caller recorded in the PR).
- `uv run python tools/check_docs_consistency.py --domain mcp` and `--domain agent` pass.

## Testing Expectations
- Unit, integration, and regression tests under `tests/mcp_servers/`, `tests/agent/`, `tests/integration/`; the parametrized empty-token test described above.
- Full validation sequence from `rules/toolchain.md`; `tests/mcp_servers/mdq/test_mdq_rag_boundary.py`.
- Documentation checkers: `check_docs_quality.py`, `check_docs_structure.py`, `check_docs_content_policy.py --strict`, `check_docs_consistency.py --domain mcp|agent`.

## Documentation Impact
- Update `mcp_06_09`, `agent_10_01`, `agent_08_04`, `mcp_05_03`, `mcp_06_01`, and ADR-003 so they state strict-only behavior, fail-closed defaults for safety lists, and failure behavior. Do not copy concrete config values.

## Out of Scope
- Server-side audit and the MCP authentication ADR (MCP security issue in this batch).
- Posture-failure handling (posture issue in this batch).
- The decision about server mandatoriness (EventBus and Group 7 decision issue).

## Dependencies
- Depends on: none.
- Blocks: `issues/20261109-113023_adrrev011_mcp-audit-auth-adr.md` (MCP security).
- Related, recently archived: `start003`, `audit001`, and `mcp007` under `issues/done/` (see Background).

## Unresolved Questions
- `Needs confirmation`: the production callers of `list_tools()`, `list_tools_with_server_key()`, and the base `health()`.
- `Needs confirmation`: whether an empty `path_denylist` / `protected_branches` / `allowed_root` currently disables restrictions, and which servers read them.
- Decision needed from a maintainer: require non-empty `path_denylist` / `protected_branches`, or register an ADR-004 exception (the issue defaults to "require non-empty").

## AI Implementation Instruction
- Remove optionality only; do not weaken or reshape any currently enforced check.
- Verify each symbol's callers with `rg` before deletion; stop and report on a production caller.
- Do not edit server logic unrelated to the settings listed here.
- Write documentation in English, follow the docs content policy, and do not commit.

## Traceability
- **Workflow phase**: issue-creator
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20261109-112640
- **Related target files**: `scripts/agent/production_config_validator.py`, `scripts/agent/startup_validation.py`, `scripts/agent/services/mcp_tool_discovery.py`, `scripts/agent/tool_policy.py`, `scripts/mcp_servers/server.py`, `config/agent.toml`, `config/github_mcp_server.toml`, `docs/22_mcp/mcp_06_09_startup-validation-behavior-tool_definitions_strict.md`, `docs/22_mcp/mcp_06_01_configuration-file-inventory.md`, `docs/22_mcp/mcp_05_03_fail-open-fail-closed-and-risk-tiers.md`, `docs/23_agent/agent_10_01_operations-and-observability-startup-and-health.md`, `docs/23_agent/agent_08_04_configuration-mcp-approval-obs.md`, `docs/10_adr/adr_02_02_003_agent-runtime-tool-registry-routing-authority.md`
