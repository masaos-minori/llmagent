## Goal

- Add commit-level tests for the stale HTTP skip, the `file://`/`force` incoming-metadata rule, and the unchanged fresh/both-`None` behavior in `tests/rag/ingestion/test_ingestion_freshness.py` (`REQ-001`, `REQ-002`, `REQ-004` test rows).

## Scope
**Release unit**: N/A: not part of a release unit (Plan lists phases 2-3 only)

- Test file only: `tests/rag/ingestion/test_ingestion_freshness.py`.

## Assumptions

- Verified in this cycle: `test_stale_payload_cannot_regress_stored_freshness` (L513-535) asserts only the stored freshness row and still passes under the skip rule (the seeded row simply remains), so it is extended, not changed (Plan Background fact 4).
- No existing test in this file pins the stale-replace behavior: `test_abort_leaves_documents_and_chunks_at_pre_run_values` (L437) and `test_fresh_payload_insert_carries_payload_freshness` (L489) use non-stale payloads (verified).
- Reuse the module's helpers unchanged: `_make_freshness_db` (L331), `_seed_document` (L339), `_freshness_row` (L369), `_prepared` (L376).

## Design decisions

- Assert the skip outcome through `commit`'s return tuple (`(doc_id, True, False)`) plus zero-write evidence (`documents`, `chunks`, `chunks_vec` compared before/after), mirroring the existing before/after pattern in the abort test — no patching of internals.
- The `file://` case is built at commit level with a `file://` URL and a `sha256`-style etag, then closed through `DocumentManager.handle_existing_document` with the file predicate to prove the loop is broken (AC-2's "recognized as unchanged on the next run").

## Alternatives considered

- End-to-end ingest tests for the file-restore loop: deferred to the ingester-level companion test scope; commit-level keeps the file's existing unit style.

## Implementation
### Target file
- `tests/rag/ingestion/test_ingestion_freshness.py`

### Procedure
- Add three new test methods and extend one existing test, all in `TestFreshnessAtomicity`.

### Method
- `test_stale_http_commit_skips_replacement` (new): seed a document with chunks; commit `replace=True, force=False` with an older HTTP payload; assert the return is `(doc_id, True, False)`, `_freshness_row` unchanged, and `chunks` / `chunks_vec` rows identical to before (AC-1).
- `test_file_payload_older_mtime_replaces_with_incoming_metadata` (new): seed a `file://` document with a newer stored mtime/hash; commit `replace=True, force=False` with older `fetched_at` and a different `etag` hash; assert chunks are replaced, `_freshness_row` equals the incoming values, and a follow-up `handle_existing_document` (file predicate, same payload) returns `skip=True` (AC-2, no loop).
- `test_force_stale_commit_writes_incoming_metadata` (new): stale HTTP payload with `force=True`; assert content replaced and stored metadata equals the incoming stale values (AC-2).
- Extend `test_stale_payload_cannot_regress_stored_freshness` (L513): append `chunks` / `chunks_vec` unchanged assertions to the existing freshness-row assertion (extension only, AC-4).

### Details
- `_seed_document` seeds the freshness row; where a test needs pre-existing chunk rows, insert them with the same pattern the abort test already uses (`SELECT content FROM chunks` before/after comparison).
- Both-`None` and unparseable-timestamp tests (`TestResolveIncomingGuard`, L538+) stay unmodified (AC-4).

## Compatibility considerations

- `tests/rag/ingestion/test_ingester_etag_guard.py` is the mirrored guard suite and must stay untouched and green (Reference Files row).

## Security considerations
N/A: test-only change.

## Rollback considerations
N/A: revert the single commit.

## Validation plan

- `uv run pytest tests/rag/ingestion/test_ingestion_freshness.py tests/rag/ingestion/test_ingester_etag_guard.py -q` — new tests fail on HEAD, pass after seq-1/seq-2 land.
- `uv run pytest tests/rag/ingestion -q` regression.

## Completion criteria

- AC-1 (stale HTTP byte-identical + skip outcome), AC-2 (file older-mtime and force cases store incoming metadata, loop broken), and AC-4 (extended stale test, guard suites unmodified) are each asserted by a green test.

## Out of Scope

- The ingester-level skip-routing test (companion of the seq-3 document), production-code changes.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Add the new tests and the extension per Implementation > Method | Completed | 20261110-0900 | 20261110-0940 | AC-1 `test_stale_http_commit_skips_replacement`, AC-2 `test_file_payload_older_mtime_replaces_with_incoming_metadata` + `test_force_stale_commit_writes_incoming_metadata`, AC-4 extension of `test_stale_payload_cannot_regress_stored_freshness`. Gate (plans/...ragrev015 phase 3) evaluated stale — rev015 phase 3 is not a dependency of rev016; cleared per prior user approval. Also fixed a seq-3 regression in `tests/rag/ingestion/test_rag_ingester.py`: three tests mocked `TransactionManager.commit` with `return_value=None`; the seq-3 unpack `_, skipped, _ = tx_mgr.commit(...)` raised `TypeError`. Restored a realistic `(1, False, False)` tuple (the documented contract) — no production None-guard added (would be dead code). |
| 2 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20261110-0940 | 20261110-1015 | ruff clean; mypy 557 files clean; lint-imports 0 broken; ast-grep clean; bandit 0 medium/high; `tests/rag/ingestion` 330 passed; `test_mdq_rag_boundary` 5 passed; diff-cover 100% on changed production lines (`transaction_commit.py` 100%, `etag_manager.py` 100%; `ingester.py` omitted by project policy). Full-suite run has 3 failed / 25 errors in `tests/eventbus/test_eventbus_auth.py` — pre-existing environment issue (`eventbus.sqlite` missing `schema_migrations`), unrelated to this change (working tree touches only `rag/ingestion`). |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| 1 | seq-3 unpack `_, skipped, _ = tx_mgr.commit(...)` broke three `test_rag_ingester.py` tests that mocked `commit` with `return_value=None` (`TypeError: cannot unpack non-iterable NoneType`). Unrelated to seq-4 production behavior. | Yes — restored realistic `(1, False, False)` mock (documented contract); no production guard added | 20261110 |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| — | — | — | — | — | — |

## Traceability
- **Workflow phase**: plan-to-implementation-procedure
- **Requirement ID**: `REQ-001` (stale HTTP commit test), `REQ-002` (file/force tests), `REQ-004` (unchanged suites)
- **Source issue**: issues/20261108-131235_ragrev016_stale-recrawl-replaces-content.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261108-170725_ragrev016_stale-recrawl-replaces-content.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261109-234108
- **Related target files**: `tests/rag/ingestion/test_ingestion_freshness.py`
