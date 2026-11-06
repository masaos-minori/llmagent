## Goal
Make `tools/check_adr_preservation.py` use the shared helper for its repository root and its git runner, with identical behavior (`REQ-003`; `REQ-004`: batch 3).

## Scope
**Release unit**: N/A: not part of a release unit

- In scope: the `REPO_ROOT` definition, `_git`, and the import block.
- Out of scope: comparison rules, finding levels, options, exit codes.

## Assumptions
- Verified on 2026-11-06 (Step 3a): the file already has the guarded bootstrap and `from tools._docs_consistency_lib import Issue, report_and_exit`; it defines `REPO_ROOT = Path(__file__).resolve().parent.parent` and `ADR_DIR = REPO_ROOT / "docs" / "10_adr"`; `_git(*args)` runs `git <args>` with `cwd=REPO_ROOT`, `text=True`, `check=False`, raises `RuntimeError(result.stderr.strip() or f"git {args} failed")` on a non-zero exit, and returns stdout; `_git` has two call sites (`changed_docs` and the `main` read of `git show {base}:{rel}`).
- `tests/tools/test_check_adr_preservation.py` imports only the pure functions (`compare`, `compare_generic`, `tokens`) and touches no git call, so no test edit is needed. The tool is called by path from skills and by `-m` from docs; neither pre-commit nor CI runs it by a `tools` path.
- No Plan overlap names this file.
- Repository-wide `REPO_ROOT` is imported by name from this module nowhere else (checked with `rg` over `tools/` and `tests/`), so keeping the name via import is safe.

## Design decisions
- Import `REPO_ROOT` and `run_git` from the helper; keep a five-line `_git` adapter because its `RuntimeError` message policy (stderr text, or a fallback message) is the call-site difference the Plan requires to be preserved. The adapter contains no `subprocess` call.

## Alternatives considered
- Inline `run_git(..., check=True)` at both call sites: rejected, it would change the exception type from `RuntimeError` to `CalledProcessError` and the message.

## Implementation
### Target file
`tools/check_adr_preservation.py`

### Procedure
1. Replace the local `REPO_ROOT = Path(__file__)...` line with an import: `from tools._tool_common import REPO_ROOT, run_git` placed after the existing `tools._docs_consistency_lib` import (the bootstrap above stays).
2. Rewrite `_git` as: call `run_git(*args, cwd=REPO_ROOT)`; if `returncode != 0` raise `RuntimeError(result.stderr.strip() or f"git {' '.join(args)} failed")`; return `result.stdout`.
3. Remove `import subprocess` and its `nosec B404` comment; remove the old `nosec B603 B607` line with the call.

### Method
- Text mode returns `stdout`/`stderr` as `str`, so `.strip()` and `.splitlines()` call sites are unchanged.

### Details
- `ADR_DIR` keeps referencing `REPO_ROOT`; no other symbol changes.

## Compatibility considerations
- Findings, exit codes, and error messages are unchanged; by-path and `-m` forms keep working through the existing bootstrap.

## Security considerations
- N/A: fixed git subcommands, `shell=False`; `base` comes from `--base` and is passed as a list element (it was before).

## Rollback considerations
- N/A: revert the commit.

## Validation plan
- `uv run pytest tests/tools/test_check_adr_preservation.py -q`, then `uv run pytest tests/tools -q`.
- Before and after on live data: `uv run python tools/check_adr_preservation.py` and `uv run python tools/check_adr_preservation.py --base HEAD~3` — compare exit code and output; also a bad `--base` value to confirm the error message is unchanged.
- Both forms: `uv run python -m tools.check_adr_preservation --help` and `uv run python tools/check_adr_preservation.py --help` (this is the Plan's "one tool in both forms" check for `REQ-005`).
- `routing.md` "Adding a new tool" steps 1-3, then `uv run python tools/run_validation_gates.py`.

## Completion criteria
- No `subprocess` import, `REPO_ROOT =` definition, or git runner remains in this file; existing tests pass unchanged; live-data output and exit code are identical before and after; both invocation forms print help.

## Out of Scope
- Comparison logic, the other seven tools.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Capture the before-run on live data, then apply Implementation > Procedure | Completed | 20261106-095242 | 20261106-095259 | Changed: tools/check_adr_preservation.py (REPO_ROOT and run_git from the helper; _git keeps its RuntimeError adapter) |
| 2 | Run the existing tests (no test edit expected) per Validation plan | Completed | 20261106-095259 | 20261106-095259 | existing tests pass (14); no test edit needed |
| 3 | Run the validation sequence (`rules/toolchain.md`) and the after-run comparison in both invocation forms | Completed | 20261106-095259 | 20261106-095259 | ruff, mypy, bandit clean; live text, --base HEAD~3 output identical, bad ref error identical; -m and by-path (repo and other cwd) --help OK |
| 4 | N/A: documentation is the `tools/TOOL_DESCRIPTIONS.md` procedure of this Plan | Completed | 20261106-095259 | 20261106-095259 | N/A: documentation is the tools/TOOL_DESCRIPTIONS.md procedure of this Plan |

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
- **Requirement ID**: `REQ-003` (use the helper), `REQ-004` (batch 3), `REQ-005` (one tool in both invocation forms)
- **Source issue**: issues/20261104-152002_toolcommon001_shared-helper-for-tools.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261105-105811_toolcommon001_shared-helper-for-tools.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261106-090444
- **Related target files**: `tools/check_adr_preservation.py`
