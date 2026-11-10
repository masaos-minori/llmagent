## Goal

- Make `TransactionManager.commit` skip the whole replace branch for a stale non-forced HTTP payload and persist incoming metadata for `file://` and `force` replaces (`REQ-001`: stale HTTP skip; `REQ-002`: incoming-wins for file/force; `REQ-004`: fresh/both-`None` paths unchanged).

## Scope
**Release unit**: ragrev016-core

- The `if doc_id is None or replace:` block of `commit` in `scripts/rag/ingestion/transaction_commit.py`.

## Assumptions

- Implementation lands after ragrev015 phase 3 (Plan Scope dependency): the caller-side helper (`commit_url_group` in ragrev015's seq-3 document) must exist first; this document does not touch the caller.
- `commit`'s return contract `(doc_id, skip, replace)` (docstring L53-56) is the vehicle for the skip outcome: a stale skip returns `(doc_id, True, False)` with no delete and no insert — verified the value is currently ignored by `ingester.py` L331-345 and the existing suite never inspects it.
- A `file://` document is recognized by `url.startswith("file://")`, the same predicate `DocumentStore.get_or_create` passes to `DocumentManager.handle_existing_document` (document_persistence.py L68).

## Design decisions

- The stale check runs inside the `begin_immediate` transaction before `delete_existing_document` (mirroring the existing pre-delete guard comment at L62-64), so the skip is race-consistent with the transaction.
- For `file://` and `force`, the `resolve_incoming` guard is bypassed entirely and the incoming `(etag, last_modified, fetched_at)` is written as-is (Plan Implementation Intent: incoming generation always wins there); for fresh HTTP and the both-`None` case the existing `resolve_incoming` call stays (REQ-004).
- The staleness rule lives in `commit` (a small private branch), not in a new module, so `commit` (radon B (7)) stays in band (Plan Design).

## Alternatives considered

- Keep replacing but always write incoming metadata: rejected by the Plan (older content would overwrite newer content and regress validators).

## Implementation
### Target file
- `scripts/rag/ingestion/transaction_commit.py`

### Procedure
- In the replace branch, before the delete, branch on source/force: HTTP non-forced stale → return the skip outcome immediately; otherwise proceed with delete + insert as today, with metadata selection per Design decisions.

### Method
- Inside `with self._db.begin_immediate():`, when `replace and doc_id is not None`:
  - `if not force and not url.startswith("file://") and ETagManager(self._db, doc_id).is_stale_incoming(etag, last_modified, fetched_at):` → `return doc_id, True, False` (transaction closes with no writes).
  - Else if `url.startswith("file://") or force`: skip the `resolve_incoming` call — persist the incoming `etag, last_modified, fetched_at` via `self._doc_store.insert(...)`.
  - Else: keep the existing `resolve_incoming(...)` call and its resolved values (fresh or both-`None` payload).
- Chunk insertion, `lastrowid` remap (L82-85), and the success return `(doc_id, False, False)` stay unchanged.

### Details
- `ETagManager` is already imported (L17); no new import edges.
- The stale-skip return happens before `delete_existing_document`, so `documents`, `chunks`, and `chunks_vec` rows are byte-identical (AC-1) — the `vec0` table is never touched on this path.
- `insert` already receives all metadata fields; no signature changes anywhere.

## Compatibility considerations

- Existing freshness tests all commit fresh or stale-HTTP payloads through paths whose asserted outcome is unchanged (verified against `tests/rag/ingestion/test_ingestion_freshness.py` L390-535 in this cycle): the stale test's asserted stored row still holds under the skip, and the abort/fresh tests use non-stale payloads.
- `resolve_incoming` stays for metadata semantics; `update()` untouched.

## Security considerations
N/A: freshness decision on already-validated values.

## Rollback considerations
N/A: revert the single commit; no schema or data migration involved.

## Validation plan

- `uv run pytest tests/rag/ingestion/test_ingestion_freshness.py tests/rag/ingestion/test_ingester_etag_guard.py -q` — the seq-4 new tests fail on HEAD, pass after; both existing suites green (AC-1, AC-2, AC-4).
- `uv run pytest tests/rag/ingestion -q` regression.
- `uv run ruff check`, `uv run mypy`, `PYTHONPATH=scripts uv run lint-imports`.

## Completion criteria

- A stale HTTP `commit(replace=True, force=False)` returns the skip outcome with zero writes (AC-1); a `file://` older-mtime or a `force` replace stores incoming metadata with replaced chunks (AC-2); fresh/both-`None` behavior is byte-identical (AC-4).

## Out of Scope

- Caller-side skip logging/routing (seq-3 document), the both-`None` validator rule (Out-of-Scope, UNK-02), the HTTP skip decision in `DocumentManager` (ragrev010).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | Gated: plans/20261108-170534_ragrev015_poison-chunk-groups-retried.md phase 3 - both plans edit the `tx_mgr.commit(...)` block chain; land the commit-error handling first so the skip handling is added to the settled block |
| 2 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | Tests-first cases live in the seq-4 document |

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
- **Requirement ID**: `REQ-001` (stale HTTP skip), `REQ-002` (incoming metadata for file/force), `REQ-004` (unchanged paths)
- **Source issue**: issues/20261108-131235_ragrev016_stale-recrawl-replaces-content.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261108-170725_ragrev016_stale-recrawl-replaces-content.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261109-234108
- **Related target files**: `scripts/rag/ingestion/transaction_commit.py`
