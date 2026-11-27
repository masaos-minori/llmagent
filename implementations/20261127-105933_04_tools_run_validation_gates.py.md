## Goal
- Add the `--failures-only` option to `tools/run_validation_gates.py` and pass it to the renderer, with the file staying at or below 24576 B and the default behavior unchanged (`REQ-002`, `REQ-003`, `REQ-004`).

## Scope
**Release unit**: N/A: not part of a release unit

- Runs after the renderer procedure (seq 03): the renderer accepts the new keyword first.

## Assumptions
- Verified in Step 3a: the file is 23946 B (limit 24576 B, no baseline entry); `_run_gates(base, mode, jobs=None, verbose=False)` (lines 555-562) calls `render_summary(results, changed, mode, base, verbose)` and returns 1 when any result is `Fail`; `build_parser` (lines 592-632) defines `--verbose`; `main` (lines 634-641) calls `_run_gates`.
- The growth of this file must be at most 500 B; measure `wc -c` before and after.

## Design decisions
- The exit code expression is unchanged, so failures-only has the same exit code as the full output by construction.
- Pass the flag as a keyword: `render_summary(results, changed, mode, base, verbose, failures_only)`.

## Alternatives considered
- Printing in this file: rejected for size; the renderer owns output.

## Implementation
### Target file
`tools/run_validation_gates.py`

### Procedure
1. In `build_parser` add after `--verbose`: `--failures-only` with `action="store_true"` and help "Print only the changed-file count, the non-passing rows, and a final Result line (the exit code is unchanged)".
2. Change `_run_gates` to `_run_gates(base, mode, jobs=None, verbose=False, failures_only=False)` and pass `failures_only` as the last argument of `render_summary`.
3. In `main` pass `args.failures_only` to `_run_gates`.

### Method
- Three small edits; do not touch gate selection, running, or the `drift` subcommand.

### Details
- Keep the existing annotations style; line length 88.

## Compatibility considerations
- Defaults are unchanged: `failures_only` is false unless the flag is given; existing callers of `_run_gates` and the CLI are unaffected.

## Security considerations
- N/A: argument handling only.

## Rollback considerations
- Revert the commit together with seq 03 and seq 05.

## Validation plan
- `uv run ruff format tools/run_validation_gates.py`, `uv run ruff check ... --fix` and confirm, `uv run mypy tools/run_validation_gates.py`, `uv run bandit tools/run_validation_gates.py`.
- `uv run python -m tools.check_module_size --scripts-dir tools --baseline tools/check_module_size_tools_baseline.txt` exits 0 and `wc -c tools/run_validation_gates.py` is at most 24446.
- `uv run pytest tests/tools/test_run_validation_gates.py -q`.
- Default-output parity: `uv run python tools/run_validation_gates.py` output before and after on the same working tree is identical.

## Completion criteria
- `--failures-only` is accepted and reaches the renderer; the exit code equals the full output's; the file is at most 24576 B (growth at most 500 B); lint, type, bandit, size gate, and existing tests pass.

## Out of Scope
- The renderer (seq 03), gate definitions, selection, and running.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Add the option, the pass-through, and the `main` call per Procedure | Pending | — | — | Needs seq 03 first |
| 2 | Run ruff, mypy, bandit, the tools size gate (growth at most 500 B) and the existing tests | Pending | — | — | |

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
- **Requirement ID**: `REQ-002` (the option), `REQ-003` (same exit code, defaults unchanged), `REQ-004` (size cap)
- **Source issue**: issues/20261126-151443_wfeff008_gate-output-filters.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261127-104530_wfeff008_gate-output-filters.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261127-105933
- **Related target files**: `tools/run_validation_gates.py`
