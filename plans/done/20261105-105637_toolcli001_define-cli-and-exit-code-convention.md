## Goal
- `tools/TOOL_DESCRIPTIONS.md` states one CLI and exit-code convention (`0` pass, `1` findings, `2` usage or environment error), every executable tool is either compliant or listed with a reason, all executable tools answer `--help`, and `generate_reference_table.py` exposes `main()`, with no change to what any tool checks or when it fails.

## Priority
Low

## Scope
- **In-Scope**: audit the exit codes of every tool and record deviations; document the convention and the option names that already exist (`--check`, `--json`, `--format`, `--dry-run`); give `check_docs_japanese.py`, `check_dependency_graph_cycles.py`, `check_needs_confirmation_inventory.py`, `check_tool_descriptions_sync.py`, and `audit_plan_target_paths.py` an `argparse` entry; wrap the module-level `__main__` block of `generate_reference_table.py` in `main()`.
- **Out-of-Scope**: splitting tools or changing tool logic; renaming or unifying options (`--json` versus `--format json`, owned by the `toolreport001` Plan); the shared exit-code constants (owned by the `toolcommon001` Plan, which consumes this convention); the four private library modules, which have no entry point.
- **Dependencies**: the convention is decided here before the `toolcommon001` Plan defines shared constants (that Plan records `Depends on` this one). `plans/20261105-105344_toolstest001_add-tests-for-untested-tools.md` adds the first tests of `audit_plan_target_paths.py`, so it lands before this Plan changes that tool's entry.
  - **Depends on**: plans/20261105-105344_toolstest001_add-tests-for-untested-tools.md | phase all | `audit_plan_target_paths.py` gets its own tests before its `main` is changed
  - **Depends on**: plans/20261105-105554_toolsdocsync001_check-index-count-in-tool-descriptions.md | phase all | both Plans edit `tools/TOOL_DESCRIPTIONS.md`; the one-line heading edit lands first

## Background
Verified on 2026-11-05 (checked in Steps 2 and 3): exit codes in `tools/*.py` are `0` and `1` with `2` returned explicitly in 11 places (`check_ci_results.py` for `gh` read failures, `classify_changes.py`, `mark_procedure_new_symbols.py`, `manage_workitem_stage.py`); argparse-based tools already exit `2` on a usage error. Five tools have no `argparse` (`check_docs_japanese.py`, `check_dependency_graph_cycles.py`, `check_needs_confirmation_inventory.py`, `check_tool_descriptions_sync.py`, `audit_plan_target_paths.py`). Four private library modules (`_adr_authority_core.py`, `_front_matter_schema.py`, `_docs_consistency_lib.py`, `_contract_manifests.py`) also lack `argparse` but have no entry point. `generate_reference_table.py` has no `main`; its entry is the module-level `if __name__ == "__main__":` block that builds its parser inline. `run_validation_gates.py` `classify` maps exit `0` to `Pass` and any other code to `Fail`, so no gate distinguishes `1` from `2`. `pyproject.toml` console scripts call `tools.check_docs_consistency:main_mcp`, `:main_agent`, `tools.check_needs_confirmation_inventory:main`, and `tools.check_tool_descriptions_sync:main` with no arguments.

## Problem
Callers (hooks, CI, `run_validation_gates.py`, skills) cannot rely on a stated meaning of each exit code, and several tools cannot be discovered or called programmatically like the rest.

## Reason for Change
Consistency and developer usability; no failure is known and the work is not time-sensitive.

## Implementation Intent
Audit first and report deviations before changing any tool. Write the contract once in `tools/TOOL_DESCRIPTIONS.md`, fix only audited deviations whose callers were reviewed, and give the five tools a `main(argv: list[str] | None = None) -> int` with a small `_parse_args` helper so existing `main()` calls and console scripts keep working. Keep behavior and exit codes identical.

