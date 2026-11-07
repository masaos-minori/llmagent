# Implementation Procedure: detector tests in test_manage_workitem_stage.py

## Goal

Add unit tests for the `detect-unexecuted-archive` subcommand to
`tests/tools/test_manage_workitem_stage.py`, implementing the `Tests` section of the Plan's
`REQ-002`. The tests run the detector over a temporary repository whose archive dates are
simulated by controlling git commit dates, asserting that a recently-archived procedure
with a stale row is reported, a recently-archived completed procedure is not, an old
procedure with a stale row is not, and no file is ever moved. (`REQ-002`: detector tests
over a temporary repository.)

## Scope
**Release unit**: N/A: not part of a release unit

## Assumptions
- The detector scans `implementations/done/` relative to the current working directory and
  resolves archive dates from the git history of the temp repo, so tests must run with the
  temp repo as CWD.
- Archive dates are controlled by the commit date of the `git mv` that places a procedure
  into `implementations/done/`; recent and old windows are simulated by setting
  `GIT_AUTHOR_DATE` / `GIT_COMMITTER_DATE` around that commit.
- This is the companion test file for the row covering `tools/manage_workitem_stage.py`, but
  it is generated as its own document because it requires a design decision of its own: the
  git-commit-date simulation strategy. It therefore fails the "needs no design decision of
  its own" companion condition in
  `skills/plan-to-implementation-procedure/SKILL.md`.

## Design decisions
- **Simulate archive dates via commit date, not mtime**: the detector keys on the first
  commit that adds the file at its `implementations/done/` path, so the test must make that
  commit's date recent or old. The clean way is to create the procedure under
  `implementations/`, commit it, then `git mv` it into `implementations/done/` with a
  controlled commit date via environment variables on the `git mv` subprocess.
- **Invoke the command through `manage_main`** (the same entry point the CLI uses) with an
  argv list and capture stdout/stderr via `capsys`, matching the existing success-path
  tests; set CWD to the temp repo with `monkeypatch.chdir`.

## Alternatives considered
- Writing files directly into `implementations/done/` and relying on filesystem mtime:
  rejected; the detector ignores mtime and uses the git add-commit date, so mtime would not
  drive the window.
- Using GitPython to set the committer date: works but more verbose than env vars on a
  single `git mv` subprocess, and mixing GitPython index commits with a dated `git mv`
  subprocess complicates the fixture.

## Implementation
### Target file
`tests/tools/test_manage_workitem_stage.py`

### Procedure
1. **Imports / helpers** — ensure `subprocess` and `datetime` are importable in the module
   (add to the existing imports if absent). Add a helper `_place_done_file(repo, rel_path,
   content, commit_date_str)` that:
   - writes `content` to `repo / rel_path` where `rel_path` starts at `implementations/`
     (e.g. `implementations/<name>.md`),
   - commits it with `repo.index.add` + `repo.index.commit` (so it exists under
     `implementations/`),
   - runs `git mv <impl-path> <done-path>` via `subprocess.run([...], cwd=repo, env={...os.environ, GIT_AUTHOR_DATE: commit_date_str, GIT_COMMITTER_DATE: commit_date_str})` to relocate it into `implementations/done/` with the controlled date.
2. **Fixture reuse** — use the existing `temp_git_repo` fixture (creates
   `implementations/done/` on disk) and `monkeypatch.chdir(temp_git_repo)` inside each test
   so the detector scans the temp repo.
3. **Test: recent archive with a stale row is reported** — place a procedure whose
   `### Execution Status` has a `Pending` row into `implementations/done/` with a recent
   date (e.g. `now - 1 day` in ISO-8601), invoke the detector, assert the filename appears
   in captured stdout and nothing about "no findings" is printed.
4. **Test: recent archive with all rows completed is not reported** — same placement but
   with a `Completed` row; assert the recent file does NOT appear and a "no findings" style
   message is present.
5. **Test: old archive with a stale row is not reported** — place a `Pending`-row procedure
   with an old date (e.g. `now - 30 days`); assert it does NOT appear in output.
6. **Test: no file is moved / read-only** — after running the detector, assert the temp
   repo's working tree is unchanged (no new commits beyond the placement commits, files
   remain at their `implementations/done/` paths) and the return code / exit is 0.
7. **Invocation** — call the detector via `manage_main(["detect-unexecuted-archive"])`
   (imported already as `manage_main`), or `cmd_detect_unexecuted_archive(args)` with an
   `argparse.Namespace(days=N)` built to mirror the parser defaults; prefer
   `manage_main` so the full argv/subcommand path is exercised.

### Method
- Append the four tests and the `_place_done_file` helper to the end of the module; do not
  modify existing tests or fixtures.
- Keep each test focused on one assertion group; use descriptive names prefixed
  `test_detect_unexecuted_archive_*`.

### Details
- Date format for `GIT_AUTHOR_DATE`/`GIT_COMMITTER_DATE`: ISO-8601 UTC strings such as
  `2026-10-07T12:00:00`, or `now - 1 day` arithmetic via `datetime.now() - timedelta`.
- For the "recent" case pick a date inside the default 7-day window; for "old" pick a date
  outside it. Do not hard-code against a specific clock by using relative offsets.
- If invoking `cmd_*` directly instead of `manage_main`, construct the args namespace with
  the same attribute names the command reads (`args.days`).
- The detector must not create commits; if a test observes a new commit, the command is
  violating its read-only contract and the test should fail.

## Compatibility considerations
- Additive: new tests and one helper; no existing test is altered, so existing coverage is
  preserved.

## Security considerations
N/A: tests operate in an isolated temp repo with no real files or history.

## Rollback considerations
N/A: revert the commit.

## Validation plan
- Run `uv run pytest tests/tools/test_manage_workitem_stage.py` — all existing and new
  tests pass.
- Confirm the four detector assertions cover: recent+stale reported, recent+completed not
  reported, old+stale not reported, and no file moved / exit 0.

## Completion criteria
The module contains tests that, over a temporary repository with simulated archive dates,
assert the detector reports a recent stale archive, stays silent on a recent completed
archive and on an old stale archive, never moves a file, and exits 0; existing tests still
pass.

## Out of Scope
- Implementing the detector itself (its own row covers `tools/manage_workitem_stage.py`).
- Editing any other test module.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Add the `_place_done_file` helper and date-simulation approach | Pending | — | — | |
| 2 | Add the four detector assertions (recent/stale, recent/completed, old/stale, read-only) | Pending | — | — | |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |

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
- **Requirement ID**: `REQ-002` — add detector tests over a temporary repository
- **Source issue**: `issues/20261106-123521_procarch001_archive-procedures-only-after-execution.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261107-121954_procarch001_archive-procedures-only-after-execution.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261107-125900
- **Related target files**: `tests/tools/test_manage_workitem_stage.py`
