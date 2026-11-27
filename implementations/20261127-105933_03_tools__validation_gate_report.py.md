## Goal
- Add the failures-only branch and the final `Result:` line to `render_summary` in `tools/_validation_gate_report.py`, with the default output byte-identical (`REQ-002`, `REQ-003`, `REQ-004`).

## Scope
**Release unit**: N/A: not part of a release unit

- Runs before the runner procedure (seq 04), which passes the new keyword to this function.

## Assumptions
- Verified in Step 3a: `render_summary(results, changed, mode, base, verbose=False)` (lines 46-75) prints the header via `_print_header` (with the full changed-file list), the rows via `_print_rows`, and one count line for `runtime-argument` rows; `HIDE_REASON = "runtime-argument"`; existing tests call it positionally with `verbose` as the fifth argument (`tests/tools/test_run_validation_gates.py:1075` onward).
- The runner's exit code is 1 only when some result has status `Fail`; the `Result:` line uses the same condition.
- The module is 2675 B; growth is not constrained by the size gate.

## Design decisions
- New keyword-only-by-position parameter `failures_only: bool = False` appended after `verbose`, so every existing call is unchanged.
- `_render_failures_only` (new) prints: the header line with the changed-file count (no file list, no blank line before rows is required but keep one blank line for readability), then the rows whose status is not `Pass` and whose reason is not `runtime-argument` unless `verbose`, then the hidden count line (same text as the default) when such rows are hidden, then `Result: Pass` or `Result: Fail ({n} failing gate(s))` where `n` counts `Fail` results.

## Alternatives considered
- Adding the branch to `tools/run_validation_gates.py`: rejected, it has 630 B below the 24576 B gate.

## Implementation
### Target file
`tools/_validation_gate_report.py`

### Procedure
1. Add `_print_count_header(changed, mode, base)` (new) printing `Validation gates — mode: {mode}, base: {base}, changed files: {len(changed)}` followed by a blank line.
2. Add `_render_failures_only(results, changed, mode, base, verbose)` (new) as in Design decisions; an empty `results` list prints the header, `No gates selected for these changed files.`, and `Result: Pass`.
3. Extend `render_summary` with the trailing parameter `failures_only: bool = False`; when true call `_render_failures_only` (new) and return before the default path.
4. Update the module docstring with one sentence on failures-only.

### Method
- Reuse `_print_rows` for the shown rows so the row format and detail lines are identical to the default.

### Details
- Type annotations on every function; line length 88; English comments.

## Compatibility considerations
- The default path is untouched (a new early return only when the new flag is true), so the default output is byte-identical.

## Security considerations
- N/A: rendering only.

## Rollback considerations
- Revert the commit together with the runner procedure (seq 04).

## Validation plan
- `uv run ruff format tools/_validation_gate_report.py`, `uv run ruff check ... --fix` and confirm, `uv run mypy tools/_validation_gate_report.py`, `uv run bandit tools/_validation_gate_report.py`.
- `uv run pytest tests/tools/test_run_validation_gates.py -q` (existing `render_summary` tests unchanged and passing; the new tests come with seq 05).

## Completion criteria
- `render_summary(..., failures_only=True)` prints the count header, the non-passing rows, and the `Result:` line; the default call is byte-identical; lint, type, and bandit pass.

## Out of Scope
- Gate selection, running, and status classification.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Add the helpers and the `failures_only` (new) parameter per Procedure | Pending | — | — | |
| 2 | Run ruff, mypy, bandit and the existing render_summary tests | Pending | — | — | New tests come with seq 05 |

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
- **Requirement ID**: `REQ-002` (failures-only rendering), `REQ-003` (default unchanged), `REQ-004` (logic in the renderer)
- **Source issue**: issues/20261126-151443_wfeff008_gate-output-filters.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261127-104530_wfeff008_gate-output-filters.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261127-105933
- **Related target files**: `tools/_validation_gate_report.py`
