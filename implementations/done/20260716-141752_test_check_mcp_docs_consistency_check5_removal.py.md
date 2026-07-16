# Implementation: tests/test_check_mcp_docs_consistency.py (remove `TestCheckToolCounts` and its dedicated helpers)

Source plan: `plans/20260716-135355_plan.md`

Note: distinct from the earlier `tests/test_check_mcp_docs_consistency.py`
docs (`implementations/done/20260703-124720_...md`,
`implementations/done/20260712-165004_...md`,
`implementations/done/20260712-192537_...md`), which each added coverage
for unrelated checks — none of them touched `TestCheckToolCounts`. This
doc removes that entire test class in full, matching the companion
`tools/check_mcp_docs_consistency.py` doc's removal of `check_tool_counts()`
itself.

## Goal

Remove `TestCheckToolCounts` (7 methods: the unit-test suite for
`check_tool_counts()`), its dedicated `_ALL_CATALOG_FILENAMES` tuple and
`_mk_all_catalog_files()` helper (which exist solely to feed this class),
and drop `check_tool_counts` from the top-of-file import block — since the
function itself is removed by the companion `tools/check_mcp_docs_consistency.py`
doc.

## Scope

**In:**
- Remove `check_tool_counts` from the `from check_mcp_docs_consistency
  import (...)` block (current line 23).
- Delete `_ALL_CATALOG_FILENAMES` (current lines 232-239) and
  `_mk_all_catalog_files()` (current lines 241-244) — confirm via
  `rg -n "_ALL_CATALOG_FILENAMES|_mk_all_catalog_files"
  tests/test_check_mcp_docs_consistency.py` that neither is used outside
  `TestCheckToolCounts` before deleting (per the source plan's Design
  section, they "exist solely to feed it").
- Delete `TestCheckToolCounts` in full (current lines 247-347+): 7 methods
  — `test_correct_count_no_issue`, `test_incorrect_count_triggers_warning`,
  `test_missing_catalog_file_returns_warning`,
  `test_partial_catalog_files_missing`, `test_unknown_server_no_issue`,
  `test_multiple_servers_checked`, `test_one_server_incorrect_count`.

**Out:**
- Every other test class in this file (covering Checks 1-4, 6-13) — not
  referenced by this plan, untouched.
- `_mk_file()` (a generic `DocFile`-constructing helper used across many
  test classes, distinct from the Check-5-only `_mk_all_catalog_files`) —
  confirm this helper is used by other, retained test classes before
  assuming it is safe to leave alone (it should be, since it is a generic
  builder, but verify via `rg -n "_mk_file\("
  tests/test_check_mcp_docs_consistency.py` shows call sites outside
  `TestCheckToolCounts`).

## Assumptions

1. `_ALL_CATALOG_FILENAMES` and `_mk_all_catalog_files()` are used only by
   `TestCheckToolCounts`'s 7 methods — per the source plan's Design
   section explicit statement ("now-unused ... helpers that exist solely
   to feed it") — re-verify via `rg` during implementation before deleting,
   since a false assumption here would break another test class.
2. Once `tools/check_mcp_docs_consistency.py`'s companion doc removes
   `check_tool_counts()`, this file's top-of-file import of that name
   would raise `ImportError` at collection time if not also removed —
   these two companion docs must land together (same commit) for the test
   suite to remain importable.

## Implementation

### Target file

`tests/test_check_mcp_docs_consistency.py`

### Procedure

1. Open `tests/test_check_mcp_docs_consistency.py`.
2. In the top-of-file `from check_mcp_docs_consistency import (...)` block
   (current line 23 area), remove the `check_tool_counts,` entry, keeping
   every other imported name.
3. Confirm via `rg -n "_ALL_CATALOG_FILENAMES|_mk_all_catalog_files"
   tests/test_check_mcp_docs_consistency.py` that both symbols are used
   only within the `# ── check_tool_counts ──` section (current lines
   230-347) before proceeding.
4. Delete the section-header comment (`# ── check_tool_counts
   ──────────────────────────────────────────────────────`, current line
   230), `_ALL_CATALOG_FILENAMES` (232-239), and `_mk_all_catalog_files()`
   (241-244).
5. Delete `TestCheckToolCounts` in full (current lines 247 through the end
   of `test_one_server_incorrect_count`'s body) — all 7 methods:
   `test_correct_count_no_issue`, `test_incorrect_count_triggers_warning`,
   `test_missing_catalog_file_returns_warning`,
   `test_partial_catalog_files_missing`, `test_unknown_server_no_issue`,
   `test_multiple_servers_checked`, `test_one_server_incorrect_count`.
6. Confirm no blank-line residue remains where the deleted section used to
   sit, matching the file's existing between-section spacing.

### Method

One import-line edit, deletion of 2 Check-5-only helpers, and deletion of
1 full test class (7 methods) — no changes to any other test class or
generic helper in the file.

### Details

- Do not remove `_mk_file()` — verify via `rg` that other retained test
  classes call it before concluding this, but expect it to be a shared,
  generic `DocFile` builder used throughout the file.
- This doc must land in the same commit as the companion
  `tools/check_mcp_docs_consistency.py` doc — the import removal here and
  the symbol removal there are two halves of one atomic change.

## Validation plan

| Check | Command | Expected |
|---|---|---|
| Import removed | `grep -n "check_tool_counts" tests/test_check_mcp_docs_consistency.py` | 0 matches |
| Class removed | `grep -n "TestCheckToolCounts" tests/test_check_mcp_docs_consistency.py` | 0 matches |
| Dedicated helpers removed | `grep -n "_ALL_CATALOG_FILENAMES\|_mk_all_catalog_files" tests/test_check_mcp_docs_consistency.py` | 0 matches |
| `_mk_file` still present and used elsewhere | `grep -n "_mk_file" tests/test_check_mcp_docs_consistency.py` | present, called by other retained test classes |
| No `ImportError` | `uv run pytest tests/test_check_mcp_docs_consistency.py --collect-only -q` | collects cleanly, no `ImportError` (requires companion `tools/check_mcp_docs_consistency.py` doc applied together) |
| Remaining tests pass | `uv run pytest tests/test_check_mcp_docs_consistency.py -v` | all remaining tests pass |
| Lint | `uv run ruff check tests/test_check_mcp_docs_consistency.py` | 0 errors |
| Type check | `uv run mypy tests/test_check_mcp_docs_consistency.py` | no new errors |
