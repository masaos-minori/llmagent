# Implementation Procedure: Verify config patterns in config_builders.py

## Traceability
- **Source issue**: issues/done/20260907-140130_regress001_widespread_test_suite_drift.md
- **Source plan**: plans/20260907-162014_plan.md
- **Related target files**: scripts/agent/config_builders.py

## Goal
Verify that PRODUCTION/tool_definitions_strict/routing_drift_strict do not exist in `scripts/agent/config_builders.py`.

## Priority
Medium

## Scope
- **In-Scope**: Verify three config pattern names are absent from config_builders.py
- **Out-of-Scope**: Any other config_builders.py behavior change

## Background
Cluster 2 (PRODUCTION/tool_definitions_strict/routing_drift_strict) identified in the original test drift analysis. The plan states that these patterns are NOT found in current source. This step verifies the claim against current source.

## Problem
Need to confirm whether all three config patterns have been removed from config_builders.py.

## Reason for change
This is a read-only verification step — no code changes are intended. The purpose is to determine whether Cluster 2 represents a stale test or an implementation regression.

## Implementation Steps

### Step 1: Search for all three patterns
Run: `rg "PRODUCTION\|tool_definitions_strict\|routing_drift_strict" scripts/agent/config_builders.py`
Expected outcome: Not found — none of the three patterns should exist in the current source.

### Step 2: Verify removal via git history (optional)
If any pattern is not found, verify they were intentionally removed by checking git history:
Run: `git log --all --oneline -- scripts/agent/config_builders.py | head -20`
Look for commits mentioning removal of these patterns.

### Step 3: Classify the cluster
If all three patterns are absent → classify as **stale test** (test references removed patterns).
If any pattern is present → classify as **implementation regression** (pattern was unexpectedly retained).

## Acceptance criteria
- [ ] All three pattern searches return no results
- [ ] Cluster 2 classified as stale test or implementation regression

## Tests
N/A: This is a read-only verification step. No code changes are made.

## Documentation Impact
N/A: This is a read-only verification step.

## Dependencies
- REQ-001: Confirm which clusters remain valid
- REQ-002: For each valid cluster, determine authoritative behavior

## Assumptions
- All three patterns were intentionally removed from config_builders.py based on the plan's Evidence column stating "Patterns NOT found in current source".

## Unknowns
| ID | Unknown Description | Evidence Missing | Resolution Path | Blocking? (True/False) |
|---|---|---|---|---|
| UNK-01 | Whether all three patterns were intentionally removed or accidentally retained | Need to search config_builders.py | Search for all three pattern names | False |

## Affected areas
`skills/DESIGN.md` Change-impact table — medium blast radius, read-only verification.

## Design
This is a Path A task (single file, read-only verification). The approach is simple: grep for all three patterns and confirm their absence.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Search for all three patterns | Pending | — | — | |
| 2 | Verify removal via git history | Pending | — | — | Optional |
| 3 | Classify cluster 2 | Pending | — | — | |

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
- **Source issue**: issues/done/20260907-140130_regress001_widespread_test_suite_drift.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260907-162014_plan.md
- **Source implementation procedure**: N/A: not applicable in this phase
- **Generated at**: 20260908-092211
- **Related target files**: scripts/agent/config_builders.py

(End of file - total 100 lines)
