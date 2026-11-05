## Goal
- `module_nodes.py`, `run_refactor_validation.py`, and `audit_plan_target_paths.py` each have a unit-test file under `tests/tools/` that fails when the tool's main behavior breaks and covers at least one negative path, without changing any tool.

## Priority
Medium

## Scope
- **In-Scope**: three new test files (`tests/tools/test_module_nodes.py`, `tests/tools/test_run_refactor_validation.py`, `tests/tools/test_audit_plan_target_paths.py`) built on temporary directories, fixed inputs, and faked subprocess calls.
- **Out-of-Scope**: tests for `fix_docs_section_marks.py`, `fix_docstring_blank_line.py`, `fix_procedure_new_markers.py`, `generate_mcp_inventory.py`, `migrate_runtime_tool_calls.py`, `check_skills_references.py`; any change to the three tools; recording a defect found by a test (that is filed as a separate issue).
- **Dependencies**: this Plan lands before the Plans for `toolcommon001`, `toolsizegate001`, `toolwrite001` (the last one changes `module_nodes.py extract`), and `toolcli001` (it changes the `audit_plan_target_paths.py` entry). Each of those four Plans records the order in its own `Depends on` line (verified 2026-11-05, checked in Step 3a); this Plan depends on none of them.

## Background
No test under `tests/` imports `module_nodes` or `run_refactor_validation`, and no test exercises `audit_plan_target_paths` directly: `tests/tools/test_amend_plan.py` mentions it only through `amend_plan.py`'s subprocess wiring (verified 2026-11-05, checked in Step 2). `module_nodes.py` moves exact source ranges between files; `run_refactor_validation.py` decides whether a refactor passes; `audit_plan_target_paths.py` flags missing Implementation Target Files paths.

## Problem
Tools that rewrite source or decide whether a refactor passes have no regression tests, so the shared-helper, size-gate, and atomic-write work filed alongside this issue cannot be checked against them.

## Reason for Change
Test gap on tools that modify or gate source; the dependent issues touch these files, so the tests land first.

## Implementation Intent
Cover each tool's main behavior and failure paths through its public functions and `main`, with `tmp_path` fixtures and monkeypatched subprocess calls, never running the real toolchain or touching the repository.

## Requirements
- `REQ-001`: `module_nodes` tests MUST cover `measure` (line span and encoded byte size per top-level non-import node, imports skipped, `--min` filter, `--json` output, missing file returns 1), `extract` (exact text moved by `--name` and by `--range`, `--dedent`, destination appended or created, source keeps the remaining lines, unknown name and missing selector exit non-zero), and `compare` (identical move exits 0, a changed body exits 1, a missing function exits 1 and prints `MISSING`). `compare` always reads the old source through `git show <old-rev>:<old-src>`, so its tests MUST fake `module_nodes.subprocess.run` and assert the recorded argv; `extract` errors (unknown name, no selector, invalid `--range`, `--dedent` on a line indented by less than 4 spaces) raise `SystemExit` with an `ERROR:` message, so those tests use `pytest.raises(SystemExit)` rather than a return value.
- `REQ-002`: `run_refactor_validation` tests MUST cover command construction (`_pytest_args` with and without coverage, the diff-cover argument list with `--include`), result aggregation in `validate` and `main` with `_run` faked (an all-pass case printing `GATE PASSED` and returning 0, a failing step printing `GATE FAILED: ...` and returning 1), `_radon_gate` grading (grade C or worse fails, grade B passes), and `--skip` dropping a step.
- `REQ-003`: `audit_plan_target_paths` tests MUST cover an existing target path (no finding), a missing target path, a create-hint exemption (the hint is matched against the second table cell only, not the "Reason for Modification" cell; see UNK-02), a missing `registry/` path without a create hint, skipped header and non-path rows, rows outside the `## Implementation Target Files` section ignored, and `main` returning 1 with findings and 0 without, with the summary line. `main()` takes no argument and reads `sys.argv[1:]`, so its tests monkeypatch `sys.argv` (which keeps working if a later Plan gives `main` an `argv` parameter).
- `REQ-004`: Every test MUST write only inside `tmp_path`, MUST NOT run ruff, mypy, pytest, or git against the real repository, and MUST leave the production files unchanged.

