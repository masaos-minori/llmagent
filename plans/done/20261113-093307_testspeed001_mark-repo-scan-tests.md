## Goal
- Mark the five tests that scan the whole repository with a dedicated pytest marker `repo_scan`, and exclude that marker from the documented iteration runs (impact-based `--testmon-forceselect` selection), so an edit-test cycle no longer pays about 158 s of call time for scans that do not depend on the change; no test is deleted, weakened, or unconditionally skipped, and the final full run, pre-commit, and CI keep running them.

## Priority
Medium

## Scope
- **In-Scope**: register the `repo_scan` marker in `pyproject.toml`; apply it to the five tests; add the exclusion to the iteration-selection commands in `skills/python-test-and-fix/workflow.md` Step 10 and `skills/code-implementation/workflow.md` Step 4; state the operational rule once in `skills/python-test-and-fix/workflow.md` Step 10 and refer to it from `skills/python-test-and-fix/SKILL.md`; confirm the selection by collection checks; record the inner-loop call time before and after.
- **Out-of-Scope**: speeding up the checkers; changing which checkers run as pre-commit hooks or in CI; the CI command (it keeps no `-m` filter); parallel-execution defaults; the slow secret-scrub and timeout tests; the production-safety default sentences and the per-test-path commands that carry the `-m "not integration and not production_paths_allowed"` expression; marking tests that scan the repository but take only seconds.
- **Dependencies**: related, not blocking: `issues/20261112-183849_testspeed003_cut-timeout-test-waits.md` (no new marker is needed there), and the Issues `issues/20261112-183922_testspeed004_adopt-parallel-test-execution.md` and `issues/20261112-184029_testspeed006_docs-only-step4-exemption.md`, which edit the same settings and Step 4 text. This Plan is written first because it defines the marker name and meaning that the other two refer to; implement it before them. No Plan or Issue blocks this one.

## Background
Measured on 2026-11-12 with `uv run pytest -n auto -q -p no:randomly -m "not integration and not production_paths_allowed" --durations=25` (8 cores, 3m47s wall time), five tests spend about 158 s of call time on whole-repository scans: `tests/tools/test_check_compat_shims.py::TestProductionCategoryZero::test_real_repo_manifest_passes`, `tests/tools/test_no_compatibility_policy_gate.py::TestNoLiveReferences::test_zero_findings_across_live_tree`, `tests/tools/test_no_compatibility_policy_gate.py::TestCheckerBlocking::test_repo_root_run_passes`, and the two tests of `tests/tools/test_check_docs_quality.py::TestRegressionFullDocsTree`. A profile of `tests/tools` on 2026-11-13 (4 workers) shows the same five on top (103 s, 100 s, 90 s, 30 s, 27 s) and nothing else above 6 s (the next are `test_run_cited_adr_tests` end-to-end tests at about 5 s and `test_live_repository_has_no_violations` at 3.5 s). The hooks `check-compat-shims` (same checker and arguments as the two compat-shims tests, but path-filtered) and `check-docs-quality` run the same checkers, and `ci.yml` runs `pre-commit run --all-files` in its `lint` job.

## Problem
Every iteration run of the non-integration suite pays about 158 s of call time for scans whose result depends on the whole repository, not on the code under change. They dominate the tail of the run, and each is one test, so they also set a floor on parallel wall time. The `-m` expression in the skills has no marker for this kind of test.

## Reason for Change
The development loop is dominated by test wall time. These five tests are the largest identifiable block that is independent of the change being made. The change is cheap, keeps the checks enforced in the final run and in CI, and is a prerequisite for measuring other speedups cleanly.

## Implementation Intent
Register one marker next to `integration` in `pyproject.toml`, apply it to the five tests at the narrowest scope (method or class) that covers only the scanning tests, and add `and not repo_scan` only to the iteration-selection commands. The `-m "not integration and not production_paths_allowed"` expression has two roles in the skills: a production-safety default (what is safe to run) and an iteration or final selection. Only the iteration commands change; the safety default, per-test-path commands, and the final full run keep selecting the marked tests. State the rule once and refer to it.

