# Implementation: docs/04_mcp_04_01_web-search-file-read-github.md (drop `（N個）` from tool headings)

Source plan: `plans/20260716-135355_plan.md`

## Goal

Remove the `（N個）` parenthetical from both `**ツール（N個）:**` headings in
this catalog doc, leaving the tool-name listing intact.

## Scope

**In:**
- Line 62: `**ツール（9個）:** \`read_text_file\`, \`list_directory\`, ...`
- Line 103: `**ツール（21個）:** 全て \`github_\` 接頭辞: \`github_search_repositories\`, ...`

**Out:**
- Any other content on these lines (the tool-name listing itself is
  unchanged) or elsewhere in the file.

## Assumptions

1. The `**ツール（N個）:**` heading is followed immediately by the tool-name
   listing (verified by direct read: line 62 lists file-read-mcp's 9
   tools, line 103 lists github-mcp's 21 tools, both prefixed
   `github_`) — dropping the count leaves `**ツール:**` followed by the
   same comma-separated/prose tool list, grammatically and structurally
   intact.
2. `tools/check_mcp_docs_consistency.py`'s Check 5 (`_TOOL_COUNT_RE =
   re.compile(r"ツール（(\d+)個）")`) is the only automated consumer of this
   exact heading pattern — its removal (companion doc for that file) means
   no CI check will re-flag a missing count here after this edit.

## Implementation

### Target file

`docs/04_mcp_04_01_web-search-file-read-github.md`

### Procedure

1. Open `docs/04_mcp_04_01_web-search-file-read-github.md`.
2. Line 62: change
   ```
   **ツール（9個）:** `read_text_file`, `list_directory`, `list_directory_with_sizes`, `directory_tree`,
   ```
   to
   ```
   **ツール:** `read_text_file`, `list_directory`, `list_directory_with_sizes`, `directory_tree`,
   ```
   (keep the rest of the line/listing exactly as-is, including any
   continuation on the following line).
3. Line 103: change
   ```
   **ツール（21個）:** 全て `github_` 接頭辞: `github_search_repositories`, `github_get_file_contents`,
   ```
   to
   ```
   **ツール:** 全て `github_` 接頭辞: `github_search_repositories`, `github_get_file_contents`,
   ```

### Method

Two mechanical parenthetical removals — same find/replace shape in both
cases (`ツール（N個）:` → `ツール:`).

### Details

- Do not alter any tool name in the listing, only the heading prefix.
- Preserve exact spacing/punctuation around `**ツール:**` (bold markdown
  markers unchanged).

## Validation plan

| Check | Command | Expected |
|---|---|---|
| Parentheticals removed | `grep -n "ツール（[0-9]*個）" docs/04_mcp_04_01_web-search-file-read-github.md` | 0 matches |
| Tool listings intact | `grep -n "read_text_file\|github_search_repositories" docs/04_mcp_04_01_web-search-file-read-github.md` | unchanged, present |
