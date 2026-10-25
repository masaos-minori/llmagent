## Goal

- Implement `tools/check_ci_results.py` (new): a read-only CI result reporter that queries recent CI runs with `gh`, groups tests that failed in two or more runs, and exits 0/1/2 per the Plan — REQ-002 (query and record runs), REQ-003 (repeat grouping and report), REQ-004 (read-only allowlist), REQ-005 (stdout-only report and exit codes).

## Scope

- **In-Scope**: the whole module — CLI options (`--limit`, `--workflow`, `--branch`, `--before`), a single allowlisted `gh` invocation wrapper, `FAILED <nodeid>` log parsing, per-run-set grouping via `collections.Counter`, the stdout report with a pointer to `skills/python-test-and-fix/SKILL.md`, and exit-code selection.
- **Out-of-Scope**: creating or enabling any scheduled task (Plan hand-off, user-gated); fixing failing/flaky tests (including the firejail failures, Plan `UNK-01`); changing `.github/workflows/ci.yml`; writing anything; filing issues automatically.

## Assumptions

- `gh` is not authenticated in the current environment (Plan `UNK-05`, re-verified 2026-10-25): all logic must be exercisable by unit tests with an injected fake runner (no network, no `gh`); the live runs (REQ-008) are gated on the user re-authenticating `gh`.
- Log-shape evidence is historical from the Plan's Step 2 (run `40144039702`): summary lines `FAILED <nodeid> - <message>` behind a `<job>\t<step>\t<timestamp> ` prefix; `pyproject.toml`'s `addopts = "-v --tb=short"` keeps the `short test summary info` block stable.
- Style reference `tools/check_plan_target_overlaps.py` (docstring-led CLI, `argparse`, `ROOT_DIR`, `main()`) exists and is read-only — confirmed in the Plan cycle.

## Design decisions

- `_run_gh` (new) is the only place that spawns a process: it accepts an argument vector only when the first two elements are `("run", "list")` or `("run", "view")` and raises `ValueError` before `subprocess.run` otherwise; `shell=False`, arguments as a list (`skills/DESIGN.md` Pythonic safety constraints). This single point is the proof of AC-3.
- Grouping uses `collections.Counter` over each run's *set* of failed-test identifiers, so a test counts once per run; in-progress runs are listed but excluded from the repeat count and from the exit-code decision.
- `--before` filters the fetched run list client-side on `createdAt`; it adds no `gh` subcommand and no write operation.
- Records are `dataclasses`; imports stay standard library only (`argparse`, `json`, `re`, `subprocess`, `sys`, `collections`, `dataclasses`) — `tools/` is outside `.importlinter`'s `root_packages`, so no import contract applies.

## Alternatives considered

- GitHub Actions scheduled workflow and cloud scheduled agent: already rejected in the Plan's Design (`REQ-001`); this row implements only the local read-only tool.
- Parsing verbose progress lines instead of the `short test summary info` block: rejected — verbose `... FAILED [  6%]` lines risk double-counting; the summary block is fixed by `addopts`.

## Implementation
### Target file
- `tools/check_ci_results.py` (new)

### Procedure
1. Open the module with a docstring stating usage, the read-only contract, and the exit codes, in the style of `tools/check_plan_target_overlaps.py`.
2. Add `main` (new) with `argparse`: `--limit` (default 10), `--workflow` (default `CI`), `--branch` (default `master`), `--before` (optional ISO-8601 timestamp).
3. Implement `_run_gh` (new): allowlist check first (raise `ValueError` on any other vector), then `subprocess.run` of `["gh", *args]`; a missing `gh` binary (`FileNotFoundError`), a non-zero `gh` exit, or unparsable JSON each stop the tool with a one-line message on stderr and exit code 2 — nothing is retried.
4. Query runs with `run list --workflow <name> --branch <branch> --limit <N> --json databaseId,conclusion,status,createdAt,headSha,workflowName`; apply the `--before` filter client-side on `createdAt`.
5. For each run whose `conclusion` is `failure`, call `run view <id> --log-failed` once and extract failed-test identifiers (Step in Method below); runs without any such line are reported as red with no test identifiers.
6. Group identifiers across runs (Counter over per-run sets); print the report: red runs (run id, head SHA, failed jobs, failed tests) first, then every test identifier that failed in two or more examined runs with its run count; every reported red state ends with a pointer to `skills/python-test-and-fix/SKILL.md`.
7. Exit per REQ-005: `0` when the latest completed run is green and no test repeats; `1` when it is red or a repeat exists; `2` on any `gh` read failure.

