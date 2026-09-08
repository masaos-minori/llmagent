# Implementation Procedure: Verify attribute names in orchestrator.py

## Traceability
- **Source issue**: issues/done/20260907-140130_regress001_widespread_test_suite_drift.md
- **Source plan**: plans/20260907-162014_plan.md
- **Related target files**: scripts/agent/orchestrator.py

## Goal
Verify that `_llm_executor` and `_llm_turn_executor` do not exist in `scripts/agent/orchestrator.py`.

## Priority
High

## Scope
- **In-Scope**: Verify two attribute names are absent from orchestrator.py
- **Out-of-Scope**: Any other orchestrator.py behavior change

## Background
Cluster 1 (_llm_turn_executor) and Cluster 2 (_llm_executor) identified in the original test drift analysis. The plan states that neither attribute name is found in orchestrator.py. This step verifies the claim against current source.

## Problem
Need to confirm whether both attributes have been removed from orchestrator.py.

## Reason for change
This is a read-only verification step — no code changes are intended. The purpose is to determine whether Clusters 1 and 2 represent stale tests or implementation regressions.

## Implementation Steps

### Step 1: Search for both attributes
Run: `rg "_llm_executor\|_llm_turn_executor" scripts/agent/orchestrator.py`
Expected outcome: Not found — neither attribute should exist in the current source.

### Step 2: Check integration tests for stale references
Run: `rg "_llm_executor\|_llm_turn_executor" tests/integration/test_orchestrator_integration.py`
Expected outcome: Integration tests also reference removed attributes — confirms stale tests.

### Step 3: Classify the clusters
If both attributes are absent → classify as **stale test** (tests reference removed attributes).
If either attribute is present → classify as **implementation regression** (attributes were unexpectedly retained).

## Acceptance criteria
- [ ] Both attribute searches return no results
- [ ] Integration test stale references confirmed
- [ ] Clusters 1 and 2 classified as stale test or implementation regression

## Tests
N/A: This is a read-only verification step. No code changes are made.

## Documentation Impact
N/A: This is a read-only verification step.

## Dependencies
- REQ-001: Confirm which clusters remain valid
- REQ-002: For each valid cluster, determine authoritative behavior

## Assumptions
- Both attributes were intentionally removed from orchestrator.py based on the plan's Evidence column stating "Neither attribute name found".

## Unknowns
| ID | Unknown Description | Evidence Missing | Resolution Path | Blocking? (True/False) |
|---|---|---|---|---|
| UNK-01 | Whether both attributes were intentionally removed or accidentally retained | Need to search orchestrator.py | Search for both attribute names | False |

## Affected areas
`skills/DESIGN.md` Change-impact table — high blast radius (many callers), read-only verification.

## Design
This is a Path A task (single file, read-only verification). The approach is simple: grep for both attribute names and confirm their absence, then check integration tests.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Search for both attributes | Pending | — | — | |
| 2 | Check integration tests | Pending | — | — | |
| 3 | Classify clusters 1 and 2 | Pending | — | — | |

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
- **Related target files**: scripts/agent/orchestrator.py

(End of file - total 100 lines)
