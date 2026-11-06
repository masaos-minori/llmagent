# Add a configurable robots.txt policy to the crawler

## Priority
Low

## Summary
Add an explicit, configurable robots.txt policy to the crawler so external-site crawling respects `Disallow` rules, instead of enforcing only a fixed delay with no politeness parsing.

## Background
The BFS crawler (`CrawlOrchestrator` + `LinkDiscovery`) filters links by `nofollow` and cross-origin rules and applies a constant `crawl_delay`. There is no robots.txt fetching or parsing anywhere in `scripts/rag/ingestion/`.

## Problem
Crawling external sites without respecting robots.txt can violate site policy, Terms of Service, or legal expectations. The current fixed delay alone does not address path-level disallow rules.

## Reason for Change
The configured targets are currently well-known documentation sites, but adding an explicit, toggleable policy now prevents future exposure when new targets are added and makes the politeness stance deliberate rather than accidental.

## Implementation Intent
Introduce an optional, disabled-by-default robots.txt layer that, when enabled, fetches and caches `robots.txt` per host and skips disallowed paths before enqueueing. Gate it behind a config flag so existing behavior is unchanged unless opted in. Keep it isolated from the core BFS loop.

## Target Files or Areas
`scripts/rag/ingestion/` (new or extended link-discovery/fetch layer), `config/crawler.toml`

## Required Changes
- Add a config flag to enable/disable robots.txt respect.
- When enabled, fetch/cache `robots.txt` per host and filter disallowed URLs before enqueue.
- Default disabled so current behavior is unchanged.

## Constraints
- Must not change crawling when the flag is off (behavior identical to today).
- Respect concurrency: cache `robots.txt` per host and avoid hammering hosts.
- Do not alter existing nofollow / cross-origin filtering.

## Acceptance Criteria
- With the flag off, behavior is unchanged (no robots.txt requests issued).
- With the flag on, disallowed paths are skipped and allowed paths are crawled.
- `robots.txt` is fetched at most once per host per crawl.

## Testing Expectations
- Test that the flag-off path issues no robots.txt requests.
- Test that the flag-on path respects a sample `Disallow` rule using mocked responses.
- `ruff` / `mypy` clean on touched files.

## Documentation Impact
Document the new config flag and its default in the crawler config notes.

## Out of Scope
- Changing link-filtering (nofollow / cross-origin) semantics.
- Crawl-rate tuning beyond the existing `crawl_delay`.

## Dependencies
N/A: none

## Unresolved Questions
- Whether robots.txt respect should be enabled by default for external hosts, or remain opt-in. Opt-in is recommended to preserve current behavior.

## AI Implementation Instruction
Add an opt-in (default off) robots.txt layer that fetches/caches per host and filters disallowed paths before enqueue. Do not change any behavior when the flag is off. Add tests for both flag states. Run `ruff` and `mypy`.

## Traceability
- **Workflow phase**: `python-code-review`
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20261106-073205
- **Related target files**: `scripts/rag/ingestion/`, `config/crawler.toml`
