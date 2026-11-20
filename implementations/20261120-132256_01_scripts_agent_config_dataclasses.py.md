## Goal

Declare the two new typed fields on `ToolConfig` and correct the stale `allowed_tools` comment so the dataclass states the mode-aware exposure contract instead of the old "Empty = all tools allowed" claim (`REQ-001`, `REQ-002`, `REQ-007`).

## Scope
**Release unit**: N/A: not part of a release unit

## Assumptions
- The default value of `tool_policy_mode` (new) is `explicit_allowlist` (new), so an absent config key resolves to explicit_allowlist without special-casing; membership is enforced at startup and `/reload` by a new validator added to `config_validators.py`.
- `disabled_tools` (new) is a hard denylist applied in both modes; its validation lives in `config_validators.py`, not here.
- Adding fields is backward compatible: no existing config sets these keys, and the section builder supplies the default when the key is absent.

## Design decisions
- Place `tool_policy_mode` (new) and `disabled_tools` (new) adjacent to `allowed_tools` in `ToolConfig` so the three exposure fields read as one group.
- Give `tool_policy_mode` (new) a concrete default (`explicit_allowlist` (new)) rather than an empty string, so the absent-key case is a valid enum value and the fail-closed default matches the current runtime. The enum accepts exactly `discovered` (new) or `explicit_allowlist` (new).

## Alternatives considered
- Empty-string default with resolution in the new validator: rejected because the plan fixes the absent-key meaning as `explicit_allowlist` (new), and a concrete default avoids a special case and keeps the field always-valid.

## Implementation
### Target file
`scripts/agent/config_dataclasses.py`

### Procedure
In `ToolConfig` (line 163), add two keyword arguments to the dataclass immediately after `allowed_tools`, and correct the `allowed_tools` field comment at line 216.

### Method
Mirror the surrounding field declarations; replace the stale "Empty = all tools allowed" comment with the mode-aware contract.

### Details
- Add `tool_policy_mode: str = "explicit_allowlist"` (new) after `allowed_tools`.
- Add `disabled_tools: list[str] = field(default_factory=list)` after `tool_policy_mode` (new).
- Rewrite the `allowed_tools` comment (line 216) to state that emptiness is mode-dependent: valid and non-denying in `discovered` (new), fatal in `explicit_allowlist` (new).

## Compatibility considerations
Backward compatible: no existing config sets either key, and the builder supplies a safe default when the key is absent.

## Security considerations
The `explicit_allowlist` (new) default is fail-closed and matches the current runtime, so an absent key cannot widen tool visibility.

## Rollback considerations
N/A: revert the commit.

## Validation plan
`uv run pytest tests/agent/test_startup_validation.py` confirms the fields exist and populate from raw config.

## Completion criteria
`ToolConfig` exposes `tool_policy_mode` (new) and `disabled_tools` (new) populated from raw config (or the documented defaults), the comment no longer claims "Empty = all tools allowed", and the startup test passes.

## Out of Scope
Section builder (`config_section_builders.py`), validators (`config_validators.py`), registry wiring (`config_field_registry.py`), and runtime application (`tool_policy.py`, `runtime_tool_registry.py`).

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
- **Requirement ID**: `REQ-001`, `REQ-002`, `REQ-007`
- **Source issue**: `issues/20261120-114209_agentcfg001_tool-policy-mode.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261120-123941_agentcfg001_tool-policy-mode.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261120-132256
- **Related target files**: `scripts/agent/config_dataclasses.py`
