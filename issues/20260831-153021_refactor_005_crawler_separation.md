# Refactor crawler.py — separation of concerns

## Priority
Medium

## Summary
Split `scripts/rag/ingestion/crawler.py`'s `WebCrawler` class (511 lines) into focused modules to clarify the boundaries between BFS crawl orchestration, HTTP fetching, HTML content extraction, language resolution, and file persistence — currently combined in one class.

## Background
`WebCrawler` is the first stage of the RAG ingestion pipeline (`crawler.py` → `chunk_splitter.py` → `ingester.py`). It already delegates pure-function helpers (`detect_lang`, `extract_text`, `normalize_url`, `same_origin`, `url_to_slug`, etc.) to `rag/ingestion/crawler_utils.py`, but the stateful crawl logic itself — HTTP fetching, HTML parsing, BFS queue management, and JSON persistence — remains in one class. Similar splits were already completed for `scripts/agent/orchestrator.py` (`issues/done/20260829-080923_refactor_001_orchestrator_separation.md`), `scripts/agent/repl.py` (`issues/done/20260829-080924_refactor_002_repl_separation.md`), and `scripts/rag/ingestion/ingester.py` — the pipeline stage immediately downstream of this one (`issues/done/20260829-080925_refactor_003_ingester_separation.md`, 890 lines split across eight extracted concerns).

## Problem
`WebCrawler` exceeds the 400-line threshold defined in `skills/DESIGN.md` File Split Rule trigger condition (511 lines) and combines at least seven distinct concerns in one class:

1. **Configuration/lifecycle** — `__init__` — loads and holds crawl-delay, depth, concurrency, DB, and target-URL settings from `crawler.toml`
2. **BFS crawl orchestration** — `crawl`, `crawl_site`, `_drain_queue_to_tasks`, `_process_crawl_url_async` — queue-driven breadth-first traversal with `asyncio.Semaphore`-bounded concurrency
3. **HTTP fetching** — `_fetch_html_async`, `_get_conditional_headers` — retrying GET requests with exponential backoff and ETag/Last-Modified conditional headers
4. **HTML content extraction** — `_extract_content`, `_extract_code_blocks`, `_fetch_and_extract_async` — title/body/code-block extraction from parsed HTML
5. **Link discovery** — `_enqueue_links`, `_should_enqueue_link` — outbound link parsing with nofollow/cross-origin filtering
6. **Language resolution** — `_resolve_lang` — CJK-ratio-based language detection with fallback
7. **File persistence** — `_save_crawl_file`, `_make_crawl_filepath`, `crawl_file` (local-file ingestion path) — JSON payload construction and write to `rag-src/`

`_process_crawl_url_async` alone threads together conditional-header lookup, fetch, extraction, language resolution, persistence, and link enqueueing in a single method body, making it hard to test any one step (e.g. conditional-header behavior, or extraction) without exercising the full per-URL pipeline. The corresponding tests are already split across four files (`test_crawler_retry_boundary.py`, `test_crawler_targets_file.py`, `test_crawler_integration.py`, plus crawler-relevant cases in `test_ingestion_freshness.py`), mirroring the concerns above without the production code reflecting the same boundaries.

## Reason for Change
- `_process_crawl_url_async`'s per-URL pipeline makes it difficult to unit-test HTTP fetching, HTML extraction, or persistence independently — most existing tests must instantiate the full `WebCrawler` and mock at the `httpx.AsyncClient` boundary.
- The downstream pipeline stage (`ingester.py`) already underwent the same separation; leaving `crawler.py` unsplit is an inconsistency in the pipeline's structural conventions.
- Extracting HTTP fetching and HTML extraction as independent units would make it easier to add per-concern tests (e.g. conditional-header edge cases) without touching BFS queue logic.

## Implementation Intent
Extract each concern into its own class/module, following the constructor-injection / delegation pattern already used for the `orchestrator.py` and `ingester.py` splits. Suggested (not mandatory) grouping, left for the implementation planning phase to finalize:
- **Crawl orchestrator** — owns the BFS queue/semaphore loop (`crawl`, `crawl_site`, `_drain_queue_to_tasks`, `_process_crawl_url_async`)
- **HTTP fetcher** — owns retrying fetch and conditional-header lookup (`_fetch_html_async`, `_get_conditional_headers`)
- **Content extractor** — owns HTML parsing (`_extract_content`, `_extract_code_blocks`, `_fetch_and_extract_async`)
- **Link discovery** — owns outbound link filtering (`_enqueue_links`, `_should_enqueue_link`)
- **Language resolver** — owns `_resolve_lang`
- **Crawl file persister** — owns JSON payload construction/write (`_save_crawl_file`, `_make_crawl_filepath`, `crawl_file`)

`WebCrawler` should become a thin composition facade wiring these components together, preserving its public interface (`crawl`, `crawl_site`, `crawl_file`, `__init__` config-loading behavior) and the CLI entry point (`main()`) unchanged.

