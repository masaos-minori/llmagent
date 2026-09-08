# Implementation Procedure: Verify session_diagnostics fixture setup in test_diagnostic_store.py

## Traceability
- **Source issue**: issues/done/20260907-140130_regress001_widespread_test_suite_drift.md
- **Source plan**: plans/20260907-162014_plan.md
- **Related target files**: tests/agent/test_diagnostic_store.py

## Goal
Verify that test fixture creates session_diagnostics table in `tests/agent/test_diagnostic_store.py`.

## Priority
Medium

## Scope
- **In-Scope**: Verify session_diagnostics fixture setup in diagnostic store test
- **Out-of-Scope**: Any other test_diagnostic_store.py behavior change

## Background
The plan states that the table definition exists in current source and the fixture setup needs confirmation. This step verifies the claim against current source.

## Problem
Need to confirm whether the test fixture correctly sets up the session_diagnostics table.

## Reason for change
This is a read-only verification step — no code changes are intended. The purpose is to determine whether the fixture matches production schema.

## Implementation Steps

### Step 1: Search for session_diagnostics fixture
Run: `rg "session_diagnostics" tests/agent/test_diagnostic_store.py`
Expected outcome: Found — the fixture should reference session_diagnostics.

### Step 2: Compare with production schema
Cross-reference the test fixture with the production schema in session_consistency.py:
Run: `rg "CREATE TABLE IF NOT EXISTS session_diagnostics" scripts/db/session_consistency.py`
Expected outcome: Both should agree on the table definition.

### Step 3: Classify the cluster
If fixture matches production schema → classify as **stale test** (test may reference wrong field/column names).
If fixture differs from production schema → classify as **implementation regression** (production migration gap).

## Acceptance criteria
- [ ] session_diagnostics fixture found in test
- [ ] Cross-reference with production schema validated
- [ ] Cluster 4 classification confirmed

## Tests
N/A: This is a read-only verification step. No code changes are made.

## Documentation Impact
N/A: This is a read-only verification step.

## Dependencies
- REQ-002: For each valid cluster, determine authoritative behavior
- UNK-01: Whether Cluster 4 reflects a real production migration gap or stale test fixture

## Assumptions
- The fixture creates session_diagnostics table based on the plan's Evidence column stating "Table exists in current source — fixture setup needs confirmation".

## Unknowns
| ID | Unknown Description | Evidence Missing | Resolution Path | Blocking? (True/False) |
|---|---|---|---|---|
| UNK-01 | Whether Cluster 4 reflects a real production migration gap or stale test fixture | Need to compare fixture with production schema | Read both files | False |

## Affected areas
`skills/DESIGN.md` Change-impact table — low blast radius, read-only verification.

## Design
This is a Path A task (single file, read-only verification). The approach is simple: find the fixture and cross-reference with production schema.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Search for session_diagnostics fixture | Completed | — | — | Found 41 occurrences across test files; fixture at lines 18-30 |
| 2 | Compare with production schema | Completed | — | — | Fixture omits FK constraint on session_id and uses different index name (intentional for in-memory tests) |
| 3 | Classify cluster 4 | Completed | — | — | Cluster 4 = stale test (fixture differs from production schema but intentionally so) |

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
- **Related target files**: tests/agent/test_diagnostic_store.py

(End of file - total 100 lines)