## Requirements
- `REQ-001`: Every `tools/*.py` module MUST be audited for its exit codes, and each deviation from the convention MUST be recorded with a reason and the callers reviewed (pre-commit, CI, `run_validation_gates.py`, skills).
- `REQ-002`: `tools/TOOL_DESCRIPTIONS.md` MUST document the convention (`0` pass, `1` findings, `2` usage or environment error), the existing common option names only where they already exist, and a deviation list; every executable tool is compliant or listed with a reason.
- `REQ-003`: `check_docs_japanese.py`, `check_dependency_graph_cycles.py`, `check_needs_confirmation_inventory.py`, `check_tool_descriptions_sync.py`, and `audit_plan_target_paths.py` MUST accept `--help` through `argparse`, keep `main()` callable without arguments and without reading the caller's `sys.argv` (except `audit_plan_target_paths.py`, which reads it today; see Design), and keep their current behavior and exit codes.
- `REQ-004`: `generate_reference_table.py` MUST expose `main(argv=None) -> int` containing its current argument handling, with the `__main__` block reduced to `sys.exit(main())`, and unchanged behavior. The three `raise SystemExit(...)` exits inside the `--check` and `--manifests` branches (`:1008`, `:1010`, `:1040`) become `return` values, and `parser.error` keeps exiting `2`.
- `REQ-005`: Tests MUST call `--help` and the main exit paths of the six changed tools, and no existing hook or CI step may change behavior (`uv run pytest tests/tools -q` and the validation gates pass).
- `REQ-006`: An exit-code change MUST NOT be made unless every caller was reviewed first; an unreviewed deviation is only recorded.

## Implementation Target Files
**Freeze status**: Frozen

| File Path | Change Responsibility | Reason for Modification | Related Requirement / Acceptance Criterion | Repository Evidence | Related Tests | Validation Status |
|---|---|---|---|---|---|---|
| `tools/TOOL_DESCRIPTIONS.md` | Convention and deviation list | Add the CLI and exit-code convention section and the deviation list | `REQ-001`, `REQ-002`, `REQ-006`; AC-1, AC-2 | 11 explicit `return 2` sites and mixed `0`/`1`/`2` use found by `rg` (checked in Step 3); no convention text exists (`rg` for exit-code wording matched per-tool rows only) | `uv run python tools/check_tool_descriptions_sync.py` | Verified |
| `tools/check_docs_japanese.py` | Add `argparse` entry | `main()` has no `argparse`; add `main(argv)` and `_parse_args` | `REQ-003`, `REQ-005`; AC-3, AC-5 | `def main() -> int` at module level, no `argparse` import (checked in Step 3) | `tests/tools/test_check_docs_japanese.py` | Verified |
| `tools/check_dependency_graph_cycles.py` | Add `argparse` entry | `main()` has no `argparse`; `radon` grades it C (16), so parsing moves to a helper | `REQ-003`, `REQ-005`; AC-3, AC-5 | `def main() -> int`, no `argparse` import (checked in Step 3) | `tests/tools/test_check_dependency_graph_cycles.py` | Verified |
| `tools/check_needs_confirmation_inventory.py` | Add `argparse` entry | `main()` has no `argparse`; console script `check-needs-confirmation` calls `main` with no arguments | `REQ-003`, `REQ-005`; AC-3, AC-5 | `def main() -> int`; `pyproject.toml` console script entry (checked in Step 3) | `tests/tools/test_check_needs_confirmation_inventory.py` | Verified |
| `tools/check_tool_descriptions_sync.py` | Add `argparse` entry | `main()` has no `argparse`; console script `check-tool-descriptions` calls `main` with no arguments | `REQ-003`, `REQ-005`; AC-3, AC-5 | `def main() -> int`; `pyproject.toml` console script entry (checked in Step 2) | `tests/tools/test_check_tool_descriptions_sync.py` | Verified |
| `tools/audit_plan_target_paths.py` | Add `argparse` entry | `main()` reads `sys.argv[1:]` directly; add positional `plans` (`nargs="*"`) | `REQ-003`, `REQ-005`; AC-3, AC-5 | `main` uses `sys.argv[1:]`; `amend_plan.py` runs the tool by path with one plan argument (checked in Step 3) | `tests/tools/test_audit_plan_target_paths.py` (added by the `toolstest001` Plan, already in the repository) and `tests/tools/test_amend_plan.py` | Verified |
| `tools/generate_reference_table.py` | Add `main()` | Move the inline parser and dispatch from the `__main__` block into `main(argv=None) -> int` | `REQ-004`, `REQ-005`; AC-4, AC-5 | 1060 lines, no `def main`, entry at the `if __name__ == "__main__":` block (checked in Step 2) | `tests/tools/test_generate_reference_table.py` | Verified |
| `tests/tools/test_tool_cli_convention.py` | `--help` and exit-path tests for the six tools | New file; `tests/tools/` exists | `REQ-005`; AC-3, AC-4, AC-5 | One parametrized file avoids editing five existing test files and the not-yet-existing audit test file (judgment, Step 5) | itself | Verified |

