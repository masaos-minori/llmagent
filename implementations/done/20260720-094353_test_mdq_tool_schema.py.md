# Implementation: tests/test_mdq_tool_schema.py (new — MDQ inputSchema bound/enum/drift assertions)

Source plan: `plans/20260719-211521_plan.md` ("Align MDQ public tool schema with runtime
constraints"), Implementation step Phase 2 / Design section ("Drift-guard test design").

No prior implementation document exists for this filename in `implementations/` or
`implementations/done/` (confirmed via `ls`/`grep -rl` — no hits). This is a new file, not an edit.

## Goal

Add `tests/test_mdq_tool_schema.py`, a new pytest module asserting that
`scripts/mcp_servers/mdq/mdq_tools.py::TOOL_LIST`'s `inputSchema` constraints (added by the
companion `mdq_tools.py` implementation doc in this same batch) match runtime reality, and that
they do not silently drift from `config/mdq_mcp_server.toml`'s live config defaults.

## Scope

**In scope:**
- One new test file, `tests/test_mdq_tool_schema.py`.
- Assertions against `TOOL_LIST` (imported from `mcp_servers.mdq.mdq_tools`) for the 6 in-scope
  tools: `search_docs`, `get_chunk`, `outline`, `index_paths`, `refresh_index`, `grep_docs`.
- A config-drift-guard case that loads `config/mdq_mcp_server.toml` via `shared.config_loader.ConfigLoader`
  and cross-checks schema `maximum` literals against the five TOML-backed keys that exist there
  (`max_results_limit`, `max_chars_per_chunk`, `max_total_result_chars`, `max_outline_items`,
  `max_grep_matches`).

**Out of scope:**
- No test targets `stats` (empty schema, nothing to assert).
- No test asserts on `mdq_models.py` Pydantic field validators — this file tests the JSON Schema
  dict only, not model-level enforcement (which does not exist per plan Assumption 7).
- No change to `tests/test_tool_server_layer_consistency.py` — verified separately (see Phase 3 of
  the plan); this new file is intentionally a separate, MDQ-specific module (per plan UNK-04).
- No integration/HTTP-level test — pure in-process import and dict inspection, consistent with
  this repo's existing MDQ schema/consistency test style (`tests/test_mdq_routing.py`,
  `tests/test_mdq_metadata_consistency.py`).

## Assumptions

1. `mcp_servers.mdq.mdq_tools.TOOL_LIST` is importable as
   `list[MCPToolSchema]` with `PYTHONPATH=scripts` (confirmed: existing tests such as
   `tests/test_mdq_routing.py` already import from this module this way — same pattern reused).
2. `shared.config_loader.ConfigLoader().load("mdq_mcp_server.toml")` returns a flat `dict[str, Any]`
   of the TOML's top-level keys (confirmed via `ConfigLoader.load(*names)` signature at
   `scripts/shared/config_loader.py:57`); this is the same loader `MdqService.__init__` uses
   (`mdq_service.py:53-57`), so the test reads config the same way the runtime does — no duplicate
   parsing logic invented.
3. `config/mdq_mcp_server.toml` (read directly) declares only 5 of the 7 numeric caps as TOML keys:
   `max_results_limit=100`, `max_chars_per_chunk=10000`, `max_total_result_chars=100000`,
   `max_outline_items=500`, `max_grep_matches=200`. `max_outline_depth` (Python default 6),
   `max_chars_per_match` (Python default 500), `context_before`/`context_after` (Python defaults
   2/2) are **not** TOML keys — they exist only as `.get(key, default)` fallback literals inside
   `mdq_service.py.__init__`. The drift-guard assertion group (item 4 below) therefore only covers
   the 5 TOML-backed keys; the other bounded fields (`max_depth`, `max_chars_per_match`) are
   asserted against their literal expected value directly (no TOML cross-check possible, since
   there is no TOML key to read) — this must be documented in the test module's docstring so a
   future reader does not assume all 7 are drift-guarded identically.
