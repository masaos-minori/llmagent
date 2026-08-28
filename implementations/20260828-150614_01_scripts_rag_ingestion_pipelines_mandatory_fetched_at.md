## Goal

Make `fetched_at` a mandatory, non-null `str` across every layer of the RAG ingestion pipeline (crawler DTO, chunk metadata, chunk JSON, ingester, document manager, etag manager, document store) and delete the null-fill compatibility branch `_update_null_fill()`. Change timestamp validation from fail-open to fail-closed.

## Scope

- **In-Scope**:
  - Crawler: generate canonical UTC `fetched_at` (`YYYY-MM-DDTHH:MM:SSZ`)
  - ChunkDocument: add mandatory `fetched_at` field
  - ChunkJsonRaw/CrawlFilePayload/ChunkOutputPayload/ChunkMetadata: add required `fetched_at`
  - Ingester: remove `fetched_at` omission branch, require `str` parameter
  - DocumentManager: require `str` for `fetched_at`/`new_fetched_at` parameters
  - ETagManager: delete `_update_null_fill()`, require `str`, fail-closed validation
  - DocumentStore protocol + SQLiteDocumentStore: add `fetched_at: str` parameter
  - Schema: remove `DEFAULT (strftime(...))` clause from `documents.fetched_at`
  - All callers, mocks, fixtures updated accordingly
- **Out-of-Scope**:
  - Changing envelope-level `MCP_TOOL_SCHEMA_VERSION` constant
  - Removing unused constructor arguments from ToolRouteResolver/ToolExecutor
  - Server-side MCP response builder changes

## Assumptions

- No production code depends on `fetched_at` being optional or database-derived (confirmed by issue verification).
- The canonical UTC form `YYYY-MM-DDTHH:MM:SSZ` is acceptable for all layers (no timezone-aware datetime objects needed downstream).
- Local-file crawl path should derive `fetched_at` from file modification time rather than wall-clock "now" (per issue statement).
- Equal-timestamp case behavior: implement "skip" (equal means not fresh) based on existing `<` comparison semantics, and document this decision explicitly.

## Design decisions

- `fetched_at` is generated once at crawl time, never regenerated downstream.
- All layers use the same canonical UTC string format (`YYYY-MM-DDTHH:MM:SSZ`).
- Fail-closed validation replaces fail-open: reject malformed timestamps instead of treating them as "not stale."
- Equal-timestamp case: recommend "skip" (equal means not fresh) since `<` comparison already defines staleness.
- For local-file crawl path: derive `fetched_at` from file modification time rather than wall-clock "now".

## Alternatives considered

- Using timezone-aware datetime objects downstream. Chose canonical UTC string format for simplicity and consistency across all layers.
- Centralizing the `schema_version` constant into a shared module. Not applicable to this task.
- Adding deprecation warnings before removing tolerance branches. Chose direct removal per issue intent — no aliasing, no deprecation warnings, no migration/fallback logic.

## Implementation

### Target files

- `scripts/rag/ingestion/crawler.py`
- `scripts/rag/models_data.py`
- `scripts/rag/ingestion/pipeline_utils.py`
- `scripts/rag/ingestion/chunk_splitter.py`
- `scripts/rag/ingestion/ingester.py`
- `scripts/rag/ingestion/document_manager.py`
- `scripts/rag/ingestion/etag_manager.py`
- `scripts/db/store_protocols.py`
- `scripts/db/store_impl.py`
- `scripts/db/schema_sql.py`

### Procedure

**Phase 1: Preparation — Establish canonical UTC format**

1. Read `scripts/rag/ingestion/crawler.py` and identify where `fetched_at` is generated via `datetime.now().isoformat(timespec="seconds")`.
2. Replace with canonical UTC form: `datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")`.
3. For local-file crawl path, derive UTC form from file modification time: confirm `mtime_iso` usage pattern at line ~134 in `crawler.py` and apply the same UTC strftime conversion.