## Requirements
- `REQ-001`: Register the marker `repo_scan` in `pyproject.toml` with a description stating that it covers tests that scan the whole repository and that iteration runs deselect it.
- `REQ-002`: Apply `@pytest.mark.repo_scan` to exactly the five tests listed in the Background, at method level for `test_real_repo_manifest_passes` and `test_repo_root_run_passes`, and at class level for `TestNoLiveReferences` and `TestRegressionFullDocsTree`, without changing any assertion.
- `REQ-003`: Show by collection checks that the marker selects exactly the intended tests, that the iteration expression deselects them, and that a run without `-m` still collects them; record that no other test in `tests/tools` is a comparable whole-tree scan above the threshold of about 10 s.
- `REQ-004`: State the operational rule once in `skills/python-test-and-fix/workflow.md` Step 10 (what the marker means, which commands exclude it, and that the final full run, the coverage run, pre-commit, and CI still run it), and add `and not repo_scan` to that step's `--testmon-forceselect` command only.
- `REQ-005`: Make `skills/python-test-and-fix/SKILL.md` (Step 10 row) and `skills/code-implementation/workflow.md` (Step 4 `--testmon-forceselect` command) consistent with REQ-004 by referring to it, without restating it.
- `REQ-006`: Keep the CI test command unchanged (no `-m` filter), keep every assertion, and record the inner-loop call time before and after, measured with the same command, in the change record.

## Implementation Target Files
**Freeze status**: Frozen

This table is the canonical, frozen source of implementation scope for this Plan. Once
`Frozen`, `Implementation steps`, `Acceptance criteria`, and every downstream
`plan-to-implementation-procedure` document MUST reference file paths only from this
table — no other file may be treated as a modification target.

| File Path | Change Responsibility | Reason for Modification | Related Requirement / Acceptance Criterion | Repository Evidence | Related Tests | Validation Status |
|---|---|---|---|---|---|---|
| pyproject.toml | Pytest configuration, including the registered markers | Add the `repo_scan` entry to `markers` next to `integration` (REQ-001) | REQ-001 / AC-001 | `[tool.pytest.ini_options]` holds `markers = ["integration: ..."]`, `addopts = "-v --tb=short"`, no `--strict-markers`; `rg repo_scan` finds no existing use (checked in Step 3) | N/A: configuration; validated by `uv run pytest --markers` and the collection checks | Verified |
| tests/tools/test_check_compat_shims.py | Tests of the compat-shims checker | Mark `TestProductionCategoryZero::test_real_repo_manifest_passes`, which runs the checker over the real repository in a subprocess (REQ-002) | REQ-002 / AC-002 | The test runs `tools/check_compat_shims.py --check-removed-names --check-doc-symbols` with `cwd=ROOT_DIR`; 100 s in the 2026-11-13 profile, 52 s on 2026-11-12; the file imports `pytest` (checked in Step 3) | tests/tools/test_check_compat_shims.py | Verified |
| tests/tools/test_no_compatibility_policy_gate.py | Tests of the no-compatibility policy gate | Mark `TestNoLiveReferences` (one test, an in-process scan of the live tree) and `TestCheckerBlocking::test_repo_root_run_passes` (a subprocess run of the checker at repo root); leave the other tests of `TestCheckerBlocking` unmarked (REQ-002) | REQ-002 / AC-002 | `test_zero_findings_across_live_tree` calls `_scan_flags()`; `test_repo_root_run_passes` runs `python -m tools.check_compat_shims` with `cwd=REPO_ROOT`; 103 s and 90 s in the profile; `TestCheckerBlocking::test_rotation_reject_then_recover` is 0.6 s (checked in Step 3) | tests/tools/test_no_compatibility_policy_gate.py | Verified |
| tests/tools/test_check_docs_quality.py | Tests of the docs-quality checker | Mark `TestRegressionFullDocsTree` (two tests that run the checker over the full `docs/` tree in a subprocess) (REQ-002) | REQ-002 / AC-002 | Both tests run `python -m tools.check_docs_quality` with `cwd=_ROOT_DIR`; 30 s and 27 s in the profile; the class holds only these two tests (checked in Step 3) | tests/tools/test_check_docs_quality.py | Verified |
| skills/python-test-and-fix/workflow.md | Procedure of the test-and-fix skill; Step 10 owns impact-based execution | State the operational rule once in Step 10 and add `and not repo_scan` to its `--testmon-forceselect` command only (REQ-004) | REQ-004 / AC-004 | Step 10 holds the `--testmon-noselect` and `--testmon-forceselect` commands with `-m "not integration and not production_paths_allowed"`; the full run, Step 11's coverage run, the flaky-investigation commands, and the `--timeout` commands also carry the expression and stay as they are (checked in Step 3) | N/A: skill text; validated by `tools/check_skills_references.py` and `tools/check_skills_heading_cycles.py` | Verified |
| skills/python-test-and-fix/SKILL.md | Skill summary of the test-and-fix skill | Make the Step 10 row refer to the rule in `workflow.md` (REQ-005) | REQ-005 / AC-004 | Row 10 of the phase table says to run `pytest --testmon-forceselect` together with `-m`; the isolation bullet holds the production-safety default expression and stays as it is (checked in Step 3) | N/A: skill text; validated by the two skill checkers | Verified |
| skills/code-implementation/workflow.md | Procedure of the code-implementation skill | Add `and not repo_scan` to the Step 4 `--testmon-forceselect` command that determines the targeted scope (REQ-005) | REQ-005 / AC-004 | Step 4 determines the targeted scope through `uv run pytest --testmon-forceselect -m "not integration and not production_paths_allowed" tests/`; its full-suite coverage command `coverage run -m pytest tests/` carries no `-m` and stays as it is (checked in Step 3) | N/A: skill text; validated by the two skill checkers | Verified |

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

