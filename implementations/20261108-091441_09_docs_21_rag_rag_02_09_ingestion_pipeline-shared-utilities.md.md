# Implementation procedure: `docs/21_rag/rag_02_09_ingestion_pipeline-shared-utilities.md` — `floats_to_blob` exception contract

## Goal
Update the `floats_to_blob()` contract line so the documented exception set matches the corrected behavior: out-of-range elements raise `ValueError`; the residual packing failure still logs and re-raises `struct.error` (`REQ-002` doc propagation).

## Scope
**Release unit**: ragvec001-full

- One contract-line edit in the "Vectors" list.

## Assumptions
- Gated: `issues/20261107-050701_adrrag001_rag-fallback-failure-policy.md` phase all - prose dependency on an open issue; the Plan's own Scope records "Related, no order required".
- The doc edit is written after Plan Phase 1 lands (the doc must describe implemented behavior).

## Design decisions
- Update the existing bullet in place; keep the exception contract at policy level (no code, no constant value).

## Alternatives considered
- N/A: docs-only single-line change.

## Implementation
### Target file
`docs/21_rag/rag_02_09_ingestion_pipeline-shared-utilities.md`

### Procedure
- In the `floats_to_blob()` bullet (currently: "`ValueError` for an empty list or non-numeric or non-finite elements; a packing failure is logged and the `struct.error` is re-raised"), state that elements outside the float32 range also raise `ValueError`, and narrow the `struct.error` clause to residual packing failures.

### Method
- Rewrite the bullet's exception clause only; the packing-purpose framing in the same bullet stays.

### Details
- Current bullet (verified at HEAD `eb19564fe`): the `struct.error` clause implies out-of-range values surface as `struct.error`, which the code never did and post-fix will not (sibling document `20261108-091441_02_scripts_rag_utils.py.md` raises `ValueError` before packing).

## Compatibility considerations
- N/A: docs-only.

## Security considerations
- N/A: docs-only.

## Rollback considerations
- N/A: revert the commit.

## Validation plan
| Target | Strategy | Command | Expected |
|---|---|---|---|
| edited doc | structure/quality gates | `uv run python tools/check_docs_quality.py`, `uv run python tools/check_docs_structure.py docs/21_rag/rag_02_09_ingestion_pipeline-shared-utilities.md`, `uv run python tools/check_docs_content_policy.py`, `uv run python tools/check_docs_consistency.py --domain rag` | No findings |

## Completion criteria
- The `floats_to_blob()` bullet's exception contract matches the implemented `ValueError`-for-out-of-range behavior (`Acceptance Criteria REQ-002`); doc checkers report no findings.

## Out of Scope
- The ingestion pack step `scripts/rag/ingestion/embedding.py` itself (Plan Out-of-Scope, `UNK-01`) — the doc line describes the utility contract, not new ingestion behavior.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Apply the contract-line edit described in Implementation > Procedure/Method/Details | Pending | — | — | Gated: issues/20261107-050701_adrrag001_rag-fallback-failure-policy.md phase all - prose dependency; Plan Scope records "Related, no order required" |
| 2 | Run the docs checkers named in the Validation plan | Pending | — | — | Gated: issues/20261107-050701_adrrag001_rag-fallback-failure-policy.md phase all - prose dependency; Plan Scope records "Related, no order required" |

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
- **Requirement ID**: `REQ-002` (`floats_to_blob` typed out-of-range rejection; docstring/doc accuracy)
- **Source issue**: `issues/20261107-203511_ragvec001_rag-embedding-float32-overflow.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261108-075301_ragvec001_rag-embedding-float32-overflow.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261108-091441
- **Related target files**: `docs/21_rag/rag_02_09_ingestion_pipeline-shared-utilities.md`
