# Implementation: docs/04_mcp_04_02_file-write-file-delete-shell.md (drop `（N個）` from tool headings)

Source plan: `plans/20260716-135355_plan.md`

## Goal

Remove the `（N個）` parenthetical from all three `**ツール（N個）:**`
headings in this catalog doc.

## Scope

**In:**
- Line 26: `**ツール（4個）:** \`write_file\`, \`edit_file\`, \`create_directory\`, \`move_file\``
- Line 58: `**ツール（2個）:** \`delete_file\`, \`delete_directory\``
- Line 90: `**ツール（1個）:** \`shell_run\``

**Out:**
- Any other content on these lines or elsewhere in the file.

## Assumptions

1. Each heading is followed immediately by its complete tool-name listing
   on the same line (verified by direct read) — dropping the count leaves
   `**ツール:**` followed by the same tool list.

## Implementation

### Target file

`docs/04_mcp_04_02_file-write-file-delete-shell.md`

### Procedure

1. Open `docs/04_mcp_04_02_file-write-file-delete-shell.md`.
2. Line 26: change `**ツール（4個）:** \`write_file\`, \`edit_file\`, \`create_directory\`, \`move_file\`` to `**ツール:** \`write_file\`, \`edit_file\`, \`create_directory\`, \`move_file\``.
3. Line 58: change `**ツール（2個）:** \`delete_file\`, \`delete_directory\`` to `**ツール:** \`delete_file\`, \`delete_directory\``.
4. Line 90: change `**ツール（1個）:** \`shell_run\`` to `**ツール:** \`shell_run\``.

### Method

Three mechanical parenthetical removals, identical shape.

### Details

- Do not alter any tool name; only the `（N個）` prefix is removed from
  each heading.

## Validation plan

| Check | Command | Expected |
|---|---|---|
| Parentheticals removed | `grep -n "ツール（[0-9]*個）" docs/04_mcp_04_02_file-write-file-delete-shell.md` | 0 matches |
| Tool listings intact | `grep -n "write_file\|delete_file\|shell_run" docs/04_mcp_04_02_file-write-file-delete-shell.md` | unchanged, present |
