## Goal
- The 14 tools listed in the Issue that rewrite repository files write atomically (temporary file in the same directory, explicit UTF-8, `os.replace`, file mode preserved), the six that lack it gain `--dry-run`, and `module_nodes.py extract` prepares both new contents before replacing either file and defines its behavior when the second replace fails.

## Priority
Medium

## Scope
- **In-Scope**: add `tools/_atomic_write.py` (atomic write helper and dry-run preview) with tests; add `--dry-run` to `set_execution_status.py`, `fix_docs_section_marks.py`, `fix_procedure_new_markers.py`, `module_nodes.py`, `migrate_runtime_tool_calls.py`, and `generate_workitem.py`; make `module_nodes.py extract` prepare then replace; switch the seven other listed writers (`manage_workitem_stage.py`, `manage_frontmatter.py`, `rename_doc.py`, `close_procedures_batch.py`, `fix_docstring_paths.py`, `fix_docstring_blank_line.py`, `mark_procedure_new_symbols.py`) to the helper in batches; document the `--dry-run` convention and the helper.
- **Out-of-Scope**: changing what any tool rewrites or its rewrite rules; rollback or undo features beyond a dry run; cross-file transactional guarantees; `git mv` archive moves in `manage_workitem_stage.py` and `rename_doc.py` (not reordered); `amend_plan.py`, which already writes atomically; the other repository writers not in the Issue's list (`generate_reference_table.py`, `generate_adr_authority.py`, `check_module_size.py --update-baseline`, `check_docstrings.py`, `scan_change_consumers.py --report`, `_contract_manifests.py`; UNK-02).
- **Dependencies**: lands after the tests Plan (for `module_nodes.py`), the mypy scope Plan, and the helper Plan phase that migrates `module_nodes.py` and `rename_doc.py`; coordinates with the reporting Plan on shared option helpers.
  - **Depends on**: plans/20261105-105344_toolstest001_add-tests-for-untested-tools.md | phase all | `module_nodes.py` needs its tests before `extract` changes
  - **Depends on**: plans/20261105-105442_toolmypy001_add-tools-to-mypy-scope.md | phase all | the helper and changed tools must be type-checked
  - **Depends on**: plans/20261105-105811_toolcommon001_shared-helper-for-tools.md | phase 3 | that phase edits `module_nodes.py` and `rename_doc.py`, files this Plan also changes
  - Coordinate with `plans/20261105-110046_toolreport001_share-report-model-and-renderers.md` (shared `--format` and option helpers; no common file).

## Background
Verified on 2026-11-05 (checked in Steps 2 and 3): of the 14 listed writers six have no `--dry-run` (`set_execution_status.py`, `fix_docs_section_marks.py`, `fix_procedure_new_markers.py`, `module_nodes.py`, `migrate_runtime_tool_calls.py`, `generate_workitem.py`); `amend_plan.py` is the only one of the 14 that writes through a temporary file and `os.replace`, the others call `write_text` directly (`manage_binaries.py` also uses `os.replace` but is not in the list). `module_nodes.py` `_cmd_extract` writes the destination and then the source with two `write_text` calls, so a failure of the second leaves moved code in both files. `set_execution_status.py` and `migrate_runtime_tool_calls.py` write without an explicit encoding. Six further tools outside the Issue's list also write repository files. Tests exist for `set_execution_status`, `generate_workitem`, `manage_workitem_stage`, `manage_frontmatter`, `rename_doc`, `close_procedures_batch`, `fix_docstring_paths`, and `mark_procedure_new_symbols`; none exists for `fix_docs_section_marks`, `fix_procedure_new_markers`, `migrate_runtime_tool_calls`, `fix_docstring_blank_line`, and (until the tests Plan lands) `module_nodes`. Corrected on 2026-11-06 (Step 3a of the procedure pass): `fix_docs_section_marks.py` already previews by default and writes only with `--apply` (it prints `[DRY-RUN]` lines), so its new `--dry-run` is an explicit flag for that no-write mode, mutually exclusive with `--apply`; `close_procedures_batch.py` also appends a final newline with `plan_path.open("a")` after its `write_text`; `generate_workitem.py` writes a plan timestamp marker (read, then rewrite) besides two skeleton writes; `migrate_runtime_tool_calls.py` has `main()` without an `argv` parameter and `_migrate(path)` does the write; only `manage_frontmatter.py` and `close_procedures_batch.py` carry the guarded `sys.path` bootstrap, so the other tools need it to import `tools._atomic_write` when run by path (the `toolcommon001` procedures add it to `module_nodes.py` and `rename_doc.py` first); no test patches `write_text` or `os.replace`.

