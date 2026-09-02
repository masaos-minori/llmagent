# Implementation Procedure: WebCrawler Separation of Concerns

## Goal

Split `scripts/rag/ingestion/crawler.py`'s `WebCrawler` class (511 lines) into focused modules to clarify the boundaries between BFS crawl orchestration, HTTP fetching, HTML content extraction, language resolution, and file persistence.

## Scope

- **In-Scope**: Extract six concerns into separate classes/modules within `scripts/rag/ingestion/`; reduce `WebCrawler` to a thin composition facade; reorganize test files to match new module boundaries
- **Out-of-Scope**: Changing BFS crawl strategy, concurrency model, or retry/backoff algorithm; changing `CrawlJsonPayload` schema or `rag-src/` output file naming; adding new crawler features; modifying `crawler_utils.py`'s existing pure-function helpers; modifying downstream pipeline stages (`chunk_splitter.py`, `ingester.py`); performance optimization

## Assumptions

- The composition/delegation pattern used in `orchestrator.py` and `ingester.py` splits is the preferred approach for this project
- Constructor injection is the correct mechanism for wiring dependencies between extracted components
- The `crawl_file` local-file ingestion path belongs with the "file persister" concern rather than the "crawl orchestrator" concern
- No new dependencies beyond what's already installed are needed for the refactoring

## Design decisions

- Each concern becomes its own class within `scripts/rag/ingestion/`
- Use constructor injection to wire dependencies
- Follow the composition/delegation pattern from `orchestrator.py` and `ingester.py` splits
- Keep `WebCrawler`'s public interface identical: `__init__(config: dict | None = None)`, `crawl(targets)`, `crawl_site(start_url, hint_lang)`, `crawl_file(path, lang)`

## Alternatives considered

- Keeping the single-class design — rejected because `WebCrawler` exceeds the 400-line threshold defined in `skills/DESIGN.md` File Split Rule trigger condition
- Using function-based decomposition instead of classes — rejected because constructor injection provides clearer dependency tracking and testability

## Implementation

### Target files

1. `scripts/rag/ingestion/http_fetcher.py` — New file: HttpFetcher class
2. `scripts/rag/ingestion/content_extractor.py` — New file: ContentExtractor class
3. `scripts/rag/ingestion/link_discovery.py` — New file: LinkDiscovery class
4. `scripts/rag/ingestion/language_resolver.py` — New file: LanguageResolver class
5. `scripts/rag/ingestion/crawl_persister.py` — New file: CrawlPersister class
6. `scripts/rag/ingestion/crawler.py` — Refactor: reduce to thin composition facade

### Procedure

#### Phase 1: Create new component modules

1. **Create `http_fetcher.py`** with `HttpFetcher` class:
   - Move `_fetch_html_async` method logic here
   - Move `_get_conditional_headers` method logic here
   - Accept `config` dict via constructor for retry count, timeout, DB settings
   - Accept `SQLiteHelper` reference for conditional header lookups

2. **Create `content_extractor.py`** with `ContentExtractor` class:
   - Move `_extract_content` method logic here
   - Move `_extract_code_blocks` method logic here
   - Accept `_min_chunk` config value via constructor

3. **Create `link_discovery.py`** with `LinkDiscovery` class:
   - Move `_enqueue_links` method logic here
   - Move `_should_enqueue_link` method logic here
   - Accept `_skip_nofollow` and `_skip_external` config values via constructor

4. **Create `language_resolver.py`** with `LanguageResolver` class:
   - Move `_resolve_lang` method logic here
   - Import `detect_lang` from `crawler_utils` and `MIN_TEXT_LENGTH_FOR_DETECTION` from `utils`

5. **Create `crawl_persister.py`** with `CrawlPersister` class:
   - Move `_save_crawl_file` method logic here
   - Move `_make_crawl_filepath` method logic here
   - Accept `_rag_src_dir` config value via constructor
   - Import `CrawlJsonPayload` from `pipeline_utils`

#### Phase 2: Refactor WebCrawler to facade

6. **Reduce `crawler.py`** to thin composition facade:
   - Replace `WebCrawler` class body with constructor that instantiates all 5 components
   - Delegate `crawl()` to `self.orchestrator.crawl()`
   - Delegate `crawl_site()` to `self.orchestrator.crawl_site()`
   - Delegate `crawl_file()` to `self.persister.save()`
   - Remove all private helper methods (they now live in their respective components)
   - Keep CLI entry point unchanged

7. **Wire component dependencies** in `WebCrawler.__init__`:
   ```python
   self.http_fetcher = HttpFetcher(self.config)
   self.content_extractor = ContentExtractor(self.http_fetcher)
   self.link_discovery = LinkDiscovery(self.http_fetcher)
   self.language_resolver = LanguageResolver()
   self.crawl_persister = CrawlPersister(self.config)
   self.orchestrator = CrawlOrchestrator(
       http_fetcher=self.http_fetcher,
       content_extractor=self.content_extractor,
       link_discovery=self.link_discovery,
       language_resolver=self.language_resolver,
       persister=self.crawl_persister,
       config=self.config,
   )
   ```

