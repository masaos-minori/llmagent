## Goal
- Add a read-only helper, `tools/check_ci_results.py`, that reads the latest CI runs on `master` with the existing `gh` authentication and prints a short report: the red-run summary and every test that failed in two or more of the last N runs, pointing the reader to `python-test-and-fix`; the check never changes code, re-runs anything, or sends data to an external service.

## Priority
Low

## Scope
- **In-Scope**:
  - The helper tool and its unit tests (grouping logic over fixed sample data).
  - The mechanism decision and its reason (recorded under Design).
  - One operational note: schedule, owner, how to disable, and the rule that follow-up is manual.
  - The `tools/TOOL_DESCRIPTIONS.md` row required for a new tool.
- **Out-of-Scope**:
  - Creating or enabling a schedule: it needs the user's explicit confirmation (Issue `AI Implementation Instruction`) and is a hand-off step, not a file change.
  - Fixing any flaky or failing test, including the failures found in Step 2 (Unknown `UNK-01`).
  - Changing `.github/workflows/ci.yml`, pytest plugins, or retry settings.
  - Automatically filing issues or opening pull requests from CI failures.
  - Lazy loading of the Step 0 mandatory-load set (no action; user decision 2026-10-24, from the Issue).
- **Dependencies**: `N/A: none` — the Issue's sibling check found no open issue covering CI monitoring; re-checked this cycle with `rg -il "ci monitor|ci result" issues/` (no match). Loosely related to the closed flaky-test issues under `issues/done/`.

## Background
CI is `.github/workflows/ci.yml` (`lint` and `test` jobs). Flaky failures were so far found by chance after the fact (three closed issues under `issues/done/`; the clock-boundary case is fixed by commit `2e27d444a`, confirmed present).

Corrections from verification (Step 2, 2026-10-25), which supersede the Issue's Background:
- The Issue says no known flaky test is open and the project memory note ("CI green") is stale only because its flaky test was fixed. The live run history contradicts the premise that CI is currently healthy: of the last 20 `CI` runs on `master` (2026-10-24 12:19Z to 23:58Z), 19 concluded `failure` and 1 was still in progress; the last `success` is 2026-10-23T03:44Z (18 successes within the last 100 runs).
- The failures are deterministic, not flaky: the two newest completed runs (`40144039702`, `40141761820`) fail 3 and 2 tests; two of them (`tests/mcp_servers/test_require_auth_token.py` and `tests/mcp_servers/test_config_isolation_import.py`, both for `mcp_servers.shell.shell_server`) raise `RuntimeError: shell_sandbox_backend=firejail is configured but firejail is not found in PATH`. One run also fails `tests/eventbus/test_eventbus_auth.py::TestProductionRouteWiring::...[GET-/health-...]` with `assert 503 == 200`, which appears in one of the two runs only.
- This is exactly the situation the check exists for, and it shows the value is not hypothetical. It also means the Issue's "thin evidence" reservation no longer holds.
- No workflow under `.github/workflows/` has a `schedule:` trigger (10 workflows read, none matches), and `gh` is authenticated for the repository (`gh run list` and `gh run view --log-failed` both succeeded). The scheduling state of this machine was inspected: `.claude/scheduled_tasks.lock` exists, but no task definition was found under `~/.claude/` or `.claude/` (`Needs confirmation` for cloud-side routines, see `UNK-03`).

## Problem
Nothing watches CI between sessions. A red or intermittently failing run is noticed only when someone looks; in the measured window it stayed red for at least 19 consecutive runs. Failures are not grouped per test across runs, so a repeat is invisible without reading each log.

## Reason for Change
Detection is currently accidental. The measured red streak shows the cost of that. Priority stays Low because the change is a read-only reporting aid and fixes no defect itself.

## Implementation Intent
Use the existing mechanisms rather than new CI infrastructure: a standalone read-only tool in `tools/` that wraps `gh run list` and `gh run view --log-failed`, plus a user-approved recurring session task (the `loop` or `schedule` skill) that runs it and shows the output. Output is a report on stdout only. Any follow-up (issue filing, test fixing) stays a human-approved step handed to `python-test-and-fix` and `issue-creator`.

