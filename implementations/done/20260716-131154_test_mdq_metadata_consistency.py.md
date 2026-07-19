# Implementation: tests/test_mdq_metadata_consistency.py (update tool count 9→7, remove admin-tool test)

Source plan: `plans/20260716-123031_plan.md`

## Goal

Update `tests/test_mdq_metadata_consistency.py` so it reflects a MDQ tool
surface with zero `"admin"`-status tools and 7 total tools, removing the
now-meaningless `test_admin_tool_statuses` test.

## Scope

**In:**
- Module docstring (lines 1-10): update `Total tool count is 9` → `7`, and
  remove the `Admin tools (\`fts_consistency_check\`, \`fts_rebuild\`) have
  \`"status": "admin"\`` bullet entirely (no admin tools remain).
- `test_total_tool_count` (lines 19-23): change
  `assert len(TOOL_LIST) == 9` → `assert len(TOOL_LIST) == 7`, and update
  the docstring `"""mdq-mcp has exactly 9 tools."""` → `7`.
- `test_production_tool_statuses` (lines 35-49): this already lists exactly
  the 7 remaining tool names as `production_tools` and its docstring says
  "7 non-admin mdq-mcp tools" — no change needed to the set literal, but
  re-verify it still reads correctly once no admin tools exist at all (i.e.
  every tool in `TOOL_LIST` should now satisfy this assertion, not just the
  named 7 — this is already true since `TOOL_LIST` will only have 7 entries
  total).
- `test_admin_tool_statuses` (lines 51-59): **delete this test function
  entirely** — with zero admin-status tools remaining in `TOOL_LIST`, there
  is nothing left for it to assert (an empty-intersection loop that never
  executes its assertion body is not a meaningful regression test).
- `test_all_tools_have_status_field` (lines 61-66): no change needed — logic
  is generic over `TOOL_LIST` regardless of count.

**Out:**
- `test_no_stub_keys_in_tools` (lines 25-33) — generic over `TOOL_LIST`, no
  change needed.
- `TestMdqHealthMetadataConsistency` (lines 72-97) — unrelated to tool
  count/status, no change needed.

## Assumptions

1. `test_admin_tool_statuses`'s loop (`for tool in TOOL_LIST: if tool["name"]
   in admin_tools: assert ...`) would still technically "pass" vacuously
   with an empty `admin_tools` intersection if left unedited (since the loop
   body never executes), but leaving a test whose docstring claims "2 admin
   mdq-mcp tools" when zero exist is misleading and should be removed per
   the source plan's explicit instruction ("remove/adjust
   `test_admin_tool_statuses` (no admin tools remain)").
2. This change must land in the same commit as the companion `tools.py` doc
   (removes the two `TOOL_LIST` entries) — otherwise `test_total_tool_count`
   fails against the still-9-entry `TOOL_LIST`.

## Implementation

### Target file

`tests/test_mdq_metadata_consistency.py`

### Procedure

1. Open `tests/test_mdq_metadata_consistency.py`.
2. Update the module docstring (lines 1-10): change
   ```
   - Admin tools (`fts_consistency_check`, `fts_rebuild`) have `"status": "admin"`
   - Total tool count is 9
   ```
   to:
   ```
   - Total tool count is 7
   ```
   (remove the admin-tools bullet entirely, update the count).
3. In `test_total_tool_count` (lines 19-23):
   ```python
   def test_total_tool_count(self) -> None:
       """mdq-mcp has exactly 9 tools."""
       from mcp_servers.mdq.mdq_tools import TOOL_LIST

       assert len(TOOL_LIST) == 9
   ```
   change to:
   ```python
   def test_total_tool_count(self) -> None:
       """mdq-mcp has exactly 7 tools."""
       from mcp_servers.mdq.mdq_tools import TOOL_LIST

       assert len(TOOL_LIST) == 7
   ```
4. Delete `test_admin_tool_statuses` in full (lines 51-59):
   ```python
   def test_admin_tool_statuses(self) -> None:
       """2 admin mdq-mcp tools (fts_consistency_check, fts_rebuild) have status='admin'."""
       from mcp_servers.mdq.mdq_tools import TOOL_LIST

       admin_tools = {"fts_consistency_check", "fts_rebuild"}
       for tool in TOOL_LIST:
           if tool["name"] in admin_tools:
               assert tool.get("status") == "admin", (
                   f"Tool '{tool['name']}' should have status='admin'"
               )
   ```
5. Confirm `test_production_tool_statuses`'s docstring
   (`"""7 non-admin mdq-mcp tools have status='production'."""`) still
   reads accurately — no edit needed since it already says 7 and the set
   literal already matches the 7 surviving tool names.

### Method

Docstring/module-docstring text edits, one numeric literal change, and one
full test-function deletion — no new tests added.

### Details

- Do not add a replacement "test_no_admin_tools_remain" test unless
  explicitly requested — the source plan says "remove/adjust", and removal
  with the count/docstring correction is sufficient; adding a new
  assertion is optional cleanup, not required by the plan (avoid
  speculative additions per project conventions).
- Keep `TestMdqToolMetadataConsistency`'s class docstring
  (`"""Verify mdq-mcp tool metadata is consistent (no stub markers, correct
  statuses)."""`) unchanged — still accurate.

## Validation plan

| Check | Command | Expected |
|---|---|---|
| Targeted tests | `uv run pytest tests/test_mdq_metadata_consistency.py -v` | all pass (requires companion `tools.py` change applied together) |
| Admin test removed | `grep -n "test_admin_tool_statuses\|fts_consistency_check\|fts_rebuild" tests/test_mdq_metadata_consistency.py` | 0 matches |
| Count updated | `grep -n "== 9\|exactly 9" tests/test_mdq_metadata_consistency.py` | 0 matches |
| Lint | `uv run ruff check tests/test_mdq_metadata_consistency.py` | 0 errors |
| Type check | `uv run mypy tests/test_mdq_metadata_consistency.py` | no new errors |
