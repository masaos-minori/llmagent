## Goal
- Add tests to `tests/tools/test_run_validation_gates.py` for `--failures-only` rendering, the `Result:` line, exit-code parity, and unchanged defaults (`REQ-002`, `REQ-003`, `REQ-004`).

## Scope
**Release unit**: N/A: not part of a release unit

- Own document: two target rows (the renderer and the runner) name this test file in `Related Tests`, so it is not a companion. Runs after seq 03 and seq 04.

## Assumptions
- Verified in Step 3a: the file already has `_mixed_results()` (line 1045: a `Fail`, a missing-tool `Not available`, and a `runtime-argument` `Not available`) and renders with `report.render_summary(results, changed, mode, base[, verbose])`; defaults are pinned by `test_default_summary_hides_runtime_argument_rows` and its neighbors, which stay unchanged.
- `_run_gates` calls module-level `_changed_files`, `select_gates`, and `run_gates` of `tools.run_validation_gates`, so tests can patch them with `monkeypatch.setattr`.

## Design decisions
- Append tests; do not edit existing tests. Build `Pass` and `Partial` results with `GateResult` as `_mixed_results` does.

## Alternatives considered
- Running the real gates: rejected, slow and environment-dependent.

## Implementation
### Target file
`tests/tools/test_run_validation_gates.py`

### Procedure
1. Failures-only rendering: with results `Pass`, `Fail`, `Partial`, `Blocked`, `Not available` (missing tool), and `Not available` (`runtime-argument`) assert the output has no `Pass` row, has the `Fail`, `Partial`, `Blocked`, and missing-tool rows, has one hidden-count line for the runtime-argument row, prints `changed files: 2` for two changed files and not the file list, and ends with `Result: Fail (1 failing gate(s))`.
2. With `verbose=True` the runtime-argument row is printed and there is no count line.
3. All results `Pass`: output is the header and `Result: Pass`; empty results: the header, `No gates selected for these changed files.`, and `Result: Pass`.
4. Default parity: `render_summary(results, changed, "fast", "master")` equals the expected literal text of the current default for `_mixed_results()` (pin the literal), and the default path with `failures_only=False` is identical.
5. Exit parity through `_run_gates`: patch `_changed_files`, `select_gates`, `run_gates` to return scripted results; for an all-`Pass` set and a set with one `Fail`, assert `_run_gates(..., failures_only=True)` and `_run_gates(...)` return the same code (0 and 1), and that `Blocked` or `Not available` alone returns 0 in both.
6. Parser: `build_parser().parse_args(["--failures-only"]).failures_only` is true and false by default.
7. Size cap: assert `Path("tools/run_validation_gates.py").stat().st_size <= 24576` (anchored at the repository root).

### Method
- Use `capsys` for rendered output and the existing import style (`import tools._validation_gate_report as report` inside the test).

### Details
- Line length 88; English comments; annotated test signatures like the neighboring tests.

## Compatibility considerations
- Test-only; the existing tests of the file stay unchanged and must pass.

## Security considerations
- N/A: no external effects.

## Rollback considerations
- Revert the commit.

## Validation plan
- `uv run pytest tests/tools/test_run_validation_gates.py -q`; `uv run ruff format`, `uv run ruff check`, `uv run mypy` on the file.

## Completion criteria
- Acceptance criteria AC-3, AC-4, AC-6 of the Plan are each covered by a passing test and the file passes ruff and mypy.

## Out of Scope
- Changes to the tools beyond what a failing test proves necessary (an amendment of the seq 03 or seq 04 procedure).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Append the tests of Procedure | Pending | — | — | Needs seq 03 and seq 04 first |
| 2 | Run the tests and fix failures in the tests or report a tool defect | Pending | — | — | |
| 3 | Run ruff and mypy on the file | Pending | — | — | |

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
- **Requirement ID**: `REQ-002`, `REQ-003`, `REQ-004` (behaviors under test)
- **Source issue**: issues/20261126-151443_wfeff008_gate-output-filters.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261127-104530_wfeff008_gate-output-filters.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261127-105933
- **Related target files**: `tests/tools/test_run_validation_gates.py`
