## Goal

Add `validate_tool_policy_mode` (new) (enum membership) and `validate_disabled_tools` (new) (names are registered tools) so startup and `/reload` reject an unknown mode, an unknown denylist name, and a mode/list mismatch (`REQ-003`, `REQ-006`).

## Scope
**Release unit**: N/A: not part of a release unit

## Assumptions
- `validate_tool_policy_mode` (new) accepts exactly `discovered` or `explicit_allowlist`; anything else raises.
- `validate_disabled_tools` (new) treats a name as valid only if it is registered in `RuntimeToolRegistry.get_all_tool_names()` (ADR-002 runtime authority).
- The existing `validate_allowed_tools` (line 144, empty list valid) stays type-only; the mode/list mismatch check lives here or in the production validator, not in the per-field validator.

## Design decisions
- Add the two validators next to `validate_allowed_tools` (line 144), mirroring the existing single-arg `ToolConfig` validator signature.
- Keep each validator type-only (raise on violation); the mode/list *combination* rule (non-empty `allowed_tools` required in `explicit_allowlist`, forbidden in `discovered`) is enforced by the production validator at load, matching the plan's split.

## Alternatives considered
- Folding the mode/list mismatch into these field validators: rejected because the mismatch needs both fields together and the production validator already owns cross-field load-time checks.

## Implementation
### Target file
`scripts/agent/services/config_validators.py`

### Procedure
Add `validate_tool_policy_mode(cfg: ToolConfig) -> None` and `validate_disabled_tools(cfg: ToolConfig) -> None` immediately after `validate_allowed_tools` (line 144).

### Method
Raise `ValueError` on the invalid case, mirroring the surrounding validators.

### Details
- `validate_tool_policy_mode` (new): raise unless `cfg.tool_policy_mode in {"discovered", "explicit_allowlist"}`.
- `validate_disabled_tools` (new): raise unless every entry of `cfg.disabled_tools` is in `RuntimeToolRegistry.get_all_tool_names()`.

## Compatibility considerations
Purely additive; existing validators and callers are untouched.

## Security considerations
Rejecting an unknown mode keeps the fail-closed default; rejecting an unknown denylist name prevents silently ignoring a disabled tool.

## Rollback considerations
N/A: revert the commit.

## Validation plan
`uv run pytest tests/agent/test_startup_validation.py` confirms unknown mode / unknown denylist name are rejected at startup.

## Completion criteria
Both validators exist, reject their invalid inputs, and register on `CONFIG_FIELD_REGISTRY`; the startup test passes.

## Out of Scope
Registry wiring (`config_field_registry.py`), load-time cross-field rules (`production_config_validator.py`), and runtime application.

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
- **Requirement ID**: `REQ-003`, `REQ-006`
- **Source issue**: `issues/20261120-114209_agentcfg001_tool-policy-mode.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261120-123941_agentcfg001_tool-policy-mode.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261120-132256
- **Related target files**: `scripts/agent/services/config_validators.py`
