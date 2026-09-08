# Implementation Procedure: Verify _ModuleConfig removal in pipeline.py

## Traceability
- **Source issue**: issues/done/20260907-140130_regress001_widespread_test_suite_drift.md
- **Source plan**: plans/20260907-162014_plan.md
- **Related target files**: scripts/rag/pipeline.py

## Goal
Verify that `_ModuleConfig` symbol was removed by refactor in `scripts/rag/pipeline.py`.

## Priority
Medium

## Scope
- **In-Scope**: Verify _ModuleConfig class/symbol is absent from pipeline.py
- **Out-of-Scope**: Any other pipeline.py behavior change

## Background
Cluster 10 (_ModuleConfig) identified in the original test drift analysis. The plan states that only a comment remains; the symbol was removed by refactor. This step verifies the claim against current source.

## Problem
Need to confirm whether _ModuleConfig has been removed from pipeline.py.

## Reason for change
This is a read-only verification step — no code changes are intended. The purpose is to determine whether Cluster 10 represents a stale test or an implementation regression.

## Implementation Steps

### Step 1: Search for _ModuleConfig
Run: `rg "_ModuleConfig" scripts/rag/pipeline.py`
Expected outcome: Only comments remain — no class definition or import.

### Step 2: Verify no _ModuleConfig.get patch target
Check whether any test patches `_ModuleConfig.get`:
Run: `rg "_ModuleConfig\.get" tests/rag/test_rag_pipeline_no_cache_freshness.py`
Expected outcome: Patch targets deleted symbol — confirms stale test.

### Step 3: Classify the cluster
If _ModuleConfig is absent from pipeline.py but patched in tests → classify as **stale test** (test patches removed symbol).
If _ModuleConfig still exists in pipeline.py → classify as **implementation regression** (symbol was unexpectedly retained).

## Acceptance criteria
- [ ] _ModuleConfig search returns only comments
- [ ] Test patch target confirmed as deleted symbol
- [ ] Cluster 10 classified as stale test or implementation regression

## Tests
N/A: This is a read-only verification step. No code changes are made.

## Documentation Impact
N/A: This is a read-only verification step.

## Dependencies
- REQ-001: Confirm which clusters remain valid
- REQ-002: For each valid cluster, determine authoritative behavior

## Assumptions
- _ModuleConfig was removed from pipeline.py based on the plan's Evidence column stating "_ModuleConfig removed — only comment remains".

## Unknowns
| ID | Unknown Description | Evidence Missing | Resolution Path | Blocking? (True/False) |
|---|---|---|---|---|
| UNK-01 | Whether _ModuleConfig is truly absent from pipeline.py | Need to search pipeline.py | Search for _ModuleConfig | False |

## Affected areas
`skills/DESIGN.md` Change-impact table — low blast radius, read-only verification.

## Design
This is a Path A task (single file, read-only verification). The approach is simple: grep for _ModuleConfig and confirm its absence, then check whether tests still patch it.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Search for _ModuleConfig | Pending | — | — | |
| 2 | Verify test patch target | Pending | — | — | |
| 3 | Classify cluster 10 | Pending | — | — | |

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
- **Related target files**: scripts/rag/pipeline.py

(End of file - total 100 lines)
