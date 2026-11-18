## Goal
Create `tools/check_status_value_baseline.txt`: the once-generated, never-grown list of archived paths that already hold a Status value outside the vocabulary, so the archived value check reports only new holders.

## Scope
**Release unit**: N/A: not part of a release unit

## Assumptions
- The value rule and its wiring exist (`implementations/20261118-050931_02_tools__workitem_status_check.py.md` and `implementations/20261118-050931_03_tools_check_workitem_structure.py.md` land first, same phase).
- The Plan's 2026-11-18 revalidation measured 637 archived procedures and 10 archived plans holding such rows (647 paths); the number is confirmed again by the generator at execution time and the file holds exactly that set.

## Design decisions
- The generator is a one-shot run of the shared parser over `implementations/done/*.md` and `plans/done/*.md`, writing the sorted repository-relative paths of every file with at least one out-of-vocabulary row; the file is committed once and only shrinks afterwards (a path is removed when its holder is rewritten or superseded), mirroring the rules of `tools/check_archived_status_baseline.txt`.
- A header comment (four `#` lines in the existing baseline's style) states: the date of generation (the execution date), that the paths are not reported, that paths must not be added by hand, and that a holder to be fixed is rewritten or superseded, never appended.

## Alternatives considered
- Hand-writing the file from the Plan's counts: rejected; REQ-004 says the baseline holds exactly today's holders, and only the shared parser produces that set.
- Seeding from the existing archived-status baseline (580 paths): rejected; the two rules have different holders (580 unfinished-row holders versus 647 value holders); mixing them would grandfather the wrong files.

## Implementation
### Target file
`tools/check_status_value_baseline.txt` (new)

### Procedure
1. Run a one-shot generator (a `uv run python -c` block, or a throwaway under `./tools/` per the repo rule if the run needs iteration): parse every archived procedure and plan with parse_execution_status_rows, collect files with a trimmed Status outside the vocabulary constants, print the sorted paths.
2. Write the file: header comment first, then the sorted paths, one per line.
3. Run `uv run python tools/check_workitem_structure.py --archived-status` and confirm the live archived set reports nothing (AC-4).

### Method
Generation from the shared parser only; no value appears in the file, only paths.

### Details
- The loader of the sibling checker procedure skips blank lines and `#` lines, the same contract as the existing baseline loader.
- Expected magnitude: about 647 path lines; the count is printed by the generator and recorded in this document's Execution Status Notes when executed.

## Compatibility considerations
- Review noise is the Plan's recorded risk; the mitigation stands: generated once, never grown by hand, header says so.

## Security considerations
Not applicable: a data file read by one tool.

## Rollback considerations
Delete the file; the checker then reports every current holder, which is the pre-Plan state.

## Validation plan
- Baseline loader tests and the archived in/out-of-baseline tests owned by `tests/tools/test_check_workitem_structure.py` (sibling procedure).
- Live smoke run `uv run python tools/check_workitem_structure.py --archived-status` exits 0 with the file in place (AC-4).

## Completion criteria
- The file holds exactly the paths that hold an out-of-vocabulary value today (generator output equals file content); the live archived set reports nothing.

## Out of Scope
- Rewriting or superseding any archived holder (explicitly out of the Plan's scope).

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
- **Requirement ID**: REQ-004
- **Source issue**: issues/20261117-132201_wftoolfu001_workitem-status-vocabulary.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261117-133851_wftoolfu001_workitem-status-vocabulary.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261118-050931
- **Related target files**: `tools/check_status_value_baseline.txt`