## Reference Files
Files that must be read to implement the targets above, but MUST NOT be modified. Same
one-file-per-row discipline as `Implementation Target Files` above — no directories,
glob patterns, components, file groups, or vague phrases.

| File Path | Why It Must Be Read | Related Target File or Requirement |
|---|---|---|
| tests/conftest.py | Registers `production_paths_allowed` in `pytest_configure`; shows why the new marker goes in `pyproject.toml` instead | pyproject.toml / REQ-001 |
| .github/workflows/ci.yml | Its test commands carry no `-m` filter and must keep none | pyproject.toml / REQ-006 |
| .pre-commit-config.yaml | The hooks `check-compat-shims` and `check-docs-quality` run the same checkers; they carry the path filter that makes the tests only partly redundant | tests/tools/test_check_compat_shims.py / REQ-003 |
| skills/python-implementation/workflow.md | Cites the expression as a production-safety default and for its wider-suite run; classified as unchanged | skills/python-test-and-fix/workflow.md / REQ-004 |
| skills/python-debug-root-cause/workflow.md | Cites the expression as a production-safety default, a bisect command, and a wider-suite run; classified as unchanged | skills/python-test-and-fix/workflow.md / REQ-004 |
| skills/python-lint-typecheck/workflow.md | Cites the expression in its coverage run (a final run); classified as unchanged | skills/python-test-and-fix/workflow.md / REQ-004 |

## Acceptance Criteria
- `AC-001` (REQ-001): `uv run pytest --markers` lists `repo_scan` with its description, and no unregistered-marker warning appears for it.
- `AC-002` (REQ-002, REQ-003): `uv run pytest --collect-only -q -m repo_scan` lists exactly the five intended tests (the two docs-quality tests, the two gate tests, and the compat-shims test); `uv run pytest --collect-only -q -m "not integration and not production_paths_allowed and not repo_scan"` deselects them; `uv run pytest --collect-only -q` with no `-m` still collects them; no assertion changed.
- `AC-003` (REQ-003): The change record states that no other test in `tests/tools` exceeds about 10 s in a whole-tree scan, naming the unmarked scans below the threshold.
- `AC-004` (REQ-004, REQ-005): The `--testmon-forceselect` commands in `skills/python-test-and-fix/workflow.md` Step 10 and `skills/code-implementation/workflow.md` Step 4 include `and not repo_scan`; Step 10 states the rule once; `skills/python-test-and-fix/SKILL.md` refers to it; the safety-default sentences, per-test-path commands, `--testmon-noselect` command, final full run, and coverage runs are unchanged; `uv run python tools/check_skills_references.py` and `uv run python tools/check_skills_heading_cycles.py` pass.
- `AC-005` (REQ-006): The CI test commands still have no `-m` filter; the call time of the iteration command with and without the exclusion is recorded in the change record, measured the same way on the same machine, and is lower by about the call time of the five tests (the 158 s of the Issue is an estimate).
- `AC-006` (REQ-002): `uv run pytest tests/tools/test_check_compat_shims.py tests/tools/test_no_compatibility_policy_gate.py tests/tools/test_check_docs_quality.py` still passes when run explicitly.

