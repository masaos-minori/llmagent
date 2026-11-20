## Goal

Remove the config-based `check_routing_drift()` from `scripts/agent/services/routing_drift.py` (`REQ-004`, scope approved). It calls `validate_routing_against_config()`, which reads the removed `McpServerConfig.tool_names` (row 5). Startup routing-drift detection is consolidated into the live-based `validate_routing_against_live()` path already wired at `mcp_tool_discovery.py:165`, so removing the config path loses no coverage. Keep `check_routing_safety_tiers()` unchanged.

## Scope
**Release unit**: static-catalog removal

## Assumptions
- `check_routing_drift()` occupies lines 14-39 of the current `routing_drift.py`; its only production caller is `startup_validation.py:174` (removed by the sibling row 17).
- Its local import of `validate_routing_against_config` (lines 22-24) dies with the function.
- `check_routing_safety_tiers()` (lines 42-52) imports `check_tool_safety_tiers` (survives, row 8) and is still called by `startup_validation.py`'s "Routing safety tiers" step; it does NOT touch `tool_names` and stays.

## Design decisions
- Delete the entire `check_routing_drift()` function (lines 14-39), including its docstring and local import. Do not replace it with a stub, so no caller can invoke a dead config-based drift check.
- Leave `check_routing_safety_tiers()` byte-for-byte.

## Alternatives considered
- Repurpose `check_routing_drift()` to call `validate_routing_against_live()`: rejected because the live path already performs startup routing-drift detection at `mcp_tool_discovery.py:165`; duplicating it would create two drift authorities (`REQ-006`).

## Implementation
### Target file
`scripts/agent/services/routing_drift.py`

### Procedure
Delete `check_routing_drift()` (lines 14-39).

### Method
Remove the function definition through its final `return warnings` (line 39) and the trailing blank line before `check_routing_safety_tiers()`.

### Details
- Delete lines 14-39: the `def check_routing_drift(...)` signature, docstring, local `validate_routing_against_config` import, and body.
- Confirm `check_routing_safety_tiers()` (lines 42-52) is intact and still imports `check_tool_safety_tiers`.
- Confirm no other reference to `check_routing_drift` remains in `routing_drift.py`.

## Compatibility considerations
Backward incompatible by design (`REQ-004`): `check_routing_drift()` no longer exists. Its only caller (`startup_validation.py`) removes its call site in the same release unit. Any external importer now fails at import time.

## Security considerations
Fail-closed preserved: routing-drift detection continues via the live-vs-registry path (`validate_routing_against_live()`), which is fatal under strict mode (`REQ-006`). Removing the config-source check removes a weaker drift path that could miss servers whose config is stale but whose live tools differ.

## Rollback considerations
N/A: revert the commit.

## Validation plan
Import `routing_drift` and assert `check_routing_drift` no longer exists while `check_routing_safety_tiers` still returns tier-missing messages. Run `tests/agent/test_startup_mcp_starter.py` (its `check_routing_drift` tests are removed by the sibling row 19) and `tests/agent/shared/test_startup_validation_pipeline.py` (see the cascade note below).

## Completion criteria
`routing_drift.py` exposes no `check_routing_drift` symbol; `check_routing_safety_tiers` is unchanged; the module imports cleanly.

## Out of Scope
The `validate_routing_against_config()` removal (`tool_routing_validation.py`, row 8), the `startup_validation.py` call-site + import removal (row 17), the `McpServerConfig.tool_names` field removal (`mcp_config.py`, row 5), and every test that patches/calls `check_routing_drift` — several of which are **not** in this Plan's target table (see the cascade note in row 17).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | Line numbers are against current source; re-verify if `agentcfg001` lands first. |
| 2 | Add or update tests per Validation plan | Pending | — | — | Test cascade documented in row 17. |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Pending | — | — | |

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
- **Related target files**: `scripts/agent/services/routing_drift.py`
