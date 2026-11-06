## Goal
Add `--dry-run` to `tools/fix_docs_section_marks.py` and write its output atomically through the shared helper, with the same exit code as the real run (`REQ-004`, and the related requirements; Plan phase 3).

## Scope
**Release unit**: N/A: not part of a release unit

- In scope: the write in `main`, the `--dry-run` option, and the import block; the companion test.
- Out of scope: rewrite rules and every other option.

## Assumptions
- Verified on 2026-11-06 (Step 3a): `main()` (no `argv` parameter) walks Markdown files, computes `new_content, count = fix_section_marks(original)`, and calls `md_file.write_text(new_content, encoding="utf-8")` only when `--apply` is given; without `--apply` it prints `[DRY-RUN] <file>: N occurrence(s) would be replaced`. The tool already previews by default, so the new `--dry-run` is an explicit flag for that no-write mode (Plan correction 2026-11-06), mutually exclusive with `--apply` (`argparse` mutually exclusive group); with `--dry-run` it prints the same `[DRY-RUN]` lines plus the unified diff. No test references the tool today (checked with `rg`).
- Companion test: `tests/tools/test_fix_docs_section_marks.py` (new file, no test exists today); it is a valid companion because only this row names it in `Related Tests`.
- The tool has no `sys.path` bootstrap, so it gains the guarded bootstrap to import `tools._atomic_write` when run by path. The helper is `tools/_atomic_write.py` (created by the earlier-`seq` sibling procedure of this Plan). No other open Plan targets this file.

## Design decisions
- The real and dry paths share the same computation and differ only at the write call, so the exit codes cannot diverge (Plan Risks).
- Dry run calls `print_dry_run(path, old_text, new_text)`; the real run calls `atomic_write_text`.

## Alternatives considered
N/A: pattern fixed by the Plan.

## Implementation
### Target file
`tools/fix_docs_section_marks.py`

### Procedure
1. Add the guarded bootstrap `if __package__ in (None, ""): sys.path.insert(0, str(Path(__file__).resolve().parent.parent))` (verify `sys` and `Path` are imported) and `from tools._atomic_write import add_dry_run_argument, atomic_write_text, print_dry_run` to the imports.
2. Add `--dry-run` to a mutually exclusive group with `--apply`; default behavior stays the current preview.
3. Replace `md_file.write_text(new_content, encoding="utf-8")` with `atomic_write_text(md_file, new_content)`; when `--dry-run` also call `print_dry_run(md_file, original, new_content)`.

### Method
- `fix_section_marks` is untouched; the exit code stays `0`.

### Details
- Do not change the no-flag output; `--dry-run` only adds the diff.

### Companion test files
- `tests/tools/test_fix_docs_section_marks.py` (new)
  - Procedure: add a new test file: the default run and `--dry-run` leave the file byte-identical (checksum), `--apply` rewrites `§` marks through the helper (UTF-8), `--dry-run` with `--apply` is rejected by argparse (exit 2), and exit codes equal the pre-change behavior.
  - Validation: `uv run pytest tests/tools/test_fix_docs_section_marks.py -q`.

## Compatibility considerations
- Default behavior, output, and exit codes without `--dry-run` are unchanged; `--dry-run` is new and additive.

## Security considerations
N/A: local files only.

## Rollback considerations
N/A: revert the commit.

## Validation plan
- `uv run pytest tests/tools/test_fix_docs_section_marks.py -q`, then `uv run pytest tests/tools -q`.
- Before and after on live data: run the tool without flags, with `--dry-run`, and with `--apply` on a temporary copy of a `docs/` file that contains `§`, comparing output and result.
- `routing.md` "Adding a new tool" steps 1-3 for the changed files, then `uv run python tools/run_validation_gates.py`.

## Completion criteria
- `--dry-run` writes no file (checksum test) and returns the real run's exit code; the real run writes through the helper with explicit UTF-8; no `Path.write_text` call remains in `tools/fix_docs_section_marks.py`; tests pass.

## Out of Scope
- Rewrite rules, other tools.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Add the dry-run test first (fails until step 2) per Companion test files | Completed | 20261106-115822 | 20261106-115851 | Changed: tools/fix_docs_section_marks.py (bootstrap, explicit --dry-run, main(argv), atomic write); tests/tools/test_fix_docs_section_marks.py (new, 5 tests) |
| 2 | Add `--dry-run` and the helper write per Implementation > Procedure | Completed | 20261106-115851 | 20261106-115851 | 5 tests pass (default preview, --dry-run diff, --apply UTF-8, mutual exclusion, clean tree) |
| 3 | Run the validation sequence (`rules/toolchain.md`) and the live-data comparison | Completed | 20261106-115851 | 20261106-115851 | ruff, mypy, bandit clean; live default run output unchanged and wrote nothing |
| 4 | N/A: documentation is the `tools/TOOL_DESCRIPTIONS.md` procedure of this Plan | Completed | 20261106-115851 | 20261106-115851 | N/A: documentation is another procedure of this Plan |

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
- **Requirement ID**: `REQ-004`, `REQ-005`, `REQ-007`
- **Source issue**: issues/20261104-152906_toolwrite001_make-mutating-tools-dry-run-and-atomic.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261105-110212_toolwrite001_make-mutating-tools-dry-run-and-atomic.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261106-092109
- **Related target files**: `tools/fix_docs_section_marks.py`, `tests/tools/test_fix_docs_section_marks.py`