## Reference Files
| File Path | Why It Must Be Read | Related Target File or Requirement |
|---|---|---|
| `tools/run_validation_gates.py` | `classify` treats every non-zero code as `Fail`; callers of tools by gate | `REQ-001`, `REQ-006` |
| `tools/check_ci_results.py` | Source of six `return 2` environment-error exits that define the convention's `2` | `REQ-001`, `REQ-002` |
| `.pre-commit-config.yaml` | Pre-commit hooks that call the changed tools (`python -m tools.<name>`) | `REQ-006` |
| `.github/workflows/ci.yml` | CI steps that call tools by path | `REQ-006` |
| `tools/amend_plan.py` | Caller of `audit_plan_target_paths.py` and `check_plan_target_overlaps.py` by path | `REQ-003`, `REQ-006` |
| `pyproject.toml` | Console scripts that call `main` with no arguments | `REQ-003` |

## Acceptance Criteria
- AC-1: The audit result lists every non-compliant tool with a reason and the callers reviewed (`REQ-001`, `REQ-006`).
- AC-2: `tools/TOOL_DESCRIPTIONS.md` documents the convention and every executable tool is compliant or listed (`REQ-002`).
- AC-3: Each of the five tools answers `--help` with exit `0`, and `main()` still works without arguments (`REQ-003`).
- AC-4: `generate_reference_table.py` exposes `main()`, `uv run python tools/generate_reference_table.py --check` behaves as before, and `--help` exits `0` (`REQ-004`).
- AC-5: Existing hooks and CI steps behave unchanged: `uv run pytest tests/tools -q` and `uv run python tools/run_validation_gates.py` pass (`REQ-005`).

## Tests
- New parametrized tests in `tests/tools/test_tool_cli_convention.py`: `--help` raises `SystemExit(0)` and prints usage for each of the six tools; an unknown flag raises `SystemExit(2)` for the five argparse-converted tools (argparse exits, it does not return); each tool's current main exit path (pass and finding) is covered by the existing test files (`REQ-003`, `REQ-004`, `REQ-005`).
- Regression: the existing per-tool tests (listed in the target rows) and `tests/tools/test_amend_plan.py` (`REQ-005`).
- Behavior check: run each changed tool before and after against live repository data and compare exit codes and output (`REQ-003`, `REQ-004`).

## Documentation Impact
Yes: `tools/TOOL_DESCRIPTIONS.md` is the documentation deliverable (`REQ-002`); the convention is named there only, not copied into `docs/*.md`. No `docs/*.md` change is required.

## Assumptions
- Existing argparse-based tools already satisfy "`2` = usage error" through argparse's default, so the audit concentrates on tools returning `1` for environment errors (judgment from `argparse` behavior and the 11 explicit `return 2` sites).
- Because `run_validation_gates.py` `classify` maps any non-zero code to `Fail`, the audit's recorded deviations do not change gate results unless a hook or workflow script matches a specific code (to be confirmed per caller in Phase 1).
- Overlap judgment (`check_plan_target_overlaps.py`, Step 8b): `tools/TOOL_DESCRIPTIONS.md` is also a target of the `toolsdocsync001` Plan. The designs are compatible (that Plan changes only the Index heading; this Plan adds a new convention section), with a sequencing dependency recorded in Scope: `toolsdocsync001` first.
- Caller review done in Step 3a (2026-11-05): every caller of the five tools passes no argument: the `docs-japanese` and `tool-descriptions-sync` pre-commit hooks use `python -m tools.<name>` with `pass_filenames: false`; the CI and `governance-docs-consistency.yml` steps and the `run_validation_gates.py` gates run the tools by path with no argument; `amend_plan.py` passes one plan path to `audit_plan_target_paths.py`; the `generate_reference_table.py` callers (CI, hook, gates) use only `--check`, `--manifests`, `--type`, and `--dry-run`. Adding an `argparse` parser with no positional argument therefore rejects no existing call.
- Ordering with the `toolsdocsync001` Plan: its procedure (the Index heading edit of `tools/TOOL_DESCRIPTIONS.md`) is generated but not yet executed, so `code-implementation` runs it before this Plan's `tools/TOOL_DESCRIPTIONS.md` procedure (the `Depends on` line in Scope).
- A single new test file is sufficient for the `--help` checks; the per-tool exit-path tests already exist (judgment, to avoid editing five test files).