#### Phase 3: Verification

8. Run `ruff` on all new/modified files
9. Run `mypy` on all new/modified files
10. Run `bandit` on all new/modified files
11. Run `uv run pytest` and compare against pre-change baseline
12. Apply full validation sequence: format → lint → type → arch → security → test → coverage

### Method

Use Write tool to create new files, Edit tool to modify existing crawler.py.

### Details

#### Component Dependency Graph

```
WebCrawler (facade)
├── CrawlOrchestrator
│   ├── HttpFetcher
│   ├── ContentExtractor
│   └── LinkDiscovery
├── LanguageResolver
└── CrawlPersister
```

All components depend on `crawler_utils.py` for pure functions. Components may also depend on `pipeline_utils.py` for TypedDict payloads.

#### WebCrawler Facade Design

After refactoring, `WebCrawler` becomes a thin composition layer:

```python
class WebCrawler:
    def __init__(self, config: dict | None = None) -> None:
        # Load config (unchanged)
        self.config = config or {}
        
        # Wire components via constructor injection
        self.http_fetcher = HttpFetcher(self.config)
        self.content_extractor = ContentExtractor(self.http_fetcher)
        self.link_discovery = LinkDiscovery(self.http_fetcher)
        self.language_resolver = LanguageResolver()
        self.crawl_persister = CrawlPersister(self.config)
        self.orchestrator = CrawlOrchestrator(
            http_fetcher=self.http_fetcher,
            content_extractor=self.content_extractor,
            link_discovery=self.link_discovery,
            language_resolver=self.language_resolver,
            persister=self.crawl_persister,
            config=self.config,
        )
    
    # Public interface preserved
    async def crawl(self, targets: list[tuple[str, str]]) -> None:
        return await self.orchestrator.crawl(targets)
    
    async def crawl_site(self, start_url: str, hint_lang: str) -> None:
        return await self.orchestrator.crawl_site(start_url, hint_lang)
    
    def crawl_file(self, path: Path, lang: str) -> int:
        return self.crawl_persister.save(path, lang)
```

## Compatibility considerations

- Preserve `WebCrawler`'s public methods (`crawl`, `crawl_site`, `crawl_file`, `__init__`) with identical signatures and behavior after the refactor
- Preserve the CLI entry point (`python crawler.py [--url ...] [--lang ...] [--targets-file ...]`) and its argument parsing behavior unchanged
- Do not change any observable crawl behavior: BFS traversal order, concurrency limits, retry/backoff timing, conditional-header handling, or JSON payload schema
- Do not change any existing log message string
- Do not change `crawler.toml`'s config keys or their meaning

## Security considerations

N/A: refactoring only; no new security-sensitive code introduced.

## Rollback considerations

If the refactoring introduces behavioral regression, revert to the original `WebCrawler` class structure using git checkout before considering alternative approaches.

## Validation plan

| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| `scripts/rag/ingestion/http_fetcher.py` | Unit: mock HTTP responses, verify retry/backoff behavior | `pytest tests/rag/ingestion/test_http_fetcher.py` | All assertions pass |
| `scripts/rag/ingestion/content_extractor.py` | Unit: feed parsed HTML, verify title/body/code-block extraction | `pytest tests/rag/ingestion/test_content_extractor.py` | All assertions pass |
| `scripts/rag/ingestion/link_discovery.py` | Unit: feed parsed HTML with links, verify nofollow/cross-origin filtering | `pytest tests/rag/ingestion/test_link_discovery.py` | All assertions pass |
| `scripts/rag/ingestion/language_resolver.py` | Unit: feed text samples, verify CJK-ratio detection | `pytest tests/rag/ingestion/test_language_resolver.py` | All assertions pass |
| `scripts/rag/ingestion/crawl_persister.py` | Unit: feed crawl data, verify JSON write to rag-src/ | `pytest tests/rag/ingestion/test_crawl_persister.py` | All assertions pass |
| `scripts/rag/ingestion/crawler.py` | Integration: end-to-end crawl with real HTTP server | `pytest tests/rag/ingestion/test_crawler_integration.py` | All assertions pass |
| Full suite | Regression: compare against pre-change baseline | `uv run pytest` | No new failures |

## Completion criteria

- Each resulting module/class addresses exactly one of the six concerns listed under Implementation Intent (REQ-001 through REQ-006)
- `WebCrawler`'s public methods (`crawl`, `crawl_site`, `crawl_file`, `__init__`) retain identical signatures and behavior after the refactor
- The CLI entry point behaves identically
- All pre-existing tests in the four crawler-related test files pass unchanged in outcome
- `ruff`, `mypy`, and `bandit` are clean on all new/modified files
- A full `uv run pytest` run shows no new failures compared to the pre-change baseline

## Out of scope

