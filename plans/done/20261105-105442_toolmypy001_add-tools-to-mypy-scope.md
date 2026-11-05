## Goal
- `uv run mypy --no-namespace-packages scripts/ tests/eventbus tools` reports no errors, and every place that runs or documents the project's mypy scope (pyproject, CI, tox, the pre-commit hook, the validation-gate table, and the rules and skills text) states the same scope including `tools/`.

## Priority
Medium

## Scope
- **In-Scope**: fix the two `attr-defined` errors in `tools/check_canonical_source_registry.py` with real typing; add `tools` to the mypy scope in `pyproject.toml`, `.github/workflows/ci.yml`, `tox.ini`, and the `TOOLCHAIN_GATES` mypy gate of `tools/run_validation_gates.py`; update the documented command and scope text in `rules/toolchain.md`, `rules/coding.md`, `skills/python-lint-typecheck/workflow.md`, and `routing.md`.
- **Out-of-Scope**: stricter mypy options (for example `--check-untyped-defs`, which would also address the two `annotation-unchecked` notes in `tools/manage_workitem_stage.py`); typing `tests/` beyond `tests/eventbus`; the pyright invocation.
- **Dependencies**: this Plan lands before the Plans for `toolcommon001`, `toolreport001`, `toolwrite001`, and `toolsizegate001`, so their refactors and moved code are type-checked (the original Issue text had this inverted; corrected in Step 2). Each of those Plans records the order in its own `Depends on` line (verified 2026-11-05, checked in Step 3a); this Plan depends on none of them.

## Background
`[tool.mypy] files` is `["scripts/", "tests/eventbus"]`, and CI, tox, the validation gate table, and the rules state the same two paths; `tools/` is not type-checked anywhere. A read-only run on 2026-11-05 of `uv run mypy --no-namespace-packages scripts/ tests/eventbus tools` checked 557 source files, reported no "Source file found twice" failure, and reported exactly two errors, both in `tools/check_canonical_source_registry.py`, plus two `annotation-unchecked` notes in `tools/manage_workitem_stage.py` that are notes, not errors (checked in Step 2).

## Problem
`tools/` holds the CI and workflow tooling that gates commits, yet type regressions in it are never caught. The two existing errors come from `validate_all` building `result` as an untyped dict literal, which mypy infers as `dict[str, object]`, so `result["errors"].extend(...)` fails.

## Reason for Change
Maintenance risk only; no incident is known. The gap is cheap to close today because one file needs a fix.

## Implementation Intent
Fix the inference at its source by annotating the `result` dict, then widen the scope in the one configuration file (`pyproject.toml`) and align every explicit command and every statement of the scope in the same change set, so the gate never turns red.

## Requirements
- `REQ-001`: The two `attr-defined` errors at `CanonicalSourceRegistry.validate_all` MUST be fixed by typing `result` (for example `dict[str, Any]`), with no `# type: ignore`.
- `REQ-002`: `pyproject.toml` `[tool.mypy] files` MUST include `tools`, and the CI mypy step, the `tox.ini` `typecheck` command, and the `mypy` gate command in `tools/run_validation_gates.py` MUST name the same scope.
- `REQ-003`: `rules/toolchain.md`, `rules/coding.md`, `skills/python-lint-typecheck/workflow.md`, and `routing.md` MUST state the same scope, and `routing.md` "Adding a new tool" step 2 MUST no longer say that a bare `uv run mypy` skips `tools/`.
- `REQ-004`: The change MUST confirm `--no-namespace-packages` still avoids "Source file found twice" with `tools` included, MUST keep `warn_unused_ignores` behavior, and MUST record the measured extra run time.
- `REQ-005`: No suppression is added without a justification (`tools/check_suppression_justification.py`), and `tools/` behavior is unchanged (`uv run pytest tests/tools -q` passes).

## Implementation Target Files
**Freeze status**: Frozen
Amended 2026-11-05 (fallout): added skills/code-implementation/workflow.md — Step 7 note says a bare 'uv run mypy' does not cover tools/; after the scope change it does, so the sentence must change
Amended 2026-11-05 (fallout): added skills/python-implementation/workflow.md — The mypy command comment says mypy's configured scope omits tools/; after the scope change it includes tools/
Amended 2026-11-05 (fallout): added skills/python-code-review/workflow.md — Two sentences say a bare 'uv run mypy' / mypy's files scope omits tools/; after the scope change they are false

