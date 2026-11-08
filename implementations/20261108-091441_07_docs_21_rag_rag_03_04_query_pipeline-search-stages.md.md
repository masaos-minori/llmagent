# Implementation procedure: `docs/21_rag/rag_03_04_query_pipeline-search-stages.md` — SearchStage error-handling note

## Goal
Extend the `SearchStage` error-handling note with the out-of-range embedding path: rejected at `get_embedding` → `embed_failed`; backstop counts packing failures; nothing propagates (`REQ-003`/`REQ-004` doc propagation).

## Scope
**Release unit**: ragvec001-full

- One note edit in the existing `SearchStage` error-handling blockquote.

## Assumptions
- Gated: `issues/20261107-050701_adrrag001_rag-fallback-failure-policy.md` phase all - prose dependency on an open issue; the Plan's own Scope records "Related, no order required".
- The doc edit is written after Plan Phases 1-3 land (the note must describe implemented behavior).

## Design decisions
- Extend the existing blockquote in place; no new section — state boundaries and failure behavior only (DESIGN Docs content policy).

## Alternatives considered
- N/A: docs-only single-note change.

## Implementation
### Target file
`docs/21_rag/rag_03_04_query_pipeline-search-stages.md`

### Procedure
- In the `> **Error handling**` blockquote (currently listing only `sqlite3.OperationalError` / `RuntimeError` for `vector_search`/`fts_search`), state that out-of-range or non-finite embedding elements are rejected at `get_embedding` and land in `embed_failed`, and that the per-query handler also counts packing failures (`ValueError`, `OverflowError`, `struct.error`) in `fts_errors` without propagation.

### Method
- One sentence appended to each of the blockquote's existing claims; keep the existing sentences intact.

### Details
- Current note (verified at HEAD `eb19564fe`) lists only `sqlite3.OperationalError` / `RuntimeError` as caught in `SearchStage`; sibling code documents `20261108-091441_01_scripts_rag_llm_client.py.md` and `20261108-091441_03_scripts_rag_stages_search.py.md` implement the behavior this note describes.

## Compatibility considerations
- N/A: docs-only.

## Security considerations
- N/A: docs-only.

## Rollback considerations
- N/A: revert the commit.

## Validation plan
| Target | Strategy | Command | Expected |
|---|---|---|---|
| edited doc | structure/quality gates | `uv run python tools/check_docs_quality.py`, `uv run python tools/check_docs_structure.py docs/21_rag/rag_03_04_query_pipeline-search-stages.md`, `uv run python tools/check_docs_content_policy.py`, `uv run python tools/check_docs_consistency.py --domain rag` | No findings |

## Completion criteria
- The note lists the out-of-range embedding degraded path accurately against the implemented code (`Acceptance Criteria REQ-003`, `REQ-004`); doc checkers report no findings.

## Out of Scope
- Any other section of the doc; the exception-inventory reference `docs/21_rag/rag_05_04-error-handling-reference.md` (Plan Reference Files: no query-path rows exist today, no edit).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Apply the note edit described in Implementation > Procedure/Method/Details | Pending | — | — | Gated: issues/20261107-050701_adrrag001_rag-fallback-failure-policy.md phase all - prose dependency; Plan Scope records "Related, no order required" |
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
- **Requirement ID**: `REQ-003` (backstop counting), `REQ-004` (degraded completion)
- **Source issue**: `issues/20261107-203511_ragvec001_rag-embedding-float32-overflow.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261108-075301_ragvec001_rag-embedding-float32-overflow.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261108-091441
- **Related target files**: `docs/21_rag/rag_03_04_query_pipeline-search-stages.md`