## Tests
- Collection checks (REQ-001, REQ-002, REQ-003): the three `--collect-only` commands of AC-002 and `uv run pytest --markers`.
- Explicit run of the three touched test files (REQ-002): all tests pass with the marker present.
- Before and after timing of the iteration command (REQ-006): `uv run pytest -n auto -q -p no:randomly -m "not integration and not production_paths_allowed" --durations=25 -o addopts=""` against the same command with `and not repo_scan`.
- No new test is added: the change is selection, not behavior.

## Documentation Impact
N/A: no `docs/` change. The operational rule is stated in the skill files named in REQ-004 and REQ-005 (intent and boundary only, no implementation detail).

## Assumptions
- The marker name `repo_scan` is the Issue's working name; `rg repo_scan` finds no existing use, so it does not collide. Falsifier: a use appears before the change lands; then rename in this Plan.
- Registering the marker in `pyproject.toml` (like `integration`) rather than in `tests/conftest.py` (like `production_paths_allowed`) avoids touching the conftest and the `check_conftest_integrity` hook; the conftest registration exists because that marker belongs to the isolation guard defined there.
- Only the iteration-selection commands exclude the marker. The final full run (`skills/python-test-and-fix/workflow.md` Step 10 full run and Step 11, `skills/code-implementation/workflow.md` Step 4 coverage run), pre-commit, and CI keep running the marked tests; this is the Issue's "the tests keep running in the full suite and in CI" read together with its "inner development loop". Falsifier: the owner wants the final run to exclude them too (UNK-02).
- The 10 s threshold for marking is a judgment from the 2026-11-13 profile, where the next-slowest repository scan is 3.5 s.
- The three known failures in `tests/mcp_servers` (see `issues/20261112-183922_testspeed004_adopt-parallel-test-execution.md`) are unrelated to this change and are recorded as pre-existing when a full run is made.
- Overlap judged compatible (Step 8b): `plans/20261112-122408_rmcompat008_compat-checker-patterns.md` also targets `tests/tools/test_check_compat_shims.py`; it adds pattern, scope, and marker-set tests and moves three fixtures, while this Plan adds one `repo_scan` decorator to `TestProductionCategoryZero::test_real_repo_manifest_passes`. The regions do not overlap, and the scanned checker changes only in how it detects leftovers, so the marked test keeps its meaning.
- A Plan overlap exists with the Plans of `issues/20261112-183922_testspeed004_adopt-parallel-test-execution.md` and `issues/20261112-184029_testspeed006_docs-only-step4-exemption.md` on `pyproject.toml`, `skills/code-implementation/workflow.md`, and `skills/python-test-and-fix/workflow.md`; the edits are to different keys and lines, and this Plan lands first.

## Unknowns
| ID | Unknown Description | Evidence Missing | Resolution Path | Blocking? (True/False) |
|---|---|---|---|---|
| UNK-01 | Whether a test outside `tests/tools` is a comparable whole-tree scan above the threshold | Only `tests/tools` was profiled in this cycle; the 2026-11-12 top-25 listing showed only the five | In Phase 3, take a duration profile of the full non-integration run; if another test is clearly a repo-wide scan above the threshold, list it as an open question for a follow-up Issue instead of marking it silently | False |
| UNK-02 | Whether the owner wants the final full run to exclude the marker as well | The Issue says the tests keep running in the full suite, but its acceptance criterion measures the iteration command | Default is to keep them in the final run; the owner may decide otherwise in a follow-up Issue; no change here | False |
| UNK-03 | The before and after call time of the iteration command | The 158 s figure is from 8 workers on 2026-11-12; a fresh baseline with the same command is needed | Measure both commands in Phase 3 on the same machine and record them | False |

