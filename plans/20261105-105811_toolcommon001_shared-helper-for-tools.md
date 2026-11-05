## Goal
- One private helper module under `tools/` provides repository-root resolution, a `git` runner with a uniform error and encoding policy, and the exit-code constants of the CLI convention; the eight tools that wrap `git` migrate to it in small batches with identical behavior, and the supported invocation forms are documented.

## Priority
Medium

## Scope
- **In-Scope**: add `tools/_tool_common.py` with tests; migrate the eight git-wrapper tools (`check_adr_preservation.py`, `classify_changes.py`, `check_workitem_traceability.py`, `rename_doc.py`, `scan_change_consumers.py`, `module_nodes.py`, `run_validation_gates.py`, `manage_binaries.py`) in three batches, removing their local git runners and, where present, local `REPO_ROOT`; document the helper and the currently supported invocation forms in `tools/TOOL_DESCRIPTIONS.md`.
- **Out-of-Scope**: removing the `sys.path` bootstrap from the 24 guarded files and the `REPO_ROOT` definitions from the other 22 files (follow-up Plans after the invocation decision, UNK-01); converting CI workflows, pre-commit hooks, `deploy/deploy.sh`, and docs to one invocation form; changing any tool's checks, exit codes, or output; splitting large tools.
- **Dependencies**: lands after the mypy scope Plan, the tests Plan, and the CLI-convention Plan (exit-code constants follow the convention).
  - **Depends on**: plans/20261105-105442_toolmypy001_add-tools-to-mypy-scope.md | phase all | the helper and the migrated tools must be type-checked
  - **Depends on**: plans/20261105-105344_toolstest001_add-tests-for-untested-tools.md | phase all | `module_nodes.py` needs its tests before its git call moves
  - **Depends on**: plans/20261105-105637_toolcli001_define-cli-and-exit-code-convention.md | phase 2 | the exit-code constants implement the documented convention
  - **Depends on**: plans/20261105-105230_tracecompanion001_scope-companion-candidates-to-target-plan.md | phase all | both Plans modify `tools/check_workitem_traceability.py`; the smaller defect fix lands first

## Background
Verified on 2026-11-05 (checked in Steps 2 and 3): the guarded `sys.path` bootstrap appears in 24 files (27 contain a `sys.path.insert`); `REPO_ROOT = Path(__file__).resolve().parent.parent` is defined in 23 files; eight files call `git` through `subprocess` with their own wrappers, each with its own error and encoding handling (`check_adr_preservation.py` `_git` with `text=True`; `classify_changes.py` bytes output with `errors="replace"` on stderr; `check_workitem_traceability.py` `_git_or_mtime`; `rename_doc.py` `check=True` calls and `git_mv`; `scan_change_consumers.py` `git ls-files` bytes; `module_nodes.py` `git show` with `check=True`; `run_validation_gates.py` `_git_diff_name_only`; `manage_binaries.py` `_git`). Invocation is mixed: `.pre-commit-config.yaml` uses `uv run python -m tools.*` (19 hooks) and the CI workflows use `python tools/<name>.py`: 7 steps in `ci.yml`, 8 in `governance-docs-consistency.yml`, one each in seven other workflow files, plus three `python3 "${REPO_ROOT}/tools/manage_binaries.py"` calls in `deploy/deploy.sh`. Tests import `tools.<name>` and the tests of five of the eight tools exercise git through real temporary repositories or an injected runner, not by patching the tool's own wrapper.

## Problem
The same code is repeated and has already diverged in error and encoding handling, so any fix must be applied in many places.

## Reason for Change
Maintenance risk; not urgent, and best done after tests and type checks cover `tools/` (the Plans this one depends on).

## Implementation Intent
Introduce `tools/_tool_common.py` (private, `_`-prefixed) with `REPO_ROOT`, `run_git`, and the three exit-code constants, and migrate the git-wrapper tools in three batches with the whole `tests/tools` suite run after each. Each migrated file keeps working in every invocation form it has today; where it lacks the repository's existing guarded bootstrap and needs it to import the helper, it gains that existing idiom, to be removed by the follow-up Plans once the invocation form is decided.

