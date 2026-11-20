## Goal

Stop reading the removed `McpServerConfig.tool_names` field in `scripts/agent/services/mcp_status.py` (`REQ-003`, fallout from row 5). `_tier_for_server` is called at line 86 with `cfg.tool_names`; once the field is gone that call breaks. Derive the per-server tool-name list from the RuntimeToolRegistry (`ctx.services_required.runtime_tools`) — the ADR-003 sole tool authority, available during `/mcp status` probing — and preserve the highest-risk-tier classification behavior unchanged.

## Scope
**Release unit**: static-catalog removal

## Assumptions
- Line 86 (`tier = _tier_for_server(cfg.tool_names, tiers)`) is the only production read of `cfg.tool_names` in `mcp_status.py`.
- `_tier_for_server(tool_names, tiers)` (lines 312-329) takes the tool-name list as a parameter and is unchanged; its behavior (highest-risk tier, READ_ONLY fallback on empty/unclassified, `McpProbeError` on unknown tier strings) stays intact.
- `ctx.services_required.runtime_tools` is a `RuntimeToolRegistry | None`, wired at `startup_validation.py:240`. `RuntimeToolRegistry.all_tools()` returns `RuntimeTool` objects exposing `.name` and `.server_key` (confirmed via `tests/shared/test_runtime_tool_registry.py` / `tests/shared/runtime_tool_factory`).
- `tool_safety_tiers` (`ctx.cfg.approval.tool_safety_tiers`, line 63) is a separate approval config untouched by this Plan; the `tiers` mapping is unchanged.

## Design decisions
- Replace the `cfg.tool_names` argument at line 86 with a registry-derived list: filter `ctx.services_required.runtime_tools.all_tools()` to `server_key == key`. When the registry is `None` or has no tools for the server, pass an empty list so `_tier_for_server` falls back to `READ_ONLY` (preserving the current empty-input behavior).
- Keep `_tier_for_server` itself unchanged; only its caller changes.

## Alternatives considered
- Deriving from the live `/v1/tools` probe result: rejected as more fragile because line 86 runs before the HTTP probe completes, so an unreachable server would yield no tools; the runtime registry reflects last-discovered tools and is available unconditionally.
- Loading the static registry manifest (row 9): rejected as an extra loader dependency; the runtime registry already holds the same ownership data and is the ADR-003 authority.

## Implementation
### Target file
`scripts/agent/services/mcp_status.py`

### Procedure
At line 86, derive the per-server tool names from the RuntimeToolRegistry instead of `cfg.tool_names`.

### Method
Replace line 86:
```python
tier = _tier_for_server(cfg.tool_names, tiers)
```
with:
```python
_server_tools = [
    t.name for t in ctx.services_required.runtime_tools.all_tools()
    if ctx.services_required.runtime_tools is not None and t.server_key == key
]
tier = _tier_for_server(_server_tools, tiers)
```
(Defensive `is not None` guard keeps the expression a single statement; a preceding `if reg is None: reg = {}` style is equally valid.)

### Details
- Confirm no other `cfg.tool_names` / `.tool_names` reference remains in `mcp_status.py`.
- Leave `_tier_for_server` (lines 312-329) byte-for-byte unchanged.
- Do not change `tiers` resolution (line 63) or the `McpProbeResult(tier=tier)` assignment (line 134).

## Compatibility considerations
Behavior-preserving by intent. A server present in the runtime registry keeps its highest-risk tier; a server absent from the registry (e.g. disabled/excluded during discovery) now resolves to `READ_ONLY` instead of its static `tool_names` tier — acceptable, since a server not serving discovered tools carries no live risk. No public API change.

## Security considerations
Fail-closed preserved: tier classification still raises `McpProbeError` on unknown tier strings and defaults to `READ_ONLY` when no tool is classified. A server whose tools are undiscoverable degrades to `READ_ONLY` (lowest risk), consistent with fail-safe status reporting.

## Rollback considerations
N/A: revert the commit.

## Validation plan
Run `tests/agent/services/test_agent_mcp_status.py`: the direct `_tier_for_server` cases (lines 20-59, which pass tool-name lists) must still pass unchanged, confirming the function itself is intact. Run `probe_all`-based tests to confirm the registry-derived tier path works with a populated and a `None` registry. Consumer-scan any other test that constructs `McpServerConfig(..., tool_names=...)` and update it (see the sibling `mode_classification.py` fallout row).

## Completion criteria
`mcp_status.py` contains no `cfg.tool_names` reference; `_tier_for_server` is unchanged; `probe_all` computes each server's tier from the runtime registry, falling back to `READ_ONLY` when the registry is absent.

## Out of Scope
The `McpServerConfig.tool_names` field removal (`mcp_config.py`, row 5), the MDQ availability check in `mode_classification.py` (fallout row 15), the required-capability model (`mcp_tool_discovery.py`, row 7), and the static registry (`config/tool_catalog.toml`, row 9).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | Line numbers are against current source; re-verify if `agentcfg001` lands first. |
| 2 | Add or update tests per Validation plan | Pending | — | — | `test_agent_mcp_status.py` exercises `_tier_for_server` directly; likely no edit needed. |
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
- **Requirement ID**: `REQ-003`
- **Source issue**: `issues/20261120-114210_agentcfg002_tool-catalog-registry.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261120-151418_agentcfg002_tool-catalog-registry.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261120-154254
- **Related target files**: `scripts/agent/services/mcp_status.py`
