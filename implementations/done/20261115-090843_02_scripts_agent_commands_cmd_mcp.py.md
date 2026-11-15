## Goal

Replace the static `/mcp status` tool count in `cmd_mcp.py` with registry totals (LLM-visible, disabled, unavailable) from `RuntimeToolRegistry.diagnostics()`. (`REQ-002`)

## Scope
**Release unit**: N/A: not part of a release unit

## Assumptions
- `ctx.services_required.runtime_tools` is available inside `_cmd_mcp_status`; when absent, show a neutral placeholder rather than a static count.
- The totals are display-only and never gate, reroute, or retry anything.

## Design decisions
- Derive the totals from `tool_registry.diagnostics()` (one dict per registered tool; keys `name, server_key, config_dependent, enabled, disabled_reason, enabled_for_llm`), aggregating into LLM-visible / disabled / unavailable counts.
- Fetch the registry near the top of `_cmd_mcp_status()` so the count line (line 128) can use it before the later `diagnostics()` block.

## Alternatives considered
- Keeping the static count: rejected by `REQ-002`.
- Counting only LLM-visible tools: narrower than the plan's required LLM-visible/disabled/unavailable breakdown.

## Implementation
### Target file
`scripts/agent/commands/cmd_mcp.py`

### Procedure
1. At the start of `_cmd_mcp_status()`, fetch `tool_registry = ctx.services_required.runtime_tools`.
2. Replace the tool-count line at line 128:
   ```python
   f"  Tools       {len(ctx.cfg.tool.tool_definitions)} (from config/tools_definitions.toml)"
   ```
   with registry totals aggregated from `tool_registry.diagnostics()`: an LLM-visible count (`enabled_for_llm` true), a disabled count (`disabled_reason` non-empty), and an unavailable count (from health/availability), plus a neutral placeholder when `tool_registry is None`.
3. Update the parenthetical label so it no longer claims the count comes from `config/tools_definitions.toml`.
4. Leave the per-tool `diagnostics()` table (lines 243-271) structurally intact; reuse the `tool_registry` fetched above.

### Method
Locate line 128 with `grep -n "Tools.*tool_definitions" scripts/agent/commands/cmd_mcp.py`; aggregate `diagnostics()` rows for the totals; re-run the `/mcp status` tests.

### Details
- `diagnostics()` returns one dict per registered tool (keys verified in `shared/runtime_tool_registry.py`): `name, server_key, config_dependent, enabled, disabled_reason, enabled_for_llm`. LLM-visible = rows with `enabled_for_llm` true; disabled = rows with a non-empty `disabled_reason`; unavailable = rows whose availability/health is unreachable.

## Compatibility considerations
Display-only change; the `Tools <count> …` line format is preserved.

## Security considerations
None beyond correctness of the displayed totals.

## Rollback considerations
Revert the commit.

## Validation plan
- A test asserts the displayed totals equal the registry's LLM-visible/disabled/unavailable counts when a registry is provided, and the placeholder when absent.
- `rg` confirms `_cmd_mcp_status` no longer reads `cfg.tool.tool_definitions` for the count.

## Completion criteria
- The `/mcp status` `Tools` line reports registry totals from `RuntimeToolRegistry`, not `cfg.tool.tool_definitions`.

## Out of Scope
- The `/help` tool-count display in `registry.py` (separate row, `REQ-003`).
- The per-tool `diagnostics()` table shape (unchanged).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 20261115-175105 | 20261115-175917 | STEP 1: replaced static count with registry totals (LLM-visible/disabled/unavailable) from diagnostics(); placeholder when registry None |
| 2 | Add or update tests per Validation plan | Completed | 20261115-175917 | 20261115-175917 | STEP 2: updated test_http_ok placeholder assertion; added test_status_line_reports_registry_totals |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20261115-175917 | 20261115-175917 | STEP 3: ruff/mypy/lint-imports/bandit clean; full suite 12246 passed (eventbus flake confirmed pre-existing) |

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
- **Requirement ID**: `REQ-002` — `/mcp status` counts must reflect RuntimeToolRegistry totals
- **Source issue**: `issues/20261111-163741_rtregistry001_runtime-registry-sole-authority.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261115-050235_rtregistry001_runtime-registry-sole-authority.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261115-090843
- **Related target files**: `scripts/agent/commands/cmd_mcp.py`