| File Path | Change Responsibility | Reason for Modification | Related Requirement / Acceptance Criterion | Repository Evidence | Related Tests | Validation Status |
|---|---|---|---|---|---|---|
| `tools/check_canonical_source_registry.py` | Fix the typing source | Annotate `result` in `CanonicalSourceRegistry.validate_all` as `dict[str, Any]` | `REQ-001`, `REQ-005`; AC-1 | `uv run mypy --no-namespace-packages tools` reports `:851` and `:854` `attr-defined`; `result = {...}` unannotated in `validate_all` (checked in Step 2 and Step 3) | `tests/tools/test_check_canonical_source_registry.py` | Verified |
| `pyproject.toml` | Widen the mypy scope in one place | Add `"tools"` to `[tool.mypy] files`; the pre-commit hook follows it | `REQ-002`; AC-2, AC-4 | `files = ["scripts/", "tests/eventbus"]` under `[tool.mypy]`; hook has `pass_filenames: false` (checked in Step 2) | N/A: configuration; verified by the mypy command | Verified |
| `.github/workflows/ci.yml` | Align the CI command | Add `tools` to the `uv run mypy --no-namespace-packages scripts/ tests/eventbus` step | `REQ-002`; AC-2 | The mypy step command in the workflow (checked in Step 2) | N/A: verified by running the command | Verified |
| `tox.ini` | Align the `typecheck` command | Add `tools` to the `typecheck` mypy command | `REQ-002`; AC-2 | `typecheck: uv run mypy --no-namespace-packages scripts/ tests/eventbus` (checked in Step 3; not listed in the Issue) | N/A: verified by running the command | Verified |
| `tools/run_validation_gates.py` | Align the gate table | Add `"tools"` to the `mypy` gate command tuple in `TOOLCHAIN_GATES` | `REQ-002`; AC-2 | The gate tuple lists `scripts/` and `tests/eventbus` (checked in Step 3) | `tests/tools/test_run_validation_gates.py` | Verified |
| `rules/toolchain.md` | Update the documented command and text | Update section 2 command, the `--no-namespace-packages` explanation, and the Completion checklist item | `REQ-003`, `REQ-004`; AC-3 | Command stated in section 2 and the Completion checklist (checked in Step 2) | N/A: documentation; `check_skills_references.py` | Verified |
| `rules/coding.md` | Update the stated scope | Update the Tool configuration `files` value and the "mypy note" scope sentence | `REQ-003`; AC-3 | States `files = ["scripts/", "tests/eventbus"]` and the CI scope (checked in Step 3; not listed in the Issue) | N/A: documentation; `check_skills_references.py` | Verified |
| `skills/python-lint-typecheck/workflow.md` | Update the stated scope and command | Update the scope sentences and the Step 6 command to include `tools` | `REQ-003`; AC-3 | Scope text and the two commands that name `tests/eventbus` (checked in Step 3; not listed in the Issue) | N/A: documentation; `check_skills_references.py` | Verified |
| `routing.md` | Update "Adding a new tool" step 2 | Replace the note that the default scope excludes `tools/` | `REQ-003`; AC-3 | Step 2 states `files` scope covers `scripts/` and `tests/eventbus`, not `tools/` (checked in Step 2) | N/A: documentation; `check_skills_references.py` | Verified |
| `skills/code-implementation/workflow.md` | Remove a stale scope statement | Step 7 note says a bare 'uv run mypy' does not cover tools/; after the scope change it does, so the sentence must change | REQ-003 / AC-3 | skills/code-implementation/workflow.md:396 'because a bare uv run mypy does not cover tools/' (found in Step 3a of plan-to-implementation-procedure) | N/A: documentation; check_skills_references.py | Verified |
| `skills/python-implementation/workflow.md` | Remove a stale scope statement | The mypy command comment says mypy's configured scope omits tools/; after the scope change it includes tools/ | REQ-003 / AC-3 | skills/python-implementation/workflow.md:330 '(mypy's configured scope omits tools/)' (found in Step 3a of plan-to-implementation-procedure) | N/A: documentation; check_skills_references.py | Verified |
| `skills/python-code-review/workflow.md` | Remove two stale scope statements | Two sentences say a bare 'uv run mypy' / mypy's files scope omits tools/; after the scope change they are false | REQ-003 / AC-3 | skills/python-code-review/workflow.md:41 and :156 name tools/ as outside mypy's scope (found in Step 3a of plan-to-implementation-procedure) | N/A: documentation; check_skills_references.py | Verified |

## Reference Files
| File Path | Why It Must Be Read | Related Target File or Requirement |
|---|---|---|
| `.pre-commit-config.yaml` | The `mypy` hook runs `uv run mypy --no-namespace-packages --no-incremental` with `pass_filenames: false`, so it follows `pyproject.toml`; no edit is needed | `REQ-002` |
| `tests/tools/test_run_validation_gates.py` | Asserts the `mypy` gate exists; confirms no test pins the command tuple | `REQ-002` |
| `tools/manage_workitem_stage.py` | Source of the two `annotation-unchecked` notes that stay out of scope | `REQ-005` |

## Acceptance Criteria
- AC-1: `uv run mypy --no-namespace-packages scripts/ tests/eventbus tools` reports no errors and no `# type: ignore` was added (`REQ-001`, `REQ-005`).
- AC-2: `pyproject.toml`, `ci.yml`, `tox.ini`, and the `run_validation_gates.py` mypy gate name the same scope (`REQ-002`).
- AC-3: `rules/toolchain.md`, `rules/coding.md`, `skills/python-lint-typecheck/workflow.md`, and `routing.md` state that scope and `routing.md` no longer says `tools/` is skipped (`REQ-003`).
- AC-4: The pre-commit `mypy` hook type-checks `tools/` without separate configuration, and the measured extra run time is recorded in `rules/toolchain.md` or the commit message (`REQ-002`, `REQ-004`).
- AC-5: `uv run pytest tests/tools -q` and `uv run python tools/run_validation_gates.py` pass (`REQ-005`).

## Tests
- No new unit test: the fix is a type annotation and the scope change is configuration; the mypy command is the check (`REQ-001`, `REQ-002`).
- Regression: `uv run pytest tests/tools -q` confirms no behavior change (`REQ-005`).
- Gate check: `uv run python tools/run_validation_gates.py` exercises the changed gate command (`REQ-002`).

## Documentation Impact
Yes (operational notes only): `rules/toolchain.md`, `rules/coding.md`, `skills/python-lint-typecheck/workflow.md`, and `routing.md` state the scope (`REQ-003`). No `docs/*.md` file states it (searched `docs/`, only ADR test paths matched).

## Assumptions
- Annotating `result` as `dict[str, Any]` is the smallest typing that matches the method's declared return type `dict[str, Any]` (judgment; a TypedDict would be a larger change than the Issue asks for).
- Leaving the two `annotation-unchecked` notes is acceptable because they are notes, and enabling `--check-untyped-defs` is stricter than this Issue's scope (Issue Out of Scope).
- A cold `--no-incremental` timing can be measured during implementation; the warm-cache run took 0.8 seconds on 2026-11-05.
- Step 3a of `plan-to-implementation-procedure` found three more files that state `tools/` is outside mypy's scope and become false after this change: `skills/code-implementation/workflow.md:396`, `skills/python-implementation/workflow.md:330`, and `skills/python-code-review/workflow.md:41` and `:156`. They were added as target rows on 2026-11-05 (class fallout, `tools/amend_plan.py`) because they only keep existing documentation true. The earlier `rg 'tests/eventbus'` enumeration missed them since they are phrased as "does not cover `tools/`"; a second search for that phrasing over `rules`, `skills`, `routing.md`, `prompts`, `templates`, `docs`, `tools`, and `.github` found no other file (checked in Step 3a).
- Overlap judgments (`check_plan_target_overlaps.py`, checked in Step 2): `.github/workflows/ci.yml`, `routing.md`, `rules/toolchain.md`, and `tools/run_validation_gates.py` are also targeted by the `toolsizegate001` Plan, and `tools/run_validation_gates.py` also by the `toolcommon001` Plan. All are sequencing dependencies, not conflicts: those Plans edit different parts (the Module size step and the `check_module_size` routing text; the `_git_diff_name_only` call) and both record `Depends on` this Plan.

## Unknowns
| ID | Unknown Description | Evidence Missing | Resolution Path | Blocking? (True/False) |
|---|---|---|---|---|
| UNK-01 | Extra CI and pre-commit time from checking `tools/` with `--no-incremental` | Only a warm-cache run (0.8 seconds) was measured | Time `uv run mypy --no-namespace-packages --no-incremental scripts/ tests/eventbus tools` before and after in Phase 3 and record both numbers | False |

## Affected areas
| File | Change | Blast Radius | Churn (30d) | Bus Factor | deploy.sh Impact |
|---|---|---|---|---|---|
| `tools/check_canonical_source_registry.py` | Modify | Low (one annotation; checker used by pre-commit) | N/A (outside the top 60 of the 30-day listing) | High (one author across the repository history) | not applicable (rsynced) |
| `pyproject.toml` | Modify | Medium (changes the pre-commit and default mypy scope) | 11 | High | not applicable (rsynced) |
| `.github/workflows/ci.yml` | Modify | Medium (CI gate) | 14 | High | not applicable (rsynced) |
| `tox.ini` | Modify | Low | N/A | High | not applicable (rsynced) |
| `tools/run_validation_gates.py` | Modify | Medium (gate table used by `run_validation_gates.py` itself) | 9 | High | not applicable (rsynced) |
| `rules/toolchain.md` | Modify | Low (documentation, loaded by every workflow) | 13 | High | not applicable (rsynced) |
| `rules/coding.md` | Modify | Low | N/A | High | not applicable (rsynced) |
| `skills/python-lint-typecheck/workflow.md` | Modify | Low | 7 | High | not applicable (rsynced) |
| `routing.md` | Modify | Low | 26 | High | not applicable (rsynced) |
| `skills/code-implementation/workflow.md` | Modify | Not assessed (amendment 2026-11-05) | N/A | N/A | Not assessed (amendment 2026-11-05) |
| `skills/python-implementation/workflow.md` | Modify | Not assessed (amendment 2026-11-05) | N/A | N/A | Not assessed (amendment 2026-11-05) |
| `skills/python-code-review/workflow.md` | Modify | Not assessed (amendment 2026-11-05) | N/A | N/A | Not assessed (amendment 2026-11-05) |

## Design
- Path B (more than 3 files). Architecture analysis: `tools/` is outside `.importlinter` contracts (no `tools` entry), so no layer rule is affected. Dependency graphing: the scope string appears in the nine target files above and in the `pre-commit` hook through `pyproject.toml`; `rg 'tests/eventbus'` over `rules`, `skills`, `tools`, `docs`, `.github`, `routing.md`, `tox.ini`, and `pyproject.toml` found no other statement of the mypy scope (the remaining matches are test paths in ADRs and rules); statements phrased as "does not cover `tools/`" were found by a second search in Step 3a and are the last three target rows. Historical analysis: churn figures are in the Affected areas table; all history is by one author (git shortlog), hence Bus Factor High. Operational dependency inspection: not applicable (no MCP server, database, or dependency upgrade).
- Validation quality baseline: `radon cc` grades `CanonicalSourceRegistry.validate_all` outside the C-or-worse list (only `generate_report` B (10) is near it); `vulture scripts/` and `bandit -r scripts/` baselines are unrelated to `tools/` changes and unchanged (`vulture` reports only existing unused-variable findings; `bandit` reports 0 Medium and 0 High severity findings on the recorded run). diff-cover baseline: `N/A: no diff exists before implementation`; the plan requires at least 90 percent on changed lines (`rules/toolchain.md` Completion checklist).
- Order inside the change set: fix the typing first, confirm `uv run mypy --no-namespace-packages tools` is clean, then widen the scope everywhere in one commit.
- Consumer scan: not applicable for a persisted schema or public API; the scope string consumers were enumerated by the `rg` above.

## Implementation steps
1. **Phase 1: Fix the typing**
   - [ ] Annotate `result` in `validate_all` (`REQ-001`, `REQ-005`; `tools/check_canonical_source_registry.py`)
2. **Phase 2: Widen the scope everywhere**
   - [ ] Add `tools` to the configuration and command rows (`REQ-002`; `pyproject.toml`, `.github/workflows/ci.yml`, `tox.ini`, `tools/run_validation_gates.py`)
   - [ ] Update the documented scope and the "Adding a new tool" note (`REQ-003`; `rules/toolchain.md`, `rules/coding.md`, `skills/python-lint-typecheck/workflow.md`, `routing.md`)
   - [ ] Remove a stale scope statement (REQ-003; `skills/code-implementation/workflow.md`) — amendment 2026-11-05
   - [ ] Remove a stale scope statement (REQ-003; `skills/python-implementation/workflow.md`) — amendment 2026-11-05
   - [ ] Remove two stale scope statements (REQ-003; `skills/python-code-review/workflow.md`) — amendment 2026-11-05
3. **Phase 3: Verification**
   - [ ] Run the new mypy command with and without `--no-incremental`, record the run times, confirm no "Source file found twice" (`REQ-004`; `pyproject.toml`)
   - [ ] Run `uv run pytest tests/tools -q`, `uv run python tools/run_validation_gates.py`, `uv run python tools/check_suppression_justification.py`, `uv run python tools/check_skills_references.py`, and the pre-commit `mypy` hook (`REQ-005`, `REQ-002`; all rows). No deploy step: no `scripts/` or `config/` file changes.

### Release units
N/A: no release unit (Phase 1 is valid alone; Phase 2 must not land before Phase 1, which the phase order guarantees)

## Validation plan
| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| `tools/check_canonical_source_registry.py` | Type check, then regression | `uv run mypy --no-namespace-packages tools`; `uv run pytest tests/tools/test_check_canonical_source_registry.py -q` | No error; tests pass |
| scope rows | Integration of the whole scope | `uv run mypy --no-namespace-packages scripts/ tests/eventbus tools` | No error, no "Source file found twice" |
| pre-commit hook | Integration | `uv run pre-commit run mypy --all-files` | Passes with `tools/` included |
| gate table | Integration | `uv run python tools/run_validation_gates.py` | Pass or documented `Not available` entries only |
| docs rows | Reference check | `uv run python tools/check_skills_references.py` | No dangling reference |
| `tools/run_validation_gates.py` | Lint, format, security | `uv run ruff format`, `uv run ruff check`, `uv run bandit tools/run_validation_gates.py` | Clean |

## Risks
- **Risk**: The hook or CI run time grows noticeably → **Mitigation**: record the cold and warm times in Phase 3 (UNK-01); the warm run took 0.8 seconds.
- **Risk**: A later `tools/` change adds a type error and blocks unrelated commits → **Mitigation**: this is the intended gate; the cost is the point of the Issue and the current baseline is clean.
- **Risk**: One of the twelve scope statements is missed and drifts → **Mitigation**: the `rg 'tests/eventbus'` enumeration and the "does not cover `tools/`" search (`rg -n "does not cover .tools|omits .tools|configured scope omits"`) are repeated at the end of Phase 2 and compared with the target rows.
- **Risk**: `rules/toolchain.md` and `routing.md` are loaded by every workflow, so a wording error spreads → **Mitigation**: edit text minimally and run `check_skills_references.py` and `check_skills_heading_cycles.py`.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Fix the typing in `validate_all` | Completed | — | 20261105-143612 |  |
| 2 | Widen the mypy scope in configuration, gate table, and docs | Completed | — | 20261105-154220 |  |
| 3 | Verify with mypy, tests, gates, and record run time | Completed | — | 20261105-154305 | Run by code-implementation. Cold mypy (--no-incremental) before 26.9 s (491 files), after 30.3 s (557 files, +3.4 s); 0 errors; no 'Source file found twice'; pre-commit mypy hook Passed; check_suppression_justification, check_skills_references, run_validation_gates clean; tests/tools covered by the full suite (11607 passed) |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| — | — | — | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| implementations/20261105-133115_01_tools_check_canonical_source_registry.py.md | 1 | Procedure | Completed | — | — |
| implementations/20261105-133115_02_pyproject.toml.md | 2 | Procedure | Completed | — | — |
| implementations/20261105-133115_03_.github_workflows_ci.yml.md | 2 | Procedure | Completed | — | — |
| implementations/20261105-133115_04_tox.ini.md | 2 | Procedure | Completed | — | — |
| implementations/20261105-133115_05_tools_run_validation_gates.py.md | 2 | Procedure | Completed | — | — |
| implementations/20261105-133115_06_rules_toolchain.md.md | 2 | Procedure | Completed | — | — |
| implementations/20261105-133115_07_rules_coding.md.md | 2 | Procedure | Completed | — | — |
| implementations/20261105-133115_08_skills_python-lint-typecheck_workflow.md.md | 2 | Procedure | Completed | — | — |
| implementations/20261105-133115_09_routing.md.md | 2 | Procedure | Completed | — | — |
| implementations/20261105-133115_10_skills_code-implementation_workflow.md.md | 2 | Procedure | Completed | — | — |
| implementations/20261105-133115_11_skills_python-implementation_workflow.md.md | 2 | Procedure | Completed | — | — |
| implementations/20261105-133115_12_skills_python-code-review_workflow.md.md | 2 | Procedure | Completed | — | — |

## Traceability
- **Workflow phase**: issue-to-plan
- **Source issue**: issues/20261104-152002_toolmypy001_add-tools-to-mypy-scope.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: this document is the generated plan
- **Source implementation procedure**: N/A: not applicable in this phase
- **Generated at**: 20261105-105442
- **Related target files**: tools/check_canonical_source_registry.py, pyproject.toml, .github/workflows/ci.yml, tox.ini, tools/run_validation_gates.py, rules/toolchain.md, rules/coding.md, skills/python-lint-typecheck/workflow.md, routing.md, skills/code-implementation/workflow.md, skills/python-implementation/workflow.md, skills/python-code-review/workflow.md

### Requirement Traceability
| Requirement ID | Source Issue section or evidence | Target file | Implementation step | Acceptance criterion | Test or validation item | Status |
|---|---|---|---|---|---|---|
| REQ-001 | Required Changes 1; mypy run (Step 2) | `tools/check_canonical_source_registry.py` | 1 | AC-1 | `uv run mypy --no-namespace-packages tools` | Confirmed by repository evidence |
| REQ-002 | Required Changes 2; Acceptance Criteria 1, 3 | `pyproject.toml` | 2, 3 | AC-2, AC-4 | Pre-commit mypy hook run | Explicit in issue |
| REQ-002 | Required Changes 2 | `.github/workflows/ci.yml` | 2 | AC-2 | Run of the CI command | Explicit in issue |
| REQ-002 | Verification of other scope statements (Step 3) | `tox.ini` | 2 | AC-2 | Run of the tox command | Confirmed by repository evidence |
| REQ-002 | Target Files (gate table, located in Step 3) | `tools/run_validation_gates.py` | 2 | AC-2 | `run_validation_gates.py` run and `test_run_validation_gates.py` | Confirmed by repository evidence |
| REQ-003 | Required Changes 3 | `rules/toolchain.md` | 2 | AC-3 | `check_skills_references.py` | Explicit in issue |
| REQ-003 | Verification of other scope statements (Step 3) | `rules/coding.md` | 2 | AC-3 | `check_skills_references.py` | Confirmed by repository evidence |
| REQ-003 | Verification of other scope statements (Step 3) | `skills/python-lint-typecheck/workflow.md` | 2 | AC-3 | `check_skills_references.py` | Confirmed by repository evidence |
| REQ-003 | Target Files (`routing.md` documented mypy commands) | `routing.md` | 2 | AC-3 | `check_skills_references.py` | Explicit in issue |
| REQ-004 | Required Changes 4; Constraints; Unresolved Questions | `pyproject.toml` | 3 | AC-4 | Timed mypy runs | Derived from confirmed evidence |
| REQ-005 | Constraints; Testing Expectations | `tools/check_canonical_source_registry.py` | 1, 3 | AC-1, AC-5 | `uv run pytest tests/tools -q`; suppression check | Explicit in issue |
| REQ-003 | Amendment 2026-11-05: Step 7 note says a bare 'uv run mypy' does not cover tools/; after the scope change it does, so the sentence must change | skills/code-implementation/workflow.md | Phase 2 | AC-3 | N/A: documentation; check_skills_references.py | Confirmed by repository evidence |
| REQ-003 | Amendment 2026-11-05: The mypy command comment says mypy's configured scope omits tools/; after the scope change it includes tools/ | skills/python-implementation/workflow.md | Phase 2 | AC-3 | N/A: documentation; check_skills_references.py | Confirmed by repository evidence |
| REQ-003 | Amendment 2026-11-05: Two sentences say a bare 'uv run mypy' / mypy's files scope omits tools/; after the scope change they are false | skills/python-code-review/workflow.md | Phase 2 | AC-3 | N/A: documentation; check_skills_references.py | Confirmed by repository evidence |

<!-- tools/generate_workitem.py implementation-procedure-pass timestamp: 20261105-133115 -->