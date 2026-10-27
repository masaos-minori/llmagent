# Implementation Procedure: Add `import sqlite3` and widen the `_process_url_groups` except tuple to include `sqlite3.Error`

## Goal
Make the ingestion batch honor its documented "log exceptions without stopping" contract for the whole SQLite error hierarchy: a `sqlite3.Error` on one URL group is logged and recorded as an unexpected failure, remaining groups still process, and `check_consistency` still runs (REQ-001, REQ-002).

## Scope
- One `import sqlite3` addition and one except-tuple extension in `_process_url_groups`. Logging call, result recording, loop structure, and `ingest_url_group` itself are untouched.

## Assumptions
- `sqlite3.Error` and its subclasses (`OperationalError`, `IntegrityError`, `DatabaseError`, `ProgrammingError`, `DataError`, `InternalError`, `NotSupportedError`) derive from `Exception`, not from `OSError`/`RuntimeError`/`ValueError` (stdlib hierarchy, Plan-verified).
- `ChunkFormatError` subclasses `ValueError` (verified `scripts/rag/exceptions.py` L27), so its current catch path is unaffected by the added category (Plan Reference Files).
- A `sqlite3.Error` reaching the loop means the group's transaction was already rolled back by `SQLiteHelper._begin_transaction` (verified rollback-on-any-exception at `scripts/db/helper.py` L219-220), so continuing introduces no partial writes (Plan Assumptions).
- Overlap: `docs/21_rag/rag_05_04-error-handling-reference.md` is also targeted by the rag003 Plan procedures (implementations/20261027-154425_26_*), which rename the `rag_service_url` occurrence in the RagPipeline table; this procedure adds a row to the RagIngester table. Disjoint tables; whichever implements second rebases (Plan Dependencies).

## Design decisions
- Catch the base class `sqlite3.Error` rather than enumerating subclasses as `check_consistency` does (which also catches `ValueError` for data-shape errors, a different context): the batch loop wants the whole hierarchy, and the base class is bounded and intent-revealing (Plan Design/Assumptions).
- Widen only at the loop boundary: `ingest_url_group` keeps propagating DB errors to direct callers, preserving the TestAtomicity contract and fail-fast per-group semantics (REQ-003).

## Alternatives considered
- Enumerate `OperationalError`/`IntegrityError`/`DatabaseError` like `document_manager.check_consistency` (verified catch at L136) — rejected: the batch loop wants the entire hierarchy, and enumeration risks missing a subclass.
- Catch `Exception` — forbidden by the Issue's Constraints and rejected: it would swallow programming errors (Plan Risks).

## Implementation
### Target file
`scripts/rag/ingestion/ingester.py`
### Procedure
1. Add `import sqlite3` to the module imports of `scripts/rag/ingestion/ingester.py` (verified: the module currently has no `sqlite3` import).
2. Extend the except tuple `except (OSError, RuntimeError, ValueError):` (verified at L377) to `except (OSError, RuntimeError, ValueError, sqlite3.Error):`.
3. Keep the body unchanged: `logger.exception("ingest_url_group failed: %s", url)` and `results.append(IngestUrlResult.unexpected_failure(url))` (verified at L378-379).
4. Confirm no other catch site in the module is widened (AC-1). The loop docstring at L370 ("log exceptions without stopping") already states the now-true contract and needs no change.
### Method
Two-line change: one import, one tuple extension. No new helper, no new result type.
### Details
- Downstream consumers of `ingest_all` results (counts, diagnostics, the `check_consistency(embed_failed=...)` aggregation verified at L169) see DB failures as the existing `unexpected_failure` result kind — no new result type (Plan Design).
- `ingest_all` reaches `check_consistency` because the loop no longer aborts on DB errors (REQ-002).

## Compatibility considerations
- No config, service, or deployment change: the existing `rag_ingester` service restarts through normal deploy (Plan Implementation steps, Phase 4).

## Security considerations
- The widened catch stays bounded to the `sqlite3.Error` hierarchy — narrower than `Exception` — so non-DB programming errors (`TypeError`, `AttributeError`) still fail fast (Plan Risks). `logger.exception` preserves the full traceback; failures are recorded as results, never silent.

## Rollback considerations
- Single commit adding the import, the widened tuple, tests, and the doc row; rollback is `git revert`. No config, schema, or deployed-state change.

## Validation plan
- `uv run pytest tests/rag/ingestion/test_rag_ingester.py` — continuation and boundary tests (procedure _02) pass; all pre-existing tests pass unmodified, including `TestAtomicity::test_database_failure_during_replacement` (AC-3).
- `uv run ruff check scripts/`, `uv run mypy --no-namespace-packages scripts/`, `uv run bandit -r scripts/ -c pyproject.toml -ll`, `PYTHONPATH=scripts uv run lint-imports` — clean; no blind-except findings (AC-1).
- `uv run pytest tests/` — full suite green (AC-5).
- Diff coverage: `uv run coverage run -m pytest tests/ && uv run coverage xml && uv run diff-cover coverage.xml --compare-branch=master --fail-under=90` — new except branch covered.

## Completion criteria
- The except tuple is `(OSError, RuntimeError, ValueError, sqlite3.Error)`; `import sqlite3` present; no other catch widened; continuation test green; TestAtomicity propagation test green unmodified.

## Out of Scope
- Broadening the catch to bare `Exception`/`BaseException` (Issue Constraint).
- Changing transaction boundaries or rollback behavior (`SQLiteHelper.begin_immediate` stays as-is).
- Changing `ingest_url_group`'s own exception semantics for direct callers.
- The `int(cfg[...])` coercion style in `crawler.py`, `chunk_splitter.py`, `db/config.py`, `db/maintenance.py`.
- httpx/transport error handling — verified contained inside `ChunkFactory.prepare` and converted to `failed_paths` (Issue Unresolved Question, answered: no change).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | |
| 2 | Add or update tests per Validation plan | Pending | — | — | |
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
- **Requirement ID**: REQ-001, REQ-002, REQ-003
- **Source issue**: issues/20261027-074526_rag004_ingester-sqlite3-error-aborts-batch.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/done/20261027-111107_rag004_ingester-sqlite3-error-aborts-batch.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261027-165951
- **Related target files**: scripts/rag/ingestion/ingester.py
