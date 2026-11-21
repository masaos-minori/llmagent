## Goal

Make the tier checks drift reports rather than decision inputs (REQ-007; AC-10).

## Scope
**Release unit**: contract-and-producers

## Assumptions
- The field-set version value is `2.1` (UNK-01, owner decision 2026-11-21).

## Design decisions
- The checks compare declared metadata with the reference data and return findings; nothing that reads the result changes a decision.

## Alternatives considered
- N/A: the plan's design section fixes the shape of this change.

## Implementation
### Target file
`scripts/shared/tool_routing_validation.py`
### Procedure
- Change `check_tool_safety_tiers()` and `check_unknown_tool_safety_tiers()` to compare declared tiers with the reference data, and remove the configuration-map argument.
### Method
- Read the registry's declared tiers instead of `cfg.approval.tool_safety_tiers`; keep the message shape so the callers' report paths do not change.
- Keep the startup consequence owned by ADR-004 as it is written today, and do not restate it here.
### Details
- Verified 2026-11-21: both functions are called from `scripts/agent/services/routing_drift.py`, which is updated by row 37; `test_tool_routing_validation.py` is not a row of this plan.

## Compatibility considerations
- `scripts/agent/services/routing_drift.py` (row 37) is the only production caller; it stays red until its own cycle lands (allowed red in the release unit).
- `tests/shared/test_tool_routing_validation.py` is not a row of this Plan but is this row's plan-listed companion test file; its `apply_policy(tier_map=...)` fixtures (red from row 04) and tier fixtures are mechanically adapted on this row so the end-of-unit full suite can pass.

## Security considerations
- N/A: no trust boundary is crossed by this file.

## Rollback considerations
- N/A: revert the commit within the release unit.

## Validation plan
- Run the validation sequence in `rules/toolchain.md`.

## Completion criteria
- A disagreement is reported as a finding, and no caller uses the result to classify a tool.

## Out of Scope
- Redesign of the fixtures in `tests/shared/test_tool_routing_validation.py` beyond the mechanical signature adaptation this row needs (a follow-up test-audit work item may restructure them).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|---|---|---|---|---|---|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | — | 2026-11-21 | Gate lifted by owner decision 2026-11-21: issues/20261120-115845_mcpdl006_two-layer-failure-verification.md phase all - the reconciliation field values and the replay boundary are defined by that issue; Phase 4; release unit: contract-and-producers Implemented: config-map arg removed; checks compare seed registry vs live declared tiers. |
| 2 | Add or update tests per Validation plan | Completed | — | 2026-11-21 | Gate lifted by owner decision 2026-11-21: issues/20261120-115845_mcpdl006_two-layer-failure-verification.md phase all - the reconciliation field values and the replay boundary are defined by that issue test_tool_routing_validation.py mechanically adapted (apply_policy tier_map removed, strict builder fields added): 27 passed. |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | — | 20261121-203301 | Gate lifted by owner decision 2026-11-21: issues/20261120-115845_mcpdl006_two-layer-failure-verification.md phase all - the reconciliation field values and the replay boundary are defined by that issue Targeted gates green 2026-11-21. Allowed reds: routing_drift.py:23 call-arg mypy (row 37), tests/shared/test_tool_safety_tiers.py TypeError on removed kwarg (row 45). unit-end validation: full suite 13314 passed / 7 skipped; ruff format+check clean; mypy 590 files clean; lint-imports 6 kept; diff-cover 97% (fail-under 90) |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | N/A | — | — | Gate lifted by owner decision 2026-11-21: issues/20261120-115845_mcpdl006_two-layer-failure-verification.md phase all - the reconciliation field values and the replay boundary are defined by that issue |

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
- **Requirement ID**: REQ-007
- **Source issue**: issues/20261120-114211_agentcfg003_runtime-tool-metadata.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261121-105007_agentcfg003_runtime-tool-metadata.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261121-115519
- **Related target files**: `scripts/shared/tool_routing_validation.py`