## Goal
Add `--dry-run` to `tools/migrate_runtime_tool_calls.py` and write its output atomically through the shared helper, with the same exit code as the real run (`REQ-004`, and the related requirements; Plan phase 3).

## Scope
**Release unit**: N/A: not part of a release unit

- In scope: the write in `_migrate`, the `--dry-run` option, and the import block; the companion test.
- Out of scope: rewrite rules and every other option.

## Assumptions
- Verified on 2026-11-06 (Step 3a): `_migrate(path)` rewrites test-file source, refuses to write on a `SyntaxError` (prints `refusing to write (syntax error: ...)` to stderr and returns `1`), otherwise calls `path.write_text(new_src)` without an encoding and prints `calls=... renamed=... kept_strict=...`; `main()` has no `argv` parameter, builds an `argparse` parser with `paths`, and returns `1` when any `_migrate` returns non-zero. `_migrate` is radon grade D (23) (Plan baseline); the change MUST NOT raise it, so only a `dry_run` parameter and the write call change. No test references the tool today (checked with `rg`).
- Companion test: `tests/tools/test_migrate_runtime_tool_calls.py` (new file, no test exists today); it is a valid companion because only this row names it in `Related Tests`.
- The tool has no `sys.path` bootstrap, so it gains the guarded bootstrap to import `tools._atomic_write` when run by path. The helper is `tools/_atomic_write.py` (created by the earlier-`seq` sibling procedure of this Plan). No other open Plan targets this file.

## Design decisions
- The real and dry paths share the same computation and differ only at the write call, so the exit codes cannot diverge (Plan Risks).
- Dry run calls `print_dry_run(path, old_text, new_text)`; the real run calls `atomic_write_text`.

## Alternatives considered
N/A: pattern fixed by the Plan.

## Implementation
### Target file
`tools/migrate_runtime_tool_calls.py`

### Procedure
1. Add the guarded bootstrap `if __package__ in (None, ""): sys.path.insert(0, str(Path(__file__).resolve().parent.parent))` (verify `sys` and `Path` are imported) and `from tools._atomic_write import add_dry_run_argument, atomic_write_text, print_dry_run` to the imports.
2. Give `main` an `argv: list[str] | None = None` parameter (`parser.parse_args(argv)`, `__main__` unchanged) and call `add_dry_run_argument(parser)`.
3. Add a `dry_run: bool = False` parameter to `_migrate`; replace `path.write_text(new_src)` with `print_dry_run(path, src, new_src)` under dry run and `atomic_write_text(path, new_src)` otherwise (explicit UTF-8, `REQ-006`). Keep the `compile` check before either path.

### Method
- The original text is already held in the local `src` (read with `path.read_text()`); reuse it for the diff.

### Details
- The syntax-error refusal and its exit code `1` apply in dry-run mode too, so both modes return the same code.

### Companion test files
- `tests/tools/test_migrate_runtime_tool_calls.py` (new)
  - Procedure: add a new test file: `--dry-run` leaves the file byte-identical and returns the real run's code, the real run writes UTF-8 bytes for non-ASCII source, and a source that would not compile is refused (return `1`, file unchanged) in both modes.
  - Validation: `uv run pytest tests/tools/test_migrate_runtime_tool_calls.py -q`.

## Compatibility considerations
- Default behavior, output, and exit codes without `--dry-run` are unchanged; `--dry-run` is new and additive.

## Security considerations
N/A: local files only.

## Rollback considerations
N/A: revert the commit.

## Validation plan
- `uv run pytest tests/tools/test_migrate_runtime_tool_calls.py -q`, then `uv run pytest tests/tools -q`.
- Before and after on live data: run the tool with `--dry-run` and for real on a temporary copy of a test file that uses `build_runtime_tool`.
- `routing.md` "Adding a new tool" steps 1-3 for the changed files, then `uv run python tools/run_validation_gates.py`.

## Completion criteria
- `--dry-run` writes no file (checksum test) and returns the real run's exit code; the real run writes through the helper with explicit UTF-8; no `Path.write_text` call remains in `tools/migrate_runtime_tool_calls.py`; tests pass.

## Out of Scope
- Rewrite rules, other tools.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Add the dry-run test first (fails until step 2) per Companion test files | Pending | — | — | |
| 2 | Add `--dry-run` and the helper write per Implementation > Procedure | Pending | — | — | |
| 3 | Run the validation sequence (`rules/toolchain.md`) and the live-data comparison | Pending | — | — | |
| 4 | N/A: documentation is the `tools/TOOL_DESCRIPTIONS.md` procedure of this Plan | Pending | — | — | |

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
- **Requirement ID**: `REQ-004`, `REQ-006`, `REQ-007`
- **Source issue**: issues/20261104-152906_toolwrite001_make-mutating-tools-dry-run-and-atomic.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261105-110212_toolwrite001_make-mutating-tools-dry-run-and-atomic.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261106-092109
- **Related target files**: `tools/migrate_runtime_tool_calls.py`, `tests/tools/test_migrate_runtime_tool_calls.py`
