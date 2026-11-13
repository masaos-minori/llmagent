## Goal
- Make the CI `test` job run the whole pytest suite once per job run, as one coverage-collecting run, while a failing test still fails the job, the 90% diff-cover gate still runs after it, and the failure output stays as informative as today.

## Priority
Medium

## Scope
- **In-Scope**: replace the two test-running steps of the `test` job in `.github/workflows/ci.yml` with one `Run tests` step that runs `uv run coverage run -m pytest -v tests/`, followed by the unchanged `Coverage report` step (`coverage xml`, `diff-cover`); update the one sentence in `skills/test-audit/workflow.md` that quotes the two CI test commands; record the evidence that failure and gate behavior are kept.
- **Out-of-Scope**: `-n auto` or other parallel execution in CI; the CI trigger set, runners, caching, other jobs, and other steps; the `diff-cover` threshold and compare branch; any `-m` filter; `tox.ini`; test-level speedups; the cited-ADR test script of the `lint` job.
- **Dependencies**: `issues/20261112-183922_testspeed004_adopt-parallel-test-execution.md` is related and not blocking: if parallel workers are adopted there, a follow-up must add a coverage parallel-mode setting to CI. No other Issue or Plan blocks this one.

## Background
`.github/workflows/ci.yml` runs on every push to `master` and every pull request to `master`. Its `test` job has a step `Run tests` (`uv run pytest -v`) and a step `Coverage report` that runs `uv run coverage run -m pytest tests/`, `uv run coverage xml`, and `uv run diff-cover coverage.xml --compare-branch=origin/master --fail-under=90`. Both pytest invocations select the whole `tests/` tree (`testpaths = ["tests"]`). `git log -S` shows both steps were added together in the initial CI commit `f54755d56` (2026-07-11), and no record gives a reason for running the suite twice. The local sequence in `skills/code-implementation/workflow.md` Step 4 and `rules/toolchain.md` section 7 already feeds the coverage gate from one `coverage run -m pytest tests/` run.

## Problem
Each CI run pays the full test cost twice: the second run executes the same tests and only adds coverage data. The two runs also differ in verbosity: `addopts` holds `-v`, so the first run runs at verbosity 2 (unabridged assertion diffs) and the second at verbosity 1. In GitHub Actions a failing step stops the later steps, so today the second run only executes after the first run passed; a failing suite is never run twice.

## Reason for Change
Test time is the largest part of the development loop and CI feedback is part of that loop. Removing the duplicate run is a small workflow-file change that does not alter what is checked, and it leaves one place to add `-n auto` later.

## Implementation Intent
Keep one test step that runs the suite under `coverage run`, with `-v` kept so the failure output stays at verbosity 2, then the existing `coverage xml` and `diff-cover` steps unchanged. Keep the step names `Run tests` and `Coverage report`. Do not change the selection, the gate threshold, or the compare branch. Keep the one stale sentence in `skills/test-audit/workflow.md` true.

## Requirements
- `REQ-001`: The `test` job of `.github/workflows/ci.yml` invokes pytest on the `tests/` tree exactly once per job run, through `uv run coverage run -m pytest -v tests/` in the step named `Run tests`.
- `REQ-002`: The `Coverage report` step keeps `uv run coverage xml` and `uv run diff-cover coverage.xml --compare-branch=origin/master --fail-under=90` unchanged and runs after the test step; no `-m` filter is added, no parallel workers are added, and no other job or step is touched.
- `REQ-003`: Evidence shows that a failing test still fails the step, that a run with no selected test still fails, and that the gate commands still run and enforce 90%.
- `REQ-004`: The sentence in `skills/test-audit/workflow.md` that quotes the CI test commands states the single merged CI command.
- `REQ-005`: The CI duration of the test portion is recorded before and after the change.

## Implementation Target Files
**Freeze status**: Frozen

This table is the canonical, frozen source of implementation scope for this Plan. Once
`Frozen`, `Implementation steps`, `Acceptance criteria`, and every downstream
`plan-to-implementation-procedure` document MUST reference file paths only from this
table — no other file may be treated as a modification target.