## Implementation Target Files
**Freeze status**: Frozen

| File Path | Change Responsibility | Reason for Modification | Related Requirement / Acceptance Criterion | Repository Evidence | Related Tests | Validation Status |
|---|---|---|---|---|---|---|
| `tests/tools/test_module_nodes.py` | Unit tests for `module_nodes.py` | New file; `tests/tools/` exists | `REQ-001`, `REQ-004`; AC-1, AC-4 | `measure`, `_cmd_measure`, `_extract_lines`, `_cmd_extract`, `_cmd_compare`, `main` in `tools/module_nodes.py`; no test references `module_nodes` (checked in Step 2 and Step 3) | itself | Verified |
| `tests/tools/test_run_refactor_validation.py` | Unit tests for `run_refactor_validation.py` | New file; `tests/tools/` exists | `REQ-002`, `REQ-004`; AC-2, AC-4 | `_run`, `_pytest_args`, `_radon_gate`, `_diff_cover_gate`, `validate`, `main` in `tools/run_refactor_validation.py`; no test references it (checked in Step 2 and Step 3) | itself | Verified |
| `tests/tools/test_audit_plan_target_paths.py` | Unit tests for `audit_plan_target_paths.py` | New file; `tests/tools/` exists | `REQ-003`, `REQ-004`; AC-3, AC-4 | `audit`, `main`, `ROW_RE`, `CREATE_HINTS` in `tools/audit_plan_target_paths.py`; `test_amend_plan.py` only fakes the subprocess call (checked in Step 2 and Step 3) | itself | Verified |

## Reference Files
| File Path | Why It Must Be Read | Related Target File or Requirement |
|---|---|---|
| `tools/module_nodes.py` | Behavior under test (`measure`, `extract`, `compare`) | `REQ-001` |
| `tools/run_refactor_validation.py` | Behavior under test (gate steps, aggregation) | `REQ-002` |
| `tools/audit_plan_target_paths.py` | Behavior under test (path audit, create hints) | `REQ-003` |
| `tests/conftest.py` | `tools/` is put on `sys.path` for all tests; existing tools tests import `tools.<name>` | `REQ-004` |
| `tests/tools/test_check_module_size.py` | Style reference for `tmp_path`-based tools tests | `REQ-001`, `REQ-002`, `REQ-003` |
| `tests/tools/test_amend_plan.py` | Shows how `audit_plan_target_paths` is faked today, so the new file does not duplicate it | `REQ-003` |

## Acceptance Criteria
- AC-1: `tests/tools/test_module_nodes.py` fails when `measure`, `extract`, or `compare` behavior is broken and has at least one negative-path test (`REQ-001`).
- AC-2: `tests/tools/test_run_refactor_validation.py` fails when command construction or aggregation is broken and has a failing-step test (`REQ-002`).
- AC-3: `tests/tools/test_audit_plan_target_paths.py` fails when path auditing is broken and has a missing-path test (`REQ-003`).
- AC-4: `uv run pytest tests/tools -q` passes; `git status` shows no change under `tools/`; no test writes outside `tmp_path` (`REQ-004`).

## Tests
- The deliverable is the tests themselves; each Requirement maps to its file above.
- Mutation check: temporarily break one behavior per tool (for example, change the `--min` comparison in `measure`) and confirm a test fails, then revert the temporary change (`REQ-001`, `REQ-002`, `REQ-003`).

## Documentation Impact
N/A: the Issue states documentation is not required, and no tool behavior changes.

## Assumptions
- Tests import the tools as `tools.<name>`, matching `tests/tools/test_check_module_size.py` (judgment based on the existing style).
- `audit_plan_target_paths.audit` resolves target paths against the current working directory, so tests use `monkeypatch.chdir(tmp_path)` (read from the source, `Path(target).exists()`).
- `module_nodes compare` has no local-file mode: `_cmd_compare` always runs `git show {old_rev}:{old_src}` with `check=True` (read from the source, checked in Step 3a; the earlier draft of this Plan assumed `--old-src` files). Tests fake `module_nodes.subprocess.run` with a `CompletedProcess` whose `stdout` is the old source, and never run git against the repository. A failing git call raises `CalledProcessError` (not caught by the tool); testing that is optional.
- `audit_plan_target_paths.ROW_RE` captures the first two table cells, and `CREATE_HINTS` is matched against the second one. The current Plan template puts "New file" in the third cell, so a real Plan row for a new file is reported as missing: running the tool on this Plan reports its three new test files (exit 1, verified 2026-11-05). The tests pin the current behavior (hint in the second cell exempts, hint only in the third cell does not) and do not change the tool.
- `run_refactor_validation` tests build radon output lines in the exact shape `_RADON_BLOCK` matches (`    F 10:0 name - C (12)`); a class line or a differently shaped line is ignored by the gate.

