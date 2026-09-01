## Goal
Add a row for `tools/check_known_deviation_sync.py` to `tools/TOOL_DESCRIPTIONS.md`'s
domain-consistency-checker table, alongside `check_docs_consistency.py` and
`check_needs_confirmation_inventory.py`, so `tools/check_tool_descriptions_sync.py`
continues to pass (REQ-007).

## Scope
- In scope: adding one row to the domain-consistency-checker table (confirmed at
  this file's lines 13-21, one row per checker in this family), after the
  `check_needs_confirmation_inventory.py` row.
- Out of scope: any other edit to `tools/TOOL_DESCRIPTIONS.md`; adding a
  `routing.md` "When to run which tool" row (left for a future increment per the
  source Plan's Scope).

## Assumptions
- The domain-consistency-checker table's existing rows (`check_docs_consistency.py`,
  `check_needs_confirmation_inventory.py`) establish the column pattern this new
  row follows.

## Design decisions
- Place the new row after the `check_needs_confirmation_inventory.py` row,
  matching the source Plan's explicit placement instruction, rather than at an
  arbitrary position in the table.

## Alternatives considered
- Creating a new section for ADR-vs-Known-Issues tooling: rejected — the source
  Plan's Scope explicitly places this entry in the existing
  domain-consistency-checker table.

## Implementation
### Target file
`tools/TOOL_DESCRIPTIONS.md`

### Procedure
1. Locate the domain-consistency-checker table (lines 13-21, containing
   `check_docs_consistency.py` and `check_needs_confirmation_inventory.py`'s
   rows).
2. Add a new row after the `check_needs_confirmation_inventory.py` row,
   describing: what `check_known_deviation_sync.py` cross-references (ADR Known
   Deviations vs. canonical Known Issues Status), that it is read-only/
   reporting-only, and its `--format json` output mode.

### Method
Direct Markdown table-row edit; verified by
`tools/check_tool_descriptions_sync.py`, which matches backtick-quoted `*.py`
filenames anywhere in the file against the live contents of `tools/*.py`
(confirmed via reading that script: regex-extracted
`` `([a-zA-Z0-9_]+\.py)` `` occurrences diffed against `TOOLS_DIR.glob("*.py")`,
independent of table/section placement).

### Details
- The added row must contain `` `check_known_deviation_sync.py` `` in backticks
  so the sync checker's regex match succeeds.
- State explicitly that the tool reports only (never auto-resolves a mismatch)
  to avoid a future reader assuming it fixes drift automatically.

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
| `tools/TOOL_DESCRIPTIONS.md` | Consistency | `uv run python tools/check_tool_descriptions_sync.py` | Passes (AC-6), requires `tools/check_known_deviation_sync.py` to already exist per seq 01 of this Plan |

## Completion criteria
- `tools/TOOL_DESCRIPTIONS.md` contains a row documenting
  `check_known_deviation_sync.py` in the domain-consistency-checker table (AC-6).
- `uv run python tools/check_tool_descriptions_sync.py` passes once
  `tools/check_known_deviation_sync.py` exists (REQ-007).

## Out of scope
- Any other edit to `tools/TOOL_DESCRIPTIONS.md` beyond the one new row.
- Adding a `routing.md` "When to run which tool" row.

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
- **Source issue**: `issues/20260831-194739_tool006_check_known_deviation_sync.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20260901-112435_plan.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260901-115359
- **Related target files**: `tools/TOOL_DESCRIPTIONS.md`
