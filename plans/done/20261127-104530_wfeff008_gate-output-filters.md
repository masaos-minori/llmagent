## Goal
- Add two opt-in output filters, leaving default output and exit codes unchanged: a repeatable `--plan PATH` option on `tools/check_plan_target_overlaps.py` that keeps only findings naming that Plan, and a `--failures-only` option on `tools/run_validation_gates.py` that prints only the changed-file count, the non-passing rows, and a final result line.

## Priority
Low

## Scope
- **In-Scope**: argument handling and rendering of the two tools (the failures-only renderer lives in `tools/_validation_gate_report.py`, where the existing renderer is); unit tests for both options; the `tools/TOOL_DESCRIPTIONS.md` rows.
- **Out-of-Scope**: changing what either checker detects or how gates are selected and run; changing default output, `--format` output, or exit codes; adopting `--plan` in the skill texts.
- **Dependencies**: N/A: none

## Background
Verified in Step 3: `tools/check_plan_target_overlaps.py` (7831 B) has only a `--format` option (`build_arg_parser`, lines 190-204) and `main` (lines 207-226) always prints every overlap and returns 0. `tools/run_validation_gates.py` (23946 B) has `--base`, `--full`, `--jobs`, `--verbose` (lines 592-632); `_run_gates` (lines 555-562) calls `render_summary` from `tools/_validation_gate_report.py` (2675 B), which prints the header with the full changed-file list, one row per gate, and a count line for the gates hidden because their command needs a runtime argument; the exit code is 1 only when a gate's status is `Fail`.

## Problem
Each run adds unrelated lines to the working context, and the useful result is a small part of it. Three details of the Issue do not match the code: the gate output has no final status line today, the renderer is not in `tools/run_validation_gates.py`, and that file has only 630 B below its 24576 B size gate.

## Reason for Change
Token cost per run; no correctness risk. Not urgent.

## Implementation Intent
Post-filter the overlap findings by Plan path, and add a failures-only branch to the existing report renderer, both behind new flags so default behavior stays byte-identical.

## Requirements
- `REQ-001`: `tools/check_plan_target_overlaps.py` accepts a repeatable `--plan PATH` (repository-relative or absolute); the findings printed in every format are only those whose detail names one of the given Plans as an exact path in its Frozen-Plan list; a `--plan` that is not an existing file ends with exit 2 and no findings output; without `--plan` output and exit code 0 are unchanged; detection (`find_cross_plan_target_overlaps`) is not modified.
- `REQ-002`: `tools/run_validation_gates.py` accepts `--failures-only`; the output is the header line with the changed-file count (no file list), every row whose status is not `Pass` (`Fail`, `Partial`, `Blocked`, and `Not available` rows; rows whose reason is `runtime-argument` stay behind the existing count line unless `--verbose` is also given), and a final line `Result: Pass` or `Result: Fail ({n} failing gate(s))` computed by the same predicate as the exit code.
- `REQ-003`: Without the new options the output of both tools is byte-identical and the exit codes are unchanged; with `--failures-only` the exit code equals the exit code of the full output for the same results.
- `REQ-004`: `tools/run_validation_gates.py` stays at or below 24576 B (`check-module-size-tools`): the renderer change is in `tools/_validation_gate_report.py` and the growth of `tools/run_validation_gates.py` is at most 500 B.
- `REQ-005`: `tools/TOOL_DESCRIPTIONS.md` documents both options.

## Implementation Target Files
**Freeze status**: Frozen (validated in Step 8b: every row `Verified`; `tools/audit_plan_target_paths.py` and the additional checks passed)

This table is the canonical, frozen source of implementation scope for this Plan. Once
`Frozen`, `Implementation steps`, `Acceptance criteria`, and every downstream
`plan-to-implementation-procedure` document MUST reference file paths only from this
table — no other file may be treated as a modification target.

