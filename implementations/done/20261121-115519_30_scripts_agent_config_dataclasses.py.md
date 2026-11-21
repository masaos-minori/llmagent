## Goal

Remove the four map fields from the approval configuration dataclass (REQ-005, REQ-006, REQ-008; AC-05, AC-06).

## Scope
**Release unit**: config-removal-and-tests

## Assumptions
- The field-set version value is `2.1` (UNK-01, owner decision 2026-11-21).

## Design decisions
- The dataclass keeps the operational exceptions only: protected paths, high-risk branches, allowed repos, and the raise-only exceptions.
- `plan_blocked_tools` stays as the documented exception denylist; it is not derived from a declared field and is not removed.

## Alternatives considered
- N/A: the plan's design section fixes the shape of this change.

## Implementation
### Target file
`scripts/agent/config_dataclasses.py`
### Procedure
- Delete the four field definitions and the default-factory use of the removed constants (row 69).
### Method
- Keep every other field, its default and its validator wiring unchanged.
### Details
- Verified 2026-11-21: the four fields are built with `default_factory` from the constants in `scripts/agent/constants.py`, which becomes dead once this row lands.
### Companion test files
- `tests/agent/test_config_dataclasses.py`
  - Procedure: Remove the field-level assertions for the four removed maps from `TestApprovalConfigValidation` and keep the operational-exception fields asserted (T-05).
  - Validation: `uv run pytest tests/agent/test_config_dataclasses.py -v`

## Compatibility considerations
- N/A: no public contract is changed by this file alone.

## Security considerations
- N/A: no trust boundary is crossed by this file.

## Rollback considerations
- N/A: revert the commit within the release unit.

## Validation plan
- Run the validation sequence in `rules/toolchain.md`.

## Completion criteria
- No removed map field exists on the dataclass, and no default value for a removed concept remains in the module.

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
- **Requirement ID**: REQ-005, REQ-006, REQ-008
- **Source issue**: issues/20261120-114211_agentcfg003_runtime-tool-metadata.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261121-105007_agentcfg003_runtime-tool-metadata.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261121-115519
- **Related target files**: `scripts/agent/config_dataclasses.py`, `tests/agent/test_config_dataclasses.py`