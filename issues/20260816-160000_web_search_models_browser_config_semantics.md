# Clarify 0-vs-missing semantics for `browser_*` config fields in `web_search_models.py`

## Priority
Low

## Summary
`scripts/mcp_servers/web_search/web_search_models.py`'s `WebSearchConfig.from_dict` parses
`browser_max_response_kb`/`browser_timeout_sec` (and similar) via an `int(d.get(key) or default)`
idiom. Because `0` is falsy in Python, a TOML value of `browser_max_response_kb = 0` would
silently fall back to the default (e.g. 256) rather than being treated as an explicit, intentional
zero.

## Reason for Change
Found during a `prompts/04_refactor.md` cycle on `web_search_models.py` (2026-08-16). Not
implemented there because tightening `0`-vs-missing semantics changes what counts as "absent" vs.
"explicitly zero" for these fields — a config-loading behavior change visible to ops/TOML
authors, not a pure refactor.

## Implementation Intent
Decide whether `0` should be treated as a valid, explicit override (requiring `d.get(key) is None`
rather than falsy-check) or whether `0` is genuinely never a sensible value for these fields (in
which case the current behavior may be intentional and this issue can be closed as "no action").
If changing: replace the `or default` idiom with an explicit `is None` check for these two fields
specifically (do not blanket-change every `or default` usage in this file without the same
per-field review).

## Target Files or Areas
- `scripts/mcp_servers/web_search/web_search_models.py` (`WebSearchConfig.from_dict`,
  `browser_max_response_kb`, `browser_timeout_sec` fields)

## Required Changes
- Determine whether `0` is a sensible explicit value for `browser_max_response_kb`/
  `browser_timeout_sec` (e.g. does `timeout_sec=0` mean "no timeout" or "instant timeout" in the
  consuming code, `search_provider.py`'s `fetch_browser`?).
- If `0` should be honored: change `int(d.get(key) or default)` to
  `int(d.get(key)) if d.get(key) is not None else default` (or equivalent) for the affected
  fields only.
- Add a characterization test asserting `browser_max_response_kb: 0` in the source dict produces
  `0` in the resulting config, not the default.

## Acceptance Criteria
- Explicit `0` values for the affected fields are either confirmed-intentionally-defaulted
  (issue closed, no code change) or honored as `0` (code changed, new test added).
- All other `WebSearchConfig` fields' current fallback behavior is unchanged.

## Testing Expectations
`tests/mcp_servers/web_search/test_web_search_models.py` full suite; new test for the `0`-value
case if the behavior is changed.

## Documentation Impact
None expected unless `config/web_search_mcp_server.toml`'s example/comments document the
fallback semantics — update if so.

## Out of Scope
- Do not change the `or default` idiom for any other field in this file without the same
  per-field sensibility review.

## AI Implementation Instruction
Check how `browser_max_response_kb=0`/`browser_timeout_sec=0` would behave downstream in
`search_provider.py`'s `fetch_browser` before deciding whether `0` is a meaningful override —
this determines whether any code change is warranted at all.
