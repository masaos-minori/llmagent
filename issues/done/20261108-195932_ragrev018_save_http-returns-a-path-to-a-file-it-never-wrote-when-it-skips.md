# save_http returns a path to a file it never wrote when it skips

## Priority
Low

## Summary
Make `CrawlPersister.save_http` return `None` on its skip branches instead of a
path to a file it did not write, so a skipped save can never be mistaken for a
written artifact.

## Background
`CrawlPersister.save_http` lives in `scripts/rag/ingestion/crawl_persister.py`
(extracted from `WebCrawler` to separate persistence from BFS orchestration). It
builds the crawl JSON payload and writes it to `rag-src/`. Its return type is
`Path`, which callers read as "the file that was just written".

## Problem
`save_http` has three early-return skip branches that compute and return
`self.make_crawl_filepath(url)` without writing any payload:

- unsupported `lang` (`scripts/rag/ingestion/crawl_persister.py` line 118-120)
- `code_blocks` not a list (`scripts/rag/ingestion/crawl_persister.py` line 121-123)
- empty content without code blocks (`scripts/rag/ingestion/crawl_persister.py` line 124-126)

Each returns a `Path` to a file that does not exist. The sole caller
`CrawlOrchestrator._process_crawl_url_async`
(`scripts/rag/ingestion/orchestrator.py` lines 244-263) pre-validates all three
conditions before calling (`not text and not code_blocks` -> return at line
244-246; `resolved_lang not in {"en","ja"}` -> return at line 249-251;
`code_blocks` always comes from `ContentExtractor.extract_content` as a list), so
these branches are currently unreachable. The defect is a contract smell, not a
live bug.

## Reason for Change
A `Path` return implies a file exists. If the pre-checks are relaxed, a new
caller is added, or `extract_content` changes what it returns, a caller could
receive a phantom path and treat it as a written artifact (e.g. count it against
the persisted budget or enqueue it). Making the skip contract explicit removes
that footgun now, while the change is cheap and the call site is known.

## Implementation Intent
Change `save_http`'s return type to `Path | None`. Return `None` on each of the
three skip branches instead of `self.make_crawl_filepath(url)`. Update the single
caller to treat `None` as "nothing persisted": skip the `budget.persisted += 1`
increment and any downstream use of the path. Keep the write path and its return
value unchanged.

## Target Files or Areas
- `scripts/rag/ingestion/crawl_persister.py` (`CrawlPersister.save_http`)
- `scripts/rag/ingestion/orchestrator.py` (`CrawlOrchestrator._process_crawl_url_async`)
- `tests/rag/ingestion/test_crawler_integration.py` (add skip-branch coverage)

## Required Changes
- Change the `save_http` return annotation from `Path` to `Path | None`.
- Return `None` on the unsupported-lang, non-list-`code_blocks`, and empty-content
  branches instead of `self.make_crawl_filepath(url)`.
- In `_process_crawl_url_async`, capture the return value and only run
  `budget.persisted += 1` (and any path use) when it is not `None`.
- Add a unit test per skip branch asserting `save_http` returns `None` and that no
  file is created.

## Constraints
- The reachable write path must behave exactly as before: same payload, same
  filename format, same `Path` return.
- Budget-counting semantics must not change for pages that are actually written.
- Do not alter `save` (local-file path), which already returns `int`.

## Acceptance Criteria
- `save_http` returns `None` when `lang` is unsupported, `code_blocks` is not a
  list, or content and code blocks are both empty.
- `save_http` returns a `Path` whose file exists on the normal path.
- No caller treats a `None` return as a written artifact or counts it against the
  persisted budget.

## Testing Expectations
- Unit test each of the three skip branches returns `None` and creates no file.
- Existing crawler integration tests still pass (write path unchanged).

## Documentation Impact
- Update the docstring of `save_http` to state it returns `None` on a skip.
- Check `docs/21_rag/rag_02_06_ingestion_pipeline-supporting-components.md` for a
  description of `save_http`'s return and update it if present.

## Out of Scope
- Changing `save` (local-file) return contract.
- Relaxing or removing the pre-validation in the caller.
- Any other persistence method.

## Dependencies
N/A: none.

## Unresolved Questions
- Should a skip return `None` or raise a dedicated error? Returning `None` matches
  the current swallow-and-log behavior; raising would be stricter but changes the
  public contract. `Needs confirmation`: prefer `None` unless a reviewer wants
  fail-closed.

## AI Implementation Instruction
- Change only `save_http`'s return type and its three skip returns to `None`, plus
  the one caller's handling. Do not touch `save` or the write path.
- Keep comments and log output in English.
- Preserve ruff/mypy cleanliness: the `Path | None` change must flow correctly
  through the caller.

## Traceability
- **Workflow phase**: `python-code-review`
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20261108-195932
- **Related target files**: `scripts/rag/ingestion/crawl_persister.py`, `scripts/rag/ingestion/orchestrator.py`
