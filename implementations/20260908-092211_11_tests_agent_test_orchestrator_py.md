# Implementation Procedure: Verify stale attribute references in test_orchestrator.py

## Traceability
- **Source issue**: issues/done/20260907-140130_regress001_widespread_test_suite_drift.md
- **Source plan**: plans/20260907-162014_plan.md
- **Related target files**: tests/agent/test_orchestrator.py

## Goal
Verify that tests reference removed attributes in `tests/agent/test_orchestrator.py`.

## Priority
High

## Scope
- **In-Scope**: Verify stale attribute references in orchestrator test
- **Out-of-Scope**: Any other test_orchestrator.py behavior change

## Background
Tests in test_orchestrator.py reference removed attributes (_llm_executor/_llm_turn_executor). This step verifies the claim against current source.

## Problem
Need to confirm whether tests still reference removed attributes.

## Reason for change
This is a read-only verification step — no code changes are intended. The purpose is to determine whether these are stale test references.

## Implementation Steps

### Step 1: Search for stale attribute references
Run: `rg "_llm_executor\|_llm_turn_executor" tests/agent/test_orchestrator.py`
Expected outcome: Found — tests reference removed attributes.

### Step 2: Identify specific test functions
Read the sections of test_orchestrator.py containing the stale references.
Expected outcome: Document which test functions reference removed attributes.

### Step 3: Classify the cluster
If tests reference removed attributes → classify as **stale test** (needs update).
If tests have been updated but still fail → investigate further for implementation regression.

## Acceptance criteria
- [ ] Stale attribute references found in test
- [ ] Specific test functions documented
- [ ] Cluster classification confirmed

## Tests
N/A: This is a read-only verification step. No code changes are made.

## Documentation Impact
N/A: This is a read-only verification step.

## Dependencies
- REQ-002: For each valid cluster, determine authoritative behavior

## Assumptions
- Tests reference removed attributes based on the plan's Evidence column stating "Attribute names not in orchestrator.py".

## Unknowns
| ID | Unknown Description | Evidence Missing | Resolution Path | Blocking? (True/False) |
|---|---|---|---|---|
| UNK-01 | Which specific test functions reference removed attributes | Need to read test_orchestrator.py | Read relevant sections | False |

## Affected areas
`skills/DESIGN.md` Change-impact table — high blast radius (many callers), read-only verification.

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
- **Related target files**: tests/agent/test_orchestrator.py

(End of file - total 100 lines)
