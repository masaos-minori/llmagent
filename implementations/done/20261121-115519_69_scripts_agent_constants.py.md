## Goal

Remove the default constants for the removed maps so each concept has one source (REQ-011).

## Scope
**Release unit**: config-removal-and-tests

## Assumptions
- The constants are read only by the builders and the dataclass defaults, which are removed by rows 30 and 31; no test references them.

## Design decisions
- Leaving the definitions as dead constants would keep a second source for a concept the plan removes, so the definitions are deleted rather than left unused.

## Alternatives considered
- N/A: the plan's design section fixes the shape of this change.

## Implementation
### Target file
`scripts/agent/constants.py`
### Procedure
- Delete `_DEFAULT_APPROVAL_RISK_RULES`, `_DEFAULT_RESOURCE_KEYS` and `_DEFAULT_DRY_RUN_TOOLS` and their imports in the modules that used them.
### Method
- Keep `_DEFAULT_PLAN_BLOCKED_TOOLS`, `_DEFAULT_PROTECTED_PATHS`, the high-risk branch and allowed-repo defaults, and the shell safe prefixes: those are operational exceptions the plan keeps.
### Details
- Verified 2026-11-21: no test references these three constants; the test fixtures use their own mirror values, which the test rows update.

## Compatibility considerations
- N/A: no public contract is changed by this file alone.

## Security considerations
- N/A: no trust boundary is crossed by this file.

## Rollback considerations
- N/A: revert the commit within the release unit.

## Validation plan
- Run the validation sequence in `rules/toolchain.md`.

## Completion criteria
- The module defines no default value for a removed concept, and `uv run ruff check scripts/` reports no unused import.

## Out of Scope
- N/A: this document covers only its target file.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|---|---|---|---|---|---|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | — | 20261121-200925 | Gate lifted by owner decision 2026-11-21: issues/20261120-115845_mcpdl006_two-layer-failure-verification.md phase all - the reconciliation field values and the replay boundary are defined by that issue; Phase 5; release unit: config-removal-and-tests _DEFAULT_APPROVAL_RISK_RULES/_DEFAULT_RESOURCE_KEYS/_DEFAULT_DRY_RUN_TOOLS deleted; docstring updated (six->three tables, REQ-011 note); kept _DEFAULT_PLAN_BLOCKED_TOOLS/_DEFAULT_PROTECTED_PATHS/_DEFAULT_SHELL_SAFE_PREFIXES |
| 2 | Add or update tests per Validation plan | Completed | — | 20261121-200926 | Gate lifted by owner decision 2026-11-21: issues/20261120-115845_mcpdl006_two-layer-failure-verification.md phase all - the reconciliation field values and the replay boundary are defined by that issue grep shows zero remaining references outside the docstring itself |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | — | 20261121-200926 | Gate lifted by owner decision 2026-11-21: issues/20261120-115845_mcpdl006_two-layer-failure-verification.md phase all - the reconciliation field values and the replay boundary are defined by that issue config builders/dataclasses/reload suites 217 passed; ruff check/format clean; mypy clean |
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
- **Requirement ID**: REQ-011
- **Source issue**: issues/20261120-114211_agentcfg003_runtime-tool-metadata.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261121-105007_agentcfg003_runtime-tool-metadata.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261121-115519
- **Related target files**: `scripts/agent/constants.py`