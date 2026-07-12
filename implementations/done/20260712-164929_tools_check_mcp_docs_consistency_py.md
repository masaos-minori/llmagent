# Implementation Procedure: tools/check_mcp_docs_consistency.py — restore tool-count check

Source plan: `plans/20260712-163137_plan.md`, Implementation steps 1-3, 6

## Goal

Restore `check_tool_counts()` to actually detect documented-vs-canonical MCP tool count drift,
which has been silently broken since the docs were split (commit `49154b4a`) in three
independent ways: stale target filename, stale regex, and a heading-parser bug.

## Scope

**In scope:**
- `tools/check_mcp_docs_consistency.py`: `_TOOL_COUNT_RE`, `_find_server_section_for_line()`,
  `check_tool_counts()`.

**Out of scope:**
- `_SERVER_TOOLS_MAP` (the canonical `frozenset` definitions) — not modified.
- `docs/04_mcp_04_01`..`05` content — not modified.
- `tests/test_check_mcp_docs_consistency.py` — separate implementation doc
  (`implementations/20260712-165005_tests_test_check_mcp_docs_consistency_py.md`).

## Assumptions

1. `_TOOL_COUNT_RE = re.compile(r"\bTools\((\d+)\)")` is still at line 371 as of this writing —
   reconfirm with a direct read before editing.
2. `_SERVER_TOOLS_MAP` starts at line 373 (not 371 — 371 is `_TOOL_COUNT_RE`; this was a citation
   error caught during plan review, now corrected).
3. `_find_server_section_for_line()` (lines 499-509) is called only from `check_tool_counts()` —
   reconfirmed via `grep -n "_find_server_section_for_line" tools/check_mcp_docs_consistency.py`
   at planning time; no other check function depends on it, so its regex fix is isolated.
4. The real doc convention is `**ツール（N個）:**` (fullwidth parentheses, Japanese `個`) — confirmed
   present in `docs/04_mcp_04_01`..`05` (9 occurrences via `grep -n "ツール（" docs/04_mcp_04_*.md`);
   `web-search-mcp`'s single-tool section (`docs/04_mcp_04_01...md:37`, `**ツール:**` with no count)
   has no count annotation and will simply not match — this is expected, not a bug to fix here.

## Implementation

### Target file

`tools/check_mcp_docs_consistency.py`

### Procedure

1. **Fix `_TOOL_COUNT_RE`** (currently line 371): change
   `re.compile(r"\bTools\((\d+)\)")` to `re.compile(r"ツール（(\d+)個）")`.
2. **Fix `_find_server_section_for_line()`** (currently lines 499-509): change the heading match
   from `re.match(r"^## (\S+)", line)` to `re.match(r"^## ([\w-]+)", line)`. This stops the match
   at the fullwidth `（` character instead of swallowing it (Python's `\w` treats fullwidth
   parentheses as non-word characters even with Unicode-aware matching, so this is sufficient —
   no `re.UNICODE`/`re.ASCII` flag changes needed). The subsequent
   `section_name = m.group(1).split("(")[0].strip()` line may be left as-is (harmless no-op with
   the new regex, since no ASCII `(` will ever appear in the captured group) or simplified to
   `section_name = m.group(1)` — prefer the smaller diff (leave the `.split("(")[0].strip()` line
   untouched) unless it visibly confuses a reviewer.
3. **Rewrite `check_tool_counts()`** (currently lines 454-496):
   - Define a module-level tuple near the existing constants (e.g. right after
     `_SERVER_TOOLS_MAP`'s closing `}`):
     ```python
     _TOOL_COUNT_CATALOG_FILES = (
         "04_mcp_04_01_web-search-file-read-github.md",
         "04_mcp_04_02_file-write-file-delete-shell.md",
         "04_mcp_04_03_rag-pipeline-and-cicd.md",
         "04_mcp_04_04_mdq.md",
         "04_mcp_04_05_git.md",
     )
     ```
   - Change the file-lookup from a single `catalog_file` to collecting all `DocFile`s whose
     `rel_path` is in `_TOOL_COUNT_CATALOG_FILES`.
   - If **none** are found, return one `Issue(file="docs/", line_no=0, severity="WARNING",
     message=...)` listing all 5 expected filenames (update the message text — it currently
     names only the old single filename).
   - If **some** are missing (partial), for each missing filename append an individual
     `Issue(..., message=f"{filename} not found — cannot verify tool counts for its section(s).")`
     and continue processing the ones that were found (do not early-return in the partial case).
   - For each found `DocFile`, run the existing per-line scan logic (search `_TOOL_COUNT_RE` per
     line, resolve `_find_server_section_for_line(doc, i)`, compare against
     `_SERVER_TOOLS_MAP`) — this inner loop's logic does not change, only its outer wrapping (one
     file instead of many).
