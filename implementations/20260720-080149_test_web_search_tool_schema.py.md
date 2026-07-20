# Implementation Procedure: tests/test_web_search_tool_schema.py (new file)

Source plan: `plans/20260719-192933_plan.md` ("Validate WebSearchConfig and align search_web input schema")

## Goal

Create a new drift-detection test file that asserts numeric/string equality
between `TOOL_LIST[0]["inputSchema"]`'s hand-written constraints (in
`web_search_tools.py`) and the live Pydantic field constraints on `SearchRequest`
(in `web_search_models.py`), so the two never silently diverge again — this is the
"schema drift test" required by the plan's Acceptance Criteria.

## Scope

**In scope**
- A new test module, `tests/test_web_search_tool_schema.py`, with no existing
  content to preserve (file does not exist yet — confirmed via `find`).
- Assertions comparing: `query.minLength`/`maxLength` vs. `SearchRequest`'s
  `min_length`/`max_length` constraints; `max_results.minimum`/`maximum` vs.
  `SearchRequest`'s `ge`/`le` constraints.

**Out of scope**
- Modifying `web_search_tools.py` or `web_search_models.py` themselves (separate
  docs: `implementations/20260720-080040_web_search_tools.py.md` and
  `implementations/20260720-080006_web_search_models.py.md`).
- Modifying `tests/test_web_search_models.py` (separate doc:
  `implementations/20260720-080108_test_web_search_models.py.md`).

## Assumptions

1. This file depends on both of the above target files being implemented first
   (it imports `TOOL_LIST` from `web_search_tools.py` and `SearchRequest` from
   `web_search_models.py`, both of which must already have the new
   `minLength`/`maxLength`/`minimum`/`maximum` schema keys and Pydantic
   constraints respectively for the drift assertions to be meaningful).
2. Pydantic v2's `SearchRequest.model_fields["query"]` exposes constraint
   metadata via `.metadata` (a list of `annotated_types` constraint objects, e.g.
   `MinLen`, `MaxLen`) and `SearchRequest.model_fields["max_results"]` exposes
   `.metadata` with `Ge`/`Le` objects — the test extracts numeric values from
   these rather than re-deriving bounds independently, to guarantee the comparison
   is against the actual live model, not a hardcoded expectation that could itself
   drift.
