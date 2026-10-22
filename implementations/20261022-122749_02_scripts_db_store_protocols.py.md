## Goal
- Replace the stale `Note:` in the `DocumentStore.chunk_insert` docstring with the same responsibility-level relationship as the DB protocol document (`REQ-002`: docstring-only reword; `REQ-003`: validate that nothing regresses).

## Scope
- Change only the two `Note:` body lines (lines 130-131) of the `chunk_insert` docstring in `DocumentStore`. No signature, code, import, or other docstring changes.

## Assumptions
- The note's claim is true: the `chunk_insert` field set matches the chunk INSERT of the RAG ingestion transaction commit (same six `chunks` columns; `scripts/db/store_impl.py:157`, `scripts/rag/ingestion/transaction_commit.py:98`). Falsified if a column list differs at implementation time; then stop and report.
- `scripts/rag/ingestion/transaction_commit.py` exists (verified); the docstring cites it as `rag/ingestion/transaction_commit.py`, the same scripts-relative style the old note used.

## Design decisions
- Same meaning as the document sentence (see the db_05 procedure), expressed in docstring style: responsibility plus module path, no private symbol name.
- Keep each new line within 88 characters (`ruff format` limit, `rules/coding.md`).

## Alternatives considered
N/A: comment-only change; the Issue fixes the intent.

## Implementation
### Target file
`scripts/db/store_protocols.py`

### Procedure
1. Replace the `Note:` body at lines 130-131 with the wording in Details.
2. Run the validation commands below.

### Method
- Use Edit with the exact old line (`Field set matches RagIngester._insert_chunk() INSERT in rag/ingester.py.`) as `old_string`; it occurs once. Keep the 12-space docstring indentation.

### Details
- Old: `Field set matches RagIngester._insert_chunk() INSERT in rag/ingester.py.`
- New (two lines, 12-space indent):
  - `Field set matches the chunk INSERT of the RAG ingestion transaction`
  - `commit (rag/ingestion/transaction_commit.py); keep the two in sync.`
- Reference only (not modified): `scripts/db/store_impl.py` (`SQLiteDocumentStore.chunk_insert`), `scripts/rag/ingestion/transaction_commit.py`, `scripts/db/schema_sql.py`, `tests/db/test_db_store_impl.py`.

## Compatibility considerations
N/A: docstring text only; the protocol signature and runtime behavior are unchanged.

## Security considerations
N/A: no code or data handling is touched.

## Rollback considerations
N/A: revert the commit.

## Validation plan
- `git diff scripts/db/store_protocols.py` — only docstring lines changed.
- `rg -n "_insert_chunk\b|rag/ingester.py" scripts/db` — no match.
- `uv run ruff format --check scripts/db/store_protocols.py` and `uv run ruff check scripts/`
- `uv run mypy --no-namespace-packages scripts/`
- `uv run pytest tests/db -q`
- `uv run python tools/check_module_size.py` (file is about 5100 B, far below the 16384 B gate).
- Deploy: the docstring change reaches `/opt/llm/` through `skills/deploy/SKILL.md`; it has no behavior change, so the deploy may be batched with the next production deploy.

## Completion criteria
- The docstring `Note:` contains neither `_insert_chunk` nor `rag/ingester.py`, states the same relationship as the db_05 sentence, and `git diff` shows docstring lines only.
- `ruff`, `mypy`, and `pytest tests/db -q` pass.

## Out of Scope
- The protocol signature, `scripts/db/store_impl.py`, the ingestion code, the tests, and the db_05 document (own procedure).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Reword the `Note:` lines of the `chunk_insert` docstring (Implementation > Procedure step 1) | Pending | — | — | |
| 2 | Run `ruff`, `mypy`, `pytest tests/db -q`, and the module size check (Validation plan) | Pending | — | — | |
| 3 | Deploy the docstring change to production, batched with the next deploy (Validation plan) | Pending | — | — | |

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
- **Requirement ID**: `REQ-002` (reword the docstring note), `REQ-003` (record the comparison and validate)
- **Source issue**: issues/20261022-104122_dbchunkref_fix-stale-insert-chunk-reference-db-doc.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261022-121654_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261022-122749
- **Related target files**: scripts/db/store_protocols.py
