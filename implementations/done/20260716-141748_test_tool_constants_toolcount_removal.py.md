# Implementation: tests/test_tool_constants.py (remove 7 count methods + 1 assert line from `TestToolConstants`)

Source plan: `plans/20260716-135355_plan.md`

## Goal

Remove the 7 literal-count/literal-name-set test methods in
`TestToolConstants` and the `len(all_tools) == 42` assertion inside
`test_no_overlapping_tools`, keeping that method's overlap-detection logic
and `test_all_tools_are_strings` intact, along with every classification
test class elsewhere in the file.

## Scope

**In:**
- Delete these 7 methods from `TestToolConstants` (current lines 31-97):
  `test_read_tools`, `test_write_tools`, `test_delete_tools`,
  `test_rag_tools`, `test_cicd_tools`, `test_mdq_tools`, `test_git_tools`.
- Inside `test_no_overlapping_tools` (current lines 113-136): delete only
  the trailing comment + assertion:
  ```python
  # Total should be 42 tools (all frozensets; github-mcp uses prefix routing separately)
  assert len(all_tools) == 42
  ```
  keep the overlap-checking loop and `all_tools.update(tools_set)` above
  it unchanged.

**Out:**
- `test_all_tools_are_strings` (current line 138) — no count assertion,
  unaffected.
- `TestGitToolClassification`, `TestGithubToolClassification`,
  `TestCicdToolClassification`, `TestRagToolClassification`,
  `TestMdqToolClassification` (current lines 155-240) — all compare
  frozensets to each other (e.g. "write tools is a subset of side-effect
  tools"), not to a literal count/name-set; explicitly retained per the
  source plan's Out-of-scope list. Do not touch any of these 5 classes.

## Assumptions

1. Each of the 7 methods being removed
   (`test_read_tools`/`test_write_tools`/`test_delete_tools`/`test_rag_tools`/
   `test_cicd_tools`/`test_mdq_tools`/`test_git_tools`) asserts a hardcoded
   `expected = {...}` set literal equal to the corresponding constant
   (`READ_TOOLS`, `WRITE_TOOLS`, etc.) — per the source plan's Design
   section pattern (already seen for `test_mdq_tools` in an earlier
   MDQ-batch companion doc, `implementations/20260716-131155_test_tool_constants.py.md`,
   which updated this exact method's expected set from 9→7 names). This
   plan removes the method entirely rather than maintaining its expected
   set going forward.
2. `test_no_overlapping_tools`'s overlap-detection loop
   (`for tools_set in [READ_TOOLS, WRITE_TOOLS, ...]: overlaps = all_tools
   & tools_set; assert not overlaps; all_tools.update(tools_set)`) has
   unique behavioral value (detects any future tool erroneously placed in
   two categories) independent of the trailing total-count assertion —
   confirmed by direct read; only the final `assert len(all_tools) == 42`
   line (plus its preceding comment) is removed.

## Implementation

### Target file

`tests/test_tool_constants.py`

### Procedure

1. Open `tests/test_tool_constants.py`.
2. Delete the 7 methods in full from `TestToolConstants`:
   `test_read_tools` (lines 31-45), `test_write_tools` (46-55),
   `test_delete_tools` (56-63), `test_rag_tools` (64-73),
   `test_cicd_tools` (74-83), `test_mdq_tools` (84-96),
   `test_git_tools` (97-112) — re-read exact boundaries during
   implementation, since line numbers may have shifted from an earlier
   MDQ-batch edit to `test_mdq_tools` in this same file.
3. In the retained `test_no_overlapping_tools`, delete only:
   ```python
       # Total should be 42 tools (all frozensets; github-mcp uses prefix routing separately)
       assert len(all_tools) == 42
   ```
   leaving the method ending right after the `all_tools.update(tools_set)`
   line inside the `for` loop (confirm the method's closing structure
   reads correctly — no dangling trailing blank assertion-less body).
4. Confirm `TestToolConstants` now contains exactly 2 methods:
   `test_no_overlapping_tools` (count-assertion-free) and
   `test_all_tools_are_strings`.
5. Leave every other class in the file (`TestGitToolClassification`
   onward) completely untouched.

### Method

Seven full-method deletions plus one partial edit (remove trailing 2 lines
of a retained method) — no weakened replacement assertions, no renaming.

### Details

- After deletion, run `uv run ruff check tests/test_tool_constants.py` to
  catch any now-unused import (e.g. if `READ_TOOLS`/`WRITE_TOOLS`/etc. are
  still imported but only used by removed methods — verify they are still
  referenced by `test_no_overlapping_tools`'s list literal and by the
  retained classification test classes before assuming any import is
  removable).
- Do not touch `TestGitToolClassification` through
  `TestMdqToolClassification` — these are subset/disjointness/side-effect
  -flag comparisons between two independent frozensets, the exact category
  of test this plan preserves.

## Validation plan

| Check | Command | Expected |
|---|---|---|
| 7 methods removed | `grep -n "def test_read_tools\|def test_write_tools\|def test_delete_tools\|def test_rag_tools\|def test_cicd_tools\|def test_mdq_tools\|def test_git_tools" tests/test_tool_constants.py` | 0 matches |
| No literal count remains | `rg "len\(.*\) == \d" tests/test_tool_constants.py` | 0 matches |
| `TestToolConstants` retains 2 methods | `grep -n "def test_" tests/test_tool_constants.py \| sed -n '1,2p'` | `test_no_overlapping_tools`, `test_all_tools_are_strings` |
| Classification classes untouched | `grep -n "^class Test" tests/test_tool_constants.py` | `TestGitToolClassification`, `TestGithubToolClassification`, `TestCicdToolClassification`, `TestRagToolClassification`, `TestMdqToolClassification` all still present |
| Targeted tests pass | `uv run pytest tests/test_tool_constants.py -v` | remaining tests pass |
| Lint | `uv run ruff check tests/test_tool_constants.py` | 0 errors |
| Type check | `uv run mypy tests/test_tool_constants.py` | no new errors |