## Requirements
- `REQ-001`: Record the chosen mechanism and the reason (Required Changes, bullet 1): a local helper tool run by a user-approved recurring session task; no GitHub Actions scheduled workflow, no cloud agent.
- `REQ-002`: The tool queries the latest N runs (default 10) of one workflow (default `CI`) on one branch (default `master`), optionally restricted to runs created at or before `--before <ISO-8601 timestamp>` so an older window can be inspected, and records per run: conclusion, status, failed job names, and failed test identifiers.
- `REQ-003`: The report lists the red runs (run id, head SHA, failed jobs, failed tests) and every test identifier that failed in two or more of the examined runs, with its run count, so a repeat is visible; each reported red state ends with a pointer to `skills/python-test-and-fix/SKILL.md`.
- `REQ-004`: The tool performs no write operation: it can only invoke `gh run list` and `gh run view`, enforced by a fixed allowlist in code (a command outside it raises before anything is spawned); it stores no credential and sends no repository content to any service.
- `REQ-005`: The report is delivered on stdout only. Exit code: `0` when the latest completed run is green and no test repeats, `1` when it is red or a repeat exists, `2` when `gh` cannot read run history (the tool stops and reports, per the Issue's `AI Implementation Instruction`).
- `REQ-006`: One operational note states the schedule, owner, how to disable the recurring task, the delivery channel (stdout in the session), and that follow-up is manual.
- `REQ-007`: Unit tests with fixed sample data cover the grouping logic (single red run, repeat across runs, all green, runs without a failed-test summary, in-progress run), the log-line parsing, and the read-only allowlist; the tool passes `routing.md` "Adding a new tool" validation and has its `tools/TOOL_DESCRIPTIONS.md` row.
- `REQ-008`: Verify the tool once on live history: a known-red window (current `master`) and a known-green window (`--limit 100` reaches runs up to 2026-10-23T03:44Z).

## Implementation Target Files
**Freeze status**: Frozen

This table is the canonical, frozen source of implementation scope for this Plan. Once
`Frozen`, `Implementation steps`, `Acceptance criteria`, and every downstream
`plan-to-implementation-procedure` document MUST reference file paths only from this
table — no other file may be treated as a modification target.

| File Path | Change Responsibility | Reason for Modification | Related Requirement / Acceptance Criterion | Repository Evidence | Related Tests | Validation Status |
|---|---|---|---|---|---|---|
| `tools/check_ci_results.py` | Read-only CI result reporter (new module) | New file; its containing directory `tools/` exists. Implements the query, parsing, grouping, report, allowlist, and exit codes | `REQ-001`..`REQ-005`; AC-1, AC-2, AC-3, AC-4 | `tools/` holds `check_*.py` detectors with a docstring-led CLI and `main()` (`tools/check_plan_target_overlaps.py` read in Step 3); `gh run list --json` fields `databaseId,conclusion,status,createdAt,headSha,workflowName` and `gh run view <id> --log-failed` returned the data this tool needs (run in Step 2) (checked in Step 2) | `tests/tools/test_check_ci_results.py` | Verified |
| `tests/tools/test_check_ci_results.py` | Unit tests over fixed sample data | New file; `tests/tools/` exists (50 entries) and mirrors `tools/` (`test_check_plan_target_overlaps.py` exists) | `REQ-007`; AC-5 | Sample log shape observed in run `40144039702`: summary lines `FAILED <nodeid> - <message>` after the `short test summary info` header, behind a `<job>\t<step>\t<timestamp> ` prefix (checked in Step 2) | itself | Verified |
| `tools/TOOL_DESCRIPTIONS.md` | Add the new tool's index row and bump the module count | `check_tool_descriptions_sync.py` fails when a `tools/*.py` file is undocumented; the file states `## Index (53 modules)` (`:15`) (checked in Step 3) | `REQ-007`; AC-6 | `routing.md` "When to run which tool" row for `tools/` changes names `check_tool_descriptions_sync.py` (checked in Step 3) | `uv run python tools/check_tool_descriptions_sync.py` | Verified |
| `rules/toolchain.md` | Add the operational note as a new section | The Issue's `Documentation Impact` requires a note; `rules/toolchain.md` already documents the CI invocation rules and has no CI-monitoring section; headings read at `:3`..`:148` (checked in Step 3) | `REQ-006`; AC-7 | `rules/toolchain.md` is 8064 B and is loaded by every Python workflow, so the note is discoverable (checked in Step 3) | `check_skills_references.py`, `check_docs_quality.py` | Verified |

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
| File Path | Why It Must Be Read | Related Target File or Requirement |
|---|---|---|
| `.github/workflows/ci.yml` | Read-only: names the `lint` and `test` jobs and the `uv run pytest -v` step whose log the tool parses; no change expected | `REQ-002` |
| `tools/check_plan_target_overlaps.py` | Style reference for a report-only `tools/` script (docstring, `argparse`, `ROOT_DIR`, `main()`) | `tools/check_ci_results.py` |
| `skills/python-test-and-fix/SKILL.md` | The workflow the report points to; its name and path are quoted in the report text | `REQ-003` |
| `routing.md` | Defines "Adding a new tool" validation and "When to run which tool" | `REQ-007` |
| `pyproject.toml` | `addopts = "-v --tb=short"` fixes the log format; confirms `pytest-randomly`, `pytest-rerunfailures`, `pytest-xdist` are dev dependencies and no `--reruns` is configured | `REQ-002` |

## Acceptance Criteria
- AC-1 (`REQ-001`, `REQ-002`): `uv run python tools/check_ci_results.py --limit 10` runs against live history and prints, per examined run, conclusion and failed job names; the chosen mechanism and its reason appear in this Plan's Design and in the operational note.
- AC-2 (`REQ-003`): on the current red history it lists the failed test identifiers and flags every test that failed in two or more runs (the two firejail-dependent tests, per Background); on a window of only green runs it prints a green statement and no repeats.
- AC-3 (`REQ-004`): the only `gh` subcommands the code can spawn are `run list` and `run view`; a unit test asserts any other argument vector raises before `subprocess` is called, and reading the command list shows no write operation.
- AC-4 (`REQ-005`): exit code is `0` for a green latest completed run without repeats, `1` for red or a repeat, `2` when `gh` fails (missing binary, auth failure, non-zero exit); the report goes to stdout only.
- AC-5 (`REQ-007`): `uv run pytest tests/tools/test_check_ci_results.py -q` passes with the grouping, parsing, in-progress, and allowlist cases.
- AC-6 (`REQ-007`): `uv run python tools/check_tool_descriptions_sync.py` passes with the new row; `routing.md` "Adding a new tool" steps 1-5 pass for `tools/check_ci_results.py`.
- AC-7 (`REQ-006`): the operational note in `rules/toolchain.md` states schedule, owner, disable instruction, delivery channel, and manual follow-up.
- AC-8 (`REQ-008`): the live check is run once on the known-red window and once on a known-green window (`--limit 100`, with `--before 2026-10-23T03:44:13Z`) and both outputs are recorded in the Execution Status notes.

## Tests
- `REQ-007` (AC-5): grouping — one red run lists its tests; the same test in two of three runs is flagged with count 2; a test failing once is listed but not flagged as a repeat; an all-green window reports green.
- `REQ-007` (AC-5): parsing — a fixed log excerpt with the `<job>\t<step>\t<timestamp> ` prefix yields exactly the `FAILED <nodeid>` summary identifiers; verbose `... FAILED [  6%]` progress lines are not counted twice; a failed run with no summary line (for example a `lint` failure) is reported as red with no test identifiers.
- `REQ-004` (AC-3): allowlist — `("run", "list", ...)` and `("run", "view", ...)` pass; `("run", "rerun", ...)`, `("workflow", "run", ...)`, and `("api", ...)` raise before any process is spawned.
- `REQ-005` (AC-4): exit codes `0`, `1`, `2` via an injected fake runner (no network, no `gh`).
- `REQ-008` (AC-8): manual live runs, not part of the automated suite.

## Documentation Impact
- `rules/toolchain.md` gains one section (`REQ-006`); `tools/TOOL_DESCRIPTIONS.md` gains one row (`REQ-007`).
- No `docs/*.md` change: the check is an operational aid with no architecture or runtime contract, and no row of `docs/00_index.md` "Document References by Task" maps a `tools/` file to a chapter. `N/A: no docs/ file requires updating`.

## Assumptions
- `gh` access to `masaos-minori/llmagent` run history is available for the active account (checked in Step 2: `gh auth status` and both read commands succeeded).
- The CI log format (`addopts = "-v --tb=short"`, a `short test summary info` block with `FAILED <nodeid> - ...` lines) is stable enough to parse; a log without such lines is treated as "red, no test identifiers" rather than an error.
- Counting a test as repeating when it fails in two or more of the examined runs follows the Issue's wording ("two or more of the last N runs"); N defaults to 10 and is a CLI option, not a config key.
- A local recurring session task, not a GitHub Actions scheduled workflow or cloud agent, is the lowest-risk mechanism: it adds no CI infrastructure, needs no new credential, and its output stays in the user's session. Owner-revisable.
- Judgment on overlaps with other Frozen Plans: none expected (Step 8b records the tool result below).

## Unknowns
| ID | Unknown Description | Evidence Missing | Resolution Path | Blocking? (True/False) |
|---|---|---|---|---|
| UNK-01 | Master CI has been red for at least 19 consecutive runs because `shell_sandbox_backend=firejail` is configured but `firejail` is absent on the runner (plus a one-off eventbus `503`). Nobody has filed an issue for it. | No open issue under `issues/` mentions `firejail` (`rg -il firejail issues/*.md` returned nothing); whether the runner should install firejail or the tests should be made environment-independent is undecided | File a separate Issue through `issue-creator` (out of this Plan's scope); do not fix it here | False |
| UNK-02 | Which delivery channel is acceptable beyond stdout in the session | The user has not stated one; the Issue marks it Unknown | Plan fixes delivery to stdout only (`REQ-005`); any notification or chat channel would need explicit user confirmation under `AGENTS.md` Execution policy and would be a new Issue | False |
| UNK-03 | Whether a cloud-side scheduled routine or other recurring task already runs for this repository and would be duplicated | Only local files were inspected (`.claude/scheduled_tasks.lock` exists, no task definition found); cloud routines cannot be listed from here | At hand-off (Phase 3), list existing routines with the `schedule` skill before creating one | False |
| UNK-04 | Whether the Issue should stay open at all given thin evidence | Resolved by evidence: 19 consecutive red runs on `master` show the check would have reported the problem within one scheduled interval; the Issue's reservation is withdrawn | None needed | False |

## Affected areas
| File | Change | Blast Radius | Churn (30d) | Bus Factor | deploy.sh Impact |
|---|---|---|---|---|---|
| `tools/check_ci_results.py` | Create | Low — standalone script, imported by nothing; calls only the `gh` CLI | N/A (new) | N/A (new) | not applicable (rsynced) |
| `tests/tools/test_check_ci_results.py` | Create | Low — new test module only | N/A (new) | N/A (new) | not applicable (rsynced) |
| `tools/TOOL_DESCRIPTIONS.md` | Modify (one row, one count) | Low — read by `check_tool_descriptions_sync.py` | 67 | High (one effective author, name-case variants in `git shortlog`) | not applicable (rsynced) |
| `rules/toolchain.md` | Modify (one new section) | Medium — loaded by every Python workflow skill, so wording must stay accurate | 8 | High | not applicable (rsynced) |

## Design
- **Task size**: Path B. Four target files, and a new tool module; the interface is a new CLI (exit codes, options), which counts as a runtime-facing interface for operators.
- **Architecture analysis** (checked in Step 3): `tools/` scripts are outside `.importlinter`'s `root_packages` (`agent db mcp_servers rag shared eventbus`), so no import contract applies; the new module imports only the standard library (`argparse`, `json`, `re`, `subprocess`, `sys`, `collections`, `dataclasses`). `lint-imports` is unaffected.
- **Dependency graph** (checked in Step 3): nothing imports a `tools/check_*.py` script; the only references are `tools/TOOL_DESCRIPTIONS.md` (checked by `check_tool_descriptions_sync.py`) and optionally `routing.md`. Four files require changes.
- **Historical analysis** (checked in Step 3): `tools/TOOL_DESCRIPTIONS.md` 67 commits and `rules/toolchain.md` 8 commits in 30 days; both have one effective author. `tools/TOOL_DESCRIPTIONS.md` is edited often, so the row insertion must be a minimal diff to avoid merge conflicts.
- **Operational dependency inspection** (checked in Step 2): the tool needs `gh` on `PATH` and an authenticated account; it holds no listening socket and touches no database. `pip-audit` is not applicable (no dependency added).
- **Mechanism (`REQ-001`)**: three options from the Issue. (1) GitHub Actions scheduled workflow: rejected — adds CI infrastructure the Issue excludes, runs outside the session so its report has no delivery path, and cannot call into `python-test-and-fix`. (2) Cloud scheduled agent: rejected as the default — the delivery channel is unconfirmed and it would send repository context to a hosted service. (3) Local recurring session task running a read-only tool: chosen — no new infrastructure or credential, output stays in the session. The recurring task itself is created only after the user confirms (Phase 3).
- **Query and parsing (`REQ-002`)**: `gh run list --workflow <name> --branch <branch> --limit <N> --json databaseId,conclusion,status,createdAt,headSha,workflowName`, then `gh run view <id> --log-failed` only for runs whose conclusion is `failure`. Test identifiers come from the `FAILED <nodeid>` lines of the `short test summary info` block; the part after ` - ` is a message and is dropped.
- **Grouping (`REQ-003`)**: `collections.Counter` over the set of identifiers per run (a test counted once per run). In-progress runs are listed but excluded from the repeat count and from the exit code decision. `--before` filters the fetched list client-side on `createdAt`; it does not add a write or a new `gh` subcommand.
- **Read-only guard (`REQ-004`)**: a private function `_run_gh(args)` accepts only argument vectors whose first two elements are `("run", "list")` or `("run", "view")` and raises `ValueError` otherwise, before `subprocess.run`. It is the single place that spawns a process, so reading it is the proof of AC-3. No token is read from the environment or repository.
- **Failure handling (`REQ-005`)**: a missing `gh`, a non-zero `gh` exit, or unparsable JSON stops with exit code 2 and a one-line message on stderr; nothing is retried.
- **Compatibility**: no existing tool or file changes behavior; no config key is added.
- **Docstring guard**: new `tools/` modules are not covered by `generate_reference_table.py` (its domains are listed in `routing.md`); no reference-table change is expected, confirmed by `generate_reference_table.py --check` in the Validation plan.

## Implementation steps
1. **Phase 1: Tests first (red)**
   - [ ] Write the grouping, parsing, in-progress, allowlist, and exit-code tests with fixed sample data; they fail because the module does not exist yet (`REQ-007`; `tests/tools/test_check_ci_results.py`)
2. **Phase 2: Tool implementation**
   - [ ] Implement `_run_gh` allowlist, the run query, log parsing, grouping, report, and exit codes (`REQ-002`, `REQ-003`, `REQ-004`, `REQ-005`; `tools/check_ci_results.py`)
   - [ ] Run `routing.md` "Adding a new tool" steps 1-4 on the file (`REQ-007`; `tools/check_ci_results.py`)
3. **Phase 3: Documentation, live verification, hand-off**
   - [ ] Add the index row and update the module count (`REQ-007`; `tools/TOOL_DESCRIPTIONS.md`)
   - [ ] Add the operational note section with schedule, owner, disable instruction, delivery channel, and manual follow-up (`REQ-006`; `rules/toolchain.md`)
   - [ ] Run the tool once on live red history and once on a known-green window and record both outputs (`REQ-008`; `tools/check_ci_results.py`)
   - [ ] Deploy: no `scripts/` or `config/` file changes, so no `skills/deploy/SKILL.md` hand-off applies; state this explicitly in the Execution Status notes
   - [ ] Hand-off: ask the user to confirm creating the recurring task (`loop` or `schedule` skill) after the commit is pushed; do not create it without that confirmation (`REQ-001`, `REQ-006`)

## Validation plan
| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| `tests/tools/test_check_ci_results.py` | Unit, fixed sample data, injected fake runner | `uv run pytest tests/tools/test_check_ci_results.py -q` (red first, then green) | Fails before Phase 2, passes after |
| `tools/check_ci_results.py` | Lint, types, security (`routing.md` "Adding a new tool") | `uv run ruff format tools/check_ci_results.py`; `uv run ruff check tools/check_ci_results.py`; `uv run mypy tools/check_ci_results.py`; `uv run bandit tools/check_ci_results.py` | All clean; bandit may flag `subprocess` (`B404`/`B603`): justify each with a scoped `# nosec` only if the allowlist makes it safe (`check_suppression_justification.py` applies) |
| `tools/check_ci_results.py` | Live smoke test (manual) | `uv run python tools/check_ci_results.py --limit 10`, and a green window | Red window exits 1 and flags the repeating firejail tests; green window exits 0 |
| Mutation check | Restore a write-capable argument in a scratch copy | Add `("run", "rerun")` to the allowlist in a scratch copy and run the allowlist test | The allowlist test fails; restore afterwards |
| `tools/TOOL_DESCRIPTIONS.md` | Consistency | `uv run python tools/check_tool_descriptions_sync.py` | Pass |
| `rules/toolchain.md`, `tools/TOOL_DESCRIPTIONS.md` | Docs checks | `uv run python tools/run_validation_gates.py`; `uv run python tools/check_skills_references.py`; `uv run python tools/check_docs_quality.py` | No `Fail` attributable to this change |
| Whole change | Full suite and generated reference | `uv run pytest -v`; `uv run python tools/generate_reference_table.py --check` | No new failure (the known firejail failures also occur on CI, not in a local run where firejail exists); no drift |

## Risks
- **Risk**: A parser over CI log text breaks when the pytest output format changes → **Mitigation**: parse only the `FAILED <nodeid>` summary lines, treat a run without them as "red, no identifiers", and cover both with fixed-log tests (likelihood: low; `addopts` is fixed in `pyproject.toml`).
- **Risk**: `gh run view --log-failed` for many red runs is slow or rate-limited → **Mitigation**: fetch logs only for `failure` runs within N (default 10), once per run, with no retry (likelihood: medium during a red streak such as the current one).
- **Risk**: The tool is later extended with a write command (rerun, dispatch) → **Mitigation**: the single `_run_gh` allowlist plus a test that fails on any added vector; the operational note states the read-only rule.
- **Risk**: A scheduled run forwards content to an external service when a notification channel is added later → **Mitigation**: delivery is fixed to stdout (`REQ-005`); a new channel is a new Issue with explicit confirmation (`UNK-02`).
- **Risk**: The report keeps flagging the same deterministic failure and trains readers to ignore it → **Mitigation**: the report flags repeats by test identifier and the operational note routes every flagged test to `python-test-and-fix`; the underlying red CI is tracked separately (`UNK-01`).
- **Risk**: `tools/TOOL_DESCRIPTIONS.md` is edited frequently (67 commits in 30 days), so the row edit can conflict → **Mitigation**: one-row, one-count diff; commit and sync promptly (`git-commit-and-sync`).

## Execution Status

Table structure, status/type vocabulary, and general guidance: see
`templates/execution-status.md`.

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Phase 1: write the failing tests (`tests/tools/test_check_ci_results.py`) | Pending | — | — | `REQ-007` |
| 2 | Phase 2: implement `tools/check_ci_results.py` and run "Adding a new tool" steps 1-4 | Pending | — | — | `REQ-002`..`REQ-005`, `REQ-007` |
| 3 | Phase 3: docs (`tools/TOOL_DESCRIPTIONS.md`, `rules/toolchain.md`), live verification, user-gated schedule hand-off | Pending | — | — | `REQ-001`, `REQ-006`, `REQ-007`, `REQ-008` |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| — | — | — | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| — | — | — | — | — | — |

## Traceability
- **Workflow phase**: issue-to-plan
- **Source issue**: issues/20261023-173506_ci001_scheduled-ci-result-check-that-routes-failures-to-the-test-and-fix-workflow.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: this document is the generated plan
- **Source implementation procedure**: N/A: not applicable in this phase
- **Generated at**: 20261025-090535
- **Related target files**: `tools/check_ci_results.py`, `tests/tools/test_check_ci_results.py`, `tools/TOOL_DESCRIPTIONS.md`, `rules/toolchain.md`

### Requirement Traceability
| Requirement ID | Source Issue section or evidence | Target file | Implementation step | Acceptance criterion | Test or validation item | Status |
|---|---|---|---|---|---|---|
| REQ-001 | Required Changes bullet 1; Implementation Intent; mechanism options weighed in Design | `rules/toolchain.md` | Phase 3 | AC-1, AC-7 | Docs gates in Validation plan | Derived from confirmed evidence |
| REQ-002 | Required Changes bullet 2; `gh run list`/`gh run view --log-failed` output read 2026-10-25 | `tools/check_ci_results.py` | Phase 2 | AC-1 | Live smoke test; parsing tests | Confirmed by repository evidence |
| REQ-003 | Required Changes bullet 3; Summary (repeat of the same test) | `tools/check_ci_results.py` | Phase 2 | AC-2 | Grouping tests; live red window | Explicit in issue |
| REQ-004 | Constraints (read-only, no credentials, no external service) | `tools/check_ci_results.py` | Phase 2 | AC-3 | Allowlist tests; mutation check | Explicit in issue |
| REQ-005 | Required Changes bullet 4; AI Implementation Instruction ("stop and report if `gh` cannot read run history") | `tools/check_ci_results.py` | Phase 2 | AC-4 | Exit-code tests | Derived from confirmed evidence |
| REQ-006 | Required Changes bullet 5; Documentation Impact | `rules/toolchain.md` | Phase 3 | AC-7 | `check_skills_references.py`, `check_docs_quality.py` | Explicit in issue |
| REQ-007 | Testing Expectations; `routing.md` "Adding a new tool" | `tests/tools/test_check_ci_results.py` | Phase 1, Phase 2 | AC-5, AC-6 | `uv run pytest tests/tools/test_check_ci_results.py -q` | Explicit in issue |
| REQ-007 | Documentation Impact (`tools/TOOL_DESCRIPTIONS.md`); `check_tool_descriptions_sync.py` | `tools/TOOL_DESCRIPTIONS.md` | Phase 3 | AC-6 | `check_tool_descriptions_sync.py` | Explicit in issue |
| REQ-007 | Testing Expectations ("Adding a new tool" validation) | `tools/check_ci_results.py` | Phase 2 | AC-6 | ruff, mypy, bandit on the file | Explicit in issue |
| REQ-008 | Acceptance Criteria bullet 1 (known-red and known-green verified once on real data); 18 successes within the last 100 runs | `tools/check_ci_results.py` | Phase 3 | AC-8 | Manual live runs | Confirmed by repository evidence |
