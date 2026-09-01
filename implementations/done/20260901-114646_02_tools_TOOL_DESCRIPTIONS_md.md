## Goal
Add an entry documenting `tools/manage_workitem_stage.py` to
`tools/TOOL_DESCRIPTIONS.md`, consistent with existing per-tool rows, and confirm
`tools/check_tool_descriptions_sync.py` passes afterward (REQ-007).

## Scope
- In scope: adding one row/entry for `manage_workitem_stage.py`, following the
  file's established `manage_*` naming-convention row pattern (e.g. the
  `manage_frontmatter.py` entry).
- Out of scope: any other edit to `tools/TOOL_DESCRIPTIONS.md`.

## Assumptions
- `tools/TOOL_DESCRIPTIONS.md` already documents `manage_frontmatter.py` as a
  subcommand-style entry (`add-missing`/`dedupe-lists`), giving the row pattern
  this new entry should follow.

## Design decisions
- Match the existing `manage_frontmatter.py` entry's format (tool name, its
  subcommands, one-line purpose per subcommand) rather than inventing a new
  entry style.

## Alternatives considered
- Creating a new section for stage-transition tooling: rejected — a single new
  tool fits within the existing per-tool entry convention.

## Implementation
### Target file
`tools/TOOL_DESCRIPTIONS.md`

### Procedure
1. Locate the existing `manage_frontmatter.py` entry as the format reference.
2. Add a new entry for `manage_workitem_stage.py` describing its three
   subcommands (`close-issue`, `close-plan`, `close-implementation`), the
   `git mv`-based archival move behavior, and the `close-implementation`
   Pending-row block with `--force --reason` override.

### Method
Direct Markdown edit; verified by `tools/check_tool_descriptions_sync.py`, which
matches backtick-quoted `*.py` filenames anywhere in the file against the live
contents of `tools/*.py` (confirmed via reading that script: regex-extracted
`` `([a-zA-Z0-9_]+\.py)` `` occurrences diffed against `TOOLS_DIR.glob("*.py")`,
independent of table/section placement).

### Details
- The added entry must contain `` `manage_workitem_stage.py` `` in backticks so
  the sync checker's regex match succeeds.
- State explicitly that `close-implementation` blocks on a `Pending` Execution
  Status row unless overridden, and that the tool does not edit file content
  beyond performing the move — avoids a future reader assuming it auto-fixes
  Execution Status rows.

## Compatibility considerations
Documentation-only change; no code path reads this file except
`tools/check_tool_descriptions_sync.py` (regex-based) and human/agent readers per
`rules/ai-execution.md` Repository Tool Usage. No compatibility impact.

## Security considerations
N/A: Markdown documentation edit only, no executable content, no secrets.

## Rollback considerations
Single-entry addition to an existing Markdown file; rollback is removing the
added entry. No other file depends on this entry's wording.

## Validation plan
| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| `tools/TOOL_DESCRIPTIONS.md` | Consistency | `uv run python tools/check_tool_descriptions_sync.py` | Exit 0, no `[ERROR]` lines (requires `tools/manage_workitem_stage.py` to already exist per seq 01 of this Plan) |

## Completion criteria
- `tools/TOOL_DESCRIPTIONS.md` documents `manage_workitem_stage.py` (AC-4).
- `uv run python tools/check_tool_descriptions_sync.py` passes once
  `tools/manage_workitem_stage.py` exists (REQ-007).

## Out of scope
Any other edit to `tools/TOOL_DESCRIPTIONS.md` beyond the one new entry.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 20260901-152906 | 20260901-152906 | Added `manage_workitem_stage.py` row to the "ドキュメント構造検証・整形補助スクリプト" table, next to `manage_frontmatter.py`; adversarial verification confirmed the three subcommands, `git mv`-based move, and `close-implementation` Pending-block/`--force --reason` behavior against current `tools/manage_workitem_stage.py` source |
| 2 | Add or update tests per Validation plan | Completed | 20260901-152906 | 20260901-152906 | N/A: documentation-only entry addition; verified by the sync checker, not a pytest test |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20260901-152906 | 20260901-152906 | `uv run python tools/check_tool_descriptions_sync.py` -> "No issues found."; `uv run pytest tests/tools/ -v --continue-on-collection-errors` -> 68 passed, 1 pre-existing collection error (`test_check_agent_docs_consistency.py`, unrelated) |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Completed | 20260901-152906 | 20260901-152906 | N/A: no `docs/00_index.md` task-scope row maps specifically to a `TOOL_DESCRIPTIONS.md` single-entry addition (checked "tools/ scripts overview" row -> `tools/01_overview.md`; not a file-level match) — consistent with the precedent from the two prior `_02_tools_TOOL_DESCRIPTIONS_md.md` cycles, neither of which edited `docs/00_index.md` or `tools/01_overview.md` |

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
- **Source issue**: `issues/20260831-194739_tool004_manage_workitem_stage_transitions.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20260901-110946_plan.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260901-114646
- **Related target files**: `tools/TOOL_DESCRIPTIONS.md`
