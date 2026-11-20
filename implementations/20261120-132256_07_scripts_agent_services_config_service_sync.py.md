## Goal

Pass the resolved `tool_policy_mode` and `disabled_tools` into `RuntimeToolRegistry.apply_policy` so the new policy inputs propagate through `sync_all` on startup and `/reload` (`REQ-005`).

## Scope
**Release unit**: `apply_policy` signature change — updating this caller together with the signature change in one commit; they cannot be validated alone.

## Assumptions
- `ctx.cfg.tool.tool_policy_mode` and `ctx.cfg.tool.disabled_tools` are populated from config (by `config_section_builders.py`) and validated (by `config_validators.py`).
- `apply_policy` gains the two new keyword parameters (declared in `runtime_tool_registry.py`).

## Design decisions
- Add `tool_policy_mode=ctx.cfg.tool.tool_policy_mode` and `disabled_tools=ctx.cfg.tool.disabled_tools` to the existing `apply_policy(...)` call at line 76, alongside the existing `tier_map=` and `allowed_tools=` kwargs.

## Alternatives considered
- Deriving the values inside `sync_all`: rejected because the plan forwards the already-resolved `cfg.tool` fields unchanged.

## Implementation
### Target file
`scripts/agent/services/config_service_sync.py`

### Procedure
At the `apply_policy(...)` call (line 76), add the two new keyword arguments from `ctx.cfg.tool`.

### Method
Extend the existing call expression; keep `tier_map=` and `allowed_tools=` unchanged.

### Details
- Add `tool_policy_mode=ctx.cfg.tool.tool_policy_mode`.
- Add `disabled_tools=ctx.cfg.tool.disabled_tools`.

## Compatibility considerations
Caller update lands in the same commit as the signature change (release unit above); no standalone-validating state.

## Security considerations
No change to the enforcement logic; only the policy inputs are forwarded, so fail-closed behavior is preserved.

## Rollback considerations
N/A: revert the commit.

## Validation plan
`uv run pytest tests/agent/services/test_config_reload.py` confirms the inputs reach `apply_policy` and visibility is correct after `/reload`.

## Completion criteria
`sync_all` forwards both new inputs to `apply_policy`; the reload test passes.

## Out of Scope
`apply_policy` definition (`runtime_tool_registry.py`) and the reload transaction (`config_reload.py`).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | Gated: issues/20261119-145303_cliplc005_staged-reload-transaction.md phase all - same field registry, validators, and Memory reload validation; second to land re-verifies its tests; AND issues/20261120-114210_agentcfg002_tool-catalog-registry.md phase all - removes the tool lists explicit_allowlist mode depends on; second to land re-verifies its tests |
| 2 | Add or update tests per Validation plan | Pending | — | — | Gated: issues/20261119-145303_cliplc005_staged-reload-transaction.md phase all - same field registry, validators, and Memory reload validation; second to land re-verifies its tests; AND issues/20261120-114210_agentcfg002_tool-catalog-registry.md phase all - removes the tool lists explicit_allowlist mode depends on; second to land re-verifies its tests |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | Gated: issues/20261119-145303_cliplc005_staged-reload-transaction.md phase all - same field registry, validators, and Memory reload validation; second to land re-verifies its tests; AND issues/20261120-114210_agentcfg002_tool-catalog-registry.md phase all - removes the tool lists explicit_allowlist mode depends on; second to land re-verifies its tests |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------|----------|-----------------|
| — | — | — | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| — | — | — | — | — | — |

## Traceability
- **Workflow phase**: plan-to-implementation-procedure
- **Requirement ID**: `REQ-005`
- **Source issue**: `issues/20261120-114209_agentcfg001_tool-policy-mode.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261120-123941_agentcfg001_tool-policy-mode.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261120-132256
- **Related target files**: `scripts/agent/services/config_service_sync.py`
