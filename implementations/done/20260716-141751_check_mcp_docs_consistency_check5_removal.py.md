# Implementation: tools/check_mcp_docs_consistency.py (remove Check 5 — Tool count consistency)

Source plan: `plans/20260716-135355_plan.md`

Note: distinct from the earlier `tools/check_mcp_docs_consistency.py`
docs (`implementations/done/20260703-124719_...md`,
`implementations/done/20260712-164929_...md`,
`implementations/done/20260712-192507_...md`), which each fixed unrelated
checks (Check-1/skip-condition wording, other checks) — none of them
touched Check 5 or removed it. This doc removes Check 5 in full, a
different target than any prior change to this file.

## Goal

Remove Check 5 ("Tool count consistency") in full — its regex, its
catalog-file tuple, its server→tools map, its two check functions, its
call site in `main()`, and its `"toolcount"` skip-option wiring (CLI
choice list + module docstring line) — since no documentation file will
contain a `ツール（N個）` heading after the companion doc edits in this same
plan land, making this check permanently a no-op.

## Scope

**In:**
- Module docstring line 13: `    --skip toolcount      Skip tool count consistency check`
- `_TOOL_COUNT_RE` (line 371)
- `_TOOL_COUNT_CATALOG_FILES` (lines 373-379)
- `_SERVER_TOOLS_MAP` (lines 381-467)
- `check_tool_counts()` (lines 470-507)
- `_check_tool_counts_for_file()` (lines 510-533)
- `_find_server_section_for_line()` (lines 536-546)
- The `"toolcount",` entry in `skip_choices` (line 914, inside `main()`)
- The `if "toolcount" not in skip: all_issues.extend(check_tool_counts(docs_dir, files))` block (lines 955-956, inside `main()`)

**Out:**
- Every other numbered check (1-4, 6-13) and their own constants/functions
  — confirmed by direct read that none of them reference `_TOOL_COUNT_RE`,
  `_TOOL_COUNT_CATALOG_FILES`, `_SERVER_TOOLS_MAP`, or any Check-5-only
  symbol.
- `_is_historical_context()` (lines 554-560) — a shared helper used by
  other checks (confirmed by its position under a "Shared helpers for new
  checks" section header, distinct from Check 5's own section) — do not
  remove it even though it is physically adjacent to the deleted Check-5
  block.
- The `--all` default behavior and every other `--skip` CLI option.

## Assumptions

1. Check 5 is the only doc-count validator in this script — Checks 1-4 and
   6-13 validate unrelated wording/terminology drift (startup modes,
   fail-open language, routing authority, active-inconsistencies
   cross-reference, live-discovery-routing, `/v1/tools`-as-routing
   -authority, tool_names-as-routing-input, audit-log format, HTTP
   transport `is_error`, stdio-transport references, watchdog-restart,
   strict-validation-skip) and do not reference any Check-5-only symbol —
   verified by reading the full file during planning.
2. `.github/workflows/mcp-docs-consistency.yml` references a nonexistent
   path (`scripts/checks/check_mcp_docs_consistency.py`) and therefore
   cannot invoke this script at all today, independent of this change —
   removing Check 5 introduces no new CI breakage (per the source plan's
   Assumption 4 / Risk R-3). Fixing that workflow path is explicitly out
   of scope for this plan.
3. The companion doc changes in this same plan (all 6 doc files) remove
   every `ツール（N個）` heading from `docs/`, so after this plan is fully
   applied, `check_tool_counts()` would find zero regex matches anyway —
   this removal is not merely "dead code cleanup ahead of its time," it is
   synchronized with the doc changes in the same plan.

## Implementation

### Target file

`tools/check_mcp_docs_consistency.py`

### Procedure

1. Open `tools/check_mcp_docs_consistency.py`.
2. Remove line 13 from the module docstring:
   ```
       --skip toolcount      Skip tool count consistency check
   ```
   (leave every other `--skip` docstring line untouched, including its
   position in the enumerated list).
3. Delete the entire "Check 5: Tool count consistency" block (current
   lines 367-546), which comprises, in order:
   - The section-header comment block (`# Check 5: Tool count
     consistency`).
   - `_TOOL_COUNT_RE = re.compile(r"ツール（(\d+)個）")`
   - `_TOOL_COUNT_CATALOG_FILES = (...)` (the 5-file tuple)
   - `_SERVER_TOOLS_MAP: dict[str, frozenset[str]] = {...}` (the full
     per-server tool-name map, ~87 lines)
   - `def check_tool_counts(docs_dir: Path, files: list[DocFile]) -> list[Issue]: ...`
   - `def _check_tool_counts_for_file(catalog_file: DocFile) -> list[Issue]: ...`
   - `def _find_server_section_for_line(catalog: DocFile, line_no: int) -> str | None: ...`

   Stop the deletion exactly before the next section header comment
   (`# Shared helpers for new checks`) — do not delete
   `_is_historical_context()` or anything below it.
4. In `main()`, remove `"toolcount",` from the `skip_choices` list (current
   line 914) — confirm the list still has valid Python syntax after
   removal (no trailing-comma issue, though a trailing comma on the
   preceding/following entry is harmless).
5. In `main()`, remove the two-line block:
   ```python
       if "toolcount" not in skip:
           all_issues.extend(check_tool_counts(docs_dir, files))
   ```
   — confirm the surrounding `if "X" not in skip: all_issues.extend(...)`
   blocks for Checks 4 and 6 remain contiguous and correctly ordered after
   this block's removal (no accidental deletion of an adjacent check's
   block).

