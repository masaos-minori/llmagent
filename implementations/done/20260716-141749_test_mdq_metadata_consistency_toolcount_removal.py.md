# Implementation: tests/test_mdq_metadata_consistency.py (remove `test_total_tool_count`; strip count wording from docstrings)

Source plan: `plans/20260716-135355_plan.md`

## Goal

Remove `test_total_tool_count` (a pure `len(TOOL_LIST) == 7` assertion)
and strip the "count is 7" / "7 tools" / "7 non-admin" wording from the
module docstring and two other tests' docstrings, leaving those two
tests' assertion bodies completely unchanged.

## Scope

**In:**
- Delete `test_total_tool_count` in full (current lines 18-22).
- Edit the module docstring (current lines 1-10): remove the
  `- Total tool count is 7` bullet.
- Edit `test_production_tool_statuses`'s docstring (current line 34):
  `"""7 non-admin mdq-mcp tools have status='production'."""` → drop the
  `7 ` prefix.
- Edit `test_all_tools_have_status_field`'s docstring (current line 53):
  `"""All 7 mdq-mcp tools have a 'status' field."""` → drop the `7 `.

**Out:**
- `test_production_tool_statuses`'s assertion body (the `production_tools`
  set literal and the per-tool status check, lines 36-50) — logic
  unchanged, this set is a name-list used to select which tools to check a
  *status field value* on, not a bare count/name-set-equality check against
  the whole `TOOL_LIST`; per the source plan's explicit instruction, only
  docstring wording changes here.
- `test_all_tools_have_status_field`'s assertion body (lines 54-57) —
  unchanged, it iterates `TOOL_LIST` checking a field's presence per tool,
  not a count.
- `test_no_stub_keys_in_tools`, `TestMdqHealthMetadataConsistency`'s two
  methods — untouched, no count wording.

## Assumptions

1. `test_total_tool_count`'s only assertion (`assert len(TOOL_LIST) == 7`)
   is a pure literal-count check with no unique behavioral coverage — the
   number itself (7) was already corrected from a stale "9" by an earlier
   MDQ-batch companion doc
   (`implementations/20260716-131154_test_mdq_metadata_consistency.py.md`);
   this plan removes the check entirely rather than maintaining the
   literal going forward.
2. `test_production_tool_statuses` and `test_all_tools_have_status_field`
   retain full behavioral value independent of their docstrings' incidental
   mention of "7" — their assertions do not depend on knowing the total
   count, only on iterating whatever `TOOL_LIST` currently contains.

## Implementation

### Target file

`tests/test_mdq_metadata_consistency.py`

### Procedure

1. Open `tests/test_mdq_metadata_consistency.py`.
2. Edit the module docstring (current lines 1-10):
   ```python
   """tests/test_mdq_metadata_consistency.py

   Unit tests for mdq-mcp health and tool metadata consistency.

   Verifies:
   - No `stub` key in any mdq-mcp tool entry
   - All tools have `"status": "production"`
   - Total tool count is 7
   - Health response dict contains no `stub` field
   """
   ```
   Remove the `- Total tool count is 7` line, leaving:
   ```python
   """tests/test_mdq_metadata_consistency.py

   Unit tests for mdq-mcp health and tool metadata consistency.

   Verifies:
   - No `stub` key in any mdq-mcp tool entry
   - All tools have `"status": "production"`
   - Health response dict contains no `stub` field
   """
   ```
3. Delete `test_total_tool_count` in full (current lines 18-22):
   ```python
       def test_total_tool_count(self) -> None:
           """mdq-mcp has exactly 7 tools."""
           from mcp_servers.mdq.mdq_tools import TOOL_LIST

           assert len(TOOL_LIST) == 7
   ```
4. Edit `test_production_tool_statuses`'s docstring (current line 34):
   ```python
   """7 non-admin mdq-mcp tools have status='production'."""
   ```
   to:
   ```python
   """Non-admin mdq-mcp tools have status='production'."""
   ```
   (assertion body below, lines 36-50, unchanged).
5. Edit `test_all_tools_have_status_field`'s docstring (current line 53):
   ```python
   """All 7 mdq-mcp tools have a 'status' field."""
   ```
   to:
   ```python
   """All mdq-mcp tools have a 'status' field."""
   ```
   (assertion body below unchanged).

### Method

One full-method deletion plus 3 docstring text edits — no change to any
retained method's assertion logic.

### Details

- Do not touch the `production_tools` set literal inside
  `test_production_tool_statuses` — it is a name-list used for filtering
  which tools to check, not a count/equality assertion against the whole
  `TOOL_LIST`, and is explicitly out of scope for removal per the source
  plan.
- Do not touch `TestMdqHealthMetadataConsistency` at all.

## Validation plan

| Check | Command | Expected |
|---|---|---|
| Method removed | `grep -n "def test_total_tool_count" tests/test_mdq_metadata_consistency.py` | 0 matches |
| Docstring wording removed | `grep -n "Total tool count is 7\|7 non-admin\|All 7 mdq-mcp" tests/test_mdq_metadata_consistency.py` | 0 matches |
| Remaining tests pass | `uv run pytest tests/test_mdq_metadata_consistency.py -v` | 3 tests remain and pass (`test_no_stub_keys_in_tools`, `test_production_tool_statuses`, `test_all_tools_have_status_field`) plus the 2 health tests |
| Lint | `uv run ruff check tests/test_mdq_metadata_consistency.py` | 0 errors |
| Type check | `uv run mypy tests/test_mdq_metadata_consistency.py` | no new errors |
