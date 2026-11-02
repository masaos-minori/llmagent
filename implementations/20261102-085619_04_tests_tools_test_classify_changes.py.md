## Goal
- Create the unit and temporary-repository tests for the classifier and for the documented split (`REQ-003`: classifier behavior; `REQ-001`: the split and rename-pair rule hold in real git).

## Scope
- In scope: a new `tests/tools/test_classify_changes.py`. Out of scope: any change to `tools/classify_changes.py` (row 03) or to other tests.

## Assumptions
- Step 3a verification: `tests/tools/` exists with one module per tool; tests import tools as `import tools.<name> as alias` and build temporary git repositories with `git init` (for example `tests/tools/test_manage_workitem_stage.py`); the file does not exist yet.
- The module under test and its names (`parse_porcelain_z` (new), `classify`, `render`, `verify_pathspec` (new), `main`, `Change`) are created by row 03 (earlier `seq`); the stale detector reports them until row 03 is executed, which is acceptable per the workflow.
- Real git is used for the end-to-end tests (no mocking of git); each test sets `user.name`, `user.email`, and `commit.gpgsign=false` inside its own temporary repository only, and no hook framework is installed there (the hook check is Plan step 1, a manual gate).
- Overlap (Step 2, `tools/check_plan_target_overlaps.py`, judged and recorded): no other Frozen Plan targets this new file. Judged compatible; see the Plan's Assumptions A6, A6b, and A7.
- Tool contract (shared by rows 01, 03, 04, 06, 07; row 03 owns the implementation):
  - Command: `uv run python tools/classify_changes.py [--status-file <path>] [--group <name> | --verify-pathspec <path> ...]`.
    Input is `git status --porcelain=v1 -z` bytes: read from `--status-file <path>` (`-` means stdin), otherwise obtained by running that exact git command in the current directory.
  - Groups, first match wins, in this print order: `artifacts` (`issues/`, `plans/`, `implementations/`, including `done/`), `code` (`scripts/`, `config/`, `deploy/`), `tests` (`tests/`), `tools` (`tools/`), `docs` (`docs/`, `skills/`, `rules/`, `templates/`, `prompts/`, `routing.md`, `AGENTS.md`, `CLAUDE.md`), `other`.
  - Default output, one block per non-empty group: `[<group>]`, then `pathspec: <shell-quoted staged paths, rename pairs adjacent as new name then old name>`, then optional `unstaged: <paths with a working-tree-only change>` and `untracked: <paths>` lines (neither is part of the pathspec). A `warnings:` section follows when needed, with `WARN partly-staged: <path>`, `WARN unmerged: <path>`, and `NOTE cross-group-rename: <old> -> <new> (grouped under <new>)`.
  - Exit codes: 0 normal; 1 when any `partly-staged` or `unmerged` warning exists (or, with `--verify-pathspec`, when a candidate pathspec names only one name of a staged rename); 2 for a usage error or a failed git call.
  - `--group <name>` prints only that group's pathspec line value (empty output when the group is empty); `--verify-pathspec` reads the candidate paths and prints `split-rename: <path> needs <partner>` for each half-named pair.

## Design decisions
- Two layers: pure unit tests over fixture `-z` byte strings built by a small `_z(*entries)` helper, and end-to-end tests that run `git` in `tmp_path` repositories and then run `main()` through `--status-file` or a changed working directory (`monkeypatch.chdir`).
- The end-to-end split test follows the documented procedure literally, so the skill text and the test cannot drift unnoticed.

## Alternatives considered
- Mocking `subprocess.run`: rejected for the end-to-end layer, the point is real pathspec behavior; the unit layer already avoids git.

## Implementation
### Target file
`tests/tools/test_classify_changes.py` (new)

### Procedure
1. Create `tests/tools/test_classify_changes.py` (new) with the module docstring header used by sibling tests, `from __future__ import annotations`, and `import tools.classify_changes as cc`.
2. Add the unit tests, then the end-to-end tests listed under Method.
3. Run the new tests and the lint sequence on the test file.

