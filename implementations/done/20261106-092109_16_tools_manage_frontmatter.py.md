## Goal
Make `tools/manage_frontmatter.py` write its repository file through the shared atomic helper instead of `Path.write_text`, with identical output and exit codes (`REQ-005`; Plan batch 4a).

## Scope
**Release unit**: N/A: not part of a release unit

- In scope: the write call in `cmd_add_missing, cmd_rename_category_to_area, cmd_dedupe_lists, and cmd_merge_related` and the import block.
- Out of scope: rewrite rules, options, `git mv` moves, and every other function.

## Assumptions
- Verified on 2026-11-06 (Step 3a): `cmd_add_missing, cmd_rename_category_to_area, cmd_dedupe_lists, and cmd_merge_related` writes four `write_text(..., encoding="utf-8")` calls (the first, second, and fourth under `args.fix`, the third unconditionally for changed files); the tool already has `--dry-run`, so no option is added. The file already has the guarded bootstrap; replace all four calls and leave `--fix` and `--dry-run` semantics unchanged.
- Existing tests: `tests/tools/test_manage_frontmatter.py` exist and none patches `write_text` or `os.replace` (checked with `rg`), so no test edit is needed.
- The helper is `tools/_atomic_write.py` (created by the earlier-`seq` sibling procedure of this Plan); this procedure follows it in `seq` order. No other open Plan targets this file.

## Design decisions
- Replace only the write call with `atomic_write_text(path, text)` (explicit UTF-8 is the helper default); the surrounding logic and prints stay byte-identical.
- Reuse the existing bootstrap.

## Alternatives considered
N/A: single call site, no realistic alternative.

## Implementation
### Target file
`tools/manage_frontmatter.py`

### Procedure
1. The file already has the guarded bootstrap; add `from tools._atomic_write import atomic_write_text` to the import block (ruff `I` decides placement).
2. In `cmd_add_missing, cmd_rename_category_to_area, cmd_dedupe_lists, and cmd_merge_related` replace the `write_text(...)` call with `atomic_write_text(<path>, <text>)` using the same path and text arguments.
3. Remove any import that the change leaves unused.

### Method
- `atomic_write_text` writes UTF-8 bytes to a same-directory temporary file, copies the mode, and replaces; the written bytes equal what `write_text(..., encoding="utf-8")` wrote.

### Details
- Do not change what is written, when, or the messages printed. 

## Compatibility considerations
- Output, exit codes, `--dry-run`, and the by-path and test-import forms are unchanged.

## Security considerations
N/A: no new input; the helper writes next to the target and never outside its directory.

## Rollback considerations
N/A: revert the commit.

## Validation plan
- `uv run pytest tests/tools/test_manage_frontmatter.py -q`, then `uv run pytest tests/tools -q`.
- Before and after on live data: run `uv run python tools/manage_frontmatter.py add-missing` (report only) before and after on `docs/`.
- `routing.md` "Adding a new tool" steps 1-3 for the changed files, then `uv run python tools/run_validation_gates.py`.

## Completion criteria
- No `Path.write_text` call on a repository file remains in `tools/manage_frontmatter.py`; existing tests pass unchanged; live-data output and exit code are identical before and after.

## Out of Scope
- Rewrite logic, the other writers.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Capture the before-run on live data, then apply Implementation > Procedure | Completed | 20261106-120053 | 20261106-120204 | Changed: tools/manage_frontmatter.py (four writes via atomic_write_text) |
| 2 | Run the existing tests (no test edit expected) per Validation plan | Completed | 20261106-120204 | 20261106-120204 | 54 tests pass; no test edit needed |
| 3 | Run the validation sequence (`rules/toolchain.md`) and the after-run comparison | Completed | 20261106-120204 | 20261106-120204 | ruff, mypy clean; existing tests pass; live read-only output identical before/after where captured; by-path --help OK from another cwd; radon grades unchanged |
| 4 | N/A: documentation is the `tools/TOOL_DESCRIPTIONS.md` procedure of this Plan | Completed | 20261106-120204 | 20261106-120204 | N/A: documentation is another procedure of this Plan |

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
- **Requirement ID**: `REQ-005` (atomic write through the helper)
- **Source issue**: issues/20261104-152906_toolwrite001_make-mutating-tools-dry-run-and-atomic.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261105-110212_toolwrite001_make-mutating-tools-dry-run-and-atomic.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261106-092109
- **Related target files**: `tools/manage_frontmatter.py`