## Target Files or Areas
- `scripts/rag/ingestion/crawler.py` — primary target
- `scripts/rag/ingestion/crawler_utils.py` — existing pure-function helpers already extracted; referenced, not modified
- `scripts/rag/ingestion/pipeline_utils.py` — referenced by `CrawlJsonPayload`
- `scripts/rag/utils.py` — referenced by `MIN_TEXT_LENGTH_FOR_DETECTION`, `validate_url`
- `db/helper.py` — referenced by `SQLiteHelper`
- `shared/config_loader.py` — referenced by `ConfigLoader`
- `tests/rag/ingestion/test_crawler_retry_boundary.py`, `test_crawler_targets_file.py`, `test_crawler_integration.py`, and the crawler-relevant cases in `test_ingestion_freshness.py` — to be reorganized alongside the split
- Documentation: Unknown — check `docs/00_index.md`'s task-scope mapping (`docs/03_rag_02_02_ingestion_pipeline-crawler.md` is the likely candidate) against whichever files actually change before editing

## Required Changes
- Extract the six concerns listed above into separate modules/classes.
- Reduce `WebCrawler` to a thin composition facade delegating to the extracted components.
- Preserve `WebCrawler`'s public interface exactly: `__init__(config: dict | None = None)`, `crawl(targets)`, `crawl_site(start_url, hint_lang)`, `crawl_file(path, lang)`.
- Preserve the CLI entry point (`main()`) and its argument parsing behavior unchanged.
- Reorganize the four existing crawler test files to mirror the new module boundaries where it clarifies ownership, without losing existing coverage.

## Constraints
- Do not change any observable crawl behavior: BFS traversal order, concurrency limits, retry/backoff timing, conditional-header (ETag/Last-Modified) handling, or the JSON payload schema written to `rag-src/`.
- Do not change any existing log message string.
- Do not change `crawler.toml`'s config keys or their meaning.
- `WebCrawler(config=...)` must remain constructible the same way tests currently use it (direct dict override, no config file required).

## Acceptance Criteria
- Each resulting module/class addresses exactly one of the six concerns listed under Implementation Intent.
- `WebCrawler`'s public methods (`crawl`, `crawl_site`, `crawl_file`, `__init__`) retain identical signatures and behavior after the refactor.
- The CLI entry point (`python crawler.py [--url ...] [--lang ...] [--targets-file ...]`) behaves identically.
- All pre-existing tests in the four crawler-related test files pass unchanged in outcome (reorganized as needed).
- `ruff`, `mypy`, and `bandit` are clean on all new/modified files.
- A full `uv run pytest` run shows no new failures compared to the pre-change baseline.

## Testing Expectations
- Run the four existing crawler-related test files (reorganized to match the new module layout) and confirm no behavioral regression.
- Run the full `uv run pytest` suite once after implementation and compare against the pre-change baseline for new failures.
- Apply the standard validation sequence in `rules/toolchain.md` (format → lint → type → arch → security → test → coverage).

## Documentation Impact
Unknown whether `docs/03_rag_02_02_ingestion_pipeline-crawler.md` or other `docs/03_rag_*` files reference `WebCrawler`'s internal method names or class structure directly — a quick check found no such references at issue-creation time, but re-verify against `docs/00_index.md`'s "Document References by Task" table for whichever files this issue's implementation actually touches, and update only the matched row(s). Do not proactively write new documentation beyond what routing directs.

## Out of Scope
- Changing the BFS crawl strategy, concurrency model, or retry/backoff algorithm.
- Changing the `CrawlJsonPayload` schema or the `rag-src/` output file naming convention.
- Adding new crawler features (e.g. sitemap support, robots.txt handling).
- Modifying `crawler_utils.py`'s existing pure-function helpers.
- Modifying the downstream pipeline stages (`chunk_splitter.py`, `ingester.py`).
- Performance optimization of the fetch/extraction pipeline.

## Dependencies
N/A: none

## Unresolved Questions
- Exact module names and file layout for the six extracted concerns are left to the `issue-to-plan` / `plan-to-implementation-procedure` phases.
- Whether the local-file ingestion path (`crawl_file`) belongs with the "crawl orchestrator" or the "file persister" concern is left to the implementer to decide and document in the resulting plan — it currently mixes both language resolution and persistence.

## AI Implementation Instruction
- Do not change observable behavior: preserve BFS traversal order, concurrency limits, retry/backoff timing, conditional-header handling, log message text, and the JSON payload schema exactly.
- Extract the six concerns into separate modules/classes; you may follow the composition/delegation pattern used in `scripts/agent/orchestrator.py`'s and `scripts/rag/ingestion/ingester.py`'s splits as a reference, but it is not mandatory.
- Verify `WebCrawler`'s public interface and the CLI entry point (`main()`) work identically after the change.
- Do not touch out-of-scope items (crawl strategy changes, payload schema changes, new features, downstream pipeline stages).
- If a required design decision (module layout, where `crawl_file` belongs) is unclear, stop and record it under Unresolved Questions rather than guessing.
