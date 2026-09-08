# Implementation Procedure: Add _check_unknown_production_keys() method

## Traceability
- **Source issue**: issues/20260907-131738_h02b_config_loader_fail_closed_remaining_gaps.md
- **Source plan**: plans/20260907-234317_plan.md
- **Related target files**: scripts/shared/production_config_validator.py

## Goal
Add `_check_unknown_production_keys()` method using `dataclasses.fields()` introspection to reject unknown/mistyped top-level config keys during production config loading.

## Priority
High

## Scope
- **In-Scope**: Add _check_unknown_production_keys() method using dataclasses.fields() introspection
- **Out-of-Scope**: Changes to ProductionConfigValidator's existing tool_safety_tiers/approval_risk_rules check logic

## Background
`scripts/shared/production_config_validator.py` has no general unknown-top-level-key rejection — only the narrower `tool_safety_tiers`-specific bidirectional check (`_check_missing_tool_safety_tiers`/`_check_unknown_tool_safety_tiers`) exists (REQ-004 unmet). The new method should use `dataclasses.fields()` introspection on all sub-config classes to derive valid config keys dynamically rather than hardcoding them.

## Problem
No general unknown-top-level-key rejection exists in ProductionConfigValidator, allowing mistyped config keys to pass validation silently.

## Reason for change
This is a security fix — unknown config keys could indicate misconfiguration that should fail closed rather than being silently ignored.

## Implementation Steps

### Step 1: Introspect all sub-config classes
Read `scripts/agent/config_dataclasses.py` to identify all sub-config classes:
- LLMConfig, RAGConfig, ToolConfig, MemoryConfig, MCPConfig, ApprovalConfig, ObservabilityConfig, DiagnosticsConfig, MessageRoleConfig

For each class, collect field names via `dataclasses.fields()`:
```python
import dataclasses
from scripts.agent.config_dataclasses import (
    LLMConfig, RAGConfig, ToolConfig, MemoryConfig,
    MCPConfig, ApprovalConfig, ObservabilityConfig,
    DiagnosticsConfig, MessageRoleConfig
)

valid_keys = set()
for cls in [LLMConfig, RAGConfig, ToolConfig, MemoryConfig,
            MCPConfig, ApprovalConfig, ObservabilityConfig,
            DiagnosticsConfig, MessageRoleConfig]:
    for field in dataclasses.fields(cls):
        valid_keys.add(field.name)
```
Expected outcome: Valid key set derived from all sub-config classes.

### Step 2: Implement _check_unknown_production_keys()
Add the method to ProductionConfigValidator:
```python
def _check_unknown_production_keys(self, config: dict) -> list[str]:
    """Reject unknown/mistyped top-level config keys."""
    known_keys = self._get_valid_production_keys()  # from Step 1
    unknown_keys = []
    for key in config:
        if key not in known_keys:
            unknown_keys.append(key)
    return unknown_keys
```
Expected outcome: Method returns list of unknown keys found in the config dict.

### Step 3: Call the new method during validation
Integrate `_check_unknown_production_keys()` into the existing validation flow, likely alongside `_check_missing_production_keys()` and `_check_unknown_tool_safety_tiers()`.
Expected outcome: Unknown keys are rejected during production config loading.

### Step 4: Verify no cross-file conflicts
Check whether any other validators or config loaders need similar changes:
Run: `rg "_check_unknown.*keys\|unknown.*key.*reject" scripts/`
Expected outcome: Only the new method in production_config_validator.py handles unknown keys.

## Acceptance criteria
- [ ] _check_unknown_production_keys() method added
- [ ] Valid keys derived from dataclasses.fields() introspection
- [ ] Unknown keys rejected during production config loading
- [ ] REQ-004 satisfied

## Tests
New unit test for unknown-key rejection in `tests/agent/test_startup.py` (see related target file).

## Documentation Impact
Yes: ADR-002 and ADR-004 documentation updates required (see related target files).

## Dependencies
- REQ-004: ProductionConfigValidator rejects unknown/mistyped top-level config keys
- Reference file: scripts/agent/config_dataclasses.py (must be read to derive valid keys)

## Assumptions
- TOML-key-to-dataclass-field mapping is direct (no nesting conflicts)
- All sub-config classes have their fields defined via dataclass decorators

## Unknowns
| ID | Unknown Description | Evidence Missing | Resolution Path | Blocking? (True/False) |
|---|---|---|---|---|
| UNK-01 | Whether the introspected field names from all sub-config classes map directly to TOML top-level keys without nesting conflicts | Need to verify TOML structure matches dataclass hierarchy exactly | Compare TOML key paths against dataclass field names | False |
| UNK-02 | Whether existing ProductionConfigValidator checks in other environments (development/staging) need identical unknown-key logic | Only production environment checked so far | Verify validator instantiation across all environments | False |

## Affected areas
`skills/DESIGN.md` Change-impact table — medium blast radius (new validation path).

## Design
This is a Path B task (> 3 files affected, interface changes). The approach uses dynamic key discovery: `dataclasses.fields()` introspection on all sub-config classes derives the valid key set at runtime, avoiding hardcoding.

## Alternatives considered
- Hardcoding the valid key set — rejected because it requires manual maintenance and is error-prone
- Using pydantic model_dump() to validate — rejected because it adds a dependency and doesn't address the root cause (TOML key validation)

## Compatibility considerations
- Unknown keys will now be rejected in production — verify existing configs don't contain mistyped keys before deploying
- Development/staging environments may also need the same validation — check UNK-02

## Security considerations
- This is a security fix — unknown config keys could indicate misconfiguration that should fail closed
- The validation should be strict in production but consider relaxing in development/staging

## Rollback considerations
- If the unknown-key rejection rejects legitimate keys, revert the validation logic temporarily while investigating TOML key paths
- Ensure rollback procedure includes verifying TOML key paths against dataclass fields

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Introspect sub-config classes | Pending | — | — | |
| 2 | Implement _check_unknown_production_keys() | Pending | — | — | |
| 3 | Integrate into validation flow | Pending | — | — | |
| 4 | Verify no cross-file conflicts | Pending | — | — | |

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
- **Source issue**: issues/20260907-131738_h02b_config_loader_fail_closed_remaining_gaps.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260907-234317_plan.md
- **Source implementation procedure**: N/A: not applicable in this phase
- **Generated at**: 20260908-093609
- **Related target files**: scripts/shared/production_config_validator.py

(End of file - total 100 lines)
