## Goal
- Add the read-only `--headroom PATH [PATH ...]` option to `tools/check_skill_size.py`, leaving the gate path and its default output untouched (`REQ-001` report, `REQ-002` defaults unchanged, `REQ-004` size); its tests are the companion `tests/tools/test_check_skill_size.py`.

## Scope
**Release unit**: N/A: not part of a release unit

- In scope: one report function, one parser option, and an early-return branch in `main`. Out of scope: `evaluate`, `_report`, `collect_covered`, `--update-baseline`, `--top` (unchanged), and any ceiling.

## Assumptions
- Verified in Step 3a: `tools/check_skill_size.py` is 7903 B; `_build_parser` defines `--root`, `--limit`, `--baseline`, `--top`, and a mutually exclusive group of `--no-baseline` and `--update-baseline`; `main` collects `sizes = collect_covered(root)`, prints `--top`, handles `--update-baseline`, loads the baseline, evaluates, and reports; `load_baseline` and `write_baseline` come from `tools/check_module_size.py`; the tools size gate is 24576 B (no baseline entry for this file).
- The existing tests use `_write`, `_tree`, and `_run(root, baseline, *extra)` (adds `--limit 100`), so the new tests reuse them.
- Report-only: the option prints and returns before the gate runs; exit 0, or 2 for a path that does not exist.

## Design decisions
- `headroom_line(relpath, size, baseline, limit)` (new) returns the line text; `report_headroom(root, paths, sizes, baseline, limit)` (new) validates every path first (all existing, else print `ERROR: path not found: {value}` to standard error and return 2 with no other output), then prints one line per path in the order given and returns 0.
- A path is resolved against `--root` when relative; `relpath` is its POSIX form relative to the resolved root; a path outside the root or not in `collect_covered` prints `{relpath-or-value}: not covered by the size gate`.
- Ceiling: the baseline entry when present (source `baseline`), otherwise the limit (source `limit`); headroom is ceiling minus size and may be negative.
- `--headroom` together with `--update-baseline` is a usage error (`parser.error`, exit 2); with `--top` the top list is not printed.

## Alternatives considered
- Run the gate after the report: rejected (Plan assumption), it would mix the report with the gate's exit code.

## Implementation
### Target file
`tools/check_skill_size.py`

### Procedure
1. Add `headroom_line` (new) and `report_headroom` (new) above `main`, annotated, with English docstrings.
2. In `_build_parser` add `--headroom` with `nargs="+"`, `default=None`, `metavar="PATH"`, help "Print size, ceiling, and headroom of these files (report only; the gate is not run)".
3. In `main`, after the root check and `sizes = collect_covered(root)`, add: if `args.headroom` and `args.update_baseline` call `parser.error("--headroom cannot be combined with --update-baseline")`; if `args.headroom`, load the baseline (`{}` with `--no-baseline`), and `return report_headroom(root, args.headroom, sizes, baseline, args.limit)` before the `--top` print.
4. Add a Usage line to the module docstring: `python tools/check_skill_size.py --headroom PATH [PATH ...]`.

### Method
- Keep `main`'s existing order for every path without `--headroom`, so the default output and exit codes are byte-identical.

### Details
- Type annotations on every function; line length 88; no new imports beyond `Path` already imported.

### Companion test files
- `tests/tools/test_check_skill_size.py`
  - Procedure: append tests using `_write`, `_tree`, `_run`: a baselined file under its ceiling prints `ceiling N B (baseline)` and positive headroom; an unbaselined file under the limit prints `(limit)`; a file over its ceiling prints negative headroom; an uncovered existing path (`docs/ignored.md`) prints the not-covered line; relative and absolute paths give the same line; several paths print in order; a missing path returns exit 2 and prints nothing to standard output; the call leaves the baseline and the covered files byte-identical and returns 0 even when the gate would fail; `--limit` and `--baseline` are honored; `--headroom` with `--update-baseline` exits 2; one test pins the clean-tree default output text.
  - Validation: `uv run pytest tests/tools/test_check_skill_size.py -q`, then ruff and mypy on the file.

## Compatibility considerations
- The default path and every existing option are unchanged; no caller (CI, the hook, `tools/run_validation_gates.py` gate rows) passes the new option.

## Security considerations
- N/A: read-only; the option only reads sizes of existing files.

## Rollback considerations
- Revert the commit; nothing else depends on the option until the instruction text of the later procedures names it.

## Validation plan
- `uv run ruff format tools/check_skill_size.py`, `uv run ruff check ... --fix` and confirm, `uv run mypy tools/check_skill_size.py`, `uv run bandit tools/check_skill_size.py`; `radon cc tools/check_skill_size.py -s` recorded.
- `uv run python -m tools.check_module_size --scripts-dir tools --baseline tools/check_module_size_tools_baseline.txt` exits 0.
- Default-output parity: save `uv run python tools/check_skill_size.py` output before the edit and compare after.
- `uv run pytest tests/tools/test_check_skill_size.py -q`.

## Completion criteria
- `--headroom` prints the three line forms and the not-covered line, returns 2 for a missing path, writes nothing, and never runs the gate; the default output and exit codes are identical to the saved output; lint, type, bandit, tests, and the size gate pass.

## Out of Scope
- The gate logic, ceilings, the baseline file, and other options.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Save the default output, then add the option, report functions, and parser change per Procedure | Pending | — | — | |
| 2 | Add the tests listed under Companion test files | Pending | — | — | |
| 3 | Run ruff, mypy, bandit, the tools size gate, and the default-output comparison | Pending | — | — | |

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
- **Requirement ID**: `REQ-001`, `REQ-002`, `REQ-004` (report, defaults unchanged, size)
- **Source issue**: issues/20261127-120059_flowopt001_skill-size-fallout-check.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261127-151623_flowopt001_skill-size-fallout-check.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261127-152121
- **Related target files**: `tools/check_skill_size.py`, `tests/tools/test_check_skill_size.py`
