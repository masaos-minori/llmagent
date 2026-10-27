# Remove the MCP Health re-export and the optional posture_gates default

## Priority
Medium

## Summary
Make `shared.mcp_health` the only import path for `McpServerHealthState` and `McpServerHealthRegistry`, and make `McpToolDiscoveryService` require real Security Posture gates, so that the two MCP backward-compatibility paths disappear and cannot be reintroduced unnoticed.

## Background
Source: `memo-issue.md` item H-01 and the Medium M-03 docstring bullet, re-verified against current source on 2026-10-27 (Confirmed by repository search).

- Health re-export: `scripts/shared/mcp_config.py` imports both types from `shared.mcp_health` with `# noqa: F401` only to re-publish them. Callers still import them through `shared.mcp_config`: `scripts/agent/services/mcp_status.py` (`McpServerHealthState`), `scripts/agent/startup_reporter.py` (deferred import of `McpServerHealthState`), `scripts/agent/context.py` (`McpServerHealthRegistry`), `scripts/shared/tool_transport_invoker.py` (both), and, in tests, `tests/shared/test_tool_executor.py`, `tests/shared/test_tool_executor_routing.py`, `tests/shared/test_tool_transport_invoker.py`, `tests/integration/test_agent_mcp_integration.py`. Other callers (`scripts/agent/factory.py`, `scripts/agent/commands/cmd_mcp.py`, `tests/agent/test_agent_factory.py`, `tests/agent/commands/test_cmd_mcp.py`) already use `shared.mcp_health`.
- posture_gates default: `McpToolDiscoveryService.__init__` in `scripts/agent/services/mcp_tool_discovery.py` declares `posture_gates: Mapping[str, PostureGate] | None = None`. When `None`, `discover_all()` passes `allowed_servers=None` and no posture allowlist is applied. Its docstring calls `None` "the migration-window value" and says "the only production caller passes real gates". The only production caller, `scripts/agent/startup_validation.py`, does pass gates from `collect_server_postures()`. Roughly 70 test call sites omit the argument: `tests/agent/services/test_mcp_tool_discovery.py`, `tests/integration/test_production_security_regression.py` (2), `tests/agent/services/test_runtime_tool_routing_integration.py` (2). `tests/agent/services/test_mcp_tool_discovery_posture_gate.py` already passes gates, including `{}`.
- The memo also claimed that the design documents say "migration-window" and "registered as before". A search of `docs/` finds neither phrase; both live only in the module docstring of `mcp_tool_discovery.py`. The only document statement about the re-export is `docs/22_mcp/mcp_03_03_transport-and-health.md` line 35 ("`shared/mcp_config.py` only re-exports the class").

## Problem
- The re-export keeps a second public path for the Health types, so the canonical module is not enforced and `mcp_status.py` depends on the old path.
- A caller that forgets `posture_gates` silently gets a discovery registry with no Security Posture gating. Most discovery tests exercise that ungated path rather than the production path.

## Reason for Change
Latent fail-open default on a security gate and a duplicated import surface; no production misbehavior is evidenced today because the single production caller passes gates, so this is Medium rather than High. Nothing makes the change time-sensitive; doing it before more callers adopt the old paths keeps the cost low.

## Implementation Intent
Move every caller to the canonical `shared.mcp_health` import, then delete the re-export. Make `posture_gates` a required parameter and delete the `None` branch so the registry cannot be built without a gate. Preserve the current semantics that an empty gate mapping registers no server (fail-closed). Add detection of both reintroductions to the compatibility checker so CI fails if either path returns. Remove migration-window wording from the docstring and the stale "only re-exports" sentence from the document.

## Target Files or Areas
- `scripts/shared/mcp_config.py`
- `scripts/agent/services/mcp_status.py`
- `scripts/agent/startup_reporter.py`
- `scripts/agent/context.py`
- `scripts/shared/tool_transport_invoker.py`
- `scripts/agent/services/mcp_tool_discovery.py`
- `scripts/agent/startup_validation.py` (read-only confirmation of the production caller)
- `tests/shared/test_tool_executor.py`, `tests/shared/test_tool_executor_routing.py`, `tests/shared/test_tool_transport_invoker.py`, `tests/integration/test_agent_mcp_integration.py`
- `tests/agent/services/test_mcp_tool_discovery.py`, `tests/integration/test_production_security_regression.py`, `tests/agent/services/test_runtime_tool_routing_integration.py`
- `docs/22_mcp/mcp_03_03_transport-and-health.md`
- `tools/check_compat_shims.py` and its tests

