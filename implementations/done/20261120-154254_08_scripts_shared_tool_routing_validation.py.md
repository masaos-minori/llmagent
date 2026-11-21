## Goal

Remove `validate_routing_against_config()` from `scripts/shared/tool_routing_validation.py` (`REQ-004`). It compares config `tool_names` against the registry, but `McpServerConfig.tool_names` is removed by row 5, so the config-vs-registry drift path no longer has an input. Live `/v1/tools` vs. registry drift (`validate_routing_against_live()`) becomes the sole routing-drift validator.

## Scope
**Release unit**: static-catalog removal

## Assumptions
- `validate_routing_against_config(registry, server_configs)` occupies lines 25-46 of the current `tool_routing_validation.py` (verified); its only production caller chain is `routing_drift.py::check_routing_drift()` → `startup_validation.py:174`, both removed by their own scope rows in this Plan.
- `validate_routing_against_live()` (lines 49-68), `check_tool_safety_tiers()` (lines 71-89), and `check_unknown_tool_safety_tiers()` (lines 92-106) do NOT read `cfg.tool_names` and survive unchanged.
- The two scope rows `scripts/agent/services/routing_drift.py` and `scripts/agent/startup_validation.py` (and the doc/test scope rows) land in the same release unit, so removing this function leaves no dangling caller.

## Design decisions
- Delete the whole `validate_routing_against_config()` function (lines 25-46); do not replace it with a stub, so no caller can invoke a dead config-based comparison.
- Leave `validate_routing_against_live()` as the single routing-drift entry point; its `registry.validate_live_tools_match()` path is unchanged.

## Alternatives considered
- Repurpose `validate_routing_against_config()` to read ownership from the new manifest instead of `cfg.tool_names`: rejected because the config-vs-registry comparison is conceptually obsolete once config tool names are gone; the live-vs-registry path already covers drift and is the fail-closed authority (`REQ-004`, `REQ-006`).

## Implementation
### Target file
`scripts/shared/tool_routing_validation.py`

### Procedure
Delete `validate_routing_against_config()` (lines 25-46).

### Method
Remove the function definition and its body; confirm the surviving functions still parse and the module imports.

### Details
- Delete lines 25-46: the `def validate_routing_against_config(...)` signature through its `return drift`.
- Confirm no remaining reference to `server_configs` / `cfg.tool_names` / `registry.validate_tool_names_match()` outside this function.
- Leave `validate_routing_against_live()`, `check_tool_safety_tiers()`, `check_unknown_tool_safety_tiers()` untouched.
- Optionally tighten the module docstring title ("... against config and live responses") to "... against live responses" to match the now-live-only surface (cosmetic; the ADR-003 citation stays valid because the live path still uses the static ToolRegistry).

## Compatibility considerations
Backward incompatible by design (`REQ-004`): any caller of `validate_routing_against_config()` now fails at import/call time. The only callers (`routing_drift.py`, `startup_validation.py`) are removed by their scope rows in this release unit.

## Security considerations
Fail-closed: routing drift is still detected via the live-vs-registry path (`validate_routing_against_live()`), which stays fatal under strict mode (`REQ-006`). Removing the config path removes a weaker, config-source drift check that could miss servers whose config is stale but whose live tools differ.

## Rollback considerations
N/A: revert the commit.

## Validation plan
Import `tool_routing_validation` and assert `validate_routing_against_config` no longer exists while `validate_routing_against_live` still detects drift for a live tool list that diverges from the registry. Run `tests/shared/test_tool_registry.py` (live-drift classes retained) and `tests/agent/test_startup_mcp_starter.py` (config-drift mocks removed by scope row).

## Completion criteria
`tool_routing_validation.py` exposes no `validate_routing_against_config()` symbol, no `cfg.tool_names` reference remains in the module, and `validate_routing_against_live()` still detects live-vs-registry drift.

## Out of Scope
The `routing_drift.py` / `startup_validation.py` caller removal, the `tool_registry.py` docstring update, the `test_startup_mcp_starter.py` mock removal, the `test_tool_registry.py` config-drift class removal, and the two doc updates — each is its own scope row in this Plan.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 20261120 | 20261120 | Deleted `validate_routing_against_config()` (lines 25-46); removed the now-unused `McpServerConfig` TYPE_CHECKING import; tightened module docstring title to live-only. |
| 2 | Add or update tests per Validation plan | N/A | — | — | No new tests: live-drift classes retained; config-drift class removal is `_20` scope. |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20261120 | 20261120 | ruff + mypy clean; `validate_routing_against_live()` body intact (still calls `validate_live_tools_match`). Owned intermediate: `test_tool_registry.py` collection + `check_routing_drift` callers fail until `_20`/`_16`. |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | N/A | — | — | Docstring tightening done inline; doc rows are `_21`/`_22` scope. |

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
- **Requirement ID**: `REQ-004`
- **Source issue**: `issues/20261120-114210_agentcfg002_tool-catalog-registry.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261120-151418_agentcfg002_tool-catalog-registry.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261120-154254
- **Related target files**: `scripts/shared/tool_routing_validation.py`
