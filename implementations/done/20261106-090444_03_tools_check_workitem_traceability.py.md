## Goal
Make `tools/check_workitem_traceability.py` use the shared helper for its repository root and its one git call, with identical behavior (`REQ-003`: no local git runner or root copy; `REQ-004`: batch 1 of three).

## Scope
**Release unit**: N/A: not part of a release unit

- In scope: the module-level root constant and `_git_or_mtime` in this file only.
- Out of scope: renderers, finding model, and `--format` (owned by the `toolreport001` Plan), companion-candidate scoping (archived `tracecompanion001` Plan).

## Assumptions
- Verified on 2026-11-06 (Step 3a): the file defines `ROOT_DIR = Path(__file__).resolve().parent.parent`, has no `sys.path` bootstrap, and `subprocess` is used only by `_git_or_mtime`. `tests/tools/test_check_workitem_traceability.py` patches `cwt.ROOT_DIR` through `monkeypatch.setattr`, so the module attribute `ROOT_DIR` MUST remain and MUST be read at call time.
- Callers: pre-commit runs `uv run python -m tools.check_workitem_traceability --active-only`; skills and docs call `uv run python tools/check_workitem_traceability.py` by path; tests import it as `tools.check_workitem_traceability`. All three forms MUST keep working.
- Overlap judgment: the `toolreport001` Plan also targets this file (renderers and finding model, different functions) and depends on this Plan's phase 2, so it is a sequencing dependency, compatible.
- The helper `tools/_tool_common.py` is created by the earlier-`seq` sibling procedure of this Plan.

## Design decisions
- Keep the name `ROOT_DIR` as an alias: `ROOT_DIR = REPO_ROOT`. It is not a second root resolution, and it keeps the test patch seam and every `ROOT_DIR` use site unchanged.
- Pass `cwd=ROOT_DIR` explicitly into `run_git` so the patched value is honored.

## Alternatives considered
- Rename every `ROOT_DIR` use to `REPO_ROOT`: rejected, it breaks the existing monkeypatch seam and widens the diff.

## Implementation
### Target file
`tools/check_workitem_traceability.py`

### Procedure
1. After the stdlib imports add the guarded bootstrap, then the helper import (ruff `I` ordering decides the exact placement; run `ruff check --fix`):
   `if __package__ in (None, ""): sys.path.insert(0, str(Path(__file__).resolve().parent.parent))` and `from tools._tool_common import REPO_ROOT, run_git`.
2. Replace the `ROOT_DIR = Path(__file__).resolve().parent.parent` line with `ROOT_DIR = REPO_ROOT`.
3. In `_git_or_mtime` replace the `subprocess.run(...)` call with `run_git("log", "-1", "--format=%ct", "--", str(path), cwd=ROOT_DIR, timeout=10)`; keep `except OSError` and the fallback to the file mtime unchanged.
4. Remove `import subprocess` and the long bandit comment block above the old call (the one `nosec` justification now lives in the helper).

### Method
- `run_git` text mode returns `stdout` as `str`; `output = result.stdout.strip()` and the `returncode == 0 and output.isdigit()` test stay as they are.
- `TimeoutExpired` is not caught today and stays uncaught.

### Details
- Behavior difference to record, not to fix: text decoding changes from the locale encoding to UTF-8 with replacement; the command only prints digits, so output is identical.
- Re-run `rg -n "subprocess|Path\(__file__\)" tools/check_workitem_traceability.py`: only the bootstrap line may match `Path(__file__)`.

## Compatibility considerations
- Output, exit codes, and the `ROOT_DIR` module attribute are unchanged; `-m`, by-path, and test-import forms keep working (the bootstrap covers by-path).

## Security considerations
- N/A: the git argv is fixed and the only variable is `str(path)` after `--`, passed as a list element with `shell=False`, as before.

## Rollback considerations
- N/A: revert the commit.

## Validation plan
- `uv run pytest tests/tools/test_check_workitem_traceability.py -q`, then `uv run pytest tests/tools -q` (batch gate).
- Before and after on live data: `uv run python tools/check_workitem_traceability.py --active-only` — compare exit code and output (stash the change for the "before" run or use `git stash`-free comparison by running from the previous commit's checkout).
- Both forms: `uv run python -m tools.check_workitem_traceability --help` and `uv run python tools/check_workitem_traceability.py --help`.
- `routing.md` "Adding a new tool" steps 1-3 for this file, then `uv run python tools/run_validation_gates.py`.

## Completion criteria
- `rg` finds no `subprocess` import, no `git` runner, and no `Path(__file__)` root resolution other than the bootstrap in this file.
- Existing tests pass unchanged; live-data exit code and output are identical before and after; both invocation forms print help.

## Out of Scope
- Any renderer or option change, the other seven tools, `tools/TOOL_DESCRIPTIONS.md`.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Capture the before-run on live data, then apply Implementation > Procedure | Completed | 20261106-094932 | 20261106-095017 | Changed: tools/check_workitem_traceability.py (bootstrap, helper import, ROOT_DIR alias, _git_or_mtime via run_git) |
| 2 | Run the existing tests (no test edit expected) per Validation plan | Completed | 20261106-095017 | 20261106-095017 | existing tests pass (87); no test edit needed |
| 3 | Run the validation sequence (`rules/toolchain.md`) and the after-run comparison | Completed | 20261106-095017 | 20261106-095017 | ruff, mypy, bandit clean; live --active-only output byte-identical before/after; -m, by-path, other-cwd --help OK; tool_descriptions_sync fails until procedure 12 (known interim) |
| 4 | N/A: documentation is the `tools/TOOL_DESCRIPTIONS.md` procedure of this Plan | Completed | 20261106-095017 | 20261106-095017 | N/A: documentation is the tools/TOOL_DESCRIPTIONS.md procedure of this Plan |

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
- **Related target files**: `tools/check_workitem_traceability.py`
