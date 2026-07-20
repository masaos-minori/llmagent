# Implementation procedure: `tests/test_runtime_tool_routing_integration.py` (rebaseline for no-fallback contract + resolver-identity preservation)

Source plan: `plans/done/20260720-134821_plan.md`, Implementation step Phase 1 (test rebaseline,
resolving UNK-03) + Phase 2 step "Apply the Phase 1 test rewrites."

No prior implementation doc targets this filename (content-grep for
"test_runtime_tool_routing_integration" across `implementations/` and `implementations/done/` returns
no hits). This is a new document.

## Goal

Rewrite `tests/test_runtime_tool_routing_integration.py` so it (1) no longer asserts any
legacy-`ToolRegistry`-fallback resolution when `runtime_registry` is `None` or empty, and (2) asserts
that `ToolExecutor.set_runtime_registry()` **preserves** resolver identity (mutates the existing
`ToolRouteResolver` in place) rather than replacing it — the opposite of what the current test
asserts.

## Scope

**In scope**: `tests/test_runtime_tool_routing_integration.py` only (288 lines, 3 classes, 18 test
methods — full file read and enumerated below).

**Out of scope**: `tests/test_route_resolver.py` — separate doc. `TestBrowserToolsConfigDependentMigration`
(lines 261-288, 3 async tests: `test_browser_tools_tool_list_contains_config_dependent`,
`test_browser_tools_no_requires_config_in_tool_list`, `test_browser_fetch_tool_has_config_dependent_true`)
— unrelated to routing-authority fallback (tests `config_dependent` schema field migration); confirmed
by reading the class in full — **no change needed**, not touched by this doc.

## Assumptions — full test-by-test classification (resolves UNK-03)

