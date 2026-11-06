# Remove unreachable CrawlOrchestrator.crawl method

## Priority
Medium

## Summary
Delete the unused `CrawlOrchestrator.crawl` method, which has no caller and contains a broad `except Exception` that violates the project's prohibited-pattern rule.

## Background
`CrawlOrchestrator` owns the per-site BFS loop via `crawl_site`. It also defines an async `crawl(targets)` method that iterates targets and calls `crawl_site` per target. `WebCrawler.crawl` in `scripts/rag/ingestion/crawler.py` performs that same iteration but calls `self.orchestrator.crawl_site` directly, and `main()` invokes `WebCrawler.crawl`.

## Problem
`CrawlOrchestrator.crawl` is never called anywhere in `scripts/` or `tests/`. It is dead code that duplicates `WebCrawler.crawl` while using a broader `except Exception as _crawl_err` than the live path (which narrows to `(httpx.RequestError, httpx.HTTPStatusError, OSError)`). If someone later wires `WebCrawler.crawl` to `orchestrator.crawl`, the broad except would silently swallow crawler failures.

## Reason for Change
Dead code with a prohibited pattern is a maintenance and correctness hazard. It invites confusion about which loop is authoritative and hides future errors if adopted.

## Implementation Intent
Remove the `crawl` method from `CrawlOrchestrator` entirely. Confirm via grep that nothing in `scripts/` or `tests/` references it before deleting. No behavioral change results, since it is unreachable.

## Target Files or Areas
`scripts/rag/ingestion/orchestrator.py`

## Required Changes
- Delete `CrawlOrchestrator.crawl` (the async method iterating targets).
- Verify with `rg` that no caller remains in `scripts/` and `tests/`.
- Confirm the module still imports and type-checks.

## Constraints
- Do not alter `CrawlOrchestrator.crawl_site` or any live method.
- Do not change `WebCrawler.crawl` behavior.

## Acceptance Criteria
- `CrawlOrchestrator.crawl` no longer exists.
- No reference to `orchestrator.crawl` remains in `scripts/` or `tests/`.
- `mypy` and `ruff` pass on `orchestrator.py`.

## Testing Expectations
- `mypy` / `ruff` clean on the edited file.
- Existing crawler tests still pass (no behavior change).

## Documentation Impact
None required.

## Out of Scope
- Refactoring `CrawlOrchestrator.crawl_site`.
- Changing `WebCrawler.crawl` to delegate to the orchestrator.

## Dependencies
N/A: none

## Unresolved Questions
N/A: none

## AI Implementation Instruction
Delete only the `crawl` async method from `CrawlOrchestrator`. Confirm with `rg` that no caller remains in `scripts/` or `tests/`. Do not touch `crawl_site` or any other method. Run `ruff` and `mypy` on the file.

## Traceability
- **Workflow phase**: `python-code-review`
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20261106-073205
- **Related target files**: `scripts/rag/ingestion/orchestrator.py`
