## Goal

Stop treating two absent HTTP validators as "unchanged" in `DocumentManager.handle_existing_document`: express "validators prove unchanged only when present" once as a shared helper used by the HTTP branch and `_is_file_unchanged`, and add the HTTP-branch matrix tests (`REQ-001`: `None`/`None` re-ingests; `REQ-002`: equal non-null validators still skip; `REQ-003`: one shared absence helper, `file://` outcomes unchanged; `REQ-004`: force, no-stored-row, and no-freshness-write behavior unchanged).

## Scope
**Release unit**: N/A: not part of a release unit

- In scope: `scripts/rag/ingestion/document_manager.py` (the helper, the HTTP branch, `_is_file_unchanged`) and the companion test file `tests/rag/ingestion/test_ingestion_freshness.py`.
- Out of scope: crawler fetch and 304 behavior, `ETagManager`, a content-hash fallback (UNK-01), the `file://` etag-only rule itself, the docs sentence (document `03`), and the fallout test in `tests/rag/ingestion/test_ingester.py` (document `04`).
- Plan: `plans/20261108-165741_ragrev010_pages-without-validators-skipped.md` (Plan steps 1 and 2).

## Assumptions

- Re-verified at generation time (by symbol): the HTTP branch of `handle_existing_document` compares `stored["etag"] == etag and stored["last_modified"] == last_modified` with no absence check, so `None`/`None` skips; `_is_file_unchanged` returns `False` when either etag is `None` and otherwise compares etags only; the sole production caller is `DocumentPersistence.get_or_create`, which maps `skip` to "no work" and `replace` to delete-then-insert.
- `ETagManager` keeps stored validators when the incoming pair is both `None` (`resolve_incoming`), so a stored-present/incoming-absent pair already differs under plain equality and re-ingests.
- Companion test file: `tests/rag/ingestion/test_ingestion_freshness.py` is named in `Related Tests` of this row only and needs no design decision beyond the Plan's helper, so it is a companion here and gets no document of its own. It already holds `_make_freshness_db`, `_seed_document`, and `TestIsFileUnchanged`; the existing HTTP calls in `TestFreshnessAtomicity` use non-null values and stay unmodified.
- Overlap: `tests/rag/ingestion/test_ingestion_freshness.py` is also a target of `plans/20261108-170725_ragrev016_stale-recrawl-replaces-content.md`; compatible (this adds a new test class; ragrev016 adds stale-payload cases elsewhere in the file). Locate code by symbol name, not line number.
- Test impact outside this row: `tests/rag/ingestion/test_ingester.py::TestIngestUrlGroup::test_skips_already_registered_url` ingests a default `_ChunkSpec` (both validators `None`) twice and relies on the old skip; it is handled by document `04`. No other test in `tests/rag` ingests the same validator-less URL twice without `force` (checked by search of the `ingest_url_group`/`RagIngester` users); the full `tests/rag` run in validation confirms.

## Design decisions

- One helper, two rules: add a module-private static method `_has_validator` (new), taking `*validators: str | None` and returning `bool`, returning `True` when any value is not `None`. The HTTP branch asks it for the stored pair and the incoming pair; `_is_file_unchanged` asks it for each single etag. The two branches keep their own comparison (pair equality versus etag-only).
- Absence means unknown: skip only when both pairs carry a validator and are equal; any other case falls through to the existing replace return.

## Alternatives considered

- Content-hash fallback or a schema column for validator-less pages: rejected (no storage; reusing `etag` would be replayed as `If-None-Match`); see Plan UNK-01.
- Inline `is None` checks in each branch: rejected; `REQ-003` requires one shared rule.

## Implementation
### Target file
`scripts/rag/ingestion/document_manager.py`

### Procedure
1. Apply the companion test procedure below first and run `uv run pytest tests/rag/ingestion/test_ingestion_freshness.py -q`: the `None`/`None` and one-sided-absent cases must fail on the unmodified code while the equal non-null and force cases pass.
2. Add the static method `_has_validator` (new) to `DocumentManager`, next to `_is_file_unchanged`.
3. In the HTTP branch, replace the bare equality with: when `_has_validator` (new) holds for the stored etag and last_modified pair and for the incoming pair and both fields are equal, return `(existing_doc_id, True, False)`; otherwise fall through to the existing replace return.
4. In `_is_file_unchanged`, replace `existing_etag is None or new_etag is None` with a check that `_has_validator` (new) is false for either etag (call it through the class, since it is a static method); keep the etag-only comparison and the unused-argument signature.
5. Update the `handle_existing_document` docstring's return list so the "unchanged" bullet says validators must be present and equal.

### Method
- Edit by symbol; leave the `force` branch, the `file://` branch body, the `stored is None` returns, and the "No freshness write here" comment untouched.
- Keep both functions at or below cyclomatic complexity B (`handle_existing_document` was B (8)); the helper holds the only new branching.

