## Goal

`REQ-001`: in `scripts/rag/ingestion/chunk_preparation.py` remove the `no-any-return` suppression on `_embed_and_store`. Embedding behavior is unchanged.

## Scope
**Release unit**: N/A: not part of a release unit

## Assumptions
- The wrapped return (`self._embed_service.embed_and_store`) is correctly typed once `rag.ingestion` is a regular package, so the suppression suppresses nothing.

## Design decisions
- Delete only the trailing `# type: ignore[no-any-return]  # –…` comment; the return expression is unchanged.

## Alternatives considered
- N/A: a single-line edit with no public-contract, persistence, or security impact.

## Implementation
### Target file
`scripts/rag/ingestion/chunk_preparation.py`

### Procedure
Remove the suppression and its comment on the `_embed_and_store` return.

### Method
In `_embed_and_store`, change
`        return self._embed_service.embed_and_store(doc_id, path)  # type: ignore[no-any-return]  # — embed_and_store() is correctly typed -> PreparedChunk | IngestionFailureReason; mypy loses this across the rag.* vs scripts.rag.* dual module-path resolution (see scripts/shared/tool_constants.py's confirmed duplicate-module-name issue)`
to
`        return self._embed_service.embed_and_store(doc_id, path)`
(current line 80).

### Details
- Preserve the method signature and docstring exactly.

## Compatibility considerations
N/A: behavior-preserving; embedding and failure handling are unchanged.

## Security considerations
N/A: no request handling or permission change.

## Rollback considerations
N/A: revert the commit.

## Validation plan
- `uv run mypy --no-namespace-packages scripts/ tests/eventbus tools`: the four `unused-ignore` are gone after this and docs 02–04 run; only the two `http_fetcher.py` `arg-type` errors remain until doc 06.
- `uv run pytest tests/rag/ingestion`: passes.
- `rg -n "type: ignore\[no-any-return\]" scripts/rag/ingestion/` (AC-1): no match after all suppression documents run.

## Completion criteria
- No `# type: ignore[no-any-return]` remains in this file.

## Out of Scope
The other suppression removals (docs 02–04), the `http_fetcher.py` typing fixes (doc 06).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 20261113-201242 | 20261113-204236 | suppression removed per Method |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20261113-201242 | 20261113-204236 | mypy 0 errors (561 files); pytest 353 passed; AC-1 clear |

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
- **Requirement ID**: `REQ-001`
- **Source issue**: issues/20261110-171004_rmcompat006_rag-ingestion-cleanup.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261112-121532_rmcompat006_rag-ingestion-cleanup.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261113-201242
- **Related target files**: `scripts/rag/ingestion/chunk_preparation.py`