4. **Do not change** `_SERVER_TOOLS_MAP` itself, and do not add a "server name → file name"
   mapping table — it was considered in planning and found unnecessary once
   `_find_server_section_for_line()` is fixed (each file resolves its own section names
   independently).

### Method

Pseudocode sketch for the rewritten `check_tool_counts()` (illustrative only):

```python
_TOOL_COUNT_CATALOG_FILES = (...)  # see above

def check_tool_counts(docs_dir: Path, files: list[DocFile]) -> list[Issue]:
    catalog_files = [d for d in files if d.rel_path in _TOOL_COUNT_CATALOG_FILES]
    issues: list[Issue] = []
    if not catalog_files:
        issues.append(Issue(file="docs/", line_no=0, severity="WARNING",
                             message=f"None of {_TOOL_COUNT_CATALOG_FILES} found — cannot verify tool counts."))
        return issues
    found_names = {d.rel_path for d in catalog_files}
    for missing in set(_TOOL_COUNT_CATALOG_FILES) - found_names:
        issues.append(Issue(file="docs/", line_no=0, severity="WARNING",
                             message=f"{missing} not found — cannot verify tool counts for its section(s)."))
    for catalog_file in catalog_files:
        for i, line in enumerate(catalog_file.lines, start=1):
            m = _TOOL_COUNT_RE.search(line)
            if m:
                server_section = _find_server_section_for_line(catalog_file, i)
                if server_section and server_section in _SERVER_TOOLS_MAP:
                    expected_count = len(_SERVER_TOOLS_MAP[server_section])
                    doc_count = int(m.group(1))
                    if doc_count != expected_count:
                        issues.append(Issue(file=catalog_file.rel_path, line_no=i, severity="WARNING",
                                             message=f"Tool count mismatch for {server_section}: documented {doc_count}, expected {expected_count}"))
    return issues
```

### Details

- Keep `Issue`, `DocFile` dataclass usage identical to the rest of the file (no new dataclass
  fields).
- Preserve the `--skip toolcount` behavior in `main()` (line ~909-910) unchanged — it already
  gates the call to `check_tool_counts()` and needs no edit.
- Run `uv run radon cc tools/check_mcp_docs_consistency.py -s` after the rewrite and confirm
  `check_tool_counts()` stays at grade B or better (baseline before this change: CC 9); if it
  climbs meaningfully higher, consider extracting the per-file inner loop into a small private
  helper (e.g. `_check_tool_counts_for_file(doc: DocFile) -> list[Issue]`) — optional, only if
  complexity actually regresses.

## Validation plan

| Check | Command | Expected |
|---|---|---|
| Unit tests | `uv run pytest tests/test_check_mcp_docs_consistency.py -v` | All `TestCheckToolCounts` tests pass (after the companion test-fixture update lands — see the paired implementation doc) |
| Live run | `uv run python tools/check_mcp_docs_consistency.py` | No `04_mcp_04_server_catalog.md not found` warning; no new tool-count mismatch warnings unless a real drift exists |
| Lint | `uv run ruff check tools/check_mcp_docs_consistency.py` | 0 errors |
| Type check | `uv run mypy tools/check_mcp_docs_consistency.py` | no new errors |
| Complexity | `uv run radon cc tools/check_mcp_docs_consistency.py -s -n C` | `check_tool_counts` grade B or better |
