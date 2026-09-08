# Implementation Procedure: Verify missing functions in startup.py

## Traceability
- **Source issue**: issues/done/20260907-140130_regress001_widespread_test_suite_drift.md
- **Source plan**: plans/20260907-162014_plan.md
- **Related target files**: scripts/agent/startup.py

## Goal
Verify that `find_all_pending_approvals` and `check_workflow_definition` are absent from `scripts/agent/startup.py`.

## Priority
Medium

## Scope
- **In-Scope**: Verify two function names are absent from startup.py
- **Out-of-Scope**: Any other startup.py behavior change

## Background
Cluster 7 (startup functions) identified in the original test drift analysis. The plan states that these two functions were intentionally removed. This step verifies the claim against current source.

## Problem
Need to confirm whether both functions have been removed from startup.py.

## Reason for change
This is a read-only verification step — no code changes are intended. The purpose is to determine whether Cluster 7 represents a stale test or an implementation regression.

## Implementation Steps

### Step 1: Search for both functions
Run: `rg "find_all_pending_approvals\|check_workflow_definition" scripts/agent/startup.py`
Expected outcome: Not found — neither function should exist in the current source.

### Step 2: Verify removal via git history (optional)
If the functions are not found, verify they were intentionally removed by checking git history:
Run: `git log --all --oneline -- scripts/agent/startup.py | head -20`
Look for commits mentioning removal of these functions.

### Step 3: Classify the cluster
If both functions are absent → classify as **stale test** (test references removed functions).
If either function is present → classify as **implementation regression** (functions were unexpectedly re-added).

## Acceptance criteria
- [ ] Both function searches return no results
- [ ] Cluster 7 classified as stale test or implementation regression

## Tests
N/A: This is a read-only verification step. No code changes are made.

## Documentation Impact
N/A: This is a read-only verification step.

## Dependencies
- REQ-002: For each valid cluster, determine authoritative behavior (implementation vs. test)

## Assumptions
- Both functions were intentionally removed from startup.py based on the plan's Evidence column stating "Not found in startup.py".

## Unknowns
| ID | Unknown Description | Evidence Missing | Resolution Path | Blocking? (True/False) |
|---|---|---|---|---|
| UNK-01 | Whether the functions were intentionally removed or accidentally retained | Need to search startup.py | Search for both function names | False |

## Affected areas
`skills/DESIGN.md` Change-impact table — medium blast radius (callers affected), read-only verification.

## Design
This is a Path A task (single file, read-only verification). The approach is simple: grep for both function names and confirm their absence.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Search for both functions | Pending | — | — | |
| 2 | Verify removal via git history | Pending | — | — | Optional |
| 3 | Classify cluster 7 | Pending | — | — | |

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
- **Related target files**: scripts/agent/startup.py

(End of file - total 100 lines)
