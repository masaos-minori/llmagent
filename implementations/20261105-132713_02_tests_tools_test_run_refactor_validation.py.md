## Goal
- Add `tests/tools/test_run_refactor_validation.py` so that a break in command construction, step aggregation, the radon gate, or `--skip` of `tools/run_refactor_validation.py` fails a test, including a failing-step case (`REQ-002`: tests for the refactor gate; `REQ-004`: tests write only inside `tmp_path` and never run the real toolchain).

## Scope
**Release unit**: N/A: not part of a release unit

- In scope: one new test file. No change to `tools/run_refactor_validation.py`.
- Plan: `plans/20261105-105344_toolstest001_add-tests-for-untested-tools.md`, Plan step 2 (Phase 2).

## Assumptions
- Tests import the tool as `tools.run_refactor_validation`, like `tests/tools/test_check_module_size.py`.
- The module-level `_run` is the only place a subprocess starts, so replacing `_run` is enough to keep ruff, mypy, radon, pytest, coverage, and diff-cover from running (verified against `tools/run_refactor_validation.py`, 2026-11-05).
- `validate` always runs `ruff format` and `ruff check` first; only `mypy`, `radon`, `tests`, and `diff-cover` can be skipped.
- Plan overlap: no other open Plan targets this file or this test file; none to record.

## Design decisions
- A small recorder class replaces `tools.run_refactor_validation._run`: it appends each `cmd` list to a list and returns the next scripted `(returncode, output)` pair, or `(0, "")` when none is scripted.
- Assert the full recorded argument lists, not only the return codes, so a changed flag is caught (Plan Risk on faked `_run`).

## Alternatives considered
- Faking `subprocess.run` instead of `_run`: rejected, it would also exercise `_run`'s output joining, which is not the subject here and needs a `CompletedProcess` for every call.

## Implementation
### Target file
`tests/tools/test_run_refactor_validation.py` (new)

### Procedure
1. Create the module with a docstring, `from __future__ import annotations`, and imports of `pytest` and `from tools import run_refactor_validation as rrv`.
2. Add the recorder fixture that patches `_run` with `monkeypatch.setattr(rrv, "_run", recorder)` and exposes the recorded commands.
3. Add the test groups below.

### Method
- Command construction: `_pytest_args(["t1.py", "t2.py"], coverage=False)` equals `["uv", "run", "pytest", "t1.py", "t2.py", "-q", "-p", "no:randomly"]`; with `coverage=True` it equals `["uv", "run", "coverage", "run", "-m", "pytest", "t1.py", "t2.py", "-q", "-p", "no:randomly"]`; `_tail` keeps the last four non-empty lines joined by ` | ` and returns `no output` for empty text.
- Diff-cover: with all calls returning 0, `_diff_cover_gate(["a.py", "b.py"], ["t.py"], "master", 90)` records the coverage run, `["uv", "run", "coverage", "xml"]`, and the diff-cover list ending in `--compare-branch=master`, `--fail-under=90`, `--include`, `a.py`, `b.py`; a failing coverage run returns one `coverage run` failure and records no later command; a failing `coverage xml` returns one `coverage xml` failure.
- Radon grading (`_radon_gate`, output lines shaped like `    F 10:0 name - C (12)`): grade B only passes with detail `worst grade B (1 function(s))`; one C line fails with `1 function(s) at C or worse`; a class-level line and an empty output pass with worst grade `A`; a non-zero return code fails with the tail of the output.
- Aggregation: `validate` with every command returning 0 returns the steps `ruff format`, `ruff check`, `mypy`, `radon`, `tests`, `diff-cover` all `ok`, and the recorded `mypy` command contains `--no-namespace-packages`; a scripted failure of the `tests` step is reported as the only failed result.
- `--skip`: `skip={"mypy", "radon", "tests", "diff-cover"}` leaves only the two ruff steps and records two commands; each single skip drops exactly its own step.
- `main`: with all passing it prints one `PASS  <name>: ...` line per step and `GATE PASSED` and returns 0; with a failing step it prints a `FAIL  <name>: ...` line and `GATE FAILED: <names>` and returns 1; `--skip` choices outside the allowed set exit through argparse (`SystemExit` 2); `--src` and `--tests` are required.

### Details
- Pass `main` an explicit `argv` list; it accepts one.
- The scripted outputs are plain strings; no file is read or written, but any path-like arguments are `tmp_path` strings if one is needed.
- Use `capsys` for the printed lines; assert on exact `PASS`/`FAIL` prefixes.
- Never call `_run` unpatched: if a test needs the real `_run`, it patches `tools.run_refactor_validation.subprocess.run` instead, and no such test is required by the Plan.

## Compatibility considerations
N/A: new test file; no tool, schema, or public contract changes.

## Security considerations
N/A: no subprocess is started and nothing outside `tmp_path` is touched.

## Rollback considerations
N/A: revert the commit.

## Validation plan
- `uv run pytest tests/tools/test_run_refactor_validation.py -q` passes.
- `uv run ruff format` and `uv run ruff check` on the file are clean.
- `uv run python tools/check_mock_patch_targets.py` reports no finding.
- Mutation check: temporarily change `g > "B"` in `_radon_gate` to `g > "C"`, confirm a test fails, revert, and confirm `git diff --stat tools/` is empty.
- `uv run pytest tests/tools -q` shows no new failure.

## Completion criteria
- Command construction, aggregation, radon grading, `--skip`, and `main` are covered, including a failing-step test.
- No test starts a real subprocess; `git status` shows no change outside the new file.
- The mutation check failed a test and was reverted.

## Out of Scope
- Changes to `tools/run_refactor_validation.py`.
- Running the real ruff, mypy, radon, pytest, or diff-cover.
- Tests of `_run` itself.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Create the file with the `_run` recorder and the command-construction tests | Pending | — | — | |
| 2 | Add the radon, diff-cover, and `--skip` tests | Pending | — | — | |
| 3 | Add the `validate` and `main` aggregation tests, including the failing step | Pending | — | — | |
| 4 | Run the validation sequence (`rules/toolchain.md`) and the mutation check | Pending | — | — | |

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
- **Requirement ID**: `REQ-002` (tests for the refactor gate), `REQ-004` (tests stay inside `tmp_path`)
- **Source issue**: issues/20261104-152002_toolstest001_add-tests-for-untested-tools.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261105-105344_toolstest001_add-tests-for-untested-tools.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261105-132713
- **Related target files**: `tests/tools/test_run_refactor_validation.py`
