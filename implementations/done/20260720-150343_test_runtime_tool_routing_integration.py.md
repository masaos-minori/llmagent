# Implementation procedure: `tests/test_runtime_tool_routing_integration.py` (browser_fetch merge fixtures)

Source plan: `plans/20260720-135137_plan.md`, Implementation step 10; Affected areas row for this
file ("update `TestBrowserToolsConfigDependentMigration` and other `browser_fetch`/
`server_key="browser"` fixtures to import `mcp_servers.web_search.web_search_tools` and expect
`server_key="web_search"`").

A prior doc for this exact filename already exists at
`implementations/20260720-142433_test_runtime_tool_routing_integration.py.md` (still pending, not
in `implementations/done/`) — read in full. It targets a **different, unrelated** plan
(`plans/done/20260720-134821_plan.md`, "RuntimeToolRegistry sole routing authority" — removing the
legacy `ToolRegistry` fallback entirely from `ToolRouteResolver.resolve()`). That doc explicitly
states (its own Scope section): "`TestBrowserToolsConfigDependentMigration` ... unrelated to
routing-authority fallback ... **no change needed**, not touched by this doc." So it does not cover
this plan's concern (relocating `browser_fetch`'s `server_key` from `"browser"` to `"web_search"`
and its import path from `mcp_servers.browser.browser_tools` to
`mcp_servers.web_search.web_search_tools`). No overlap — this is a new, additional document for the
same filename, as expected when two independent plans touch one file for different reasons.

**Sequencing note**: both docs touch overlapping test bodies (e.g. `_make_runtime_registry()`,
`test_runtime_registry_set_runtime_registry_replaces_resolver`). Whichever implementation lands
second must re-read the file's then-current state rather than blindly re-applying a stale line-based
procedure — both docs' Procedure sections are written against the file's state as of this design
cycle (2026-07-20, 288 lines) and may conflict on exact line numbers if applied out of order. This
doc calls out every place its concern touches the same lines the other doc touches, in the
Assumptions below.

## Goal

Update every `browser_fetch`/`server_key="browser"` fixture and the
`TestBrowserToolsConfigDependentMigration` class so they reflect `browser_fetch` now routing to
`server_key="web_search"` and its `TOOL_LIST` entry living in
`mcp_servers.web_search.web_search_tools` instead of the deleted `mcp_servers.browser.browser_tools`.

## Scope

**In scope** (full file read, 288 lines, confirmed current state):
- `_make_runtime_registry()` (lines 58-78): `server_key="browser"` (line 62) → `"web_search"`.
- `test_runtime_registry_wins_when_both_available` (lines 87-92): `configs = {"browser": _http(...)}`
  (line 90) → `{"web_search": _http(...)}`; `resolver.resolve("browser_fetch") == "browser"`
  (line 92) → `== "web_search"`.
- `test_runtime_only_resolve` (lines 100-105): `resolver.resolve("browser_fetch") == "browser"`
  (line 105) → `== "web_search"`.
- `test_mixed_tools_resolve_correctly` (lines 115-121): `resolver.resolve("browser_fetch") ==
  "browser"` (line 120) → `== "web_search"`.
- `test_runtime_registry_set_runtime_registry_replaces_resolver` (lines 188-199):
  `ex._resolver.resolve("browser_fetch") == "browser"` (line 197) → `== "web_search"`.
- `TestBrowserToolsConfigDependentMigration` (lines 261-288): import path (3 occurrences, lines
  266, 276, 285) `from mcp_servers.browser.browser_tools import TOOL_LIST` →
  `from mcp_servers.web_search.web_search_tools import TOOL_LIST`; plus the assertion-generalization
  fix described in Assumption 3 below.

**Out of scope**: `test_legacy_fallback_when_runtime_unavailable`,
`test_runtime_none_does_not_break_resolve`, `test_strict_mode_error_message_mentions_any_registry`,
`test_runtime_empty_registry_resolves_via_legacy`, `test_both_registries_count_as_mapped` and other
tests whose subject is the legacy-`ToolRegistry`-fallback mechanism itself, not `browser_fetch`'s
identity — these belong entirely to the other, already-documented plan
(`implementations/20260720-142433_...md`) and are not touched here. `test_runtime_mapped_tool_is_mapped`
/ `test_runtime_only_tool_is_mapped` (lines 210-217, 233-242) use `known_tools = frozenset({"browser_fetch"})`
and assert on mapped-*count* only (e.g. "1/1 tools mapped"), never on the resolved `server_key`
value — no change needed for this plan's concern (the tool name `"browser_fetch"` itself is
unchanged by the merge; only its `server_key` changes, and these two tests never assert a
`server_key`).

## Assumptions

