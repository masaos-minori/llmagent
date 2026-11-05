## Goal
- The module size gate also runs on `tools/` through a separate invocation with its own grandfathering baseline wired into pre-commit, CI, and the validation gates, so a new oversized tool or growth of a baselined tool fails, and the baseline entries of `manage_workitem_stage.py` and `run_validation_gates.py` are reduced by splitting each tool by responsibility while keeping its CLI behavior and import paths.

## Priority
Low

## Scope
- **In-Scope**: a new baseline file for `tools/` holding the 15 current violations; a second invocation of `tools/check_module_size.py` (`--scripts-dir tools --baseline <new baseline>`) in pre-commit, CI, and the `run_validation_gates.py` gate table; tests for the second invocation; the gate scope text in `routing.md`, `rules/toolchain.md`, and `tools/TOOL_DESCRIPTIONS.md`; one split of `tools/manage_workitem_stage.py` and one of `tools/run_validation_gates.py`, in separate changes, each followed by tightening the baseline.
- **Out-of-Scope**: splitting the other 13 oversized tools; changing the 24576 B limit for `scripts/`; changing `check_module_size.py` behavior (the existing `--scripts-dir` and `--baseline` options already select another directory and baseline).
- **Dependencies**: lands last among the `tools/` Plans, because it moves code that they edit.
  - **Depends on**: plans/20261105-105344_toolstest001_add-tests-for-untested-tools.md | phase all | the splits use `module_nodes.py`, which needs its tests first
  - **Depends on**: plans/20261105-105442_toolmypy001_add-tools-to-mypy-scope.md | phase all | the moved code is then type-checked
  - **Depends on**: plans/20261105-105811_toolcommon001_shared-helper-for-tools.md | phase 3 | that phase edits `run_validation_gates.py`, a split target
  - **Depends on**: plans/20261105-110212_toolwrite001_make-mutating-tools-dry-run-and-atomic.md | phase 4 | that phase edits `manage_workitem_stage.py`, a split target

## Background
Verified on 2026-11-05 (checked in Steps 2 and 3): `tools/check_module_size.py` measures `.py` files under the directory given by `--scripts-dir` (default `scripts/`) against 24576 B with a baseline file as a ceiling (`--baseline`), and `tools/check_module_size_baseline.txt` is empty. Fifteen files directly under `tools/` exceed 24576 B (the Issue said 14; corrected in Step 2): `manage_workitem_stage.py` (57,146 B), `generate_reference_table.py` (42,997 B), `run_validation_gates.py` (42,591 B), `check_canonical_source_conflicts.py` (41,349 B), `stale_detector.py` (40,847 B), `check_docs_consistency.py`, `check_workitem_traceability.py`, `check_canonical_source_registry.py`, `check_docs_quality.py`, `check_docs_content_policy.py`, `manage_frontmatter.py`, `check_compat_shims.py`, `generate_workitem.py`, `_adr_authority_core.py`, and `check_docs_structure.py`. The pre-commit hook `check-module-size` runs `python -m tools.check_module_size` with `files` limited to `scripts/` and the checker's own files, and CI runs `python tools/check_module_size.py`. `routing.md`, `rules/toolchain.md`, and `tools/TOOL_DESCRIPTIONS.md` tie the gate to `scripts/` only. `module_nodes.py measure` shows `manage_workitem_stage.py` clusters: `build_parser` (7,201 B), `update_execution_status` (5,528 B), `cmd_close_batch` (4,790 B), `move_to_done` (2,966 B), and a 4,517 B module docstring; `run_validation_gates.py` holds two gate tables of 14,288 B and 2,619 B. `tools/close_procedures_batch.py` and `tools/plan_dependency_order.py` import from `tools.manage_workitem_stage`, and `tests/tools/test_run_validation_gates.py` imports from `tools.run_validation_gates`.

## Problem
Tools have no size discipline, so the files that gate and move workflow documents grow without review limits, and long functions such as `build_parser` are hard to test.

## Reason for Change
Maintainability only; no incident, timing is flexible, and the work is large, hence Low.

