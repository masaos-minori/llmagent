# Implementation: tests/test_mdq_search_modes.py (update `TestResultLimitBehavior`'s
wording-dependent assertions for new matched/shown count phrasing)

Source plan: `plans/20260719-210826_plan.md` ("Fix MDQ freshness detection and search result
correctness"), Assumption 4, Implementation step 4 ("Update existing test file
`tests/test_mdq_search_modes.py`"). This file is explicitly called out in the plan as "not in
the requirement's target file list but must be updated in the same commit" (plan Assumption 4).
No existing implementation document references this filename — new file.

## Goal

Update `TestResultLimitBehavior`'s three existing tests so their assertions match the new
header wording introduced by the companion `search.py` document
(`implementations/20260720-092134_search.py.md`), without weakening each test's original intent
(default-limit-honored, request-override-below-cap-is-honored,
request-override-above-cap-is-bounded). Today these three tests assert the literal substrings
`"3 found"` / `"5 found"`, which directly encode the old `f"...({original_total} found)"` header
format this plan's companion `search.py` document replaces.

## Scope

**In scope:**
- `TestResultLimitBehavior.test_default_limit_from_config` (`tests/test_mdq_search_modes.py:67-
  76`): currently asserts `"Truncated" not in result` and `"3 found" in result`. Update the
  second assertion to match the new no-truncation header wording (per companion `search.py`
  document: when `matched_count == shown_count`, the simple phrasing is retained, e.g. still
  `"3 found"` if that specific case's wording is unchanged — see Assumption 1 below for why this
  particular test may need NO wording change at all).
- `test_request_override_below_cap_is_honored` (lines 78-91): currently asserts `"Truncated" in
  result` and `"5 found"` in result — this is the case that changes: `original_total` (5) equals
  the number of documents indexed, but is displayed even though only 2 are shown after the
  `max_results_limit=2` override. Under the new wording, "5 found" is exactly the kind of
  overclaiming this plan intends to fix (it's the *matched* count, but the phrasing today doesn't
  distinguish it from an unqualified "found" total) — update the assertion to check for the new
  matched/shown-distinguishing wording instead (e.g. assert both `"5"` and `"2"` appear, rather
  than the single hardcoded substring `"5 found"`).
- `test_request_override_above_cap_is_bounded` (lines 93-106): currently asserts `"Truncated" in
  result` only (no `"N found"` assertion in the current code — re-verify against actual file
  content before editing; if a count-wording assertion needs adding here too for symmetry with
  the other two tests, add one).

**Out of scope:**
- `TestSearchModeRestriction` (lines 36-52) and `TestMaxSearchResultsRemoved` (lines 55-63) —
  unrelated to count/limit wording, untouched.
- The `service` fixture (lines 22-33) — untouched, already suitable for these tests as-is.
- Any test in this file beyond `TestResultLimitBehavior` — untouched.

## Assumptions

1. Direct read of the current file confirms:
   - `test_default_limit_from_config` (lines 67-76): indexes 3 docs, no explicit
     `max_results_limit`, asserts `"Truncated" not in result` and `"3 found" in result`. Since
     no limiting occurs here (`matched_count == shown_count == 3`), per the companion
     `search.py` document's Design ("if `matched_count == shown_count`... keep the simple
     existing phrasing style, e.g. `f'...({matched_count} found)'`"), this test's assertions may
     require **no change at all** — the simple "3 found" phrasing is retained precisely for the
     no-truncation case. Verify this against the actual wording chosen at implementation time;
     if the implementer's final wording differs even in the untruncated case (e.g. always says
     "matched" regardless), update this assertion too.
   - `test_request_override_below_cap_is_honored` (lines 78-91): indexes 5 docs, requests
     `max_results_limit=2`, asserts `"Truncated" in result` and `"5 found" in result`. This IS
     the mislabeling case the plan targets: 5 is the exact match count, but only 2 are shown, and
     the current text presents "5 found" without qualification — the new wording must surface
     both numbers distinguishably. Requires an assertion change.
   - `test_request_override_above_cap_is_bounded` (lines 93-106): indexes 3 docs, sets
     `service.max_results_limit = 2` directly, requests `max_results_limit=100`, asserts only
     `"Truncated" in result` (no substring-count assertion in the current code — confirmed by
     reading lines 100-106, the test body ends after the `"Truncated" in result` assertion).
