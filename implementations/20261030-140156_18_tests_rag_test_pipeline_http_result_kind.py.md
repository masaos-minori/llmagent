# Implementation Procedure: `tests/rag/test_pipeline_http_result_kind.py` (RAGCORPUS001 Phase 3)

**Plan**: `plans/done/20261030-013620_ragcorpus001_rag-corpus-identity.md` (REQ-004)

## Goal
Assert the recorded corpus generation on each result kind.

## Scope
- `_make_pipeline` `:18`; result-kind tests: `test_remote_nonempty` `:34`,
  `test_remote_empty` `:68`, `test_in_process_fallback` `:107`, `test_no_http_mode`
  `:159`, auth regression `test_auth_error_fails_closed_without_in_process_fallback`
  `:186` — extend the existing four with generation assertions; do not duplicate the
  auth test (doc 16 owns the gate-side auth matrix).

## Assumptions
- Plan-level assumptions apply unchanged; see the Source plan Assumptions section.

## Design decisions

## Alternatives considered
- No file-level alternatives beyond those evaluated in the Source plan; this procedure executes the selected option.

## Implementation
### Test cases to land
- Extend each existing result-kind test with a `corpus_generation` assertion:
  remote-served results record the remote corpus generation; fallback results record the
  local generation (doc 08 contract); `test_no_http_mode` records the local generation.
- `test_generation_none_when_unverified` (new): corrupt local meta + no HTTP mode →
  `corpus_generation is None` (identity-unverified state is observable in diagnostics).

1. Patch identity stubs into the shared `_make_pipeline` `:18` fixture (test-local knob,
   same pattern as doc 16).
2. Add assertions inside the existing tests (they stay single tests per kind — no
   duplication of the auth regression).

## Compatibility considerations
**Dependencies**: upstream: docs 08, 12 (generation recorded on results/diagnostics)
**Blocks**: none

## Security considerations
- Existing authentication/authorization boundaries are unchanged except where this procedure states otherwise; secret values must never appear in logs, audit records, or error messages (plan Risk).

## Rollback considerations
- Revert or remove the added test rows; no production change to unwind.

## Validation plan
- `uv run pytest tests/rag/test_pipeline_http_result_kind.py`

## Completion criteria
- Every accepted result kind carries the generation used; AC-2 verifiable from
  diagnostics alone.

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
| `20261030-140156_08_scripts_rag_pipeline.py.md` | 1 (dependency) | Procedure | Pending | — | — |

## Marker record
- `(new)` markers applied: `test_generation_none_when_unverified` (Test cases section);
  the four extensions are in-place edits, listed in Test cases section.

## Traceability
- **Workflow phase**: plan-to-implementation-procedure
- **Requirement ID**: REQ-004
- **Source issue**: `issues/20261029-104506_ragcorpus001_rag-corpus-identity.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/done/20261030-013620_ragcorpus001_rag-corpus-identity.md` — Implementation Target Files row 18
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261030-140156
- **Related target files**: `tests/rag/test_pipeline_http_result_kind.py`
