## Goal
State in the ChunkSplitter document that a `--force` run replaces the document's full chunk series in `chunk/` (`REQ-004`).

## Scope
**Release unit**: N/A: not part of a release unit

- In scope: the idempotency paragraph of section 3.1 of `docs/21_rag/rag_02_03_ingestion_pipeline-chunksplitter.md`.
- Out of scope: every other section, and `docs/21_rag/rag_02_01_ingestion_pipeline-overview.md` (owned by another Plan).

## Assumptions
- Verified on 2026-11-06 (Step 3a): the paragraph under "3.1 Class Overview" says the splitter is idempotent because an existing `{stem}-0000.json` sentinel skips processing, and that processing can be overwritten with `--force`; it does not say what a forced run does to files of the previous run. The document is English and has front matter.
- The behavior comes from the first procedure of this Plan; write the sentence in terms of intent and boundary, not of the helper's name or implementation (`skills/DESIGN.md` Docs content policy and No source-code line numbers).
- Overlap: the `raging007` Plan (gated on this one) also targets this document, in another section; the edits are compatible and this one lands first.
- The docs mapping for this change is `docs/00_index.md` "Document References by Task" (RAG ingestion); apply `skills/python-documentation/SKILL.md`.

## Design decisions
- Extend the existing paragraph with one or two sentences: a forced run is authoritative for the source's chunk series, so chunks of the previous run that the new run does not produce are removed, including when the new run produces none; non-forced runs are unchanged; a source that cannot be read or chunked keeps its existing series.

## Alternatives considered
N/A: single-paragraph update.

## Implementation
### Target file
`docs/21_rag/rag_02_03_ingestion_pipeline-chunksplitter.md`

### Procedure
1. Read the paragraph and its neighboring text.
2. Add the sentences described in Design decisions to that paragraph.
3. Run the documentation checkers listed in Validation plan.

### Method
- Write short, explicit sentences with consistent terms (`skills/DESIGN.md` Output language); do not copy file names of tests, line numbers, counts, or configuration values.

### Details
- Keep the front matter and every other section unchanged; keep code fences balanced.

## Compatibility considerations
N/A: documentation only.

## Security considerations
N/A: no secrets, hosts, or ports are written.

## Rollback considerations
N/A: revert the commit.

## Validation plan
- `uv run python tools/check_docs_quality.py`, `uv run python tools/check_docs_structure.py docs/21_rag/rag_02_03_ingestion_pipeline-chunksplitter.md`, `uv run python tools/check_docs_content_policy.py`, `uv run python tools/check_docs_consistency.py --domain rag`, `uv run python tools/check_docs_japanese.py`.
- `uv run python tools/check_needs_confirmation_inventory.py` (the paragraph adds no Needs-confirmation marker).

## Completion criteria
- The paragraph states that a forced run replaces the full series, that non-forced runs and unreadable sources keep the existing series, and every documentation checker above passes.

## Out of Scope
- Other sections and documents.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Update the idempotency paragraph | Pending | — | — | |
| 2 | Run the documentation checkers (`routing.md` Tools "When to run which tool") | Pending | — | — | |
| 3 | N/A: no tests | Pending | — | — | |

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
- **Requirement ID**: `REQ-004` (document the forced-run behavior)
- **Source issue**: issues/20261106-073538_raging004_force-rechunk-stale-chunks.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261106-101257_raging004_force-rechunk-stale-chunks.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261106-131606
- **Related target files**: `docs/21_rag/rag_02_03_ingestion_pipeline-chunksplitter.md`
