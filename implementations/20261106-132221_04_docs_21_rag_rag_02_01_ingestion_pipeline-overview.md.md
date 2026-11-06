## Goal
Update the chunk-file lifecycle row to the two terminal directories: `registered/` on success, `failed/` with a `.error.json` file on any failure, with no `retry/` mention (`REQ-005`).

## Scope
**Release unit**: N/A: not part of a release unit

- In scope: the lifecycle table row of `chunk/` files in `docs/21_rag/rag_02_01_ingestion_pipeline-overview.md`.
- Out of scope: every other row and document.

## Assumptions
- Verified on 2026-11-06 (Step 3a): the `chunk/` row says files are moved out of `chunk/` to `registered/` on success, to `retry/` (embedding failures) or `failed/` (other failures, with a `.error.json` file) on failure; no other RAG document references the `retry/` directory (the error-handling reference describes only the embedding client's HTTP backoff, and the logging reference lists log categories). The document is English with front matter.
- The 003 Plan's documentation procedure (`implementations/20261106-115721_05_docs_21_rag_rag_02_01_ingestion_pipeline-overview.md.md`, not yet executed) rewrites the same row to its final lifecycle after this one; this procedure only removes `retry/`, so the two do not contradict each other, and this Plan goes first.
- Apply `skills/python-documentation/SKILL.md`; the mapping is `docs/00_index.md` "Document References by Task" (RAG ingestion).
- Design 2 was approved by the operator on 2026-11-06 (Plan UNK-01 resolved): remove the `retry/` tier; every failed chunk goes to `failed/` with its `.error.json`.
- Release unit `retry-tier-removal` (Plan phases 1 and 2) has three members in `seq` order: the test file first (its flipped assertions fail until the code lands), then `file_routing.py`, then `chunk_preparation.py`; the end-of-unit run is the single full-suite run (`skills/code-implementation/workflow.md` Batch mode).
- Overlap: the 003 Plan's procedures (not yet executed) also edit `scripts/rag/ingestion/ingester.py` (group-failure routing) and the lifecycle row of `docs/21_rag/rag_02_01_ingestion_pipeline-overview.md`; they do not edit `file_routing.py`, `chunk_preparation.py`, or this test file's retry tests. This Plan goes first (Plan Design) and the 003 documentation procedure rewrites the same row afterwards.
- Step 3a (2026-11-06, HEAD `97b8f4f6b`): `RagIngester.ingest_url_group` passes the fixed reason string `embedding_partial_failure` (not an `IngestionFailureReason` member) for each prepared chunk of a group that also had a failed chunk; the Plan was corrected so this known production reason is accepted without a `WARNING`.

## Design decisions
- Rewrite the failure part of the row: all failures move to `failed/` together with a `.error.json` file; remove the `retry/` wording. Mention recovery only as the existing supported paths (re-chunking from the source with `--force`, or re-running the ingester after the embedding service is fixed), without copying commands or configuration values.

## Alternatives considered
N/A: single-row update.

## Implementation
### Target file
`docs/21_rag/rag_02_01_ingestion_pipeline-overview.md`

### Procedure
1. Read the row and the paragraph around it.
2. Replace the failure part of the row as described in Design decisions.
3. Run the documentation checkers listed in Validation plan.

### Method
- Short, explicit sentences, consistent terms; no line numbers, counts, or configuration values (`skills/DESIGN.md`).

### Details
- Keep the front matter and the other rows unchanged; keep table pipes and code fences intact.

## Compatibility considerations
N/A: documentation only.

## Security considerations
N/A: no secrets, hosts, or ports are written.

## Rollback considerations
N/A: revert the commit.

## Validation plan
- `uv run python tools/check_docs_quality.py`, `uv run python tools/check_docs_structure.py docs/21_rag/rag_02_01_ingestion_pipeline-overview.md`, `uv run python tools/check_docs_content_policy.py`, `uv run python tools/check_docs_consistency.py --domain rag`, `uv run python tools/check_docs_japanese.py`.
- `rg -n 'retry/' docs/21_rag` shows no remaining mention of the removed directory.

## Completion criteria
- The row lists only `registered/` and `failed/` as destinations, states that failures carry a `.error.json` file, and every documentation checker above passes.

## Out of Scope
- Other rows and documents.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Update the lifecycle row | Completed | 20261106-163353 | 20261106-163353 |  |
| 2 | Run the documentation checkers (`routing.md` Tools "When to run which tool") | Completed | 20261106-163353 | 20261106-163353 |  |
| 3 | N/A: no tests | Completed | 20261106-163353 | 20261106-163353 |  |

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
- **Requirement ID**: `REQ-005` (lifecycle documentation)
- **Source issue**: issues/20261106-073538_raging005_retry-dir-no-consumer.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261106-102010_raging005_retry-dir-no-consumer.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261106-132221
- **Related target files**: `docs/21_rag/rag_02_01_ingestion_pipeline-overview.md`