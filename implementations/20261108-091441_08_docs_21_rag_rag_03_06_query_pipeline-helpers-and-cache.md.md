# Implementation procedure: `docs/21_rag/rag_03_06_query_pipeline-helpers-and-cache.md` — `get_embedding` magnitude contract

## Goal
State the `get_embedding` response contract in the helpers doc: elements must be finite and within the float32 range or the response is rejected with `ValueError` (`REQ-001` doc propagation).

## Scope
**Release unit**: ragvec001-full

- One contract sentence added to the `RagLLM`/`get_embedding` section (7.3).

## Assumptions
- Gated: `issues/20261107-050701_adrrag001_rag-fallback-failure-policy.md` phase all - prose dependency on an open issue; the Plan's own Scope records "Related, no order required".
- The doc edit is written after Plan Phase 2 lands (the note must describe implemented behavior).

## Design decisions
- Extend the existing section 7.3 prose; state the policy and its consequence, not the constant value or code (DESIGN Docs content policy — no implementation-detail duplication).

## Alternatives considered
- N/A: docs-only single-sentence change.

## Implementation
### Target file
`docs/21_rag/rag_03_06_query_pipeline-helpers-and-cache.md`

### Procedure
- In section 7.3 (`RagLLM (scripts/rag/llm_client.py)`), after the sentence describing the module-provided `get_embedding`, add the response contract: every element must be numeric, finite, and within the float32 magnitude range, otherwise `get_embedding` raises `ValueError` naming the offending index and the search stage counts the query as `embed_failed` (degraded).

### Method
- One or two sentences appended to the existing 7.3 paragraphs; existing timeout-contract prose stays untouched.

### Details
- Current 7.3 (verified at HEAD `eb19564fe`) describes `get_embedding` timeout forwarding but no magnitude contract; sibling document `20261108-091441_01_scripts_rag_llm_client.py.md` implements the check.

## Compatibility considerations
- N/A: docs-only.

## Security considerations
- N/A: docs-only.

## Rollback considerations
- N/A: revert the commit.

## Validation plan
| Target | Strategy | Command | Expected |
|---|---|---|---|
| edited doc | structure/quality gates | `uv run python tools/check_docs_quality.py`, `uv run python tools/check_docs_structure.py docs/21_rag/rag_03_06_query_pipeline-helpers-and-cache.md`, `uv run python tools/check_docs_content_policy.py`, `uv run python tools/check_docs_consistency.py --domain rag` | No findings |

## Completion criteria
- Section 7.3 states the finite/float32-range rejection contract accurately against the implemented code (`Acceptance Criteria REQ-001`); doc checkers report no findings.

## Out of Scope
- Other sections of the doc (cache, fusion, pipeline types).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Apply the contract sentence described in Implementation > Procedure/Method/Details | Pending | — | — | Gated: issues/20261107-050701_adrrag001_rag-fallback-failure-policy.md phase all - prose dependency; Plan Scope records "Related, no order required" |
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
- **Requirement ID**: `REQ-001` (`get_embedding` finite/float32-range response rejection)
- **Source issue**: `issues/20261107-203511_ragvec001_rag-embedding-float32-overflow.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261108-075301_ragvec001_rag-embedding-float32-overflow.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261108-091441
- **Related target files**: `docs/21_rag/rag_03_06_query_pipeline-helpers-and-cache.md`
