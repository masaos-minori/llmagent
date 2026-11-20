## Goal

- Raise the recorded size baseline for `tools/_adr_authority_core.py` once the three new validators make the file exceed it.

## Scope
**Release unit**: N/A: not part of a release unit

- Baseline raise for the core growth from REQ-001/REQ-004/REQ-006 (the Plan's Requirement Traceability links this row to REQ-028's CI module-size gate).

## Assumptions
- Verified current state: the file is 25689 bytes and the baseline file carries the row `_adr_authority_core.py	25689` (tab-separated, verified in Step 2); the baseline file has 13 rows.
- The new value is measured from the actual post-implementation file size in the same commit as the core change (core row's document), never guessed in advance.

## Design decisions
- Raise only the core's row; no other baseline row is touched (the generator/checker rows' growth is not projected to exceed their baselines — if any does at implementation time, the CI failure names the row and its raise belongs to that row's own document scope check).

## Alternatives considered
- Refactoring the core to stay under the baseline — rejected by the Plan: the row exists precisely to record the legitimate growth (issue constraint: no unrelated cleanup).

## Implementation
### Target file
`tools/check_module_size_tools_baseline.txt`
### Procedure
- After the core row's validators land, measure the new byte size of `tools/_adr_authority_core.py` and update only this file's `_adr_authority_core.py` row to the measured value, in the same commit (REQ-001/REQ-004/REQ-006 validation gate).
### Method
- Single-row edit preserving the tab-separated `name<TAB>bytes` format and the file's row ordering.
### Details
- Measure with the same command the CI step uses (`tools/check_module_size.sh` reads this file); record the measured value, not a padded ceiling.

## Compatibility considerations
- The raise must be in the same commit as the growth: a pre-emptive raise with no growth, or growth with a stale baseline, fails the CI module-size step.

## Security considerations
- N/A: baseline record.

## Rollback considerations
- N/A: revert the commit (the baseline reverts with the core change).

## Validation plan
- `tools/check_module_size.sh` CI step (invoked locally the same way CI does) — exit 0 with the new value.

## Completion criteria
- The row equals the post-change file size and the module-size check passes (AC-7 precondition for Phase 1's tool suite).

## Out of Scope
- The core implementation (its own row) and every other baseline row.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Measure the grown core file and update its baseline row in the same commit | Pending | — | — | |
| 2 | Run the module-size check | Pending | — | — | |

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
- **Requirement ID**: REQ-001/REQ-004/REQ-006 (growth this baseline records), REQ-028 (CI module-size gate)
- **Source issue**: issues/20261117-123015_adrchk015_adr-graph-semantics.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261120-075008_adrchk015_adr-graph-semantics.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261120-092705
- **Related target files**: `tools/check_module_size_tools_baseline.txt`
