# Implementation: docs/04_mcp_04_02_file-write-file-delete-shell.md — update requires_config mentions to config_dependent

Source plan: `plans/20260717-173602_plan.md` ("Replace requires_config with config_dependent in MCP tool definitions")

Note: `implementations/done/20260716-141743_04_mcp_04_02_file-write-file-delete-shell_toolcount_removal.md.md`
matches this filename but its Goal is unrelated ("Remove the `（N個）`
parenthetical from all three `**ツール（N個）:**` headings") — a stale
filename match, not covering the `requires_config` rename. Treated as
not-already-implemented.

## Goal

Update the 2 inline mentions of `requires_config` in
`docs/04_mcp_04_02_file-write-file-delete-shell.md` to `config_dependent`,
preserving surrounding Japanese prose. Text-only change.

## Scope

**In scope**: the 2 occurrences at lines 28 and 60 of this file.

**Out of scope**: any other content (tool lists, config field names, etc.).

## Assumptions

- Pure text substitution: the backtick-quoted field name changes; the
  Japanese sentence around it ("config を必要としない") stays as-is since
  the semantic claim (write/delete file tools do NOT need config) is
  unaffected by the rename.
- Both occurrences currently read `false` (matches code-side value in
  `write_tools.py`/`delete_tools.py`, both all-`False` per plan Scope).

## Implementation

### Target file

`/home/sugimoto/llmagent/docs/04_mcp_04_02_file-write-file-delete-shell.md`

### Procedure

1. Line 28: `全ツールとも config を必要としない（`requires_config: false`）。`
   (in the write-tools section, following `write_file`, `edit_file`,
   `create_directory`, `move_file`) -> replace `requires_config: false` with
   `config_dependent: false` inside the backticks.
2. Line 60: same sentence structure, in the delete-tools section (following
   `delete_file`, `delete_directory`) -> same replacement.

### Method

Literal text find-and-replace of `requires_config` -> `config_dependent` at
the 2 identified lines only (verified via `grep -n "requires_config"
docs/04_mcp_04_02_file-write-file-delete-shell.md`).

### Details

- Both lines have identical sentence structure but appear in different
  sections (write-tools vs delete-tools); edit each independently since a
  naive global search-replace of the exact line text would work here too
  (both lines are textually identical), but treat as 2 separate edit
  targets for clarity and to avoid missing either.
- Post-edit: `grep -n "requires_config"
  docs/04_mcp_04_02_file-write-file-delete-shell.md` -> 0 matches;
  `grep -c "config_dependent" docs/04_mcp_04_02_file-write-file-delete-shell.md`
  -> 2.

## Validation plan

| Check | Command | Target |
|---|---|---|
| Residual check (this file) | `grep -n "requires_config" docs/04_mcp_04_02_file-write-file-delete-shell.md` | 0 matches |
| New term present | `grep -c "config_dependent" docs/04_mcp_04_02_file-write-file-delete-shell.md` | 2 |

Full cross-file validation is covered by the cross-cutting doc
`full_validation_pass_config_dependent_rename.md`.
