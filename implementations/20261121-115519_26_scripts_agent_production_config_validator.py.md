## Goal

Remove the tier-map validation and move the fail-closed check to declared metadata (REQ-004, REQ-011; AC-04, AC-05).

## Scope
**Release unit**: contract-and-producers

## Assumptions
- No field-set version value is asserted here; the value is UNK-01.

## Design decisions
- The removed keys become unknown keys and are rejected through the normal unknown-key path; no compatibility reader is added (REQ-011).
- The risk floor for the git tools stays, but its input becomes the declared tier/risk rather than a configuration map.

## Alternatives considered
- N/A: the plan's design section fixes the shape of this change.

## Implementation
### Target file
`scripts/agent/production_config_validator.py`
### Procedure
- Remove `_check_missing_tool_safety_tiers()` and `_check_unknown_tool_safety_tiers()`, drop the removed keys from `_get_valid_production_keys()`, and express the fail-closed case as a missing declared field.
### Method
- Keep the `_check_approval_risk_floor()` outcome for the named git tools, reading it from declared metadata.
- The registry-facing `validate_against_registry()` keeps its reporting shape.
### Details
- Verified 2026-11-21: `_check_unknown_tool_safety_tiers()` is called from `validate()`; both tier checks read the removed map.
### Companion test files
- `tests/agent/test_production_config_validator.py`
  - Procedure: Remove the tier-map cases (`TestProductionConfigValidatorSafetyTiers`, `TestProductionConfigValidatorValidateUnknownToolSafetyTiers`) and add the fail-closed missing-field and unknown-key cases; keep the risk-floor group reading declared metadata (T-02, T-05).
  - Validation: `uv run pytest tests/agent/test_production_config_validator.py -v`

## Compatibility considerations
- N/A: no public contract is changed by this file alone.

## Security considerations
- A stale deployed `config/agent.toml` fails at startup with a named key; that is the intended behaviour, not a fallback kept for removed configuration.

## Rollback considerations
- N/A: revert the commit within the release unit.

## Validation plan
- Run the validation sequence in `rules/toolchain.md`.

## Completion criteria
- A configuration that still contains a removed map is rejected as an unknown key with the key named, and no tier-map check remains.

## Out of Scope
- N/A: this document covers only its target file.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|---|---|---|---|---|---|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | Gated: issues/20261120-115845_mcpdl006_two-layer-failure-verification.md phase all - the reconciliation field values and the replay boundary are defined by that issue; Phase 4; release unit: contract-and-producers |
| 2 | Add or update tests per Validation plan | Pending | — | — | Gated: issues/20261120-115845_mcpdl006_two-layer-failure-verification.md phase all - the reconciliation field values and the replay boundary are defined by that issue |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | Gated: issues/20261120-115845_mcpdl006_two-layer-failure-verification.md phase all - the reconciliation field values and the replay boundary are defined by that issue |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Pending | — | — | Gated: issues/20261120-115845_mcpdl006_two-layer-failure-verification.md phase all - the reconciliation field values and the replay boundary are defined by that issue |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|---|---|---|---|
| — | — | — | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---|---|---|---|---|---|
| — | — | — | — | — | — |

## Traceability
- **Workflow phase**: plan-to-implementation-procedure
- **Requirement ID**: REQ-004, REQ-011
- **Source issue**: issues/20261120-114211_agentcfg003_runtime-tool-metadata.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261121-105007_agentcfg003_runtime-tool-metadata.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261121-115519
- **Related target files**: `scripts/agent/production_config_validator.py`, `tests/agent/test_production_config_validator.py`