## Requirements
- `REQ-001`: `tools/_tool_common.py` MUST provide a single `REPO_ROOT`, a `run_git` function with one documented error and encoding policy (UTF-8 text mode with replacement on undecodable bytes, and a bytes mode for NUL-delimited output), and the exit-code constants `0`, `1`, `2` named per the CLI convention.
- `REQ-002`: `tests/tools/test_tool_common.py` MUST cover success, git failure (non-zero exit with and without `check`), and non-UTF-8 output.
- `REQ-003`: The eight git-wrapper tools MUST call the helper instead of a local git runner, and MUST NOT keep a local copy of repository-root resolution; each tool's checks, exit codes, and output MUST stay identical, preserving any difference in error handling at the call site.
- `REQ-004`: Migration MUST proceed in three batches, each leaving `uv run pytest tests/tools -q` and the validation gates green.
- `REQ-005`: Each migrated tool MUST still work in every invocation form it has today (`-m tools.<name>`, `tools/<name>.py` by path where used, test import), verified for one tool in both forms and for `manage_binaries.py` by path as `deploy/deploy.sh` calls it.
- `REQ-006`: `tools/TOOL_DESCRIPTIONS.md` MUST list the private helper and state the currently supported invocation forms and the migration status.

## Implementation Target Files
**Freeze status**: Frozen

| File Path | Change Responsibility | Reason for Modification | Related Requirement / Acceptance Criterion | Repository Evidence | Related Tests | Validation Status |
|---|---|---|---|---|---|---|
| `tools/_tool_common.py` | Shared helper | New file; `tools/` exists and holds the other `_`-prefixed private modules | `REQ-001`; AC-1 | Private-module convention (`_docs_consistency_lib.py`, `_front_matter_schema.py`) (checked in Step 3) | `tests/tools/test_tool_common.py` | Verified |
| `tests/tools/test_tool_common.py` | Helper tests | New file; `tests/tools/` exists | `REQ-002`; AC-1 | No existing helper tests; `tests/tools/test_classify_changes.py` shows the temporary-repository style (checked in Step 3) | itself | Verified |
| `tools/check_adr_preservation.py` | Migrate git runner and `REPO_ROOT` | Replace `_git` and the local `REPO_ROOT` with the helper | `REQ-003`, `REQ-004`; AC-2, AC-3 | `_git(*args)` with `subprocess.run(["git", *args], cwd=REPO_ROOT, ...)`; local `REPO_ROOT` and bootstrap (checked in Step 3) | `tests/tools/test_check_adr_preservation.py` | Verified |
| `tools/classify_changes.py` | Migrate git runner | Replace the bytes-mode `subprocess.run` call with the helper's bytes mode | `REQ-003`, `REQ-004`; AC-2, AC-3 | `subprocess.run` with `errors="replace"` stderr handling (checked in Step 3) | `tests/tools/test_classify_changes.py` | Verified |
| `tools/check_workitem_traceability.py` | Migrate git call | Replace the `subprocess.run` in `_git_or_mtime` with the helper | `REQ-003`, `REQ-004`; AC-2, AC-3 | `_git_or_mtime` calls `subprocess.run` with `text=True, check=False` (checked in Step 3) | `tests/tools/test_check_workitem_traceability.py` | Verified |
| `tools/rename_doc.py` | Migrate git calls | Replace the `git ls-files` call and `git_mv` subprocess calls with the helper | `REQ-003`, `REQ-004`; AC-2, AC-3 | `subprocess.run(..., check=True)` calls and `git_mv` (checked in Step 3) | `tests/tools/test_rename_doc.py` | Verified |
| `tools/scan_change_consumers.py` | Migrate git call | Replace the `git ls-files` call with the helper's bytes mode | `REQ-003`, `REQ-004`; AC-2, AC-3 | `subprocess.run` with `stderr.decode(errors="replace")` error message (checked in Step 3) | `tests/tools/test_scan_change_consumers.py` | Verified |
| `tools/module_nodes.py` | Migrate git call | Replace the `git show` call in `_cmd_compare` with the helper | `REQ-003`, `REQ-004`; AC-2, AC-3 | `subprocess.run(..., check=True)` in `_cmd_compare` (checked in Step 3) | `tests/tools/test_module_nodes.py` (from the tests Plan) | Verified |
| `tools/run_validation_gates.py` | Migrate git call | Replace the `_git_diff_name_only` subprocess call with the helper; the gate runner stays | `REQ-003`, `REQ-004`; AC-2, AC-3 | `_git_diff_name_only` and a separate `_subprocess_runner` for gates (checked in Step 3) | `tests/tools/test_run_validation_gates.py` | Verified |
| `tools/manage_binaries.py` | Migrate git helper | Replace `_git(repo, *args)` with the helper; keep working when `deploy/deploy.sh` runs it by path | `REQ-003`, `REQ-004`, `REQ-005`; AC-2, AC-3, AC-4 | `_git` at module level; `deploy/deploy.sh` calls it three times with `python3` by path (checked in Step 3) | `tests/tools/test_manage_binaries.py` | Verified |
| `tools/TOOL_DESCRIPTIONS.md` | Document helper and invocation forms | Add the helper row and an invocation-forms note | `REQ-006`; AC-5 | Index lists private modules with a `(private)` category (checked in Step 3) | `uv run python tools/check_tool_descriptions_sync.py` | Verified |