## Affected areas
| File | Change | Blast Radius | Churn (30d) | Bus Factor | deploy.sh Impact |
|---|---|---|---|---|---|
| pyproject.toml | Modify | Medium (pytest configuration for every test run; additive entry) | 8 | N/A | not applicable (rsynced) |
| tests/tools/test_check_compat_shims.py | Modify | Low | 9 | N/A | not applicable (rsynced) |
| tests/tools/test_no_compatibility_policy_gate.py | Modify | Low | 2 | N/A | not applicable (rsynced) |
| tests/tools/test_check_docs_quality.py | Modify | Low | 2 | N/A | not applicable (rsynced) |
| skills/python-test-and-fix/workflow.md | Modify | Medium (read by several skills and by every test cycle) | 8 | N/A | not applicable (rsynced) |
| skills/python-test-and-fix/SKILL.md | Modify | Low | 8 | N/A | not applicable (rsynced) |
| skills/code-implementation/workflow.md | Modify | Medium (read by every implementation cycle) | 15 | N/A | not applicable (rsynced) |

## Design
- Path B because seven files are targets. Architecture analysis: tests, configuration, and skill text only; no import or layer change, so `lint-imports` is unaffected. Dependency graphing: the `-m "not integration and not production_paths_allowed"` expression appears in six skill files; this Plan changes the iteration commands in two and the summary row of a third, and leaves the rest (see the classification below). Historical analysis: the 30-day commit counts are in `Affected areas`; `skills/code-implementation/workflow.md` is the busiest target, so the edit there is one command. Operational inspection: not applicable; no MCP server, port, or database is touched.
- Validation quality baseline: `N/A: no Python target` under `scripts/` or `tools/`.
- Classification of the expression's occurrences: Role 1, the production-safety default (the "Default to `-m ...`" sentences in `skills/python-test-and-fix/SKILL.md`, `skills/python-implementation/workflow.md`, `skills/python-debug-root-cause/workflow.md`): unchanged, because it selects what is safe to run, not what is fast. Role 2, selection: the `--testmon-forceselect` commands in `skills/python-test-and-fix/workflow.md` Step 10 and `skills/code-implementation/workflow.md` Step 4 are iteration commands and gain the exclusion; the per-test-path flaky-investigation and bisect commands must keep selecting the test under investigation and stay as they are; the full run, `--testmon-noselect`, and the coverage runs are final runs and stay as they are.
- Marker scope: class level where the class holds only scanning tests (`TestNoLiveReferences`, `TestRegressionFullDocsTree`); method level otherwise, so the 0.6 s tests of `TestCheckerBlocking` still run in iteration.
- Consumer scan: the marker name is a new name, not a persisted schema, public API, or shared constant, so `tools/scan_change_consumers.py` is not needed; the search for `repo_scan` found no existing consumer.
- Rejected: registering the marker in `tests/conftest.py` (touches the conftest integrity gate for no gain); excluding the marker in the final run (removes pre-merge coverage that only the path-filtered hook and CI would then provide).
- Sequencing: `issues/20261112-183922_testspeed004_adopt-parallel-test-execution.md` edits `addopts` in the same `pyproject.toml` table and the Step 4 command lines; `issues/20261112-184029_testspeed006_docs-only-step4-exemption.md` adds a case to Step 4 and may name this marker. Implement this Plan first.

## Implementation steps
Each step cites the rows of `Implementation Target Files` above.

1. **Phase 1: Register and apply the marker**
   - [ ] Add the `repo_scan` entry to `markers` in `pyproject.toml` (REQ-001; pyproject.toml)
   - [ ] Mark the five tests at the scopes in REQ-002 without changing assertions (REQ-002; tests/tools/test_check_compat_shims.py, tests/tools/test_no_compatibility_policy_gate.py, tests/tools/test_check_docs_quality.py)
   - [ ] Run the collection checks of AC-002 and the explicit run of AC-006 (REQ-002, REQ-003; the three test files and pyproject.toml)
2. **Phase 2: Skill text**
   - [ ] State the rule once in Step 10 and add `and not repo_scan` to its `--testmon-forceselect` command (REQ-004; skills/python-test-and-fix/workflow.md)
   - [ ] Make the Step 10 row refer to that rule (REQ-005; skills/python-test-and-fix/SKILL.md)
   - [ ] Add `and not repo_scan` to the Step 4 `--testmon-forceselect` command (REQ-005; skills/code-implementation/workflow.md)
