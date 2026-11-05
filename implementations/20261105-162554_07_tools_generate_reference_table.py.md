## Goal
- Give `tools/generate_reference_table.py` a `main(argv=None) -> int` entry that contains its current argument handling, with the `__main__` block reduced to `sys.exit(main())` and unchanged behavior, exit codes, and output (`REQ-004`: `main()` and unchanged behavior; `REQ-005`: no hook or CI change).

## Scope
**Release unit**: N/A: not part of a release unit

- In scope: `tools/generate_reference_table.py` only: move the inline parser and dispatch of the `__main__` block (lines 974-1060) into `main`, split into small helpers.
- Plan: `plans/20261105-105637_toolcli001_define-cli-and-exit-code-convention.md`, Plan step 4 (Phase 4).

## Assumptions
- The block builds the parser inline and uses `raise SystemExit(1)` (line 1008) and `raise SystemExit(0)` (lines 1010 and 1040) inside the `--check` and `--manifests` branches, `parser.error(...)` (exit `2`) at lines 1016 and 1043, and falls through with no explicit exit after a normal run (verified 2026-11-05). In `main` those become `return 1`, `return 0`, and a final `return 0`; `parser.error` keeps exiting `2`.
- Callers use only `--check`, `--manifests`, `--type`, and `--dry-run`: the CI steps (`uv run python tools/generate_reference_table.py --check` and `--manifests`), the `manifest-check` pre-commit hook (`python -m tools.generate_reference_table --check`), the `generate_reference_table_*` gates, and `routing.md` (verified 2026-11-05). No in-process caller exists (no test references `main`), so `main(None)` uses `sys.argv[1:]`.
- The file is 42,997 B, above the 24576 B limit, which gates `scripts/` only; the extraction keeps the size roughly unchanged and splitting stays with the `toolsizegate001` Plan.
- A single `main` holding the whole dispatch would grade D under `radon cc` (about 25 branches), so the dispatch is split into helpers; the grade C functions `_config_ownership_entries` (17), `_health_contract_entries` (14), and `_invariant_coverage_entries` (12) are not touched.
- Plan overlap: no other open Plan targets this file.

## Design decisions
- `_build_parser` (new) returns the existing `ArgumentParser` with the same four options and help texts; `_run_check` (new) returns the `--check` exit code; `_run_manifests` (new) takes the parsed arguments and the parser and returns `0`; `_run_domain` (new) handles the single-domain path; `main(argv: list[str] | None = None) -> int` parses with `parser.parse_args(argv)` and dispatches in the same order as today (`--check`, then `--manifests`, then `--type`).
- The `__main__` block becomes `sys.exit(main())`.

## Alternatives considered
- Leaving the whole dispatch in `main`: rejected, it would add a grade D function to a file whose grade C functions are already a known cost.

## Implementation
### Target file
`tools/generate_reference_table.py`

### Procedure
1. Extract the parser construction into `_build_parser` (new) without changing any option name, default, or help text.
2. Extract the `--check` branch into `_run_check` (new): same drift calls and printed lines, `return 1` where it raised `SystemExit(1)`, and `return 0` for `No drift found`.
3. Extract the `--manifests` branch into `_run_manifests` (new) and the final single-domain path into `_run_domain` (new), keeping every printed line and the `parser.error` calls.
4. Add `main` that builds the parser, parses `argv`, and returns the helper results; reduce the `__main__` block to `sys.exit(main())`.

### Method
- Move code without editing its statements, except `raise SystemExit(n)` becoming `return n`.
- Before editing, record the output and exit code of `uv run python tools/generate_reference_table.py --check` and of `--type mcp --dry-run`; compare after the change.

### Details
- Keep the order of the checks identical: `--check` wins over `--manifests`, which wins over `--type`.
- `parser.error` raises `SystemExit(2)`, so the manifests helper and the single-domain helper need the parser passed in.
- Do not move or rename any other function in the file.

## Compatibility considerations
- CI, the pre-commit hook, and the gates call the file by path or `-m` with the same flags; their output and exit codes must match the before-run.

## Security considerations
N/A: the write paths (`registry/manifests/` and the guarded doc blocks) are unchanged; do not run the writing modes except with `--dry-run` during checks.

## Rollback considerations
N/A: revert the commit; the checks above write nothing.

## Validation plan
- `uv run python tools/generate_reference_table.py --check` exits as before (`0`, `No drift found`); `uv run python tools/generate_reference_table.py --help` exits `0`.
- `uv run pytest tests/tools/test_generate_reference_table.py -q` passes.
- `uv run ruff format`, `uv run ruff check`, `uv run mypy tools/generate_reference_table.py`, `uv run bandit tools/generate_reference_table.py` are clean; `radon cc` shows no new function above grade B.

## Completion criteria
- `main` exists, the `__main__` block is `sys.exit(main())`, the before-and-after outputs and exit codes match, and the checks above are clean.

## Out of Scope
- Splitting the module, changing generators, manifests, or option names.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Record the before-run output and exit codes | Pending | — | — | |
| 2 | Extract the helpers and add `main` | Pending | — | — | |
| 3 | Run the validation sequence (`rules/toolchain.md`), the `radon` check, and the after-run comparison | Pending | — | — | |

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
- **Requirement ID**: `REQ-004` (`main()` and unchanged behavior), `REQ-005` (no hook or CI change)
- **Source issue**: issues/20261104-152002_toolcli001_define-cli-and-exit-code-convention.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261105-105637_toolcli001_define-cli-and-exit-code-convention.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261105-162554
- **Related target files**: `tools/generate_reference_table.py`
