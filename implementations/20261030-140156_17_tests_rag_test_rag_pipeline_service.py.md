# Implementation Procedure: `tests/rag/test_rag_pipeline_service.py` (RAGCORPUS001 Phase 3)

**Plan**: `plans/done/20261030-013620_ragcorpus001_rag-corpus-identity.md` (REQ-002)

## Goal
Contract tests for the additive identity fields on `CallRagResult`.

## Scope
- `TestCallToolEndpoint` `:29`, `TestResponseParsing` `:108`,
  `TestFallbackReasonCallback` `:209`, `TestReturnedStatusCode` `:278` (file 501 lines).
- Response-parsing tests to mirror for the new field live in `TestResponseParsing`
  (`test_parses_result_field` `:111`).

## Assumptions
- Plan-level assumptions apply unchanged; see the Source plan Assumptions section.

## Design decisions

## Alternatives considered
- No file-level alternatives beyond those evaluated in the Source plan; this procedure executes the selected option.

## Implementation
### Test cases to land
- `TestCallRagResultIdentityFields` (new class):
  - `test_identity_parsed_from_response_envelope` (new): payload carrying the six wire
    fields → `CallRagResult.remote_identity` populated, field-by-field equality.
  - `test_identity_absent_is_none` (new): legacy payload → `remote_identity is None`,
    all other parsing unchanged.
  - `test_malformed_identity_is_none_not_partial` (new): wrong types → `None`.

1. Append the class after `TestResponseParsing` region; reuse its payload-builder
   patterns (`:111-168`).

## Compatibility considerations
**Dependencies**: upstream: doc 11 (`CallRagResult.remote_identity`)
**Blocks**: none

## Security considerations
- No new security surface beyond what the Source plan records.

## Rollback considerations
- Revert or remove the added test rows; no production change to unwind.

## Validation plan
- `uv run pytest tests/rag/test_rag_pipeline_service.py`

## Completion criteria
- Additive contract locked; existing 501-line suite green without edits to prior tests.

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
| `20261030-140156_11_scripts_rag_pipeline_service.py.md` | 1 (dependency) | Procedure | Pending | — | — |

## Marker record
- `(new)` markers applied: `TestCallRagResultIdentityFields`,
  `test_identity_parsed_from_response_envelope`, `test_identity_absent_is_none`,
  `test_malformed_identity_is_none_not_partial` (Test cases section).

## Traceability
- **Workflow phase**: plan-to-implementation-procedure
- **Requirement ID**: REQ-002
- **Source issue**: `issues/20261029-104506_ragcorpus001_rag-corpus-identity.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/done/20261030-013620_ragcorpus001_rag-corpus-identity.md` — Implementation Target Files row 17
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261030-140156
- **Related target files**: `tests/rag/test_rag_pipeline_service.py`
