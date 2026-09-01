## Goal
Document `tools/generate_workitem.py` in `tools/TOOL_DESCRIPTIONS.md`, consistent with
the file's established `generate_*` table, so `tools/check_tool_descriptions_sync.py`
passes (REQ-005).

## Scope
- In scope: adding one row for `generate_workitem.py` to the existing
  "リファレンス自動生成スクリプト" table (or an equivalently placed `generate_*` entry) in
  `tools/TOOL_DESCRIPTIONS.md`.
- Out of scope: any other edit to `tools/TOOL_DESCRIPTIONS.md`; documenting the four
  other tools tracked as separate issues (traceability checking, stage-transition
  automation, document renaming, Known Deviation/Known Issue sync checking).

## Assumptions
- The new entry follows the same two-column row pattern already used by
  `generate_reference_table.py` and `generate_mcp_inventory.py` in the current
  "リファレンス自動生成スクリプト" table (confirmed present at the read time of this
  document: `| generate_reference_table.py | --type rag|mcp|deployment で指定 | ... |`,
  `| generate_mcp_inventory.py | --format json|csv で指定 | ... |`).

## Design decisions
- Add the new row to the existing `generate_*` table rather than creating a new
  table/section — `generate_workitem.py` matches that table's established purpose
  (scripts that produce new content) more closely than the other categorized
  sections in this file (documentation structure/validation, Front Matter, etc.).

## Alternatives considered
- Creating a separate "ワークアイテム生成スクリプト" section: rejected — a single new tool
  does not warrant a new section when the existing `generate_*` table's stated
  purpose already fits.

## Implementation
### Target file
`tools/TOOL_DESCRIPTIONS.md`

### Procedure
1. Locate the existing "リファレンス自動生成スクリプト" table (rows for
   `generate_reference_table.py` and `generate_mcp_inventory.py`).
2. Add one new row for `generate_workitem.py`, describing its `--kind
   {issue,plan,implementation-procedure}` flag and the work-item document kind it
   produces, following the existing rows' column pattern (generation-mode column,
   output-destination column).

### Method
Direct Markdown table-row edit; no script or automation involved — this is a
documentation-only change verified by `tools/check_tool_descriptions_sync.py`,
which matches backtick-quoted `*.py` filenames anywhere in the file against the
live contents of `tools/*.py` (confirmed via reading
`tools/check_tool_descriptions_sync.py`: it extracts `` `([a-zA-Z0-9_]+\.py)` ``
occurrences and diffs them against `TOOLS_DIR.glob("*.py")`, independent of which
section/table the backtick reference appears in).

### Details
- The added row must contain `` `generate_workitem.py` `` in backticks so the sync
  checker's regex match succeeds.
- Describe the `--kind` flag's three values and that the tool writes a
  placeholder-only skeleton (no substantive content) to keep the entry consistent
  with this Plan's Out-of-Scope statement, avoiding a misleading implication that
  the tool generates finished documents.

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
| `tools/TOOL_DESCRIPTIONS.md` | Consistency | `uv run python tools/check_tool_descriptions_sync.py` | Pass, no drift (requires `tools/generate_workitem.py` to already exist per seq 01 of this Plan) |

## Completion criteria
- `tools/TOOL_DESCRIPTIONS.md` contains a row documenting `generate_workitem.py`
  (AC4).
- `uv run python tools/check_tool_descriptions_sync.py` passes once
  `tools/generate_workitem.py` exists (REQ-005).

## Out of scope
- Any other edit to `tools/TOOL_DESCRIPTIONS.md` beyond the one new row.
- Documenting the four other tools tracked as separate issues.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 20260901-122201 | 20260901-122201 | Adversarial verification confirmed `tools/generate_workitem.py` exists, its `--kind {issue,plan,implementation-procedure}` flag, and the existing table rows; no correction to this procedure needed. Added one row for `generate_workitem.py` to the "リファレンス自動生成スクリプト" table |
| 2 | Add or update tests per Validation plan | Completed | 20260901-122201 | 20260901-122201 | N/A: documentation-only row addition; verified by the sync checker, not a pytest test |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20260901-122201 | 20260901-122201 | `uv run python tools/check_tool_descriptions_sync.py` -> "No issues found." Also ran `uv run pytest tests/tools/ -v` (52 passed; pre-existing unrelated collection error in `test_check_agent_docs_consistency.py` ignored per instruction) |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Completed | 20260901-122201 | 20260901-122201 | N/A: no `docs/00_index.md` "Document References by Task" row maps `tools/TOOL_DESCRIPTIONS.md` or `generate_workitem.py`; no edit made |

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
- **Requirement ID**: REQ-005
- **Source issue**: `issues/20260831-194739_tool002_generate_workitem_scaffold.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20260901-105731_plan.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260901-113804
- **Related target files**: `tools/TOOL_DESCRIPTIONS.md`