## Reference Files
| File Path | Why It Must Be Read | Related Target File or Requirement |
|---|---|---|
| `.pre-commit-config.yaml` | Hooks call tools as `python -m tools.<name>` | `REQ-005` |
| `.github/workflows/ci.yml` | Steps call tools by path | `REQ-005` |
| `.github/workflows/governance-docs-consistency.yml` | Eight steps call tools by path | `REQ-005` |
| `deploy/deploy.sh` | Runs `tools/manage_binaries.py` by path on the deploy path | `REQ-005` |
| `tools/_docs_consistency_lib.py` | Existing private helper whose import style the new helper follows | `REQ-001` |
| `tools/check_adr_structure.py` | Example of the guarded bootstrap plus `from tools._docs_consistency_lib import` idiom | `REQ-005` |
| `tests/conftest.py` | Puts `tools/` on `sys.path` for all tests | `REQ-002` |
| `rules/coding.md` | Explicit sign-off gate rule used for the invocation decision | `REQ-006` |

## Acceptance Criteria
- AC-1: One implementation of repository-root resolution and the git runner exists in `tools/_tool_common.py` with passing tests for success, git failure, and non-UTF-8 output (`REQ-001`, `REQ-002`).
- AC-2: None of the eight migrated tools keeps a local git runner or local `REPO_ROOT` (`rg` finds no `subprocess.run` of `git` and no `REPO_ROOT =` definition in them) (`REQ-003`).
- AC-3: After each batch `uv run pytest tests/tools -q` and `uv run python tools/run_validation_gates.py` pass, and each tool's exit code and output match a before-and-after run on live data (`REQ-003`, `REQ-004`).
- AC-4: One migrated tool is run in both `python -m tools.<name>` and `python tools/<name>.py` forms, and `python3 tools/manage_binaries.py` works by path (`REQ-005`).
- AC-5: `tools/TOOL_DESCRIPTIONS.md` lists the helper and states the supported invocation forms, and `check_tool_descriptions_sync.py` passes (`REQ-006`).

## Tests
- Unit tests for the helper (success, git failure with and without `check`, non-UTF-8 bytes in stdout and stderr, bytes mode, working directory) in `tests/tools/test_tool_common.py` (`REQ-001`, `REQ-002`).
- Regression: the existing per-tool tests (target rows) run after each batch (`REQ-003`, `REQ-004`).
- Invocation smoke: the same read-only subcommand of one tool in both invocation forms and `python3 tools/manage_binaries.py --help` (`REQ-005`).

## Documentation Impact
Yes: `tools/TOOL_DESCRIPTIONS.md` (helper entry, invocation forms, migration status) (`REQ-006`). Docs that state how tools are called (`skills/`, `rules/`, `routing.md`) change only in the follow-up Plans after the invocation decision; no `docs/*.md` file is affected.

## Assumptions
- The helper is imported as `tools._tool_common`, matching `tools._docs_consistency_lib` (judgment from the existing style); a migrated file that lacks the guarded bootstrap and runs by path gains the existing idiom until the follow-up Plans remove it.
- Where the eight wrappers differ in error handling (raise on failure, return empty, return an exit code), the helper offers `check` and a result object so each call site preserves its current behavior; no tool's behavior is unified in this Plan (Issue Constraints: behavior stays identical).
- The three exit-code constants only define the convention's names; adopting them in other tools is not part of this Plan.
- Overlap judgments (`check_plan_target_overlaps.py`): `tools/TOOL_DESCRIPTIONS.md` is also targeted by the `toolsdocsync001` and `toolcli001` Plans, `tools/check_workitem_traceability.py` by the `tracecompanion001` Plan, and `tools/run_validation_gates.py` by the `toolmypy001` Plan (a gate-command tuple versus the `_git_diff_name_only` call); the changes are in different sections or functions, so they are compatible, with the sequencing recorded in Scope. The later `toolreport001`, `toolwrite001`, and `toolsizegate001` Plans touch the same tools and follow this one.

