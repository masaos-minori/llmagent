# Implementation procedure: `tests/test_tool_server_layer_consistency.py` (add registry-vs-live-`/v1/tools` drift case for `search_web`)

Source plan: `plans/20260719-202346_plan.md`, Implementation step Phase 3 / Design §3.

No prior implementation doc exists for this exact filename (`grep -rl`/`ls | grep -F` over
`implementations/` and `implementations/done/` returns no hits). This is a new document.

## Goal

Add a focused test to `tests/test_tool_server_layer_consistency.py` exercising
`shared.tool_routing_validation.validate_routing_against_live()` directly for `search_web`, using a
stubbed `live_tool_lists` dict (per UNK-02's resolved default: stubbed unit test, not a live HTTP
integration test), asserting the function correctly reports `search_web` as missing from live
discovery when the stub omits it, and reports no drift when the stub matches reality.

## Scope

**In scope**
- One new small test (function or class), added to `tests/test_tool_server_layer_consistency.py`,
  scoped to `search_web`/`web_search` only — **not** a generalization of the existing
  `_SERVERS`-parametrized matrix (verified: that matrix covers all 8 registry keys for
  schema/dispatch/registry consistency, a different, already-adequate set of checks; this plan's
  Design §3 explicitly scopes the new live-drift case to `search_web` only, not all 8 servers).
- Two stub scenarios per Design §3: (a) `live_tool_lists={"web_search": ["search_web"]}` (matches
  reality — asserts empty drift dict), and (b) a deliberately-broken variant, e.g.
  `{"web_search": ["other_tool"]}` (asserts `search_web` is reported missing from live discovery).
- Explicit test docstring stating this validates `validate_routing_against_live()` directly and
  that the function is **not currently wired into agent startup** (per the plan's own Risks table
  entry on this point, and the plan's Scope's explicit out-of-scope note on wiring
  `validate_all_routing()`/`validate_routing_against_live()` into `agent/startup.py`).

**Out of scope**
- Extending the `_SERVERS` dict/parametrized tests (`test_schema_subset_of_dispatch_table`, etc.)
  to include a live-discovery dimension for all 8 servers — out of scope per the plan (search_web
  only).
- A live-HTTP-integration-style test that starts the actual web_search MCP server and hits
  `/v1/tools` — explicitly rejected by UNK-02's resolution (stubbed unit test is the chosen
  default; no established live-HTTP test pattern exists in this repo per the plan's own
  investigation).
- Wiring `validate_routing_against_live()`/`validate_all_routing()` into `agent/startup.py` — out of
  scope per the plan's Scope section; this test exercises the function directly only.

## Assumptions

1. Verified directly, `shared/tool_routing_validation.py::validate_routing_against_live()`
   (lines 38-59): signature is
   `validate_routing_against_live(registry: ToolRegistry | None = None, live_tool_lists: dict[str, list[str]] | None = None) -> dict[str, list[str]]`.
   It defaults `registry` to `get_registry()` (the real, populated registry) if not passed, and
   returns `{}` immediately if `live_tool_lists is None`. Internally it calls
   `registry.validate_live_tools_match(server_key, tool_names)` per server_key in the passed dict —
   confirmed this method exists on `ToolRegistry` (used elsewhere in
   `tests/test_tool_registry.py`, e.g. `test_no_drift_when_live_matches_registry`,
   `test_tool_in_live_not_in_registry`, verified at lines 85, 100 of that file).
2. Using the **real** registry (`get_registry()`, default) rather than a synthetic one is
   deliberate here — the whole point of this test is confirming the real `search_web`
   registration behaves correctly against a stubbed live-discovery map, complementing
   `tests/test_tool_registry.py`'s already-existing synthetic-registry unit tests for the same
   function (which use `MagicMock`/hand-built registries, not the real one — verified those tests
   do not specifically exercise `search_web`/`web_search`).
