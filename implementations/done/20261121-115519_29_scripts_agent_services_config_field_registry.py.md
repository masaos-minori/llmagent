## Goal

Remove the four removed configuration fields from the hot-reload field registry (REQ-005, REQ-011; AC-05).

## Scope
**Release unit**: config-removal-and-tests

## Assumptions
- The field-set version value is `2.1` (UNK-01, owner decision 2026-11-21).

## Design decisions
- No entry is kept as a compatibility reader: a removed key is unknown and rejected.

## Alternatives considered
- N/A: the plan's design section fixes the shape of this change.

## Implementation
### Target file
`scripts/agent/services/config_field_registry.py`
### Procedure
- Delete the registry entries for `tool_safety_tiers`, `approval_risk_rules`, `approval_dry_run_tools` and `approval_resource_keys`, and the import of the removed validator.
### Method
- Keep every other entry and the validation call shape unchanged.
### Details
- Verified 2026-11-21: the entries carry the section name and the validator reference, so the import of `validate_tool_safety_tiers` and `validate_approval_risk_rules` must be checked against the remaining fields.

## Compatibility considerations
- Hot reload accepts only the fields that remain; this is the intended change to the field set.

## Security considerations
- N/A: no trust boundary is crossed by this file.

## Rollback considerations
- N/A: revert the commit within the release unit.

## Validation plan
- Run the validation sequence in `rules/toolchain.md`.

## Completion criteria
- The registry no longer lists a removed field, and a configuration containing one is reported as an unknown key.

## Out of Scope
- N/A: this document covers only its target file.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|---|---|---|---|---|---|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 2026-11-21 | 2026-11-21 | Gate lifted by owner decision 2026-11-21: issues/20261120-115845_mcpdl006_two-layer-failure-verification.md phase all - the reconciliation field values and the replay boundary are defined by that issue; Phase 5; release unit: config-removal-and-tests Implemented 2026-11-21 in config-removal sub-batch rows 28-33. |
| 2 | Add or update tests per Validation plan | Completed | 2026-11-21 | 2026-11-21 | Gate lifted by owner decision 2026-11-21: issues/20261120-115845_mcpdl006_two-layer-failure-verification.md phase all - the reconciliation field values and the replay boundary are defined by that issue test_config_dataclasses.py adapted (row 30 companion). Green: config_dataclasses, removed_config_keys_rejected, config_loader. |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | — | 20261121-203305 | Gate lifted by owner decision 2026-11-21: issues/20261120-115845_mcpdl006_two-layer-failure-verification.md phase all - the reconciliation field values and the replay boundary are defined by that issue ruff/format/mypy/lint-imports green for production files 2026-11-21. Allowed reds: test_config_builders (import, row 57), test_config_reload 14 (row 59), test_agent_cmd_config 15 (row 36 companion). unit-end validation: full suite 13314 passed / 7 skipped; ruff format+check clean; mypy 590 files clean; lint-imports 6 kept; diff-cover 97% (fail-under 90) |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | N/A | — | — | Gate lifted by owner decision 2026-11-21: issues/20261120-115845_mcpdl006_two-layer-failure-verification.md phase all - the reconciliation field values and the replay boundary are defined by that issue docs owned by rows 62-67. |

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
- **Requirement ID**: REQ-005, REQ-011
- **Source issue**: issues/20261120-114211_agentcfg003_runtime-tool-metadata.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261121-105007_agentcfg003_runtime-tool-metadata.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261121-115519
- **Related target files**: `scripts/agent/services/config_field_registry.py`