## Unknowns
| ID | Unknown Description | Evidence Missing | Resolution Path | Blocking? (True/False) |
|---|---|---|---|---|
| UNK-01 | Which invocation form to standardize on (`python -m tools.<name>` versus `tools/<name>.py`) | Owner decision; affects 9 workflow files, `deploy/deploy.sh`, and the documented commands | Owner decides after Phase 4 using the recorded invocation facts; sign-off as a comment on this Plan (`rules/coding.md` Explicit sign-off gates); the follow-up Plans for bootstrap and `REPO_ROOT` removal and caller conversion are filed after the decision. This Plan does not depend on it | False |
| UNK-02 | Whether any consumer outside the repository calls `tools/<name>.py` by path | Cannot be searched from the repository; `deploy/deploy.sh` is the only on-host caller found | Keep the path form working for every migrated tool (`REQ-005`); ask the owner before the follow-up removes the bootstrap | False |
| UNK-03 | Whether the remaining 22 `REPO_ROOT` files and 24 bootstrap files should migrate "when otherwise touched" or in dedicated batches | Issue allows either | Decide with UNK-01; file one follow-up issue per batch | False |

## Affected areas
| File | Change | Blast Radius | Churn (30d) | Bus Factor | deploy.sh Impact |
|---|---|---|---|---|---|
| `tools/_tool_common.py` | Create | Medium (imported by eight tools; no importer yet) | N/A | High (one author across the repository history) | not applicable (rsynced) |
| `tests/tools/test_tool_common.py` | Create | Low | N/A | High | not applicable (rsynced) |
| `tools/check_adr_preservation.py` | Modify | Medium (pre-commit and CI) | N/A (outside top 60) | High | not applicable (rsynced) |
| `tools/classify_changes.py` | Modify | Low | N/A | High | not applicable (rsynced) |
| `tools/check_workitem_traceability.py` | Modify | Medium (pre-commit hook) | 7 | High | not applicable (rsynced) |
| `tools/rename_doc.py` | Modify | Low | N/A | High | not applicable (rsynced) |
| `tools/scan_change_consumers.py` | Modify | Low | N/A | High | not applicable (rsynced) |
| `tools/module_nodes.py` | Modify | Medium (edits production source during splits) | N/A | High | not applicable (rsynced) |
| `tools/run_validation_gates.py` | Modify | Medium (gate entry point) | 9 | High | not applicable (rsynced) |
| `tools/manage_binaries.py` | Modify | High (run by `deploy/deploy.sh` on the deploy path) | N/A | High | not applicable (rsynced) |
| `tools/TOOL_DESCRIPTIONS.md` | Modify | Low | 82 | High | not applicable (rsynced) |

## Design
- Path B (more than 3 files, new module). Architecture analysis: `tools/` is outside the `.importlinter` contracts; the helper imports only the standard library, so it creates no cycle. Dependency graphing: the eight tools were found by `rg 'subprocess'` plus `"git"` over `tools/*.py`; their callers are pre-commit (`-m` form), CI (path form), `deploy/deploy.sh` (path form, `manage_binaries.py` only), and tests (`tools.<name>` import). Historical analysis: churn figures are in the Affected areas table and all history is by one author. Operational dependency inspection: `deploy/deploy.sh` runs `manage_binaries.py swap`, `check`, and `record-revision` on the deploy path, so `manage_binaries.py` migrates last and is smoke-tested by path; no MCP server or database is touched.
- Validation quality baseline: `radon cc` grades `manage_binaries.py` `_run` C (17), `_check_binary` C (11), `swap` C (11), and `check_adr_preservation.py` `compare` D (22); migration MUST NOT raise any grade. `vulture` and `bandit` baselines on `scripts/` are unrelated and unchanged. diff-cover baseline: `N/A: no diff exists before implementation`; at least 90 percent on changed lines is required (`rules/toolchain.md`).
- Helper design (decisions): module `tools/_tool_common.py`; `REPO_ROOT: Path`; `run_git(*args, cwd: Path | None = None, check: bool = False, binary: bool = False)` returning `subprocess.CompletedProcess` with `encoding="utf-8", errors="replace"` in text mode; `EXIT_OK`, `EXIT_FINDINGS`, `EXIT_ERROR`. Alternatives rejected: a class wrapping git state (more surface than the Issue asks); a helper per concern (the Issue asks for one small module). Compatibility impact: none for callers, because only the eight migrating tools import it.
- Persisted-schema, public-API, and shared-constant consumer scan: the exit-code constants are new names (no existing consumers); `REPO_ROOT` in the helper is new and the 23 existing definitions are untouched except in migrated files.

