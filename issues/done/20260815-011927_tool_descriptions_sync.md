# tool-descriptions-sync hook fails: fix_scripts_docstring_paths.py missing from TOOL_DESCRIPTIONS.md

## Priority
Low

## Summary
The `tool-descriptions-sync` pre-commit hook fails because `tools/fix_scripts_docstring_paths.py`
exists in the repository but is not mentioned in `tools/TOOL_DESCRIPTIONS.md`. This prevents
clean commits until the sync is resolved.

## Reason for Change
The `tool-descriptions-sync` hook enforces that every Python file under `tools/` is documented
in `tools/TOOL_DESCRIPTIONS.md`. A new tool script (`fix_scripts_docstring_paths.py`) was added
but its documentation entry was never created.

## Target Files
- `tools/fix_scripts_docstring_paths.py` (missing from TOOL_DESCRIPTIONS.md)
- `tools/TOOL_DESCRIPTIONS.md` (needs new entry)

## Current Error
```
Found 1 error(s).
[ERROR] fix_scripts_docstring_paths.py: exists in tools/ but is not mentioned in TOOL_DESCRIPTIONS.md
```

## Acceptance Criteria
- `uv run pre-commit run tool-descriptions-sync --all-files` passes without errors
- `tools/TOOL_DESCRIPTIONS.md` contains an entry for `fix_scripts_docstring_paths.py`

## Notes
This is a pre-existing issue unrelated to any recent feature changes. The tool script exists
and works correctly — only the documentation entry is missing.
