## Goal
Add an entry for `tools/check_workitem_traceability.py` to `tools/TOOL_DESCRIPTIONS.md`'s
checker table, and confirm `tools/check_tool_descriptions_sync.py` passes afterward
(REQ-007).

## Scope
- In scope: adding one row for `check_workitem_traceability.py` to the existing
  checker table in `tools/TOOL_DESCRIPTIONS.md`, following the table's established
  column format (file / target domain or overview / main checks).
- Out of scope: any other edit to `tools/TOOL_DESCRIPTIONS.md`; documenting the
  sibling tools tracked as separate issues.

## Assumptions
- `tools/TOOL_DESCRIPTIONS.md` already contains a checker table (rows for other
  `check_*.py` scripts) whose column pattern this new row must follow — confirmed
  via Read at Plan time.

## Design decisions
- Add the new row to the existing checker table rather than creating a new
  section — `check_workitem_traceability.py` is a `check_*` script matching that
  table's established purpose.

## Alternatives considered
- Creating a new section specifically for workitem-traceability tooling: rejected
  — a single new checker does not warrant a new section when the existing checker
  table's stated purpose already fits.

## Implementation
### Target file
`tools/TOOL_DESCRIPTIONS.md`

### Procedure
1. Locate the existing checker table (rows for other `check_*.py` scripts, e.g.
   `check_compat_shims.py`, `check_tool_descriptions_sync.py`).
2. Add one new row for `check_workitem_traceability.py`, describing: the four
   report categories it checks (missing-source-file, no-plan-yet, no-procedure-
   yet, stale-target heuristic), that it is read-only, and its `--format json|csv`
   output modes.

### Method
Direct Markdown table-row edit; verified by
`tools/check_tool_descriptions_sync.py`, which matches backtick-quoted `*.py`
filenames anywhere in the file against the live contents of `tools/*.py`
(confirmed via reading that script: it extracts `` `([a-zA-Z0-9_]+\.py)` ``
occurrences via regex and diffs them against `TOOLS_DIR.glob("*.py")`, independent
of table/section placement).

### Details
- The added row must contain `` `check_workitem_traceability.py` `` in backticks
  so the sync checker's regex match succeeds.
- State explicitly in the row that the tool is read-only (never writes/renames/
  moves/deletes files under `issues/`/`plans/`/`implementations/`) to avoid a
  future reader assuming it auto-fixes findings.

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
| `tools/TOOL_DESCRIPTIONS.md` | Consistency | `uv run python tools/check_tool_descriptions_sync.py` | Pass, no drift (requires `tools/check_workitem_traceability.py` to already exist per seq 01 of this Plan) |

## Completion criteria
- `tools/TOOL_DESCRIPTIONS.md` contains a row documenting
  `check_workitem_traceability.py` (AC-006).
- `uv run python tools/check_tool_descriptions_sync.py` passes once
  `tools/check_workitem_traceability.py` exists (REQ-007).

## Out of scope
- Any other edit to `tools/TOOL_DESCRIPTIONS.md` beyond the one new row.
- Documenting the sibling tools tracked as separate issues.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 20260901-120000 | 20260901-120010 | Added one row for `check_workitem_traceability.py` to the checker table, after `check_needs_confirmation_inventory.py` and before `check_compat_shims.py` |
| 2 | Add or update tests per Validation plan | Completed | 20260901-120000 | 20260901-120010 | N/A: documentation-only row addition; verified by the sync checker, not a pytest test |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20260901-120010 | 20260901-120030 | `uv run python tools/check_tool_descriptions_sync.py` -> "No issues found." Also ran `uv run pytest tests/tools/ -v --continue-on-collection-errors`: 61 passed, 1 pre-existing collection error (`test_check_agent_docs_consistency.py`, unrelated) — no new failures. This file is outside `scripts/`, so ruff/mypy/lint-imports do not apply |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Completed | 20260901-120030 | 20260901-120035 | N/A: no `docs/00_index.md` "Document References by Task" row targets `tools/TOOL_DESCRIPTIONS.md` itself (only `tools/01_overview.md` is mapped) — no edit made, per Step 5/6 of `skills/code-implementation/workflow.md` |

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
- **Source issue**: `issues/20260831-194739_tool003_check_workitem_traceability.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20260901-110301_plan.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260901-114312
- **Related target files**: `tools/TOOL_DESCRIPTIONS.md`