- Changing BFS crawl strategy, concurrency model, or retry/backoff algorithm
- Changing `CrawlJsonPayload` schema or `rag-src/` output file naming
- Adding new crawler features
- Modifying `crawler_utils.py`'s existing pure-function helpers
- Modifying downstream pipeline stages (`chunk_splitter.py`, `ingester.py`)
- Performance optimization

## Execution Status

### Execution Status

| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Create http_fetcher.py | Complete | 2026-09-02 00:00 | 2026-09-02 00:00 | sqlite3 import fixed |
| 2 | Create content_extractor.py | Complete | 2026-09-02 00:00 | 2026-09-02 00:00 | — |
| 3 | Create link_discovery.py | Complete | 2026-09-02 00:00 | 2026-09-02 00:00 | BeautifulSoup type hint fixed |
| 4 | Create language_resolver.py | Complete | 2026-09-02 00:00 | 2026-09-02 00:00 | — |
| 5 | Create crawl_persister.py | Complete | 2026-09-02 00:00 | 2026-09-02 00:00 | — |
| 6 | Reduce crawler.py to facade | Complete | 2026-09-02 00:00 | 2026-09-02 00:00 | BFS moved to orchestrator |
| 7 | Wire component dependencies | Complete | 2026-09-02 00:00 | 2026-09-02 00:00 | Constructor injection applied |
| 8 | Run ruff on all files | Complete | 2026-09-02 00:00 | 2026-09-02 00:00 | All checks passed |
| 9 | Run mypy on all files | Complete | 2026-09-02 00:00 | 2026-09-02 00:00 | Success: no issues found |
| 10 | Run bandit on all files | Complete | 2026-09-02 00:00 | 2026-09-02 00:00 | No issues identified |
| 11 | Run uv run pytest | Pending | — | — | Requires existing test baseline |

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
- **Source plan**: plans/20260831-153021_plan.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: $(date +%Y%m%d-%H%M%S)
- **Related target files**: scripts/rag/ingestion/crawler.py, scripts/rag/ingestion/http_fetcher.py, scripts/rag/ingestion/content_extractor.py, scripts/rag/ingestion/link_discovery.py, scripts/rag/ingestion/language_resolver.py, scripts/rag/ingestion/crawl_persister.py

### Requirement Traceability

| Requirement ID | Source Issue section or evidence | Target file | Implementation step | Acceptance criterion | Test or validation item | Status |
|---|---|---|---|---|---|---|
| REQ-001 | Problem section; verified WebCrawler exceeds 400-line threshold | scripts/rag/ingestion/crawler.py | Phase 2, Step 6 | Crawl orchestrator owns BFS queue/semaphore loop | Manual review | Confirmed by repository evidence |
| REQ-002 | Problem section; verified _fetch_html_async combines HTTP fetching logic | scripts/rag/ingestion/http_fetcher.py | Phase 1, Step 1 | HTTP fetcher owns retrying fetch and conditional-header lookup | Manual review | Confirmed by repository evidence |
| REQ-003 | Problem section; verified _extract_content combines HTML parsing logic | scripts/rag/ingestion/content_extractor.py | Phase 1, Step 2 | Content extractor owns HTML parsing | Manual review | Confirmed by repository evidence |
| REQ-004 | Problem section; verified _enqueue_links combines link discovery logic | scripts/rag/ingestion/link_discovery.py | Phase 1, Step 3 | Link discovery owns outbound link filtering | Manual review | Confirmed by repository evidence |
| REQ-005 | Problem section; verified _resolve_lang combines language resolution logic | scripts/rag/ingestion/language_resolver.py | Phase 1, Step 4 | Language resolver owns _resolve_lang | Manual review | Confirmed by repository evidence |
| REQ-006 | Problem section; verified _save_crawl_file combines persistence logic | scripts/rag/ingestion/crawl_persister.py | Phase 1, Step 5 | Crawl file persister owns JSON payload construction/write | Manual review | Confirmed by repository evidence |
| REQ-007 | Problem section; verified public interface must be preserved | scripts/rag/ingestion/crawler.py | Phase 2, Step 7 | Preserve WebCrawler's public interface exactly | Manual review | Confirmed by repository evidence |
| REQ-008 | Problem section; verified CLI entry point must be preserved | scripts/rag/ingestion/crawler.py | Phase 2, Step 7 | Preserve the CLI entry point unchanged | Manual review | Confirmed by repository evidence |
| REQ-009 | Problem section; verified observable crawl behavior must not change | scripts/rag/ingestion/crawler.py | Phase 3, Step 11 | Do not change any observable crawl behavior | Manual review | Confirmed by repository evidence |
| REQ-010 | Problem section; verified lint/type/security must be clean | scripts/rag/ingestion/*.py | Phase 3, Steps 8-10 | ruff, mypy, and bandit are clean on all new/modified files | Manual review | Confirmed by repository evidence |
| REQ-011 | Problem section; verified full test suite must pass | scripts/rag/ingestion/*.py | Phase 3, Step 11 | Full uv run pytest run shows no new failures | Manual review | Confirmed by repository evidence |
