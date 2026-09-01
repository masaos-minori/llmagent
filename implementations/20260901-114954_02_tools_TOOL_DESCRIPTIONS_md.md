## Goal
Document `tools/rename_doc.py` in `tools/TOOL_DESCRIPTIONS.md`'s
"ドキュメント構造検証・整形補助スクリプト" table, the same table as
`rename_mcp_modules.py`, so `tools/check_tool_descriptions_sync.py` passes
(REQ-007).

## Scope
- In scope: adding one row for `rename_doc.py` to the
  "ドキュメント構造検証・整形補助スクリプト" table (confirmed: this is the table
  containing `rename_mcp_modules.py`'s row, at that section's heading).
- Out of scope: any other edit to `tools/TOOL_DESCRIPTIONS.md`; documenting the
  other tools tracked as separate issues.

## Assumptions
- The table's existing `rename_mcp_modules.py` row (one line, tool name column +
  free-text description column) is the format pattern this new row follows.

## Design decisions
- Add the new row immediately adjacent to (or within) the same table as
  `rename_mcp_modules.py`'s row, per the Plan's explicit instruction, rather than
  creating a new section — both tools share the `rename_*` naming convention
  already documented in this file's intro line ("`merge_part_files.py`/
  `rename_*` = 個別操作").

## Alternatives considered
- Creating a new section for documentation-rename tooling: rejected — the
  Plan's Scope explicitly places this entry in the same table as
  `rename_mcp_modules.py`.

## Implementation
### Target file
`tools/TOOL_DESCRIPTIONS.md`

### Procedure
1. Locate the "ドキュメント構造検証・整形補助スクリプト" table (confirmed at this
   file's line 32 heading, containing `rename_mcp_modules.py`'s row).
2. Add a new row for `rename_doc.py` describing: its `<old-path> <new-path>`
   arguments, the `git mv` + Markdown-link rewrite behavior, the opt-in
   `--old-title`/`--new-title` flag, and its `--dry-run` (default) / `--apply`
   modes.

### Method
Direct Markdown table-row edit; verified by
`tools/check_tool_descriptions_sync.py`, which matches backtick-quoted `*.py`
filenames anywhere in the file against the live contents of `tools/*.py`
(confirmed via reading that script: regex-extracted
`` `([a-zA-Z0-9_]+\.py)` `` occurrences diffed against `TOOLS_DIR.glob("*.py")`,
independent of table/section placement).

### Details
- The added row must contain `` `rename_doc.py` `` in backticks so the sync
  checker's regex match succeeds.
- Mention explicitly that the tool defaults to `--dry-run` and requires
  `--apply` to write, matching the row-description style already used for other
  `--dry-run`/`--apply` tools in this same table (e.g. `fix_docs_section_marks.py`'s
  row states "`--apply` を付けない限り dry-run").
- State that writes are restricted to `docs/` only, to avoid a future reader
  assuming broader scope.

## Compatibility considerations
Documentation-only change; no code path reads this file except
`tools/check_tool_descriptions_sync.py` (regex-based) and human/agent readers per
`rules/ai-execution.md` Repository Tool Usage. No compatibility impact.

## Security considerations
N/A: Markdown documentation edit only, no executable content, no secrets.

## Rollback considerations
Single-row addition to an existing Markdown table; rollback is removing the added
row. No other file depends on this specific row's wording.

## Validation plan
| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| `tools/TOOL_DESCRIPTIONS.md` | Consistency | `uv run python tools/check_tool_descriptions_sync.py` | Pass, no drift (requires `tools/rename_doc.py` to already exist per seq 01 of this Plan) |

## Completion criteria
- `tools/TOOL_DESCRIPTIONS.md` contains a row documenting `rename_doc.py` in the
  "ドキュメント構造検証・整形補助スクリプト" table (AC5).
- `uv run python tools/check_tool_descriptions_sync.py` passes once
  `tools/rename_doc.py` exists (REQ-007).

## Out of scope
- Any other edit to `tools/TOOL_DESCRIPTIONS.md` beyond the one new row.
- Documenting the other tools tracked as separate issues.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | |
| 2 | Add or update tests per Validation plan | Pending | — | — | N/A: documentation-only row addition; verified by the sync checker, not a pytest test |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | `uv run python tools/check_tool_descriptions_sync.py` only — this file is outside `scripts/`, so ruff/mypy/lint-imports do not apply |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Pending | — | — | This step's own subject is the documentation update; no further doc dependency |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| — | — | — | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| — | — | — | — | — | — |

## Traceability
- **Workflow phase**: plan-to-implementation-procedure
- **Requirement ID**: REQ-007
- **Source issue**: `issues/20260831-194739_tool005_rename_doc_and_update_references.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20260901-111505_plan.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260901-114954
- **Related target files**: `tools/TOOL_DESCRIPTIONS.md`