## Problem
Tools that modify source and work-item documents cannot preview their effect (six of them), and a failure during a write can leave truncated or duplicated content. Recovery depends on git, which these tools do not require to be clean first.

## Reason for Change
Data-integrity risk for repository files, concentrated in `module_nodes.py`, which edits production source. No incident is known and timing is flexible.

## Implementation Intent
Add one small module with an atomic text write (same-directory temporary file, UTF-8 bytes written without newline translation, mode copied, `os.replace`) and a dry-run preview that prints a unified diff and writes nothing. Change `module_nodes.py` first, then the five other dry-run additions, then switch the seven atomic-only writers, one batch per commit, without changing any rewrite logic.

## Requirements
- `REQ-001`: `tools/_atomic_write.py` MUST provide an atomic text write that writes a temporary file in the target's directory, preserves file mode and line endings, encodes as UTF-8, and replaces with `os.replace`; an interruption before the replace MUST leave the original unchanged and the temporary file removed.
- `REQ-002`: `tools/_atomic_write.py` MUST provide a dry-run preview that prints a unified diff of the intended change and writes no file, and an option helper adding `--dry-run` to an argument parser.
- `REQ-003`: `module_nodes.py extract` MUST prepare both new contents first, write both temporary files, and only then replace; on a failure before the first replace nothing changes; when the destination replace succeeds and the source replace fails, it MUST restore the destination from its saved original (or remove a destination it created), report the error with exit code 1, and, if the restore also fails, report both paths and the duplicated code without losing the moved code.
- `REQ-004`: `set_execution_status.py`, `fix_docs_section_marks.py`, `fix_procedure_new_markers.py`, `module_nodes.py`, `migrate_runtime_tool_calls.py`, and `generate_workitem.py` MUST accept `--dry-run`, print the intended change, write nothing (verified by checksum), and return the exit code the real run would return.
- `REQ-005`: The seven atomic-only writers MUST write through the helper and MUST NOT call `Path.write_text` on a repository file, with identical outputs and exit codes; `git mv` moves are untouched.
- `REQ-006`: `set_execution_status.py` and `migrate_runtime_tool_calls.py` MUST write with explicit UTF-8 through the helper.
- `REQ-007`: Tests MUST cover the helper (success, interruption before replace leaves the original, explicit UTF-8, mode preserved), a dry-run test per tool in `REQ-004`, and a fault-injection test for `module_nodes.py extract` where the second write fails; existing tests MUST pass.
- `REQ-008`: `tools/TOOL_DESCRIPTIONS.md` MUST document the `--dry-run` convention and the helper.

## Implementation Target Files
**Freeze status**: Frozen