| File Path | Change Responsibility | Reason for Modification | Related Requirement / Acceptance Criterion | Repository Evidence | Related Tests | Validation Status |
|---|---|---|---|---|---|---|
| .github/workflows/ci.yml | CI workflow; the `test` job runs the suite | Merge the `Run tests` (`uv run pytest -v`) step and the pytest call of the `Coverage report` step into one `coverage run` step (REQ-001, REQ-002) | REQ-001, REQ-002 / AC-001, AC-002 | The `test` job holds `Run tests` with `uv run pytest -v` and `Coverage report` with `coverage run -m pytest tests/`, `coverage xml`, and `diff-cover ... --compare-branch=origin/master --fail-under=90`; no `-m` filter appears; the two steps came from one commit `f54755d56` (checked in Step 2 and Step 3) | N/A: no pytest test reads this workflow; validated by `uv run yamllint` and the local combined command in the Validation plan | Verified |
| skills/test-audit/workflow.md | Procedure of the test-audit skill | The sentence "Run pytest the way CI does (`.github/workflows/ci.yml`: `uv run pytest -v`, and `uv run coverage run -m pytest tests/` for coverage)" names two CI commands that no longer exist after the merge (REQ-004) | REQ-004 / AC-004 | `skills/test-audit/workflow.md` quotes both commands in its test-execution section (checked in Step 3) | N/A: skill text; validated by `tools/check_skills_references.py` and `tools/check_skills_heading_cycles.py` | Verified |

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
| tox.ini | The `tests` environment runs one `uv run pytest {posargs}` with no coverage step, so it has no duplicate run and needs no change | .github/workflows/ci.yml / REQ-001 |
| rules/toolchain.md | Section 7 holds the local coverage sequence that CI will now match; it does not describe the CI steps and stays unchanged | .github/workflows/ci.yml / REQ-002 |
| pyproject.toml | `addopts` holds `-v` (verbosity) and `[tool.coverage.run]` has no `parallel` or `concurrency` setting, which is correct for a serial run | .github/workflows/ci.yml / REQ-001 |
| tools/check_ci_results.py | Reads `FAILED <nodeid>` lines of a failed-run log and does not depend on step names; confirms the merge does not break it | .github/workflows/ci.yml / REQ-001 |
| skills/code-implementation/workflow.md | Step 4 already runs the suite once under `coverage run`; the local pattern CI will match | .github/workflows/ci.yml / REQ-002 |

## Acceptance Criteria
- `AC-001` (REQ-001): `.github/workflows/ci.yml` invokes pytest on the `tests/` tree exactly once in the `test` job, in the step named `Run tests` with `uv run coverage run -m pytest -v tests/`.
- `AC-002` (REQ-002): The `Coverage report` step still runs `coverage xml` and `diff-cover` with `--compare-branch=origin/master --fail-under=90` after the test step; the diff of `ci.yml` touches no other job or step and adds no `-m` filter or `-n` option.
- `AC-003` (REQ-003): `coverage run -m pytest` is shown to exit non-zero for a failing test and for an empty selection (exit 1 and exit 5, measured on a scratch test in Step 2), and the combined local command's pass or fail result matches a plain `uv run pytest` on the same tree.
- `AC-004` (REQ-004): The `skills/test-audit/workflow.md` sentence names the single CI command, and `tools/check_skills_references.py` and `tools/check_skills_heading_cycles.py` pass.
- `AC-005` (REQ-005): The test-portion duration of the CI job before and after the change is recorded in the change record, or marked `Not available` with the reason when CI access is missing.

## Tests
- No pytest test is added or changed (REQ-001, REQ-002): the change is workflow and skill text.
- Exit-status check (REQ-003): `uv run coverage run -m pytest` on a scratch failing test and on an empty selection, run in Step 2 of this cycle; repeated in Phase 3 against the real tree.
- Combined local command (REQ-003): `uv run coverage run -m pytest -v tests/ && uv run coverage xml && uv run diff-cover coverage.xml --compare-branch=master --fail-under=90`, compared with a plain `uv run pytest` result.

## Documentation Impact
N/A: no `docs/` change. `rules/toolchain.md` section 7 shows the local sequence and does not describe the CI steps. The one skill sentence that quotes the CI commands is covered by REQ-004.

## Assumptions
- Keeping `-v` in the merged command preserves today's failure output (verbosity 2); falsifier: the first CI run after the change shows less detail than before.
- Running the whole suite under `coverage run` passes where the second CI run passed; the second run already ran under coverage on green builds. Falsifier: a test that fails only under coverage tracing (UNK-03).
- The step names `Run tests` and `Coverage report` stay, so nothing that refers to them breaks; `tools/check_ci_results.py` does not depend on them.
- The 2026-11-13 local state has three known failures in `tests/mcp_servers` (see `issues/20261112-183922_testspeed004_adopt-parallel-test-execution.md`); the local combined run is compared with a plain run on the same tree, so both show the same failures.

