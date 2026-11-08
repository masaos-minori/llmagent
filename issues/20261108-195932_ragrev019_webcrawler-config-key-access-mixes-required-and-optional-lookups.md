# WebCrawler config-key access mixes required and optional lookups

## Priority
Low

## Summary
Normalize `WebCrawler.__init__` config-key access so every key is read through a
single consistent mechanism (`cfg.get(key, default)` or one validation pass),
removing the mix of subscript (required) and `.get()` (optional) lookups that
produces an opaque `KeyError` for a missing required key.

## Background
`WebCrawler.__init__` (`scripts/rag/ingestion/crawler.py` lines 56-100) reads its
settings from a config dict. The rest of the crawler stack
(`HttpFetcher`, `CrawlOrchestrator`, `CrawlPersister`) reads config exclusively
with `cfg.get(key, default)` and defaults throughout. This class is the outlier.

## Problem
In `WebCrawler.__init__` the following keys use subscript access, which raises an
unhelpful `KeyError` if absent:

- `cfg["rag_src_dir"]` (line 60)
- `cfg["crawl_delay"]` (line 61)
- `cfg["max_depth"]` (line 62)
- `cfg["min_chunk"]` (line 63)
- `cfg["fetch_retry"]` (line 64)
- `cfg["target_urls"]` (line 68)

while these use `.get()` with defaults:

- `fetch_timeout`, `crawl_concurrency`, `max_pages` (lines 65-67)
- `skip_nofollow`, `skip_external`, `respect_robots` (lines 70-72)
- `rag_db_path`, `sqlite_timeout`, `sqlite_busy_timeout_ms` (lines 75-79)

All keys exist in `config/crawler.toml`, so this is not currently triggered. The
issue is an inconsistency and a fragile startup error path.

## Reason for Change
A missing required key raises a bare `KeyError` at startup instead of a clear
configuration error, and the mixed access pattern is inconsistent with the rest
of the crawler. Normalizing now is cheap before more keys are added.

## Implementation Intent
Route all crawler config keys through one consistent mechanism. Two acceptable
options (pick one, do not mix):

1. Convert every key to `cfg.get(key, default)` with an explicit, documented
   default, OR
2. Keep required keys genuinely required but validate them once up front with a
   single pass that raises a clear configuration error naming every missing key.

Preserve current values for present keys exactly.

## Target Files or Areas
- `scripts/rag/ingestion/crawler.py` (`WebCrawler.__init__`)
- `config/crawler.toml` (only if a new default is introduced; otherwise unchanged)

## Required Changes
- Make all config-key access in `__init__` consistent (all `.get()` or one
  validation pass), per the chosen option.
- If converting required keys to `.get()`, choose sensible defaults and record
  why in a comment (the existing `max_depth`/`max_pages` comments note unmeasured
  defaults).
- Ensure behavior for present keys is byte-for-byte unchanged.

## Constraints
- `config/crawler.toml` defines every key, so runtime behavior must not change
  for the shipped configuration.
- Do not change the semantics of any value (e.g. `target_urls` parsing must stay
  identical).
- Keep comments and log output in English.

## Acceptance Criteria
- No subscript (`cfg[...]`) access remains in `WebCrawler.__init__` unless a
  single explicit validation pass is used.
- A config dict missing a required key yields either a clear configuration error
  (option 2) or the documented default (option 1).
- All existing crawler tests pass; shipped config values unchanged.

## Testing Expectations
- Add a unit test constructing `WebCrawler` with a config missing one required
  key, asserting the expected outcome (clear error or default) for the chosen
  option.
- Existing crawler integration tests still pass.

## Documentation Impact
- If a new default is introduced, note it near the key. Otherwise no doc change
  required; verify `docs/21_rag/rag_02_02_ingestion_pipeline-crawler.md` does not
  document per-key defaults that would now drift.

## Out of Scope
- Changing any other component's config access.
- Changing default values that operators rely on without recorded rationale.
- Adding or removing config keys.

## Dependencies
N/A: none.

## Unresolved Questions
- Option 1 (all `.get()` with defaults) hides misconfiguration by silently
  applying defaults; option 2 (explicit validation) fails loudly. Which behavior
  is preferred for genuinely-required keys like `rag_src_dir` and `target_urls`?
  `Needs confirmation`.

## AI Implementation Instruction
- Change only `WebCrawler.__init__` config access. Pick ONE consistent approach
  (all `.get()` or one validation pass); do not mix.
- Preserve exact values for present keys. Keep ruff/mypy clean.

## Traceability
- **Workflow phase**: `python-code-review`
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20261108-195932
- **Related target files**: `scripts/rag/ingestion/crawler.py`