3. **Phase 3: Verification and change record**
   - [ ] Run the two skill checkers, ruff and mypy on the touched test files, and `tools/run_validation_gates.py` (REQ-004, REQ-005; the three skill files and three test files)
   - [ ] Measure the iteration command before and after, take the duration profile for UNK-01, confirm the CI commands still have no `-m`, and write the numbers and the 10 s threshold decision in the commit message (REQ-003, REQ-006; pyproject.toml)
   - [ ] No deploy step: no file under `scripts/` or `config/` changes

### Release units
N/A: no release unit

## Validation plan
| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| pyproject.toml | Collection | `uv run pytest --markers`, `uv run pytest --collect-only -q -m repo_scan` | `repo_scan` listed; exactly the five intended tests selected |
| pyproject.toml | Collection | `uv run pytest --collect-only -q -m "not integration and not production_paths_allowed and not repo_scan"` and `uv run pytest --collect-only -q` | The five tests deselected in the first, collected in the second |
| tests/tools/test_check_compat_shims.py, tests/tools/test_no_compatibility_policy_gate.py, tests/tools/test_check_docs_quality.py | Unit and subprocess | `uv run pytest tests/tools/test_check_compat_shims.py tests/tools/test_no_compatibility_policy_gate.py tests/tools/test_check_docs_quality.py` | All pass with the marker present |
| The same three files | Static | `uv run ruff format <files>`, `uv run ruff check <files>`, `uv run mypy --no-namespace-packages <files>` | Clean |
| Three skill files | Static | `uv run python tools/check_skills_references.py`, `uv run python tools/check_skills_heading_cycles.py` | Exit 0 |
| Iteration command | Timing | `uv run pytest -n auto -q -p no:randomly -m "not integration and not production_paths_allowed" --durations=25 -o addopts=""` and the same with `and not repo_scan` | Call time lower by about the five tests' call time; both recorded |
| .github/workflows/ci.yml | Read | `rg -n "pytest" .github/workflows/ci.yml` | No `-m` in the test commands |
| Diff | Gate discovery | `uv run python tools/run_validation_gates.py` | Summary without `Fail` |

## Risks
- **Risk**: The marked tests stop running anywhere and a regression in the scanned trees goes unseen → **Mitigation**: only iteration commands exclude them; the final full run, the coverage run, pre-commit (path-filtered), and CI (no `-m`, plus `pre-commit run --all-files` in `lint`) still run them; AC-005 checks the CI commands.
- **Risk**: Over-marking hides real failures from iteration → **Mitigation**: mark only the five tests above the 10 s threshold, at the narrowest scope; name the unmarked scans in the change record.
- **Risk**: The exclusion is added to the wrong occurrences of the expression (a safety default or a per-test-path command), so a developer debugging a marked test finds it deselected → **Mitigation**: the Design classifies each occurrence; the Reference Files rows record the unchanged ones; the skill checkers and a read of the diff confirm only the listed commands changed.
- **Risk**: `--testmon-forceselect` plus the exclusion skips a marked test exactly when its checker changed → **Mitigation**: the final full run of the same cycle runs it; Step 10's statement says the marked tests run in the final run.
- **Risk**: The skill edits create a heading-level reference cycle → **Mitigation**: refer from `SKILL.md` and `code-implementation/workflow.md` to the one statement in `python-test-and-fix/workflow.md` Step 10 and run `check_skills_heading_cycles.py`.
- **Risk**: Overlapping edits with the Plans for `testspeed004` and `testspeed006` conflict → **Mitigation**: this Plan lands first and changes one command line in each shared section; the overlap checker and a re-read before those Plans are implemented.

## Execution Status

