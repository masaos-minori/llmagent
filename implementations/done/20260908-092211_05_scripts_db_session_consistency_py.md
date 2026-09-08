# Implementation Procedure: Verify session_diagnostics schema in session_consistency.py

## Traceability
- **Source issue**: issues/done/20260907-140130_regress001_widespread_test_suite_drift.md
- **Source plan**: plans/20260907-162014_plan.md
- **Related target files**: scripts/db/session_consistency.py

## Goal
Verify that `CREATE TABLE IF NOT EXISTS session_diagnostics` exists in `scripts/db/session_consistency.py`.

## Priority
Medium

## Scope
- **In-Scope**: Verify session_diagnostics table definition exists
- **Out-of-Scope**: Any other session_consistency.py behavior change

## Background
Cluster 4 (session_diagnostics) identified in the original test drift analysis. The plan states that the session_diagnostics table definition exists in current source. This step verifies the claim against current source.

## Problem
Need to confirm whether the session_diagnostics table definition exists in session_consistency.py.

## Reason for change
This is a read-only verification step — no code changes are intended. The purpose is to determine whether Cluster 4 represents a stale test or an implementation regression.

## Implementation Steps

### Step 1: Search for session_diagnostics table definition
Run: `rg "CREATE TABLE IF NOT EXISTS session_diagnostics" scripts/db/session_consistency.py`
Expected outcome: Found — the table definition should exist in the current source.

### Step 2: Read the table schema
Read the section of session_consistency.py containing the CREATE TABLE statement.
Expected outcome: Confirm the table schema matches what tests expect.

### Step 3: Compare with test fixture (UNK-01 resolution)
Read `tests/agent/test_diagnostic_store.py` to compare the test fixture setup with the production schema.
Expected outcome: Determine if the test fixture correctly mirrors the production schema.

### Step 4: Classify the cluster
If the table exists and matches test expectations → classify as **stale test** (test may reference wrong field/column names).
If the table does NOT exist or differs significantly → classify as **implementation regression** (production migration gap).

## Acceptance criteria
- [ ] session_diagnostics table definition found
- [ ] Test fixture compared with production schema
- [ ] Cluster 4 classified as stale test or implementation regression

## Tests
N/A: This is a read-only verification step. No code changes are made.

## Documentation Impact
N/A: This is a read-only verification step.

## Dependencies
- REQ-002: For each valid cluster, determine authoritative behavior (implementation vs. test)
- UNK-01: Whether Cluster 4 reflects a real production migration gap or stale test fixture

## Assumptions
- The session_diagnostics table definition exists in session_consistency.py based on the plan's Evidence column stating "Table definition exists in current source".

## Unknowns
| ID | Unknown Description | Evidence Missing | Resolution Path | Blocking? (True/False) |
|---|---|---|---|---|
| UNK-01 | Whether Cluster 4 reflects a real production migration gap or stale test fixture | Need to compare test fixture with production schema | Read test_diagnostic_store.py and compare | False |

## Affected areas
`skills/DESIGN.md` Change-impact table — low blast radius, read-only verification.

## Design
This is a Path A task (single file, read-only verification). The approach is simple: find the table definition and compare it with the test fixture.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Search for table definition | Pending | — | — | |
| 2 | Read table schema | Pending | — | — | |
| 3 | Compare with test fixture | Pending | — | — | |
| 4 | Classify cluster 4 | Pending | — | — | |

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
- **Related target files**: scripts/db/session_consistency.py

(End of file - total 100 lines)
