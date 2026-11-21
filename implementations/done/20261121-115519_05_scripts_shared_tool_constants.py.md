## Goal

Demote the static tool-name sets to reference data used only for drift detection and tests, and move `RETRYABLE_TOOLS` ownership to the declared retry policy (REQ-007; AC-04, AC-10).

## Scope
**Release unit**: contract-and-producers

## Assumptions
- The per-server tool lists used inside an MCP server for its own write-protection gate are out of scope (UNK-05).

## Design decisions
- The sets stay in the module as reference data because the drift checks need something to compare a declaration against; what changes is that no decision reads them.
- `RETRYABLE_TOOLS` is kept as reference data only, with a note that the declared `retry_policy` is the authority; the ownership statement is recorded in the ADR change (row 67).

## Alternatives considered
- N/A: the plan's design section fixes the shape of this change.

## Implementation
### Target file
`scripts/shared/tool_constants.py`
### Procedure
- Mark the sets as reference data in the module docstring and comments, and remove their use as a decision input from this module's own helpers.
### Method
- Keep the existing `READ_TOOLS`, `WRITE_TOOLS`, `DELETE_TOOLS`, `RETRYABLE_TOOLS` and the per-server sets unchanged in content; the change is the stated role, so a reader cannot mistake a drift report for a decision.
- Keep the existing note that the classification dimensions are not to be conflated, and restate it in terms of declared fields.
### Details
- Verified 2026-11-21: `RETRYABLE_TOOLS` is currently named as the single source of truth by `scripts/agent/tool_runner.py`, which credits ADR-008; that credit is what the ADR row records as moved.
### Companion test files
- `tests/shared/test_tool_constants.py`
  - Procedure: Rewrite the ownership assertions at lines 103, 117 and 127 as drift comparisons against declared metadata rather than ownership of `RETRYABLE_TOOLS` (T-08, T-09).
  - Validation: `uv run pytest tests/shared/test_tool_constants.py -v`

## Compatibility considerations
- Tests that assert ownership of `RETRYABLE_TOOLS` are updated by the companion test file listed on this row.

## Security considerations
- N/A: no trust boundary is crossed by this file.

## Rollback considerations
- N/A: revert the commit within the release unit.

## Validation plan
- Run the validation sequence in `rules/toolchain.md`.

## Completion criteria
- No runtime decision reads a set in this module; only drift comparisons and tests read it.
- The drift test against `config/mcp_dedup.toml` still compares declarations with this data.

## Out of Scope
- N/A: this document covers only its target file.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|---|---|---|---|---|---|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | — | 2026-11-21 | Gate lifted by owner decision 2026-11-21: issues/20261120-115845_mcpdl006_two-layer-failure-verification.md phase all - the reconciliation field values and the replay boundary are defined by that issue; Phase 4; release unit: contract-and-producers Implemented: sets marked reference data; RETRYABLE_TOOLS/ALL_SIDE_EFFECTING_TOOLS ownership wording removed. |
| 2 | Add or update tests per Validation plan | Completed | — | 2026-11-21 | Gate lifted by owner decision 2026-11-21: issues/20261120-115845_mcpdl006_two-layer-failure-verification.md phase all - the reconciliation field values and the replay boundary are defined by that issue test_tool_constants.py: TestRetryClassDriftConsistency framing; 11 passed. |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | — | 20261121-203300 | Gate lifted by owner decision 2026-11-21: issues/20261120-115845_mcpdl006_two-layer-failure-verification.md phase all - the reconciliation field values and the replay boundary are defined by that issue Targeted gates green 2026-11-21; full suite at unit end. unit-end validation: full suite 13314 passed / 7 skipped; ruff format+check clean; mypy 590 files clean; lint-imports 6 kept; diff-cover 97% (fail-under 90) |
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
- **Related target files**: `scripts/shared/tool_constants.py`, `tests/shared/test_tool_constants.py`