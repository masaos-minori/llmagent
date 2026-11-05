## Goal
- Give `tools/check_dependency_graph_cycles.py` an `argparse` entry so it answers `--help`, while `main()` keeps working without arguments, its behavior and exit codes stay identical, and the complexity grade of `main` does not worsen (`REQ-003`: `--help` through `argparse`, no behavior change; `REQ-005`: no hook or CI change).

## Scope
**Release unit**: N/A: not part of a release unit

- In scope: `tools/check_dependency_graph_cycles.py` only: a `_parse_args` (new) helper, the `main(argv)` signature, and the `__main__` call.
- Plan: `plans/20261105-105637_toolcli001_define-cli-and-exit-code-convention.md`, Plan step 3 (Phase 3).

## Assumptions
- `main` is graded C (16) by `radon cc` today (verified 2026-11-05), so the new parsing must live in the helper and `main` must gain no branch; a plain call `_parse_args(argv)` adds none.
- Callers pass no argument: the CI step in `.github/workflows/governance-docs-consistency.yml` runs `python tools/check_dependency_graph_cycles.py`; `tests/tools/test_check_dependency_graph_cycles.py` calls `cdgc.main()` while `sys.argv` holds pytest's arguments, so `_parse_args(None)` must parse `[]` (verified 2026-11-05).
- Plan overlap: no other open Plan targets this file.

## Design decisions
- Same pattern as the other four tools: `_parse_args(argv: list[str] | None) -> argparse.Namespace` with no option and `parse_args([] if argv is None else argv)`; `main(argv=None)` calls it first.
- The `__main__` block becomes `raise SystemExit(main(sys.argv[1:]))`, keeping its current exit mechanism.

## Alternatives considered
N/A: same pattern as the sibling procedures.

## Implementation
### Target file
`tools/check_dependency_graph_cycles.py`

### Procedure
1. Add `import argparse`.
2. Add `_parse_args` (new) above `main`, using the first line of the module docstring as the description.
3. Change the signature to `main(argv: list[str] | None = None) -> int` and add `_parse_args(argv)` as the first statement.
4. Change the `__main__` block to `raise SystemExit(main(sys.argv[1:]))`.

### Method
- Keep every existing return (`1` for a missing document, missing section, no edges, unknown nodes, or a cycle; `0` otherwise).

### Details
- Re-run `uv run radon cc tools/check_dependency_graph_cycles.py -s` and confirm `main` is still C (16) or better.
- Do not touch `parse_edges`, `find_cycle`, or the section constants.

## Compatibility considerations
- The CI step and `main()` calls keep working because no caller passes an argument and `main()` parses `[]`.

## Security considerations
N/A: no new input is read.

## Rollback considerations
N/A: revert the commit.

## Validation plan
- `uv run pytest tests/tools/test_check_dependency_graph_cycles.py -q` passes.
- `uv run python tools/check_dependency_graph_cycles.py --help` exits `0`; a run on live data prints the same line and exits `0` as before.
- `uv run ruff format`, `uv run ruff check`, `uv run mypy tools/check_dependency_graph_cycles.py`, `uv run bandit tools/check_dependency_graph_cycles.py` are clean; `radon` grade of `main` is not worse.

## Completion criteria
- `--help` exits `0`, `main()` without arguments behaves as before, and the checks above are clean.

## Out of Scope
- The cycle detection logic and the governance workflow.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Add `_parse_args` and the `main(argv)` signature | Pending | — | — | |
| 2 | Update the existing tests only if one breaks; otherwise record `N/A: no test change needed` | Pending | — | — | |
| 3 | Run the validation sequence (`rules/toolchain.md`), the `radon` check, and a before-and-after run on live data | Pending | — | — | |

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
- **Related target files**: `tools/check_dependency_graph_cycles.py`