4. Test module follows the existing dict-field-inspection style already used in
   `tests/test_tool_server_layer_consistency.py` (per plan's Design section reference) — direct
   `TOOL_LIST` indexing by tool name, then by `["inputSchema"]["properties"][field]`, no schema
   library (e.g. `jsonschema`) dependency needed since assertions are simple key/value checks.

## Implementation

### Target file

`tests/test_mdq_tool_schema.py` (new file)

Imports from:
- `scripts/mcp_servers/mdq/mdq_tools.py::TOOL_LIST` (module path `mcp_servers.mdq.mdq_tools`).
- `scripts/shared/config_loader.py::ConfigLoader`.

### Procedure

1. Add module docstring stating: this file asserts `TOOL_LIST` inputSchema constraints match
   runtime caps in `mdq_service.py`/`mdq_models.py`, and guards against config/schema literal
   drift for the 5 TOML-backed keys (per Assumption 3 — note the 2 Python-default-only keys are
   checked by literal value, not cross-checked against TOML).
2. Add a module-level helper `_tool_schema(name: str) -> dict` that finds and returns the
   `inputSchema` dict for a given tool name from `TOOL_LIST` (small loop or generator-expression
   lookup; raises `KeyError`/`AssertionError` with a clear message if not found — fails loudly
   rather than silently skipping if a tool is ever renamed).
3. Add one test function per assertion group (4 groups, per plan Design section):
   - `test_search_docs_mode_enum_bm25_only` — `_tool_schema("search_docs")["properties"]["mode"]["enum"] == ["bm25"]`.
   - `test_search_docs_integer_bounds` — assert `minimum`/`maximum` on `limit`, `max_results_limit`,
     `max_total_result_chars` equal `(1, 100)`, `(1, 100)`, `(1, 100000)` respectively.
   - `test_search_docs_tag_filter_items_type` — `tag_filter["items"] == {"type": "string"}`.
   - `test_get_chunk_max_chars_per_chunk_bounds` — `(1, 10000)`.
   - `test_outline_bounds_and_max_depth_present` — `max_outline_items` bounds `(1, 500)`;
     `max_depth` property exists with bounds `(1, 6)`.
   - `test_index_paths_and_refresh_index_paths_items_and_min_items` — parametrized or duplicated
     for both tool names: `paths["items"] == {"type": "string"}` and `paths["minItems"] == 1`.
   - `test_grep_docs_bounds_and_items` — `max_grep_matches` `(1, 200)`, `max_chars_per_match`
     `(1, 500)`, `context_before`/`context_after` `minimum == 0` and no `maximum` key present,
     `paths["items"] == {"type": "string"}` and no `minItems` key present (asymmetry vs
     index_paths/refresh_index is intentional — assert absence explicitly, not just non-failure).
4. Add the config-drift-guard test:
   - `test_schema_maxima_match_config_defaults` — load
     `ConfigLoader().load("mdq_mcp_server.toml")`, then assert each of the 5 TOML-backed
     schema `maximum` literals (`search_docs.limit`/`max_results_limit` → `max_results_limit`,
     `search_docs.max_total_result_chars` → `max_total_result_chars`, `get_chunk.max_chars_per_chunk`
     → `max_chars_per_chunk`, `outline.max_outline_items` → `max_outline_items`,
     `grep_docs.max_grep_matches` → `max_grep_matches`) equal the corresponding config dict value,
     falling back to the same Python-side default literal (100/10000/100000/500/200) if the TOML
     key is absent (mirrors `mdq_cfg.get(key, default)` pattern in `mdq_service.py`, so the test
     passes whether or not the TOML file declares the key explicitly).

### Method

Pseudocode only (per `skills/python-design/SKILL.md` — no production code blocks):

```
from mcp_servers.mdq.mdq_tools import TOOL_LIST
from shared.config_loader import ConfigLoader


def _tool_schema(name: str) -> dict:
    for tool in TOOL_LIST:
        if tool["name"] == name:
            return tool["inputSchema"]
    raise AssertionError(f"tool {name!r} not found in TOOL_LIST")


def test_search_docs_mode_enum_bm25_only() -> None:
    props = _tool_schema("search_docs")["properties"]
    assert props["mode"]["enum"] == ["bm25"]


def test_schema_maxima_match_config_defaults() -> None:
    cfg = ConfigLoader().load("mdq_mcp_server.toml")
    assert _tool_schema("search_docs")["properties"]["max_results_limit"]["maximum"] == cfg.get("max_results_limit", 100)
    assert _tool_schema("get_chunk")["properties"]["max_chars_per_chunk"]["maximum"] == cfg.get("max_chars_per_chunk", 10000)
    assert _tool_schema("search_docs")["properties"]["max_total_result_chars"]["maximum"] == cfg.get("max_total_result_chars", 100000)
    assert _tool_schema("outline")["properties"]["max_outline_items"]["maximum"] == cfg.get("max_outline_items", 500)
    assert _tool_schema("grep_docs")["properties"]["max_grep_matches"]["maximum"] == cfg.get("max_grep_matches", 200)

# ... remaining test functions per Procedure step 3, one assertion group each.
```

### Details

- No fixtures/mocking needed — `TOOL_LIST` is a plain module-level constant, `ConfigLoader` reads
  the real `config/mdq_mcp_server.toml` from disk (read-only; same file the running server reads).
- Do not assert on `"description"` string contents — that is covered (separately, if at all) by
  the unrelated `implementations/20260720-092231_mdq_tools.py.md` description-text doc; this file
  is schema-shape/bounds only.
- Keep each test function single-purpose (one assertion group per plan's 4 groups, further split
  per-tool as shown in Procedure) so a future regression pinpoints exactly which tool/field broke.
- File belongs in `tests/` (not `tests/mdq/` or similar) — matches flat layout of existing MDQ test
  files (`tests/test_mdq_routing.py`, `tests/test_mdq_metadata_consistency.py`, etc.).

## Validation plan

| Check | Command | Target |
|---|---|---|
| New test file passes | `uv run pytest tests/test_mdq_tool_schema.py -v` | all pass |
| Lint | `uv run ruff format tests/test_mdq_tool_schema.py && uv run ruff check tests/test_mdq_tool_schema.py` | 0 errors |
| Type check | `uv run mypy scripts/` (tests/ covered per `rules/coding.md` mypy note) | no new errors |
| Depends on companion schema edit | run only after `scripts/mcp_servers/mdq/mdq_tools.py` edits from the sibling `mdq_tools.py` implementation doc land — otherwise all bound/enum assertions fail by design (drift caught, not a false negative) | fails before Phase 1, passes after |
| Regression | `uv run pytest tests/test_tool_server_layer_consistency.py tests/test_mdq_*.py -v` | no new failures |
| Full suite | `uv run pytest` | no new failures |
| Coverage | `uv run coverage run -m pytest tests/ && uv run coverage xml && uv run diff-cover coverage.xml --compare-branch=main --fail-under=90` | >= 90% on changed lines |
