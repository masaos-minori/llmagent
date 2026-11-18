## Goal
Wire the new Status value rule into `tools/check_workitem_structure.py`: run it in `--file` mode and the directory scan as category `status-value`, and extend `--archived-status` to report archived procedures and plans outside a new status-value baseline.

## Scope
**Release unit**: N/A: not part of a release unit

## Assumptions
- The rule module exists after `implementations/20261118-050931_02_tools__workitem_status_check.py.md` lands, and the vocabulary constants exist after the status-table procedure lands.
- The checker is 21266 B of the 24576 B gate; this document adds calls only (the rule itself lives in the new module), so the gate still passes.
- Multi-path `--file` already exists in the current tree; no CLI shape change is needed.

## Design decisions
- Active scope: the rule runs for the plan and implementation kinds only (issues have no Execution Status table by contract). It is added to the same per-file collection the section and release-unit checks already use, so a finding exits 1 with the other categories.
- Archived scope: `--archived-status` keeps its unfinished-row check over `implementations/done/` and its existing baseline file, and additionally runs the value rule over both `implementations/done/` and `plans/done/`, skipping the paths listed in the new baseline `tools/check_status_value_baseline.txt`.
- The new baseline is a second constant beside the existing archived-status baseline constant; the existing `--baseline` flag keeps overriding only the unfinished-row baseline.

## Alternatives considered
- Running the value rule through the unfinished-row scan in one pass: rejected; the two checks have different scopes (unfinished rows: procedures only, existing baseline; values: procedures and plans, new baseline), and merging them would change what the archived-status baseline grandfathers.
- Extending `--archived-status` with a second flag for values: rejected; REQ-004 says `--archived-status` reports both, and the hook must catch both in one run.

## Implementation
### Target file
`tools/check_workitem_structure.py`

### Procedure
1. Import find_status_value_findings from the new module.
2. In the single-file collection used by `--file`, and in the per-file collection used by the directory scan, call the rule for plan and implementation documents and extend the findings list with its findings.
3. Add a module-level constant for the status-value baseline path (default `tools/check_status_value_baseline.txt`) and reuse the existing baseline-file loader for it.
4. In the archived-status mode, after the unfinished-row findings, walk `implementations/done/` and `plans/done/`, run the rule on each file, skip baselined paths, and append the findings.
5. Keep the exit behavior: any finding means exit 1.

### Method
Calls only: the rule, the baseline loader, and the existing report rendering stay unchanged. No function of grade C or worse (REQ-007).

### Details
- The archived-status report currently names only unfinished rows; with values included, its detail strings keep the `category` key so CSV/JSON consumers sort as before.
- A missing status-value baseline file means an empty baseline set (same loader behavior as the existing one), so a fresh checkout without the file reports every archived holder — the file lands in the Plan's Phase 4 (sibling procedure) together with this wiring.

## Compatibility considerations
- The `archived-procedure-status` hook runs this mode; widening its trigger to `plans/done/` is the sibling `.pre-commit-config.yaml` procedure.
- The routing rows and tool description are updated in the Plan's Phase 5 (siblings), per UNK-03 re-reading the shared rows before editing.

## Security considerations
Read-only; no new I/O beyond reading one baseline text file that already follows the existing loader.

## Rollback considerations
Revert this file; the new module and baseline file become unreferenced and are removed by their own procedures' reverts.

## Validation plan
- `uv run pytest tests/tools/test_check_workitem_structure.py -v` (owned by the sibling test procedure);
- `uv run python tools/check_workitem_structure.py` and `uv run python tools/check_workitem_structure.py --archived-status` — exit 0 on the live sets after the baseline lands (AC-4);
- lint, mypy, bandit, radon, and both `tools/check_module_size.py` invocations per the Plan's Validation plan row for the tools.

## Completion criteria
- An active plan or procedure with a bad Status value makes `--file` and the directory scan exit 1 naming file, step, and value; an accepted value and N/A pass (AC-3, tests).
- `--archived-status` reports an archived holder outside the baseline and not one inside it; the live sets report nothing (AC-4).
- Size gates pass and no new grade C function exists (AC-7).

## Out of Scope
- Generating the baseline file content (sibling procedure).
- The hook trigger widening (sibling procedure).

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
- **Requirement ID**: REQ-003, REQ-004, REQ-007
- **Source issue**: issues/20261117-132201_wftoolfu001_workitem-status-vocabulary.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261117-133851_wftoolfu001_workitem-status-vocabulary.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261118-050931
- **Related target files**: `tools/check_workitem_structure.py`
