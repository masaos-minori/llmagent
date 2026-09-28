# Fix crawler max_pages default mismatch and confirm limit rationale (NC-035)

## Priority
Medium

## Summary
Fix a confirmed bug — `scripts/rag/ingestion/crawler.py`'s fallback default for `max_pages` (500) diverges from the deployed `config/crawler.toml` value (200), breaking this file's own established fallback-default convention — and separately route the still-genuinely-unknown `max_depth=3`/`max_pages=200` rationale to the owner.

## Background
NC-035 originally asked why crawl depth is limited to 3 hops and max pages to 200, and (per this session's own earlier update) also flagged that the code's fallback default (500) differs from the deployed config value (200). A deep-dive investigation (2026-09-27) found:
- No rationale for `max_depth=3`/`max_pages=200` exists anywhere in git history; `config/crawler.toml`'s own inline comment already states this is an unvalidated heuristic.
- The 500-vs-200 mismatch is a confirmed **bug**, not intentional design: every other `cfg.get(key, default)` fallback in `crawler.py` (`fetch_timeout`, `crawl_concurrency`, `sqlite_timeout`, `sqlite_busy_timeout_ms`) exactly mirrors its deployed `config/crawler.toml` value — `max_pages` is the sole outlier. Commit `e184208c` ("chore: apply recommended default values to config files", 2026-07-05) deliberately retuned the deployed config's `max_pages` from 500 → 200, but the code's own fallback default in the crawler constructor was never updated to match — a stale leftover from before that tuning commit.
- A related, lower-stakes finding (not part of this issue's scope): `skip_nofollow`'s default (`False`) also diverges from the deployed `True` value, by the same class of staleness.

## Problem
If the `max_pages` key were ever removed or misconfigured in `config/crawler.toml`, the crawler would silently revert to 500 pages per site instead of the intended 200 — a behavior change with no warning, breaking the file's own "fallback mirrors deployed value" convention.

## Reason for Change
This is a real, evidence-confirmed bug (not merely an unknown-rationale documentation gap): the code's fallback default should follow the same convention as every sibling config value in the same file.

## Implementation Intent
Change `scripts/rag/ingestion/crawler.py`'s `cfg.get("max_pages", 500)` fallback default to `200`, matching every other fallback in the file and the deployed config. Separately, route the `max_depth=3`/`max_pages=200` rationale question to the owner for confirmation or explicit "no rationale" acceptance — this does not block the code fix.

## Target Files or Areas
- `scripts/rag/ingestion/crawler.py` (fix the `max_pages` fallback default)
- `config/crawler.toml` (reference; already documents the "no rationale" finding for 3/200 via its own inline comment)
- `docs/00_governance/governance_03_issue-and-uncertainty-management.md` (NC-035 entry)

## Required Changes
- Change `cfg.get("max_pages", 500)` to `cfg.get("max_pages", 200)` in `scripts/rag/ingestion/crawler.py`.
- Owner confirmation of `max_depth=3`/`max_pages=200`'s historical rationale, or explicit acceptance that none exists.
- Update/remove the NC-035 entry in `governance_03` once both the code fix lands and the rationale question is resolved (or formally accepted as unknown).

## Constraints
Preserve existing behavior for any deployment where `config/crawler.toml`'s `max_pages` key is present and set to 200 (the common case) — only the fallback path (key absent) changes.

## Acceptance Criteria
- `scripts/rag/ingestion/crawler.py`'s `max_pages` fallback default is `200`, matching every other fallback in the file.
- A test confirms the fallback default (absent `max_pages` key in config) produces `200`, not `500`.
- Full test suite passes with no regression.
- NC-035 is resolved or reduced to only the still-unknown 3/200 rationale question, once the code fix and its test land.

## Testing Expectations
Unit test asserting the fallback default when `max_pages` is absent from config. Run the targeted test, then the full suite once per `rules/toolchain.md`.

## Documentation Impact
Update NC-035 in `governance_03` to remove the now-fixed code/config mismatch language, keeping only the still-open `max_depth=3`/`max_pages=200` rationale question until the owner responds.

## Out of Scope
- The separate `skip_nofollow` default mismatch (a related but distinct finding; file separately if desired).
- Performing empirical crawl-limit tuning/validation (a separate future issue if the owner requests changing 3/200 itself, as opposed to merely explaining it).

## Dependencies
N/A: none.

## Unresolved Questions
Whether the owner has historical rationale for `max_depth=3`/`max_pages=200`, or whether this should be closed as "no rationale, accepted as-is" (the fallback-default bug fix itself does not depend on this answer).

## AI Implementation Instruction
Make only the one-line fallback-default fix plus its test. Do not touch `skip_nofollow` or any other fallback default in the same file — that is a separate, distinct finding. Do not invent a rationale for 3/200.

## Traceability
- **Workflow phase**: issue-creator
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20260927-211418
- **Related target files**: scripts/rag/ingestion/crawler.py, config/crawler.toml (reference), docs/00_governance/governance_03_issue-and-uncertainty-management.md