## Required Changes
- Change every import of `McpServerHealthState` and `McpServerHealthRegistry` from `shared.mcp_config` to `shared.mcp_health` in the files listed above, then re-run a repository-wide search to confirm zero remaining callers.
- Remove the re-export and its `# noqa: F401` from `scripts/shared/mcp_config.py`.
- Make `posture_gates` a required argument of `McpToolDiscoveryService`, remove the `None` branch in `discover_all()`, and rewrite the class and module docstrings without migration-window wording.
- Update the discovery tests and integration tests to pass real gates, using a shared helper if the call-site count makes per-test construction noisy.
- Keep a test that an empty gate mapping registers no tool.
- Add checker rules to `tools/check_compat_shims.py` for the `shared.mcp_config` Health import and for a `McpToolDiscoveryService(` call without `posture_gates`, with checker tests.
- Fix the "only re-exports" sentence in `docs/22_mcp/mcp_03_03_transport-and-health.md`.

## Constraints
- Runtime behavior of the production startup path must not change.
- `lint-imports` contracts (notably `agent-mcp-config-models`) must still pass after the import moves.
- Suppression comments follow `rules/coding.md` Suppression governance.
- The `posture_gates` change affects about 3 test files and about 70 call sites (blast radius per `rules/toolchain.md` Impact-radius check); record it in the plan.

## Acceptance Criteria
- `rg "from shared.mcp_config import" scripts tests` shows no import of `McpServerHealthState` or `McpServerHealthRegistry`.
- `shared/mcp_config.py` no longer references either type.
- `McpToolDiscoveryService(ctx)` without `posture_gates` raises `TypeError`.
- A test confirms that an empty gate mapping yields an empty tool registry.
- `uv run python tools/check_compat_shims.py --check-removed-names --check-doc-symbols` fails on a reintroduced old import or a gate-less constructor call, and passes on the repository.
- The document no longer claims that `shared/mcp_config.py` re-exports the Health class.

## Testing Expectations
- Targeted pytest: `tests/shared/`, `tests/agent/services/`, `tests/integration/test_agent_mcp_integration.py`, `tests/integration/test_production_security_regression.py`, plus the new checker tests.
- Full suite, `uv run mypy --no-namespace-packages scripts/`, `PYTHONPATH=scripts uv run lint-imports`, ruff.
- `uv run python tools/check_docs_consistency.py --domain mcp` and the docs checkers in `routing.md` for the edited document.

## Documentation Impact
Yes, small. Correct the Health module ownership statement in `docs/22_mcp/mcp_03_03_transport-and-health.md`. Describe only current boundaries; do not add a history note. Do not copy implementation detail into the document (`skills/DESIGN.md` Docs content policy).

## Out of Scope
- Changing posture classification or `allowed_server_keys()` semantics.
- Rewriting unrelated discovery tests.
- The Tool Schema 2.0 validator (see `issues/*mcpcompat003*`).
- Removing the `eventbus.db` facade.

## Dependencies
- Shares `tools/check_compat_shims.py` and its tests with the sibling issues of this batch (`ebcompat002`, `mcpcompat003`); land the checker edits in sequence, not in parallel.
- No open issue or in-flight plan touches `mcp_config.py` or `mcp_tool_discovery.py`; `issues/20261027-001347_mcpinv002_remove-dead-check-startup-mode-guard.md` edits `tool_executor.py` only and does not overlap.

## Unresolved Questions
- 不明: whether the `tests/agent/services/test_mcp_tool_discovery_posture_gate.py` empty-mapping test already asserts an empty registry (the call exists, its assertion was not read).
- 不明: preferred shape of the gate fixture for the roughly 70 test call sites (shared helper versus a permissive gate per test); to be decided in the plan.

## AI Implementation Instruction
Change only the imports, the constructor contract, the listed tests, the one document sentence and the checker rules. Do not refactor discovery or health logic. Re-run the repository search for callers immediately before deleting the re-export. Stop and report if a caller outside the listed files appears.

## Traceability
- **Workflow phase**: issue-creator
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20261027-104222
- **Related target files**: scripts/shared/mcp_config.py, scripts/agent/services/mcp_status.py, scripts/agent/startup_reporter.py, scripts/agent/context.py, scripts/shared/tool_transport_invoker.py, scripts/agent/services/mcp_tool_discovery.py, docs/22_mcp/mcp_03_03_transport-and-health.md, tools/check_compat_shims.py