### Method
- `parse_failed_tests` (new): strip the `<job>\t<step>\t<timestamp> ` line prefix, then match the `FAILED <nodeid>` summary lines; everything after ` - ` is a message and is dropped; verbose progress lines are not counted (a run with no summary match yields an empty identifier set, still reported red).
- `group_repeats` (new): Counter as in Design decisions; a repeat threshold of two or more runs (Plan Assumption; N is the `--limit` window).
- `main` (new): orchestrate query → parse → group → report → exit code; in-progress runs (`status` not `completed`) are listed but never decide the exit code.

### Details
- GitHub `createdAt` is UTC ISO-8601 with a `Z` suffix; `--before` is compared against it.
- No credential is read from the environment or repository; no repository content is sent to any service beyond the read-only `gh` queries; report output is stdout only (stderr carries only the `gh` failure lines).
- `RunRecord` (new) dataclass fields: run id, head SHA, conclusion, status, created-at, failed job names, failed test identifiers.

## Compatibility considerations

- New standalone module imported by nothing; no existing tool or config changes behavior; `generate_reference_table.py` does not cover `tools/` domains, so no reference-table change is expected (confirmed by its `--check` in the validation run).

## Security considerations

- The `_run_gh` (new) allowlist is the enforcement point: any write-capable vector (`run rerun`, `workflow run`, `api`) raises before a process spawns (AC-3, with a mutation check in the Plan's Validation plan).
- `bandit` may flag `B404`/`B603` for the `subprocess` import/use: suppress only with scoped `# nosec` plus em-dash justification per `rules/coding.md` Suppression governance, then `tools/check_suppression_justification.py` passes.

## Rollback considerations

- Delete the new file and revert the single commit; nothing imports it, so no ripple.

## Validation plan

| Target | Strategy | Command | Expected |
|---|---|---|---|
| `tools/check_ci_results.py` | routing.md "Adding a new tool" steps 1-4 | `uv run ruff format tools/check_ci_results.py`; `uv run ruff check tools/check_ci_results.py`; `uv run mypy tools/check_ci_results.py` (explicit path — mypy's default scope excludes `tools/`); `uv run bandit tools/check_ci_results.py` | All clean |
| `tools/check_ci_results.py` | unit suite (row 02 document) | `uv run pytest tests/tools/test_check_ci_results.py -q` | Green after this row and row 02 are both implemented |
| `tools/check_ci_results.py` | live smoke (manual, gated on `UNK-05` gh re-authentication) | `uv run python tools/check_ci_results.py --limit 10`, and a green window via `--limit 100 --before 2026-10-23T03:44:13Z` | Red window exits 1 and flags repeats; green window exits 0; record both outputs in the Plan's Execution Status notes (AC-8) |
| `tools/check_ci_results.py` | mutation check | Add `("run", "rerun")` to the allowlist in a scratch copy; run the row 02 allowlist test | The test fails; restore afterwards |

## Completion criteria

- AC-1..AC-4 hold for this file: live report per run (once gh is available), repeat flagging, allowlist-only spawn points, exit codes `0`/`1`/`2` with stdout-only report.
- `routing.md` "Adding a new tool" steps 1-4 pass clean; the row 02 unit tests pass.
- AC-8 live runs are recorded in the Plan's Execution Status notes once `UNK-05` is resolved by the user.

## Out of Scope

- Scheduling the recurring task, fixing any failing test, CI workflow changes, automatic issue filing (Plan Scope; Plan hand-off Phase 3).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement `tools/check_ci_results.py` per Procedure/Method/Details | Pending | — | — | `REQ-002`..`REQ-005` |
| 2 | Run row 02 unit tests (`tests/tools/test_check_ci_results.py`) | Pending | — | — | `REQ-007` |
| 3 | Run "Adding a new tool" steps 1-4 gates (ruff/mypy/bandit) | Pending | — | — | `REQ-007` |
| 4 | Live smoke runs (red window + green window), record outputs | Pending | — | — | `REQ-008`; blocked until gh is re-authenticated (`UNK-05`) |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| 4 | `gh` not authenticated in this environment; live runs gated on user re-authentication | N/A: unresolved at procedure generation time (`UNK-05`) | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| — | — | — | — | — | — |

## Traceability
- **Workflow phase**: plan-to-implementation-procedure
- **Requirement ID**: `REQ-001`..`REQ-005` (mechanism record, run query, repeat grouping, read-only guard, exit codes)
- **Source issue**: issues/20261023-173506_ci001_scheduled-ci-result-check-that-routes-failures-to-the-test-and-fix-workflow.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261025-090535_ci001_scheduled-ci-result-check-that-routes-failures-to-the-test-and-fix-workflow.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261025-100210
- **Related target files**: `tools/check_ci_results.py`
