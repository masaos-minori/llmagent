## Goal
- Replace the dangling `RagIngester._insert_chunk()` reference in the DB protocol document with a responsibility-level statement that matches the verified field-set relationship (`REQ-001`: reword the sentence; `REQ-003`: confirm the `db` domain no longer reports `_insert_chunk()`).

## Scope
- Reword only the field-set sentence in line 22 of the target file. Every other sentence of that paragraph, and every other line of the file, stays unchanged.

## Assumptions
- The `chunk_insert` field set and the ingestion chunk INSERT write the same six `chunks` columns (`doc_id`, `chunk_index`, `content`, `normalized_content`, `chunk_type`, `source_file`); evidence: `scripts/db/store_impl.py:157` and `scripts/rag/ingestion/transaction_commit.py:98`. Falsified if a column list differs at implementation time; then stop and report instead of asserting a match.
- A module path in the sentence is acceptable under the docs content policy, because the current sentence already cites one; falsified if `check_docs_content_policy.py --strict` reports the sentence.

## Design decisions
- Name the ingestion side by responsibility ("the chunk INSERT of the RAG ingestion transaction commit") plus its module path; do not name the private method `_insert_chunks_batch`.
- Limit the claim to the field set. The empty-string-to-NULL normalization and the `chunks_vec` insert in ingestion are behavior differences and must not be added to the sentence.

## Alternatives considered
N/A: wording-only change; the Issue fixes the intent (restate at responsibility level).

## Implementation
### Target file
`docs/41_db/db_05_api_and_operations-protocol-and-backend.md`

### Procedure
1. Replace the clause `matches \`RagIngester._insert_chunk()\` in \`scripts/rag/ingestion/ingester.py\`, so callers must verify consistency with the ingester when adding or modifying chunk fields` with the wording in Details.
2. Run the validation commands below.

### Method
- Use Edit with the exact old clause as `old_string`; it occurs once (line 22).

### Details
- Old clause: `intentionally matches \`RagIngester._insert_chunk()\` in \`scripts/rag/ingestion/ingester.py\`, so callers must verify consistency with the ingester when adding or modifying chunk fields.`
- New clause: `intentionally matches the chunk INSERT of the RAG ingestion transaction commit (\`scripts/rag/ingestion/transaction_commit.py\`), so callers must keep the two in sync when adding or modifying chunk fields.`
- The wording must stay identical in meaning to the docstring note written for `scripts/db/store_protocols.py` (a separate procedure document).

## Compatibility considerations
N/A: one documentation sentence; no code, config, or test reads it.

## Security considerations
N/A: no code or data handling is touched.

## Rollback considerations
N/A: revert the commit.

## Validation plan
- `uv run python tools/check_docs_consistency.py --domain db` — no `_insert_chunk()` Warning (the unrelated `copy2()` Warning in `db_07_...` may remain).
- `uv run python tools/check_docs_quality.py`
- `uv run python tools/check_docs_structure.py docs/41_db/db_05_api_and_operations-protocol-and-backend.md`
- `uv run python tools/check_docs_content_policy.py`
- `rg -n "_insert_chunk\b|RagIngester" docs/41_db` — no match.

## Completion criteria
- The sentence contains neither `_insert_chunk` nor `RagIngester`, names the ingestion transaction commit's chunk INSERT by responsibility, and keeps the "callers must keep the field sets in sync" instruction.
- `git diff` for the file shows only that sentence changed; the docs checkers pass and the `db` domain no longer reports `_insert_chunk()`.

## Out of Scope
- `scripts/db/store_protocols.py` (own procedure), the ADR that cites the private ingestion method, and the `copy2()` Warning in `db_07_api_and_operations-recovery-and-reference.md`.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Reword the field-set sentence at line 22 (Implementation > Procedure step 1) | Completed | 20261022-125044 | 20261022-125044 |  |
| 2 | Run the `db` domain consistency check and the docs checkers (Validation plan) | Completed | 20261022-125044 | 20261022-125044 |  |

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
- **Requirement ID**: `REQ-001` (reword the document sentence), `REQ-003` (record the comparison and validate)
- **Source issue**: issues/20261022-104122_dbchunkref_fix-stale-insert-chunk-reference-db-doc.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261022-121654_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261022-122749
- **Related target files**: docs/41_db/db_05_api_and_operations-protocol-and-backend.md