## Unknowns
| ID | Unknown Description | Evidence Missing | Resolution Path | Blocking? (True/False) |
|---|---|---|---|---|
| UNK-01 | Whether any caller depends on a non-standard exit code | The audit has not been run over all tools and callers | Phase 1 reads every caller in pre-commit, CI, `run_validation_gates.py`, and `skills/` before any exit-code change; a deviation stays documented if a caller is unclear | False |
| UNK-02 | Which tools besides the six deviate and would need a code change | Audit not yet performed | Phase 1 lists them; a fix to a tool outside the target table is added only through `tools/amend_plan.py` after owner approval (scope change class) | False |

## Affected areas
| File | Change | Blast Radius | Churn (30d) | Bus Factor | deploy.sh Impact |
|---|---|---|---|---|---|
| `tools/TOOL_DESCRIPTIONS.md` | Modify | Low (documentation checked by `check_tool_descriptions_sync.py`) | 82 | High (one author across the repository history) | not applicable (rsynced) |
| `tools/check_docs_japanese.py` | Modify | Medium (runs as the `docs-japanese` pre-commit hook) | N/A (outside top 60) | High | not applicable (rsynced) |
| `tools/check_dependency_graph_cycles.py` | Modify | Medium (CI and hook use) | N/A | High | not applicable (rsynced) |
| `tools/check_needs_confirmation_inventory.py` | Modify | Medium (console script and hook) | N/A | High | not applicable (rsynced) |
| `tools/check_tool_descriptions_sync.py` | Modify | Medium (console script, CI, routing gate) | N/A | High | not applicable (rsynced) |
| `tools/audit_plan_target_paths.py` | Modify | Low (called by `amend_plan.py`) | N/A | High | not applicable (rsynced) |
| `tools/generate_reference_table.py` | Modify | Medium (CI `--check` and generator for reference tables) | 6 | High | not applicable (rsynced) |
| `tests/tools/test_tool_cli_convention.py` | Create | Low | N/A | High | not applicable (rsynced) |

## Design
- Path B (more than 3 files). Architecture analysis: `tools/` is outside the `.importlinter` contracts, so no layer rule applies. Dependency graphing: callers of the changed tools are pre-commit hooks (`python -m tools.<name>`), CI steps (by path), `amend_plan.py` (by path), and `pyproject.toml` console scripts; the 11 explicit `return 2` sites belong to four tools outside the target table and are not changed. Historical analysis: churn is in the Affected areas table, and all history is by one author. Operational dependency inspection: not applicable (no MCP server, database, or dependency change).
- Validation quality baseline: `radon cc` grades `check_dependency_graph_cycles.main` C (16), `generate_reference_table.py` `_config_ownership_entries` C (17) and `_health_contract_entries` C (14) (not touched), and `check_needs_confirmation_inventory.py` `_parse_inventory_entries` C (14) (not touched); other grade C functions in the target files that stay unchanged: `audit_plan_target_paths.py` `audit` C (19), `check_needs_confirmation_inventory.py` `check_untracked_inline_markers` C (11), `generate_reference_table.py` `_invariant_coverage_entries` C (12) (verified 2026-11-05); the change MUST NOT worsen `main` grades, so argument parsing goes into `_parse_args` helpers. `vulture` and `bandit` baselines on `scripts/` are unrelated and unchanged. diff-cover baseline: `N/A: no diff exists before implementation`; at least 90 percent on changed lines is required (`rules/toolchain.md`).
- Pattern: `def _parse_args(argv: list[str]) -> argparse.Namespace` (description from the module docstring) and `def main(argv: list[str] | None = None) -> int`. In-process callers (the existing tests `cdgc.main()` in `test_check_dependency_graph_cycles.py` and `mod.main()` in `test_check_needs_confirmation_inventory.py`, and the `pyproject.toml` console scripts) call `main()` with no argument while `sys.argv` holds pytest's or the launcher's arguments. Verified 2026-11-05 (checked in Step 3a): `argparse.ArgumentParser().parse_args()` inside a pytest run exits 2 with `unrecognized arguments`. So for the four tools that take no arguments today, `main(None)` parses `[]` (identical to current behavior) and the `__main__` block passes `sys.argv[1:]`, which is what makes `--help` and unknown-flag handling reachable from the command line. `audit_plan_target_paths.py` reads `sys.argv[1:]` today, so its `main(None)` keeps that fallback (the `toolstest001` tests patch `sys.argv`). `generate_reference_table.py` has no in-process caller, so its `main(None)` uses `sys.argv[1:]`.
- `generate_reference_table.py` is over the 24576 B limit (42,997 B) but the gate covers `scripts/` only; extracting `main` keeps the byte size roughly unchanged. Splitting stays with the `toolsizegate001` Plan.
- Consumer scan: not applicable for a persisted schema or public API; the callers were enumerated by the `rg` searches above.

