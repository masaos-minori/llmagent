## Goal

Make the `/help` tool-count line read runtime totals from `RuntimeToolRegistry` instead of the static config list. (`REQ-003`)

## Scope
**Release unit**: N/A: not part of a release unit

## Assumptions
- `ctx.services_required.runtime_tools` is available inside `_cmd_help`; when absent, show a neutral placeholder rather than the static count.
- The count is display-only.

## Design decisions
- Derive the count from `tool_registry.diagnostics()` (aggregated totals), matching the `/mcp status` derivation in `cmd_mcp.py` (`REQ-002`) so both displays stay consistent.

## Alternatives considered
- Keeping the static count: rejected by `REQ-003`.
- Reading a different config field: the registry is the single source, so count from it.

## Implementation
### Target file
`scripts/agent/commands/registry.py`

### Procedure
1. In `_cmd_help()` (around line 101), replace:
   ```python
   n_tools = len(ctx.cfg.tool.tool_definitions)
   ```
   with totals derived from `ctx.services_required.runtime_tools` (LLM-visible / disabled / unavailable aggregation of `diagnostics()`), falling back to a neutral placeholder when the registry is `None`.
2. Confirm the `Tools: {n_tools}` line at line 117 still renders with the new value.

### Method
Locate line 101 with `grep -n "n_tools = len" scripts/agent/commands/registry.py`; derive from the registry; run the registry/help tests.

### Details
- `diagnostics()` returns one dict per registered tool (keys `name, server_key, config_dependent, enabled, disabled_reason, enabled_for_llm`); aggregate into the same totals as `cmd_mcp.py` (`REQ-002`).
- The fail-fast handler validation in `__init__` (lines 73-85) is unrelated and unchanged.

## Compatibility considerations
Display-only change; the `Tools: <n>` format in the help footer is preserved.

## Security considerations
None beyond correctness of the displayed count.

## Rollback considerations
Revert the commit.

## Validation plan
- A test asserts the `/help` count equals the registry's totals when a registry is provided and the placeholder when absent.
- `rg` confirms `_cmd_help` no longer reads `cfg.tool.tool_definitions` for the count.

## Completion criteria
- The `/help` `Tools` count is derived from `RuntimeToolRegistry`, not `cfg.tool.tool_definitions`.

## Out of Scope
- The `/mcp status` tool-count display in `cmd_mcp.py` (separate row, `REQ-002`).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 20261115-184406 | 20261115-184406 | REQ-003: registry.py _cmd_help reads RuntimeToolRegistry totals; ruff/bandit/lint-imports/mypy pass; targeted tests pass |
| 2 | Add or update tests per Validation plan | Completed | 20261115-184406 | 20261115-184406 | targeted pytest pass (test_command_def_sync + test_cmd_mcp) |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20261115-184406 | 20261115-184406 | ruff format+check, bandit, lint-imports, mypy all clean |

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
- **Requirement ID**: `REQ-003` — `/help` tool count must reflect RuntimeToolRegistry
- **Source issue**: `issues/20261111-163741_rtregistry001_runtime-registry-sole-authority.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261115-050235_rtregistry001_runtime-registry-sole-authority.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261115-090843
- **Related target files**: `scripts/agent/commands/registry.py`