# Implementation Procedure: Verify _ModuleConfig patch references in test_rag_pipeline_no_cache_freshness.py

## Traceability
- **Source issue**: issues/done/20260907-140130_regress001_widespread_test_suite_drift.md
- **Source plan**: plans/20260907-162014_plan.md
- **Related target files**: tests/rag/test_rag_pipeline_no_cache_freshness.py

## Goal
Verify that tests patch `_ModuleConfig.get` in `tests/rag/test_rag_pipeline_no_cache_freshness.py`.

## Priority
Medium

## Scope
- **In-Scope**: Verify _ModuleConfig.get patch references in RAG pipeline test
- **Out-of-Scope**: Any other test_rag_pipeline_no_cache_freshness.py behavior change

## Background
The plan states that tests still patch _ModuleConfig.get. This step verifies the claim against current source.

## Problem
Need to confirm whether tests still reference _ModuleConfig.get.

## Reason for change
This is a read-only verification step — no code changes are intended. The purpose is to determine whether these are stale test patches.

## Implementation Steps

### Step 1: Search for _ModuleConfig.get patch
Run: `rg "_ModuleConfig\.get" tests/rag/test_rag_pipeline_no_cache_freshness.py`
Expected outcome: Found — tests patch _ModuleConfig.get.

### Step 2: Cross-reference with pipeline.py
Verify that _ModuleConfig has been removed from pipeline.py:
Run: `rg "_ModuleConfig" scripts/rag/pipeline.py`
Expected outcome: Only comments remain — confirms test patches deleted symbol.

### Step 3: Classify the cluster
If tests patch _ModuleConfig.get but it was removed from pipeline.py → classify as **stale test** (test patches removed symbol).
If _ModuleConfig still exists in pipeline.py → classify as **implementation regression**.

## Acceptance criteria
- [ ] _ModuleConfig.get patch found in test
- [ ] Cross-reference with pipeline.py validated
- [ ] Cluster classification confirmed

## Tests
N/A: This is a read-only verification step. No code changes are made.

## Documentation Impact
N/A: This is a read-only verification step.

## Dependencies
- REQ-001: Confirm which clusters remain valid
- REQ-002: For each valid cluster, determine authoritative behavior

## Assumptions
- Tests patch _ModuleConfig.get based on the plan's Evidence column stating "Patches still reference _ModuleConfig.get".

## Unknowns
| ID | Unknown Description | Evidence Missing | Resolution Path | Blocking? (True/False) |
|---|---|---|---|---|
| UNK-01 | Whether _ModuleConfig.get is truly absent from pipeline.py | Need to cross-reference both files | Read both files | False |

## Affected areas
`skills/DESIGN.md` Change-impact table — low blast radius, read-only verification.

## Design
This is a Path A task (single file, read-only verification). The approach is simple: find _ModuleConfig.get patches and cross-reference with pipeline.py.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Search for _ModuleConfig.get patch | Completed | — | — | Found 3 occurrences (lines 90, 112, 137); all patch deleted symbol |
| 2 | Cross-reference with pipeline.py | Completed | — | — | pipeline.py has only comment referencing _ModuleConfig (line 79); symbol removed |
| 3 | Classify cluster | Completed | — | — | Cluster 10 = stale test (test patches removed symbol) |

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
- **Related target files**: tests/rag/test_rag_pipeline_no_cache_freshness.py

(End of file - total 100 lines)