## Implementation steps
1. **Phase 1: Helper with failing tests**
   - [ ] Add the helper tests, then the helper (`REQ-001`, `REQ-002`; `tests/tools/test_tool_common.py`, `tools/_tool_common.py`)
2. **Phase 2: Batch 1 (read-mostly tools)**
   - [ ] Migrate `check_workitem_traceability.py`, `classify_changes.py`, and `scan_change_consumers.py`; run `tests/tools` (`REQ-003`, `REQ-004`; `tools/check_workitem_traceability.py`, `tools/classify_changes.py`, `tools/scan_change_consumers.py`)
3. **Phase 3: Batch 2 (tools that move or gate source)**
   - [ ] Migrate `module_nodes.py`, `rename_doc.py`, and `run_validation_gates.py`; run `tests/tools` and the gates (`REQ-003`, `REQ-004`; `tools/module_nodes.py`, `tools/rename_doc.py`, `tools/run_validation_gates.py`)
4. **Phase 4: Batch 3 (deploy-path tools)**
   - [ ] Migrate `check_adr_preservation.py` and `manage_binaries.py`; run `tests/tools` and the path-form smoke (`REQ-003`, `REQ-004`, `REQ-005`; `tools/check_adr_preservation.py`, `tools/manage_binaries.py`)
5. **Phase 5: Documentation and verification**
   - [ ] Add the helper row and invocation-forms note; run `check_tool_descriptions_sync.py`, the per-file checks of `routing.md` "Adding a new tool", the invocation smoke in both forms, and the before-and-after live-data comparison (`REQ-005`, `REQ-006`; `tools/TOOL_DESCRIPTIONS.md` and all tool rows). No deploy step is part of this Plan: no `scripts/` or `config/` file changes. `tools/manage_binaries.py` runs on the deploy path, so deploying after commit and push is the user's separate decision (`skills/deploy/SKILL.md`).

### Release units
N/A: no release unit

## Validation plan
| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| `tools/_tool_common.py` | Unit | `uv run pytest tests/tools/test_tool_common.py -q` | All pass |
| each migrated tool | Regression per batch | `uv run pytest tests/tools -q` | No new failure |
| each migrated tool | Before-and-after run on live data | Run the tool's read-only mode before and after and compare exit code and output | Identical |
| one tool plus `manage_binaries.py` | Invocation integration | `uv run python -m tools.<name> --help` and `uv run python tools/<name>.py --help`; `python3 tools/manage_binaries.py --help` | Both forms work |
| all changed Python files | Lint, type, security (paths explicit) | `uv run ruff format`, `uv run ruff check`, `uv run mypy --no-namespace-packages <files>`, `uv run bandit <files>` | Clean |
| diff | Gates | `uv run python tools/run_validation_gates.py` | Pass |
| `tools/TOOL_DESCRIPTIONS.md` | Sync check | `uv run python tools/check_tool_descriptions_sync.py` | `No issues found.` |
| patched symbols | Mock-patch check | `uv run python tools/check_mock_patch_targets.py` | No finding |

