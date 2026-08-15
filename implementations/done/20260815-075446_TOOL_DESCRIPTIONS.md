## Goal
Add a documentation entry for `fix_scripts_docstring_paths.py` to `tools/TOOL_DESCRIPTIONS.md` in the "ドキュメント構造検証・整形補助スクリプト" section, resolving the `tool-descriptions-sync` pre-commit hook failure.

## Scope
**In-Scope**:
- Add a row to `tools/TOOL_DESCRIPTIONS.md` table in the "ドキュメント構造検証・整形補助スクリプト" section
- Row placement: before the `check_tool_descriptions_sync.py` entry
- Column 1: `fix_scripts_docstring_paths.py`
- Column 2: Japanese description matching existing format style
- Verify `uv run python -m tools.check_tool_descriptions_sync` passes

**Out-of-Scope**:
- Modifying `fix_scripts_docstring_paths.py` itself
- Any other entries in TOOL_DESCRIPTIONS.md
- New test coverage

## Assumptions
- The tool script `fix_scripts_docstring_paths.py` exists and its functionality is stable (confirmed via source review)
- The "ドキュメント構造検証・整形補助スクリプト" section is the correct location (it contains other docstring-related tools like `fix_d205.py`)
- Existing table format uses pipe-delimited Markdown tables with backtick-wrapped filenames

## Design decisions
- Place the new row before `check_tool_descriptions_sync.py` as specified in the plan, maintaining alphabetical ordering within the section
- Use Japanese description consistent with existing entries in the same section

## Alternatives considered
- Placing the entry elsewhere in the document: rejected because the "ドキュメント構造検証・整形補助スクリプト" section groups docstring-related tools together
- Using English description: rejected because all existing entries in this section use Japanese

## Implementation

### Target file
`tools/TOOL_DESCRIPTIONS.md`

### Procedure
1. Open `tools/TOOL_DESCRIPTIONS.md`
2. Locate the "ドキュメント構造検証・整形補助スクリプト" section
3. Find the `check_tool_descriptions_sync.py` entry row
4. Insert a new row before that entry:
   ```markdown
   | `fix_scripts_docstring_paths.py` | `scripts/**/*.py` のモジュールレベルdocstringヘッダーパスをリポジトリルートからの相対パス（scripts/<relpath>形式）に書き換える。--dry-run で変更内容を表示、--apply で実際に適用。 |
   ```
5. Save the file

### Method
Documentation update — single-row insertion into an existing Markdown table.

### Details
```markdown
# Before (section excerpt):
| ... | ... |
| `check_tool_descriptions_sync.py` | ... |

# After (section excerpt):
| ... | ... |
| `fix_scripts_docstring_paths.py` | `scripts/**/*.py` のモジュールレベルdocstringヘッダーパスをリポジトリルートからの相対パス（scripts/<relpath>形式）に書き換える。--dry-run で変更内容を表示、--apply で実際に適用。 |
| `check_tool_descriptions_sync.py` | ... |
```

## Compatibility considerations
- No compatibility concern — this is a documentation-only change
- The description follows the same pattern as existing entries in the section

## Security considerations
- N/A — documentation-only change

## Rollback considerations
- Remove the inserted row from `tools/TOOL_DESCRIPTIONS.md` if the sync check still fails after the change

## Validation plan

| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| tools/TOOL_DESCRIPTIONS.md | Sync check verification | `uv run python -m tools.check_tool_descriptions_sync` | Clean (no errors) |

## Out of scope
- Fixing missing entries for other tools (separate plan items)
- Modifying the `fix_scripts_docstring_paths.py` script itself
- Adding new sections or restructuring the document

## Traceability

- Workflow phase: plan-to-implementation-procedure
- Source issue: issues/20260815-011927_tool_descriptions_sync.md
- Source requirement: requires/20260815-064335_require.md
- Source plan: plans/20260815-073909_plan.md
- Source implementation procedure: N/A
- Generated at: 20260815-075446
- Related target files: tools/TOOL_DESCRIPTIONS.md, tools/fix_scripts_docstring_paths.py
