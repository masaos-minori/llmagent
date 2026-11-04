# Give mutating tools dry-run support and atomic writes

## Priority
Medium

## Summary
Make the tools that rewrite repository files preview their changes with `--dry-run`, write files atomically, and leave a multi-file change either fully applied or untouched.

## Background
Confirmed by repository evidence on 2026-11-04:

- Of the 14 tools that write files (`amend_plan`, `manage_workitem_stage`, `manage_frontmatter`, `set_execution_status`, `rename_doc`, `close_procedures_batch`, `fix_docstring_paths`, `fix_docstring_blank_line`, `fix_docs_section_marks`, `fix_procedure_new_markers`, `mark_procedure_new_symbols`, `module_nodes`, `migrate_runtime_tool_calls`, `generate_workitem`), six have no `--dry-run`: `set_execution_status.py`, `fix_docs_section_marks.py`, `fix_procedure_new_markers.py`, `module_nodes.py`, `migrate_runtime_tool_calls.py`, `generate_workitem.py`.
- Only `amend_plan.py` writes through a temporary file and `os.replace`; the others call `Path.write_text` directly, so an interruption can leave a truncated file.
- `module_nodes.py` `_cmd_extract` moves source ranges between files by writing the destination (`args.dest.write_text(dest_code)`) and then the source (`args.src.write_text("".join(kept_lines))`) as two separate writes. If the second write fails, the moved code exists in both files. `module_nodes` has no `--dry-run`, and no test references it (see `issues/20261104-152002_toolstest001_add-tests-for-untested-tools.md`).
- `set_execution_status.py:161` and `migrate_runtime_tool_calls.py:124` write without an explicit encoding.

## Problem
Tools that modify source and work-item documents cannot preview their effect (six of them), and a failure during a write can leave truncated or duplicated content. Recovery depends on git, which these tools do not require to be clean first.

## Reason for Change
Data-integrity risk for repository files, concentrated in `module_nodes.py` (it edits production source). No incident is known. Timing is flexible.

## Implementation Intent
Add a small shared write helper (temporary file in the same directory, then `os.replace`, explicit UTF-8) and a common `--dry-run` that prints a diff-style summary without writing. For multi-file operations, prepare all new contents first and then replace the files, so a failure before the first replace changes nothing. Keep tool behavior and output otherwise identical.

## Target Files or Areas
- `tools/module_nodes.py` (`_cmd_extract`)
- `tools/set_execution_status.py`, `tools/fix_docs_section_marks.py`, `tools/fix_procedure_new_markers.py`, `tools/migrate_runtime_tool_calls.py`, `tools/generate_workitem.py`
- Other writers listed above for the atomic helper: `manage_workitem_stage.py`, `manage_frontmatter.py`, `rename_doc.py`, `close_procedures_batch.py`, `fix_docstring_paths.py`, `fix_docstring_blank_line.py`, `mark_procedure_new_symbols.py`
- New shared write helper (location: may be the helper module from `issues/20261104-152002_toolcommon001_shared-helper-for-tools.md`)
- `tests/tools/`

## Required Changes
- Add an atomic write helper with tests (success, interruption before replace leaves the original, explicit UTF-8).
- Add `--dry-run` to the six tools, printing the intended change and writing nothing.
- Make `module_nodes.py extract` prepare both new contents first and replace the files together; define the behavior when the destination write succeeds and the source write fails.
- Switch the other writers to the helper in small batches, without behavior changes.

## Constraints
- Preserve each tool's current outputs and exit codes; `--dry-run` must exit with the same code the real run would, or the documented code.
- File mode and line endings must be preserved by the atomic write.
- Archive moves done with `git mv` (`manage_workitem_stage.py`, `rename_doc.py`) are outside the helper and must not be reordered.
- `os.replace` across two files is not a single atomic operation; the issue asks for "fail before the first replace changes nothing", not for cross-file atomicity.

## Acceptance Criteria
- Every tool that writes repository files supports `--dry-run`, and a dry run changes no file (verified by a checksum test).
- A failure injected before the first replace leaves all files unchanged for `module_nodes.py extract`.
- No migrated tool calls `Path.write_text` directly on a repository file.
- Existing tests pass; each changed tool has a dry-run test.

## Testing Expectations
- Unit tests for the helper; dry-run tests per tool using temporary directories; a fault-injection test for `module_nodes.py extract` (second write fails); run `uv run pytest tests/tools -q`, ruff, and mypy.

## Documentation Impact
Update `tools/TOOL_DESCRIPTIONS.md` with the `--dry-run` convention and the write helper (operational notes).

## Out of Scope
- Changing what any tool rewrites or its rewrite rules.
- Rollback or undo features beyond a dry run.
- Cross-file transactional guarantees.

## Dependencies
- Depends on `issues/20261104-152002_toolstest001_add-tests-for-untested-tools.md` for `module_nodes.py` (tests first) and on `issues/20261104-152002_toolmypy001_add-tools-to-mypy-scope.md`.
- Coordinate with `issues/20261104-152002_toolcommon001_shared-helper-for-tools.md` (where the helper lives) and `issues/20261104-152906_toolreport001_share-report-model-and-renderers.md` (shared `--format`/option helpers).

## Unresolved Questions
- Whether a partial write has ever corrupted a file in practice: unknown.
- Whether the one-shot formatters (`fix_docs_section_marks.py`, `migrate_runtime_tool_calls.py`) are still needed; if retired, their `--dry-run` work is moot: unknown.
- Preferred dry-run output form (diff versus summary): unknown.

## AI Implementation Instruction
Write the failing fault-injection and dry-run tests first. Change `module_nodes.py` before the low-risk formatters. Do not alter rewrite logic while changing how files are written.

## Traceability
- **Workflow phase**: issue-creator
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20261104-152906
- **Related target files**: `tools/module_nodes.py`, `tools/set_execution_status.py`, `tools/fix_docs_section_marks.py`, `tools/fix_procedure_new_markers.py`, `tools/migrate_runtime_tool_calls.py`, `tools/generate_workitem.py`
