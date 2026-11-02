## Goal
- Add the `ROUTING_GATES` entry for the new routing row so `drift_report()` passes (`REQ-007`).

## Scope
- In scope: one `Gate` entry in `ROUTING_GATES`.
- Out of scope: `drift_report()` logic, the hook-parity change of flowimp005, other Plans' entries.

## Assumptions
- Plan A6 and A9. Step 3a verified (2026-11-02): `ROUTING_GATES` is a tuple of `Gate` entries at line 656; the `check_workitem_structure` entry (command with `--file`, `<path>`) is the placeholder pattern; `checker_id` for `... plan_dependency_order.py --plan <path>` is `plan_dependency_order:<path>` by `_checker_id_from_command`, identical to the id derived from the routing cell in row 10. The Gate name is created by this document (marked new below); the Plan-level symbols named by rows 01 to 03 are created by earlier rows.
- Overlap (Step 2): `flowimp001`, `flowimp010`, `flowimp011` add one entry each, and `implementations/20261102-084648_01_tools_run_validation_gates.py.md` (flowimp005, archived Plan with procedures) changes `drift_report()` to a hook comparison and appends seven entries to `ROUTING_GATES`. Judged compatible: row-additive entries; the hook-parity check applies to tool-backed hooks and this tool has no hook; whichever lands second rebases onto the other's `ROUTING_GATES` additions.
- Sibling dependency: row 10 adds the routing row; the two must land together.

## Design decisions
- Entry name `plan_dependency_order` (new), command `("uv","run","python","tools/plan_dependency_order.py","--plan","<path>")`, `source=SOURCE_ROUTING`, `mode=MODE_FAST`, patterns `("plans/*.md",)`; it has a placeholder, so it is `Not available` at run time like the existing placeholder gates.

## Alternatives considered
- A gate without a placeholder: rejected, it would diverge from the routing cell and fail `drift`.

## Implementation
### Target file
`tools/run_validation_gates.py`

### Procedure
- Append the `Gate` entry to `ROUTING_GATES` (after the `manage_workitem_stage_list` entry); keep the existing tuple formatting.

### Method
- Copy the shape of the `check_workitem_structure` entry and change the name, argv, and patterns.

### Details
- Argument tokens must be exactly those in row 10's Run cell.

## Compatibility considerations
- Only gains an entry; existing ids and `drift_report()` behavior are unchanged.

## Security considerations
- N/A: fixed argv tuple, no shell.

## Rollback considerations
- N/A: revert the commit.

## Validation plan
- `uv run python tools/run_validation_gates.py drift`; `uv run pytest tests/tools/test_run_validation_gates.py -v`.
- `uv run ruff format tools/run_validation_gates.py`; `uv run ruff check tools/run_validation_gates.py`; `uv run mypy tools/run_validation_gates.py`; `uv run bandit tools/run_validation_gates.py` (pre-existing findings recorded, only new ones count).

## Completion criteria
- `drift` reports no unmapped checker after rows 10 and 11; the existing gate tests and lint, type, and security checks pass.

## Out of Scope
- The routing row (row 10) and the `TOOL_DESCRIPTIONS.md` rows (row 09).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 20261102-102309 | 20261102-102309 | Stale check clean. No correction. Files: tools/run_validation_gates.py (plan_dependency_order Gate entry, patterns plans/** and implementations/**, placeholder <path> reports Not available at run time like check_workitem_structure) |
| 2 | Add or update tests per Validation plan | Completed | 20261102-102309 | 20261102-102309 | Run `tests/tools/test_run_validation_gates.py`; add a case only if the existing drift tests do not already cover a new placeholder entry drift OK; tests/tools/test_run_validation_gates.py 56 passed; ruff, mypy clean; bandit 5 pre-existing findings identical to HEAD. Full suite deferred to plan end |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20261102-102315 | 20261102-102315 | Tool lint sequence of `routing.md` "Adding a new tool" plus `drift` ruff format/check, mypy, bandit (no new findings) as recorded in row 2 |

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
- **Requirement ID**: REQ-007 (gate mapping entry for the new routing row)
- **Source issue**: issues/20261030-191144_flowimp003_plan-dependency-gate.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261102-080134_flowimp003_plan-dependency-gate.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261102-085056
- **Related target files**: tools/run_validation_gates.py