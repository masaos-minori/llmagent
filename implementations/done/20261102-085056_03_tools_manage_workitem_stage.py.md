## Goal
- Add `list --plan {plan_path} --order`: procedures whose `Source plan` is that Plan, in Plan phase order, grouped under the Plan (`REQ-004`).

## Scope
- In scope: new `--plan` and `--order` options on the `list` subparser, a new separate function for the order view, and the `cmd_list` dispatch to it.
- Out of scope: any change to `update_execution_status`, `cmd_close_batch`, `show`, or existing `list` output.

## Assumptions
- Plan A4 and A9. Step 3a verified (2026-11-02): `list_parser` has `--kind` and `--status` only; `cmd_list(args)` groups by status; `_get_workitem_files(kind)` returns `implementations/*.md` (not `done/`) sorted; `parse_execution_status_rows(content)` returns row dicts; `_extract_source_issue(content)` shows the Traceability regex style (`\*\*Source issue\*\*:\s*`?([^`\s]+)`?`).
- Step 3a verified: no function in the module reads a procedure's `Source plan` or `Related target files`; the order view adds `_extract_traceability_field` (new) for both.
- Overlap (Step 2): `plans/20261102-080336_flowimp002_plan-release-units.md` also edits `list` and `show` (unit grouping). Judged a sequencing dependency, not a conflict: this change adds options and a separate function, flowimp002 changes how results are grouped; whichever lands second rebases (Plan Scope Dependencies). `plans/20261102-080631_flowimp008_workitem-bulk-close.md` and `plans/20261102-080828_flowimp009_test-row-grouping.md` only read this file.
- The order view reads a Plan at `plans/` or `plans/done/` and procedures in `implementations/` only (an archived procedure is out of the in-flight view).

## Design decisions
- New, separate function `cmd_list_order(args)` (new) with helpers; `cmd_list` calls it only when `--order` is set, so existing output is byte-identical.
- Phase of a procedure: the first top-level `Implementation steps` item of the Plan whose text cites the procedure's target file; a procedure that matches no step is listed last with a warning (Plan A4).

## Alternatives considered
- A new `order` subcommand: rejected, the Plan fixes `list --plan --order` and a flag keeps one entry point.
- Sorting by `seq` alone: rejected, `seq` follows the target table order, not the phase order the Plan states.

## Implementation
### Target file
`tools/manage_workitem_stage.py`

### Procedure
- Add `--plan` (path) and `--order` (store_true) to `list_parser`. `--order` without `--plan` exits 2 with `--order requires --plan`; `--plan` without `--order` also requires `--order` (the Plan option has no other meaning).
- In `cmd_list`, at the top: `if args.order: return cmd_list_order(args)` (the function is new).
- Add `_extract_traceability_field(content, label)` (new), `_plan_phase_map(plan_text)` (new, step number and cited paths), and `cmd_list_order(args)` (new).

### Method
- `_plan_phase_map(plan_text) -> list[tuple[int, str]]`: read the `## Implementation steps` section; each line starting `N. ` opens phase N and every backticked path in that item and its sub-bullets is attributed to N; return `(phase, text)` pairs.
- `cmd_list_order` (new): resolve `args.plan` (a missing file prints `ERROR: plan not found` to stderr, returns 1); collect `_get_workitem_files("implementation-procedure")`; keep procedures whose `Source plan` equals the plan path (treat `plans/x.md` and `plans/done/x.md` as equal); for each, take `Related target files`, find its phase, and sort by `(phase, seq)` where `seq` is parsed from the filename (`<timestamp>_<seq>_`); procedures with no matching phase sort after all phases and print `WARNING: no Plan step cites {file}`.
- Output: `Plan: {path}` then `  Phase {N}` then `    {procedure path} [{Status summary}]`, reusing `_get_status_from_file`. A Plan with no matching procedures prints `No procedures found for plan {path}` and returns 0. When a procedure's Notes carry a `Gated:` prefix (row 06), append ` [gated]`.

### Details
- The `Gated:` check reads the procedure's Execution Status rows through `parse_execution_status_rows`; it only displays and never edits.
- Keep helper functions small; `update_execution_status` and `cmd_close_batch` (rated D by `radon cc`) are not touched.

## Compatibility considerations
- Existing `list --kind/--status` and `show` behavior and output are unchanged; the new flags are optional. `tools/TOOL_DESCRIPTIONS.md` is updated in row 09.

## Security considerations
- N/A: read-only; the path argument is only read, and only files under `implementations/` are listed.

## Rollback considerations
- N/A: revert the commit.

## Validation plan
- `uv run pytest tests/tools/test_manage_workitem_stage.py tests/tools/test_manage_workitem_stage_new.py -v` (row 04 adds cases).
- `uv run ruff format tools/manage_workitem_stage.py`; `uv run ruff check tools/manage_workitem_stage.py`; `uv run mypy tools/manage_workitem_stage.py`; `uv run bandit tools/manage_workitem_stage.py` (record pre-existing findings; only new ones count).
- Smoke: `uv run python tools/manage_workitem_stage.py list --plan <a plan with procedures> --order`.

## Completion criteria
- `list --plan {plan} --order` prints the Plan's procedures grouped by phase in Plan phase order, a no-match Plan prints the no-procedures line, and an unmatched procedure is listed last with a warning.
- Existing `list` and `show` output is unchanged; lint, type, and security checks are clean.

## Out of Scope
- Tests (row 04); the docs entry for the new option (row 09); the unit grouping of flowimp002.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 20261102-101746 | 20261102-101938 | Implement the order view Stale check clean. No procedure correction. Files: tools/manage_workitem_stage.py (list --plan --order, cmd_list_order and helpers). Smoke run on the flowimp003 Plan listed phases 2 to 5 in order |
| 2 | Add or update tests per Validation plan | Completed | 20261102-101938 | 20261102-101938 | Tests live in the row 04 document (`tests/tools/test_manage_workitem_stage.py`); run them here Tests in row 04 document: tests/tools/test_manage_workitem_stage.py 95 passed with test_manage_workitem_stage_new.py. Full suite deferred to plan end |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20261102-101938 | 20261102-101938 | Tool lint sequence of `routing.md` "Adding a new tool" plus the order view smoke run ruff format/check, mypy and bandit clean (baseline clean too) |

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
- **Requirement ID**: REQ-004 (order view in `list`)
- **Source issue**: issues/20261030-191144_flowimp003_plan-dependency-gate.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261102-080134_flowimp003_plan-dependency-gate.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261102-085056
- **Related target files**: tools/manage_workitem_stage.py