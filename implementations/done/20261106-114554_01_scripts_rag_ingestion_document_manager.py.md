## Goal

Remove the pre-commit etag write from `DocumentManager.handle_existing_document`'s HTTP replace branch so no freshness UPDATE can commit before the chunk replacement transaction (REQ-001: no DB write on the replace branch).

## Scope
**Release unit**: etag-atomic-fix

## Assumptions

- No existing test asserts the pre-commit etag advancement (re-verified this cycle: `rg '_update_etag'` matches only `document_manager.py` in source).
- Freshness resolution moves to the commit insert path (sibling procedures seq 02 and 03); this file only loses the write, it does not gain one.

## Design decisions

- Delete the call, the method, and the import outright rather than moving the UPDATE into the transaction: the replace branch's insert already carries freshness and would overwrite a moved UPDATE — the guard only becomes real at the insert (Plan Design).
- Keep `handle_existing_document`'s `fetched_at` parameter even though it becomes unused: removing it cascades into `ingester.py` and mock-based tests, which the issue does not require; ruff's ARG rule is not selected, so the unused parameter is lint-clean.

## Alternatives considered

N/A: deletion-only row; the rejected move-the-UPDATE alternative is recorded in the Plan's Design section.

## Implementation
### Target file
`scripts/rag/ingestion/document_manager.py`
### Procedure

- Delete the `self._update_etag(...)` call (document_manager.py:101) from the replace branch of `handle_existing_document`.
- Delete the `_update_etag` method (document_manager.py:104-112).
- Delete the now-unused `ETagManager` import (document_manager.py:13).

### Method

- Deletion only; no replacement logic in this file. `handle_existing_document`'s return contract (`skip`/`replace`) is unchanged.

### Details

- After REQ-001, `ETagManager.update` has no production caller; it stays per the Plan Design (removal deferred to `rules/coding.md` Deprecation policy with a zero-caller `rg` re-check in the next plan touching `etag_manager.py`).
- `DocumentStore.get_or_create`'s pass-through of `fetched_at` stays unchanged.

## Compatibility considerations

- Co-target: `document_manager.py` is also targeted by plan `20261106-104959_raging012_ingest-callback-narrow-catch.md` (overlap tool) — verify the two designs do not contradict each other before/while implementing.

## Security considerations

N/A: removal of a DB write path; no input handling or credential change.

## Rollback considerations

N/A: revert the single commit (the full fix spans sibling procedures 02-04; revert the whole change set together).

## Validation plan

| Check | Command | Expected |
|---|---|---|
| Ingestion regression | `uv run pytest tests/rag/ingestion` | All green; no pre-commit etag write anywhere |
| Static gates | `uv run ruff check scripts/`, `uv run mypy --no-namespace-packages scripts/ tests/eventbus tools`, `PYTHONPATH=scripts uv run lint-imports`, `uv run bandit -r scripts/ -c pyproject.toml -ll` | Clean, no new findings |
| Coverage | `uv run coverage run -m pytest tests/` → `uv run coverage xml` → `uv run diff-cover coverage.xml --compare-branch=master` | ≥ 90% on changed lines |

## Completion criteria

- AC-1: after a failed re-ingestion the `documents` row still holds previous freshness and a later run re-processes the URL.
- AC-2: no freshness write occurs outside the commit transaction.
- AC-6: `uv run pytest tests/rag/ingestion` passes; diff-cover ≥ 90%.

## Out of Scope

- Removing the now-unused `fetched_at` parameter from `handle_existing_document` / `get_or_create`.
- Deleting `ETagManager.update` (deferred per Deprecation policy) and its log-string wording (issue `20261106-073538_raging008_etagmanager-stale-log-error.md`).
- `http_fetcher.py` conditional-request logic; retry/re-queue design (issue `20261106-073538_raging005_retry-dir-no-consumer.md`).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 2026-11-06 | 2026-11-06 | Execute after sibling procedure 02/03 land and Phase 1 tests exist (RED first) |
| 2 | Add or update tests per Validation plan | Completed | 2026-11-06 | 2026-11-06 | Tests live in sibling procedure `implementations/20261106-114554_04_tests_rag_ingestion_test_ingestion_freshness.py.md` Tests in sibling procedure 04: TestFreshnessAtomicity pins no-write-on-replace-branch; rg '_update_etag' confirmed no test asserted the removed method |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 2026-11-06 | 2026-11-06 | Includes diff-cover ≥ 90% End-of-unit gate: ingestion suite 200/200; ruff/mypy/lint-imports/bandit/mock-patch/docstrings/module-size clean; full suite 11772 passed 9 skipped (deterministic order); diff-cover 100% (etag_manager.py, transaction_commit.py) |

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
- **Requirement ID**: `REQ-001` (remove the pre-commit etag write on the HTTP replace branch)
- **Source issue**: `issues/20261106-073538_raging002_etag-updated-before-reingestion.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261106-094942_raging002_etag-updated-before-reingestion.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261106-114554
- **Related target files**: `scripts/rag/ingestion/document_manager.py`