## Unknowns
| ID | Unknown Description | Evidence Missing | Resolution Path | Blocking? (True/False) |
|---|---|---|---|---|
| UNK-01 | CI wall time of the test portion before and after | `gh` is not authenticated on this machine, so run durations cannot be read | The repository owner reads the Actions step timings before the change and after the first post-merge run and records them in the change record (AC-005) | False |
| UNK-02 | Whether the first `pytest -v` run was kept intentionally | No record in the files read; `git log -S` shows both steps came in one commit | None needed: no reason was found; if one surfaces, stop and report it instead of removing the run (Issue AI Implementation Instruction) | False |
| UNK-03 | Whether any test behaves differently when it is the first run under coverage tracing | A failing suite never reaches the coverage step today, so only green runs were observed under coverage | The first CI run after the change; a failure that appears only there is filed as its own Issue | False |
| UNK-04 | Open dependency named by the Issue: `issues/20261112-183922_testspeed004_adopt-parallel-test-execution.md` (Plan `plans/20261113-093804_testspeed004_adopt-parallel-test-execution.md`, rows not `Completed`) | The Plan is `Pending` | Not needed first: this Plan keeps CI serial; if parallel workers reach CI later, a follow-up must add a coverage parallel-mode setting (that Plan measured 0% worker coverage under `-n`) | False |

## Affected areas
| File | Change | Blast Radius | Churn (30d) | Bus Factor | deploy.sh Impact |
|---|---|---|---|---|---|
| .github/workflows/ci.yml | Modify | Medium (gates every push and pull request to master; limited to the `test` job) | N/A | N/A | not applicable (rsynced) |
| skills/test-audit/workflow.md | Modify | Low | N/A | N/A | not applicable (rsynced) |

## Design
- Path A: two target files, no public or runtime-facing interface, no schema. Direct verification: `ci.yml` and the skill sentence were read; references to CI step names and commands were searched (`rg` for `ci.yml`, `Run tests`, `Coverage report`), with these results: `tools/check_ci_results.py` is step-name independent; `tests/tools/test_check_ci_results.py` uses `Run tests` only as fixture text; `skills/test-audit/workflow.md` quotes the two commands (a target row); `skills/python-lint-typecheck/` refers to the `lint` job only. Zero matches in a pattern search is not proof of no other reader.
- Validation quality baseline: `N/A: no Python target`.
- Single step rather than two: `coverage run` wraps pytest and returns pytest's exit status (measured: failing test gives 1, empty selection gives 5), so the job still fails on a failing test, and `coverage xml` and `diff-cover` only read the data file.
- Verbosity: the first run is at verbosity 2 because the CLI `-v` adds to the `-v` of `addopts`; the second is at 1. The merged command keeps `-v` so the unabridged assertion diffs stay in the failure log.
- Failure semantics: a failing step stops the later steps of a GitHub Actions job, so merging does not change what happens on red (the suite never ran twice there); on green it removes one full run.
- Not changed: `tox.ini` (one run, no coverage step), `rules/toolchain.md` section 7 (local sequence), `pyproject.toml` (no parallel coverage setting is needed for a serial run).
- Deploy: no step; `.github/workflows/ci.yml` and a skill file are not under `scripts/` or `config/`.

## Implementation steps
Each step cites the rows of `Implementation Target Files` above.

1. **Phase 1: Merge the CI test steps**
   - [ ] Replace the `Run tests` command with `uv run coverage run -m pytest -v tests/` and remove the pytest call from the `Coverage report` step, keeping `coverage xml` and `diff-cover` unchanged (REQ-001, REQ-002; .github/workflows/ci.yml)
2. **Phase 2: Keep the skill sentence true**
   - [ ] Reword the CI sentence in the test-execution section so it names the single merged CI command (REQ-004; skills/test-audit/workflow.md)
3. **Phase 3: Verification**
   - [ ] Run `uv run yamllint .github/workflows/ci.yml` and review the workflow diff by reading, since `actionlint` is not installed (REQ-001, REQ-002; .github/workflows/ci.yml)
   - [ ] Run the combined local command and compare its result with a plain `uv run pytest`; run the skill checkers (REQ-003, REQ-004; .github/workflows/ci.yml, skills/test-audit/workflow.md)
   - [ ] After the change is pushed (a user decision), the owner confirms the first CI run and records the before and after durations (REQ-005; .github/workflows/ci.yml)

### Release units
N/A: no release unit