3. Test file naming and layout follow the existing convention in
   `tests/test_web_search_models.py` (module docstring, `from __future__ import
   annotations`, plain `pytest` functions or a `Test*` class — either is
   acceptable; a `Test*` class matches the sibling file's existing style).

## Implementation

### Target file

`tests/test_web_search_tool_schema.py` (new — does not exist yet; verified via
`find . -name "test_web_search_tool_schema.py"` returning no results).

Related existing files this test imports from:
- `scripts/mcp_servers/web_search/web_search_tools.py` — `TOOL_LIST` (L11-30,
  see `implementations/20260720-080040_web_search_tools.py.md` for the planned
  schema shape after implementation).
- `scripts/mcp_servers/web_search/web_search_models.py` — `SearchRequest` (L68-82,
  see `implementations/20260720-080006_web_search_models.py.md` for the planned
  constraint shape after implementation).

### Procedure

1. Create the new file with a module docstring following the sibling file's
   pattern (`"""tests/test_web_search_tool_schema.py\nDrift tests..."""`).
2. Import `TOOL_LIST` from `mcp_servers.web_search.web_search_tools` and
   `SearchRequest` from `mcp_servers.web_search.web_search_models`.
3. Add a helper (module-level function or fixture) that locates the `search_web`
   tool's `inputSchema` in `TOOL_LIST` by `name == "search_web"` rather than
   assuming index `0`, so the test survives future reordering of `TOOL_LIST`.
4. Add test cases:
   - `test_query_min_length_matches_model` — schema `query.minLength` ==
     `SearchRequest`'s `query` `min_length` constraint value.
   - `test_query_max_length_matches_model` — schema `query.maxLength` ==
     `SearchRequest`'s `query` `max_length` constraint value.
   - `test_max_results_minimum_matches_model` — schema `max_results.minimum` ==
     `SearchRequest`'s `max_results` `ge` constraint value.
   - `test_max_results_maximum_matches_model` — schema `max_results.maximum` ==
     the live `_cfg.max_results_limit` (or `get_max_results_limit()`, per whichever
     accessor `web_search_tools.py` ends up using) — this must equal
     `SearchRequest`'s `max_results` `le` constraint value, since both are sourced
     from the same `_cfg` singleton.
5. Add one negative/shape test — `test_search_web_tool_present` — asserting exactly
   one `TOOL_LIST` entry has `name == "search_web"`, so the lookup helper (step 3)
   fails loudly if the tool is ever renamed or removed rather than silently
   skipping all other assertions.

### Method

Pseudocode only (per `skills/python-design/SKILL.md` — no production code blocks):

```
"""tests/test_web_search_tool_schema.py
Drift tests between TOOL_LIST["search_web"].inputSchema and SearchRequest."""

from __future__ import annotations

from mcp_servers.web_search.web_search_models import SearchRequest
from mcp_servers.web_search.web_search_tools import TOOL_LIST


def _search_web_schema() -> dict:
    matches = [t for t in TOOL_LIST if t["name"] == "search_web"]
    assert len(matches) == 1
    return matches[0]["inputSchema"]


def _query_constraint(name: str) -> int:
    # extract MinLen/MaxLen value from SearchRequest.model_fields["query"].metadata
    ...


def _max_results_constraint(name: str) -> int:
    # extract Ge/Le value from SearchRequest.model_fields["max_results"].metadata
    ...


class TestSearchWebSchemaDrift:
    def test_search_web_tool_present(self) -> None:
        assert any(t["name"] == "search_web" for t in TOOL_LIST)

    def test_query_min_length_matches_model(self) -> None:
        schema = _search_web_schema()
        assert schema["properties"]["query"]["minLength"] == _query_constraint("min_length")

    def test_query_max_length_matches_model(self) -> None:
        schema = _search_web_schema()
        assert schema["properties"]["query"]["maxLength"] == _query_constraint("max_length")

    def test_max_results_minimum_matches_model(self) -> None:
        schema = _search_web_schema()
        assert schema["properties"]["max_results"]["minimum"] == _max_results_constraint("ge")

    def test_max_results_maximum_matches_model(self) -> None:
        schema = _search_web_schema()
        assert schema["properties"]["max_results"]["maximum"] == _max_results_constraint("le")
```

### Details

- Extracting constraint values from `SearchRequest.model_fields[...].metadata` is
  the Pydantic v2 idiom for reading `Field(..., min_length=..., ge=..., ...)`
  constraints back out; the exact `annotated_types` class names (`MinLen`,
  `MaxLen`, `Ge`, `Le`) should be confirmed against the installed `pydantic`/
  `annotated_types` version at implementation time (not guessed at design time)
  by inspecting `SearchRequest.model_fields["query"].metadata` interactively if
  needed.
- This file has no production-code counterpart to modify — it is purely additive
  and does not appear in `deploy/deploy.sh` (per the plan's Affected Areas table:
  `tests/` is not part of the deploy copy list).
- Keep this file's assertions strictly about *drift* (schema vs. model equality),
  not about correctness of the bounds themselves (that is
  `tests/test_web_search_models.py`'s responsibility) — avoids duplicate/overlapping
  coverage between the two test files.

## Validation plan

Reference commands only (do not run as part of this design-only task; see
`rules/toolchain.md` for the authoritative sequence):

```bash
uv run ruff format tests/
uv run ruff check tests/
uv run mypy scripts/
uv run pytest tests/test_web_search_tool_schema.py -v
uv run pytest tests/test_tool_server_layer_consistency.py tests/test_mcp_tool_schema_exports.py tests/agent/services/test_mcp_tool_discovery.py -v
uv run pytest -v
uv run coverage run -m pytest tests/ && uv run coverage xml && uv run diff-cover coverage.xml --compare-branch=main --fail-under=90
uv run pre-commit run --all-files
```

Expected outcome: all new drift assertions pass once both
`web_search_tools.py` and `web_search_models.py` implement the planned schema/model
changes; no regressions in the three named regression suites.