## Implementation Intent
Add the gate with a full baseline first so nothing turns red, using the existing options in a second invocation. Then split one tool per change by responsibility (parser construction and the status-table logic from `manage_workitem_stage.py`; the gate tables from `run_validation_gates.py`), keeping the original module as the CLI entry that re-exports the moved names, and tighten the baseline after each split.

## Requirements
- `REQ-001`: A baseline file for `tools/` MUST record the 15 current violations at their current byte sizes, and the existing baseline for `scripts/` MUST stay unchanged.
- `REQ-002`: A second invocation `check_module_size.py --scripts-dir tools --baseline tools/check_module_size_tools_baseline.txt` MUST run in a pre-commit hook and a CI step, and MUST be mapped in `tools/run_validation_gates.py` so the hook-parity drift check passes.
- `REQ-003`: Tests MUST cover the second invocation against a directory named `tools`: a new violation fails, growth of a baselined file fails, shrinkage is reported, and a stale baseline entry fails, with the `scripts/` baseline unaffected.
- `REQ-004`: The gate scope text in `routing.md`, `rules/toolchain.md`, and `tools/TOOL_DESCRIPTIONS.md` MUST state that the gate covers `scripts/` and `tools/` with separate baselines.
- `REQ-005`: `tools/manage_workitem_stage.py` MUST be split by responsibility into `tools/_workitem_status_table.py` and `tools/_workitem_stage_parser.py` plus the reduced entry module, keeping every CLI subcommand, exit code, and the import paths `tools.manage_workitem_stage.<name>` used by `close_procedures_batch.py`, `plan_dependency_order.py`, and the tests, and the baseline entry MUST be reduced afterwards.
- `REQ-006`: `tools/run_validation_gates.py` MUST be split into `tools/_validation_gate_defs.py` (the `Gate` type and the gate tables) plus the reduced entry module, keeping the CLI behavior and the import paths used by `tests/tools/test_run_validation_gates.py`, and the baseline entry MUST be reduced afterwards.
- `REQ-007`: The baseline MUST only shrink: after each split its entries are removed or lowered, and no entry is raised or added except the initial 15.

## Implementation Target Files
**Freeze status**: Frozen

