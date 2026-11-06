## Goal
Make `tools/manage_binaries.py` run git through the shared helper while it keeps working when `deploy/*.sh` runs it by path with the system `python3` (`REQ-003`; `REQ-004`: batch 3; `REQ-005`: by-path invocation).

## Scope
**Release unit**: N/A: not part of a release unit

- In scope: `_git(repo, *args)` and the import block of this file.
- Out of scope: its own `EXIT_OK`, `EXIT_FAIL`, `EXIT_USAGE` constants (not unified in this Plan), `BINARY_SOURCES`, every subcommand's logic.

## Assumptions
- Verified on 2026-11-06 (Step 3a): `_git(repo, *args)` resolves git with `shutil.which("git")` (raising `RuntimeError("git executable not found")` when absent), runs `[git, "-C", str(repo), *args]` with `capture_output=True, text=True, check=False`, and raises `RuntimeError(f"git {' '.join(args)} failed: {stderr.strip()}")` on a non-zero exit. Its callers are `_head`, `_dirty`, `_changed_paths`, and further helpers in the same file. The file has no root constant and no bootstrap; `shutil` is still used elsewhere (`copy2`).
- Corrected by this pass: the by-path callers are not only `deploy/deploy.sh` (`swap`, `check`, `record-revision`) but also `deploy/build_binaries.sh` (`rollback`, `write-info`, `swap`) and `deploy/start_agent.sh` (`check`, twice, on the service start path). All run `python3 "${REPO_ROOT}/tools/manage_binaries.py"`, so `sys.path[0]` is `tools/` and `import tools._tool_common` only works after the guarded bootstrap.
- `tests/tools/test_manage_binaries.py` uses real temporary repositories through `mod.main(...)`, runs `bash -n` on the deploy scripts, and runs `build_binaries.sh --rollback`; it patches no git call, so no test edit is needed. The host's `python3` is 3.13 (checked with `python3 --version`); the file already needs `datetime.UTC` (3.11+).
- No Plan overlap names this file.

## Design decisions
- Keep `git -C <repo>` semantics: call `run_git("-C", str(repo), *args)` with `cwd=None`. Passing `cwd=repo` would turn a missing repository directory into `FileNotFoundError` instead of the current git exit-128 `RuntimeError`.
- Keep a short `_git` adapter (no `subprocess` call) so both `RuntimeError` messages stay identical; map `FileNotFoundError` from `run_git` to `RuntimeError("git executable not found")`.

## Alternatives considered
- Resolve git with `shutil.which` inside the helper: rejected, only this tool needs it, and the helper's policy stays uniform.

## Implementation
### Target file
`tools/manage_binaries.py`

### Procedure
1. After the stdlib imports add the guarded bootstrap `if __package__ in (None, ""): sys.path.insert(0, str(Path(__file__).resolve().parent.parent))` and `from tools._tool_common import run_git` (`sys` and `Path` are already imported).
2. Rewrite `_git(repo, *args)`: try `proc = run_git("-C", str(repo), *args)`; `except FileNotFoundError as exc: raise RuntimeError("git executable not found") from exc`; on `proc.returncode != 0` raise `RuntimeError(f"git {' '.join(args)} failed: {proc.stderr.strip()}")`; return `proc.stdout`.
3. Remove `import subprocess` and its `nosec B404` comment; keep `import shutil` (used elsewhere).

### Method
- The adapter preserves both failure messages; successful calls return the same `str`.

### Details
- Verify by path with the system interpreter, exactly as the scripts call it: `python3 tools/manage_binaries.py --help`, then a `check` run against a temporary repository (the test fixtures show the arguments).
- Run the `bash -n` parametrized deploy-script tests; do not run `deploy/deploy.sh` (deploying is the user's separate decision, `skills/deploy/SKILL.md`).

## Compatibility considerations
- Subcommand output and exit codes are unchanged; the five by-path callers in `deploy/*.sh` keep working through the bootstrap; `-m` and test-import forms are unaffected.

## Security considerations
- N/A: fixed git subcommands and list arguments, no shell. The bootstrap inserts only the repository root, the same idiom other tools already use.

## Rollback considerations
- This file runs on the deploy and service-start path: if a by-path smoke fails, revert this commit before any deploy. No data migration is involved.

## Validation plan
- `uv run pytest tests/tools/test_manage_binaries.py -q`, then `uv run pytest tests/tools -q`.
- By path with the system interpreter: `python3 tools/manage_binaries.py --help` and one read-only subcommand (`check`) against a temporary repository; compare exit code and output with the pre-change run.
- `routing.md` "Adding a new tool" steps 1-3, then `uv run python tools/run_validation_gates.py`.
- Record the `radon cc` grades for `_run`, `_check_binary`, and `swap` before and after; none may rise (Plan Design baseline: C, C, C).

## Completion criteria
- No `subprocess` import or `subprocess.run` of git remains; both failure messages are unchanged; by-path `python3` runs work for `--help` and `check`; existing tests pass unchanged; no `radon` grade rises.

## Out of Scope
- Unifying the local exit constants, changing any subcommand, deploying, the other seven tools.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Capture the by-path before-run and `radon` grades, then apply Implementation > Procedure | Completed | 20261106-095300 | 20261106-095334 | Changed: tools/manage_binaries.py (bootstrap, _git via run_git(-C repo) with both RuntimeError messages kept; subprocess import removed) |
| 2 | Run the existing tests (no test edit expected) per Validation plan | Completed | 20261106-095334 | 20261106-095334 | existing tests pass (21); no test edit needed |
| 3 | Run the validation sequence (`rules/toolchain.md`) and the by-path after-run with the system `python3` | Completed | 20261106-095334 | 20261106-095334 | ruff, mypy, bandit clean; radon grades of _run, _check_binary, swap unchanged (C 17, 11, 11); by-path smoke with system python3 on a temporary repo: --help, record-revision, check |
| 4 | N/A: documentation is the `tools/TOOL_DESCRIPTIONS.md` procedure of this Plan | Completed | 20261106-095334 | 20261106-095334 | N/A: documentation is the tools/TOOL_DESCRIPTIONS.md procedure of this Plan |

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
- **Requirement ID**: `REQ-003` (use the helper), `REQ-004` (batch 3), `REQ-005` (by-path invocation as the deploy scripts call it)
- **Source issue**: issues/20261104-152002_toolcommon001_shared-helper-for-tools.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261105-105811_toolcommon001_shared-helper-for-tools.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261106-090444
- **Related target files**: `tools/manage_binaries.py`
