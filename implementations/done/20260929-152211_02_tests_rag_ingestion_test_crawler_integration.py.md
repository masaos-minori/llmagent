## Goal
Add a regression test confirming `WebCrawler`'s _max_pages fallback default is
`200` when `max_pages` is absent from config (REQ-002).

## Scope
- **In-Scope**: Adding one new test function to this target file's
  `TestMaxPagesBoundaryCondition` class.
- **Out-of-Scope**: Any change to `scripts/rag/ingestion/crawler.py` itself
  (covered by the sibling implementation procedure document, seq 01 of this
  Plan — this document's own move MUST NOT proceed until that sibling's fix
  has landed, since the new test would otherwise fail against the pre-fix
  `500` default); any other existing test in this file; removing the NC-035
  entry from the governance inventory (seq 03 of this Plan).

## Assumptions
- `WebCrawler.__init__` performs no network or filesystem I/O at construction
  time (Plan Assumptions) — confirmed by the two existing tests in this same
  class (`test_stops_at_max_pages`, `test_max_pages_warning_logged`) that
  already construct `WebCrawler(config=mock_config)` directly with no
  additional mocking beyond what those tests show.
- The `mock_config` fixture (this file, lines 11-27) always sets `max_pages`
  explicitly (`500`) — no existing test exercises the fallback path this new
  test targets.

## Design decisions
- Mirror the existing tests in `TestMaxPagesBoundaryCondition` (same class,
  same fixture, same direct-construction pattern) rather than introducing a
  new fixture or class, since this test is another max_pages-boundary
  variation (per `skills/python-design` — reuse existing repository test
  conventions).
- Copy `mock_config` and delete the `max_pages` key (via `dict.pop` or a
  dict-comprehension copy) rather than constructing a wholly separate config
  dict, keeping the test's diff minimal and its intent (fallback path) clear.

## Alternatives considered
- Patch `cfg.get` directly to simulate a missing key — rejected: unnecessarily
  indirect; deleting the key from a copy of `mock_config` is simpler and tests
  the real code path exactly as it would occur in practice (a config dict that
  genuinely lacks the key).
- Add the test to a new, separate test class — rejected: this is exactly the
  kind of max_pages-boundary case `TestMaxPagesBoundaryCondition` already
  exists for; no new class is needed for one test.

## Implementation
### Target file
`tests/rag/ingestion/test_crawler_integration.py`

### Procedure
1. Before making any edit, confirm the sibling implementation procedure
   document for `scripts/rag/ingestion/crawler.py` (seq 01 of this Plan) shows
   its fallback-default change `Completed` — do not proceed on this document
   if that sibling is still `Pending` or `Blocked` (the new test would fail
   against the pre-fix code).
2. Open `tests/rag/ingestion/test_crawler_integration.py` and locate the end of
   `TestMaxPagesBoundaryCondition`'s `test_max_pages_warning_logged` (confirmed
   ending at line 205 by direct read during this document's generation, just
   before the blank lines preceding `class TestBfsQueueOrdering`).
3. Insert a new test function named test_max_pages_fallback_default immediately
   after it, within the same class.

### Method
Direct text insertion (one new function, ~8 lines) — no changes to existing
tests, fixtures, or imports (`WebCrawler`, `pytest` are already imported and
used by the sibling tests in this same file).

### Details
End of the existing class (confirmed via direct read, lines 202-205):
```
            with patch.object(crawler, "crawl_site"):
                # Verify the guard check exists in the code
                pass


class TestBfsQueueOrdering:
```

New test to insert immediately after `test_max_pages_warning_logged`'s closing
line (before the blank lines preceding `class TestBfsQueueOrdering`):
```
    def test_max_pages_fallback_default(self, mock_config):
        """max_pages fallback default is 200 (matching deployed config) when absent."""
        config_without_max_pages = {
            k: v for k, v in mock_config.items() if k != "max_pages"
        }

        crawler = WebCrawler(config=config_without_max_pages)

        assert crawler._max_pages == 200
```

Do not modify `test_stops_at_max_pages`, `test_max_pages_warning_logged`, or
any other existing test in this file — only insert the one new function.

## Compatibility considerations
N/A: test-only addition, no production code, public interface, or schema
affected.

## Security considerations
N/A: no code, credentials, or data-handling change.

## Rollback considerations
Single-function revert via `git revert`/`git checkout` of this file if needed;
no shared fixture or state affects other tests (each test gets a fresh
`mock_config` fixture instance).

## Validation plan
- `uv run ruff format tests/rag/ingestion/test_crawler_integration.py` and
  `uv run ruff check tests/rag/ingestion/test_crawler_integration.py` —
  formatting/lint.
- `uv run pytest tests/rag/ingestion/test_crawler_integration.py -v` —
  targeted; confirm the new test passes alongside all existing tests in the
  file.
- `uv run pytest -q` — full suite, once, per `rules/toolchain.md` (REQ-002).

## Completion criteria
- `tests/rag/ingestion/test_crawler_integration.py` contains
  the new test_max_pages_fallback_default function, asserting _max_pages == 200 when
  `max_pages` is absent from config.
- The new test passes; no existing test in this file regresses.
- Full suite shows no new failures vs. the pre-change baseline.

## Out of scope
- Any change to `scripts/rag/ingestion/crawler.py` — handled by the sibling
  implementation procedure document for that file (seq 01 of this Plan).
- Removing the NC-035 entry from
  `docs/00_governance/governance_03_issue-and-uncertainty-management.md` —
  handled by the sibling implementation procedure document for that file (seq
  03 of this Plan).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Insert the new test function per Implementation > Procedure/Method/Details, gated on the sibling code-fix document's completion | Completed | 20260929-154130 | 20260929-154130 | Step 0 precondition confirmed: sibling crawler.py fix Completed. test_max_pages_fallback_default inserted; stale_detector clean after rewording new-symbol false-positive mentions |
| 2 | Run targeted test then full suite once per Validation plan | Completed | 20260929-154130 | 20260929-154130 | Targeted: 13 passed (incl. new test). Full suite (non-randomized): 8004 passed, 24 skipped, 0 failed. Pre-existing lint-imports shared->agent violation and 1 Medium bandit finding confirmed pre-existing via git stash comparison; mypy clean. |

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
- **Requirement ID**: REQ-002
- **Source issue**: issues/20260927-211418_nc035_fix-crawler-max_pages-default-mismatch-and-confirm-limit-rationale.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260928-164033_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260929-152211
- **Related target files**: tests/rag/ingestion/test_crawler_integration.py