| File Path | Change Responsibility | Reason for Modification | Related Requirement / Acceptance Criterion | Repository Evidence | Related Tests | Validation Status |
|---|---|---|---|---|---|---|
| `tools/_atomic_write.py` | Atomic write and dry-run helper | New file; `tools/` exists and holds `_`-prefixed private modules; only `amend_plan.py` has an in-file atomic write today | `REQ-001`, `REQ-002`; AC-1 | `amend_plan.py` uses a temporary file and `os.replace`; others `write_text` (checked in Step 3) | `tests/tools/test_atomic_write.py` | Verified |
| `tests/tools/test_atomic_write.py` | Helper tests | New file; `tests/tools/` exists | `REQ-001`, `REQ-002`, `REQ-007`; AC-1 | No existing tests for an atomic writer (checked in Step 3) | itself | Verified |
| `tools/module_nodes.py` | Prepare-then-replace extract and `--dry-run` | Rewrite the two `write_text` calls of `_cmd_extract`; add `--dry-run` to `extract` | `REQ-003`, `REQ-004`; AC-2, AC-3 | `args.dest.write_text(dest_code)` then `args.src.write_text("".join(kept_lines))` in `_cmd_extract` (checked in Step 3) | `tests/tools/test_module_nodes_extract_atomic.py` | Verified |
| `tests/tools/test_module_nodes_extract_atomic.py` | Fault-injection and dry-run tests for `extract` | New file, separate from the tests Plan's `test_module_nodes.py` so the two Plans share no file | `REQ-003`, `REQ-007`; AC-2 | `_cmd_extract` two-step write (checked in Step 3) | itself | Verified |
| `tools/set_execution_status.py` | Add `--dry-run`; atomic UTF-8 write | The `write_text` without encoding in the rewrite function | `REQ-004`, `REQ-006`; AC-3, AC-5 | `path.write_text("\n".join(rebuilt) + "\n")` without encoding (checked in Step 3) | `tests/tools/test_set_execution_status.py` | Verified |
| `tests/tools/test_set_execution_status.py` | Add a dry-run test | Existing file; add a checksum test | `REQ-004`, `REQ-007`; AC-3 | File exists (checked in Step 3) | itself | Verified |
| `tools/fix_docs_section_marks.py` | Add `--dry-run`; atomic write | One-shot formatter writes with `write_text` and has no `--dry-run` | `REQ-004`, `REQ-005`; AC-3, AC-5 | `--dry-run` count 0; one `write_text` (checked in Step 3) | `tests/tools/test_fix_docs_section_marks.py` | Verified |
| `tests/tools/test_fix_docs_section_marks.py` | Dry-run and write tests | New file; no tests exist | `REQ-004`, `REQ-007`; AC-3 | No test references `fix_docs_section_marks` (checked in Step 2) | itself | Verified |
| `tools/fix_procedure_new_markers.py` | Add `--dry-run`; atomic write | Same pattern | `REQ-004`, `REQ-005`; AC-3, AC-5 | `--dry-run` count 0; one `write_text` (checked in Step 3) | `tests/tools/test_fix_procedure_new_markers.py` | Verified |
| `tests/tools/test_fix_procedure_new_markers.py` | Dry-run and write tests | New file; no tests exist | `REQ-004`, `REQ-007`; AC-3 | No test references `fix_procedure_new_markers` (checked in Step 2) | itself | Verified |
| `tools/migrate_runtime_tool_calls.py` | Add `--dry-run`; atomic UTF-8 write | `path.write_text(new_src)` without encoding after the syntax check | `REQ-004`, `REQ-006`; AC-3, AC-5 | `write_text(new_src)` without encoding (checked in Step 3) | `tests/tools/test_migrate_runtime_tool_calls.py` | Verified |
| `tests/tools/test_migrate_runtime_tool_calls.py` | Dry-run and write tests | New file; no tests exist | `REQ-004`, `REQ-006`, `REQ-007`; AC-3 | No test references `migrate_runtime_tool_calls` (checked in Step 2) | itself | Verified |
| `tools/generate_workitem.py` | Add `--dry-run`; atomic write of skeletons and the plan marker | Three `write_text` calls (skeletons and a plan marker append) | `REQ-004`, `REQ-005`; AC-3, AC-5 | Three `write_text` calls; no `--dry-run`; collision refusal exists (checked in Step 3) | `tests/tools/test_generate_workitem.py` | Verified |
| `tests/tools/test_generate_workitem.py` | Add a dry-run test | Existing file; add a checksum test | `REQ-004`, `REQ-007`; AC-3 | File exists (checked in Step 3) | itself | Verified |
| `tools/manage_workitem_stage.py` | Atomic write | Replace the `write_text` of the status rewrite; keep `git mv` as is | `REQ-005`; AC-5 | One `write_text`; `--dry-run` exists (checked in Step 3) | `tests/tools/test_manage_workitem_stage.py` | Verified |
| `tools/manage_frontmatter.py` | Atomic write | Replace four `write_text` calls | `REQ-005`; AC-5 | Four `write_text` calls; `--dry-run` exists (checked in Step 3) | `tests/tools/test_manage_frontmatter.py` | Verified |
| `tools/rename_doc.py` | Atomic write | Replace the `write_text` of the link rewrite; keep `git mv` as is | `REQ-005`; AC-5 | One `write_text`; `--dry-run` exists (checked in Step 3) | `tests/tools/test_rename_doc.py` | Verified |
| `tools/close_procedures_batch.py` | Atomic write | Replace the `write_text` | `REQ-005`; AC-5 | One `write_text`; `--dry-run` exists (checked in Step 3) | `tests/tools/test_close_procedures_batch.py` | Verified |
| `tools/fix_docstring_paths.py` | Atomic write | Replace the `write_text` | `REQ-005`; AC-5 | One `write_text`; `--dry-run` exists (checked in Step 3) | `tests/tools/test_fix_docstring_paths.py` | Verified |
| `tools/fix_docstring_blank_line.py` | Atomic write | Replace the `write_text` | `REQ-005`; AC-5 | One `write_text`; `--dry-run` exists; no test file (checked in Step 3) | `tests/tools/test_fix_docstring_blank_line.py` | Verified |
| `tests/tools/test_fix_docstring_blank_line.py` | Regression test for the atomic switch | New file; no tests exist | `REQ-005`, `REQ-007`; AC-5 | No test references `fix_docstring_blank_line` (checked in Step 2) | itself | Verified |
| `tools/mark_procedure_new_symbols.py` | Atomic write | Replace the `write_text` | `REQ-005`; AC-5 | One `write_text`; `--dry-run` exists (checked in Step 3) | `tests/tools/test_mark_procedure_new_symbols.py` | Verified |
| `tools/TOOL_DESCRIPTIONS.md` | Document `--dry-run` and the helper | Add the helper row and the convention note | `REQ-008`; AC-6 | Index lists private modules (checked in Step 3) | `uv run python tools/check_tool_descriptions_sync.py` | Verified |