**Phase 2: Core Logic — Propagate fetched_at through DTOs and models**

4. Read `scripts/rag/models_data.py` and add mandatory `fetched_at: str` field to `ChunkDocument`.
5. Read `scripts/rag/ingestion/pipeline_utils.py` and change `ChunkJsonRaw.fetched_at` from `NotRequired[str | None]` to required `str`.
6. Read `scripts/rag/ingestion/chunk_splitter.py` and add `fetched_at: str` to `CrawlFilePayload`, `ChunkOutputPayload`, `ChunkMetadata`.
7. Thread crawler's `fetched_at` through `ChunkSplitter` per-chunk output construction.

**Phase 3: Core Logic — Make ingester and document manager strict**

8. Read `scripts/rag/ingestion/ingester.py` and change `Ingester._get_or_create_document()`, `_insert_document()`, `_commit_url_transaction()` parameters to `fetched_at: str`.
9. Delete `cursor2` branch in `_insert_document()` that omits `fetched_at` column.
10. Read `scripts/rag/ingestion/document_manager.py` and change `DocumentManager.handle_existing_document()` and `_update_etag()` to require `str` for `fetched_at`/`new_fetched_at`.

**Phase 4: Core Logic — Fix etag manager**

11. Read `scripts/rag/ingestion/etag_manager.py` and change `ETagManager.update()` to require `new_fetched_at: str`.
12. Delete `_update_null_fill()` entirely and its dispatch branch in `update()`.
13. In `_is_stale_update()`: reject timezone-naive `new_fetched_at`, raise on `ValueError` for incoming timestamp, raise for stored timestamp parse failure.
14. Replace `COALESCE(?, fetched_at)` with `fetched_at = ?` in `_update_with_freshness()`.
15. Ensure `update()` calls freshness path even when `etag` and `last_modified` are both `null`.
16. Resolve equal-timestamp case: implement consistent "skip" behavior with test.

**Phase 5: Core Logic — Update store protocol and implementation**

17. Read `scripts/db/store_protocols.py` and add `fetched_at: str` to `DocumentStore.doc_upsert()` protocol signature.
18. Read `scripts/db/store_impl.py` and update `SQLiteDocumentStore.doc_upsert()` to accept `fetched_at: str`, use directly for INSERT and ON CONFLICT UPDATE.
19. Remove `fetched_at = strftime('%Y-%m-%dT%H:%M:%SZ', 'now')` substitution in upsert.

**Phase 6: Schema cleanup**

20. Read `scripts/db/schema_sql.py` and remove `DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ', 'now'))` clause from `documents.fetched_at`.

**Phase 7: Test and fixture updates**

21. Update all mocks/fixtures that construct `ChunkDocument` without `fetched_at`.
22. Update all mocks/fixtures calling changed signatures without `fetched_at`.
23. Add unit tests per Testing Expectations section.

**Phase 8: Verification**

24. Run `rg -n "fetched_at|_update_null_fill|new_fetched_at.*None|COALESCE\(\?, fetched_at\)|strftime\('%Y-%m-%dT%H:%M:%SZ'" scripts tests` — verify zero matches for `_update_null_fill` and `COALESCE(?, fetched_at)`.
25. Run `uv run pytest -q tests` — confirm all affected tests pass.

### Method

Direct edits to source files following the phased approach above. Each phase modifies one logical subsystem before proceeding to the next.

### Details

**Phase 1 details:**
- Current: `datetime.now().isoformat(timespec="seconds")` produces naive local time like `"2026-08-28T15:00:00"`
- Replacement: `datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")` produces canonical UTC like `"2026-08-28T15:00:00Z"`
- For local-file crawl: replace wall-clock "now" with `os.path.getmtime(filepath)` converted to ISO UTC form

**Phase 2 details:**
- `ChunkDocument`: add `fetched_at: str` field (non-optional, no default)
- `ChunkJsonRaw.fetched_at`: change `NotRequired[str | None]` → `Required[str]`
- `chunk_splitter.py`: add `fetched_at: str` to all three TypedDicts; thread crawler's value through per-chunk output

