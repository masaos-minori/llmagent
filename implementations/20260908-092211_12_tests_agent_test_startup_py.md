# Implementation Procedure: Verify stale function references in test_startup.py

## Traceability
- **Source issue**: issues/done/20260907-140130_regress001_widespread_test_suite_drift.md
- **Source plan**: plans/20260907-162014_plan.md
- **Related target files**: tests/agent/test_startup.py

## Goal
Verify that tests reference removed functions in `tests/agent/test_startup.py`.

## Priority
Medium

## Scope
- **In-Scope**: Verify stale function references in startup test
- **Out-of-Scope**: Any other test_startup.py behavior change

## Background
Tests in test_startup.py reference removed functions (find_all_pending_approvals/check_workflow_definition). This step verifies the claim against current source.

## Problem
Need to confirm whether tests still reference removed functions.

## Reason for change
This is a read-only verification step — no code changes are intended. The purpose is to determine whether these are stale test references.

## Implementation Steps

### Step 1: Search for stale function references
Run: `rg "find_all_pending_approvals\|check_workflow_definition" tests/agent/test_startup.py`
Expected outcome: Found — tests reference removed functions.

### Step 2: Identify specific test functions
Read the sections of test_startup.py containing the stale references.
Expected outcome: Document which test functions reference removed functions.

### Step 3: Classify the cluster
If tests reference removed functions → classify as **stale test** (needs update).
If tests have been updated but still fail → investigate further for implementation regression.

## Acceptance criteria
- [ ] Stale function references found in test
- [ ] Specific test functions documented
- [ ] Cluster classification confirmed

## Tests
N/A: This is a read-only verification step. No code changes are made.

## Documentation Impact
N/A: This is a read-only verification step.

## Dependencies
- REQ-002: For each valid cluster, determine authoritative behavior

## Assumptions
- Tests reference removed functions based on the plan's Evidence column stating "Functions not in startup.py".

## Unknowns
| ID | Unknown Description | Evidence Missing | Resolution Path | Blocking? (True/False) |
|---|---|---|---|---|
| UNK-01 | Which specific test functions reference removed functions | Need to read test_startup.py | Read relevant sections | False |

## Affected areas
`skills/DESIGN.md` Change-impact table — medium blast radius (callers affected), read-only verification.

## Design
This is a Path A task (single file, read-only verification). The approach is simple: grep for stale references and identify affected test functions.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Search for stale references | Pending | — | — | |
| 2 | Identify affected test functions | Pending | — | — | |
| 3 | Classify cluster | Pending | — | — | |

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
- **Related target files**: tests/agent/test_startup.py

(End of file - total 100 lines)
