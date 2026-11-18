## Goal
Create `tools/_workitem_status_check.py`, the single module that decides, for one plan or procedure document, which Execution Status rows hold a Status value outside the shared vocabulary.

## Scope
**Release unit**: N/A: not part of a release unit

## Assumptions
- UNK-01 of the Plan is confirmed: N/A is a vocabulary value, so the rule accepts exactly N/A and rejects `N/A:` prose variants.
- The vocabulary constants exist after `implementations/20261118-050931_01_tools__workitem_status_table.py.md` lands; this module imports them and defines no status string of its own.
- The checker module is 21266 B of the 24576 B gate, so the Plan routes new logic to this new module and the checker gains only a call.

## Design decisions
- Public contract: one function, find_status_value_findings(content, rel_path), returning a list of finding dicts shaped like the checker's existing findings (`category`, `file`, `detail`), with category `status-value` and detail naming the step and the offending value; empty list when the document has no Execution Status table (parser returns None: absence of a table is reported by the section gate, not here).
- Matching is exact against the vocabulary after trimming cell whitespace; no case folding, so `completed` is reported (Decision 4).
- Imports are limited to the standard library and `tools/_workitem_status_table.py` (parse_execution_status_rows and the vocabulary constants); no checker import, so the module stays testable without the checker.

## Alternatives considered
- Putting the rule inside `tools/check_workitem_structure.py`: rejected by the Plan row — the checker module is near the size gate and the structure-gate Plan already added code to it.
- Reporting per-row instead of per-file: the checker's finding format is per-file with the steps named in detail; the rule follows it so `--file`, the directory scan, and `--archived-status` render identically.

## Implementation
### Target file
`tools/_workitem_status_check.py` (new)

### Procedure
1. Module docstring: state that it is a shared base read by `tools/check_workitem_structure.py`, mirroring the `_workitem_*` helper modules.
2. Implement find_status_value_findings: parse rows with parse_execution_status_rows; when None, return an empty list; trim each row's Status; collect rows whose value is not in the vocabulary; if any, return one finding naming the file and the Steps with their values.
3. No CLI, no file writes.

### Method
A single function of roughly fifteen lines; keep its complexity grade B or better (REQ-007 forbids grade C or worse).

### Details
- A row whose Status cell is empty after trimming is outside the vocabulary and is reported.
- The detail string names each offending step and its exact value, matching AC-3 ("name the file, step, and value").
- Baseline behavior does not live here: the checker owns baseline files; this module judges one document.

## Compatibility considerations
- New file; no existing importer. `tools/TOOL_DESCRIPTIONS.md` gains its row in the Plan's Phase 5 (sibling procedure).

## Security considerations
Read-only over a string the caller already read; no I/O of its own.

## Rollback considerations
Delete the file and remove the checker calls (sibling procedure); nothing else references it.

## Validation plan
- Tests live in `tests/tools/test_check_workitem_structure.py` (sibling procedure owns them).
- `uv run ruff format tools tests/tools`, `uv run ruff check tools tests/tools`, `uv run mypy --no-namespace-packages scripts/ tests/eventbus tools`, `uv run bandit tools/_workitem_status_check.py tools/check_workitem_structure.py`, `uv run radon cc tools/_workitem_status_check.py tools/check_workitem_structure.py -s -n C`, both `tools/check_module_size.py` invocations.

## Completion criteria
- The module reports an out-of-vocabulary row with file, step, and value; accepts the six vocabulary values; rejects `N/A:` prose (AC-3 tests pass).
- bandit and mypy clean; no function of grade C or worse; under the size gate.

## Out of Scope
- Baseline loading and archived scanning (checker procedure).
- Rewriting values in existing documents.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | — | 20261118-121802 | find_status_value_findings implemented |
| 2 | Add or update tests per Validation plan | N/A | — | — | tests owned by procedure 11 |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | — | 20261118-121802 | ruff/mypy/bandit/radon/size OK |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | N/A | — | — | TOOL_DESCRIPTIONS row owned by sibling 10 |

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
- **Requirement ID**: REQ-003, REQ-004, REQ-007
- **Source issue**: issues/20261117-132201_wftoolfu001_workitem-status-vocabulary.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261117-133851_wftoolfu001_workitem-status-vocabulary.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261118-050931
- **Related target files**: `tools/_workitem_status_check.py`