## Validation plan
| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| .github/workflows/ci.yml | Static | `uv run yamllint .github/workflows/ci.yml` (`actionlint` is not installed: `Not available`; fallback is reading the diff) | No findings |
| .github/workflows/ci.yml | Integration (local equivalent of the CI step) | `uv run coverage run -m pytest -v tests/ && uv run coverage xml && uv run diff-cover coverage.xml --compare-branch=master --fail-under=90`, then a plain `uv run pytest` | Same pass or fail result; the same failing tests, if any; `diff-cover` runs |
| .github/workflows/ci.yml | Exit status | `uv run coverage run -m pytest` on a failing scratch test and on an empty selection | Exit 1 and exit 5 |
| .github/workflows/ci.yml | Hook gates matched by the path | `uv run python tools/check_tool_descriptions_sync.py` | Exit 0 |
| skills/test-audit/workflow.md | Static | `uv run python tools/check_skills_references.py` and `uv run python tools/check_skills_heading_cycles.py` | Exit 0 |
| Diff | Gate discovery | `uv run python tools/run_validation_gates.py` | Summary without `Fail` |

## Risks
- **Risk**: The merged step prints less failure detail than the first run did → **Mitigation**: keep `-v` in the command so verbosity 2 is preserved (measured on the config parser).
- **Risk**: The merged step takes longer than the plain first run because coverage traces the suite → **Mitigation**: the saving is the removed second run; record the durations (AC-005); a net gain is expected because the plain run is removed in full.
- **Risk**: A test fails only under coverage tracing and is now the first failure seen on a red build → **Mitigation**: UNK-03; the second run already ran under coverage on every green build; file an Issue if one appears.
- **Risk**: A reader of the step names breaks → **Mitigation**: keep `Run tests` and `Coverage report`; `tools/check_ci_results.py` does not depend on them.
- **Risk**: Merging weakens the gate by accident (a changed threshold, branch, or filter) → **Mitigation**: the gate lines stay byte-identical; the diff is reviewed for this in Phase 3.
- **Risk**: A deliberately failing pull request would verify the failure path but is an outward-facing push → **Mitigation**: use the local exit-status evidence instead and do not push a failing test.

## Execution Status

Table structure, status/type vocabulary, and general guidance: see
`templates/execution-status.md`. Default rows for a freshly generated Plan (replace
with the Plan's actual steps once Implementation steps are broken down):

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Phase 1: merge the CI test steps (.github/workflows/ci.yml) | Completed | — | 20261113-122331 |  |
| 2 | Phase 2: keep the skill sentence true (skills/test-audit/workflow.md) | Completed | — | 20261113-122331 |  |
| 3 | Phase 3: verification and duration record (.github/workflows/ci.yml, skills/test-audit/workflow.md) | Pending | — | — |  |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| — | — | — | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| implementations/20261113-102111_01_.github_workflows_ci.yml.md | 1 | Procedure | Completed | — | — |
| implementations/20261113-102111_02_skills_test-audit_workflow.md.md | 2 | Procedure | Completed | — | — |

## Traceability
- **Workflow phase**: issue-to-plan
- **Source issue**: issues/20261112-183953_testspeed005_run-ci-suite-once.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: this document is the generated plan
- **Source implementation procedure**: N/A: not applicable in this phase
- **Generated at**: 20261113-092617
- **Related target files**: .github/workflows/ci.yml, skills/test-audit/workflow.md

### Requirement Traceability
| Requirement ID | Source Issue section or evidence | Target file | Implementation step | Acceptance criterion | Test or validation item | Status |
|---|---|---|---|---|---|---|
| REQ-001 | Issue Required Changes (replace the two steps); `ci.yml` steps (checked in Step 2) | .github/workflows/ci.yml | Phase 1 | AC-001 | Validation plan: static and integration rows | Confirmed by repository evidence |
| REQ-002 | Issue Constraints (gate, compare branch, no `-m`, no parallel workers) | .github/workflows/ci.yml | Phase 1 | AC-002 | Validation plan: static row and diff review | Explicit in issue |
| REQ-003 | Issue Required Changes (confirm failure and gate); exit-status measurement (checked in Step 2) | .github/workflows/ci.yml | Phase 3 | AC-003 | Validation plan: integration and exit-status rows | Confirmed by repository evidence |
| REQ-004 | `skills/test-audit/workflow.md` sentence naming the two CI commands (checked in Step 3) | skills/test-audit/workflow.md | Phase 2 | AC-004 | Validation plan: skill checker row | Derived from confirmed evidence |
| REQ-005 | Issue Acceptance Criteria (record CI duration before and after) | .github/workflows/ci.yml | Phase 3 | AC-005 | Phase 3 owner step (UNK-01) | Explicit in issue |

<!-- tools/generate_workitem.py implementation-procedure-pass timestamp: 20261113-102111 -->