## Risks
- **Risk**: A migrated file breaks under an invocation form it used before (especially `manage_binaries.py` on the deploy path) → **Mitigation**: `REQ-005` smoke in every form, `manage_binaries.py` last, and a path-form run before any deploy.
- **Risk**: A uniform helper policy silently changes a tool's error handling or output → **Mitigation**: preserve each call site's handling, compare before and after on live data, and migrate three files per batch.
- **Risk**: Adding the guarded bootstrap to files that lack it adds temporary duplication → **Mitigation**: recorded as an accepted trade-off; the follow-up Plans remove all bootstrap copies after UNK-01.
- **Risk**: The helper becomes a dumping ground → **Mitigation**: scope is limited to `REPO_ROOT`, `run_git`, and the exit-code constants (Issue Out of Scope).
- **Risk**: Several Plans edit the same tools (`tracecompanion001`, `toolreport001`, `toolwrite001`, `toolsizegate001`) → **Mitigation**: sequencing in Scope and one batch per commit; re-run `check_plan_target_overlaps.py` at each procedure generation.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Add the helper and its tests | Pending | — | — | |
| 2 | Migrate batch 1 (three read-mostly tools) | Pending | — | — | |
| 3 | Migrate batch 2 (three source-moving or gating tools) | Pending | — | — | |
| 4 | Migrate batch 3 (two deploy-path tools) | Pending | — | — | |
| 5 | Document the helper and invocation forms; verify | Pending | — | — | |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| — | — | — | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| — | — | — | — | — | — |

## Traceability
- **Workflow phase**: issue-to-plan
- **Source issue**: issues/20261104-152002_toolcommon001_shared-helper-for-tools.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: this document is the generated plan
- **Source implementation procedure**: N/A: not applicable in this phase
- **Generated at**: 20261105-105811
- **Related target files**: tools/_tool_common.py, tests/tools/test_tool_common.py, tools/check_adr_preservation.py, tools/classify_changes.py, tools/check_workitem_traceability.py, tools/rename_doc.py, tools/scan_change_consumers.py, tools/module_nodes.py, tools/run_validation_gates.py, tools/manage_binaries.py, tools/TOOL_DESCRIPTIONS.md

### Requirement Traceability
| Requirement ID | Source Issue section or evidence | Target file | Implementation step | Acceptance criterion | Test or validation item | Status |
|---|---|---|---|---|---|---|
| REQ-001 | Implementation Intent; Required Changes 2 | `tools/_tool_common.py` | 1 | AC-1 | `test_tool_common.py` | Explicit in issue |
| REQ-002 | Testing Expectations (helper tests) | `tests/tools/test_tool_common.py` | 1 | AC-1 | `test_tool_common.py` | Explicit in issue |
| REQ-003 | Acceptance Criteria 1, 2; Background (eight git wrappers, Step 3) | `tools/check_adr_preservation.py` | 4 | AC-2, AC-3 | `test_check_adr_preservation.py`; live-data comparison | Confirmed by repository evidence |
| REQ-003 | Same | `tools/classify_changes.py` | 2 | AC-2, AC-3 | `test_classify_changes.py` | Confirmed by repository evidence |
| REQ-003 | Same | `tools/check_workitem_traceability.py` | 2 | AC-2, AC-3 | `test_check_workitem_traceability.py` | Confirmed by repository evidence |
| REQ-003 | Same | `tools/rename_doc.py` | 3 | AC-2, AC-3 | `test_rename_doc.py` | Confirmed by repository evidence |
| REQ-003 | Same | `tools/scan_change_consumers.py` | 2 | AC-2, AC-3 | `test_scan_change_consumers.py` | Confirmed by repository evidence |
| REQ-003 | Same | `tools/module_nodes.py` | 3 | AC-2, AC-3 | `test_module_nodes.py` | Confirmed by repository evidence |
| REQ-003 | Same | `tools/run_validation_gates.py` | 3 | AC-2, AC-3 | `test_run_validation_gates.py` | Confirmed by repository evidence |
| REQ-003 | Same | `tools/manage_binaries.py` | 4 | AC-2, AC-3 | `test_manage_binaries.py` | Confirmed by repository evidence |
| REQ-004 | Constraints (do not migrate in one large change); Acceptance Criteria 4 | `tools/check_workitem_traceability.py` | 2, 3, 4 | AC-3 | `uv run pytest tests/tools -q` after each batch | Explicit in issue |
| REQ-005 | Testing Expectations (both invocation forms); `deploy/deploy.sh` (Step 3) | `tools/manage_binaries.py` | 4, 5 | AC-4 | Path-form smoke | Confirmed by repository evidence |
| REQ-006 | Required Changes 1; Documentation Impact | `tools/TOOL_DESCRIPTIONS.md` | 5 | AC-5 | `check_tool_descriptions_sync.py` | Explicit in issue |