## Reference Files
| File Path | Why It Must Be Read | Related Target File or Requirement |
|---|---|---|
| `tools/amend_plan.py` | Existing atomic write (`os.replace`) and `--dry-run` pattern to match | `REQ-001`, `REQ-002` |
| `tools/manage_binaries.py` | Another existing temporary-file and `os.replace` implementation (binaries) | `REQ-001` |
| `tools/check_workitem_structure.py` | Not modified; confirms writers' outputs stay valid work items | `REQ-005` |
| `tests/tools/test_amend_plan.py` | Existing dry-run and atomic test style | `REQ-007` |
| `tests/tools/test_module_nodes.py` | Created by the tests Plan; the non-atomic `extract` behavior this Plan preserves | `REQ-003` |

## Acceptance Criteria
- AC-1: The helper tests pass for success, interruption before replace (original unchanged, no temporary file left), explicit UTF-8, and mode preservation (`REQ-001`, `REQ-002`, `REQ-007`).
- AC-2: A failure injected before the first replace leaves both files unchanged, and a failure of the source replace restores the destination (or reports duplicated code if the restore also fails) (`REQ-003`, `REQ-007`).
- AC-3: Every tool in `REQ-004` accepts `--dry-run`, a dry run changes no file (checksum test), and its exit code equals the real run's (`REQ-004`, `REQ-006`, `REQ-007`).
- AC-4: `module_nodes.py extract` output and moved text are identical to the pre-change behavior on a successful run (`REQ-003`).
- AC-5: None of the 13 migrated tools calls `Path.write_text` on a repository file, and existing tests pass (`REQ-005`, `REQ-006`).
- AC-6: `tools/TOOL_DESCRIPTIONS.md` documents the `--dry-run` convention and the helper, and `check_tool_descriptions_sync.py` passes (`REQ-008`).

## Tests
- Unit tests of the helper (success, injected failure before replace, UTF-8, mode and line endings preserved) (`REQ-001`, `REQ-002`, `REQ-007`).
- Fault injection for `module_nodes.py extract`: second replace raises; restore succeeds; restore fails (`REQ-003`, `REQ-007`).
- Dry-run checksum tests for the six tools, in temporary directories (`REQ-004`, `REQ-006`, `REQ-007`).
- Regression: existing tests of the seven atomic-only writers after each batch (`REQ-005`).
- Live-data comparison: run each tool's read-only or dry-run mode before and after and compare output (`REQ-004`, `REQ-005`).

## Documentation Impact
Yes: `tools/TOOL_DESCRIPTIONS.md` (the `--dry-run` convention and the helper entry; operational notes only) (`REQ-008`). No `docs/*.md` file is affected.