2. The companion `search.py` document leaves exact wording as an implementation-time choice; this
   document's assertion updates use loose substring checks (`"5" in result and "2" in result`)
   rather than pinning one exact phrase, so this test file does not need a second edit if the
   implementer's exact wording differs slightly from any one example string.
3. `"Truncated" in result` assertions (present in 2 of the 3 tests) are NOT changed — the
   companion `search.py` document's Design keeps a `[Truncated — ...]` trailer for the truncated
   case; only the *count* wording inside the header/trailer changes, not whether the word
   "Truncated" appears at all.

## Implementation

### Target file

`tests/test_mdq_search_modes.py`

### Procedure

1. `test_default_limit_from_config` (lines 67-76): re-verify against the implemented wording;
   likely no change needed (see Assumption 1). If the implementer's final untruncated-case
   wording differs from `"{matched_count} found"`, update the assertion accordingly — e.g. if it
   becomes `"3 matched"` instead of `"3 found"`, change the substring to match.
2. `test_request_override_below_cap_is_honored` (lines 78-91): replace
   ```python
   assert "Truncated" in result
   assert "5 found" in result
   ```
   with an assertion that both the matched count (5) and shown count (2) are discoverable in the
   text without asserting one single exact phrase, e.g.:
   ```python
   assert "Truncated" in result
   assert "5" in result  # matched_count
   assert "2" in result  # shown_count
   ```
3. `test_request_override_above_cap_is_bounded` (lines 93-106): current test only asserts
   `"Truncated" in result`; optionally strengthen for symmetry by also asserting the matched
   (3) and shown (2) counts are both present, matching the pattern established in step 2:
   ```python
   assert "Truncated" in result
   assert "3" in result  # matched_count
   assert "2" in result  # shown_count
   ```

### Method

Targeted assertion-string edits inside three existing test method bodies — no change to fixture
setup, indexing calls, or request construction in any of the three tests; only the final
`assert` line(s) checking rendered text content change.

### Details

- Do not weaken the tests' original intent per plan Assumption 4: each test must still prove
  (a) default limit is honored when no override is given, (b) a request override below the
  config cap is honored, (c) a request override above the config cap is still bounded by the
  config cap. The assertion changes here only adapt to new wording, not new behavior being
  tested.
- If the implementer chooses exact wording during implementation (per companion `search.py`
  document's Option A/B choice), prefer to keep these assertions as loose substring checks (as
  drafted above) rather than pinning a single exact string — this avoids a second round of test
  churn if the wording is refined after initial implementation.
- Re-run this file together with the new `tests/test_mdq_search_limits.py` and
  `tests/test_mdq_search_counts.py` (companion documents) since all three exercise overlapping
  `search_docs()`/`_search_docs_structured()` code paths — a passing run across all three is the
  strongest signal the count/limit rework is internally consistent.

## Validation plan

| Check | Command | Expected |
|---|---|---|
| Assertions updated | `git diff tests/test_mdq_search_modes.py` | only `TestResultLimitBehavior`'s assertion lines changed; no fixture/setup changes |
| Lint | `uv run ruff check tests/test_mdq_search_modes.py` | 0 errors |
| Type check | `uv run mypy tests/test_mdq_search_modes.py` | no new errors |
| Targeted run | `uv run pytest tests/test_mdq_search_modes.py -v` | all pass (after companion `search.py` code change lands) |
| No intent regression | Manual: confirm each of the 3 `TestResultLimitBehavior` tests still fails if `search.py`'s limit-honoring logic itself is reverted (not just the wording) | each test still exercises real limit-bounding behavior, not only string matching |
| Combined run | `uv run pytest tests/test_mdq_search_modes.py tests/test_mdq_search_limits.py tests/test_mdq_search_counts.py tests/test_mdq_service.py -v` | all pass |