| File Path | Change Responsibility | Reason for Modification | Related Requirement / Acceptance Criterion | Repository Evidence | Related Tests | Validation Status |
|---|---|---|---|---|---|---|
| `tools/check_module_size_tools_baseline.txt` | Baseline for `tools/` | New file; `tools/` exists; holds the 15 current violations, later reduced | `REQ-001`, `REQ-007`; AC-1, AC-5 | 15 files over 24576 B by `wc -c tools/*.py`; the existing baseline is empty (checked in Step 2) | `tests/tools/test_check_module_size.py` | Verified |
| `tests/tools/test_check_module_size.py` | Tests for the second invocation | Add cases using a directory named `tools` and a separate baseline | `REQ-003`; AC-2 | `main` accepts `--scripts-dir` and `--baseline`; existing tests use a `scripts` directory (checked in Step 3) | itself | Verified |
| `.pre-commit-config.yaml` | Pre-commit hook | Add a hook running `python -m tools.check_module_size --scripts-dir tools --baseline tools/check_module_size_tools_baseline.txt` with `files` for `tools/*.py` and the baseline | `REQ-002`; AC-3 | `check-module-size` hook runs the module with `pass_filenames: false` and a `scripts/`-limited `files` regex (checked in Step 3) | `uv run python tools/run_validation_gates.py drift` | Verified |
| `.github/workflows/ci.yml` | CI step | Add a step running the second invocation after "Module size check" | `REQ-002`; AC-3 | Step `Module size check` runs `uv run python tools/check_module_size.py` (checked in Step 3) | N/A: verified by running the command | Verified |
| `tools/run_validation_gates.py` | Gate mapping and split | Add a `check_module_size_tools` routing gate for `tools/*.py`; later move the gate tables into `tools/_validation_gate_defs.py` | `REQ-002`, `REQ-006`; AC-3, AC-6 | `Gate(name="check_module_size", ... patterns=("scripts/*.py", "scripts/**/*.py"))`; 42,591 B with two gate tables of 14,288 B and 2,619 B; `drift` reports hook parity (checked in Step 3) | `tests/tools/test_run_validation_gates.py` | Verified |
| `tests/tools/test_run_validation_gates.py` | Gate-table tests | Add an assertion that the tools size gate is mapped and the re-exported names still import | `REQ-002`, `REQ-006`; AC-3, AC-6 | Imports from `tools.run_validation_gates`; asserts the `mypy` gate name (checked in Step 3) | itself | Verified |
| `tools/_validation_gate_defs.py` | Moved gate definitions | New file; `Gate`, source and mode constants, and the gate tables move here | `REQ-006`; AC-6 | `ROUTING_GATES` and `TOOLCHAIN_GATES` tuples in `run_validation_gates.py` (checked in Step 3) | `tests/tools/test_run_validation_gates.py` | Verified |
| `tools/manage_workitem_stage.py` | Split by responsibility | Move status-table logic and parser construction out; keep CLI entry, subcommands, and re-exports | `REQ-005`; AC-4 | 57,146 B, 1526 lines; `build_parser` 208 lines; `update_execution_status` 146 lines; importers `close_procedures_batch.py` and `plan_dependency_order.py` (checked in Step 3) | `tests/tools/test_manage_workitem_stage.py`, `tests/tools/test_manage_workitem_stage_new.py` | Verified |
| `tools/_workitem_status_table.py` | Moved status-table logic | New file; Execution Status parsing and rewriting move here (for example `parse_execution_status_rows`, `update_execution_status`) | `REQ-005`; AC-4 | `parse_execution_status_rows` is imported from `tools.manage_workitem_stage` by `plan_dependency_order.py` (checked in Step 3) | `tests/tools/test_manage_workitem_stage.py` | Verified |
| `tools/_workitem_stage_parser.py` | Moved parser construction | New file; `build_parser` moves here and receives the command handlers as an argument so the dependency stays one-directional | `REQ-005`; AC-4 | `build_parser` spans 208 lines and registers every subcommand (checked in Step 3) | `tests/tools/test_manage_workitem_stage.py` | Verified |
| `routing.md` | Gate scope text | Update the `check_module_size.py` row scope from `scripts/**/*.py` to `scripts/` and `tools/` | `REQ-004`; AC-5 | Row states the gate covers `scripts/**/*.py` modules only (checked in Step 2) | `uv run python tools/check_skills_references.py` | Verified |
| `rules/toolchain.md` | Gate scope text | Update the module-size command line to name both invocations | `REQ-004`; AC-5 | `uv run python tools/check_module_size.py --top 5` with the `scripts/` scope comment (checked in Step 3) | `uv run python tools/check_skills_references.py` | Verified |
| `tools/TOOL_DESCRIPTIONS.md` | Gate scope text and new modules | Update the two `check_module_size.py` rows and add rows for the three new private modules | `REQ-004`, `REQ-005`, `REQ-006`; AC-5 | Index and "Module Size Gate" section describe `scripts/` only (checked in Step 3) | `uv run python tools/check_tool_descriptions_sync.py` | Verified |

## Reference Files
| File Path | Why It Must Be Read | Related Target File or Requirement |
|---|---|---|
| `tools/check_module_size.py` | `--scripts-dir` and `--baseline` already select another directory and baseline; baseline entries are relative paths | `REQ-001`, `REQ-002`, `REQ-003` |
| `tools/check_module_size_baseline.txt` | Existing `scripts/` baseline (empty); format reference | `REQ-001` |
| `skills/python-refactoring/path-c.md` | Path C split rules the splits follow | `REQ-005`, `REQ-006` |
| `tools/module_nodes.py` | Measures clusters and moves nodes verbatim; `compare` proves a move changed nothing | `REQ-005`, `REQ-006` |
| `tools/close_procedures_batch.py` | Imports names from `tools.manage_workitem_stage` that must keep resolving | `REQ-005` |
| `tools/plan_dependency_order.py` | Imports `parse_execution_status_rows` from `tools.manage_workitem_stage` | `REQ-005` |
| `tools/close_procedure.sh` | Calls `manage_workitem_stage.py close-implementation` by path | `REQ-005` |