## Assumptions
- The helper is a separate module, `tools/_atomic_write.py`, not part of the helper Plan's module, so the two Plans share no new file and can land in either order after their dependencies (judgment; the Issue allows either location).
- Dry-run output form is a unified diff of the intended change (judgment for the Issue's open question "diff versus summary"); a tool whose change is a new file prints the content path and a diff against empty.
- Each tool that imports the helper and lacks the repository's guarded bootstrap (`if __package__ in (None, ""): sys.path.insert(0, ...)`) gains it, so by-path runs from skills keep working; the follow-up Plans of `toolcommon001` remove all bootstraps after the invocation decision (Step 3a).
- Needs confirmation (non-blocking, Step 3a): the open-append of one newline in `close_procedures_batch.py` is a second, non-atomic write; it is left as is because it is one byte and the Plan names `write_text` calls, and the owner may extend the row.
- The one-shot formatters (`fix_docs_section_marks.py`, `migrate_runtime_tool_calls.py`) are still in the repository and listed by the Issue, so they are included; if the owner retires them first, their rows are dropped through a Plan amendment (UNK-03).
- Overlap judgments (`check_plan_target_overlaps.py`): `tools/module_nodes.py` and `tools/rename_doc.py` are also targeted by the `toolcommon001` Plan (git calls versus write calls), `tools/generate_workitem.py` and others by no other Plan, and `tools/TOOL_DESCRIPTIONS.md` by four other Plans (different sections); the changes are compatible, with the sequencing recorded in Scope.

## Unknowns
| ID | Unknown Description | Evidence Missing | Resolution Path | Blocking? (True/False) |
|---|---|---|---|---|
| UNK-01 | Whether a partial write has ever corrupted a file in practice | No incident record | Not needed to proceed; the helper closes the risk regardless | False |
| UNK-02 | Whether the six repository writers outside the Issue's list should also move to the helper and gain `--dry-run` | Owner decision on scope | File a follow-up issue after this Plan completes | False |
| UNK-03 | Whether the one-shot formatters are still needed | Owner knowledge | If retired, amend the Plan with `tools/amend_plan.py` to drop their rows; otherwise implement as planned | False |
| UNK-04 | Line-ending behavior of tools that read with `read_text` and join with `"\n"` | Not measured per tool | The helper writes bytes as given; each tool's current newline handling is kept and covered by its existing tests | False |

## Affected areas
| File | Change | Blast Radius | Churn (30d) | Bus Factor | deploy.sh Impact |
|---|---|---|---|---|---|
| `tools/_atomic_write.py` | Create | Medium (used by 13 tools that edit repository files) | N/A | High (one author across the repository history) | not applicable (rsynced) |
| `tools/module_nodes.py` | Modify | High (edits production source during splits) | N/A (outside top 60) | High | not applicable (rsynced) |
| `tools/set_execution_status.py` | Modify | Medium (edits work-item status tables) | N/A | High | not applicable (rsynced) |
| `tools/fix_docs_section_marks.py` | Modify | Low | N/A | High | not applicable (rsynced) |
| `tools/fix_procedure_new_markers.py` | Modify | Low | N/A | High | not applicable (rsynced) |
| `tools/migrate_runtime_tool_calls.py` | Modify | Low | N/A | High | not applicable (rsynced) |
| `tools/generate_workitem.py` | Modify | Medium (scaffolds Plans, procedures, Unknown and Risk files) | N/A | High | not applicable (rsynced) |
| `tools/manage_workitem_stage.py` | Modify | High (moves and edits workflow documents; used by skills) | 5 | High | not applicable (rsynced) |
| `tools/manage_frontmatter.py` | Modify | Medium | N/A | High | not applicable (rsynced) |
| `tools/rename_doc.py` | Modify | Medium | N/A | High | not applicable (rsynced) |
| `tools/close_procedures_batch.py` | Modify | Low | N/A | High | not applicable (rsynced) |
| `tools/fix_docstring_paths.py` | Modify | Low | N/A | High | not applicable (rsynced) |
| `tools/fix_docstring_blank_line.py` | Modify | Low | N/A | High | not applicable (rsynced) |
| `tools/mark_procedure_new_symbols.py` | Modify | Low | N/A | High | not applicable (rsynced) |
| `tests/tools/test_atomic_write.py` | Create | Low | N/A | High | not applicable (rsynced) |
| `tests/tools/test_module_nodes_extract_atomic.py` | Create | Low | N/A | High | not applicable (rsynced) |
| `tests/tools/test_set_execution_status.py` | Modify | Low | N/A | High | not applicable (rsynced) |
| `tests/tools/test_generate_workitem.py` | Modify | Low | N/A | High | not applicable (rsynced) |
| `tests/tools/test_fix_docs_section_marks.py` | Create | Low | N/A | High | not applicable (rsynced) |
| `tests/tools/test_fix_procedure_new_markers.py` | Create | Low | N/A | High | not applicable (rsynced) |
| `tests/tools/test_migrate_runtime_tool_calls.py` | Create | Low | N/A | High | not applicable (rsynced) |
| `tests/tools/test_fix_docstring_blank_line.py` | Create | Low | N/A | High | not applicable (rsynced) |
| `tools/TOOL_DESCRIPTIONS.md` | Modify | Low | 82 | High | not applicable (rsynced) |

## Design
- Path B (more than 3 files, new module). Architecture analysis: `tools/` is outside the `.importlinter` contracts; `tools/_atomic_write.py` imports only the standard library, so no cycle arises. Dependency graphing: the writers were found by `rg 'write_text'` over `tools/*.py` and compared with the Issue's list; callers are skills, hooks, and manual runs, and none of the thirteen is invoked by `deploy/deploy.sh`. Historical analysis: churn figures are in the Affected areas table and all history is by one author. Operational dependency inspection: not applicable (no MCP server, database, or dependency change).
- Validation quality baseline: `radon cc` grades `migrate_runtime_tool_calls.py` `_migrate` D (23), `set_execution_status.py` `find_table` C (12) and `apply_updates` C (12), `fix_docstring_paths.py` `process_file` C (20) and `compute_new_header` C (14); the changes MUST NOT raise these grades, so write changes are limited to the write call and the argument. `vulture` and `bandit` baselines on `scripts/` are unrelated and unchanged. diff-cover baseline: `N/A: no diff exists before implementation`; at least 90 percent on changed lines is required (`rules/toolchain.md`).
- Atomic write: `tempfile.mkstemp(dir=target.parent)`, write encoded bytes, copy mode with `shutil.copymode`, `os.replace`, and remove the temporary file in a `finally` on failure.
- `module_nodes.py extract`: compute `dest_code` and `kept_text`; write both temporary files; save the original destination text (or note that it did not exist); replace destination, then source; on a source-replace failure restore the destination (atomic write of the original, or unlink if it was created), print the error, and return 1; if the restore fails too, print both paths and state that the moved code remains in both files. Alternatives rejected: replacing the source first (a failure then loses code), and a journal file (more machinery than the Issue asks). `--dry-run` prints the diffs and returns the exit code a real run would.
- Consumer scan: not applicable for a persisted schema or public API; no tool's output or arguments change except the added `--dry-run`.

## Implementation steps
1. **Phase 1: Helper with failing tests**
   - [ ] Add the helper tests, then `tools/_atomic_write.py` (`REQ-001`, `REQ-002`, `REQ-007`; `tests/tools/test_atomic_write.py`, `tools/_atomic_write.py`)
2. **Phase 2: `module_nodes.py extract`**
   - [ ] Add the fault-injection and dry-run tests, then implement prepare-then-replace and `--dry-run` (`REQ-003`, `REQ-004`, `REQ-007`; `tests/tools/test_module_nodes_extract_atomic.py`, `tools/module_nodes.py`)
3. **Phase 3: Dry-run for the five other tools**
   - [ ] Add the dry-run tests, then `--dry-run` and the helper in `set_execution_status.py`, `fix_docs_section_marks.py`, `fix_procedure_new_markers.py`, `migrate_runtime_tool_calls.py`, and `generate_workitem.py` (`REQ-004`, `REQ-005`, `REQ-006`, `REQ-007`; the five tool rows and `tests/tools/test_set_execution_status.py`, `tests/tools/test_generate_workitem.py`, `tests/tools/test_fix_docs_section_marks.py`, `tests/tools/test_fix_procedure_new_markers.py`, `tests/tools/test_migrate_runtime_tool_calls.py`)
4. **Phase 4: Atomic switch for the seven writers**
   - [ ] Switch `manage_workitem_stage.py`, `manage_frontmatter.py`, and `rename_doc.py` (batch 4a), then `close_procedures_batch.py`, `fix_docstring_paths.py`, `fix_docstring_blank_line.py`, and `mark_procedure_new_symbols.py` (batch 4b) to the helper; add `tests/tools/test_fix_docstring_blank_line.py`; run `tests/tools` after each batch (`REQ-005`, `REQ-007`; the seven tool rows and `tests/tools/test_fix_docstring_blank_line.py`)
5. **Phase 5: Documentation and verification**
   - [ ] Document the convention and helper; run `check_tool_descriptions_sync.py`, the per-file checks of `routing.md` "Adding a new tool", the validation gates, and the live-data comparison (`REQ-008`; `tools/TOOL_DESCRIPTIONS.md` and all tool rows). No deploy step: only `tools/` and `tests/` change.

### Release units
N/A: no release unit

## Validation plan
| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| `tools/_atomic_write.py` | Unit | `uv run pytest tests/tools/test_atomic_write.py -q` | All pass |
| `tools/module_nodes.py` | Fault injection and dry-run | `uv run pytest tests/tools/test_module_nodes_extract_atomic.py tests/tools/test_module_nodes.py -q` | All pass |
| six dry-run tools | Dry-run checksum tests | `uv run pytest tests/tools/test_set_execution_status.py tests/tools/test_generate_workitem.py tests/tools/test_fix_docs_section_marks.py tests/tools/test_fix_procedure_new_markers.py tests/tools/test_migrate_runtime_tool_calls.py -q` | All pass |
| seven atomic-only writers | Regression per batch | `uv run pytest tests/tools -q` | No new failure |
| every changed tool | Live-data comparison | Run `--dry-run` or the read-only mode before and after | Identical output and exit code |
| changed Python files | Lint, type, security (paths explicit) | `uv run ruff format`, `uv run ruff check`, `uv run mypy --no-namespace-packages <files>`, `uv run bandit <files>` | Clean |
| diff | Gates | `uv run python tools/run_validation_gates.py` | Pass |
| `tools/TOOL_DESCRIPTIONS.md` | Sync check | `uv run python tools/check_tool_descriptions_sync.py` | `No issues found.` |

## Risks
- **Risk**: The atomic write changes file mode or line endings → **Mitigation**: copy the mode, write bytes as given, and test both (`REQ-001`).
- **Risk**: A failure between the two `extract` replaces still leaves duplicated code → **Mitigation**: replace the destination first, restore it on failure, and report both paths if the restore fails; no code is ever lost (`REQ-003`).
- **Risk**: The change to `module_nodes.py` precedes full tests of it → **Mitigation**: the tests Plan lands first (Scope dependency) and Phase 2 starts with failing tests.
- **Risk**: A dry run diverges from the real run (different exit code or content) → **Mitigation**: the real and dry paths share the same computation and differ only at the write call; test both on the same fixtures.
- **Risk**: Switching seven writers at once hides a regression → **Mitigation**: two batches, `tests/tools` after each, and live-data comparison.
- **Risk**: `tools/TOOL_DESCRIPTIONS.md` and the shared tools are edited by several Plans → **Mitigation**: sequencing in Scope; re-run `check_plan_target_overlaps.py` at procedure generation.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Add the atomic write helper and its tests | Completed | — | 20261106-121355 |  |
| 2 | Make `module_nodes.py extract` prepare-then-replace with `--dry-run` | Completed | — | 20261106-121355 |  |
| 3 | Add `--dry-run` to the five other tools | Completed | — | 20261106-121355 |  |
| 4 | Switch the seven atomic-only writers to the helper | Completed | — | 20261106-121355 |  |
| 5 | Document and verify | Completed | — | 20261106-121355 |  |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| — | — | — | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| implementations/20261106-092109_01_tools__atomic_write.py.md | 1 | Procedure | Completed | — | — |
| implementations/20261106-092109_03_tools_module_nodes.py.md | 2 | Procedure | Completed | — | — |
| implementations/20261106-092109_05_tools_set_execution_status.py.md | 3 | Procedure | Completed | — | — |
| implementations/20261106-092109_07_tools_fix_docs_section_marks.py.md | 3 | Procedure | Completed | — | — |
| implementations/20261106-092109_09_tools_fix_procedure_new_markers.py.md | 3 | Procedure | Completed | — | — |
| implementations/20261106-092109_11_tools_migrate_runtime_tool_calls.py.md | 3 | Procedure | Completed | — | — |
| implementations/20261106-092109_13_tools_generate_workitem.py.md | 3 | Procedure | Completed | — | — |
| implementations/20261106-092109_15_tools_manage_workitem_stage.py.md | 4 | Procedure | Completed | — | — |
| implementations/20261106-092109_16_tools_manage_frontmatter.py.md | 4 | Procedure | Completed | — | — |
| implementations/20261106-092109_17_tools_rename_doc.py.md | 4 | Procedure | Completed | — | — |
| implementations/20261106-092109_18_tools_close_procedures_batch.py.md | 4 | Procedure | Completed | — | — |
| implementations/20261106-092109_19_tools_fix_docstring_paths.py.md | 4 | Procedure | Completed | — | — |
| implementations/20261106-092109_20_tools_fix_docstring_blank_line.py.md | 4 | Procedure | Completed | — | — |
| implementations/20261106-092109_22_tools_mark_procedure_new_symbols.py.md | 4 | Procedure | Completed | — | — |
| implementations/20261106-092109_23_tools_TOOL_DESCRIPTIONS.md.md | 5 | Procedure | Completed | — | — |

## Traceability
- **Workflow phase**: issue-to-plan
- **Source issue**: issues/20261104-152906_toolwrite001_make-mutating-tools-dry-run-and-atomic.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: this document is the generated plan
- **Source implementation procedure**: N/A: not applicable in this phase
- **Generated at**: 20261105-110212
- **Related target files**: tools/_atomic_write.py, tools/module_nodes.py, tools/set_execution_status.py, tools/fix_docs_section_marks.py, tools/fix_procedure_new_markers.py, tools/migrate_runtime_tool_calls.py, tools/generate_workitem.py, tools/manage_workitem_stage.py, tools/manage_frontmatter.py, tools/rename_doc.py, tools/close_procedures_batch.py, tools/fix_docstring_paths.py, tools/fix_docstring_blank_line.py, tools/mark_procedure_new_symbols.py, tests/tools/test_atomic_write.py, tests/tools/test_module_nodes_extract_atomic.py, tests/tools/test_set_execution_status.py, tests/tools/test_generate_workitem.py, tests/tools/test_fix_docs_section_marks.py, tests/tools/test_fix_procedure_new_markers.py, tests/tools/test_migrate_runtime_tool_calls.py, tests/tools/test_fix_docstring_blank_line.py, tools/TOOL_DESCRIPTIONS.md

### Requirement Traceability
| Requirement ID | Source Issue section or evidence | Target file | Implementation step | Acceptance criterion | Test or validation item | Status |
|---|---|---|---|---|---|---|
| REQ-001 | Required Changes 1; Implementation Intent | `tools/_atomic_write.py` | 1 | AC-1 | `test_atomic_write.py` | Explicit in issue |
| REQ-002 | Required Changes 2; Constraints | `tools/_atomic_write.py` | 1 | AC-1 | `test_atomic_write.py` | Explicit in issue |
| REQ-003 | Required Changes 3; Background (`_cmd_extract`, Step 3) | `tools/module_nodes.py` | 2 | AC-2, AC-4 | `test_module_nodes_extract_atomic.py` | Confirmed by repository evidence |
| REQ-004 | Required Changes 2 (six tools without `--dry-run`, Step 3) | `tools/module_nodes.py` | 2 | AC-3 | Dry-run checksum test | Confirmed by repository evidence |
| REQ-004 | Same | `tools/set_execution_status.py` | 3 | AC-3 | `test_set_execution_status.py` | Confirmed by repository evidence |
| REQ-004 | Same | `tools/fix_docs_section_marks.py` | 3 | AC-3 | `test_fix_docs_section_marks.py` | Confirmed by repository evidence |
| REQ-004 | Same | `tools/fix_procedure_new_markers.py` | 3 | AC-3 | `test_fix_procedure_new_markers.py` | Confirmed by repository evidence |
| REQ-004 | Same | `tools/migrate_runtime_tool_calls.py` | 3 | AC-3 | `test_migrate_runtime_tool_calls.py` | Confirmed by repository evidence |
| REQ-004 | Same | `tools/generate_workitem.py` | 3 | AC-3 | `test_generate_workitem.py` | Confirmed by repository evidence |
| REQ-005 | Required Changes 4; Acceptance Criteria 3 | `tools/manage_workitem_stage.py` | 4 | AC-5 | `test_manage_workitem_stage.py` | Explicit in issue |
| REQ-005 | Same | `tools/manage_frontmatter.py` | 4 | AC-5 | `test_manage_frontmatter.py` | Explicit in issue |
| REQ-005 | Same | `tools/rename_doc.py` | 4 | AC-5 | `test_rename_doc.py` | Explicit in issue |
| REQ-005 | Same | `tools/close_procedures_batch.py` | 4 | AC-5 | `test_close_procedures_batch.py` | Explicit in issue |
| REQ-005 | Same | `tools/fix_docstring_paths.py` | 4 | AC-5 | `test_fix_docstring_paths.py` | Explicit in issue |
| REQ-005 | Same | `tools/fix_docstring_blank_line.py` | 4 | AC-5 | `test_fix_docstring_blank_line.py` | Explicit in issue |
| REQ-005 | Same | `tools/mark_procedure_new_symbols.py` | 4 | AC-5 | `test_mark_procedure_new_symbols.py` | Explicit in issue |
| REQ-006 | Background (writes without encoding, Step 3) | `tools/set_execution_status.py` | 3 | AC-3 | Dry-run and write tests | Confirmed by repository evidence |
| REQ-006 | Same | `tools/migrate_runtime_tool_calls.py` | 3 | AC-3 | `test_migrate_runtime_tool_calls.py` | Confirmed by repository evidence |
| REQ-007 | Testing Expectations; Acceptance Criteria 2, 4 | `tests/tools/test_atomic_write.py` | 1 | AC-1 | Helper tests | Explicit in issue |
| REQ-007 | Same | `tests/tools/test_module_nodes_extract_atomic.py` | 2 | AC-2 | Fault-injection test | Explicit in issue |
| REQ-007 | Same | `tests/tools/test_set_execution_status.py` | 3 | AC-3 | Dry-run test | Explicit in issue |
| REQ-007 | Same | `tests/tools/test_generate_workitem.py` | 3 | AC-3 | Dry-run test | Explicit in issue |
| REQ-007 | Same | `tests/tools/test_fix_docs_section_marks.py` | 3 | AC-3 | Dry-run test | Explicit in issue |
| REQ-007 | Same | `tests/tools/test_fix_procedure_new_markers.py` | 3 | AC-3 | Dry-run test | Explicit in issue |
| REQ-007 | Same | `tests/tools/test_migrate_runtime_tool_calls.py` | 3 | AC-3 | Dry-run test | Explicit in issue |
| REQ-007 | Same | `tests/tools/test_fix_docstring_blank_line.py` | 4 | AC-5 | Regression test | Explicit in issue |
| REQ-008 | Documentation Impact | `tools/TOOL_DESCRIPTIONS.md` | 5 | AC-6 | `check_tool_descriptions_sync.py` | Explicit in issue |