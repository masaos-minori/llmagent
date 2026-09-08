# Implementation Procedure: Verify missing methods in ingester.py

## Traceability
- **Source issue**: issues/done/20260907-140130_regress001_widespread_test_suite_drift.md
- **Source plan**: plans/20260907-162014_plan.md
- **Related target files**: scripts/rag/ingestion/ingester.py

## Goal
Verify that `_get_or_create_document` and `_get_embedding` are absent from `scripts/rag/ingestion/ingester.py`.

## Priority
Medium

## Scope
- **In-Scope**: Verify two method names are absent from ingester.py
- **Out-of-Scope**: Any other ingester.py behavior change

## Background
Cluster 8 (RagIngester methods) identified in the original test drift analysis. The plan states that these methods were intentionally removed. This step verifies the claim against current source.

## Problem
Need to confirm whether both methods have been removed from ingester.py.

## Reason for change
This is a read-only verification step — no code changes are intended. The purpose is to determine whether Cluster 8 represents a stale test or an implementation regression.

## Implementation Steps

### Step 1: Search for both methods
Run: `rg "_get_or_create_document\|_get_embedding" scripts/rag/ingestion/ingester.py`
Expected outcome: Not found — neither method should exist in the current source.

### Step 2: Verify removal via git history (optional)
If the methods are not found, verify they were intentionally removed by checking git history:
Run: `git log --all --oneline -- scripts/rag/ingestion/ingester.py | head -20`
Look for commits mentioning removal of these methods.

### Step 3: Classify the cluster
If both methods are absent → classify as **stale test** (test references removed methods).
If either method is present → classify as **implementation regression** (methods were unexpectedly retained).

## Acceptance criteria
- [ ] Both method searches return no results
- [ ] Cluster 8 classified as stale test or implementation regression

## Tests
N/A: This is a read-only verification step. No code changes are made.

## Documentation Impact
N/A: This is a read-only verification step.

## Dependencies
- REQ-002: For each valid cluster, determine authoritative behavior (implementation vs. test)

## Assumptions
- Both methods were intentionally removed from ingester.py based on the plan's Evidence column stating "Not found in ingester.py".

## Unknowns
| ID | Unknown Description | Evidence Missing | Resolution Path | Blocking? (True/False) |
|---|---|---|---|---|
| UNK-01 | Whether the methods were intentionally removed or accidentally retained | Need to search ingester.py | Search for both method names | False |

## Affected areas
`skills/DESIGN.md` Change-impact table — medium blast radius (callers affected), read-only verification.

## Design
This is a Path A task (single file, read-only verification). The approach is simple: grep for both method names and confirm their absence.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Search for both methods | Completed | — | — | Not found in ingester.py; methods moved to other files during reorganization |
| 2 | Verify removal via git history | Completed | — | — | Both methods removed in f7f7616f (reorganization) and confirmed absent in 747aed92 |
| 3 | Classify cluster 8 | Completed | — | — | Cluster 8 = stale test (methods relocated, not deleted) |

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
- **Related target files**: scripts/rag/ingestion/ingester.py

(End of file - total 100 lines)