## Acceptance Criteria
- AC-1: The new baseline holds exactly the 15 current violations at their current sizes and the `scripts/` baseline is unchanged (`REQ-001`).
- AC-2: The second invocation fails on a new oversized tool and on growth of a baselined one, reports shrinkage, and fails on a stale entry, shown by tests (`REQ-003`).
- AC-3: The gate runs in pre-commit, CI, and `run_validation_gates.py`, and `uv run python tools/run_validation_gates.py drift` reports parity (`REQ-002`).
- AC-4: After the `manage_workitem_stage.py` split, every subcommand and import path works, its baseline entry is lower, and all existing tests pass (`REQ-005`, `REQ-007`).
- AC-5: The gate scope text in `routing.md`, `rules/toolchain.md`, and `tools/TOOL_DESCRIPTIONS.md` is updated and their checkers pass (`REQ-004`).
- AC-6: After the `run_validation_gates.py` split, its CLI behavior and imports are unchanged, its baseline entry is lower, and all existing tests pass (`REQ-006`, `REQ-007`).

## Tests
- Unit: the second-invocation cases in `tests/tools/test_check_module_size.py` (new violation, growth, shrinkage, stale entry, separate baselines) (`REQ-003`).
- Unit: the gate-mapping assertion and re-export check in `tests/tools/test_run_validation_gates.py` (`REQ-002`, `REQ-006`).
- Regression: `uv run pytest tests/tools -q` after each phase, plus a before-and-after run of each split tool's subcommands on live data (`REQ-005`, `REQ-006`).
- Move proof: `module_nodes.py compare` for the moved functions against their pre-move source (`REQ-005`, `REQ-006`).

## Documentation Impact
Yes: the gate scope text in `routing.md` and `rules/toolchain.md`, and the rows and the "Module Size Gate" section of `tools/TOOL_DESCRIPTIONS.md` (`REQ-004`, `REQ-005`, `REQ-006`). No `docs/*.md` file is affected.

## Assumptions
- A separate invocation of the existing checker satisfies the Issue's "second directory or separate invocation" and needs no change to `check_module_size.py` (judgment from the verified `--scripts-dir` and `--baseline` options); a test confirms a directory named `tools` works.
- The new module names are decided here by responsibility (status table, parser, gate definitions); if measuring at procedure time shows a different boundary, the Plan is amended with `tools/amend_plan.py`.
- "Removed or reduced" (Issue Acceptance Criteria 3) is satisfied by a lower baseline size; the splits are not required to bring a tool under 24576 B.
- The existing 24576 B limit is used for `tools/`; whether it is the right limit stays open (UNK-01).
- Overlap judgments (`check_plan_target_overlaps.py`): `tools/run_validation_gates.py` is also targeted by the `toolmypy001` and `toolcommon001` Plans, `tools/TOOL_DESCRIPTIONS.md` by five Plans, `tools/manage_workitem_stage.py` by the `toolwrite001` Plan, and `.github/workflows/ci.yml`, `routing.md`, and `rules/toolchain.md` by the `toolmypy001` Plan; the other Plans change a gate tuple, a git call, a heading or section, a write call, or the mypy scope line, while this Plan moves code or edits the module-size lines, so the changes are compatible and this Plan is sequenced last (Scope).

## Unknowns
| ID | Unknown Description | Evidence Missing | Resolution Path | Blocking? (True/False) |
|---|---|---|---|---|
| UNK-01 | Whether 24576 B is the right limit for `tools/` | Owner judgment | Keep the default; the `--limit` option allows a later change without code edits | False |
| UNK-02 | Exact cluster boundaries for the two splits | `module_nodes.py measure` at finer granularity | Measure at procedure generation; amend the Plan rows if names or boundaries change | False |
| UNK-03 | How `plan-to-implementation-procedure` should order the two split changes against the other `tools/` Plans' procedures | Not decided | Follow Scope Dependencies; confirm with `tools/plan_dependency_order.py --plan <path>` | False |

