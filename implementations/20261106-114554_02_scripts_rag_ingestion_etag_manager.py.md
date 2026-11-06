## Goal

Give `ETagManager` a `resolve_incoming` (new) guarded value-selection API with the existing staleness/parse/exception semantics, and make `update()` delegate to the same shared core with unchanged observable behavior (REQ-002: shared guard logic).

## Scope
**Release unit**: etag-atomic-fix

## Assumptions

- `update()`'s guard contract stays byte-identical: `ValueError` on empty `new_fetched_at` (etag_manager.py:42-43), both-`None` early return (etag_manager.py:44-45), stale skip with the current `logger.info` message (etag_manager.py:46-53), `InvalidIncomingTimestampError` / `InvalidStoredTimestampError` from `_is_stale_update` (etag_manager.py:57-90).
- `test_ingester_etag_guard.py` is characterization coverage: it stays unchanged and green.

## Design decisions

- `resolve_incoming` (new), signature `(etag, last_modified, new_fetched_at) -> tuple[str | None, str | None, str]`, performs the same guard decision but returns the resolved (incoming vs. stored) values instead of writing; the caller persists them.
- Extract the guard decision (validation, both-`None` check, stored-row fetch, staleness/parse via `_is_stale_update`) into one private core shared by `update()` and `resolve_incoming` (new) so the two paths cannot diverge.

## Alternatives considered

- Duplicate the guard rules inside the commit path: rejected — silent divergence between `update()` and the insert path (Plan Risks).

## Implementation
### Target file
`scripts/rag/ingestion/etag_manager.py`
### Procedure

- Add `resolve_incoming` (new) to `ETagManager` with the signature above; raise the same exceptions as `update()` for empty `new_fetched_at` and invalid stored/incoming timestamps.
- Refactor `update()` (etag_manager.py:31) so its decision comes from the shared core; keep its `_update_with_freshness` + `_log_updated` write path and stale-skip log identical.

### Method

- `resolve_incoming` (new) semantics: no stored row or non-stale incoming → incoming values win; stale incoming or both-`None` incoming → stored `etag`/`last_modified`/`fetched_at` win (both-`None` with no stored row keeps incoming, matching today's early return).
- Minimal change only: guard rules, exceptions, and `update()`'s log behavior stay identical; no new exception types.

### Details

- Both classes currently raise on `new_fetched_at` validation before any DB access; keep that ordering in `resolve_incoming` (new) so the caller's transaction aborts cleanly (Plan Assumption).

## Compatibility considerations

- Co-target: `etag_manager.py` is also targeted by plan `20261106-103659_raging008_etagmanager-stale-log-error.md` (overlap tool) — that plan changes log-string wording only; verify designs do not contradict before/while implementing.
- After sibling procedure 01 lands, `update()` has no production caller but stays per the Plan Design (Deprecation policy defers removal).

## Security considerations

N/A: timestamp comparison logic only; no I/O or credential change.

## Rollback considerations

N/A: revert the single commit (revert together with sibling procedures 01/03/04).

## Validation plan

| Check | Command | Expected |
|---|---|---|
| Characterization | `uv run pytest tests/rag/ingestion/test_ingester_etag_guard.py -v` | Unchanged tests pass against the delegated `update()` |
| Unit (guard rules of `resolve_incoming` (new)) | `uv run pytest tests/rag/ingestion/test_ingestion_freshness.py -v` | Stale skip, both-`None` keep-stored, invalid-timestamp raises, no-stored-row keeps-incoming |
| Static gates | `uv run ruff check scripts/`, `uv run mypy --no-namespace-packages scripts/ tests/eventbus tools`, `PYTHONPATH=scripts uv run lint-imports`, `uv run bandit -r scripts/ -c pyproject.toml -ll` | Clean, no new findings |

## Completion criteria

- AC-4: `resolve_incoming` (new) guard rules match `update()`'s documented contract and are test-covered; `update()` observable behavior unchanged (`test_ingester_etag_guard.py` green, unchanged).
- AC-6: `uv run pytest tests/rag/ingestion` passes; diff-cover ≥ 90%.

## Out of Scope

- Log-string wording changes (plan `20261106-103659_raging008_etagmanager-stale-log-error.md`).
- Deleting `update()` (zero-caller removal deferred per `rules/coding.md` Deprecation policy).
- `docs/21_rag/rag_02_06_ingestion_pipeline-supporting-components.md` §4.9 stays semantically correct; update only if the documented API surface changes (Plan Documentation Impact).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | Sibling procedures 03/04 depend on this landing first |
| 2 | Add or update tests per Validation plan | Pending | — | — | `resolve_incoming` (new) unit tests live in sibling procedure `implementations/20261106-114554_04_tests_rag_ingestion_test_ingestion_freshness.py.md` |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | Includes diff-cover ≥ 90% |

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
- **Requirement ID**: `REQ-002` (shared guarded value selection in `ETagManager`)
- **Source issue**: `issues/20261106-073538_raging002_etag-updated-before-reingestion.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261106-094942_raging002_etag-updated-before-reingestion.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261106-114554
- **Related target files**: `scripts/rag/ingestion/etag_manager.py`
