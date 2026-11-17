## Goal

Make the `check_workitem_structure` gate auto-runnable on changed top-level work item files only (REQ-003) and reconcile the checker id so the gate, the routing Run cell, and the new hook all resolve to `check_workitem_structure:--file` (plan Decision 6).

## Scope
**Release unit**: N/A: not part of a release unit

## Assumptions

- `tools/run_validation_gates.py` already expands the `__CHANGED_FILES__` sentinel against the paths that match the gate patterns (`_expand_changed_files`); it stays unmodified (Reference File).
- 24247 B of the 24576 B module limit — 329 B headroom (re-measured 20261117); the gate-row swap shrinks slightly and the sentinel skip adds a few short lines.
- `_glob_to_regex` compiles `*` as `[^/]*`, so `issues/*.md` style patterns never match a `done/` path (verified 20261117).

## Design decisions

- `_checker_id_from_command` skips the `__CHANGED_FILES__` token before scanning for a positional or value flag; without the skip the gate id becomes `check_workitem_structure:__CHANGED_FILES__` and the drift check fails (3 simulated errors: routing row unmapped, mapping entry not a routing checker, hook unmapped).
- The sentinel is not a placeholder for `requires_context`: `_PLACEHOLDER_TOKEN_RE` only matches `<`, `[`, `]`, `...`, so the flipped command makes the gate auto-selectable (AC-4) with no orchestrator change.

## Alternatives considered

- Keep the gate context-required and rely on the hook only: rejected, REQ-003 names the gate as the commit-skill run.
- Add the hook to `COMMIT_ONLY_HOOKS`: rejected, AC-6 requires no allowlist entry.

## Implementation
### Target file
`tools/_validation_gate_defs.py`

### Procedure

- In the `check_workitem_structure` Gate: replace the `<path>` token with `__CHANGED_FILES__` and replace the patterns with `("issues/*.md", "plans/*.md", "implementations/*.md")`.
- Add a module-level constant `_CHANGED_FILES_SENTINEL` (new) holding `__CHANGED_FILES__`, and in `_checker_id_from_command` drop tokens equal to it before the positional and value-flag scans.

### Method

- The gate-row edit mirrors plan Decision 2: single-segment globs matching the hook `files` regex of the seq 03 document.
- `_checker_id_from_command` keeps its grade-C budget: the skip is one filter step at the top of the function (Baseline correction in the plan).

### Details

- After the edit the gate's `checker_id` property must yield `check_workitem_structure:--file`, and the `check_archived_status` gate row stays untouched (its id `check_workitem_structure:--archived-status` already maps the existing hook).

## Compatibility considerations

- `_checker_id_from_command` is also used for routing Run cells (via `_checker_id_from_cell`), so the routing row must adopt `--file __CHANGED_FILES__` in the same plan phase pair (seq 04 document); landing 02 without 04 leaves drift red.
- Toolchain gates already carrying the sentinel (the ruff rows) derive no `tools/*.py` base token, so their ids are unaffected (verified by the 20261117 drift simulation: 0 errors after the skip).

## Security considerations

N/A: no new I/O; the module only declares commands.

## Rollback considerations

- Revert the commit; the gate returns to `Not available` (context-required), which is the pre-change state.

## Validation plan

- `uv run pytest tests/tools/test_run_validation_gates.py -v` — selection, `requires_context`, expansion, and id tests are added by the seq 08 document.
- `uv run python tools/run_validation_gates.py drift` — 0 errors once the seq 03/04 documents land (the gate alone maps to the updated routing cell).
- `uv run python tools/check_module_size.py --scripts-dir tools --baseline tools/check_module_size_tools_baseline.txt` — module below the limit (AC-9).

## Completion criteria

- AC-4 and AC-5 hold as tests; `checker_id` equals `check_workitem_structure:--file`; the size gate passes; radon reports no grade change for `_checker_id_from_command`.

## Out of Scope

- Any change to `tools/run_validation_gates.py` (Reference File); the hook, routing row, and tests (other documents of this plan).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Edit the gate row and add the sentinel skip in `_checker_id_from_command` | Completed | 20261117-165453 | 20261117-165453 | gate row: --file __CHANGED_FILES__, single-segment patterns; _CHANGED_FILES_SENTINEL skip in _checker_id_from_command; checker_id=check_workitem_structure:--file; requires_context False |
| 2 | Tests are added by the seq 08 document | Completed | 20261117-165453 | 20261117-165453 | landed with seq 03/04/08 as the drift-consistent pair; 86/86 pass in test_run_validation_gates.py; radon _checker_id_from_command grade unchanged C (16->18, comprehension +2) |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20261117-165453 | 20261117-170012 | ruff/mypy/bandit/size gate pass; drift: 45 checkers mapped, 0 errors; full sequence at batch end full batch validation: pytest tests/ 12591 passed 7 skipped; diff-cover no measurable lines (tools/tests/docs only); drift 0 errors; hooks pass |

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
- **Requirement ID**: `REQ-003` (auto-runnable top-level gate), `REQ-007` (module-size and complexity constraints)
- **Source issue**: `issues/20261117-123330_wftool001_gate-workitem-structure.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261117-124139_wftool001_gate-workitem-structure.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261117-151927
- **Related target files**: `tools/_validation_gate_defs.py`