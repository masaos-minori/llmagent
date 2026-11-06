## Goal
Make `tools/run_validation_gates.py` use the shared helper for its git diff call and its one local repository-root copy, with identical behavior (`REQ-003`; `REQ-004`: batch 2).

## Scope
**Release unit**: N/A: not part of a release unit

- In scope: `_git_diff_name_only`, the `repo_root` line in `_run_drift`, and the import block.
- Out of scope: the gate table, `_subprocess_runner` (it runs gates, not git), `classify`, and any size-gate wiring (owned by the `toolsizegate001` Plan, which depends on this Plan's phase 3).

## Assumptions
- Verified on 2026-11-06 (Step 3a): `_git_diff_name_only(extra_args)` runs `git diff --name-only <extra_args>` in the process working directory with `capture_output=True, text=True, check=False`, raises `RuntimeError(f"git diff failed (exit {n}): {stderr.strip()}")` on a non-zero exit, and returns stripped non-empty lines. `_run_drift` computes `repo_root = Path(__file__).resolve().parent.parent` (a local root copy not named `REPO_ROOT`). The file has no bootstrap and imports `yaml` (third party). `subprocess` stays imported for `_subprocess_runner`. The gate table entry `("git", "diff")` is a gate command, not a wrapper, and stays.
- Callers: pre-commit `uv run python -m tools.run_validation_gates drift` and by-path use from `routing.md`; both forms MUST keep working. `tests/tools/test_run_validation_gates.py` uses an injected runner and its own `REPO_ROOT`; it does not patch `_git_diff_name_only`, so no test edit is needed.
- Overlap judgment: the `toolsizegate001` Plan also targets this file (gate-table entries, different code) and depends on this Plan's phase 3; sequencing dependency, compatible. The earlier `toolmypy001` Plan is archived.

## Design decisions
- Keep `cwd=None` (process working directory) for `_git_diff_name_only`, since the tool is documented to run from the repository root and today inherits the caller's directory.
- Replace `repo_root` in `_run_drift` with the imported `REPO_ROOT`.

## Alternatives considered
- Passing `cwd=REPO_ROOT` to the diff call: rejected, it changes behavior when the tool is run from another directory.

## Implementation
### Target file
`tools/run_validation_gates.py`

### Procedure
1. Add the guarded bootstrap and `from tools._tool_common import REPO_ROOT, run_git` after the stdlib and `yaml` imports (ruff `I` decides the order).
2. In `_git_diff_name_only` replace the `subprocess.run([...])` call with `run_git("diff", "--name-only", *extra_args)`; keep the returncode check, the `RuntimeError` message, and the return expression.
3. In `_run_drift` delete the `repo_root = Path(__file__)...` line and use `REPO_ROOT` in the two reads.
4. Keep `import subprocess` and `from pathlib import Path` only if still used (`_SELF_CHECKER_ID` uses `Path(__file__).stem`, so `Path` stays).

### Method
- Text mode returns `str` stdout and stderr, so `proc.stderr.strip()` and `proc.stdout.splitlines()` stay valid.

### Details
- This file is the gate entry point: after the change run both `uv run python tools/run_validation_gates.py drift` and a plain `uv run python tools/run_validation_gates.py` to prove the gates still run.
- `_validate_ref` stays the guard for refs before they reach `run_git`.

## Compatibility considerations
- Gate selection, summaries, and exit codes are unchanged; `-m` and by-path forms keep working.

## Security considerations
- N/A: refs are validated by `_validate_ref` first and passed as list elements; no shell.

## Rollback considerations
- N/A: revert the commit.

## Validation plan
- `uv run pytest tests/tools/test_run_validation_gates.py -q`, then `uv run pytest tests/tools -q`.
- Before and after on live data: `uv run python tools/run_validation_gates.py` and `... drift` — compare exit code and the summary lines.
- Both forms: `uv run python -m tools.run_validation_gates drift` and `uv run python tools/run_validation_gates.py drift`.
- `routing.md` "Adding a new tool" steps 1-3 for this file.

## Completion criteria
- No `subprocess.run` of git and no `Path(__file__).resolve().parent.parent` root resolution (other than the bootstrap) remain; existing tests pass unchanged; live-data exit code and summary are identical before and after; both invocation forms work.

## Out of Scope
- Gate table changes, size-gate wiring, the other seven tools.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Capture the before-run on live data, then apply Implementation > Procedure | Completed | 20261106-095206 | 20261106-095236 | Changed: tools/run_validation_gates.py (bootstrap, _git_diff_name_only via run_git, _run_drift uses REPO_ROOT; subprocess kept for the gate runner) |
| 2 | Run the existing tests (no test edit expected) per Validation plan | Completed | 20261106-095236 | 20261106-095236 | existing tests pass (56); no test edit needed |
| 3 | Run the validation sequence (`rules/toolchain.md`) and the after-run comparison | Completed | 20261106-095236 | 20261106-095236 | ruff, mypy clean; bandit shows only pre-existing low findings of the gate runner; drift output identical before/after in -m, by-path, and other-cwd forms; tool_descriptions_sync fails until procedure 12 (known interim) |
| 4 | N/A: documentation is the `tools/TOOL_DESCRIPTIONS.md` procedure of this Plan | Completed | 20261106-095236 | 20261106-095236 | N/A: documentation is the tools/TOOL_DESCRIPTIONS.md procedure of this Plan |

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
- **Requirement ID**: `REQ-003` (use the helper), `REQ-004` (batch 2)
- **Source issue**: issues/20261104-152002_toolcommon001_shared-helper-for-tools.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261105-105811_toolcommon001_shared-helper-for-tools.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261106-090444
- **Related target files**: `tools/run_validation_gates.py`
