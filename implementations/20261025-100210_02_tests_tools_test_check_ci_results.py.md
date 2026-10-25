# Procedure: `tests/tools/test_check_ci_results.py`

Stage-2 output for Issue 20261024-105844 / Plan 20261025-090535. Source plan: `plans/20261025-090535_ci001_scheduled-ci-result-check-that-routes-failures-to-the-test-and-fix-workflow.md`. Frozen decisions are copied from the plan; this procedure does not re-decide any of them.

**Row:** 2 of 4, Type `Test`, Path `tests/tools/test_check_ci_results.py`, Action `Create`, Size `M`, Depends on `tools/check_ci_results.py`

## File Scope

- Create, one file: `tests/tools/test_check_ci_results.py`.
- `tests/tools/` currently contains only `test_check_skills_structure.py` and `test_manage_workitem_stage.py`; no conftest exists there and none is added (sample-data builders live in this test file as module-level helpers).
- No changes to `scripts/`, `tasks/`, `tools/check_ci_results.py`, or the existing top-level `tests/conftest.py`.

## Pre-Change State

- `tests/tools/` exists but has no CI-result tests (confirmed by directory listing, Step 3a).
- pytest contract (`pytest.ini`): `importmode = importlib`, `addopts = "-v --tb=short"`, `asyncio_mode = auto`, `testpaths = tests/unit, tests/integration`.
  - **Operational note:** `tests/tools/` is NOT in `testpaths`, so a bare `uv run pytest` does not collect this file. Every command in this procedure — and any future CI/scheduled invocation — must pass the path explicitly (`uv run pytest tests/tools/...`). Recorded so the scheduled-CI row (docs/00_index mapping) inherits it.
- The mock pattern in this repo is `unittest.mock.AsyncMock`/`MagicMock` + `monkeypatch` (confirmed by grep across `tests/`); `tests/unit/test_mcp_skill_audit_server.py:36-39` monkeypatches module-level subprocess helpers the same way this file will monkeypatch `_run_gh`.
- Test-count baseline: 925 tests collected (Step 3a run, 29.76s). This file must add tests without altering any existing count.

## Frozen Decisions (from the plan, copied not re-decided)

| ID | Decision | Where it lands in tests |
|---|---|---|
| REQ-003 / AC-3 | gh usage restricted to the three approved call shapes | `test_allowed_call_shapes` asserts every recorded call matches one of the three templates exactly |
| REQ-004 / AC-2 | grouping: passed runs not reported; latest failed run's annotations only; empty annotations fall back to job names | `TestGrouping` (4 cases) |
| REQ-005 / AC-4 | report lists failed run id + branch + job/annotation text | `TestReportContent` |
| REQ-006 / AC-5 | exit codes 0/1/2 | `TestExitCodes` |
| REQ-007 / AC-6 | malformed/empty input handled without crash | `TestMalformedInput` |
| Constraint: fixed sample CI data | all fixtures are literal JSON dicts in this file — no live API at test time | all fixtures |
| Constraint: deterministic, no network | no `monkeypatch` of env except the `_run_gh` seam; no sleeps | enforced by using an injected fake runner |

