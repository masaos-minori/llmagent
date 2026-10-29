# Make MCP posture gating and component mandatoriness construction-time contracts

## Priority
Medium

## Summary
Finish making the MCP execution path fail-closed by construction: `RuntimeToolRegistry` must not accept a missing posture allowlist (today `None` means "no gate"), and component mandatoriness must come from one machine-readable registry that `config/agent.toml` `required` values are validated against, instead of being configuration-only.

## Background
Source: `memo-issue.md` item H-04 (original tasks H-05 and M-01), re-verified against current source on 2026-10-29. Part of the memo's scope is already done, so this issue covers the remainder. The memo rates it High; the priority here is lowered for the reason under Reason for Change.

Already done (`Explicit in code`):
- `ToolExecutor` and `ToolTransportInvoker` take a required `health_registry` constructor argument (`scripts/shared/tool_executor.py:51`, docstring "Required health registry"; `scripts/shared/tool_transport_invoker.py:41`), and `scripts/agent/factory.py:117-122` creates the registry. `ToolExecutor` raises `TypeError` when the runtime registry is `None` (`tool_executor.py:82`). This was delivered by `issues/done/20261027-155847_mcpexec004_make-mcp-deps-mandatory.md` (plan `plans/done/20261028-093529_mcpexec004_make-mcp-deps-mandatory.md`).
- The registry builders in `scripts/agent/services/mcp_tool_discovery_registry.py` (lines 62 and 98) take `allowed_servers: frozenset[str]` as a required input, and the only production construction site passes it (`mcp_tool_discovery_registry.py:92`, fed from `scripts/agent/services/mcp_tool_discovery.py:110-112`).
- Safety and integrity posture failures already abort startup regardless of `required` (`scripts/agent/services/mcp_health.py:139-147`, `_is_fatal_gate`); `required` decides only the fate of an availability failure.
- ADR-004 defines the classification criteria (mandatory and non-mandatory components, lines 73-77 of `docs/10_adr/adr_02_01_004_platform-environment-failure-handling-policy.md`, `Documentation only`).

Still open (`Explicit in code`):
- `RuntimeToolRegistry.__init__` still declares `allowed_servers: frozenset[str] | None = None`; its docstring says `None` "means no gate was supplied and today's behavior is kept" and the filter applies only when the value is not `None` (`scripts/shared/runtime_tool_registry.py:49-60, 91-92`). Test code constructs the registry directly in many places (about 20 constructions across `tests/shared/`, `tests/agent/`, `tests/integration/`, measured with `rg -c`).
- `required` is a per-server field in the configuration (`scripts/shared/mcp_config.py:100, 326`, default `True`; non-required subprocess servers are rejected at lines 163-167). No machine-readable registry of component classifications exists: a search for mandatoriness or component-classification data under `scripts/` and `config/` finds none (`Explicit by absence search`).

## Problem
Because `required` is configuration-only, nothing records which components the architecture approves as mandatory, so a configuration edit can downgrade a mandatory component or leave a new component unclassified without a check. And although production code always supplies an allowlist, the constructor still offers a fail-open `None` that a future caller can reach.

## Reason for Change
The registry default is the last optional gate on the executable-exposure path, and the mandatoriness authority is the missing half of ADR-004's classification contract. Priority is Medium, not the memo's High: the production path already passes a posture allowlist, Safety and Integrity failures are fatal irrespective of configuration, and the health registry is already mandatory, so the remaining risk is latent and configuration-drift related, with no demonstrated fail-open execution. It is not time-sensitive.

## Implementation Intent
Make the allowlist an explicit required constructor input of `RuntimeToolRegistry` (an explicit empty set means deny all) and migrate its direct constructions in tests. Add a machine-readable component-mandatoriness registry whose single authoritative source is chosen with the ADR authority work, validate `config/agent.toml` `required` values against it at startup (unknown or conflicting classifications are fatal), and generate the diagnostics and operator reference from it. Reuse the existing `_is_fatal_gate` logic and the posture gates rather than adding a parallel mechanism.

## Target Files or Areas
- `scripts/shared/runtime_tool_registry.py`, `scripts/shared/mcp_config.py`
- `scripts/agent/services/mcp_tool_discovery_registry.py`, `scripts/agent/services/mcp_health.py`
- `scripts/agent/startup_validation.py`, `scripts/agent/production_config_validator.py`, `scripts/agent/factory.py`
- `config/agent.toml`
- The new component-classification source and its tests; tests that construct `RuntimeToolRegistry` directly (`tests/shared/test_tool_executor_routing.py`, `tests/shared/test_tool_routing_validation.py`, `tests/shared/test_tool_executor.py`, and others found by `rg "RuntimeToolRegistry\("`)
- ADR-004 documentation and the MCP operator reference under `docs/22_mcp/`

