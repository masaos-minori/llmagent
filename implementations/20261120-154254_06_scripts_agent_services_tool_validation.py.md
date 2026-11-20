## Goal

Rewrite `_check_tool_definitions` in `scripts/agent/services/tool_validation.py` to compare live `/v1/tools` against the new static ownership/capability registry and the routing registry instead of `ctx.cfg.tool.tool_definitions` (`REQ-004`), make a static-vs-live ownership mismatch fatal (`REQ-006`), and remove all `tools_definitions.toml` wording (`REQ-007`).

## Scope
**Release unit**: static-catalog removal

## Assumptions
- `_check_tool_definitions(ctx, strict=True)` is imported and called by `mcp_tool_discovery.py:195` (`_check_tool_definitions_finding`); its signature and the `check_tool_definitions_runtime` wrapper must stay intact so the startup/health wiring is unchanged.
- The new registry (`config/tool_catalog.toml`, a separate target row) maps each server key to its owned tools/capabilities; `tool_routing_validation.py` (a separate target row) already compares live lists against the registry. This row composes those two inputs.
- `strict=True` still raises `RuntimeError` on fatal findings; `strict=False` returns them as warnings.

## Design decisions
- Replace the `cfg_names` set built from the removed `ToolConfig.tool_definitions` field with the ownership data read from the new registry manifest; reuse `tool_routing_validation.py`'s live-vs-registry comparison for the routing-drift half so the two modules do not diverge.
- Keep the function's two entry points (`_check_tool_definitions`, `check_tool_definitions_runtime`) and the `strict` flag unchanged.

## Alternatives considered
- Keep comparing against `ctx.cfg.tool.tool_definitions`: rejected by `REQ-002`/`REQ-004`, which remove that field and the comparison.

## Implementation
### Target file
`scripts/agent/services/tool_validation.py`

### Procedure
Replace the body of `_check_tool_definitions` (lines 106-181) with a registry+routing drift check; delete every `tools_definitions.toml` string.

### Method
- Remove the `cfg_names` comprehension (lines 135-139) that reads the removed field.
- Build the expected per-server tool/capability sets from the new registry manifest instead of config.
- Delegate the live-vs-registry matching to `tool_routing_validation.py` (a separate target row) for the routing-drift half.
- Add a fatal ownership-mismatch finding when a server's live tools do not match its declared ownership in the registry (`REQ-006`).
- Keep duplicate tool-name and routing-drift findings fatal under `strict=True`.
- Delete the three `tools_definitions.toml` message strings (lines 120, 129, 160/164) and their `label="tool_definitions"` warning (line 162); replace with ownership/routing labels (`REQ-007`).

### Details
- Preserve the unreachable-server handling (all-unreachable skip vs. strict raise) but base the "expected" set on the registry, not config.
- Confirm no other symbol in the module references `ctx.cfg.tool.tool_definitions`.
- Coordinate with the `mcp_tool_discovery.py` row: the caller's `_check_tool_definitions_finding` still receives a `HealthCheckResult`; fatal findings still surface as `RuntimeError`.

## Compatibility considerations
Backward incompatible by design (`REQ-004`, `REQ-006`): the drift check now fails on static-vs-live ownership mismatches that the old config-based check never saw. The registry manifest must exist and be populated, or every server reports an ownership mismatch.

## Security considerations
Fail-closed: a server surfacing tools outside its declared ownership is now fatal, closing a tool-injection / drift vector the config-based check could miss.

## Rollback considerations
N/A: revert the commit.

## Validation plan
Drive `_check_tool_definitions` with a registry-shaped expected set: ownership match passes, ownership mismatch is fatal under `strict=True` and a warning under `strict=False`, and `tools_definitions.toml` no longer appears in any message.

## Completion criteria
`_check_tool_definitions` reads no `ToolConfig.tool_definitions`, compares live tools against the registry/routing registry, reports ownership mismatches fatally, and contains no `tools_definitions.toml` string.

## Out of Scope
The required-capability conversion (`mcp_tool_discovery.py`), the registry manifest (`config/tool_catalog.toml`), the live-vs-registry comparison helper (`tool_routing_validation.py`), tests, and docs.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | Signature preserved for the `mcp_tool_discovery.py` caller. |
| 2 | Add or update tests per Validation plan | Pending | — | — | |
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
- **Requirement ID**: `REQ-004`, `REQ-006`, `REQ-007`
- **Source issue**: `issues/20261120-114210_agentcfg002_tool-catalog-registry.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261120-151418_agentcfg002_tool-catalog-registry.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261120-154254
- **Related target files**: `scripts/agent/services/tool_validation.py`