3. No existing test in this repo calls `validate_routing_against_live()` with a `web_search`-keyed
   stub specifically (verified: `grep -n "web_search" tests/test_tool_registry.py` and
   `tests/test_startup_routing_drift.py` return no hits for this function's tests) — confirming
   this is genuinely new coverage, not a duplicate of existing generic tests for the same function.

## Implementation

### Target file

`tests/test_tool_server_layer_consistency.py` (existing file, 403 lines per the plan's Affected
Areas table — verified still current via `wc -l`; new test added near the end, after the existing
`test_serial_tools_flagged_requires_serial` parametrized test, or as a small standalone class).

Related existing files this test imports from:
- `scripts/shared/tool_routing_validation.py::validate_routing_against_live` (lines 38-59).
- `scripts/shared/tool_registry.py::get_registry` (already imported in this file, verified in the
  existing import block).

### Procedure

1. Add an import of `validate_routing_against_live` from `shared.tool_routing_validation`
   alongside this file's existing `from shared.tool_registry import get_registry` import.
2. Add a new test function (or small class, matching this file's existing mostly-function style
   for the parametrized tests) with two cases:
   - `test_search_web_live_drift_detected_when_missing` — call
     `validate_routing_against_live(live_tool_lists={"web_search": ["other_tool"]})`; assert the
     returned dict has a `"web_search"` key whose message list mentions `search_web` (e.g. contains
     the substring `"search_web"`).
   - `test_search_web_no_live_drift_when_matching` — call
     `validate_routing_against_live(live_tool_lists={"web_search": ["search_web"]})`; assert the
     returned dict is `{}` (no drift).
3. Add a docstring on the new test(s) or a module-level comment near them, explicitly noting: this
   validates `validate_routing_against_live()` directly; it is not currently invoked at agent
   startup (per the plan's Risks table mitigation requirement).

### Method

Pseudocode only (per `skills/python-design/SKILL.md` — no production code blocks):

```
from shared.tool_routing_validation import validate_routing_against_live

# NOTE: validate_routing_against_live() is exercised directly here. It is not
# currently wired into agent startup (see plans/20260719-202346_plan.md Scope
# — wiring it into agent/startup.py is explicitly out of scope for this plan).

def test_search_web_live_drift_detected_when_missing() -> None:
    drift = validate_routing_against_live(live_tool_lists={"web_search": ["other_tool"]})
    assert "web_search" in drift
    assert any("search_web" in msg for msg in drift["web_search"])


def test_search_web_no_live_drift_when_matching() -> None:
    drift = validate_routing_against_live(live_tool_lists={"web_search": ["search_web"]})
    assert drift == {}
```

### Details

- Uses the real, default `get_registry()` (via `validate_routing_against_live`'s own default
  parameter) rather than constructing a synthetic `ToolRegistry` — this deliberately differs from
  `tests/test_tool_registry.py`'s synthetic-registry unit tests for the same function, so together
  the two files cover both "function logic in isolation" (existing) and "function behavior against
  the real, currently-deployed `search_web` registration" (this new addition).
- Do not add this case into the `_SERVERS`-parametrized matrix — it tests a different axis (live
  discovery, not schema/dispatch/registry triple-consistency) and is deliberately scoped to
  `search_web` only per the plan, so a standalone test (or small dedicated class) is clearer than
  forcing it into the existing per-server parametrization.
- No production code or config is modified by this item; purely additive test coverage.

## Validation plan

| Check | Command | Target |
|---|---|---|
| New tests | `uv run pytest tests/test_tool_server_layer_consistency.py -v -k "live"` | both new cases pass |
| Full file | `uv run pytest tests/test_tool_server_layer_consistency.py -v` | all existing + new cases pass, no regressions |
| Format/lint | `uv run ruff format tests/ && uv run ruff check tests/` | 0 errors |
| Type check | `uv run mypy scripts/` | no new errors |
| Regression | `uv run pytest tests/test_tool_registry.py -v` | no regressions (synthetic-registry tests for the same function still pass) |
| Full suite | `uv run pytest -v` | no new failures |
| Diff-scoped coverage | `uv run coverage run -m pytest tests/ && uv run coverage xml && uv run diff-cover coverage.xml --compare-branch=main --fail-under=90` | ≥ 90% on changed lines |