## Required Changes
- Require `allowed_servers` in `RuntimeToolRegistry`; remove the `None`-means-allow-all behavior; treat an explicit empty set as deny all.
- Prevent publication of a `RuntimeToolRegistry` before posture evaluation succeeds (verify the current flow first; see Unresolved Questions).
- Create the machine-readable component-mandatoriness registry with component ID, approved classification, failure category, safety role, safely disableable functions, startup consequence, observability requirements, owner, and authority ADR.
- Validate `config/agent.toml` `required` values against the registry; treat unknown or conflicting classifications as fatal.
- Generate diagnostics and operator reference material from the registry.
- Measure the blast radius of the constructor change with `rg -l 'RuntimeToolRegistry\(' tests/` before migrating, and migrate callers in small steps.

## Constraints
- Do not weaken the existing fail-closed startup rules or the rule that Safety and Integrity failures are fatal.
- Production behavior stays unchanged for a correct configuration; only previously unvalidated configurations may now fail at startup.
- The registry is a derived contract source; keep one authoritative definition and do not create a competing copy of ADR-004's criteria.
- Keep `shared` a leaf module (it cannot import Agent posture DTOs; the allowlist stays a plain set of server keys).

## Acceptance Criteria
- A `RuntimeToolRegistry` cannot be constructed without an explicit allowlist, and no production path interprets a missing allowlist as allow all.
- Tool execution cannot be constructed without health tracking (existing behavior preserved).
- A registry cannot be published without posture evaluation.
- Configuration cannot downgrade an architecture-mandatory component; unknown classifications stop startup.
- Tools of unaccepted or safely disabled servers are absent from LLM executable exposure and routing.
- Every disable or fatal decision has an observable reason.

## Testing Expectations
- Regression tests that fail before the change and pass after: missing allowlist rejected, empty allowlist denies all, downgrade of a mandatory component rejected, unknown classification fatal.
- Existing tests that construct `RuntimeToolRegistry` updated without changing their assertions' meaning.
- `uv run pytest tests/shared tests/agent`, `uv run pytest tests/integration/test_production_security_regression.py`, `uv run mypy --no-namespace-packages scripts/ tests/eventbus`, `PYTHONPATH=scripts uv run lint-imports`, `uv run python tools/check_docs_consistency.py --domain mcp`.

## Documentation Impact
Yes. ADR-004 and the MCP operator reference must state where the mandatoriness registry lives, that configuration cannot weaken it, and the startup consequence of each classification; document intent, boundaries, and failure behavior only (`skills/DESIGN.md` Docs content policy). Generated reference blocks follow `tools/generate_reference_table.py`.

## Out of Scope
- Health-registry mandatoriness (already done by `mcpexec004`) and the dynamic tool-health hint (`issues/20261029-104507_toolhint001_dynamic-tool-health-hints.md`).
- Changing which components the architecture classifies as mandatory (the registry records the approved classification; it does not re-decide it).
- Unrelated refactoring or formatting-only changes.

## Dependencies
- Builds on the archived `issues/done/20261027-155847_mcpexec004_make-mcp-deps-mandatory.md`; re-verify this issue against current source if that work changes.
- Coordinate with `issues/20261029-104504_adrauth001_adr-authority-model.md`: the registry's authority ADR and its placement among generated contracts depend on the ADR authority model.
- Blocks the component-mandatoriness manifest in `issues/20261029-104505_adrcov001_contract-manifests-invariant-coverage.md`.
- Related: `issues/20261029-104503_toolexec001_idempotent-tool-call-snapshot.md` consumes the posture and tool-definition generation identifiers.

## Unresolved Questions
- `Needs confirmation`: whether registry publication before posture evaluation is already prevented by the current startup flow (this issue lists it as a requirement but did not trace the call path end to end).
- `Needs confirmation`: where the authoritative mandatoriness data should live (a TOML or JSON file under `config/`, a Python table, or the ADR front matter) and who owns it.
- `Needs confirmation`: how many direct `RuntimeToolRegistry` constructions in tests need migration beyond the about 20 counted with `rg -c`.

## AI Implementation Instruction
- Read ADR-003, ADR-004, `scripts/shared/runtime_tool_registry.py`, and `scripts/agent/services/mcp_health.py` before editing; reuse `_is_fatal_gate` and the posture gates.
- Measure the test blast radius first and migrate callers incrementally, running the affected tests after each step.
- Do not change which components are mandatory; stop and report open questions about the registry's home and owner instead of choosing.
- Keep `shared` free of Agent imports.

## Traceability
- **Workflow phase**: issue-creator
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20261029-104502
- **Related target files**: `scripts/shared/runtime_tool_registry.py`, `scripts/shared/mcp_config.py`, `scripts/agent/services/mcp_tool_discovery_registry.py`, `scripts/agent/services/mcp_health.py`, `scripts/agent/startup_validation.py`, `scripts/agent/production_config_validator.py`, `scripts/agent/factory.py`, `config/agent.toml`
