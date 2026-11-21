## Goal

Remove the display lines for the removed maps (REQ-05 placeholder; AC-05).

## Scope
**Release unit**: contract-and-producers

## Assumptions
- The field-set version value is `2.1` (UNK-01, owner decision 2026-11-21).

## Design decisions
- No substitute line is added: the values they showed no longer exist as configuration.

## Alternatives considered
- N/A: the plan's design section fixes the shape of this change.

## Implementation
### Target file
`scripts/agent/commands/cmd_config_display.py`
### Procedure
- Remove the risk-rule, dry-run, tool-safety-count lines from the approval and tool-safety display sections.
### Method
- Keep the remaining display sections and the output shape unchanged.
### Details
- Verified 2026-11-21: the display reads `approval_risk_rules`, `approval_dry_run_tools` and the count of `tool_safety_tiers` entries.
### Companion test files
- `tests/agent/commands/test_agent_cmd_config.py`
  - Procedure: Remove the four assertions on the removed maps in `TestPrintConfigValues` and `TestApplyConfigDict` (T-05).
  - Validation: `uv run pytest tests/agent/commands/test_agent_cmd_config.py -v`

## Compatibility considerations
- N/A: no public contract is changed by this file alone.

## Security considerations
- N/A: no trust boundary is crossed by this file.

## Rollback considerations
- N/A: revert the commit within the release unit.

## Validation plan
- Run the validation sequence in `rules/toolchain.md`.

## Completion criteria
- The config display prints no line for a removed field.

## Out of Scope
- N/A: this document covers only its target file.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|---|---|---|---|---|---|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 2026-11-21 | 2026-11-21 | Gate lifted by owner decision 2026-11-21: issues/20261120-115845_mcpdl006_two-layer-failure-verification.md phase all - the reconciliation field values and the replay boundary are defined by that issue; Phase 4; release unit: contract-and-producers Implemented 2026-11-21 with companion tests in same sub-batch. |
| 2 | Add or update tests per Validation plan | Completed | 2026-11-21 | 2026-11-21 | Gate lifted by owner decision 2026-11-21: issues/20261120-115845_mcpdl006_two-layer-failure-verification.md phase all - the reconciliation field values and the replay boundary are defined by that issue test_agent_mcp_status.py TestTierForServer rewritten on declared tiers; test_agent_cmd_config.py removed-map cases converted to REQ-011 negative cases. 52 passed. |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | — | 20261121-203306 | Gate lifted by owner decision 2026-11-21: issues/20261120-115845_mcpdl006_two-layer-failure-verification.md phase all - the reconciliation field values and the replay boundary are defined by that issue ruff/format/mypy/lint-imports green 2026-11-21. unit-end validation: full suite 13314 passed / 7 skipped; ruff format+check clean; mypy 590 files clean; lint-imports 6 kept; diff-cover 97% (fail-under 90) |
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
- **Requirement ID**: REQ-005
- **Source issue**: issues/20261120-114211_agentcfg003_runtime-tool-metadata.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261121-105007_agentcfg003_runtime-tool-metadata.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261121-115519
- **Related target files**: `scripts/agent/commands/cmd_config_display.py`, `tests/agent/commands/test_agent_cmd_config.py`