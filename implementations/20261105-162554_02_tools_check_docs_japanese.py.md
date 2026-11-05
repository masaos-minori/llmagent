## Goal
- Give `tools/check_docs_japanese.py` an `argparse` entry so it answers `--help`, while `main()` keeps working without arguments and its behavior and exit codes stay identical (`REQ-003`: `--help` through `argparse`, no behavior change; `REQ-005`: no hook or CI change).

## Scope
**Release unit**: N/A: not part of a release unit

- In scope: `tools/check_docs_japanese.py` only: a `_parse_args` (new) helper, `main(argv)`, and the `__main__` call.
- Plan: `plans/20261105-105637_toolcli001_define-cli-and-exit-code-convention.md`, Plan step 3 (Phase 3).

## Assumptions
- Every caller passes no argument: the `docs-japanese` pre-commit hook (`python -m tools.check_docs_japanese`, `pass_filenames: false`) and the `check_docs_japanese` gate in `tools/run_validation_gates.py` (verified 2026-11-05).
- Existing tests call `main()` or the helper functions without arguments while `sys.argv` holds pytest's arguments; `argparse` with no argument would reject them (verified 2026-11-05: `parse_args()` under pytest exits 2), so the new helper must parse `[]` when it is given `None`.
- Plan overlap: no other open Plan targets this file.

## Design decisions
- The new helper (a function taking `argv: list[str] | None` and returning `argparse.Namespace`) builds `ArgumentParser(description=...)` from the first line of the module docstring, defines no option, and returns `parser.parse_args([] if argv is None else argv)`.
- `main(argv: list[str] | None = None) -> int` calls the new helper first and then runs the existing body unchanged; the `__main__` block becomes `sys.exit(main(sys.argv[1:]))`, which makes `--help` and unknown-flag handling reachable from the command line.

## Alternatives considered
N/A: the same pattern is applied to the four tools that take no argument today.

## Implementation
### Target file
`tools/check_docs_japanese.py`

### Procedure
1. Add `import argparse` next to the existing imports.
2. Add `_parse_args` (new) above `main`.
3. Change `main()` to `main(argv: list[str] | None = None)`, call the new helper as its first statement, and keep every later line unchanged.
4. Change the `__main__` block to `sys.exit(main(sys.argv[1:]))`.

### Method
- No existing exit code (`1` for a missing `docs/` directory or any Japanese file, `0` otherwise) changes.

### Details
- Do not add any option; the parser exists for `--help` and for rejecting unknown flags with exit `2`.
- Keep the module docstring's `Usage:` block as it is.

## Compatibility considerations
- The hook, the gate, and `main()` calls keep working because no caller passes an argument and `main()` parses `[]`.

## Security considerations
N/A: no new input is read; unknown arguments are rejected by `argparse`.

## Rollback considerations
N/A: revert the commit.

## Validation plan
- `uv run pytest tests/tools/test_check_docs_japanese.py -q` passes.
- `uv run python tools/check_docs_japanese.py --help` exits `0`; `uv run python tools/check_docs_japanese.py` exits as before on live data.
- `uv run ruff format`, `uv run ruff check`, `uv run mypy tools/check_docs_japanese.py`, `uv run bandit tools/check_docs_japanese.py` are clean (`routing.md` "Adding a new tool").

## Completion criteria
- `--help` exits `0`, `main()` without arguments gives the same result and exit code as before, and the checks above are clean.

## Out of Scope
- Changing the Japanese detection, its exit codes, or the hook configuration.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Add the argument-parsing helper and the `main(argv)` signature | Pending | — | — | |
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
- **Source plan**: plans/20261105-105637_toolcli001_define-cli-and-exit-code-convention.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261105-162554
- **Related target files**: `tools/check_docs_japanese.py`