### Details
- Do not log in the new path: re-ingesting validator-less pages every run is the intended default, and a per-page log line would be noise (a count is the owner's query in UNK-02).
- Run `uv run python tools/check_module_size.py` after the edit; the module is small, so a baseline entry is not expected.

### Companion test files
- `tests/rag/ingestion/test_ingestion_freshness.py`
  - Procedure: add `TestHandleExistingDocumentHttpValidators` (new) using `_make_freshness_db`, `_seed_document` (with `etag`/`last_modified` set per case), and the real `DocumentManager`, calling `handle_existing_document("https://example.com/doc", doc_id, False, etag, last_modified, "2024-06-20T00:00:00Z", lambda u: False)`: parametrize (stored, incoming, expected `(skip, replace)`) over `(None, None)` vs `(None, None)` -> `(False, True)`; `("e", "lm")` vs `("e", "lm")` -> `(True, False)`; `("e", None)` vs `("e", None)` -> `(True, False)`; `(None, "lm")` vs `(None, "lm")` -> `(True, False)`; differing etag, differing last_modified, `("e", "lm")` vs `(None, None)`, `(None, None)` vs `("e", "lm")`, and `("e", None)` vs `("e", "lm")` -> `(False, True)`; plus `force=True` with `None`/`None` -> `(False, True)`, and a missing stored row (a `doc_id` not in `documents`) -> `(doc_id, False, False)`. Assert `_freshness_row(conn)` is unchanged after each call (no freshness write). Add one test that the new validator-presence helper returns `False` for `(None, None)` and `True` for `(None, "x")`, and that `_is_file_unchanged` still returns `False` for a `None` etag on either side and `True` for equal etags (the existing `TestIsFileUnchanged` cases stay unmodified and cover the rest).
  - Validation: `uv run pytest tests/rag/ingestion/test_ingestion_freshness.py -q`; the new `None`/`None` case fails on HEAD and passes after step 3.

## Compatibility considerations

- Behavior change by design: an existing HTTP page whose stored or incoming validators are both absent is now re-chunked and re-embedded on every crawl run (Plan Assumptions, UNK-02 for the cost count). Pages with equal non-null validators still skip.
- `handle_existing_document` keeps its signature and return meaning; `_is_file_unchanged` keeps its signature and `file://` outcomes. `_has_validator` (new) is private and has no other caller.

## Security considerations

N/A: no input parsing, trust boundary, or persistence change; the helper only inspects values already read from the `documents` row and the chunk payload.

## Rollback considerations

- Revert the commit; no persisted state changes. Re-ingested validator-less pages stay replaced (content is identical or newer), so no data repair is needed.

## Validation plan

- `uv run pytest tests/rag/ingestion/test_ingestion_freshness.py -q`, then `uv run pytest tests/rag/ingestion -q`, then `uv run pytest tests/rag -q` (after document `04` is applied).
- `uv run ruff format` and `uv run ruff check` on both files; `uv run mypy`; `PYTHONPATH=scripts uv run lint-imports`; `uv run python tools/check_module_size.py`; `uv run python tools/check_mock_patch_targets.py`.
- Coverage on changed lines at 90 percent (`diff-cover`), per the Plan Design section.

## Completion criteria

- A stored or incoming `(None, None)` pair on an existing HTTP document yields `(skip=False, replace=True)`; equal pairs with at least one non-null validator yield `(True, False)`; force, no-stored-row, and `file://` outcomes are unchanged.
- `_has_validator` (new) is the only absence rule used by both branches; no new `None` comparison remains inline in either.
- The new matrix tests pass, the new `None`/`None` case demonstrably failed before the code change, and the existing freshness tests pass unmodified.

## Out of Scope

- A hash or any other fallback signal for validator-less pages, schema changes, `ETagManager` changes, crawler and conditional-request changes, and the docs and `test_ingester.py` edits (documents `03` and `04`).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Add the HTTP-branch matrix tests and confirm the absent-validator cases fail on HEAD | Pending | — | — | |
| 2 | Add `_has_validator` (new), rewire the HTTP branch and `_is_file_unchanged`, update the docstring | Pending | — | — | |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |

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
- **Requirement ID**: `REQ-001` (absent pair re-ingests), `REQ-002` (equal non-null still skips), `REQ-003` (one shared helper), `REQ-004` (force and no-write unchanged)
- **Source issue**: issues/20261108-131124_ragrev010_pages-without-validators-skipped.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261108-165741_ragrev010_pages-without-validators-skipped.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261109-142759
- **Related target files**: `scripts/rag/ingestion/document_manager.py`, `tests/rag/ingestion/test_ingestion_freshness.py`
