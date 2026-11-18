# Procedure: tools/TOOL_DESCRIPTIONS.md - complete_doc_procedure.py rows

## Goal

State in the tool documentation what the tool will do after the archival change: the sanctioned archival through `move_to_done`, the unfinished-row refusal, the location requirement, and the exit codes.

## Scope
**Release unit**: N/A: not part of a release unit

- Update the two rows that describe `complete_doc_procedure.py`: the summary-table row (re-verified 20261118 at line 109) and the detailed row in the tool reference table (line 257). (REQ-007)
- No other row of the file changes; the sibling Plans of this batch edit other rows of the same file and are sequenced before or after this Plan's row edit by plan order (plan UNK-03).

## Assumptions

- The exit-code contract keeps its shape (0 success, 1 refusals, 2 usage errors); the unfinished-row refusal joins the exit-1 family and the location refusal joins the exit-2 family, so the row only needs the new refusal names, not new codes.
- `tools/check_tool_descriptions_sync.py` compares the rows with the tools' argparse/usage surfaces; the CLI surface of `complete_doc_procedure.py` is unchanged, so only the prose of the two rows is at risk, not the option list.

## Design decisions

- Edit prose in place, keeping the row layout (three-column summary row, four-column detailed row) and the existing sentence order: what the tool does, then the refusal rules, then the dry-run behavior, then exit codes.
- Apply this edit after the tool change of `implementations/20261118-070621_01_tools_complete_doc_procedure.py.md` is implemented (plan Phase 4 after Phases 1-3), so the description states the shipped behavior, and re-read both rows first because sibling Plans of this batch also edit this file.

## Alternatives considered

- Rewrite the detailed row from scratch. Rejected: the row is one cell of a table shared by four open Plans of this batch; a minimal targeted edit minimizes merge conflict surface against the sibling Plans.
- Defer the row update to a later docs pass. Rejected: `check_tool_descriptions_sync.py` and the stale-doc convention make an out-of-date tool row a finding; REQ-007 scopes it to this Plan.

## Implementation

### Target file

`tools/TOOL_DESCRIPTIONS.md` (exists)

### Procedure

1. In the summary-table row for `complete_doc_procedure.py`, extend the one-line description to name the unfinished-row refusal (for example: docs-wave bookkeeping in one call; refuses `Pending`/`In Progress`/`Blocked` rows when archiving).
2. In the detailed row, replace the archival sentence: the move goes through the sanctioned `move_to_done` of `manage_workitem_stage.py` as a staged `git mv` carrying the rewritten content, not a copy-and-delete; state that archival requires the document to be directly under `implementations/` (otherwise usage error, exit 2); state the unfinished-row refusal (exit 1, rows listed) and that `--no-archive` updates rows without it; state that the memo line is removed after a successful move. Keep the destination-exists refusal sentence, the dry-run sentence, and the exit-code sentence (0, 1, 2) as they remain accurate.
3. Run the sync checker and the structure check on the file.

### Method

Targeted cell edits with the edit tool; read the current rows first (UNK-03: sibling Plans may have changed row order or neighboring rows by then).

### Details

- Keep the row's existing usage-string sentence (the CLI flags are unchanged) so the sync checker keeps matching the tool's usage text.

## Compatibility considerations

- Documentation-only change; readers of the file (operators and the checker) see new prose only.
- The two rows must describe the post-change tool; landing this edit before the tool change would make the documentation state behavior the tool does not have.

## Security considerations

- None beyond keeping the file's Markdown table structure intact for the checkers.

## Rollback considerations

- Reverting this file restores the previous two rows; no runtime state is involved.

## Validation plan

- `uv run python tools/check_tool_descriptions_sync.py` reports no finding for the two rows.
- `uv run python tools/check_workitem_structure.py --file tools/TOOL_DESCRIPTIONS.md` stays clean (the checker's applicability to this file per `routing.md`).

## Completion criteria

- AC-7: the two rows state the sanctioned archival, the unfinished-row refusal, the location requirement, and the exit codes, and `check_tool_descriptions_sync.py` reports no finding.

## Out of Scope

- Rows of other tools, including the `manage_workitem_stage.py` row and rows owned by the sibling Plans of this batch.
- The tool's docstring (owned by the tool procedure document).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | |
| 2 | Add or update tests per Validation plan | Pending | — | — | |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Pending | — | — | |

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
- **Source issue**: issues/20261117-132202_wftoolfu002_doc-procedure-archival.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261117-134130_wftoolfu002_doc-procedure-archival.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261118-070621
- **Related target files**: `tools/TOOL_DESCRIPTIONS.md`, `tools/complete_doc_procedure.py`