## Unknowns
| ID | Unknown Description | Evidence Missing | Resolution Path | Blocking? (True/False) |
|---|---|---|---|---|
| UNK-01 | Whether the byte-size rule of `module_nodes measure` is specified anywhere other than its docstring | No other document found | Treat the docstring and the `measure` code (encoded bytes of the node's lines joined by newlines) as the contract; ask the owner only if a test contradicts it | False |
| UNK-02 | Whether `audit_plan_target_paths` matching its create hints against the second table cell (not the "Reason for Modification" cell of the current Plan template) is intended | No document states which cell carries the hint; the tool's header skip list still names the older `Change Type` column | Pin the current behavior in the tests; file a separate issue for the owner (a test never changes the tool, per Scope) | False |

## Affected areas
| File | Change | Blast Radius | Churn (30d) | Bus Factor | deploy.sh Impact |
|---|---|---|---|---|---|
| `tests/tools/test_module_nodes.py` | Create | Low (new test file only) | N/A | N/A | not applicable (rsynced) |
| `tests/tools/test_run_refactor_validation.py` | Create | Low | N/A | N/A | not applicable (rsynced) |
| `tests/tools/test_audit_plan_target_paths.py` | Create | Low | N/A | N/A | not applicable (rsynced) |

## Design
- Path A: three new files, no interface or schema change. Validation quality baseline: `N/A: no Python target under scripts/ or tools/` (the targets are new test files; the three tools are reference only).
- `module_nodes`: build small source fixtures in `tmp_path`, call `measure`, `_extract_lines`, and `main([...])` with argument lists so the real argparse paths run; assert on exact moved text and on file contents after `extract`. For `compare`, monkeypatch `module_nodes.subprocess.run` to return the old source and assert the recorded `git show` argv.
- `run_refactor_validation`: monkeypatch the module-level `_run` with a recorder returning scripted `(returncode, output)` pairs; assert the recorded commands and the printed `PASS` and `FAIL` lines.
- `audit_plan_target_paths`: write plan files with an `## Implementation Target Files` table into `tmp_path`, `monkeypatch.chdir(tmp_path)`, and call `audit` and `main`.
- Consumer scan: not applicable; no persisted schema, public API, or shared constant changes.

## Implementation steps
1. **Phase 1: `audit_plan_target_paths` tests**
   - [ ] Add the path-audit and `main` tests (`REQ-003`, `REQ-004`; `tests/tools/test_audit_plan_target_paths.py`)
2. **Phase 2: `run_refactor_validation` tests**
   - [ ] Add the command-construction, aggregation, radon, and `--skip` tests (`REQ-002`, `REQ-004`; `tests/tools/test_run_refactor_validation.py`)
3. **Phase 3: `module_nodes` tests**
   - [ ] Add the `measure`, `extract`, and `compare` tests, including negative paths (`REQ-001`, `REQ-004`; `tests/tools/test_module_nodes.py`)
4. **Phase 4: Verification**
   - [ ] Run the full `tests/tools` suite, the per-file checks of `routing.md` "Adding a new tool" applied to the test files, and the mutation check from Tests (`REQ-001` to `REQ-004`; the three test files). No deploy step: only `tests/` changes.

### Release units
N/A: no release unit

## Validation plan
| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| `tests/tools/test_module_nodes.py` | Unit | `uv run pytest tests/tools/test_module_nodes.py -q` | All pass |
| `tests/tools/test_run_refactor_validation.py` | Unit with faked subprocess | `uv run pytest tests/tools/test_run_refactor_validation.py -q` | All pass |
| `tests/tools/test_audit_plan_target_paths.py` | Unit with temporary plans | `uv run pytest tests/tools/test_audit_plan_target_paths.py -q` | All pass |
| `tests/tools` | Regression | `uv run pytest tests/tools -q` | No new failure |
| three new files | Lint and format | `uv run ruff format` and `uv run ruff check` on each file | Clean |
| three new files | Mock-patch target check | `uv run python tools/check_mock_patch_targets.py` | No finding |

## Risks
- **Risk**: A test exposes a defect in a tool → **Mitigation**: record it as a separate issue and keep the tool unchanged (Issue Constraints).
- **Risk**: A faked `_run` hides a real command-construction error → **Mitigation**: assert the full recorded argument lists, not only the return codes.
- **Risk**: `extract` tests write outside `tmp_path` through relative paths → **Mitigation**: pass absolute `tmp_path` paths and assert `git status` shows no change after the run.
- **Risk**: A `compare` test that does not fake `subprocess.run` runs the real `git show` against the repository → **Mitigation**: an autouse fixture in `test_module_nodes.py` replaces `module_nodes.subprocess.run` with a function that fails the test unless a test installs its own fake.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Add `audit_plan_target_paths` tests | Completed | — | 20261105-143206 |  |
| 2 | Add `run_refactor_validation` tests | Completed | — | 20261105-142642 |  |
| 3 | Add `module_nodes` tests | Completed | — | 20261105-142252 |  |
| 4 | Verify the suite, lint, and mutation check | Completed | — | 20261105-143225 | Run by code-implementation: full suite, ruff, mypy, check_mock_patch_targets on the three files; one mutation per tool failed a test and was reverted; git diff tools/ empty |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| — | — | — | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| implementations/20261105-132713_01_tests_tools_test_module_nodes.py.md | 3 | Procedure | Completed | — | — |
| implementations/20261105-132713_02_tests_tools_test_run_refactor_validation.py.md | 2 | Procedure | Completed | — | — |
| implementations/20261105-132713_03_tests_tools_test_audit_plan_target_paths.py.md | 1 | Procedure | Completed | — | — |

## Traceability
- **Workflow phase**: issue-to-plan
- **Source issue**: issues/20261104-152002_toolstest001_add-tests-for-untested-tools.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: this document is the generated plan
- **Source implementation procedure**: N/A: not applicable in this phase
- **Generated at**: 20261105-105344
- **Related target files**: tests/tools/test_module_nodes.py, tests/tools/test_run_refactor_validation.py, tests/tools/test_audit_plan_target_paths.py

### Requirement Traceability
| Requirement ID | Source Issue section or evidence | Target file | Implementation step | Acceptance criterion | Test or validation item | Status |
|---|---|---|---|---|---|---|
| REQ-001 | Required Changes (module_nodes); `tools/module_nodes.py` | `tests/tools/test_module_nodes.py` | 3 | AC-1 | `test_module_nodes.py` and mutation check | Confirmed by repository evidence |
| REQ-002 | Required Changes (run_refactor_validation); `tools/run_refactor_validation.py` | `tests/tools/test_run_refactor_validation.py` | 2 | AC-2 | `test_run_refactor_validation.py` | Confirmed by repository evidence |
| REQ-003 | Required Changes (audit_plan_target_paths, corrected in Step 2); `tools/audit_plan_target_paths.py` | `tests/tools/test_audit_plan_target_paths.py` | 1 | AC-3 | `test_audit_plan_target_paths.py` | Confirmed by repository evidence |
| REQ-004 | Constraints; Acceptance Criteria 3 | `tests/tools/test_module_nodes.py` | 3, 4 | AC-4 | Full `tests/tools` run | Explicit in issue |
| REQ-004 | Constraints; Acceptance Criteria 3 | `tests/tools/test_run_refactor_validation.py` | 2, 4 | AC-4 | Full `tests/tools` run | Explicit in issue |
| REQ-004 | Constraints; Acceptance Criteria 3 | `tests/tools/test_audit_plan_target_paths.py` | 1, 4 | AC-4 | Full `tests/tools` run | Explicit in issue |

<!-- tools/generate_workitem.py implementation-procedure-pass timestamp: 20261105-132713 -->