# Implementation: docs/04_mcp_04_01_web-search-file-read-github.md — update requires_config mentions to config_dependent

Source plan: `plans/20260717-173602_plan.md` ("Replace requires_config with config_dependent in MCP tool definitions")

Note: `implementations/done/20260716-141742_04_mcp_04_01_web-search-file-read-github_toolcount_removal.md.md`
matches this filename but its Goal is unrelated ("Remove the `（N個）`
parenthetical from both `**ツール（N個）:**` headings") — a stale filename
match, not covering the `requires_config` rename. Treated as
not-already-implemented.

## Goal

Update the 2 inline mentions of `requires_config` in
`docs/04_mcp_04_01_web-search-file-read-github.md` to `config_dependent`,
preserving surrounding Japanese prose. Text-only change.

## Scope

**In scope**: the 2 occurrences at lines 67 and 111 of this file.

**Out of scope**: any other content, including the `web_search` tools
section of this doc (that server has no `requires_config`/`config_dependent`
field at all — out of scope per the plan's own Scope section).

## Assumptions

- Pure text substitution: the backtick-quoted field name changes; the
  Japanese sentence around it stays as-is.
- Line 67 (`false`, in the file-read tools section) and line 111 (`true`, in
  the github tools section) both keep their existing boolean value —
  matches the code-side values in `read_tools.py` (all `False`) and the
  github `tools_*.py` files (all `True`).

## Implementation

### Target file

`/home/sugimoto/llmagent/docs/04_mcp_04_01_web-search-file-read-github.md`

### Procedure

1. Line 67: `全ツールとも config を必要としない（`requires_config: false`）。`
   (in the file-read tools section, following `read_media_file`,
   `read_multiple_files`, `search_files`, `grep_files`, `get_file_info`) ->
   replace `requires_config: false` with `config_dependent: false`.
2. Line 111: `全ツールとも config が必須（`requires_config: true`）。` (in the
   github tools section, following `github_search_code`,
   `github_create_pull_request`, etc.) -> replace `requires_config: true`
   with `config_dependent: true`.

### Method

Literal text find-and-replace of `requires_config` -> `config_dependent` at
the 2 identified lines only (verified via `grep -n "requires_config"
docs/04_mcp_04_01_web-search-file-read-github.md` — exactly 2 matches).

### Details

- These 2 lines are in different sections (file-read vs github tools) with
  different boolean values (`false` vs `true`) — edit each independently,
  do not do a naive identical-line replace across both since the surrounding
  value differs.
- Post-edit: `grep -n "requires_config"
  docs/04_mcp_04_01_web-search-file-read-github.md` -> 0 matches;
  `grep -c "config_dependent" docs/04_mcp_04_01_web-search-file-read-github.md`
  -> 2.

## Validation plan

| Check | Command | Target |
|---|---|---|
| Residual check (this file) | `grep -n "requires_config" docs/04_mcp_04_01_web-search-file-read-github.md` | 0 matches |
| New term present | `grep -c "config_dependent" docs/04_mcp_04_01_web-search-file-read-github.md` | 2 |

Full cross-file validation is covered by the cross-cutting doc
`full_validation_pass_config_dependent_rename.md`.