### Method

Delete one self-contained code block (regex + 2 constants + 3 functions),
one docstring line, one CLI choice-list entry, and one function-call
block inside `main()` — no other check's code is touched.

### Details

- Do not remove `_is_historical_context()` — it is a genuinely shared
  helper (used by other checks), not part of Check 5 itself, despite
  sitting physically adjacent to it in the file.
- After deletion, run `uv run ruff check tools/check_mcp_docs_consistency.py`
  to confirm no now-unused import remains (e.g. if `re` or `frozenset`
  -adjacent imports become unused — unlikely since `re` is almost
  certainly used by other checks too, but verify rather than assume).
- Confirm `main()`'s remaining `if "X" not in skip: ...` blocks are still
  in the same relative order as before (Checks 1-4, then 6 onward),
  matching the module docstring's enumerated list order.

## Validation plan

| Check | Command | Expected |
|---|---|---|
| Check-5 symbols removed | `grep -n "_TOOL_COUNT_RE\|_TOOL_COUNT_CATALOG_FILES\|_SERVER_TOOLS_MAP\|def check_tool_counts\|def _check_tool_counts_for_file\|def _find_server_section_for_line" tools/check_mcp_docs_consistency.py` | 0 matches |
| `toolcount` skip option removed | `grep -n "toolcount" tools/check_mcp_docs_consistency.py` | 0 matches |
| `_is_historical_context` intact | `grep -n "_is_historical_context" tools/check_mcp_docs_consistency.py` | still present, unchanged |
| CLI rejects `toolcount` | `uv run python tools/check_mcp_docs_consistency.py --skip toolcount` | `argparse` error: invalid choice `'toolcount'` |
| Default run clean | `uv run python tools/check_mcp_docs_consistency.py` | exits 0 (or with only unrelated pre-existing issues), no tool-count-related output |
| Lint | `uv run ruff check tools/check_mcp_docs_consistency.py` | 0 errors |
| Type check | `uv run mypy tools/check_mcp_docs_consistency.py` | no new errors |
| Companion test file | `uv run pytest tests/test_check_mcp_docs_consistency.py -v` (after companion doc for that file also lands) | passes, no `ImportError` from the removed `check_tool_counts` symbol |