## Implementation steps
1. **Phase 1: Audit**
   - [ ] Audit every tool's exit codes and callers and record deviations with reasons (`REQ-001`, `REQ-006`; `tools/TOOL_DESCRIPTIONS.md`)
2. **Phase 2: Document the convention**
   - [ ] Add the convention, the existing option names, and the deviation list; run the sync checker (`REQ-002`; `tools/TOOL_DESCRIPTIONS.md`)
3. **Phase 3: Add `argparse` to the five tools**
   - [ ] Add `_parse_args` and `main(argv)` to the five tools without changing behavior or exit codes (`REQ-003`, `REQ-005`; `tools/check_docs_japanese.py`, `tools/check_dependency_graph_cycles.py`, `tools/check_needs_confirmation_inventory.py`, `tools/check_tool_descriptions_sync.py`, `tools/audit_plan_target_paths.py`)
4. **Phase 4: `generate_reference_table.py` `main()`**
   - [ ] Move the `__main__` block body into `main(argv=None) -> int` (`REQ-004`, `REQ-005`; `tools/generate_reference_table.py`)
5. **Phase 5: `--help` and unknown-flag tests**
   - [ ] Add the parametrized tests. They land after the tools: the procedure cycles follow the target table order and a cycle cannot end with a failing test, so the earlier plan to add them failing first is replaced by a mutation check (make one tool's `_parse_args` ignore its argument, confirm a test fails, revert) (`REQ-005`; `tests/tools/test_tool_cli_convention.py`)
6. **Phase 6: Verification**
   - [ ] Run the per-file checks of `routing.md` "Adding a new tool" for each changed tool, the full `tests/tools` suite, the validation gates, and a before-and-after run on live data (`REQ-003`, `REQ-004`, `REQ-005`; all rows). No deploy step: only `tools/` and `tests/` change.

### Release units
N/A: no release unit

## Validation plan
| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| five tools and `generate_reference_table.py` | Unit (`--help`, unknown flag) | `uv run pytest tests/tools/test_tool_cli_convention.py -q` | All pass |
| each changed tool | Regression | `uv run pytest tests/tools -q` | No new failure |
| each changed tool | Lint, type, security (path passed explicitly) | `uv run ruff format`, `uv run ruff check`, `uv run mypy <file>`, `uv run bandit <file>` | Clean |
| `tools/TOOL_DESCRIPTIONS.md` | Sync check | `uv run python tools/check_tool_descriptions_sync.py` | `No issues found.` |
| `generate_reference_table.py` | Generated-reference check | `uv run python tools/generate_reference_table.py --check` | Exit 0, as before |
| whole diff | Gates | `uv run python tools/run_validation_gates.py` | Pass |

## Risks
- **Risk**: A hook or CI step matches a specific exit code that the audit changes → **Mitigation**: no exit-code change without reviewing every caller (`REQ-006`); `run_validation_gates.py` `classify` treats all non-zero codes alike.
- **Risk**: Adding `argparse` rejects an argument a caller already passes (for example an unlisted flag) → **Mitigation**: grep each caller invocation in pre-commit, CI, and skills before Phase 3 and keep unknown-flag handling only where no caller passes extras; add a test for every caller form.
- **Risk**: `check_dependency_graph_cycles.main` complexity (grade C) grows → **Mitigation**: parsing lives in `_parse_args`; re-run `radon cc` on the file.
- **Risk**: Concurrent edits of the high-churn `tools/TOOL_DESCRIPTIONS.md` conflict → **Mitigation**: apply after the `toolsdocsync001` one-line edit and edit only the new section.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Audit exit codes and callers; record deviations | In Progress | — | — |  |
| 2 | Document the convention and deviations | In Progress | — | — |  |
| 3 | Add `argparse` to the five tools | In Progress | — | — |  |
| 4 | Add `main()` to `generate_reference_table.py` | In Progress | — | — |  |
| 5 | Add the `--help` and unknown-flag tests | In Progress | — | — |  |
| 6 | Verify tests, checks, gates, and live-data behavior | Pending | — | — |  |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| — | — | — | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| implementations/20261105-162554_01_tools_TOOL_DESCRIPTIONS.md.md | 1, 2 | Procedure | Pending | — | — |
| implementations/20261105-162554_02_tools_check_docs_japanese.py.md | 3 | Procedure | Pending | — | — |
| implementations/20261105-162554_03_tools_check_dependency_graph_cycles.py.md | 3 | Procedure | Pending | — | — |
| implementations/20261105-162554_04_tools_check_needs_confirmation_inventory.py.md | 3 | Procedure | Pending | — | — |
| implementations/20261105-162554_05_tools_check_tool_descriptions_sync.py.md | 3 | Procedure | Pending | — | — |
| implementations/20261105-162554_06_tools_audit_plan_target_paths.py.md | 3 | Procedure | Pending | — | — |
| implementations/20261105-162554_07_tools_generate_reference_table.py.md | 4 | Procedure | Pending | — | — |
| implementations/20261105-162554_08_tests_tools_test_tool_cli_convention.py.md | 5 | Procedure | Pending | — | — |

## Traceability
- **Workflow phase**: issue-to-plan
- **Source issue**: issues/20261104-152002_toolcli001_define-cli-and-exit-code-convention.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: this document is the generated plan
- **Source implementation procedure**: N/A: not applicable in this phase
- **Generated at**: 20261105-105637
- **Related target files**: tools/TOOL_DESCRIPTIONS.md, tools/check_docs_japanese.py, tools/check_dependency_graph_cycles.py, tools/check_needs_confirmation_inventory.py, tools/check_tool_descriptions_sync.py, tools/audit_plan_target_paths.py, tools/generate_reference_table.py, tests/tools/test_tool_cli_convention.py

### Requirement Traceability
| Requirement ID | Source Issue section or evidence | Target file | Implementation step | Acceptance criterion | Test or validation item | Status |
|---|---|---|---|---|---|---|
| REQ-001 | Required Changes 1; Unresolved Questions | `tools/TOOL_DESCRIPTIONS.md` | 1 | AC-1 | Audit record in the deviation list | Explicit in issue |
| REQ-002 | Required Changes 2; Acceptance Criteria 1 | `tools/TOOL_DESCRIPTIONS.md` | 2 | AC-2 | Sync checker run | Explicit in issue |
| REQ-003 | Required Changes 3; Background (five tools, verified in Step 3) | `tools/check_docs_japanese.py` | 3 | AC-3 | `test_tool_cli_convention.py`; `test_check_docs_japanese.py` | Confirmed by repository evidence |
| REQ-003 | Required Changes 3 | `tools/check_dependency_graph_cycles.py` | 3 | AC-3 | `test_tool_cli_convention.py`; `test_check_dependency_graph_cycles.py` | Confirmed by repository evidence |
| REQ-003 | Required Changes 3 | `tools/check_needs_confirmation_inventory.py` | 3 | AC-3 | `test_tool_cli_convention.py`; `test_check_needs_confirmation_inventory.py` | Confirmed by repository evidence |
| REQ-003 | Required Changes 3 | `tools/check_tool_descriptions_sync.py` | 3 | AC-3 | `test_tool_cli_convention.py`; `test_check_tool_descriptions_sync.py` | Confirmed by repository evidence |
| REQ-003 | Required Changes 3 | `tools/audit_plan_target_paths.py` | 3 | AC-3 | `test_tool_cli_convention.py`; `test_amend_plan.py` | Confirmed by repository evidence |
| REQ-004 | Required Changes 3; Background (`generate_reference_table.py` has no `main`) | `tools/generate_reference_table.py` | 4 | AC-4 | `test_generate_reference_table.py`; `--check` run | Confirmed by repository evidence |
| REQ-005 | Testing Expectations; Acceptance Criteria 3 | `tests/tools/test_tool_cli_convention.py` | 5, 6 | AC-3, AC-4, AC-5 | `uv run pytest tests/tools -q`; validation gates | Explicit in issue |
| REQ-006 | Constraints (exit-code changes reviewed against callers) | `tools/TOOL_DESCRIPTIONS.md` | 1, 2 | AC-1 | Caller review recorded in the deviation list | Explicit in issue |

<!-- tools/generate_workitem.py implementation-procedure-pass timestamp: 20261105-162554 -->