### Method
Unit tests (fixture bytes):
- `test_parse_modification_and_unstaged` (new): `M  a.py` and ` M b.py` become staged and worktree-only changes.
- `test_parse_rename_keeps_both_names` (new): `R  new.md\0old.md\0` yields one `Change` with `orig_path == "old.md"`; the following entry is not swallowed.
- `test_parse_untracked_deleted_and_ignored` (new): `?? x`, `D  y`, ` D z`; `!! i` is skipped.
- `test_parse_rejects_short_entry` (new): a malformed token raises `ValueError`.
- `test_parse_unusual_names` (new): spaces, a single quote, and a non-ASCII name round-trip; `render` output quotes them with `shlex.quote`.
- `test_classify_groups` (new): one path per group including `other`, `routing.md` and `AGENTS.md` in `docs`, `tests/tools/x.py` in `tests` (not `tools`).
- `test_rename_pair_stays_in_one_group` (new) and `test_cross_group_rename_noted` (new): `scripts/a.py -> tools/a.py` is grouped under `tools` with both names in its pathspec and a `NOTE`.
- `test_partly_staged_flagged_and_exit_1` (new): MM and RM entries produce `WARN partly-staged`; `main` returns 1; a clean status returns 0.
- `test_unmerged_flagged` (new): UU entry produces `WARN unmerged`, exit 1.
- `test_untracked_and_unstaged_not_in_pathspec` (new).
- `test_verify_pathspec_refuses_half_pair` (new): only the new name of a rename gives a `split-rename` message and exit 1; both names give exit 0.
- `test_group_option_prints_only_that_pathspec` (new) and `test_unknown_group_exit_2` (new).
- `test_main_never_writes` (new): run `main` in a repository and assert the index and working tree are byte-identical before and after (compare `git status --porcelain=v1 -z` and `git ls-files -s`).
End-to-end tests (`tmp_path` repositories):
- `test_split_commits_two_groups` (new): commit a base with a `tools/` file and `plans/x.md`; edit the tool file and `git add` it; `git mv plans/x.md plans/done/x.md`; run the classifier; run `git commit -m "tools: change" -- <tools pathspec>` then `git commit -m "plan: archive" -- <artifacts pathspec>`; assert two new commits, each with only its group's paths, `git status --porcelain` empty, and `git show --name-status -M HEAD` showing `R100` for the rename.
- `test_commit_of_new_name_only_leaves_staged_deletion` (new): committing only `plans/done/x.md` leaves `D  plans/x.md` staged (the failure the rename rule prevents).
- `test_pathspec_commit_includes_unstaged_part_of_mm_path` (new): for an `MM` path the commit holds the working-tree content, and the classifier flagged it beforehand.

### Details
- Use a helper `_git(repo, *args)` running `subprocess.run(["git", *args], cwd=repo, check=True, capture_output=True)`; no shell.
- Keep each test independent; do not touch the real repository (use `tmp_path`, never `ROOT_DIR`), and do not install a pre-commit hook in the temporary repositories.

## Compatibility considerations
- New test module only; no fixtures shared with other tests; runs under the default `uv run pytest` selection.

## Security considerations
N/A: tests run git in temporary directories with static argument lists.

## Rollback considerations
N/A: new test file; revert the commit.

## Validation plan
- `uv run pytest tests/tools/test_classify_changes.py -v`: all pass.
- `uv run ruff format tests/tools/test_classify_changes.py`; `uv run ruff check tests/tools/test_classify_changes.py`; `uv run mypy tests/tools/test_classify_changes.py`.

## Completion criteria
- Unit tests cover modification, rename, untracked, deleted, partly staged, unmerged, and cross-group rename; end-to-end tests prove the two-commit split, the rename record, no staged leftovers, and the half-pair failure; all pass (`AC-3`, `AC-4`, `AC-5`).

## Out of Scope
- Changes to `tools/classify_changes.py`; testing the pre-commit hook interaction (a manual Plan gate); tests of `run_validation_gates.py` (the existing drift test covers rows 06 and 07).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Create `tests/tools/test_classify_changes.py` with the unit and end-to-end tests in Implementation > Method | Pending | — | — |  |
| 2 | Run the new tests and fix the tool or test per the failing assertion's owner (tool fixes are row 03's file) | Pending | — | — | a tool defect is a Plan Gap for row 03, not edited here |
| 3 | Run the validation sequence (`rules/toolchain.md`) for the test file | Pending | — | — |  |

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
- **Requirement ID**: `REQ-003`, `REQ-001`; acceptance `AC-3`, `AC-4`, `AC-5`
- **Source issue**: issues/20261030-191702_flowimp010_artifact-commit-split.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261102-081312_flowimp010_artifact-commit-split.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261102-085619
- **Related target files**: tests/tools/test_classify_changes.py