| File Path | Change Responsibility | Reason for Modification | Related Requirement / Acceptance Criterion | Repository Evidence | Related Tests | Validation Status |
|---|---|---|---|---|---|---|
| `tools/check_plan_target_overlaps.py` | Add the repeatable `--plan` option and a post-filter of the findings in `main` | The Issue's Target Files name it; detection stays untouched | `REQ-001`, `REQ-003`; AC-1, AC-2, AC-5 | `tools/check_plan_target_overlaps.py:190-226` `build_arg_parser` and `main`; the finding's `detail` lists Plan paths comma-separated after `targeted by N Frozen Plans at once: ` (lines 139-163) (checked in Step 3) | `tests/tools/test_check_plan_target_overlaps.py` | Verified |
| `tests/tools/test_check_plan_target_overlaps.py` | Add tests for `--plan` in text, JSON, and CSV output, the repeat, the unknown path, and the unchanged default | Unit tests for the new option are required by the Issue | `REQ-001`, `REQ-003`; AC-1, AC-2, AC-5 | `tests/tools/test_check_plan_target_overlaps.py:1-30` has the `_write` and `_plan_text` helpers and imports `tools.check_plan_target_overlaps` (checked in Step 3) | `tests/tools/test_check_plan_target_overlaps.py` | Verified |
| `tools/_validation_gate_report.py` | Add the failures-only branch and the final `Result:` line to `render_summary` | The renderer lives here, not in `tools/run_validation_gates.py` (a discovery that adds this row) | `REQ-002`, `REQ-003`, `REQ-004`; AC-3, AC-4, AC-6 | `tools/_validation_gate_report.py:46-76` `render_summary`, `_print_header`, `_print_rows`; 2675 B; `HIDE_REASON = "runtime-argument"` (checked in Step 3) | `tests/tools/test_run_validation_gates.py` | Verified |
| `tools/run_validation_gates.py` | Add the `--failures-only` option and pass it through `main` and `_run_gates` to the renderer | The Issue's Target Files name it; the file has 630 B of headroom under the 24576 B gate | `REQ-002`, `REQ-003`, `REQ-004`; AC-3, AC-4, AC-6 | `tools/run_validation_gates.py:555-562` `_run_gates`, `:592-632` `build_parser`, `:634-641` `main`; 23946 B (checked in Step 3) | `tests/tools/test_run_validation_gates.py` | Verified |
| `tests/tools/test_run_validation_gates.py` | Add tests for `--failures-only` rendering, the `Result:` line, the exit code parity, and the unchanged default | Unit tests for the new option are required by the Issue; the file already tests `render_summary` (line 1075) | `REQ-002`, `REQ-003`, `REQ-004`; AC-3, AC-4, AC-6 | `tests/tools/test_run_validation_gates.py:1075` `report.render_summary(_mixed_results(), ...)` with a `_mixed_results` helper (checked in Step 3) | `tests/tools/test_run_validation_gates.py` | Verified |
| `tools/TOOL_DESCRIPTIONS.md` | Update the Index and Work Items or runner rows of both tools with the new options | The Issue's Documentation Impact; `tools/check_tool_descriptions_sync.py` guards the inventory | `REQ-005`; AC-7 | `tools/TOOL_DESCRIPTIONS.md` rows for `check_plan_target_overlaps.py` (lines 116, 293) and `run_validation_gates.py` (lines 172, 306) (checked in Step 3) | `tools/check_tool_descriptions_sync.py` run | Verified |

Rules (see `rules/workflow-lifecycle.md` Implementation Target Files Validation (Plan
Freeze) for the full validation procedure):
- One row per file. A directory, glob pattern (`*`, `**`), component/module name, file
  group, or a vague phrase (e.g. "related files", "as necessary", "etc.") MUST NOT
  appear as a row — list each file individually by its exact repository-relative path.
- Record a test, configuration, schema, migration, deployment, or documentation file as
  its own row when it requires modification — do not fold it into the row for the
  source file it accompanies.
- `Validation Status` is `Verified` or `Needs confirmation` per row; every row must be
  `Verified` before this section may be marked `Frozen`.
- Write every `File Path` cell, every `tests/...py` path in `Related Tests`, and every path in
  `Implementation steps` in backticks.

## Reference Files
Files that must be read to implement the targets above, but MUST NOT be modified.

| File Path | Why It Must Be Read | Related Target File or Requirement |
|---|---|---|
| `tools/amend_plan.py` | Runs `check_plan_target_overlaps.py` and filters its lines to the amended Plan; its caller behavior must not change | `REQ-003` |
| `tools/_validation_gate_defs.py` | The `Gate` type and the status vocabulary the renderer prints | `REQ-002` |
| `tools/check_module_size_tools_baseline.txt` | Confirms `tools/run_validation_gates.py` has no baseline entry, so the 24576 B gate applies | `REQ-004` |
| `rules/ai-execution.md` | Item 12: an unrun check is never reported as passed, which governs the `Not available` rows | `REQ-002` |

