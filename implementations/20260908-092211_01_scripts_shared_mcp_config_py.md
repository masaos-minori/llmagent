# Implementation Procedure: Verify auth_token validation in mcp_config.py

## Traceability
- **Source issue**: issues/done/20260907-140130_regress001_widespread_test_suite_drift.md
- **Source plan**: plans/20260907-162014_plan.md
- **Related target files**: scripts/shared/mcp_config.py

## Goal
Verify that ValueError for empty auth_token is still enforced in `scripts/shared/mcp_config.py`.

## Priority
Medium

## Scope
- **In-Scope**: Verify auth_token validation exists in current source
- **Out-of-Scope**: Any other mcp_config.py behavior change

## Background
Cluster 5 (auth_token) identified in the original test drift analysis. The plan states that auth_token validation should still be enforced. This step verifies the claim against current source.

## Problem
Need to confirm whether the auth_token validation logic in mcp_config.py is still present and correct.

## Reason for change
This is a read-only verification step — no code changes are intended. The purpose is to determine whether Cluster 5 represents a stale test or an implementation regression.

## Implementation Steps

### Step 1: Search for auth_token validation
Run: `rg "auth_token.*must not be empty" scripts/shared/mcp_config.py`
Expected outcome: Found — the validation string should exist in the current source.

### Step 2: Verify the validation is in __init__ or property setter
Read the relevant section of mcp_config.py around the auth_token field.
Expected outcome: The ValueError is raised when auth_token is empty or None.

### Step 3: Classify the cluster
If the validation exists → classify as **stale test** (test expects validation but may reference wrong parameter name).
If the validation does NOT exist → classify as **implementation regression** (validation was removed).

## Acceptance criteria
- [ ] auth_token validation search returns results
- [ ] Validation location confirmed (line number recorded)
- [ ] Cluster 5 classified as stale test or implementation regression

## Tests
N/A: This is a read-only verification step. No code changes are made.

## Documentation Impact
N/A: This is a read-only verification step.

## Dependencies
- REQ-002: For each valid cluster, determine authoritative behavior (implementation vs. test)

## Assumptions
- The auth_token validation exists in mcp_config.py based on the plan's Evidence column stating "Validation exists in current source".

## Unknowns
| ID | Unknown Description | Evidence Missing | Resolution Path | Blocking? (True/False) |
|---|---|---|---|---|
| UNK-01 | Whether auth_token validation is in __init__ or a property setter | Need to read mcp_config.py | Read the file and locate the validation | False |

## Affected areas
`skills/DESIGN.md` Change-impact table — low blast radius, read-only verification.

## Design
This is a Path A task (single file, read-only verification). The approach is simple: grep for the expected validation pattern, confirm its presence, and classify the cluster.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Search for auth_token validation | Pending | — | — | |
| 2 | Verify validation location | Pending | — | — | |
| 3 | Classify cluster 5 | Pending | — | — | |

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
- **Related target files**: scripts/shared/mcp_config.py

(End of file - total 100 lines)
