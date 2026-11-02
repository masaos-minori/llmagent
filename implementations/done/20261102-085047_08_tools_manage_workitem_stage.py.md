## Goal
- Group procedures by release unit in `list` and print the unit in `show`, leaving output for procedures without a unit unchanged (`REQ-005`).

## Scope
- In scope: two small read helpers and changes to `cmd_list` and `cmd_show`. Out of scope: `build_parser`, the close/set-status commands, and the order view another Plan adds to `list`.

## Assumptions
- Step 3a: `cmd_list` collects `(path, kind)` per status string via `_get_status_from_file` and prints `  [kind] path` lines; `cmd_show` prints the `### Execution Status` table only; `build_parser` defines `list` with `--kind`/`--status` and `show` with `kind` and `path` (all checked in the current file).
- Overlap (Step 2): `tools/manage_workitem_stage.py` is also targeted by the Plan filed from `flowimp003`, which adds `list --plan --order`. Judged a sequencing dependency, not a conflict (plan Assumption A7): both edit `cmd_list`; whichever lands second rebases onto the other's `cmd_list`.
- Group key is the procedure's `Source plan` value plus the unit name (plan Unknown UNK-02), so two Plans using the same unit name stay separate.
- Depends on rows 02 and 04: a member procedure's `## Scope` carries a `**Release unit**` line with the name; `N/A...` means no unit.
- Caveat (Step 3a): `tools/TOOL_DESCRIPTIONS.md` describes `list` and `show` at subcommand level; that file is not a target of this Plan, so any wording update there is left to a separate change.

## Design decisions
- Parse with two module-level helpers (new): `_release_unit_name` (new) reading the `**Release unit**` line, and `_source_plan_path` (new) reading the `**Source plan**` Traceability line; both return `None` when absent or `N/A`.
- `list`: in each status block, print the ungrouped items exactly as today, then one block per `(source plan, unit)` as `  Unit: {name} ({source plan})` followed by its members indented one level deeper. Plans (kind `plan`) are never grouped.

## Alternatives considered
- Printing a unit suffix on each line was rejected: it does not group members, which REQ-005 requires.

## Implementation
### Target file
`tools/manage_workitem_stage.py`

### Procedure
- Add the two helpers near `_get_status_from_file`.
- In `cmd_list`, carry the unit and source plan per item in `results`, and render grouped output as above.
- In `cmd_show`, after the table, print `Release unit: {name}` only when the file carries a unit.

### Method
- Reuse the file content already read (`_get_status_from_file` reads it; read the file once per item in `cmd_list` and pass the content to the helpers rather than reading a second time where practical).
- Match lines with anchored regexes tolerant of a leading `- ` list marker and surrounding whitespace.
- Keep ordering deterministic: sort groups by `(source plan, unit)`.

### Details
- An item whose status filter does not match is excluded before grouping, as today.
- `show` prints the unit for either kind, since only procedures carry the line.

## Compatibility considerations
- Items without a unit produce byte-identical output to the current `list` and `show`; the existing `TestList` and `show` tests in `tests/tools/test_manage_workitem_stage_new.py` are the regression check.

## Security considerations
N/A: read-only parsing of local workitem files.

## Rollback considerations
N/A: revert the commit.

## Validation plan
- `uv run pytest tests/tools/test_manage_workitem_stage.py tests/tools/test_manage_workitem_stage_new.py -v`.
- Per `routing.md` "Adding a new tool": `ruff format`, `ruff check --fix` then plain, `mypy tools/manage_workitem_stage.py`, `bandit tools/manage_workitem_stage.py`, and a smoke run of `uv run python tools/manage_workitem_stage.py list --kind implementation-procedure` on live `implementations/`.

## Completion criteria
- `list` groups unit members and `show` prints the unit; procedures without a unit print as before (AC-4); lint, type, and security checks are clean.

## Out of Scope
- The order view and `--plan` option (another Plan), and `tools/TOOL_DESCRIPTIONS.md`.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the unit helpers and the `list` and `show` changes | Completed | 20261102-125424 | 20261102-125424 | Stale clean; 3a: cmd_list now has order view from flowimp003 (cmd_list_order) - rebased onto it, ordering path untouched; reused existing _extract_traceability_field/_normalize_plan_path. Changed: tools/manage_workitem_stage.py (_release_unit_name, _source_plan_path, cmd_list grouping, cmd_show unit line) |
| 2 | Add tests (row 09) and run both test modules | Completed | 20261102-125428 | 20261102-125428 | Tests live in row 09's document existing test_manage_workitem_stage + _new: 95 passed (regression); new grouped tests are procedure 09's; full suite deferred to plan end |
| 3 | Run the tool lint sequence and the smoke run (`routing.md` Adding a new tool) | Completed | 20261102-125428 | 20261102-125428 | `ruff`, `mypy`, `bandit`, `check_tool_descriptions_sync.py` ruff format/check clean, mypy clean, bandit 0 medium/high, check_tool_descriptions_sync clean; smoke list/show on live implementations ok (no unit, output unchanged). TOOL_DESCRIPTIONS wording not updated (out of scope) |

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
- **Requirement ID**: `REQ-005`
- **Source issue**: issues/20261030-191057_flowimp002_plan-release-units.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261102-080336_flowimp002_plan-release-units.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261102-085047
- **Related target files**: tools/manage_workitem_stage.py