**Phase 3 details:**
- `Ingester`: change all `fetched_at: str | None` parameters to `fetched_at: str`; delete `cursor2` branch
- `DocumentManager`: change `fetched_at: str | None` / `new_fetched_at: str | None` to `fetched_at: str` / `new_fetched_at: str`

**Phase 4 details:**
- `ETagManager.update()`: change `new_fetched_at: str | None` to `new_fetched_at: str`
- Delete `_update_null_fill()` method body and its call site in `update()`
- `_is_stale_update()`: add `try/except ValueError` around `datetime.fromisoformat()` for both incoming and stored values; raise on parse failure
- `_update_with_freshness()`: replace `COALESCE(?, fetched_at)` with direct `fetched_at = ?` assignment
- Equal-timestamp: implement "skip" — only update when `new_fetched_at > stored_fetched_at` (strict greater-than)

**Phase 5 details:**
- `store_protocols.py`: add `fetched_at: str` to `doc_upsert()` protocol signature
- `store_impl.py`: change `SQLiteDocumentStore.doc_upsert()` to accept `fetched_at: str`, use it directly in INSERT and ON CONFLICT UPDATE clauses
- Remove all `strftime('%Y-%m-%dT%H:%M:%SZ', 'now')` substitutions in write paths

**Phase 6 details:**
- `schema_sql.py`: remove `DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ', 'now'))` from `documents.fetched_at` column definition
- Document why DEFAULT was removed in a comment

**Phase 7 details:**
- Search `tests/` for all `ChunkDocument` constructions and add `fetched_at` argument
- Search `tests/` for all calls to changed signatures and add `fetched_at` arguments
- Add unit tests covering: newer timestamp with non-null HTTP metadata, newer timestamp with both etag/last_modified null, older (stale) timestamp, equal timestamp, timezone-naive input (expect raise), malformed input (expect raise)

## Compatibility considerations

- Removing `DEFAULT (strftime(...))` from schema could break any direct SQL inserts that omit `fetched_at`. Verify no such inserts exist; if they do, add the column to those INSERT statements.
- Changing `_is_stale_update()` from fail-open to fail-closed could cause legitimate updates to be rejected if there are existing malformed timestamps in the database. This is intentional — the issue states "no legacy data depends on fetched_at being optional or database-derived," so any malformed values should be surfaced as errors during migration.

## Security considerations

- Fail-closed validation prevents corrupt timestamps from silently passing through to update SQL, which could otherwise lead to incorrect freshness tracking and stale content serving.
- The equal-timestamp "skip" decision ensures that an attacker cannot replay an old but valid-looking timestamp to prevent detection of a real update.

## Rollback considerations

- Revert each phase independently if issues arise.
- Schema change (Phase 6) requires careful rollback: restoring the DEFAULT clause may not fully recover original behavior if rows were inserted without `fetched_at` during the interim period.
- No data migration needed — the change removes a default rather than adding one.

## Validation plan

| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| `scripts/rag/ingestion/crawler.py` | Unit: assert fetched_at format is YYYY-MM-DDTHH:MM:SSZ with Z suffix | uv run pytest tests/rag/ingestion/test_crawler.py | UTC format verified |
| `scripts/rag/models_data.py` | Unit: assert ChunkDocument constructor requires fetched_at | uv run pytest tests/rag/test_models_data.py | Mandatory field enforced |
| `scripts/rag/ingestion/chunk_splitter.py` | Integration: assert all chunk files from one crawl carry identical fetched_at | uv run pytest tests/rag/ingestion/test_chunk_splitter.py | Consistent propagation |
| `scripts/rag/ingestion/ingester.py` | Unit: assert fetched_at column always present in INSERT | uv run pytest tests/rag/ingestion/test_ingester.py | No omission branch |
| `scripts/rag/ingestion/etag_manager.py` | Unit: assert _update_null_fill removed, fail-closed validation works | uv run pytest tests/rag/ingestion/test_etag_manager.py | Zero _update_null_fill refs, raises on bad input |
| `scripts/db/store_impl.py` | Integration: assert fetched_at lands in documents.fetched_at after insert/update | uv run pytest tests/db/test_store_impl.py | Source time preserved |
| `scripts/db/schema_sql.py` | Schema: verify no DEFAULT clause on fetched_at | rg -n "DEFAULT.*strftime.*fetched_at" scripts/db/schema_sql.py | Zero matches |