## Affected areas
| File | Change | Blast Radius | Churn (30d) | Bus Factor | deploy.sh Impact |
|---|---|---|---|---|---|
| `tools/check_module_size_tools_baseline.txt` | Create | Low (read only by the second invocation) | N/A | High (one author across the repository history) | not applicable (rsynced) |
| `tests/tools/test_check_module_size.py` | Modify | Low | N/A (outside top 60) | High | not applicable (rsynced) |
| `.pre-commit-config.yaml` | Modify | Medium (new hook runs on every `tools/` commit) | 12 | High | not applicable (rsynced) |
| `.github/workflows/ci.yml` | Modify | Medium (CI gate) | 14 | High | not applicable (rsynced) |
| `tools/run_validation_gates.py` | Modify | High (gate entry point; split moves its tables) | 9 | High | not applicable (rsynced) |
| `tests/tools/test_run_validation_gates.py` | Modify | Low | 6 | High | not applicable (rsynced) |
| `tools/_validation_gate_defs.py` | Create | Medium (new home of the gate tables) | N/A | High | not applicable (rsynced) |
| `tools/manage_workitem_stage.py` | Modify | High (moves and edits workflow documents; imported by two tools; used by skills) | 5 | High | not applicable (rsynced) |
| `tools/_workitem_status_table.py` | Create | Medium | N/A | High | not applicable (rsynced) |
| `tools/_workitem_stage_parser.py` | Create | Medium | N/A | High | not applicable (rsynced) |
| `routing.md` | Modify | Low (loaded by every workflow) | 26 | High | not applicable (rsynced) |
| `rules/toolchain.md` | Modify | Low | 13 | High | not applicable (rsynced) |
| `tools/TOOL_DESCRIPTIONS.md` | Modify | Low | 82 | High | not applicable (rsynced) |

