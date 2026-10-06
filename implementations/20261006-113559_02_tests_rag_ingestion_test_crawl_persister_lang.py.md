## Goal

Add unit and integration tests covering the local-file `auto` resolution path and the
`file://` + `auto` dispatch through `WebCrawler.crawl()`. Implements `REQ-003` (and exercises
the behavior required by `REQ-001`).

## Scope

Create `tests/rag/ingestion/test_crawl_persister_lang.py`.

Out of scope: modifying existing test files' assertions. Existing tests must still pass
unchanged (`REQ-005`).

## Assumptions

- `CrawlPersister(config)` takes a config dict exposing `rag_src_dir`; the written JSON lands
  under that directory as `yyyymmddhhmmss-{slug}.json`.
- `WebCrawler.crawl()` dispatches `file://` targets to `WebCrawler.crawl_file(path, lang)`.
- Detection uses `crawler_utils.detect_lang()`: deterministic results require ≥ 100 characters;
  CJK ratio ≥ threshold → `ja`, else `en`, short/inconclusive → `en`.

## Design decisions

- New standalone test module placed under `tests/rag/ingestion/`, mirroring the layout and
  fixture patterns of the existing `test_ingestion_freshness.py` / `test_crawler_integration.py`
  so `CrawlPersister` and `WebCrawler` are constructed the same way.
- Use `tmp_path` fixtures for input files and assert on both the returned int and the
  produced JSON's `lang` field.

## Alternatives considered

- N/A: single target file; no cross-file alternatives.

## Implementation

### Target file

`tests/rag/ingestion/test_crawl_persister_lang.py` (new)

### Procedure

1. Create `tests/rag/ingestion/test_crawl_persister_lang.py`.
2. Add unit tests for `CrawlPersister.save()` / `WebCrawler.crawl_file()` with `auto`:
   - Japanese (CJK-dominant, ≥ 100 chars) → returns `1` and writes a JSON with `lang == "ja"`.
   - English (≥ 100 chars) → returns `1` and writes a JSON with `lang == "en"`.
   - Short (< 100 chars) → returns `1` and writes a JSON with `lang == "en"` (inconclusive fallback).
   - Unsupported value (e.g. `"fr"`) → returns `0`, writes nothing, and logs a warning.
3. Add an integration test: `WebCrawler.crawl()` with a `file://` target carrying `auto` in
   the targets list produces exactly one crawl JSON whose `lang` is resolved to a value in
   `{en, ja}`.
4. Build input files under `tmp_path`; locate the written JSON by listing `rag_src_dir` and
   reading its `lang` field.

### Method

- Inspect `test_ingestion_freshness.py` and `test_crawler_integration.py` to learn how they
  construct `CrawlPersister` / `WebCrawler`, set up `rag_src_dir`, and find the written JSON.
  Mirror those patterns rather than inventing new helpers.
- For the `file://` + `auto` test, build the targets tuple as
  `(f"file://{tmp_path.resolve()}", "auto")` and call `WebCrawler.crawl()`, then assert that
  exactly one JSON exists and its `lang` is in `{en, ja}`.
- Craft the JA/EN fixtures to be ≥ 100 characters so `detect_lang()` is deterministic.

### Details

- `detect_lang()` needs ≥ 100 characters for a deterministic result; keep the JA and EN
  fixtures at or above that length.
- The unsupported-value case exercises the pre-existing rejection branch (unchanged code):
  confirm `0` is returned and no JSON is written. This doubles as a regression guard for the
  part of `save()` this procedure does not modify.
- Reference behavior: `REQ-001` (the resolved `ja`/`en`/`en`/`0` outcomes) and `REQ-003`
  (coverage of the local-file `auto` path and the `file://` + `auto` dispatch).

## Compatibility considerations

- Does not modify any existing test; `test_ingestion_freshness.py` must still pass unchanged
  (`REQ-005`).

## Security considerations

- Tests use temp files only. No network access, secrets, subprocess, or deserialization of
  untrusted data beyond asserting on locally written JSON.

## Rollback considerations

- Delete the new test file to revert. `deploy.sh` rsyncs the tree; not applicable.

## Validation plan

- `uv run pytest tests/rag/ingestion/test_crawl_persister_lang.py -v` — expect `ja`/`en`/`en`/
  `0`+warning and exactly one JSON with a resolved `lang` for `file://` + `auto`.
- `uv run pytest tests/rag` (full RAG suite).
- `uv run ruff check scripts/ tests/rag/ingestion/test_crawl_persister_lang.py`,
  `uv run mypy`, `PYTHONPATH=scripts uv run lint-imports`,
  `uv run bandit -r scripts/rag/ingestion/ -c pyproject.toml`.

## Completion criteria

- All new tests pass.
- `test_ingestion_freshness.py` passes unchanged.
- Static checks (ruff/mypy/lint-imports/bandit) report no new findings.

## Out of scope

Modifying existing test assertions; changing detection thresholds or supported languages.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | create new test module |
| 2 | Add or update tests per Validation plan | Pending | — | — | `REQ-001`, `REQ-003` |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | ruff/mypy/lint-imports/bandit/pytest |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Pending | — | — | N/A: doc handled by separate row |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| — | — | N/A: no blockers | N/A |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| — | — | — | — | — | — |

## Traceability
- **Workflow phase**: plan-to-implementation-procedure
- **Requirement ID**: `REQ-003`
- **Source issue**: `issues/20261005-102245_rag001_crawl_file-does-not-resolve-lang-auto.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261005-214953_plan.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261006-113559
- **Related target files**: `tests/rag/ingestion/test_crawl_persister_lang.py`
