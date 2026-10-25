# Procedure: `tests/tools/test_check_ci_results.py`

Stage-2 output for Issue 20261023-173506 / Plan 20261025-090535. Source plan:
`plans/done/20261025-090535_ci001_scheduled-ci-result-check-that-routes-failures-to-the-test-and-fix-workflow.md`.
Frozen decisions are copied from the plan; this procedure does not re-decide any of them.

**Correction note (2026-10-25, execution cycle):** the originally generated version of this
document referenced a nonexistent issue (`20261024-105844`), a nonexistent requirements doc
(`doc0001`), a nonexistent mock-pattern file, a nonexistent `pytest.ini`, and a gh
annotations-based design (`--failed` / `--comments` / `--max-annotations`, async runner, exit
`1` on gh failure) that contradicts the Plan's frozen design (`--json` fields + `run view
--log-failed`, synchronous allowlisted runner, exit `2` on gh read failure). The user approved
rewriting it to match the Plan and the row 1 implementation; this is that rewrite.

**Row:** 2 of 4, Type `Test`, Path `tests/tools/test_check_ci_results.py`, Action `Create`, Size `M`, Depends on `tools/check_ci_results.py`

## Goal

- Implement `tests/tools/test_check_ci_results.py` (new): the row 1 unit suite for
  `tools/check_ci_results.py` — Plan `REQ-007` (AC-5): grouping cases, log-line parsing,
  the read-only allowlist, and the `0`/`1`/`2` exit codes, all over fixed sample data with an
  injected fake runner (Plan Validation plan bullets `:95`..`:98`).

## Scope

- **In-Scope**: one new test file covering the four Plan validation bullet groups plus the
  `--before` filter and the report's skill pointer.
- **Out-of-Scope**: live `gh` runs (`REQ-008`, row 1 Step 4, gated on `UNK-05`); any change to
  `tools/check_ci_results.py`, existing tests, `pyproject.toml`, or `conftest.py` files.

## Assumptions

- `gh` is not authenticated (Plan `UNK-05`): every test runs offline through a fake injected
  via `monkeypatch.setattr` on the module attribute `_run_gh`; the allowlist tests additionally
  patch `subprocess.run` inside `tools.check_ci_results` to prove nothing spawns.
- pytest config is `pyproject.toml [tool.pytest.ini_options]`: `testpaths = ["tests"]`,
  `addopts = "-v --tb=short"`, `asyncio_mode = "auto"` (confirmed 2026-10-25). The row-commands
  still use explicit paths (`tests/tools/test_check_ci_results.py`) per the Plan's AC-5 command.
- `tests/tools/` holds 49 existing `test_<tool>.py` files; the import/monkeypatch style of
  `tests/tools/test_check_plan_target_overlaps.py` (`import tools.<module> as <alias>`,
  `monkeypatch.setattr(<alias>, "<symbol>", ...`) is the pattern this file mirrors.
- Test-shape baseline in `tests/tools/`: 1141 tests collected repo-wide for `tests/tools`
  (2026-10-25 run); this file only adds tests.

## Design decisions

- The fake runner is a callable class installed on the module attribute `ccr._run_gh` — the
  same seam row 1 documented (`_run_gh` is the only process-spawn point). It records every
  argument vector so call-shape assertions are possible.
- Allowlist proof has two halves: (a) every vector `main()` records is one of the two allowed
  shapes, and (b) each forbidden vector (`run rerun`, `workflow run`, `api`, short vectors)
  raises `ValueError` with `subprocess.run` patched to a recorder that must never be called.
- Fixed samples are literal gh-JSON dicts (`databaseId,conclusion,status,createdAt,headSha,workflowName`)
  and prefixed log text builders emitting the `<job>\t<step>\t<timestamp> ` shape recorded in
  the Plan Background (run `40144039702`); the all-green / repeat / mixed / no-summary /
  in-progress shapes of the Plan's grouping bullets are each one sample.
- Exit codes are asserted on `main()`'s return value (row 1's `main` returns the code);
  `sys.exit(main())` at module bottom is exercised only in the `__main__` guard, not per-test.

## Alternatives considered

- Running the real CLI through `subprocess` in tests: rejected — no `gh` auth (`UNK-05`) and
  nondeterministic; the Plan fixes an injected fake runner.
- Patching `subprocess.run` for every test instead of the `_run_gh` seam: rejected for
  query-shape tests — it bypasses the allowlist check itself and would hide allowlist
  regressions; reserved for the two allowlist-proof cases.

## Implementation
### Target file
- `tests/tools/test_check_ci_results.py` (new)

### Procedure
1. Open the module with a docstring naming the tool under test and the `REQ-007` coverage, in
   the style of `tests/tools/test_check_plan_target_overlaps.py`.
2. Add module-level sample builders: `_run_json(run_id, conclusion, status, created_at, ...)`
   (gh-JSON dict), `_gh_json(runs)` (payload string), `_log(job, step, lines)` (prefixed log),
   and `class FakeGh` (records `calls`; scripted list/view payloads, `list_rc`,
   `view_rc`, `missing_binary`, `not_json` switches).
3. Parsing group (Plan bullet `:96`): prefixed excerpt yields exactly the `FAILED <nodeid>`
   identifiers; the part after ` - ` is dropped; verbose `... FAILED [  6%]` progress lines are
   not counted; a red run with no summary line parses to an empty list; duplicate summary lines
   dedupe per run.
4. Grouping group (Plan bullet `:95`): one red run lists its tests; the same test in two of
   three runs is counted 2; a test failing twice within one run counts 1 (per-run set);
   an all-green window counts nothing; in-progress runs contribute nothing.
5. Allowlist group (Plan bullet `:97`): `("run","list",...)` and `("run","view",...)` reach the
   patched `subprocess.run` as `["gh", ...]` without `shell`; `("run","rerun",...)`,
   `("workflow","run",...)`, `("api",...)`, and one-element vectors raise `ValueError` before
   the recorder is called; a full `main()` run records only allowed shapes.
6. Exit-code group (Plan bullet `:98`): all-green latest completed → 0 with no pointer; red
   latest completed → 1; green latest with a 2-run repeat → 1 (repeat section names the test
   with its count); older failure + green latest, no repeat → 0; only in-progress runs → 0;
   missing binary, non-zero `gh` exit, unparsable JSON, failed `run view` → 2 with a one-line
   stderr message.
7. `--before` group: a `--before` timestamp drops runs created at/after it (the red newest run
   disappears, no `run view` call is made for it) and an ISO parse error exits via
   `parser.error` (SystemExit code 2).
8. Report-content group: the red run's id, short head SHA, job names, and failed test
   identifiers appear on stdout; the pointer to `skills/python-test-and-fix/SKILL.md` appears
   in red/repeat reports and is absent from an all-green report.

### Method
- Fixtures use `monkeypatch` only (no network, no sleeps, no env patching), matching the repo
  pattern; each test installs `monkeypatch.setattr(ccr, "_run_gh", fake)` and asserts on
  `main([...])`'s return code plus `capsys` output.
- `RunRecord` and `group_repeats`/`parse_failed_tests` are also called directly for the
  parsing/grouping groups (no CLI round-trip needed).

### Details
- `FakeGh.__call__(args)` mirrors the real signature `(list[str]) -> subprocess.CompletedProcess[str]`.
- Sample timestamps use fixed `createdAt` values (`2026-10-23T03:36:19Z` etc.) so `--before`
  comparisons are exact; the newest sample is ordered first, as `gh run list` returns.
- One sample set mirrors the Plan Background's two firejail repeat offenders as generic
  `tests/agent/test_x.py::test_a` / `test_b` identifiers; no live log text is copied.

## Compatibility considerations

- New test file only; no existing test, conftest, or `pyproject.toml` change; the
  `tests/tools` collected count rises by this file's cases only.

## Security considerations

- Tests never spawn `gh` or open the network: the fake replaces the module's only
  process-spawn point, and the allowlist cases prove the guard before `subprocess.run`.

## Rollback considerations

- Delete the new file; row 1's tool and the rest of the suite are unaffected.

## Validation plan

| Target | Strategy | Command | Expected |
|---|---|---|---|
| `tests/tools/test_check_ci_results.py` | targeted suite | `uv run pytest tests/tools/test_check_ci_results.py -q` | All green |
| `tests/tools/` | whole tools-dir suite regression | `uv run pytest tests/tools/ -q` | Green, no existing test changed |
| `tests/tools/test_check_ci_results.py` | lint/format gates | `uv run ruff format tests/tools/test_check_ci_results.py`; `uv run ruff check tests/tools/test_check_ci_results.py` | Clean |
| `tests/tools/test_check_ci_results.py` | mock-target checker | `uv run python tools/check_mock_patch_targets.py` | Passes (patch targets the module under test) |
| row 1 + row 2 | mutation guard (Plan row 1 Validation plan) | scratch copy of `tools/check_ci_results.py` with `("run","rerun")` added to `_ALLOWED_VECTORS`; run the allowlist test | The test fails; scratch copy discarded, real file untouched |

## Completion criteria

- AC-5: the targeted command passes with the grouping, parsing, in-progress, allowlist,
  exit-code, and `--before` cases (Plan `:89`).
- Whole `tests/tools/` green; row 1's Execution Status step 2 can then be marked Completed.
- Mutation guard executed once and reverted.

## Out of Scope

- Live `gh` verification (`REQ-008` / AC-8, row 1 step 4, `UNK-05`); CI workflow YAML;
  scheduling (Plan Phase 3, user-gated).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement `tests/tools/test_check_ci_results.py` per Procedure/Method/Details | Completed | 2026-10-25 | 2026-10-25 | 29 tests, 4 classes; import/monkeypatch style mirrors test_check_plan_target_overlaps.py |
| 2 | Run targeted + whole-`tests/tools/` suites | Completed | 2026-10-25 | 2026-10-25 | 29 passed targeted; whole tests/tools 1168 passed, 2 skipped in 22.33s (1141 collected before + 29 new) |
| 3 | Run lint gates and the mutation guard | Completed | 2026-10-25 | 2026-10-25 | ruff format/check clean; mypy clean (explicit path); check_mock_patch_targets no findings; mutation guard: adding (run,rerun) to _ALLOWED_VECTORS turned test_forbidden_vectors_raise_before_any_spawn[vector0] red (DID NOT RAISE ValueError), reverted, 29 green again |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| — | None: tests are offline by design (`UNK-05` only gates row 1's live runs) | N/A | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| — | — | — | — | — | — |

## Traceability
- **Workflow phase**: code-implementation (procedure corrected in-cycle per user approval)
- **Requirement ID**: `REQ-007` (unit tests over fixed sample data)
- **Source issue**: issues/20261023-173506_ci001_scheduled-ci-result-check-that-routes-failures-to-the-test-and-fix-workflow.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261025-090535_ci001_scheduled-ci-result-check-that-routes-failures-to-the-test-and-fix-workflow.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261025-100210 (rewritten 2026-10-25 in the execution cycle)
- **Related target files**: `tests/tools/test_check_ci_results.py`, `tools/check_ci_results.py`