## Acceptance Criteria
- AC-1 (`REQ-001`): `--plan` output contains only findings that name a given Plan, in text, JSON, and CSV; repeating the option keeps findings that name any of them.
- AC-2 (`REQ-001`): A `--plan` naming a Plan with no overlap prints `No findings.` (the format's empty form) and exits 0; a path that is not a file exits 2.
- AC-3 (`REQ-002`): `--failures-only` output omits `Pass` rows and the changed-file list, shows the changed-file count, every `Fail`, `Partial`, `Blocked`, and visible `Not available` row, and ends with the `Result:` line.
- AC-4 (`REQ-003`): `--failures-only` returns the same exit code as the full output for the same results (1 only when a gate is `Fail`).
- AC-5 (`REQ-003`): Output and exit code of `tools/check_plan_target_overlaps.py` without `--plan` are byte-identical to before.
- AC-6 (`REQ-003`, `REQ-004`): Output and exit code of `tools/run_validation_gates.py` without `--failures-only` are byte-identical to before; the file is at most 24576 B.
- AC-7 (`REQ-005`): `check_tool_descriptions_sync.py` passes and both options are documented; the existing tests of both tools pass.

## Tests
- `REQ-001`: tests with two synthetic Frozen Plans and one overlap: `--plan` of either Plan keeps the finding, `--plan` of a third Plan prints the empty form, repeat keeps a union, absolute and relative paths match, an unknown path exits 2, JSON and CSV outputs are filtered the same way.
- `REQ-002`, `REQ-003`: tests that render a mixed result set (`Pass`, `Fail`, `Partial`, `Blocked`, `Not available` with and without `runtime-argument`) and assert rows, header count, the `Result:` line, and the exit code parity through `_run_gates`.
- `REQ-003`: tests that the default outputs equal the pre-change expected text (the existing tests stay unchanged and pass).
- Tool checks: ruff, mypy, bandit on the changed Python files; `uv run python -m tools.check_module_size --scripts-dir tools --baseline tools/check_module_size_tools_baseline.txt`.

## Documentation Impact
N/A: no `docs/*.md` change. The rows of `tools/TOOL_DESCRIPTIONS.md` are a target row (`REQ-005`).

## Assumptions
- The failures-only mode keeps the existing hide rule for `Not available` rows whose reason is `runtime-argument` (shown as the count line, as in the default output) instead of printing them as rows, because `rules/ai-execution.md` item 12 is already met by that count line and printing three to six always-unavailable rows would defeat the filter; `--verbose` together with `--failures-only` prints them.
- `Partial` counts as non-passing and is printed; only `Pass` rows are omitted.
- Row order is implementation order (`seq` follows the table position): the renderer row precedes the runner row because the runner passes a new keyword to `render_summary`, which would fail at run time before the renderer accepts it (reordered in plan-to-implementation-procedure Step 3a).
- The `Result:` line is new and appears only in `--failures-only` output (the default output has no final status line today), so the default stays byte-identical.
- `skills/git-commit-and-sync/workflow.md` Phase 4 tells the reader to compare the summary's file list with the staged set; that text keeps working because the default output still prints the list, and the failures-only output omits it by design (stated in the tool row).

## Unknowns
| ID | Unknown Description | Evidence Missing | Resolution Path | Blocking? (True/False) |
|---|---|---|---|---|
| UNK-01 | Whether the Issue meant `runtime-argument` `Not available` rows to print in failures-only mode | The Issue says "every `Not available` row" while the default output already collapses these rows into a count line | Resolved by the Assumption above (existing hide rule kept, `--verbose` shows them); revisit only if the owner wants rows | False |
| UNK-02 | Whether any other caller parses `tools/run_validation_gates.py` or `tools/check_plan_target_overlaps.py` output | A repository search covers only this repository | Defaults are unchanged, so no parsing caller can break; the `amend_plan.py` filter is a reference file | False |

## Affected areas
`skills/DESIGN.md` Change-impact table, extended with `Churn (30d)` and `Bus Factor`
columns. The `File` column here MUST be a subset of `Implementation Target Files`'
rows — this table analyzes change-impact risk for those same files; it is not a
separate scope-of-record.

| File | Change | Blast Radius | Churn (30d) | Bus Factor | deploy.sh Impact |
|---|---|---|---|---|---|
| `tools/check_plan_target_overlaps.py` | Modify | Low — one caller by subprocess (`tools/amend_plan.py`), default output unchanged | 1 | High (100% single author) | not applicable (not rsynced) |
| `tools/run_validation_gates.py` | Modify | Medium — pre-commit hooks, the git-commit-and-sync skill, and many tests rely on it; 630 B below the size gate | 11 | High (100% single author) | not applicable (not rsynced) |
| `tools/_validation_gate_report.py` | Modify | Low — one importer (`tools/run_validation_gates.py`); covered by `tests/tools/test_run_validation_gates.py` | 1 | High (100% single author) | not applicable (not rsynced) |
| `tests/tools/test_check_plan_target_overlaps.py` | Modify | Low | 0 | High (100% single author) | not applicable (rsynced) |
| `tests/tools/test_run_validation_gates.py` | Modify | Low — large existing file, appended tests only | 10 | High (100% single author) | not applicable (rsynced) |
| `tools/TOOL_DESCRIPTIONS.md` | Modify | Low — read by `tools/check_tool_descriptions_sync.py` | 82 | High (100% single author) | not applicable (not rsynced) |

## Design
Path B (more than 3 files, public CLI options of two tools). Analysis recorded:
- Architecture (checked in Step 3): `tools/run_validation_gates.py` imports `render_summary` from `tools/_validation_gate_report.py`, which imports `GateResult` only for typing; the failures-only branch belongs in the renderer so the runner stays small. The overlap tool's `main` prints through `render_text`, `render_json`, or `render_csv`; filtering the finding list before rendering keeps all three formats consistent without touching detection.
- Dependency graphing (checked in Step 3): `tools/amend_plan.py:516-527` runs the overlap tool by subprocess and filters its lines itself, so the new option does not change it; `tests/tools/test_run_validation_gates.py` exercises `report.render_summary` (line 1075) and `tests/tools/test_check_plan_target_overlaps.py` exercises the finders and renderers.
- Historical analysis and operational dependencies: churn and bus factor are in `Affected areas`; no MCP server, database, or port is involved.
- Decision (filter by exact path): a finding's `detail` has the form `targeted by N Frozen Plans at once: p1, p2 -- verify ...`; the filter extracts the comma-separated list between the colon and ` -- ` and tests membership, so a path that is a prefix of another never matches.
- Decision (size): `tools/run_validation_gates.py` growth is limited to the parser option, one parameter through `_run_gates`, and the `main` call; the render logic is in the report module (which has a wide margin).
- Predictable fallout check (checked in Step 3): module size - `tools/run_validation_gates.py` 23946 B to at most 24446 B, under the gate; pinned counts - no test pins the option count or the row count of the runner's parser (`rg` over `tests/tools/`), and the existing `render_summary` tests stay valid because defaults do not change; tool inventory - `tools/TOOL_DESCRIPTIONS.md` is a target row and no tool is added or removed; generated blocks - not affected; gate entry in `tools/_validation_gate_defs.py` and `rules/tool-gates.md` row - not affected: no tool is added and the existing gate commands do not use the new options.
- Consumer scan and persisted schema check: not applicable (no schema, shared constant, or removed symbol; two optional CLI options are added).
- Validation baseline: `radon` is run per Python target (`radon cc <path> -s`) at implementation time; `vulture` is not installed (Tool availability guard); `bandit` runs by path; diff-cover N/A because CI measures `--cov=scripts`, so `tools/` changes are validated by unit tests.

## Implementation steps
1. **Phase 1: Overlap checker option**
   - [ ] Add `--plan` and the post-filter to `tools/check_plan_target_overlaps.py` (`REQ-001`, `REQ-003`).
   - [ ] Add the tests to `tests/tools/test_check_plan_target_overlaps.py` (`REQ-001`, `REQ-003`); run ruff, mypy, bandit, and the file's tests.
2. **Phase 2: Gate runner option**
   - [ ] Add the failures-only branch to `tools/_validation_gate_report.py` (`REQ-002`, `REQ-003`).
   - [ ] Add `--failures-only` and the pass-through to `tools/run_validation_gates.py` (`REQ-002`, `REQ-004`).
   - [ ] Add the tests to `tests/tools/test_run_validation_gates.py` (`REQ-002`, `REQ-003`, `REQ-004`); run ruff, mypy, bandit, the tests, and the tools size gate.
3. **Phase 3: Documentation and deployment check**
   - [ ] Update the rows in `tools/TOOL_DESCRIPTIONS.md` (`REQ-005`); run `check_tool_descriptions_sync.py`.
   - [ ] Deployment: N/A, no `scripts/` or `config/` file changes; `tools/` is not rsynced by `deploy/deploy.sh`.

### Release units
N/A: no release unit

## Validation plan
| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| `tools/check_plan_target_overlaps.py` | Unit | `uv run pytest tests/tools/test_check_plan_target_overlaps.py` | All tests pass, existing ones unchanged |
| `tools/run_validation_gates.py`, `tools/_validation_gate_report.py` | Unit | `uv run pytest tests/tools/test_run_validation_gates.py` | All tests pass, existing ones unchanged |
| the three tool files | Static checks | `uv run ruff format`, `uv run ruff check`, `uv run mypy`, `uv run bandit` on each file | No findings |
| `tools/run_validation_gates.py` | Size gate | `uv run python -m tools.check_module_size --scripts-dir tools --baseline tools/check_module_size_tools_baseline.txt` | Exit 0 |
| `tools/TOOL_DESCRIPTIONS.md` | Inventory sync | `uv run python tools/check_tool_descriptions_sync.py` | Exit 0 |
| both tools | Default-output parity | run each without the new option before and after (saved output) | Byte-identical |

## Risks
- **Risk**: The runner file crosses 24576 B and fails `check-module-size-tools` → **Mitigation**: the renderer holds the logic, the growth is capped at 500 B in `REQ-004`, and the size gate runs before the cycle ends.
- **Risk**: A default-output change breaks a reader of the summary (`skills/git-commit-and-sync/workflow.md` Phase 4 reads the file list) → **Mitigation**: defaults are tested byte-identical (`REQ-003`); only the new option omits the list.
- **Risk**: The path filter matches a similar path by substring → **Mitigation**: exact membership in the extracted list, with a test using a prefix path.
- **Risk**: `--failures-only` hides a check that did not run → **Mitigation**: `Not available` rows other than `runtime-argument` stay visible and the runtime-argument gates stay in the count line, as in the default output (`rules/ai-execution.md` item 12).
- **Risk**: The new `Result:` line is mistaken for part of the default contract → **Mitigation**: it is printed only in failures-only mode and documented in the tool row.

## Execution Status

Table structure, status/type vocabulary, and general guidance: see
`templates/execution-status.md`.

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Add `--plan` and its tests (`tools/check_plan_target_overlaps.py`, `tests/tools/test_check_plan_target_overlaps.py`) | In Progress | — | — |  |
| 2 | Add `--failures-only`, its renderer branch, and tests (`tools/_validation_gate_report.py`, `tools/run_validation_gates.py`, `tests/tools/test_run_validation_gates.py`) | In Progress | — | — |  |
| 3 | Update the tool rows; deployment check is N/A (`tools/TOOL_DESCRIPTIONS.md`) | In Progress | — | — |  |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| — | — | — | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| implementations/20261127-105933_01_tools_check_plan_target_overlaps.py.md | 1 | Procedure | Pending | — | — |
| implementations/20261127-105933_03_tools__validation_gate_report.py.md | 2 | Procedure | Pending | — | — |
| implementations/20261127-105933_04_tools_run_validation_gates.py.md | 2 | Procedure | Pending | — | — |
| implementations/20261127-105933_05_tests_tools_test_run_validation_gates.py.md | 2 | Procedure | Pending | — | — |
| implementations/20261127-105933_06_tools_TOOL_DESCRIPTIONS.md.md | 3 | Procedure | Pending | — | — |

## Traceability
- **Workflow phase**: issue-to-plan
- **Source issue**: issues/20261126-151443_wfeff008_gate-output-filters.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: this document is the generated plan
- **Source implementation procedure**: N/A: not applicable in this phase
- **Generated at**: 20261127-104530
- **Evidence revision**: 1b5713cfa10bad8c4ce6aa43ede8c07cf30d54ee
- **Related target files**: `tools/check_plan_target_overlaps.py`, `tools/run_validation_gates.py`, `tools/_validation_gate_report.py`, `tests/tools/test_check_plan_target_overlaps.py`, `tests/tools/test_run_validation_gates.py`, `tools/TOOL_DESCRIPTIONS.md`

### Requirement Traceability

| Requirement ID | Source Issue section or evidence | Target file | Implementation step | Acceptance criterion | Test or validation item | Status |
|---|---|---|---|---|---|---|
| `REQ-001` | Issue Required Changes 1 | `tools/check_plan_target_overlaps.py` | Phase 1 | AC-1, AC-2 | `tests/tools/test_check_plan_target_overlaps.py` | Explicit in issue |
| `REQ-001` | Issue Testing Expectations | `tests/tools/test_check_plan_target_overlaps.py` | Phase 1 | AC-1, AC-2 | `uv run pytest tests/tools/test_check_plan_target_overlaps.py` | Explicit in issue |
| `REQ-002` | Issue Required Changes 2; renderer location verified in Step 3 | `tools/run_validation_gates.py` | Phase 2 | AC-3 | `tests/tools/test_run_validation_gates.py` | Derived from confirmed evidence |
| `REQ-002` | Issue Required Changes 2; `tools/_validation_gate_report.py:46-76` | `tools/_validation_gate_report.py` | Phase 2 | AC-3 | `tests/tools/test_run_validation_gates.py` | Derived from confirmed evidence |
| `REQ-002` | Issue Testing Expectations | `tests/tools/test_run_validation_gates.py` | Phase 2 | AC-3 | `uv run pytest tests/tools/test_run_validation_gates.py` | Explicit in issue |
| `REQ-003` | Issue Constraints, Acceptance Criteria 2 and 3 | `tools/check_plan_target_overlaps.py` | Phase 1 | AC-5 | `tests/tools/test_check_plan_target_overlaps.py` | Explicit in issue |
| `REQ-003` | Issue Constraints | `tools/run_validation_gates.py` | Phase 2 | AC-4, AC-6 | `tests/tools/test_run_validation_gates.py` | Explicit in issue |
| `REQ-003` | Issue Constraints | `tools/_validation_gate_report.py` | Phase 2 | AC-4, AC-6 | `tests/tools/test_run_validation_gates.py` | Explicit in issue |
| `REQ-003` | Issue Acceptance Criteria 3 | `tests/tools/test_check_plan_target_overlaps.py` | Phase 1 | AC-5 | `uv run pytest tests/tools/test_check_plan_target_overlaps.py` | Explicit in issue |
| `REQ-003` | Issue Acceptance Criteria 3 | `tests/tools/test_run_validation_gates.py` | Phase 2 | AC-4, AC-6 | `uv run pytest tests/tools/test_run_validation_gates.py` | Explicit in issue |
| `REQ-004` | `tools/run_validation_gates.py` 23946 B vs the 24576 B gate (measured in Step 3) | `tools/run_validation_gates.py` | Phase 2 | AC-6 | `uv run python -m tools.check_module_size --scripts-dir tools --baseline tools/check_module_size_tools_baseline.txt` | Confirmed by repository evidence |
| `REQ-004` | Renderer placement | `tools/_validation_gate_report.py` | Phase 2 | AC-6 | `uv run python -m tools.check_module_size --scripts-dir tools --baseline tools/check_module_size_tools_baseline.txt` | Derived from confirmed evidence |
| `REQ-004` | Size cap check by test | `tests/tools/test_run_validation_gates.py` | Phase 2 | AC-6 | `uv run pytest tests/tools/test_run_validation_gates.py` | Derived from confirmed evidence |
| `REQ-005` | Issue Documentation Impact | `tools/TOOL_DESCRIPTIONS.md` | Phase 3 | AC-7 | `uv run python tools/check_tool_descriptions_sync.py` | Explicit in issue |

<!-- tools/generate_workitem.py implementation-procedure-pass timestamp: 20261127-105933 -->