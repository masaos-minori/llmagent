## Goal

Update the `allowed_tools` display to reflect the resolved `tool_policy_mode` instead of the unconditional "(none: all tools denied)" (`REQ-007`).

## Scope
**Release unit**: N/A: not part of a release unit

## Assumptions
- `ctx.cfg.tool.tool_policy_mode` is available at display time and already validated.
- An empty `allowed_tools` is valid in `discovered` mode (base visibility applies) and fatal in `explicit_allowlist` mode.

## Design decisions
- In the `allowed_tools` display branch (lines 120-124), branch on `ctx.cfg.tool.tool_policy_mode` for the empty case: show a `discovered`-mode message when empty, and keep "(none: all tools denied)" semantics only under `explicit_allowlist`.

## Alternatives considered
- Always showing "(none: all tools denied)": rejected because it is false in `discovered` mode where an empty list is valid and non-denying.

## Implementation
### Target file
`scripts/agent/commands/cmd_config_display.py`

### Procedure
In the `allowed_tools` display block (lines 120-124), replace the single empty-case string with a mode-aware one.

### Method
Branch on `ctx.cfg.tool.tool_policy_mode` in the `else` (empty) arm.

### Details
- Non-empty: keep `", ".join(allowed_tools)`.
- Empty + `discovered`: e.g. `(none: discovered mode — base visibility applies)`.
- Empty + `explicit_allowlist`: `(none: all tools denied)`.

## Compatibility considerations
Display-only change; no behavior change. The new message is accurate under both modes.

## Security considerations
No security impact: the display reflects the resolved mode; enforcement is unchanged.

## Rollback considerations
N/A: revert the commit.

## Validation plan
`uv run pytest tests/agent/commands/test_cmd_config_char.py` confirms the expected display string.

## Completion criteria
The `allowed_tools` display reflects the resolved mode; the char/display test passes.

## Out of Scope
Enforcement logic (`tool_policy.py`, `runtime_tool_registry.py`).

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

### Companion test files
- `tests/agent/commands/test_cmd_config_char.py`
  - Procedure: update the expected `allowed_tools` display string for the empty/discovered case.
  - Validation: `uv run pytest tests/agent/commands/test_cmd_config_char.py` passes.

## Traceability
- **Workflow phase**: plan-to-implementation-procedure
- **Requirement ID**: `REQ-007`
- **Source issue**: `issues/20261120-114209_agentcfg001_tool-policy-mode.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261120-123941_agentcfg001_tool-policy-mode.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261120-132256
- **Related target files**: `scripts/agent/commands/cmd_config_display.py`, `tests/agent/commands/test_cmd_config_char.py`
