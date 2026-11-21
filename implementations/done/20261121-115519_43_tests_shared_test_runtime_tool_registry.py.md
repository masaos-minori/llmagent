## Goal

Assert that a policy application does not derive a tier from configuration (REQ-002, REQ-004, REQ-013 / T-02).

## Scope
**Release unit**: config-removal-and-tests

## Assumptions
- The fixture helpers build `RuntimeTool` instances, so they must carry the new required fields.

## Design decisions
- The assertions move from a configuration-derived tier to the tier the entry was declared with.

## Alternatives considered
- N/A: the plan's design section fixes the shape of this change.

## Implementation
### Target file
`tests/shared/test_runtime_tool_registry.py`
### Procedure
- Change `TestApplyPolicyReversibility` and the fixture helper `_registry_with()` to the reduced `apply_policy()` signature, and assert the lookup returns the declared tier.
### Method
- Add a case where a declared tier differs from what the removed configuration map would have produced, so the test cannot pass by coincidence.
### Details
- Verified 2026-11-21: this file is named by rows 04 and 39, so it keeps its own document.

## Compatibility considerations
- N/A: no public contract is changed by this file alone.

## Security considerations
- N/A: no trust boundary is crossed by this file.

## Rollback considerations
- N/A: revert the commit within the release unit.

## Validation plan
- `uv run pytest tests/shared/test_runtime_tool_registry.py -v`

## Completion criteria
- A policy application cannot change a declared tier, and the fixture supplies the required fields.

## Out of Scope
- N/A: this document covers only its target file.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|---|---|---|---|---|---|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | — | 20261121-193005 | Gate lifted by owner decision 2026-11-21: issues/20261120-115845_mcpdl006_two-layer-failure-verification.md phase all - the reconciliation field values and the replay boundary are defined by that issue; Phase 6; release unit: config-removal-and-tests tier_map kwargs removed from all apply_policy calls; fixture helper already used build_fixture_runtime_tool; added declared-tier cases where the removed tier_map would have produced ADMIN |
| 2 | Add or update tests per Validation plan | Completed | — | 20261121-193006 | Gate lifted by owner decision 2026-11-21: issues/20261120-115845_mcpdl006_two-layer-failure-verification.md phase all - the reconciliation field values and the replay boundary are defined by that issue new test_apply_policy_keeps_declared_tier plus the declared-tier-vs-removed-map case |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | — | 20261121-193006 | Gate lifted by owner decision 2026-11-21: issues/20261120-115845_mcpdl006_two-layer-failure-verification.md phase all - the reconciliation field values and the replay boundary are defined by that issue 49 passed; ruff check/format clean |
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
- **Requirement ID**: REQ-002, REQ-004, REQ-013
- **Source issue**: issues/20261120-114211_agentcfg003_runtime-tool-metadata.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261121-105007_agentcfg003_runtime-tool-metadata.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261121-115519
- **Related target files**: `tests/shared/test_runtime_tool_registry.py`