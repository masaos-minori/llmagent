# Implementation: tests/test_tool_constants.py (update `test_mdq_tools` expected set/count)

Source plan: `plans/20260716-123031_plan.md`

## Goal

Update `tests/test_tool_constants.py::test_mdq_tools` (lines 84-97) to
assert the post-removal 7-name `MDQ_TOOLS` set, matching the companion
`tool_constants.py` change.

## Scope

**In:**
- `test_mdq_tools` (lines 84-97): remove `"fts_consistency_check",` and
  `"fts_rebuild",` from the `expected` set literal, and change
  `assert len(MDQ_TOOLS) == 9` → `assert len(MDQ_TOOLS) == 7`.

**Out:**
- Any other test in this file (`test_mdq_write_tools` if present elsewhere,
  `test_cicd_tools`, `test_git_tools`, etc.) — not part of this plan's
  scope; confirm via `grep -n "MDQ_WRITE_TOOLS" tests/test_tool_constants.py`
  whether a separate `MDQ_WRITE_TOOLS`-specific test exists — if one does
  and asserts `fts_rebuild` membership, it must also be updated as part of
  this same file's change (expand scope within this same doc rather than
  creating a second doc, since it is the same target file).

## Assumptions

1. `test_mdq_tools` imports `MDQ_TOOLS` from `shared.tool_constants` (same
   module as the companion `tool_constants.py` doc) — this test's literal
   expectations must track that source exactly.
2. This change must land in the same commit as the companion
   `tool_constants.py` doc — otherwise this test fails against the
   still-9-name `MDQ_TOOLS`.

## Implementation

### Target file

`tests/test_tool_constants.py`

### Procedure

1. Open `tests/test_tool_constants.py`.
2. Locate `test_mdq_tools` (current lines 84-97):
   ```python
   def test_mdq_tools(self) -> None:
       expected = {
           "search_docs",
           "get_chunk",
           "outline",
           "index_paths",
           "refresh_index",
           "stats",
           "grep_docs",
           "fts_consistency_check",
           "fts_rebuild",
       }
       assert MDQ_TOOLS == expected
       assert len(MDQ_TOOLS) == 9
   ```
3. Change to:
   ```python
   def test_mdq_tools(self) -> None:
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
       assert len(MDQ_TOOLS) == 7
   ```
4. Search the rest of the file for any `MDQ_WRITE_TOOLS`-specific
   assertion (`grep -n "MDQ_WRITE_TOOLS" tests/test_tool_constants.py`) — if
   found, update it to expect `{"index_paths", "refresh_index"}` (2 items,
   no `fts_rebuild`) in the same edit pass.

### Method

Literal-value edit to one existing test function (plus a conditional
same-file edit to any `MDQ_WRITE_TOOLS` assertion found during
implementation) — no new test functions added.

### Details

- Keep the multi-line set-literal formatting style already used in the
  file (one name per line).
- Do not touch `test_cicd_tools`, `test_git_tools`, or any other
  tool-constant test in this file — out of scope.

## Validation plan

| Check | Command | Expected |
|---|---|---|
| Targeted test | `uv run pytest tests/test_tool_constants.py -k test_mdq_tools -v` | pass (requires companion `tool_constants.py` change applied together) |
| No stale references | `grep -n "fts_consistency_check\|fts_rebuild" tests/test_tool_constants.py` | 0 matches (or only inside an updated, correctly-scoped `MDQ_WRITE_TOOLS` assertion if one exists and was updated per step 4) |
| Full file | `uv run pytest tests/test_tool_constants.py -v` | all pass |
| Lint | `uv run ruff check tests/test_tool_constants.py` | 0 errors |
