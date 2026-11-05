## Goal
- Give `tools/check_tool_descriptions_sync.py` an `argparse` entry so it answers `--help`, while `main()` keeps working without arguments (including through the `check-tool-descriptions` console script), with behavior and exit codes unchanged (`REQ-003`: `--help` through `argparse`, no behavior change; `REQ-005`: no hook or CI change).

## Scope
**Release unit**: N/A: not part of a release unit

- In scope: `tools/check_tool_descriptions_sync.py` only: a `_parse_args` (new) helper, the `main(argv)` signature, and the `__main__` call.
- Plan: `plans/done/20261105-105637_toolcli001_define-cli-and-exit-code-convention.md`, Plan step 3 (Phase 3).

## Assumptions
- Callers pass no argument: the `tool-descriptions-sync` pre-commit hook (`python -m tools.check_tool_descriptions_sync`, `pass_filenames: false`), the `check_tool_descriptions_sync` gate in `tools/run_validation_gates.py`, the `check-tool-descriptions` console script in `pyproject.toml`, and `routing.md` instructions (verified 2026-11-05).
- `tests/tools/test_check_tool_descriptions_sync.py` does not call `main` (no reference found), but the console script and in-process callers pass no `argv`, so `_parse_args(None)` parses `[]`.
- Plan overlap: this tool is the checker for the document the `toolsdocsync001` and `toolcli001` Plans edit; no other open Plan targets this file.

## Design decisions
- Same pattern as the sibling procedures: `_parse_args(argv: list[str] | None) -> argparse.Namespace` with no option and `parse_args([] if argv is None else argv)`; `main(argv=None)` calls it first; the `__main__` block becomes `raise SystemExit(main(sys.argv[1:]))`.

## Alternatives considered
N/A: same pattern as the sibling procedures.

## Implementation
### Target file
`tools/check_tool_descriptions_sync.py`

### Procedure
1. Add `import argparse`.
2. Add `_parse_args` (new) above `main`, using the first line of the module docstring as the description.
3. Change the signature to `main(argv: list[str] | None = None) -> int` and add `_parse_args(argv)` as the first statement.
4. Change the `__main__` block to `raise SystemExit(main(sys.argv[1:]))`.

### Method
- Keep the checks (`undocumented`, `stale`, `dangling`), the printed lines, and the returns (`1` for a missing document or any error, `0` otherwise) unchanged.

### Details
- Do not change `_BACKTICKED_PY_RE`, `_CONFIG_TOOL_REF_RE`, or `_EXEMPT`.

## Compatibility considerations
- The hook, the gate, the console script, and `main()` calls keep working because no caller passes an argument and `main()` parses `[]`.

## Security considerations
N/A: no new input is read.

## Rollback considerations
N/A: revert the commit.

## Validation plan
- `uv run pytest tests/tools/test_check_tool_descriptions_sync.py -q` passes.
- `uv run python tools/check_tool_descriptions_sync.py --help` exits `0`; `uv run python tools/check_tool_descriptions_sync.py` prints `No issues found.` and exits `0`.
- `uv run ruff format`, `uv run ruff check`, `uv run mypy tools/check_tool_descriptions_sync.py`, `uv run bandit tools/check_tool_descriptions_sync.py` are clean.

## Completion criteria
- `--help` exits `0`, `main()` without arguments behaves as before, and the checks above are clean.

## Out of Scope
- The sync checks themselves and the document the checker reads.

## Adversarial Verification (20261106)
- Applied `rules/ai-execution.md` Adversarial Verification (Base). Claims treated as unverified; checked `tools/check_tool_descriptions_sync.py`, `tests/tools/test_check_tool_descriptions_sync.py`, `.pre-commit-config.yaml`, `pyproject.toml`, `tools/run_validation_gates.py`, `routing.md`, and the open plans referencing this tool.
- Claim 1 (callers pass no argument: `tool-descriptions-sync` hook `pass_filenames: false`; gate in `run_validation_gates.py`; `check-tool-descriptions` console script in `pyproject.toml`; `routing.md`): CONFIRMED. Hook entry `python -m tools.check_tool_descriptions_sync` with `pass_filenames: false` (`pyproject.toml:185` console script, `run_validation_gates.py:844` gate).
- Claim 2 (test does not call `main`; console/in-process callers pass no `argv`, so `_parse_args(None)` parses `[]`): CONFIRMED. `grep -c main tests/tools/test_check_tool_descriptions_sync.py` == 0.
- Claim 3 (no other open Plan targets this file): CONFIRMED. The four open plans mentioning this tool (`toolsizegate001`, `toolcommon001`, `toolwrite001`, `toolreport001`) cite `check_tool_descriptions_sync.py` only as a **validation command to run**; their `Implementation Target Files` target `tools/TOOL_DESCRIPTIONS.md`, never the checker script itself.
- Detail check: `argparse` is not yet imported (count 0) and `main()` takes no argument — consistent with Step 1.
- Deliverable state: implementation steps remain `Pending` (not executed under this verify-only task). No behavioral claim is stale.
- Gates: `pytest` -> 3 passed; `ruff check` clean; `mypy` -> no issues; live run -> `No issues found.`.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Add `_parse_args` and the `main(argv)` signature | Pending | — | — | |
| 2 | Update the existing tests only if one breaks; otherwise record `N/A: no test change needed` | Pending | — | — | |
| 3 | Run the validation sequence (`rules/toolchain.md`) and a before-and-after run on live data | Pending | — | — | |

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
- **Requirement ID**: `REQ-003` (`--help` through `argparse`), `REQ-005` (no hook or CI change)
- **Source issue**: issues/20261104-152002_toolcli001_define-cli-and-exit-code-convention.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/done/20261105-105637_toolcli001_define-cli-and-exit-code-convention.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261105-162554
- **Related target files**: `tools/check_tool_descriptions_sync.py`
