## Goal
- Create `tests/tools/test_fill_affected_areas.py` to verify the tool of `tools/fill_affected_areas.py` on a temporary git repository (`REQ-001` to `REQ-005`: Change, Churn, Bus Factor, deploy impact, read-only and `--insert`, closed standard input).

## Scope
**Release unit**: N/A: not part of a release unit

- In scope: the new test module. It is its own document (not a companion) because `tools/TOOL_DESCRIPTIONS.md` also names it in `Related Tests`.
- Out of scope: the three-Plan comparison (`REQ-007`), which is a manual step recorded in the implementation report.

## Assumptions
- The tool module from the seq 01 procedure exists first; run the procedures in `seq` order.
- Test helpers build a temporary repository with `git init`, local `user.name`/`user.email` via `git -c`, and dated commits using `GIT_AUTHOR_DATE` and `GIT_COMMITTER_DATE`; no network.

## Design decisions
- Import as `import tools.fill_affected_areas as fa`, the same pattern as `tests/tools/test_amend_plan.py` (`import tools.amend_plan as ap`).
- A `_repo(tmp_path)` helper creates the repository and a `commit(path, author, date)` helper; a `_plan_text(rows)` helper writes a fixture Plan with `## Implementation Target Files`, `## Affected areas`, and one other section whose bytes must not change.

## Alternatives considered
- Mocking `subprocess.run`: rejected, the acceptance criteria are about real git behavior (stdin, dates, author names).

## Implementation
### Target file
`tests/tools/test_fill_affected_areas.py` (new)

### Procedure
1. Add the helpers above and one test per behavior below, each with a docstring-free, descriptive name.
2. Change mapping: parametrized `change_kind` cases (`Create`, `New file`, `generated` give `Create`; `Delete`, `remove the file` give `Delete`; `Edit the parser` gives `Modify`).
3. Churn: commits dated 5 and 60 days ago (set both dates); assert the count is 1 for `--since=30.days`.
4. Bus factor: authors `Alice` and `alice` (one person), then a share of exactly 70 percent gives `Low (70% top author)` and 75 percent gives `High (75% single author)`.
5. New, deleted, and history-less files: `Create` prints `N/A (new)` twice; a deleted file keeps its history values; an existing untracked file prints `N/A: no history`.
6. Deploy mapping: fixture `deploy/deploy.sh` lines; `scripts/x.py`, `tests/x.py`, `docs/x.md` give `not applicable (rsynced)`; `tools/x.py`, `skills/x.md` give `not applicable (not rsynced)`; `config/a.toml` Create, Delete, Modify with and without a cp line. One test asserts that the live `deploy/deploy.sh` still contains the rsync lines for `scripts/`, `tests/`, `docs/`, and `registry/`.
7. Size note: a `scripts/m.py` of known size prints bytes and headroom against 24576; a `tools/` target prints no note.
8. Read-only and insert: a default run leaves the Plan byte-identical; `--insert` changes only the `Affected areas` rows, keeps an existing `Blast Radius`, and appends a missing row; `--dry-run` prints a diff and writes nothing.
9. Standard input: run `fa.main` with `sys.stdin` replaced by a pipe that is never written and compare its output with a run on closed input.

### Method
- Use `monkeypatch.chdir`/`--root tmp_path` instead of the real repository; the live-repository test in step 6 reads only `deploy/deploy.sh`.
- Mark the temporary-git tests so they are skipped when `git` is absent (`shutil.which("git")`).

### Details
- Follow `rules/coding.md`: line length 88, English comments, type annotations on helpers.

## Compatibility considerations
- Test-only file; `tests/` is rsynced by `deploy/deploy.sh`, which is harmless. It depends on `tools.amend_plan` only through the tool under test.

## Security considerations
- N/A: no secrets; git identity is passed per command and no global git configuration is modified.

## Rollback considerations
- N/A: revert the commit.

## Validation plan
- `uv run pytest tests/tools/test_fill_affected_areas.py -q`
- `uv run ruff format tests/tools/test_fill_affected_areas.py`, `uv run ruff check tests/tools/test_fill_affected_areas.py`, `uv run mypy tests/tools/test_fill_affected_areas.py`
- `uv run python tools/check_mock_patch_targets.py` if any `patch` is used.

## Completion criteria
- Each Plan acceptance criterion AC-1 to AC-6 is covered by at least one passing test; the suite runs without network and without touching the real repository state.

## Out of Scope
- The `REQ-007` comparison on live Plans; any change to `tools/fill_affected_areas.py` beyond what a failing test proves necessary (that would be a procedure amendment for seq 01).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Create `tests/tools/test_fill_affected_areas.py` with the helpers and tests of Procedure | Completed | 20261127-090934 | 20261127-091109 | Needs seq 01 first Changed: tests/tools/test_fill_affected_areas.py (new, 22 tests pass); dates in the churn test must be monotonic |
| 2 | Run the tests and fix failures in the test or report a tool defect | Completed | 20261127-091109 | 20261127-091109 |  |
| 3 | Run ruff and mypy on the file | Completed | 20261127-091109 | 20261127-092340 | ruff, mypy pass; End-of-batch full suite: 15915 passed, 3 failed (tests/mcp_servers/git, pre-existing: same 3 fail on a clean HEAD worktree); diff-cover N/A: no scripts/ change |

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
- **Requirement ID**: `REQ-001`, `REQ-002`, `REQ-003`, `REQ-004`, `REQ-005` (behaviors under test)
- **Source issue**: issues/20261126-151440_wfeff005_affected-areas-tool.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261127-085326_wfeff005_affected-areas-tool.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261127-090100
- **Related target files**: `tests/tools/test_fill_affected_areas.py`