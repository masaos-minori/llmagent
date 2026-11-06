## Goal
- Give `tools/check_needs_confirmation_inventory.py` an `argparse` entry so it answers `--help`, while `main()` keeps working without arguments (including through the `check-needs-confirmation` console script), with behavior and exit codes unchanged (`REQ-003`: `--help` through `argparse`, no behavior change; `REQ-005`: no hook or CI change).

## Scope
**Release unit**: N/A: not part of a release unit

- In scope: `tools/check_needs_confirmation_inventory.py` only: a `_parse_args` (new) helper, the `main(argv)` signature, and the `__main__` call.
- Plan: `plans/done/20261105-105637_toolcli001_define-cli-and-exit-code-convention.md`, Plan step 3 (Phase 3).

## Assumptions
- Callers pass no argument: the `check-needs-confirmation` console script in `pyproject.toml` calls `tools.check_needs_confirmation_inventory:main`, `.github/workflows/governance-docs-consistency.yml` and the `check_needs_confirmation_inventory` gate run it by path, and `tests/tools/test_check_needs_confirmation_inventory.py` calls `mod.main()` while `sys.argv` holds pytest's arguments, so `_parse_args(None)` must parse `[]` (verified 2026-11-05).
- `main` ends with `return report_and_exit(all_issues)`, which keeps the "warnings do not fail, errors do" contract in the module docstring; it is not changed.
- Plan overlap: no other open Plan targets this file.

## Design decisions
- Same pattern as the sibling procedures: `_parse_args(argv: list[str] | None) -> argparse.Namespace` with no option and `parse_args([] if argv is None else argv)`; `main(argv=None)` calls it first; the `__main__` block becomes `raise SystemExit(main(sys.argv[1:]))`.

## Alternatives considered
N/A: same pattern as the sibling procedures.

## Implementation
### Target file
`tools/check_needs_confirmation_inventory.py`

### Procedure
1. Add `import argparse` (check whether it is already imported first).
2. Add `_parse_args` (new) above `main`, using the first line of the module docstring as the description.
3. Change the signature to `main(argv: list[str] | None = None) -> int` and add `_parse_args(argv)` as the first statement.
4. Change the `__main__` block to `raise SystemExit(main(sys.argv[1:]))`.

### Method
- Keep every existing return and the order of the check calls unchanged.

### Details
- `_parse_inventory_entries` (grade C 14) and `check_untracked_inline_markers` (grade C 11) are not touched.

## Compatibility considerations
- The console script, the CI step, the gate, and `main()` calls keep working because no caller passes an argument and `main()` parses `[]`.

## Security considerations
N/A: no new input is read.

## Rollback considerations
N/A: revert the commit.

## Validation plan
- `uv run pytest tests/tools/test_check_needs_confirmation_inventory.py -q` passes.
- `uv run python tools/check_needs_confirmation_inventory.py --help` exits `0`; a run on live data prints the same report and exits as before.
- `uv run ruff format`, `uv run ruff check`, `uv run mypy tools/check_needs_confirmation_inventory.py`, `uv run bandit tools/check_needs_confirmation_inventory.py` are clean.

## Completion criteria
- `--help` exits `0`, `main()` without arguments behaves as before, and the checks above are clean.

## Out of Scope
- The inventory checks and the console script definition.

## Adversarial Verification (20261106)
- Applied `rules/ai-execution.md` Adversarial Verification (Base). Claims treated as unverified; checked `tools/check_needs_confirmation_inventory.py`, `tests/tools/test_check_needs_confirmation_inventory.py`, `pyproject.toml`, `.github/workflows/governance-docs-consistency.yml`, `tools/run_validation_gates.py`, and parent plan `plans/done/20261105-105637_toolcli001_define-cli-and-exit-code-convention.md`.
- Claim 1 (callers pass no argument: `check-needs-confirmation` console script `tools.check_needs_confirmation_inventory:main` in `pyproject.toml`; CI by path; tests call `mod.main()` under pytest's `sys.argv`, so `_parse_args(None)` must parse `[]`): CONFIRMED. Console script present (`pyproject.toml:184`); CI runs by path (`python tools/check_needs_confirmation_inventory.py`); tests import `as mod` and call `mod.main()` with no argument.
- Claim 2 (`main` ends with `return report_and_exit(all_issues)`, keeping "warnings do not fail, errors do"): CONFIRMED. `report_and_exit` (`tools/_docs_consistency_lib.py`) returns `1` only on ERROR, else `0`.
- Claim 3 (no other open Plan targets this file): CONFIRMED. Only the parent `toolcli001` Plan references this file; archived in `plans/done/`.
- Detail check: `argparse` is not yet imported (count 0) and `main()` takes no argument — procedure Step 1's "check whether it is already imported first" is consistent.
- Deliverable state: implementation steps remain `Pending` (not executed under this verify-only task). No behavioral claim is stale.
- Gates: `pytest` -> 32 passed; `ruff check` clean; `mypy` -> no issues.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Add `_parse_args` and the `main(argv)` signature | Completed | 20261106-112509 | 20261106-112839 | Changed: tools/check_needs_confirmation_inventory.py (_parse_args, main(argv), __main__ passes argv) |
| 2 | Update the existing tests only if one breaks; otherwise record `N/A: no test change needed` | Completed | 20261106-112839 | 20261106-112839 | N/A: no test change needed; existing tests pass |
| 3 | Run the validation sequence (`rules/toolchain.md`) and a before-and-after run on live data | Completed | 20261106-112839 | 20261106-112839 | ruff, mypy, bandit clean; --help exit 0, unknown flag exit 2; behavior and exit codes unchanged on live data |

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
- **Related target files**: `tools/check_needs_confirmation_inventory.py`
