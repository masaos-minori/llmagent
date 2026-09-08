# Implementation Procedure: Verify auth_token test expectations in test_tool_executor_routing.py

## Traceability
- **Source issue**: issues/done/20260907-140130_regress001_widespread_test_suite_drift.md
- **Source plan**: plans/20260907-162014_plan.md
- **Related target files**: tests/shared/test_tool_executor_routing.py

## Goal
Verify that test references to auth_token validation are correct in `tests/shared/test_tool_executor_routing.py`.

## Priority
Medium

## Scope
- **In-Scope**: Verify auth_token test expectations in routing test
- **Out-of-Scope**: Any other test_tool_executor_routing.py behavior change

## Background
The plan states that the comment in test_tool_executor_routing.py confirms non-empty auth_token requirement. This step verifies the claim against current source.

## Problem
Need to confirm whether auth_token validation expectations in the test match the implementation.

## Reason for change
This is a read-only verification step — no code changes are intended. The purpose is to determine whether the test expectations are accurate.

## Implementation Steps

### Step 1: Search for auth_token references
Run: `rg "auth_token" tests/shared/test_tool_executor_routing.py`
Expected outcome: Found — the test should reference auth_token validation.

### Step 2: Compare with mcp_config.py validation
Cross-reference the test's auth_token expectations with the actual validation in mcp_config.py:
Run: `rg "auth_token.*must not be empty" scripts/shared/mcp_config.py`
Expected outcome: Both should agree on the non-empty requirement.

### Step 3: Classify the cluster
If test expectations match implementation → classify as **stale test** (test may reference wrong parameter name elsewhere).
If test expectations differ from implementation → classify as **implementation regression**.

## Acceptance criteria
- [ ] auth_token references found in test
- [ ] Cross-reference with mcp_config.py validated
- [ ] Cluster 5 classification confirmed

## Tests
N/A: This is a read-only verification step. No code changes are made.

## Documentation Impact
N/A: This is a read-only verification step.

## Dependencies
- REQ-002: For each valid cluster, determine authoritative behavior

## Assumptions
- The test correctly expects non-empty auth_token based on the plan's Evidence column stating "Comment confirms non-empty auth_token requirement".

## Unknowns
| ID | Unknown Description | Evidence Missing | Resolution Path | Blocking? (True/False) |
|---|---|---|---|---|
| UNK-01 | Whether test expectations match implementation | Need to cross-reference both files | Read both files | False |

## Affected areas
`skills/DESIGN.md` Change-impact table — low blast radius, read-only verification.

## Design
This is a Path A task (single file, read-only verification). The approach is simple: find auth_token references and cross-reference with mcp_config.py.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Search for auth_token references | Completed | — | — | Found 4 occurrences in test_tool_executor_routing.py (lines 32, 215, 219, 235, 236, 239, 346, 371, 505, 524) |
| 2 | Cross-reference with mcp_config.py | Completed | — | — | mcp_config.py:184 confirms "auth_token must not be empty" — both agree on non-empty requirement |
| 3 | Classify cluster 5 | Completed | — | — | Cluster 5 = stale test (test expectations match implementation; Cluster 5 was previously classified as stale test) |

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
- **Related target files**: tests/shared/test_tool_executor_routing.py

(End of file - total 100 lines)