1. `_make_runtime_registry()`'s `build_runtime_tool(name="browser_fetch", server_key="browser",
   ...)` (lines 60-77) is the single shared fixture factory used by 5+ tests across both this doc's
   scope and the other pending doc's scope — changing `server_key="browser"` to
   `server_key="web_search"` here is the one edit that propagates correctly to every test using this
   helper (including tests this doc does not otherwise touch, e.g.
   `test_unknown_tool_raises_with_runtime_only`, which uses the fixture but never asserts on the
   resolved key — unaffected either way).
2. `test_runtime_registry_set_runtime_registry_replaces_resolver` (lines 188-199) is also targeted by
   the other pending doc (which renames it and changes its `is not`/`is` assertion on resolver
   identity, per that doc's Procedure step 6). This doc's concern (line 197's `"browser"` →
   `"web_search"`) is orthogonal — whichever doc's edit lands first, the second implementer must
   re-read the test body's then-current shape rather than apply a stale diff; both edits are
   compatible (one changes the resolver-identity assertion, the other changes the expected
   `server_key` string) and can be applied together without conflict if done thoughtfully.
3. `TestBrowserToolsConfigDependentMigration`'s first two tests (lines 264-281) iterate **every**
   entry in `TOOL_LIST` asserting `"config_dependent" in tool` / `"requires_config" not in tool`.
   This assumption silently broke by the merge: `mcp_servers.web_search.web_search_tools.TOOL_LIST`
   now contains **two** entries — `search_web` (per the `web_search_tools.py` doc, has no
   `config_dependent` key at all, confirmed by direct read of that file) and `browser_fetch` (has
   `config_dependent: True`). Iterating the whole list and asserting `"config_dependent" in tool`
   for `search_web` would **fail** post-merge. This is a genuine cross-file consequence of the
   merge, not addressed by the plan's brief Affected-areas note — it must be fixed here, not
   silently left broken.

## Implementation

### Target file

`tests/test_runtime_tool_routing_integration.py`

### Procedure

1. In `_make_runtime_registry()` (line 62): `server_key="browser"` → `server_key="web_search"`.
2. In `test_runtime_registry_wins_when_both_available` (lines 90, 92): change
   `configs = {"browser": _http("http://127.0.0.1:8001")}` to
   `configs = {"web_search": _http("http://127.0.0.1:8001")}`; change
   `resolver.resolve("browser_fetch") == "browser"` to `== "web_search"`.
3. In `test_runtime_only_resolve` (line 105): `resolver.resolve("browser_fetch") == "browser"` →
   `== "web_search"`.
4. In `test_mixed_tools_resolve_correctly` (line 120): same substitution.
5. In `test_runtime_registry_set_runtime_registry_replaces_resolver` (line 197): same substitution
   (leave line 195's resolver-identity assertion and line 199's "Legacy fallback still works" line
   alone — those belong to the other pending doc's concern; if that doc has already landed and
   removed/renamed this test, re-derive the equivalent edit against its new shape instead of
   reintroducing a stale `"browser"` string).
6. In `TestBrowserToolsConfigDependentMigration`, rewrite all 3 tests:
   - Change every `from mcp_servers.browser.browser_tools import TOOL_LIST` to
     `from mcp_servers.web_search.web_search_tools import TOOL_LIST` (lines 266, 276, 285).
   - Rewrite `test_browser_tools_tool_list_contains_config_dependent` and
     `test_browser_tools_no_requires_config_in_tool_list` to filter to the `browser_fetch` entry
     specifically (matching what `test_browser_fetch_tool_has_config_dependent_true` already does
     at line 287), e.g.:
     ```
     fetch_tool = next(t for t in TOOL_LIST if t["name"] == "browser_fetch")
     assert "config_dependent" in fetch_tool
     ```
     rather than iterating the whole (now 2-tool) `TOOL_LIST` — per Assumption 3, the blanket
     iteration is no longer a valid invariant once `search_web` shares the list.
   - Consider renaming the class/module comment (line 4: "...and browser tools config_dependent
     migration") to reflect that `TOOL_LIST` is now `web_search`'s combined list, not
     browser-exclusive — a documentation-quality nicety, not a hard requirement.

### Method

Direct string substitutions (`"browser"` → `"web_search"` for `server_key`/dict-key/assert values;
import-path rewrite) plus a targeted assertion-scope fix for the one test class whose blanket
iteration assumption the merge invalidates. No new fixtures/helpers introduced.

### Details

- After this edit, `grep -n 'server_key="browser"' tests/test_runtime_tool_routing_integration.py`
  and `grep -n 'mcp_servers.browser' tests/test_runtime_tool_routing_integration.py` both return no
  output.
- `_http("http://127.0.0.1:8001")`-style URL literals are arbitrary test fixtures, not real
  endpoints — no change needed to the port numbers themselves, only the dict key naming the server.

## Validation plan

| Check | Command | Target |
|---|---|---|
| Targeted unit tests | `uv run pytest tests/test_runtime_tool_routing_integration.py -v` | all pass; every `browser_fetch` resolution assertion expects `"web_search"`; `TestBrowserToolsConfigDependentMigration` imports from `mcp_servers.web_search.web_search_tools` and passes with the 2-tool `TOOL_LIST` |
| Full suite | `uv run pytest -v` | no new failures |
| No stale references | `grep -n "mcp_servers.browser\|server_key=\"browser\"" tests/test_runtime_tool_routing_integration.py` | 0 matches |
| Cross-doc consistency | manual read after both this doc and `implementations/20260720-142433_...md` have been applied | no leftover conflicting edits on shared lines (e.g. `test_runtime_registry_set_runtime_registry_replaces_resolver`) |
