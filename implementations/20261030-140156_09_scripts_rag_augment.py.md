# Implementation Procedure: `scripts/rag/augment.py` (RAGCORPUS001 Phase 3)

**Plan**: `plans/done/20261030-013620_ragcorpus001_rag-corpus-identity.md` (REQ-003)

## Goal
Pass the remote identity carried by the HTTP augment chain through to the gate without
changing existing call semantics.

## Scope
- `class AugmentRefiner` `:40`; `async def run_http_augment(...)` `:69`;
  `run_refiner` `:146`; `_forward_fetch_result` `:113`;
  `map_http_result_kind` `:186`.

## Assumptions
- Plan-level assumptions apply unchanged; see the Source plan Assumptions section.

## Design decisions
- `run_http_augment` `:69` keeps its existing parameters and return type; the remote
  identity rides inside the existing result objects it already forwards (doc 10's
  `HttpAugmentResult` field and doc 11's `CallRagResult` field) — this file adds no new
  parameter to any public signature (REQ-009 additive-only).
- Where `run_http_augment` assembles/forwards results (`:113` region), copy the identity
  field through verbatim; `None` (server predates identity) must survive the copy, not
  become an empty default.

## Alternatives considered
- No file-level alternatives beyond those evaluated in the Source plan; this procedure executes the selected option.

## Implementation
1. Follow the identity field through each result copy in the method bodies between `:69`
   and `:146`; keep the refiner path untouched.

## Compatibility considerations
**Dependencies**:
- Upstream: doc 10 (`HttpAugmentResult` identity field), doc 11 (`CallRagResult`
**Blocks**: docs 08, 16

## Security considerations
- No new security surface beyond what the Source plan records.

## Rollback considerations
- Revert this file together with its paired test rows in the same commit; the change is additive and gated by the plan's checkers.

## Validation plan
- `uv run pytest tests/rag/test_rag_http_mode.py` (doc 16).

## Completion criteria
- Identity present end-to-end on the HTTP path; `None` identity preserved; no signature
  changes.

## Out of Scope
- Everything outside the target file and the anchors recorded above; cross-plan boundaries and sequencing are recorded in the Source plan.

## Execution Status
### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Re-verify cited anchors before editing | Pending | — | — | |
| 2 | Apply the Implementation procedure | Pending | — | — | |
| 3 | Run the Validation plan gates | Pending | — | — | |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| — | — | — | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| `20261030-140156_10_scripts_rag_http_augment.py.md` | 1 (dependency) | Procedure | Pending | — | — |
| `20261030-140156_11_scripts_rag_pipeline_service.py.md` | 1 (dependency) | Procedure | Pending | — | — |

## Marker record
- No new named constructs (field plumbing through existing objects).

## Traceability
- **Workflow phase**: plan-to-implementation-procedure
- **Requirement ID**: REQ-003
- **Source issue**: `issues/20261029-104506_ragcorpus001_rag-corpus-identity.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/done/20261030-013620_ragcorpus001_rag-corpus-identity.md` — Implementation Target Files row 09
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261030-140156
- **Related target files**: `scripts/rag/augment.py`