Note on AC-2 precision: REQ-004 text says "most recent failed run", the AC-2 bullet says "most recent failed run per job". AC-8 lists both a per-job-failed and a mixed pass/fail sample. The test suite below implements the **per-job** reading (each job's latest run decides its reporting status) and records the alternative run-level reading as an Unknown carried to doc0001.

## Implementation Procedure

### Stage 1 — sample-data builders and fake-runner fixtures

Create module-level builders (pure dicts, no I/O):

```python
def _run(run_id, branch, status, conclusion, jobs):   # one CI run dict
def _job(name, conclusion, steps):                    # one job dict
def _annotation(name, annotation_level, message):     # one annotation dict
```

Fixed samples (minimum set, all literal):
- `SAMPLE_ALL_GREEN` — 2 runs, both `completed`/`success`.
- `SAMPLE_JOB_FAILED` — job `unit-tests`: latest run `failure` with annotations `test_a.py::test_x` / `test_b.py::test_y`; older runs success.
- `SAMPLE_MIXED` — `unit-tests` latest `success`, `integration-tests` latest `failure` (with annotations).
- `SAMPLE_EMPTY_ANNOTATIONS` — latest run `failure`, annotations `[]`, failed job name only.
- `SAMPLE_FAILED_THEN_GREEN` — job `unit-tests`: older run `failure` (with annotations), latest run `success`.
- `SAMPLE_OLDED_FAIL_ANNOTATIONS` — latest run `failure` with **no** annotations, an older `failure` run **with** annotations (pins "latest only").
- `SAMPLE_IN_PROGRESS` — a `status = "in_progress"` run (must not be counted failed).
- `SAMPLE_NO_RUNS` — `[]`.

Fake runner fixture:

```python
class FakeGh:
    def __init__(self, by_args):   # maps (subcommand tuple prefix) -> payload json str
    async def __call__(self, args, timeout=120):
        # records (args, timeout); returns (0, payload, "") or scripted (exit, "", stderr)
```

Injection point: `monkeypatch.setattr(check_ci_results, "_run_gh", fake)` — the single seam, matching `tests/unit/test_mcp_skill_audit_server.py:36-39`'s pattern for module-level subprocess helpers. Import via `from tools import check_ci_results` (tests import from `tools/` freely; the import-linter contract covers `scripts/` only — plan Phase 3 Risk 5).

### Stage 2 — grouping semantics (AC-2)

- `test_all_green_exits_zero` — `SAMPLE_ALL_GREEN` → exit 0, no failures reported.
- `test_job_failed_is_reported` — `SAMPLE_JOB_FAILED` → the failed job's annotations appear in output.
- `test_mixed_only_failed_reported` — `SAMPLE_MIXED` → only `integration-tests` content appears; `unit-tests` name absent from the failure list.
- `test_older_failures_not_used_when_latest_green` — `SAMPLE_FAILED_THEN_GREEN` → exit 0.
- `test_only_latest_failed_run_annotations_used` — `SAMPLE_OLDED_FAIL_ANNOTATIONS` → failed output does NOT contain the older run's annotations (pins the "latest only" rule).
- `test_in_progress_run_not_failed` — `SAMPLE_IN_PROGRESS` → not reported as failure (and, if no other failures, exit 0).

### Stage 3 — fallback and report content (AC-2 fallback, AC-4)

- `test_empty_annotations_falls_back_to_job_name` — `SAMPLE_EMPTY_ANNOTATIONS` → job name reported, no crash.
- `test_report_contains_run_id_and_branch` — failed output contains the run id and branch strings (`SAMPLE_JOB_FAILED`).
- `test_no_gh_run_log_calls` — after a full failing-sample run, assert none of the recorded fake calls contain `log` or `view` (AC-3 negative half; mutation guard against a log-fetching implementation).

### Stage 4 — allowlist call shapes (AC-3)

- `test_allowed_call_shapes` — every recorded call matches exactly one of:
  1. `("gh","run","list","--per-page","<int>")` (literal token order as doc0001's constants)
  2. `("gh","run","list","--failed","--per-page","<int>")`
  3. `("gh","run","view","<int>","--comments")`
  Parameterised over `SAMPLE_ALL_GREEN`, `SAMPLE_JOB_FAILED`, `SAMPLE_MIXED`.
- `test_no_repo_flag` — assert `--repo` appears in no recorded call (plan Risk 3 guard).

### Stage 5 — exit codes and malformed input (AC-5, AC-6)

- `test_exit_1_on_gh_failure` — fake returns `(1, "", "gh: http 500")` → module exits 1 (`SystemExit` code check or returned code, per doc0001's `main` contract).
- `test_exit_2_on_malformed_json` — fake returns `(0, "not json", "")` → exit 2, error message on stderr names the failing subcommand (AC-6).
- `test_no_runs_exits_zero` — `SAMPLE_NO_RUNS` → exit 0.
- `test_timeout_surfaces_as_error` — fake raises `asyncio.TimeoutError` → exit 2-class error path, no traceback escape (AC-6).

## Tests to Write/Run

```bash
uv run pytest tests/tools/test_check_ci_results.py -v          # this file only (explicit path required)
uv run pytest tests/tools/ -v                                   # whole tools dir
uv run pytest tests/unit tests/integration tests/tools -v       # full existing suite + new file
```

Expected: new file green against doc0001's implementation; total collected rises from the 925 baseline by the number of cases staged here (about 15) with zero existing tests changed.

Mutation guard: temporarily making doc0001's fetch use `gh run view <id>` (no `--comments`) or append `--repo` must turn Stage 4 red — verified once during implementation, then reverted.

## Risk & Impact

- Blast radius: new file only; `testpaths` unaffected; no existing test touched.
- Contract risk: none — `tests/` has no contract (`contract-intra-scripts` covers `scripts.*` only).
- Coupling risk: these tests pin doc0001's internal constants (`_run_gh` name, argument templates, `main` return/exit contract). The two docs must be implemented in dependency order (row 2 depends on row 1, per plan's target table).
- Hidden coupling: `addopts = "-v --tb=short"` already applies to tests/tools runs (confirmed Step 3a); no pytest.ini change is needed or allowed here.

## Scope Decisions

- In: the five stages above. Out: live-gh smoke (REQ-008, gated by UNK-05, belongs to the plan's Step 3 live verification, not to this file); any CI workflow YAML (blocked pending the plan's workflow-availability decision).

## Definition of Done

- All staged tests green with an explicit path invocation; call-shape and no-`--repo` assertions green; full-suite baseline unchanged; mutation-guard check performed once and reverted; `uv run pytest tests/tools/` green.