Table structure, status/type vocabulary, and general guidance: see
`templates/execution-status.md`. Default rows for a freshly generated Plan (replace
with the Plan's actual steps once Implementation steps are broken down):

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Phase 1: register and apply the marker (pyproject.toml, tests/tools/test_check_compat_shims.py, tests/tools/test_no_compatibility_policy_gate.py, tests/tools/test_check_docs_quality.py) | Completed | — | 20261113-133722 |  |
| 2 | Phase 2: skill text (skills/python-test-and-fix/workflow.md, skills/python-test-and-fix/SKILL.md, skills/code-implementation/workflow.md) | Completed | — | 20261113-133722 |  |
| 3 | Phase 3: verification and change record (pyproject.toml and all touched files) | Pending | — | — |  |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| — | — | — | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| implementations/20261113-102218_01_pyproject.toml.md | 1 | Procedure | Completed | — | — |
| implementations/20261113-102218_02_tests_tools_test_check_compat_shims.py.md | 1 | Procedure | Completed | — | — |
| implementations/20261113-102218_03_tests_tools_test_no_compatibility_policy_gate.py.md | 1 | Procedure | Completed | — | — |
| implementations/20261113-102218_04_tests_tools_test_check_docs_quality.py.md | 1 | Procedure | Completed | — | — |
| implementations/20261113-102218_05_skills_python-test-and-fix_workflow.md.md | 2 | Procedure | Completed | — | — |
| implementations/20261113-102218_06_skills_python-test-and-fix_SKILL.md.md | 2 | Procedure | Completed | — | — |
| implementations/20261113-102218_07_skills_code-implementation_workflow.md.md | 2 | Procedure | Completed | — | — |

## Traceability
- **Workflow phase**: issue-to-plan
- **Source issue**: issues/20261112-183738_testspeed001_mark-repo-scan-tests.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: this document is the generated plan
- **Source implementation procedure**: N/A: not applicable in this phase
- **Generated at**: 20261113-093307
- **Related target files**: pyproject.toml, tests/tools/test_check_compat_shims.py, tests/tools/test_no_compatibility_policy_gate.py, tests/tools/test_check_docs_quality.py, skills/python-test-and-fix/workflow.md, skills/python-test-and-fix/SKILL.md, skills/code-implementation/workflow.md

### Requirement Traceability
| Requirement ID | Source Issue section or evidence | Target file | Implementation step | Acceptance criterion | Test or validation item | Status |
|---|---|---|---|---|---|---|
| REQ-001 | Issue Required Changes (register the marker); `markers` list (checked in Step 3) | pyproject.toml | Phase 1 | AC-001 | Validation plan: first collection row | Confirmed by repository evidence |
| REQ-002 | Issue Required Changes (apply to the five tests); duration profile (checked in Step 2) | tests/tools/test_check_compat_shims.py | Phase 1 | AC-002, AC-006 | Validation plan: explicit run row | Confirmed by repository evidence |
| REQ-002 | Issue Required Changes (apply to the five tests); duration profile (checked in Step 2) | tests/tools/test_no_compatibility_policy_gate.py | Phase 1 | AC-002, AC-006 | Validation plan: explicit run row | Confirmed by repository evidence |
| REQ-002 | Issue Required Changes (apply to the five tests); duration profile (checked in Step 2) | tests/tools/test_check_docs_quality.py | Phase 1 | AC-002, AC-006 | Validation plan: explicit run row | Confirmed by repository evidence |
| REQ-003 | Issue Required Changes (`--collect-only` confirmation); Acceptance Criteria | pyproject.toml | Phase 1, Phase 3 | AC-002, AC-003 | Validation plan: collection rows | Explicit in issue |
| REQ-004 | Issue Required Changes (update the `-m` expression); expression classification (checked in Step 3) | skills/python-test-and-fix/workflow.md | Phase 2 | AC-004 | Validation plan: skill checker row | Derived from confirmed evidence |
| REQ-005 | Issue Target Files (`skills/code-implementation/workflow.md`, `skills/python-test-and-fix/SKILL.md`) | skills/python-test-and-fix/SKILL.md | Phase 2 | AC-004 | Validation plan: skill checker row | Derived from confirmed evidence |
| REQ-005 | Issue Target Files (`skills/code-implementation/workflow.md`, `skills/python-test-and-fix/SKILL.md`) | skills/code-implementation/workflow.md | Phase 2 | AC-004 | Validation plan: skill checker row | Derived from confirmed evidence |
| REQ-006 | Issue Constraints (CI unchanged) and Required Changes (record before and after) | pyproject.toml | Phase 3 | AC-005 | Validation plan: timing and CI read rows | Explicit in issue |

<!-- tools/generate_workitem.py implementation-procedure-pass timestamp: 20261113-102218 -->