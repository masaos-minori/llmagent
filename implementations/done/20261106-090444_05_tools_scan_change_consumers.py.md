## Goal
Make `tools/scan_change_consumers.py` use the shared helper for its repository root and `git ls-files`, with identical behavior (`REQ-003`; `REQ-004`: batch 1).

## Scope
**Release unit**: N/A: not part of a release unit

- In scope: the `ROOT_DIR` constant, `list_tracked_files`, and the import block.
- Out of scope: finders, categories, output, the `--root` option semantics.

## Assumptions
- Verified on 2026-11-06 (Step 3a): the file defines `ROOT_DIR = Path(__file__).resolve().parent.parent` (used as the `--root` default), has no bootstrap, and `subprocess` is used only by `list_tracked_files`, which runs `git ls-files -z` with `cwd=root`, bytes output, `check=False`, catches `OSError` into `SystemExit("cannot run git ls-files: ...")`, and raises `SystemExit("git ls-files failed in {root}: {stderr}")` on a non-zero exit.
- `tests/tools/test_scan_change_consumers.py` `TestListTrackedFiles` uses a real temporary repository and asserts the `git ls-files failed` message for a non-repository; it patches `scc.list_tracked_files` elsewhere, so the function name MUST stay. No test edit is needed.
- No Plan overlap names this file.

## Design decisions
- Keep `ROOT_DIR = REPO_ROOT` as an alias because the module-level name is used as the `--root` default and is a possible patch seam.
- Keep the error mapping at the call site: the helper only returns the process; the `SystemExit` messages stay here.

## Alternatives considered
- N/A: single call site.

## Implementation
### Target file
`tools/scan_change_consumers.py`

### Procedure
1. Add the guarded bootstrap and `from tools._tool_common import REPO_ROOT, run_git` (ruff `I` places it after `import orjson`).
2. Replace the `ROOT_DIR = Path(__file__)...` line with `ROOT_DIR = REPO_ROOT`.
3. In `list_tracked_files` replace the `subprocess.run(...)` call with `run_git("ls-files", "-z", cwd=root, binary=True)`; keep `except OSError` and both `SystemExit` messages.
4. Remove `import subprocess`.

### Method
- Bytes mode returns bytes for stdout and stderr, so `proc.stderr.decode(errors="replace")` and `proc.stdout.decode().split("\0")` stay as they are.

### Details
- `proc.stdout.decode()` stays strict UTF-8 as today; do not switch it to replacement.

## Compatibility considerations
- Output, the `--root` default, and the two error messages are unchanged.

## Security considerations
- N/A: fixed argv, `shell=False`.

## Rollback considerations
- N/A: revert the commit.

## Validation plan
- `uv run pytest tests/tools/test_scan_change_consumers.py -q`, then `uv run pytest tests/tools -q`.
- Before and after on live data: `uv run python tools/scan_change_consumers.py --seed scripts/shared/formatters.py` (a real seed) — compare exit code and output.
- `routing.md` "Adding a new tool" steps 1-3, then `uv run python tools/run_validation_gates.py`.

## Completion criteria
- No `subprocess` import, git runner, or `Path(__file__)` root resolution other than the bootstrap remains; existing tests pass unchanged; live-data exit code and output are identical before and after.

## Out of Scope
- Finder changes, new options, the other seven tools.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Capture the before-run on live data, then apply Implementation > Procedure | Completed | 20261106-095041 | 20261106-095058 | Changed: tools/scan_change_consumers.py (bootstrap, ROOT_DIR alias, list_tracked_files via run_git) |
| 2 | Run the existing tests (no test edit expected) per Validation plan | Completed | 20261106-095058 | 20261106-095058 | existing tests pass (26); no test edit needed |
| 3 | Run the validation sequence (`rules/toolchain.md`) and the after-run comparison | Completed | 20261106-095058 | 20261106-095058 | ruff, mypy, bandit clean; live scan output identical before/after; by-path --help OK from another cwd |
| 4 | N/A: documentation is the `tools/TOOL_DESCRIPTIONS.md` procedure of this Plan | Completed | 20261106-095058 | 20261106-095058 | N/A: documentation is the tools/TOOL_DESCRIPTIONS.md procedure of this Plan |

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
- **Related target files**: `tools/scan_change_consumers.py`
