## Goal

Register `validate_tool_policy_mode` and `validate_disabled_tools` on `CONFIG_FIELD_REGISTRY` so the two new fields route through the validated reload path (`REQ-006`).

## Scope
**Release unit**: N/A: not part of a release unit

## Assumptions
- The two validators exist in `config_validators.py` (declared `(new)` there, resolved as siblings here).
- The registry entry pattern mirrors the existing `allowed_tools` entry (line 83): a `ConfigFieldRegistry(name, section, required, validator)`.

## Design decisions
- Add the two entries adjacent to the `allowed_tools` entry (line 83) under the Tool section, reusing the validators imported at the top of the file.
- Keep the same shape as neighboring entries so the registry stays uniform.

## Alternatives considered
- Defining the validators inline in the registry entry: rejected for consistency with the existing single-responsibility validator functions.

## Implementation
### Target file
`scripts/agent/services/config_field_registry.py`

### Procedure
Add two `ConfigFieldRegistry(...)` entries for `tool_policy_mode` and `disabled_tools` right after the `allowed_tools` entry (line 83), and ensure the two validators are imported.

### Method
Mirror the `allowed_tools` entry's structure and the Tool-section column layout.

### Details
- `ConfigFieldRegistry("tool_policy_mode", "tool", True, validate_tool_policy_mode)`
- `ConfigFieldRegistry("disabled_tools", "tool", True, validate_disabled_tools)`
- Import `validate_tool_policy_mode`, `validate_disabled_tools` from `config_validators` if not already present.

## Compatibility considerations
Purely additive registry entries; no existing entry changes.

## Security considerations
Routing the new fields through the registry guarantees they are validated on the reload path, closing a gap where an unvalidated field could bypass startup/reload checks.

## Rollback considerations
N/A: revert the commit.

## Validation plan
`uv run pytest tests/agent/services/test_config_reload.py` confirms the new fields are validated on the reload path.

## Completion criteria
Both validators are registered on `CONFIG_FIELD_REGISTRY`; the reload validation test passes.

## Out of Scope
Validator bodies (`config_validators.py`) and load-time cross-field rules (`production_config_validator.py`).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 20261120-182438 | 20261120-182438 | Gated: issues/20261119-145303_cliplc005_staged-reload-transaction.md phase all - same field registry, validators, and Memory reload validation; second to land re-verifies its tests; AND issues/20261120-114210_agentcfg002_tool-catalog-registry.md phase all - removes the tool lists explicit_allowlist mode depends on; second to land re-verifies its tests STEP: Added ConfigFieldRegistry entries for tool_policy_mode/disabled_tools after allowed_tools; imported both validators. Regenerated registry/manifests (agent_api.yaml, config_ownership.yaml) + docs/23_agent/agent_14 via generate_reference_table.py --manifests (mechanical addition of the two fields/validators; no drift). |
| 2 | Add or update tests per Validation plan | Completed | 20261120-182438 | 20261120-182438 | Gated: issues/20261119-145303_cliplc005_staged-reload-transaction.md phase all - same field registry, validators, and Memory reload validation; second to land re-verifies its tests; AND issues/20261120-114210_agentcfg002_tool-catalog-registry.md phase all - removes the tool lists explicit_allowlist mode depends on; second to land re-verifies its tests STEP: Updated TestRegistryFieldClassification.test_tool_section_fields_are_classified_correctly expected set (+tool_policy_mode,+disabled_tools); added nothing else. |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20261120-182438 | 20261120-182438 | Gated: issues/20261119-145303_cliplc005_staged-reload-transaction.md phase all - same field registry, validators, and Memory reload validation; second to land re-verifies its tests; AND issues/20261120-114210_agentcfg002_tool-catalog-registry.md phase all - removes the tool lists explicit_allowlist mode depends on; second to land re-verifies its tests STEP: ruff clean; mypy clean; generate_reference_table --check 'No drift'; 27 ref-table + 69 reload tests passed. |

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
- **Requirement ID**: `REQ-006`
- **Source issue**: `issues/20261120-114209_agentcfg001_tool-policy-mode.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261120-123941_agentcfg001_tool-policy-mode.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261120-132256
- **Related target files**: `scripts/agent/services/config_field_registry.py`