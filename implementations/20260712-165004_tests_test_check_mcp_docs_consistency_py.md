# Implementation Procedure: tests/test_check_mcp_docs_consistency.py — TestCheckToolCounts fixtures

Source plan: `plans/20260712-163137_plan.md`, Implementation steps 4-5

## Goal

Update `TestCheckToolCounts`'s fixtures to use the real documentation convention (fullwidth
parentheses, `ツール（N個）`, real filenames) instead of a synthetic format that never matched
production docs — the mismatch that let the underlying checker bug go unnoticed. Add a
partial-file-missing test case.

## Scope

**In scope:**
- `tests/test_check_mcp_docs_consistency.py`: `TestCheckToolCounts` class (currently lines
  233-306) — all 6 existing tests' fixtures, plus one new test.

**Out of scope:**
- Any other test class in this file.
- `tools/check_mcp_docs_consistency.py` — implemented in the paired doc
  (`implementations/20260712-164929_tools_check_mcp_docs_consistency_py.md`); this task assumes
  that change lands first (or concurrently) since these tests exercise the new behavior.

## Assumptions

1. The `_mk_file(rel: str, lines: list[str]) -> DocFile` helper (line 32) is reused as-is; no
   changes to test helpers are needed.
2. Real doc line format, confirmed by direct read of `docs/04_mcp_04_04_mdq.md:26` and
   `docs/04_mcp_04_01_web-search-file-read-github.md:31`:
   - Heading: `## <server-name>-mcp（ポート NNNN）` (fullwidth parens, e.g.
     `## web-search-mcp（ポート 8004）`)
   - Count line: `**ツール（N個）:**` (e.g. `**ツール（9個）:**`)
3. `rel_path` in test fixtures must be one of the 5 real filenames now recognized by
   `_TOOL_COUNT_CATALOG_FILES` (see the paired tool implementation doc), not the old
   `"04_mcp_04_server_catalog.md"`.

## Implementation

### Target file

`tests/test_check_mcp_docs_consistency.py`

### Procedure

For each existing test in `TestCheckToolCounts` (lines 233-306), update the fixture's `rel_path`
and line content to the real format:

1. `test_correct_count_no_issue`: `rel_path="04_mcp_04_01_web-search-file-read-github.md"`,
   lines `["## web-search-mcp（ポート 8004）", "**ツール（1個）:** search_web"]`.
2. `test_incorrect_count_triggers_warning`: same `rel_path`, lines
   `["## web-search-mcp（ポート 8004）", "**ツール（2個）:** search_web"]` (documented count 2,
   expected 1 — mismatch).
3. `test_missing_catalog_file_returns_warning`: rename in spirit to "all 5 catalog files
   missing" — construct a `DocFile` (or empty `files` list) whose `rel_path` is none of the 5
   `_TOOL_COUNT_CATALOG_FILES` entries (e.g. keep the existing
   `rel_path="04_mcp_02_protocol_and_transport.md"`, which is unrelated and already not in the
   catalog list) and assert the "none found" WARNING fires.
4. `test_unknown_server_no_issue`: `rel_path="04_mcp_04_01_web-search-file-read-github.md"`,
   lines `["## unknown-mcp（ポート 9999）", "**ツール（5個）:** fake_tool"]`.
5. `test_multiple_servers_checked`: use two real servers from the same real file, e.g.
   `rel_path="04_mcp_04_02_file-write-file-delete-shell.md"`, lines
   `["## file-write-mcp（ポート 8007）", "**ツール（4個）:** write_file, edit_file, create_directory, move_file",
   "## file-delete-mcp（ポート 8008）", "**ツール（2個）:** delete_file, delete_directory"]`
   (matches `_SERVER_TOOLS_MAP["file-write-mcp"]` and `["file-delete-mcp"]` exactly — both
   counts correct, expect no issues).
6. `test_one_server_incorrect_count`: same two-server fixture as above but with one count wrong,
   e.g. `"**ツール（3個）:** ..."` for file-write-mcp (documented 3, expected 4) — assert exactly
   one issue mentioning `"file-write-mcp"`.
7. **New test** `test_partial_catalog_files_missing`: construct `files` with only 1 of the 5
   `_TOOL_COUNT_CATALOG_FILES` present (e.g. only
   `"04_mcp_04_01_web-search-file-read-github.md"`, correctly formatted with no count mismatch)
   plus one unrelated `DocFile`. Assert the result contains a WARNING issue naming at least one
   of the 4 missing catalog filenames, and does NOT contain a tool-count-mismatch issue (since
   the one present file's counts are correct).

### Method

Use `docs/04_mcp_04_02_file-write-file-delete-shell.md` and
`docs/04_mcp_04_01_web-search-file-read-github.md` as the source of truth for exact heading text
— copy the real lines via `grep -n "^## \|ツール（" docs/04_mcp_04_01_web-search-file-read-github.md
docs/04_mcp_04_02_file-write-file-delete-shell.md` rather than retyping the fullwidth parentheses
by hand, to avoid introducing halfwidth/fullwidth typos in the test fixtures themselves.

### Details

- Keep each test's assertion style consistent with the existing tests (`assert not issues`,
  `assert len(issues) == 1`, `assert "..." in issues[0].message`).
- Do not remove any existing test; only update fixture content and add the one new test.

## Validation plan

| Check | Command | Expected |
|---|---|---|
| Unit tests | `uv run pytest tests/test_check_mcp_docs_consistency.py -v -k TestCheckToolCounts` | All tests pass, including the new partial-missing case |
| Full suite | `uv run pytest tests/test_check_mcp_docs_consistency.py -v` | No regressions in other test classes |
| Lint | `uv run ruff check tests/test_check_mcp_docs_consistency.py` | 0 errors |