Read the entire file directly (offset 1-288). The plan's Affected Areas table names 5 tests as
"rewrite/remove" plus 1 "rename." A full read confirms this list is accurate for this file (unlike
`test_route_resolver.py`, where the plan's sample undercounted) but adds two more tests whose bodies
also depend on legacy fallback that the plan did not explicitly name:

| Test | Line | Current behavior | Post-plan disposition |
|---|---|---|---|
| `test_runtime_registry_wins_when_both_available` | 87 | `runtime_registry` provided; resolves via it | **No change** — already exercises the sole-authority path since `runtime_registry` is present and covers the queried tool |
| `test_legacy_fallback_when_runtime_unavailable` | 94 | No `runtime_registry`; resolves `read_text_file` via legacy fallback | **DELETE** (named in plan) — this test's entire premise (fallback exists) is now false; there is no replacement assertion to salvage, since "no registry → `ValueError`" is already covered elsewhere (e.g. `test_unknown_tool_raises_with_runtime_only`, adapted) |
| `test_runtime_only_resolve` | 100 | `runtime_registry` provided, no legacy dependency | **No change** |
| `test_unknown_tool_raises_with_runtime_only` | 107 | `runtime_registry` provided; unknown tool raises | **No change** |
| `test_mixed_tools_resolve_correctly` | 115 | `runtime_registry` provided (covers `browser_fetch` only) **and** asserts `resolve("read_text_file") == "file_read"` via `configs = {"file_read": _http(...)}` | **BREAKS — not named in plan.** `read_text_file` is not in the `runtime_registry` built by `_make_runtime_registry()` (which only registers `browser_fetch`); today it resolves via legacy fallback. Must add `read_text_file` to the `runtime_registry` fixture (e.g. extend `_make_runtime_registry()` or build a combined registry inline) or drop that half of the assertion |
| `test_runtime_none_does_not_break_resolve` | 123 | `runtime_registry=None` explicitly; resolves `read_text_file` via legacy fallback | **BREAKS — not named in plan.** With no fallback, `runtime_registry=None` now means `resolve("read_text_file")` raises `ValueError`, not resolves to `"file_read"`. Rewrite the test's assertion to `pytest.raises(ValueError, ...)`, and rename to reflect the new meaning (e.g. `test_runtime_none_raises_for_all_tools`), since the current name/docstring ("does not break resolve") no longer matches — passing `None` now means zero routable tools |
| `test_strict_mode_error_message_mentions_any_registry` | 129 | Asserts message contains "any registry" | **BREAKS (named in plan)** — update `match=` to whatever new message `_raise_strict_error()` produces (keep in lockstep with the same-named test in `test_route_resolver.py`, per that doc's step 3) |
| `test_warn_on_missing_logs_warning_for_unknown_tool` | 139 | `runtime_registry` provided; unknown tool | **No change** |
| `test_runtime_empty_registry_resolves_via_legacy` | 149 | Empty `RuntimeToolRegistry()`; resolves `read_text_file` via legacy fallback | **DELETE or REWRITE (named in plan)** — an empty `RuntimeToolRegistry` now behaves identically to `runtime_registry=None`: `ValueError` for every tool. Either delete (redundant with the rewritten `test_runtime_none_raises_for_all_tools`) or rewrite to assert `ValueError` and rename (e.g. `test_empty_runtime_registry_raises_for_all_tools`) |
| `test_runtime_registry_resolves_all_its_tools` | 156 | `runtime_registry` covers `tool_a`/`tool_b`; no legacy dependency | **No change** |
| `test_runtime_registry_set_runtime_registry_replaces_resolver` | 188 | Asserts `ex._resolver is not resolver_before` (identity **changes**) after `set_runtime_registry()`; also asserts `ex._resolver.resolve("read_text_file") == "file_read"` (line 199, "Legacy fallback still works") | **RENAME + REWRITE (named in plan)** — per the `tool_executor.py` doc, `set_runtime_registry()` now mutates in place. Rename to e.g. `test_set_runtime_registry_preserves_resolver_identity`; change the core assertion to `ex._resolver is resolver_before`; **delete** the "Legacy fallback still works" assertion (line 199) entirely — there is no legacy fallback to demonstrate, and `read_text_file` is not registered in the `runtime_registry` this test constructs, so that line would raise `ValueError`, not return `"file_read"`, once the fallback is gone |
| `test_runtime_mapped_tool_is_mapped` | 210 | `runtime_registry` provided; `browser_fetch` known | **No change** — but note (pre-existing, unrelated gap): this test body (lines 210-217) contains **no assertions at all** — it only constructs the resolver inside a `caplog.at_level` block and returns. This is a pre-existing test gap, not introduced or worsened by this plan; out of scope to fix here, flagged for visibility only |
| `test_all_unmapped_when_both_registries_miss` | 219 | No `runtime_registry`; `totally_unknown_tool` correctly unmapped in both current and post-plan worlds | **Likely no assertion change needed (plan names it as a rewrite candidate)** — verify at implementation time: since the tool is absent from every registry either way, "0/1 tools mapped" holds unmodified; only the docstring's "both registries" phrasing needs updating to avoid implying two registries are still consulted |
| `test_runtime_only_tool_is_mapped` | 233 | `runtime_registry` provided; `browser_fetch` known | **No change** |
| `test_both_registries_count_as_mapped` | 244 | No `runtime_registry` passed to the resolver's `configs`/`known_tools`, but relies on `read_text_file` resolving via legacy fallback inside `_log_routing_coverage()` to reach "2/2 tools mapped" | **BREAKS (named in plan)** — once `_log_routing_coverage()` only checks `_lookup_runtime_registry()`, `read_text_file` (not in `runtime_reg`, which only has `browser_fetch`) becomes unmapped, so the count becomes "1/2," not "2/2." Extend the `runtime_reg` fixture to also register `read_text_file`, or change the expected count/message and rename (e.g. `test_runtime_registry_mapped_tools_count_correctly`) |
| 3 async `TestBrowserToolsConfigDependentMigration` tests | 264-288 | Unrelated to routing fallback | **No change** — out of scope, confirmed by full read |

## Implementation

### Target file

`tests/test_runtime_tool_routing_integration.py`

### Procedure

1. Delete `test_legacy_fallback_when_runtime_unavailable` (line 94) outright.
2. Rewrite `test_runtime_none_does_not_break_resolve` (line 123): change body to
   `with pytest.raises(ValueError, match="Unknown tool"): resolver.resolve("read_text_file")`;
   rename to `test_runtime_none_raises_for_all_tools`; update docstring.
3. Rewrite or delete `test_runtime_empty_registry_resolves_via_legacy` (line 149): if kept, rename to
   `test_empty_runtime_registry_raises_for_all_tools` and change the assertion to
   `pytest.raises(ValueError, ...)`; if the resulting test would be a near-duplicate of the rewritten
   `test_runtime_none_raises_for_all_tools`, delete this one instead and note the removal.
4. Update `test_strict_mode_error_message_mentions_any_registry` (line 129): change
   `match="any registry"` to match the new message text from the `route_resolver.py` doc — keep this
   test's wording synchronized with its near-duplicate in `tests/test_route_resolver.py`.
5. Fix `test_mixed_tools_resolve_correctly` (line 115): extend the `_make_runtime_registry()` call
   (or build an ad hoc registry inline for this test) to also register `read_text_file` → `file_read`,
   so both assertions on lines 120-121 remain valid without a legacy fallback.
6. Rename and rewrite `test_runtime_registry_set_runtime_registry_replaces_resolver` (line 188) to
   `test_set_runtime_registry_preserves_resolver_identity`:
   - Change `assert ex._resolver is not resolver_before` to `assert ex._resolver is resolver_before`.
   - Delete the "Legacy fallback still works" assertion (`ex._resolver.resolve("read_text_file") ==
     "file_read"`, line 199) — replace with, if desired, an assertion that a tool *not* in the new
     `runtime_reg` (e.g. `read_text_file`) now raises `ValueError`, demonstrating the sole-authority
     contract explicitly.
   - Keep the `ex._resolver.resolve("browser_fetch") == "browser"` assertion (line 197) — still valid,
     now demonstrating that the *mutated* resolver picks up the new registry's tools.
7. Fix `test_both_registries_count_as_mapped` (line 244): extend `_make_runtime_registry()`'s tool set
   (or build inline) to also cover `read_text_file`, preserving the "2/2 tools mapped" assertion; or
   rename to `test_runtime_registry_mapped_tools_count_correctly` and adjust the expected count to
   "1/2" if the fixture is left as-is. Prefer extending the fixture — it keeps the test's original
   intent ("multiple tools all mapped") rather than degrading it to a lesser assertion.
8. For `test_all_unmapped_when_both_registries_miss` (line 219): update only the docstring
   ("Tool absent from both registries is UNMAPPED" → "Tool absent from RuntimeToolRegistry is
   UNMAPPED"); verify the assertion body needs no change.
9. Leave `TestBrowserToolsConfigDependentMigration` untouched.

### Method

Test-only edits; no production code touched by this doc. Reuse the file's existing
`_make_runtime_registry()` / `build_runtime_tool()` / `_make_executor()` helpers — extend them or add
a second small helper (e.g. `_make_runtime_registry_with(*, extra: dict[str, str] | None = None)`) if
multiple tests need `read_text_file` added to the fixture, to avoid duplicating the
`build_runtime_tool(...)` call verbatim in three places.

### Details

- After this rewrite, grep the file for `"file_read"` value expectations paired with a
  `runtime_registry` that does not register a matching tool — that pattern is the exact signature of
  a latent fallback dependency; the three tests found this way
  (`test_mixed_tools_resolve_correctly`, `test_runtime_registry_set_runtime_registry_replaces_resolver`,
  `test_both_registries_count_as_mapped`) are all listed above.
- `_make_executor()` (module helper, lines 45-55) constructs a real `ToolExecutor` — the
  resolver-identity test (item 6) depends on `ToolExecutor.__init__` still constructing exactly one
  `ToolRouteResolver` (per the companion `tool_executor.py` doc, unchanged) for `resolver_before` to
  be meaningfully compared against `ex._resolver` after the call.

## Validation plan

| Check | Command | Expected |
|---|---|---|
| Targeted unit tests | `uv run pytest tests/test_runtime_tool_routing_integration.py -v` | All tests pass (18 total, adjusted for 1-2 deletions); resolver-identity test asserts `is`, not `is not` |
| Full suite | `uv run pytest` | No new failures |
| Diff coverage | `uv run coverage run -m pytest tests/ && uv run coverage xml && uv run diff-cover coverage.xml --compare-branch=master --fail-under=90` | ≥ 90% on changed lines |
| Format/lint | `uv run ruff format tests/test_runtime_tool_routing_integration.py && uv run ruff check tests/test_runtime_tool_routing_integration.py` | 0 errors |
| Cross-file consistency | manual diff of `match=` strings in both files' `test_strict_mode_error_message_mentions_any_registry` | Identical expected substring |
