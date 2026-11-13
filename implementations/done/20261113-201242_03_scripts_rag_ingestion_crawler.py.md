## Goal

`REQ-001`, `REQ-003`, `REQ-004`, `REQ-005`: in `scripts/rag/ingestion/crawler.py` remove the `no-any-return` suppression, read `args.targets_file` directly, keep one `ConfigLoader` import, rename the non-existent modules in the docstring, and reword the "bypass" comment to the `crawler.toml` model. Crawling behavior is unchanged.

## Scope
**Release unit**: N/A: not part of a release unit

## Assumptions
- `--targets-file` is always added to the argument parser (lines 192–196), so `args.targets_file` always exists; direct access cannot silently yield `None` the way `getattr(args, "targets_file", None)` could.
- The top-level `from shared.config_loader import ConfigLoader` (line 34) is the single import; the one inside `if __name__ == "__main__":` (line 224) is the duplicate.
- The wrapped return (`CrawlPersister.save`) is correctly typed once `rag.ingestion` is a regular package.

## Design decisions
- Direct attribute access turns a renamed CLI argument into an explicit `AttributeError` (parser error territory) instead of a silent `None`.
- Removing the duplicate import keeps `ConfigLoader` resolvable from line 34 for both `WebCrawler.__init__` (line 74) and `main()` (line 226 `restrict_to`).

## Alternatives considered
- N/A: line-local edits with no public-contract, persistence, or security impact.

## Implementation
### Target file
`scripts/rag/ingestion/crawler.py`

### Procedure
1. Remove the suppression and its comment on `CrawlPersister.save`'s return.
2. Read `args.targets_file` directly at the two `getattr` sites.
3. Remove the duplicate `ConfigLoader` import in `__main__`.
4. Rename the modules in the docstring (entry point + pipeline line).
5. Reword the DB-settings comment.

### Method
1. In `CrawlPersister.save`, change
   `        return self.crawl_persister.save(path, lang)  # type: ignore[no-any-return]  # — CrawlPersister.save() is correctly typed -> int; mypy loses this across the rag.* vs scripts.rag.* dual module-path resolution (see scripts/shared/tool_constants.py's confirmed duplicate-module-name issue)`
   to
   `        return self.crawl_persister.save(path, lang)`
   (current line 127).
2. In `main()`, change
   `    if args.url and getattr(args, "targets_file", None):`
   to
   `    if args.url and args.targets_file:`
   (current line 200), and
   `    if getattr(args, "targets_file", None):`
   to
   `    if args.targets_file:`
   (current line 205). The body already reads `Path(args.targets_file)` at line 207.
3. Remove the local import block
   ```python
   if __name__ == "__main__":
       from shared.config_loader import ConfigLoader

       ConfigLoader.restrict_to("crawler.toml")
       main()
   ```
   to
   ```python
   if __name__ == "__main__":
       ConfigLoader.restrict_to("crawler.toml")
       main()
   ```
   (delete line 224 only; keep line 34).
4. Module docstring: change
   `Entry point: python Crawler.py [--url URL ...] [--lang {en,ja}]`
   to
   `Entry point: uv run python scripts/rag/ingestion/crawler.py [--url URL ...] [--lang {en,ja}]`
   (line 5), and
   `Pipeline position: Crawler.py → ChunkSplitter.py → RagIngester.py`
   to
   `Pipeline position: crawler → chunk_splitter → ingester`
   (line 10).
5. In `CrawlPersister`, reword
   `        # DB settings for conditional-header cache lookups (bypasses build_db_config)`
   to
   `        # DB settings loaded from crawler.toml for conditional-header cache lookups`
   (line 95).

### Details
- Preserve each file's existing arrow character (`→` in the docstring, `->` elsewhere); only the module tokens change.
- Do not alter argument parsing, the mutual-exclusion check, or the crawl dispatch.

## Compatibility considerations
N/A: behavior-preserving; the CLI contract (`--targets-file`) and crawl flow are unchanged.

## Security considerations
N/A: no request handling or permission change.

## Rollback considerations
N/A: revert the commit.

## Validation plan
- `uv run pytest tests/rag/ingestion`: the existing parser-error tests (`--url` with `--targets-file`, missing file, parse error) still pass, covering the `args.targets_file` change.
- `uv run mypy --no-namespace-packages scripts/ tests/eventbus tools`: the four `unused-ignore` from docs 03–05 are gone after this runs; only the two `http_fetcher.py` `arg-type` errors remain until doc 06.
- `rg -n "getattr\(args" scripts/rag/ingestion/` (AC-3): no match.
- `rg -n "Crawler\.py|ChunkSplitter\.py|RagIngester\.py" scripts/rag/ingestion/` (AC-4): no match.
- `rg -n "bypass(es)? build_db_config" scripts/rag/ingestion/` (AC-5): no match.
- `tools/check_docstrings.py`: `rag/ingestion/crawler.py` still conforms (em-dash on its "Output" line); no new finding.
- `lint-imports`: one `from shared.config_loader import ConfigLoader` remains (line 34); baseline unchanged.

## Completion criteria
- No `# type: ignore[no-any-return]`, no `getattr(args`, no second `ConfigLoader` import, no `Crawler.py`/`ChunkSplitter.py`/`RagIngester.py`, and no `bypass build_db_config` wording remain in this file.
- `crawler.py` has exactly one `from shared.config_loader import ConfigLoader`.

## Out of Scope
The suppression removals in docs 04–05, the `http_fetcher.py` typing fixes (doc 06), the `chunk_splitter.py` import/suppression fix (doc 04).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 20261113-201242 | 20261113-204236 | suppression removed; getattr direct; duplicate import gone; docstring/comment reworded |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20261113-201242 | 20261113-204236 | mypy 0 errors (561 files); pytest 353 passed; AC-3/AC-4/AC-5 clear; lint-imports one ConfigLoader import |

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
- **Requirement ID**: `REQ-001`, `REQ-003`, `REQ-004`, `REQ-005`
- **Source issue**: issues/20261110-171004_rmcompat006_rag-ingestion-cleanup.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261112-121532_rmcompat006_rag-ingestion-cleanup.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261113-201242
- **Related target files**: `scripts/rag/ingestion/crawler.py`