## Completion criteria

- AC-001: Crawler output always contains a canonical UTC `fetched_at` (`YYYY-MM-DDTHH:MM:SSZ`) — REQ-001
- AC-002: Every chunk produced from one crawler record contains the identical `fetched_at` — REQ-003
- AC-003: `ChunkDocument`, `Ingester`, `DocumentManager`, `ETagManager`, and `DocumentStore` (protocol + `SQLiteDocumentStore`) all require a non-null `fetched_at`/`new_fetched_at` — REQ-002, REQ-004, REQ-005, REQ-006, REQ-008
- AC-004: `documents.fetched_at` equals the source crawler timestamp after both INSERT and UPDATE — REQ-004, REQ-008, REQ-009
- AC-005: `ETagManager._update_null_fill()` no longer exists in the codebase — REQ-006
- AC-006: No application path omits or synthesizes `fetched_at` — REQ-004
- AC-007: An update with an older incoming `fetched_at` does not overwrite newer stored metadata — REQ-006
- AC-008: An update with a newer incoming `fetched_at` updates `documents.fetched_at` even when `etag` and `last_modified` are both `null` — REQ-007
- AC-009: Malformed or timezone-naive timestamps raise before reaching update SQL — REQ-006
- AC-010: `fetched_at = COALESCE(?, fetched_at)` no longer appears in `etag_manager.py` — REQ-006, REQ-007
- AC-011: The equal-timestamp case has a defined, tested behavior — REQ-010
- AC-012: All affected tests pass

## Out of scope

- Changing envelope-level `MCP_TOOL_SCHEMA_VERSION` constant
- Removing unused constructor arguments from ToolRouteResolver/ToolExecutor
- Server-side MCP response builder changes

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| Phase 1 | Preparation — Establish canonical UTC format | Pending | — | — | |
| Phase 2 | Core Logic — Propagate fetched_at through DTOs and models | Pending | — | — | |
| Phase 3 | Core Logic — Make ingester and document manager strict | Pending | — | — | |
| Phase 4 | Core Logic — Fix etag manager | Pending | — | — | |
| Phase 5 | Core Logic — Update store protocol and implementation | Pending | — | — | |
| Phase 6 | Schema cleanup | Pending | — | — | |
| Phase 7 | Test and fixture updates | Pending | — | — | |
| Phase 8 | Verification | Pending | — | — | |

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
- **Requirement ID**: REQ-001, REQ-002, REQ-003, REQ-004, REQ-005, REQ-006, REQ-007, REQ-008, REQ-009, REQ-010
- **Source issue**: `issues/20260828_01_remove-fetched-at-null-fill-and-mandatory-contract.md`
- **Source requirement**: `requires/20260819-144406_require.md` ("Replace permissive RAG payload handling with strict crawl and chunk contracts")
- **Source plan**: `plans/20260828-150000_plan.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260828-150614
- **Related target files**: `scripts/rag/ingestion/crawler.py`, `scripts/rag/models_data.py`, `scripts/rag/ingestion/pipeline_utils.py`, `scripts/rag/ingestion/chunk_splitter.py`, `scripts/rag/ingestion/ingester.py`, `scripts/rag/ingestion/document_manager.py`, `scripts/rag/ingestion/etag_manager.py`, `scripts/db/store_protocols.py`, `scripts/db/store_impl.py`, `scripts/db/schema_sql.py`
