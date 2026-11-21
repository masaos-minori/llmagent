## Goal

Assert the tier checks report drift only, with no decision effect (REQ-007, REQ-013 / T-09).

## Scope
**Release unit**: config-removal-and-tests

## Assumptions
- No field-set version value is asserted here; the value is UNK-01.

## Design decisions
- The fixture that reads the real `config/agent.toml` tiers (`_real_tool_safety_tiers()`) becomes a comparison against declared metadata.

## Alternatives considered
- N/A: the plan's design section fixes the shape of this change.

## Implementation
### Target file
`tests/shared/test_tool_safety_tiers.py`
### Procedure
- Change `TestRealAgentTomlSafetyTiers` and `TestUnknownToolSafetyTiersEarlyReturn` to the removed configuration argument, and assert the result is a finding rather than a classification.
### Method
- Keep the early-return case as a no-finding case for an empty registry.
### Details
- Verified 2026-11-21: 20 direct references to the removed map in this file.

## Compatibility considerations
- N/A: no public contract is changed by this file alone.

## Security considerations
- N/A: no trust boundary is crossed by this file.

## Rollback considerations
- N/A: revert the commit within the release unit.

## Validation plan
- `uv run pytest tests/shared/test_tool_safety_tiers.py -v`

## Completion criteria
- No assertion in this file depends on a removed configuration map.

## Out of Scope
- The test file that exercises the shared tier check through fixtures only (follow-up test-audit work item).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|---|---|---|---|---|---|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | Gated: issues/20261120-115845_mcpdl006_two-layer-failure-verification.md phase all - the reconciliation field values and the replay boundary are defined by that issue; Phase 6; release unit: config-removal-and-tests |
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
- **Requirement ID**: REQ-007, REQ-013
- **Source issue**: issues/20261120-114211_agentcfg003_runtime-tool-metadata.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261121-105007_agentcfg003_runtime-tool-metadata.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261121-115519
- **Related target files**: `tests/shared/test_tool_safety_tiers.py`