## Design
- Path B (more than 3 files, new modules). Architecture analysis: `tools/` is outside the `.importlinter` contracts; the new modules form a one-directional dependency (entry module imports `_workitem_status_table` and `_workitem_stage_parser`; the parser receives handlers as arguments; `run_validation_gates.py` imports `_validation_gate_defs`), so no cycle arises. Dependency graphing: `rg` found importers of `manage_workitem_stage` in `close_procedures_batch.py`, `plan_dependency_order.py`, and the tests, a path-form call in `tools/close_procedure.sh`, and pre-commit and CI callers of `check_module_size`; `tests/tools/test_run_validation_gates.py` imports from `tools.run_validation_gates`. Historical analysis: churn figures are in the Affected areas table and all history is by one author. Operational dependency inspection: not applicable (no MCP server, database, or dependency change).
- Validation quality baseline: `radon cc` grades in `manage_workitem_stage.py` `update_execution_status` D (30), `cmd_close_batch` D (21), `cmd_list` D (21), `cmd_list_order` C (16), `parse_execution_status_rows` C (14), `parse_execution_status_table` C (14), `_find_owning_plan` C (14), `cmd_set_step_status` C (12), and `move_to_done` C (11), and in `run_validation_gates.py` `_checker_id_from_command` C (16); the splits move code verbatim and MUST NOT raise any grade, and `update_execution_status` and `cmd_close_batch` are the highest-risk moves. `vulture` and `bandit` baselines on `scripts/` are unrelated and unchanged. diff-cover baseline: `N/A: no diff exists before implementation`; at least 90 percent on changed lines is required (`rules/toolchain.md`).
- Design decisions: (1) separate baseline file and invocation instead of a multi-directory checker (smaller change; the existing options suffice); (2) original modules stay the CLI entry and re-export moved names so pre-commit, CI, path-form callers, and tests are unaffected; (3) parser construction receives handlers as an argument to avoid a circular import. Alternatives rejected: extending `check_module_size.py` to take two directories (new behavior and tests for no gain); moving every cluster out of the large tools (exceeds the Issue's "reduce" criterion).
- Consumer scan: no persisted schema or public API changes; the moved names' consumers were enumerated by the `rg` searches above.

## Implementation steps
1. **Phase 1: Gate for `tools/`**
   - [ ] Add the failing second-invocation tests, then create the baseline from the current violations (`--update-baseline` on `tools`), and verify it lists exactly the 15 files (`REQ-001`, `REQ-003`, `REQ-007`; `tests/tools/test_check_module_size.py`, `tools/check_module_size_tools_baseline.txt`)
   - [ ] Add the pre-commit hook, CI step, and `check_module_size_tools` gate mapping; confirm hook parity with `drift` (`REQ-002`; `.pre-commit-config.yaml`, `.github/workflows/ci.yml`, `tools/run_validation_gates.py`, `tests/tools/test_run_validation_gates.py`)
   - [ ] Update the gate scope text (`REQ-004`; `routing.md`, `rules/toolchain.md`, `tools/TOOL_DESCRIPTIONS.md`)
2. **Phase 2: Split `manage_workitem_stage.py`**
   - [ ] Measure clusters, move the status-table logic and the parser with `module_nodes.py extract`, prove the move with `compare`, keep re-exports, run `tests/tools` and each subcommand on live data, then lower the baseline entry (`REQ-005`, `REQ-007`; `tools/manage_workitem_stage.py`, `tools/_workitem_status_table.py`, `tools/_workitem_stage_parser.py`, `tools/check_module_size_tools_baseline.txt`, `tools/TOOL_DESCRIPTIONS.md`)
3. **Phase 3: Split `run_validation_gates.py`**
   - [ ] Move `Gate` and the gate tables into `tools/_validation_gate_defs.py`, keep re-exports, run `tests/tools/test_run_validation_gates.py`, `drift`, and the gates, then lower the baseline entry (`REQ-006`, `REQ-007`; `tools/run_validation_gates.py`, `tools/_validation_gate_defs.py`, `tools/check_module_size_tools_baseline.txt`, `tools/TOOL_DESCRIPTIONS.md`)
4. **Phase 4: Verification**
   - [ ] Run the per-file checks of `routing.md` "Adding a new tool" on every changed Python file, `check_tool_descriptions_sync.py`, `check_skills_references.py`, the module-size gate for both directories, and the validation gates. No deploy step: only `tools/`, `tests/`, CI, and documentation change.

### Release units
N/A: no release unit

## Validation plan
| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| `tests/tools/test_check_module_size.py` | Unit (second invocation) | `uv run pytest tests/tools/test_check_module_size.py -q` | All pass |
| `tools/check_module_size_tools_baseline.txt` | Integration | `uv run python tools/check_module_size.py --scripts-dir tools --baseline tools/check_module_size_tools_baseline.txt` | Exit 0; no regression, shrinkage reported after a split |
| pre-commit, CI, gates | Integration | `uv run python tools/run_validation_gates.py drift`; `uv run pre-commit run check-module-size-tools --all-files` | Parity OK; hook passes |
| split tools | Regression per phase | `uv run pytest tests/tools -q` | No new failure |
| moved code | Move proof | `uv run python tools/module_nodes.py compare ...` for each moved function | Identical |
| changed Python files | Lint, type, security (paths explicit) | `uv run ruff format`, `uv run ruff check`, `uv run mypy --no-namespace-packages <files>`, `uv run bandit <files>` | Clean |
| docs rows | Sync and reference checks | `uv run python tools/check_tool_descriptions_sync.py`; `uv run python tools/check_skills_references.py` | Pass |

## Risks
- **Risk**: A split changes CLI behavior or breaks a caller's import → **Mitigation**: the original module keeps the entry point and re-exports; `compare`, the existing tests, and live-data runs of each subcommand.
- **Risk**: The pre-commit and CI gates turn red when the baseline is incomplete → **Mitigation**: create the baseline from the current sizes first and run both invocations before wiring them.
- **Risk**: The Plans that edit the same tools conflict with the splits → **Mitigation**: this Plan is sequenced last with explicit phase dependencies; re-run `check_plan_target_overlaps.py` at procedure generation.
- **Risk**: A split introduces a circular import → **Mitigation**: handlers are passed to the parser module as arguments; the dependency direction is one-way.
- **Risk**: `--update-baseline` run later grandfathers a new violation → **Mitigation**: change the baseline only by lowering entries after each split and review the diff (`REQ-007`).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Add the gate for `tools/` with a full baseline, wiring, and scope text | Pending | — | — | |
| 2 | Split `manage_workitem_stage.py` and lower its baseline | Pending | — | — | |
| 3 | Split `run_validation_gates.py` and lower its baseline | Pending | — | — | |
| 4 | Verify the checks and gates | Pending | — | — | |

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
- **Source issue**: issues/20261104-152002_toolsizegate001_apply-size-gate-to-tools.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: this document is the generated plan
- **Source implementation procedure**: N/A: not applicable in this phase
- **Generated at**: 20261105-110406
- **Related target files**: tools/check_module_size_tools_baseline.txt, tests/tools/test_check_module_size.py, .pre-commit-config.yaml, .github/workflows/ci.yml, tools/run_validation_gates.py, tests/tools/test_run_validation_gates.py, tools/_validation_gate_defs.py, tools/manage_workitem_stage.py, tools/_workitem_status_table.py, tools/_workitem_stage_parser.py, routing.md, rules/toolchain.md, tools/TOOL_DESCRIPTIONS.md

### Requirement Traceability
| Requirement ID | Source Issue section or evidence | Target file | Implementation step | Acceptance criterion | Test or validation item | Status |
|---|---|---|---|---|---|---|
| REQ-001 | Required Changes 1; Background (15 oversized files, corrected in Step 2) | `tools/check_module_size_tools_baseline.txt` | 1 | AC-1 | Baseline run | Confirmed by repository evidence |
| REQ-002 | Required Changes 2 | `.pre-commit-config.yaml` | 1 | AC-3 | `drift`; hook run | Explicit in issue |
| REQ-002 | Required Changes 2 | `.github/workflows/ci.yml` | 1 | AC-3 | Run of the CI command | Explicit in issue |
| REQ-002 | Required Changes 2; gate mapping (Step 3) | `tools/run_validation_gates.py` | 1 | AC-3 | `test_run_validation_gates.py`; `drift` | Derived from confirmed evidence |
| REQ-002 | Same | `tests/tools/test_run_validation_gates.py` | 1 | AC-3 | Gate-mapping assertion | Derived from confirmed evidence |
| REQ-003 | Testing Expectations (multi-directory gate) | `tests/tools/test_check_module_size.py` | 1 | AC-2 | Second-invocation tests | Explicit in issue |
| REQ-004 | Required Changes 2; Documentation Impact | `routing.md` | 1 | AC-5 | `check_skills_references.py` | Explicit in issue |
| REQ-004 | Same | `rules/toolchain.md` | 1 | AC-5 | `check_skills_references.py` | Explicit in issue |
| REQ-004 | Same | `tools/TOOL_DESCRIPTIONS.md` | 1, 2, 3 | AC-5 | `check_tool_descriptions_sync.py` | Explicit in issue |
| REQ-005 | Required Changes 3; Background (`measure`, Step 3) | `tools/manage_workitem_stage.py` | 2 | AC-4 | Existing tests; `compare`; live-data run | Confirmed by repository evidence |
| REQ-005 | Same | `tools/_workitem_status_table.py` | 2 | AC-4 | Existing tests; `compare` | Derived from confirmed evidence |
| REQ-005 | Same | `tools/_workitem_stage_parser.py` | 2 | AC-4 | Existing tests; `compare` | Derived from confirmed evidence |
| REQ-006 | Required Changes 3; Background (gate tables, Step 3) | `tools/_validation_gate_defs.py` | 3 | AC-6 | `test_run_validation_gates.py`; `drift` | Derived from confirmed evidence |
| REQ-006 | Same | `tools/run_validation_gates.py` | 3 | AC-6 | `test_run_validation_gates.py`; `drift` | Confirmed by repository evidence |
| REQ-007 | Constraints (baseline only shrinks); Acceptance Criteria 3 | `tools/check_module_size_tools_baseline.txt` | 2, 3 | AC-4, AC-6 | Baseline run after each split | Explicit in issue |
