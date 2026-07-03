## Goal

Fix the comment for `command_defs.py` in `docs/01_overview-files.md` (remove the incorrect "コマンド定義の単一ソース" claim) and add a missing entry for `command_defs_list.py` with a correct ownership comment.

## Scope

- In-Scope:
  - Line 95: change the inline comment from `# CommandDef / SubcommandSpec データクラス (コマンド定義の単一ソース)` to `# CommandDef / SubcommandSpec データクラス (データクラス定義のみ; _COMMANDS は持たない)`
  - Insert a new line immediately after the `command_defs.py` line: `├─ command_defs_list.py  # _COMMANDS: 全組み込みスラッシュコマンドの単一ソース (コマンド追加はここへ)`
  - Preserve exact indentation and tree-drawing characters of the surrounding lines
- Out-of-Scope:
  - Any other line in `docs/01_overview-files.md`
  - `registry.py` entry (line 94) — not changing its comment
  - Other documentation files

## Assumptions

1. Line 95 currently reads: `│   │   │   ├─ command_defs.py              # CommandDef / SubcommandSpec データクラス (コマンド定義の単一ソース)` (confirmed by reading the file).
2. The indentation prefix for entries inside `scripts/agent/commands/` is `│   │   │   ├─ ` (16 characters plus tree glyphs) — must match exactly to preserve Markdown code block rendering.
3. `command_defs_list.py` has no existing entry in the file tree section (confirmed: only `command_defs.py` appears, not `command_defs_list.py`).
4. Inserting the new line directly after `command_defs.py` (between `command_defs.py` and `mixin_base.py`) is the correct alphabetical/logical position.

## Implementation

### Target file

`/home/masaos/llmagent/docs/01_overview-files.md`

### Procedure

1. Read line 94–96 of the file to confirm the exact content (including whitespace and tree-drawing characters) of the `command_defs.py` line and the line immediately following it.
2. Use `Edit` tool to replace the single line for `command_defs.py` with two lines:
   - Line A (updated): `command_defs.py` with the corrected comment
   - Line B (new): `command_defs_list.py` entry with the ownership comment
3. Verify the surrounding lines (e.g., `mixin_base.py`) were not disturbed.

### Method

`old_string` (single line, exact current text from line 95):
```
				├─ command_defs.py              # CommandDef / SubcommandSpec データクラス (コマンド定義の単一ソース)
```

`new_string` (two lines — same indent prefix for both):
```
				├─ command_defs.py              # CommandDef / SubcommandSpec データクラス (データクラス定義のみ; _COMMANDS は持たない)
				├─ command_defs_list.py         # _COMMANDS: 全組み込みスラッシュコマンドの単一ソース (コマンド追加はここへ)
```

IMPORTANT: The indentation before `├─` is produced by spaces (not tabs) in the Markdown fenced code block. Read the actual bytes of line 95 first and copy the prefix character-for-character.

### Details

- The file uses a Markdown fenced code block (` ``` `) to render the directory tree; all entries inside must use consistent spacing.
- Current line 94: `registry.py` entry — do not touch.
- Current line 95: `command_defs.py` — this is the target for the comment fix + insertion.
- Current line 96: `mixin_base.py` — must remain unchanged after the edit.
- The new `command_defs_list.py` line uses `├─` (not `└─`) because it is not the last item in the directory listing.

## Validation plan

```bash
# Confirm command_defs_list.py now appears in the file
grep "command_defs_list" docs/01_overview-files.md

# Confirm the old incorrect comment is gone
grep "コマンド定義の単一ソース" docs/01_overview-files.md
# Expected: no output (zero matches)

# Confirm the correct comment for command_defs.py is present
grep "command_defs\.py" docs/01_overview-files.md
# Expected: line with "データクラス定義のみ; _COMMANDS は持たない"

# Confirm registry.py entry is unchanged
grep "registry\.py" docs/01_overview-files.md

# Full test suite (no runtime breakage)
uv run pytest tests/
```

Expected: first `grep` has one match; second `grep` has no output; third `grep` shows the corrected comment; tests pass.
