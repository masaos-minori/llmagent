# Implementation procedure: `tests/test_web_search_tool_schema.py` (agent.toml vs TOOL_LIST parameter parity)

Source plan: `plans/20260719-202346_plan.md`, Implementation step Phase 2 / Design §5.

**Exact-filename collision, checked and confirmed NOT the same task.** A prior doc exists for
this filename: `implementations/20260720-080149_test_web_search_tool_schema.py.md` (sourced from
a sibling plan, `plans/20260719-192933_plan.md`, "Validate WebSearchConfig and align search_web
input schema"). Opened and read in full. That doc's scope is a *different* schema-drift axis:
numeric/string constraint equality between `web_search_tools.py::TOOL_LIST`'s `inputSchema`
(`minLength`/`maxLength`/`minimum`/`maximum`) and `web_search_models.py::SearchRequest`'s Pydantic
field constraints (`min_length`/`max_length`/`ge`/`le`) — i.e., **TOOL_LIST vs. the Pydantic
model**. This plan's need (Design §5) is a *different* comparison: **`config/agent.toml`'s
`[[tool_definitions]]` parameter set vs. `TOOL_LIST`'s `inputSchema.properties`** — i.e., the
LLM-facing config definition vs. the MCP server's own schema, catching the `max_results`-missing-
from-`agent.toml` divergence this plan's Design §2 fixes. These are genuinely different test
concerns that happen to share a plausible filename; per the task's caution note, verified by
opening the doc rather than skipping on name match alone. Both tests can coexist in the same file
once implemented (same module, two independent test classes) — this doc covers only the
agent.toml-vs-TOOL_LIST half; the TOOL_LIST-vs-Pydantic-model half is out of scope here (already
covered by the sibling doc).

## Goal

Add test coverage (in the same `tests/test_web_search_tool_schema.py` file the sibling plan's
cycle also targets) asserting `config/agent.toml`'s `search_web` `[[tool_definitions]]` parameter
set is consistent with `web_search_tools.py::TOOL_LIST`'s `inputSchema.properties` for `search_web`
— written to fail against pre-Design-§2 `agent.toml` (proving it catches the `max_results` drift
class) and pass after Design §2's `max_results` addition lands.

## Scope

**In scope**
- New test case(s) comparing: `agent.toml`'s `search_web` tool-definition's
  `parameters.properties` keys and `parameters.required` array against `TOOL_LIST`'s `search_web`
  entry's `inputSchema.properties` keys and `inputSchema.required` array.
- Per Design §5: assert the `agent.toml` parameter *set* is a subset of (pre-fix) — becoming an
  equality check (post-fix, once both have `query` + `max_results`) — the `TOOL_LIST` parameter
  set.
- If the sibling plan's doc (`20260720-080149_test_web_search_tool_schema.py.md`) has already
  created this file by the time this item is implemented, this item's test class/functions are
  **added** to the existing file, not written as a separate competing file — both docs target the
  same physical file but different, non-overlapping test classes within it. If this item lands
  first, the sibling doc's tests get added to this same file later; either order is fine since the
  two test classes are independent (no shared fixtures required across them, though both import
  `TOOL_LIST` from the same module and could share that one import line).

**Out of scope**
- The `TOOL_LIST`-vs-`SearchRequest` (Pydantic model) constraint-equality tests — that is the
  sibling doc's (`20260720-080149_*`) responsibility; do not duplicate `minLength`/`maxLength`/
  `minimum`/`maximum` assertions here.
- Modifying `agent.toml` or `web_search_tools.py` themselves — those are separate items (this
  plan's own `implementations/20260720-090021_agent.toml.md`, and the sibling cycle's
  `web_search_tools.py` doc, respectively).

## Assumptions

1. Verified directly, `config/agent.toml` lines 400-413 (pre-fix): `search_web`'s
   `[[tool_definitions]]` block currently has only `query` in `parameters.properties` and
   `required = ["query"]`. Post this plan's Design §2 fix, it will also have `max_results` in
   `properties` (not in `required`).
2. Verified directly, `web_search_tools.py::TOOL_LIST` (lines 11-30): `search_web`'s entry has
   `inputSchema.properties` = `{query, max_results}`, `inputSchema.required` = `["query"]`. This is
   the fixed target the `agent.toml` comparison should converge to.
3. `config/agent.toml` must be parsed with `tomllib` (stdlib, matches the pattern already used in
   `tests/test_tool_registry.py::TestValidateRoutingAgainstRealConfig` — verified, that class reads
   `config/agent.toml` via `tomllib.load()` directly from the repo root path
   `Path(__file__).parent.parent / "config" / "agent.toml"`). This test should reuse that same
   real-file-reading pattern rather than mocking `agent.toml`'s content, so it exercises the actual
   deployed config, not a synthetic stand-in.
4. `[[tool_definitions]]` is a TOML array of tables; the `search_web` entry must be located by
   `name == "search_web"` (matching `[tool_definitions.function].name`), not by array index — same
   defensive lookup pattern the sibling doc uses for `TOOL_LIST` (locate by `name`, not index 0),
   since `agent.toml`'s `tool_definitions` array has many entries besides `search_web`.

## Implementation

### Target file

`tests/test_web_search_tool_schema.py` (new, or shared with the sibling doc's cycle if it lands
first — verified via `find . -name "test_web_search_tool_schema.py"` returning no results at
design time).

Related existing files this test reads/imports from:
- `config/agent.toml` — parsed via `tomllib`, `[[tool_definitions]]` array, `search_web` entry.
- `scripts/mcp_servers/web_search/web_search_tools.py::TOOL_LIST` (lines 11-30, verified) —
  `search_web` entry's `inputSchema`.

### Procedure

1. If the file does not yet exist, create it with a module docstring; if it exists (sibling doc's
   cycle landed first), add to it rather than overwriting.
2. Add a helper that loads `config/agent.toml` via `tomllib` from the repo-root-relative path and
   returns the `search_web` entry from `tool_definitions` (matched by
   `entry["function"]["name"] == "search_web"`).
3. Add a helper (or reuse the sibling doc's, if already present) that locates `search_web`'s
   `inputSchema` in `TOOL_LIST` by `name == "search_web"`.
4. Add test cases:
   - `test_agent_toml_search_web_properties_subset_of_tool_list` — every key in `agent.toml`'s
     `search_web.parameters.properties` also appears in `TOOL_LIST`'s `search_web.inputSchema.properties`
     (subset check; becomes equality once Design §2 lands both `query`+`max_results` on both sides).
   - `test_agent_toml_search_web_max_results_present` — explicit, named assertion that
     `"max_results"` is a key in `agent.toml`'s `search_web.parameters.properties` — this is the
     test written first against *pre-fix* `agent.toml` to confirm it fails (per the plan's Design
     §5 instruction to prove the test is not vacuous), then confirmed to pass after Design §2's
     `agent.toml` edit lands.
   - `test_agent_toml_search_web_max_results_not_required` — `"max_results"` is absent from
     `agent.toml`'s `search_web.parameters.required` array (optional-parameter invariant).
   - `test_agent_toml_search_web_required_matches_tool_list` — `agent.toml`'s
     `search_web.parameters.required` == `TOOL_LIST`'s `search_web.inputSchema.required`
     (both `["query"]`, unaffected by the `max_results` addition since it stays optional on both
     sides).

### Method

Pseudocode only (per `skills/python-design/SKILL.md` — no production code blocks):

```
"""tests/test_web_search_tool_schema.py
(this section) Drift tests between config/agent.toml's search_web tool
definition and web_search_tools.py::TOOL_LIST's inputSchema."""

import tomllib
from pathlib import Path

from mcp_servers.web_search.web_search_tools import TOOL_LIST


def _agent_toml_search_web() -> dict:
    path = Path(__file__).parent.parent / "config" / "agent.toml"
    with open(path, "rb") as f:
        cfg = tomllib.load(f)
    matches = [
        td["function"] for td in cfg["tool_definitions"]
        if td["function"]["name"] == "search_web"
    ]
    assert len(matches) == 1
    return matches[0]["parameters"]


def _tool_list_search_web_schema() -> dict:
    matches = [t for t in TOOL_LIST if t["name"] == "search_web"]
    assert len(matches) == 1
    return matches[0]["inputSchema"]


class TestAgentTomlVsToolListParity:
    def test_agent_toml_search_web_properties_subset_of_tool_list(self) -> None:
        agent_props = set(_agent_toml_search_web()["properties"])
        tool_list_props = set(_tool_list_search_web_schema()["properties"])
        assert agent_props <= tool_list_props

    def test_agent_toml_search_web_max_results_present(self) -> None:
        assert "max_results" in _agent_toml_search_web()["properties"]

    def test_agent_toml_search_web_max_results_not_required(self) -> None:
        assert "max_results" not in _agent_toml_search_web()["required"]

    def test_agent_toml_search_web_required_matches_tool_list(self) -> None:
        assert _agent_toml_search_web()["required"] == _tool_list_search_web_schema()["required"]
```

### Details

- Reads the *real* `config/agent.toml` (not a fixture/mock), matching the precedent in
  `tests/test_tool_registry.py::TestValidateRoutingAgainstRealConfig` — this is deliberate so the
  test exercises the actually-deployed config content, catching drift that a synthetic config
  fixture would mask.
- Keep this test class's assertions strictly about *agent.toml-vs-TOOL_LIST* parity — do not add
  Pydantic-model (`SearchRequest`) assertions here; that is the sibling doc's dedicated concern,
  avoiding duplicate/overlapping coverage between the two test classes in this same file.
- This file has no production-code counterpart to modify; purely additive, not part of
  `deploy/deploy.sh`'s copy list (tests/ is excluded per the plan's Affected Areas table).

## Validation plan

| Check | Command | Target |
|---|---|---|
| Written pre-fix | `uv run pytest tests/test_web_search_tool_schema.py -v` (against `agent.toml` before Design §2's edit) | `test_agent_toml_search_web_max_results_present` and the subset test fail, proving the test is not vacuous |
| Written post-fix | `uv run pytest tests/test_web_search_tool_schema.py -v` (after Design §2's `agent.toml` edit) | all new test cases pass |
| Format/lint | `uv run ruff format tests/ && uv run ruff check tests/` | 0 errors |
| Type check | `uv run mypy scripts/` | no new errors |
| Regression | `uv run pytest tests/test_tool_server_layer_consistency.py tests/test_tool_registry.py -v` | no regressions |
| Full suite | `uv run pytest -v` | no new failures |
| Diff-scoped coverage | `uv run coverage run -m pytest tests/ && uv run coverage xml && uv run diff-cover coverage.xml --compare-branch=main --fail-under=90` | ≥ 90% on changed lines |
