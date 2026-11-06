## Goal
Make `tools/classify_changes.py` read `git status` through the shared helper's bytes mode, with identical behavior (`REQ-003`; `REQ-004`: batch 1).

## Scope
**Release unit**: N/A: not part of a release unit

- In scope: `_read_status` and the import block of this file.
- Out of scope: grouping rules, options, output, and exit codes.

## Assumptions
- Verified on 2026-11-06 (Step 3a): `_read_status` runs `git status --porcelain=v1 -z` in the process working directory (no `cwd`), with `capture_output=True` and `check=False`, and decodes stderr itself with `errors="replace"` for the `RuntimeError` message. The file has no `REPO_ROOT`, no root constant, and no `sys.path` bootstrap; `subprocess` is used only there.
- `tests/tools/test_classify_changes.py` runs the tool against real temporary repositories (`monkeypatch.chdir`) and patches only `sys.stdin`; it does not patch the git call, so no test edit is needed. The tool is called by path from skills (`skills/git-commit-and-sync/workflow.md` Phase 2 per `routing.md`), never from pre-commit or CI.
- No Plan overlap names this file.

## Design decisions
- Call `run_git("status", "--porcelain=v1", "-z", binary=True)` with `cwd` left as `None`, because the tool relies on the caller's working directory.
- Keep the `RuntimeError` message text and the call-site stderr decoding unchanged.

## Alternatives considered
- N/A: single call site, no realistic alternative.

## Implementation
### Target file
`tools/classify_changes.py`

### Procedure
1. Add the guarded bootstrap and `from tools._tool_common import run_git` to the import block (the file has no bootstrap; by-path use needs it).
2. In `_read_status` replace the `subprocess.run(...)` call with `run_git("status", "--porcelain=v1", "-z", binary=True)`.
3. Keep the `proc.returncode != 0` branch and the `RuntimeError` message exactly; keep `return proc.stdout`.
4. Remove `import subprocess` and update the module docstring sentence "the only subprocess is the status read" only if it becomes inaccurate (it names the git status read, which still holds).

### Method
- Bytes mode returns `bytes` for stdout and stderr, so `proc.stderr.decode("utf-8", errors="replace")` stays valid.

### Details
- Do not add `REPO_ROOT` here; the tool never used one.
- `OSError` from a missing git still propagates as before (it was never caught).

## Compatibility considerations
- Output, exit codes (including exit 1 on partly staged or unmerged paths), and the `--status-file` paths are unchanged.

## Security considerations
- N/A: fixed argv, no user input reaches git.

## Rollback considerations
- N/A: revert the commit.

## Validation plan
- `uv run pytest tests/tools/test_classify_changes.py -q`, then `uv run pytest tests/tools -q`.
- Before and after on live data: `uv run python tools/classify_changes.py` — compare exit code and output on the same working tree.
- `routing.md` "Adding a new tool" steps 1-3 for this file, then `uv run python tools/run_validation_gates.py`.

## Completion criteria
- No `subprocess` import or git runner remains in this file; existing tests pass unchanged; live-data exit code and output are identical before and after; `uv run python tools/classify_changes.py --help` works from the repository root and from another directory.

## Out of Scope
- Grouping logic, new options, the other seven tools.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Capture the before-run on live data, then apply Implementation > Procedure | Completed | 20261106-095018 | 20261106-095039 | Changed: tools/classify_changes.py (bootstrap, run_git binary mode) |
| 2 | Run the existing tests (no test edit expected) per Validation plan | Completed | 20261106-095039 | 20261106-095039 | existing tests pass (25); no test edit needed |
| 3 | Run the validation sequence (`rules/toolchain.md`) and the after-run comparison | Completed | 20261106-095039 | 20261106-095039 | ruff, mypy, bandit clean; --status-file output identical before/after; live git status path runs; by-path --help OK from repo and another cwd |
| 4 | N/A: documentation is the `tools/TOOL_DESCRIPTIONS.md` procedure of this Plan | Completed | 20261106-095039 | 20261106-095039 | N/A: documentation is the tools/TOOL_DESCRIPTIONS.md procedure of this Plan |

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
- **Requirement ID**: `REQ-003` (use the helper), `REQ-004` (batch 1)
- **Source issue**: issues/20261104-152002_toolcommon001_shared-helper-for-tools.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261105-105811_toolcommon001_shared-helper-for-tools.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261106-090444
- **Related target files**: `tools/classify_changes.py`
