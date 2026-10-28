# Make RuntimeTool construction fail closed on missing write metadata

## Priority
Medium

## Summary
Stop `build_runtime_tool()` from treating a missing `is_write` as read-only in production paths, separate permissive construction for tests and fixtures from the production builder, and update the stale module documentation.

## Background
Source: `memo-issue.md` Issue 10, re-verified against current source on 2026-10-27.

- `build_runtime_tool()` in `scripts/shared/runtime_tool.py` takes `is_write: bool | None = None` and resolves a missing value to `False` (`resolved_is_write = _or_default(is_write, False)`). Its docstring states "`is_write` defaults to `False` when not explicitly supplied". `requires_serial` defaults to `True` when `is_write` was not supplied. `Explicit in code`.
- The module docstring still describes `RuntimeTool` as the type that "a future `RuntimeToolRegistry` ... will store" with "no consumer yet", although the registry and discovery wiring are active. `Explicit in code` (docstring) against active callers in `scripts/agent/services/mcp_tool_discovery*.py`.
- Callers of `build_runtime_tool` in `scripts/`: `mcp_tool_discovery.py`, `mcp_tool_discovery_registry.py`, `mcp_tool_discovery_fetch.py` and the module itself. Callers in `tests/`: at least `tests/shared/test_runtime_tool.py`, `tests/agent/services/test_mcp_tool_discovery.py` and several routing tests. `Explicit in code` (file search).
- Discovery validates the four required Schema 2.0 fields before building (see `issues/done/20261027-104324_mcpcompat003_align-legacy-resource-scope.md` for validator-boundary work), so the production discovery path does not rely on the default. `Strongly implied by code`.

## Problem
Any direct caller that omits `is_write` gets a tool recorded as read-only, although its write behavior is unknown. Read/write classification affects approval, scheduling and policy decisions.

## Reason for Change
No production path is shown to hit the default today, so the risk is latent: a future caller or a refactor of discovery validation could register an unclassified tool as read-only. Severity is Medium (safety default, no demonstrated misclassification).

## Implementation Intent
The production builder requires the execution metadata (write, serialization, scope, visibility, safety tier) and raises on a missing value; a clearly named test/fixture builder keeps the permissive defaults and is not importable from production modules. Consider representing "unknown" explicitly if the permissive path stays, rather than mapping it to `False`.

## Target Files or Areas
- `scripts/shared/runtime_tool.py`
- `scripts/agent/services/mcp_tool_discovery.py`, `mcp_tool_discovery_registry.py`, `mcp_tool_discovery_fetch.py`
- `tests/shared/test_runtime_tool.py` and the test modules that call `build_runtime_tool`
- Docs describing RuntimeTool ownership under `docs/22_mcp/` or the relevant ADR-003 text (only the sentences about current consumers)

## Required Changes
- Enumerate all `build_runtime_tool()` callers and classify them as production or test/fixture.
- Make the production construction path require the metadata fields and reject missing values.
- Introduce a separate permissive builder for fixtures if tests still need defaults, and keep it out of production imports (enforce with a check or import-linter rule if practical).
- Update the module and doc text so it describes the current registry consumers.

## Constraints
- Discovery must remain compatible with validated Schema 2.0 entries; do not change the validation behavior owned by mcpcompat003.
- Public `RuntimeTool` field names and meanings are unchanged.

## Acceptance Criteria
- Production construction with a missing `is_write` (or other required metadata) raises; no production path can register an unclassified tool as read-only.
- Test fixtures use the separate permissive builder and the production modules do not import it.
- Module documentation matches the current architecture.

## Testing Expectations
- Unit tests: production builder rejects each missing required field; discovery still builds tools from validated entries.
- Update affected tests to the fixture builder; `uv run pytest tests/shared tests/agent/services`, mypy, ruff, `PYTHONPATH=scripts uv run lint-imports`.

## Documentation Impact
Yes, small: the `runtime_tool.py` module docstring and any doc sentence that calls the registry future work. Current behavior only.

## Out of Scope
- Legacy `resource_scope` handling and validator responsibility split (mcpcompat003).
- Changing Schema 2.0 required fields.
- Registry or routing changes.

## Dependencies
Coordinate with `plans/20261027-121337_mcpcompat003_align-legacy-resource-scope.md`, which also touches `scripts/shared/runtime_tool.py` (and the validator boundary); implement that plan first or rebase carefully.

## Unresolved Questions
- Should "unknown" write state be an explicit value instead of failing construction? `Needs confirmation` (design decision).
- How many test call sites rely on the permissive defaults? `Needs confirmation`: count before choosing the fixture-builder shape.

## AI Implementation Instruction
Keep the change to the builder split and its callers. Do not alter discovery validation. If many tests depend on the defaults, propose the fixture builder first and stop for confirmation.

## Traceability
- **Workflow phase**: issue-creator
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20261027-155851
- **Related target files**: `scripts/shared/runtime_tool.py`, `scripts/agent/services/mcp_tool_discovery.py`, `scripts/agent/services/mcp_tool_discovery_registry.py`, `scripts/agent/services/mcp_tool_discovery_fetch.py`, `tests/shared/test_runtime_tool.py`
