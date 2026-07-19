# Implementation: tests/test_mdq_routing.py (remove `TestMdqToolsCount`; remove 1 assert line from `test_v1_tools_returns_all_tools`)

Source plan: `plans/20260716-135355_plan.md`

## Goal

Remove `TestMdqToolsCount` (3 methods, all literal-count/name-set checks)
and the `len(body["tools"]) == 7` assertion inside
`test_v1_tools_returns_all_tools`, keeping that test's `"tools" in body`
presence check and every other class in the file untouched.

## Scope

**In:**
- Delete `TestMdqToolsCount` in full (current lines 11-38):
  `test_mdq_tools_count`, `test_mdq_production_tools_count`,
  `test_mdq_tools_exact_names`.
- Inside `test_v1_tools_returns_all_tools` (current lines 191-201): delete
  only the trailing line `assert len(body["tools"]) == 7`; keep
  `assert response.status_code == 200`, `body = response.json()`, and
  `assert "tools" in body`.

**Out:**
- `TestMdqNoUnmappedTools`, `TestMdqSafetyTiers`,
  `TestMdqMCPServerConformance`, `TestMdqV1ToolsEndpoint`'s other 2 methods
  (`test_v1_tools_names_match_mdq_tools`, `test_v1_tools_includes_server_key`)
  — all compare two independent sources (e.g. live `/v1/tools` response
  vs. `MDQ_TOOLS` constant) or check structural shape, not a literal
  count; explicitly retained per the source plan's Out-of-scope list.

## Assumptions

1. `test_mdq_production_tools_count`'s docstring says "TOOL_LIST should
   have exactly 7 production-status tools" and asserts
   `len(production_tools) == 7` where `production_tools` is filtered from
   `TOOL_LIST` by `status == "production"` — this is still a literal-count
   check (just filtered first), matching the source plan's removal target;
   confirmed no other test depends on this specific method's side effects
   (none — each test method is independent).
2. `test_v1_tools_names_match_mdq_tools` (the method immediately after
   `test_v1_tools_returns_all_tools`) compares the live endpoint's tool
   names against `MDQ_TOOLS` (an independent source) — this is a
   cross-source check and stays untouched, confirming the file's `class
   TestMdqV1ToolsEndpoint` is not being removed wholesale, only one
   assertion line inside one of its 3 methods.

## Implementation

### Target file

`tests/test_mdq_routing.py`

### Procedure

1. Open `tests/test_mdq_routing.py`.
2. Delete `TestMdqToolsCount` in full (current lines 11-38):
   ```python
   class TestMdqToolsCount:
       """Verify MDQ_TOOLS contains exactly 7 expected tools."""

       def test_mdq_tools_count(self) -> None:
           assert len(MDQ_TOOLS) == 7

       def test_mdq_production_tools_count(self) -> None:
           """TOOL_LIST should have exactly 7 production-status tools."""
           from mcp_servers.mdq.mdq_tools import TOOL_LIST

           production_tools = [t for t in TOOL_LIST if t.get("status") == "production"]
           assert len(production_tools) == 7, (
               f"Expected 7 production tools, got {len(production_tools)}: "
               f"{[t['name'] for t in production_tools]}"
           )

       def test_mdq_tools_exact_names(self) -> None:
           expected = {
               "search_docs",
               "get_chunk",
               "outline",
               "index_paths",
               "refresh_index",
               "stats",
               "grep_docs",
           }
           assert MDQ_TOOLS == expected
   ```
   (Exact body per the earlier MDQ-batch companion doc
   `implementations/20260716-131153_test_mdq_routing.py.md`'s already
   -corrected 7-name state — re-read the live file to confirm current
   exact content before deleting, in case further drift occurred.)
3. In `test_v1_tools_returns_all_tools` (current lines 191-201):
   ```python
       def test_v1_tools_returns_all_tools(self) -> None:
           """GET /v1/tools should return all 7 MDQ tools."""
           from fastapi.testclient import TestClient
           from mcp_servers.mdq.mdq_server import app

           client = TestClient(app)
           response = client.get("/v1/tools")
           assert response.status_code == 200
           body = response.json()
           assert "tools" in body
           assert len(body["tools"]) == 7
   ```
   Delete only the last line (`assert len(body["tools"]) == 7`), leaving
   the method ending at `assert "tools" in body`. Also update the
   docstring `"""GET /v1/tools should return all 7 MDQ tools."""` to drop
   the "7 " reference, e.g. `"""GET /v1/tools should return the tools
   list."""`.
4. Confirm the `MDQ_TOOLS` import at the top of the file is still used
   elsewhere (by `TestMdqNoUnmappedTools`, per the earlier read of that
   class) — do not remove the import.

### Method

One full-class deletion plus one partial edit (remove 1 trailing
assertion line + adjust 1 docstring) inside a retained method — no
weakened replacement assertions.

### Details

- Do not touch `TestMdqNoUnmappedTools`, `TestMdqSafetyTiers`,
  `TestMdqMCPServerConformance`, or the other 2 methods of
  `TestMdqV1ToolsEndpoint`.
- Run `uv run ruff check` after the edit to confirm no import becomes
  unused as a result of deleting `TestMdqToolsCount`.

## Validation plan

| Check | Command | Expected |
|---|---|---|
| Class removed | `grep -n "TestMdqToolsCount" tests/test_mdq_routing.py` | 0 matches |
| Assert line removed | `grep -n 'len(body\["tools"\]) == 7' tests/test_mdq_routing.py` | 0 matches |
| `"tools" in body` retained | `grep -n '"tools" in body' tests/test_mdq_routing.py` | 1 match |
| Remaining tests pass | `uv run pytest tests/test_mdq_routing.py -v` | all remaining tests pass; `TestMdqToolsCount` no longer collected |
| Lint | `uv run ruff check tests/test_mdq_routing.py` | 0 errors |
| Type check | `uv run mypy tests/test_mdq_routing.py` | no new errors |
