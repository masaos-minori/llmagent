## Goal

Give `RagIngester` one explicit lifecycle: remove the unused `_rag_pipeline_service_url` attribute, the `__del__` that duplicates `close()`, and the uncalled `_log_ingest_failure`; make `main()` close the client in a `finally` block (REQ-003 / AC-3).

## Scope
**Release unit**: N/A: not part of a release unit

## Assumptions

- The only production caller is `main()`, which will now call `close()` in a `finally`. Tests construct the ingester directly and already call `close()` or mock `_client`.
- After deleting `_log_ingest_failure`, `read_chunk_json` and `ChunkFormatError` remain used (at `_read_chunk_json` and around `commit_url_group`), so no import becomes dangling.
- Re-verified 2026-11-12: there is no compatibility / past-signature sentence in the `ingest_all` or `__init__` docstring, so that clause of REQ-003 is already satisfied (no-op).

## Design decisions

- `main()` uses `try/finally` (not a context manager): `try: ingester.ingest_all(args.force)` / `finally: ingester.close()`. Adds no new protocol to `RagIngester`.

## Alternatives considered

A context-manager (`__aenter__`/`__exit__` or `contextlib`) was considered but rejected: `try/finally` adds no new protocol and matches the existing call site.

## Implementation
### Target file
`scripts/rag/ingestion/ingester.py`

### Procedure
Remove the attribute, `__del__`, and `_log_ingest_failure`; wrap `main()`'s call in `try/finally`.

### Method
Edit.

### Details
1. In `__init__`, delete the attribute assignment (line 123):

```
        self._rag_pipeline_service_url: str = cfg.get("rag_pipeline_service_url", "")
```

2. Delete the `__del__` method (lines 138-143):

```
    def __del__(self) -> None:
        try:
            client = getattr(self, "_client", None)
            if client is not None:
                client.close()
        except OSError:
            pass

```

3. Delete the `_log_ingest_failure` method (lines 392-412, up to but not including `def commit_url_group`):

```
    def _log_ingest_failure(self, doc_id: int, path: Path, e: Exception) -> None:
        """Log a chunk ingestion failure."""
        chunk_url = ""
        try:
            chunk_data = read_chunk_json(path)
            chunk_url = chunk_data.url or ""
        except ChunkFormatError:
            pass
        logger.error(
            "Failed to ingest %s: %s",
            path,
            e,
            extra={
                "doc_id": doc_id,
                "url": chunk_url,
                "source_type": "file",
                "stage_name": "ingester",
            },
        )

```

4. In `main()`, wrap the ingest call in `try/finally`:

```
    ingester = RagIngester()
    try:
        ingester.ingest_all(args.force)
    finally:
        ingester.close()
```

## Compatibility considerations

Callers that never called `close()` now rely on `finally`; the sole production caller (`main()`) is covered.

## Security considerations

N/A: lifecycle cleanup only.

## Rollback considerations

N/A: revert the commit.

## Validation plan

- `uv run pytest tests/rag/ingestion` passes; no `__del__`/`_log_ingest_failure` remains.
- `rg -n "__del__|_log_ingest_failure" scripts/rag/ingestion/ingester.py` returns nothing.
- `uv run ruff format` / `ruff check` / `mypy --no-namespace-packages` clean.

## Completion criteria

`RagIngester` defines no `__del__` and no `_log_ingest_failure`; `main()` closes its client in a `finally` block.

## Out of Scope

The same-named `_log_ingest_failure` in `chunk_preparation.py` (called, stays untouched).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | |
| 2 | Add or update tests per Validation plan | Pending | — | — | N/A: no new lifecycle test |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Pending | — | — | |

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
- **Requirement ID**: REQ-003 — `RagIngester` lifecycle cleanup + `main()` `finally` close
- **Source issue**: issues/20261110-170632_rmcompat001_rag-delegation-leftovers.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261112-115458_rmcompat001_rag-delegation-leftovers.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261112-210705
- **Related target files**: scripts/rag/ingestion/ingester.py
