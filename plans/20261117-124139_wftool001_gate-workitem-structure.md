## Goal
- Make every new or changed top-level issue, plan, and implementation procedure pass an automatic structure check at commit time (the validation gate and a pre-commit hook), and make the structure checker detect unfilled issue-template leftovers by itself, so the manual snippet in the issue-creator workflow can be removed.

## Priority
Medium

## Scope
- **In-Scope**: (1) `tools/check_workitem_structure.py` accepts several paths after one `--file`; (2) the checker reports template leftovers of an issue; (3) the gate table runs the check on changed top-level work item files; (4) a pre-commit hook with the same trigger; (5) the issue-creator Step 10.4 snippet and the routing row are updated; (6) the tool description is updated; (7) tests for each.
- **Out-of-Scope**: changing any template; checking archived work items under `done/`; content-quality judgment; leftover detection for plans and procedures (UNK-01); automatic detection of generic `{...}` braces; any change to `tools/run_validation_gates.py`.
- **Dependencies**: N/A: nothing must be done first. The gate-output-noise work (wftool006) follows this Plan, because this Plan removes the structure check from the runtime-placeholder rows of the gate output. `tools/TOOL_DESCRIPTIONS.md` is also edited by the other tooling issues of this batch and by the open procedure `implementations/20261117-110514_04_tools_TOOL_DESCRIPTIONS.md.md`; the edits here touch one table row, and the order is settled at implementation time (UNK-02).

## Background
Filed from the investigation of the issue -> plan -> implementation toolchain. The gate table maps the structure check with a runtime placeholder, so it is always `Not available`; the only pre-commit hook for the checker is `--archived-status`. The checker verifies section presence only, and `skills/issue-creator/workflow.md` Step 10.4 replaces leftover detection with a manual shell snippet.

## Problem
A structurally incomplete or unfilled work item can be committed and pushed: the latest issue commits passed the gate run and the pre-commit run with no structure check. Evidence: the gate row for `check_workitem_structure` carries `<path>` (`Explicit in code`, `tools/_validation_gate_defs.py`); the hook list holds only `archived-procedure-status` for this checker (`Explicit in code`, `.pre-commit-config.yaml`); the checker has no leftover logic (`Explicit in code`).

## Reason for Change
The skills rely on each author running the check by hand, and the leftover check exists only as prose plus a snippet that an author can skip or mistype. The gate already has a changed-file expansion (`__CHANGED_FILES__`), so closing the gap needs a small change; no deadline makes it urgent.

## Implementation Intent
The gate and the hook select the structure check for changed top-level work item files only, and the checker derives its leftover rule from `templates/issue.md` so there is one source. The existing `--file` single-path behavior and the checker id stay stable, so the routing row and the hook-parity check need no new mapping logic. The change lands in the gate table module, not in the already near-limit orchestrator.

## Requirements
- `REQ-001`: `--file` accepts one or more paths (`nargs="+"`); a single path behaves exactly as before, and each path is checked and reported.
- `REQ-002`: For an issue, the checker reports category `template-leftover` findings for (a) a verbatim template instruction line, (b) a verbatim template bullet line that holds a `{...}` placeholder, and (c) the verbatim `# <Issue Title>` title line; the rule is derived at run time from the `templates/issue.md` fence and applies in `--file` and directory-scan modes; plans and procedures are unaffected.
- `REQ-003`: The `check_workitem_structure` gate runs automatically: its command is `--file __CHANGED_FILES__` and its patterns select only top-level `issues/*.md`, `plans/*.md`, and `implementations/*.md` (never `done/`).
- `REQ-004`: A pre-commit hook `workitem-structure` runs the same command on staged top-level work item files, mirrors the gate trigger, and passes the hook-parity check without an allowlist entry.
- `REQ-005`: `skills/issue-creator/workflow.md` Step 10.4 replaces the leftover snippet with the checker invocation and keeps the manual brace judgment; the `routing.md` row states the automatic run and the leftover check.
- `REQ-006`: The `check_workitem_structure.py` entry of `tools/TOOL_DESCRIPTIONS.md` describes the multi-path `--file` and the leftover check.
- `REQ-007`: The change keeps the `tools/` module-size gates passing with `tools/_validation_gate_defs.py` below the limit, adds no new function of complexity grade C, and keeps ruff, mypy, and bandit clean on the changed tools.

## Implementation Target Files
**Freeze status**: Frozen

This table is the canonical, frozen source of implementation scope for this Plan. Once
`Frozen`, `Implementation steps`, `Acceptance criteria`, and every downstream
`plan-to-implementation-procedure` document MUST reference file paths only from this
table — no other file may be treated as a modification target.

| File Path | Change Responsibility | Reason for Modification | Related Requirement / Acceptance Criterion | Repository Evidence | Related Tests | Validation Status |
|---|---|---|---|---|---|---|
| `tools/check_workitem_structure.py` | Multi-path `--file`; leftover detection for issues | `--file` takes one `Path` and the module has no leftover logic | REQ-001, REQ-002, REQ-007 / AC-1, AC-2, AC-3, AC-9 | `build_arg_parser` defines `--file` with `type=Path`; no leftover function exists; 18168 B of a 24576 B limit; not in the size baseline (checked in Step 3) | `tests/tools/test_check_workitem_structure.py` | Verified |
| `tools/_validation_gate_defs.py` | Make the structure gate auto-runnable and top-level only | The gate row carries `<path>` and `**` patterns, so `requires_context` is true and `done/` matches | REQ-003, REQ-007 / AC-4, AC-5, AC-9 | The `check_workitem_structure` Gate holds `"<path>"` and `("plans/**", "issues/**", "implementations/**")`; 24247 B, 329 B of headroom (checked in Step 3) | `tests/tools/test_run_validation_gates.py` | Verified |
| `.pre-commit-config.yaml` | Add the `workitem-structure` hook | The only hook for this checker is `--archived-status` | REQ-004 / AC-6 | `archived-procedure-status` is the sole `check_workitem_structure` hook; `workitem-traceability` is the precedent for the `files` filter (checked in Step 3) | `tests/tools/test_run_validation_gates.py` | Verified |
| `routing.md` | State the automatic run and the leftover check in the existing row | The row still describes a manual `--file <path>` check only | REQ-005 / AC-7 | The "When to run which tool" row for `check_workitem_structure.py --file <path>` (checked in Step 3) | `tools/check_skills_references.py`, `tools/check_skills_heading_cycles.py` | Verified |
| `skills/issue-creator/workflow.md` | Replace the Step 10.4 snippet with the checker call | The step carries a `mktemp` snippet and a manual placeholder search | REQ-005 / AC-7 | Step 10.4 holds the snippet and the brace search (checked in Step 3) | `tools/check_skills_references.py` | Verified |
| `tools/TOOL_DESCRIPTIONS.md` | Update the entry for the changed flag and the new check | The entries describe presence-only checking and a one-path `--file` | REQ-006 / AC-8 | Table rows for `check_workitem_structure.py` exist in two sections (checked in Step 3) | `tools/check_tool_descriptions_sync.py` | Verified |
| `tests/tools/test_check_workitem_structure.py` | Add multi-path and leftover tests | No test covers several paths or leftovers | REQ-001, REQ-002 / AC-1, AC-2, AC-3 | Existing end-to-end tests install the real templates under `tmp_path` and monkeypatch `ROOT_DIR` (checked in Step 3) | The file itself | Verified |
| `tests/tools/test_run_validation_gates.py` | Add gate-selection and hook-parity tests | `_PARITY_GATES` and the trigger table do not include the structure gate | REQ-003, REQ-004 / AC-4, AC-5, AC-6 | `_PARITY_GATES` and `test_parity_gate_triggers_mirror_hook_filters` pin gate triggers to hook filters (checked in Step 3) | The file itself | Verified |

## Reference Files
Files that must be read to implement the targets above, but MUST NOT be modified. Same
one-file-per-row discipline as `Implementation Target Files` above — no directories,
glob patterns, components, file groups, or vague phrases.

| File Path | Why It Must Be Read | Related Target File or Requirement |
|---|---|---|
| `tools/run_validation_gates.py` | `run_gate` already expands `__CHANGED_FILES__` for the files that match the gate patterns; it stays unchanged and is 23988 B of 24576 B | `tools/_validation_gate_defs.py` / REQ-003, REQ-007 |
| `templates/issue.md` | Its fenced block is the single source of the leftover rule | `tools/check_workitem_structure.py` / REQ-002 |
| `tools/amend_plan.py` | It runs the checker with one `--file` path, so the single-path behavior must stay | `tools/check_workitem_structure.py` / REQ-001 |
| `tools/check_module_size_tools_baseline.txt` | Neither changed tool is listed, so both must stay under the limit | `tools/_validation_gate_defs.py` / REQ-007 |

## Acceptance Criteria
- AC-1 (REQ-001): `--file a b` checks both documents and reports each finding with its file; a single path gives the output it gave before (test).
- AC-2 (REQ-002): An unfilled issue scaffold exits `1` with `template-leftover` findings, a filled issue exits `0`, and an issue whose own content holds braces is not reported (tests).
- AC-3 (REQ-002): A plan and an implementation procedure built from their real templates get no `template-leftover` finding (test).
- AC-4 (REQ-003): `select_gates` selects `check_workitem_structure` for `issues/i.md`, `plans/p.md`, and `implementations/i.md`, never for a `done/` path; the gate is not `requires_context`, and its command expands to `--file <matched paths>` (tests).
- AC-5 (REQ-003): A top-level issue lacking a required section makes the checker exit `1`, so the gate result is `Fail` (test with a runner).
- AC-6 (REQ-004): `parse_precommit_hooks` maps `workitem-structure` to the gate's checker id, `uv run python tools/run_validation_gates.py drift` passes with no `COMMIT_ONLY_HOOKS` entry, and the parity test includes the gate.
- AC-7 (REQ-005): Step 10.4 no longer contains the `mktemp` snippet, and `tools/check_skills_references.py` and `tools/check_skills_heading_cycles.py` pass.
- AC-8 (REQ-006): `tools/check_tool_descriptions_sync.py` passes and the entry names the new behavior.
- AC-9 (REQ-007): Both `tools/check_module_size.py` scopes pass, `tools/_validation_gate_defs.py` is below the limit, and ruff, mypy, and bandit are clean on the changed tools; radon reports no new grade C function.

## Tests
- `tests/tools/test_check_workitem_structure.py`: multi-path `--file`; unfilled scaffold, filled issue, brace content, and the title line (REQ-001, REQ-002); plan and procedure skeletons stay clean (REQ-002).
- `tests/tools/test_run_validation_gates.py`: selection for top-level and `done/` paths, `requires_context` false, sentinel expansion, hook-id parity, and the extended `_PARITY_GATES` table (REQ-003, REQ-004).
- Smoke run on the live repository: the checker over the open work items and a throwaway scaffold (REQ-001, REQ-002).

## Documentation Impact
N/A for `docs/*.md`: no file under `docs/` changes. The routing row, the issue-creator workflow step, and the tool description change (REQ-005, REQ-006).

## Assumptions
- `_changed_files` lists tracked staged or modified paths only (`git diff --name-only`), so the gate sees a new issue file once it is staged; this matches the commit skill's stage-then-gate order.
- pre-commit passes the staged filenames to a hook whose `pass_filenames` is left at its default, and the hook `files` regular expression mirrors the gate patterns (the same shape as `workitem-traceability`).
- A single maintainer owns every target file (the shortlog shows one author under name variants), so no cross-owner approval step is planned.
- The open procedure for `tools/TOOL_DESCRIPTIONS.md` of `compat004` edits other rows than the `check_workitem_structure.py` entries; its content was not read in this cycle (UNK-02).
- Overlap with other active Frozen Plans: none, because `plans/` holds no other Plan (recorded in Step 8b).

## Unknowns
| ID | Unknown Description | Evidence Missing | Resolution Path | Blocking? (True/False) |
|---|---|---|---|---|
| UNK-01 | Which leftover rule suits plans and procedures | The issue-template rule does not transfer: the plan template has many instruction lines and a filled archived plan keeps many of them verbatim, and a filled archived procedure keeps most of the procedure template's instruction lines | File a follow-up issue that analyses a rule per template (for example bracket-wrapped placeholder lines) before extending REQ-002 | False |
| UNK-02 | Order against the open procedure `implementations/20261117-110514_04_tools_TOOL_DESCRIPTIONS.md.md` and the sibling tooling issues that edit `tools/TOOL_DESCRIPTIONS.md` | The procedure's target rows were not read | Read its target rows at implementation time; the edits are row-level and compatible unless they share the `check_workitem_structure.py` rows, in which case land the earlier one first | False |

## Affected areas
`skills/DESIGN.md` Change-impact table, extended with `Churn (30d)` and `Bus Factor`
columns. The `File` column here MUST be a subset of `Implementation Target Files`'
rows — this table analyzes change-impact risk for those same files; it is not a
separate scope-of-record.

| File | Change | Blast Radius | Churn (30d) | Bus Factor | deploy.sh Impact |
|---|---|---|---|---|---|
| `tools/check_workitem_structure.py` | Modify | Medium: four workflow documents, `tools/amend_plan.py`, a hook, and a gate call it | 4 | High: single author | not applicable (rsynced) |
| `tools/_validation_gate_defs.py` | Modify | Low: imported by the orchestrator and its test only; one gate row changes | 5 | High: single author | not applicable (rsynced) |
| `.pre-commit-config.yaml` | Modify | Medium: the hook runs on every commit that touches a top-level work item | 11 | High: single author | not applicable (rsynced) |
| `routing.md` | Modify | Low: one table row; the drift check reads the Run cell | 20 | High: single author | not applicable (rsynced) |
| `skills/issue-creator/workflow.md` | Modify | Low: one step | 4 | High: single author | not applicable (rsynced) |
| `tools/TOOL_DESCRIPTIONS.md` | Modify | Low: documentation rows; the sync checker reads it | 74 | High: single author | not applicable (rsynced) |
| `tests/tools/test_check_workitem_structure.py` | Modify | Low | 4 | High: single author | not applicable (rsynced) |
| `tests/tools/test_run_validation_gates.py` | Modify | Low | 10 | High: single author | not applicable (rsynced) |

## Design
**Classification**: Path B (eight target rows). The architecture, dependency, historical, and operational analyses were run once for this cycle.
- **Architecture**: both Python targets import only the standard library, `orjson`, and `tools._workitem_status_table`; the import-linter contracts (six) are kept and cover `scripts/` packages, so no boundary is affected.
- **Dependency graphing**: callers of the checker are four skills, `routing.md`, `tools/amend_plan.py` (one `--file` path), the gate table (two rows), and one test module; `tools/_validation_gate_defs.py` is imported by `tools/run_validation_gates.py` and its test. The consumer scan for the checker found no other consumer; it lists candidates only, and the test-impact data it relies on was stale.
- **Historical**: churn is highest for `tools/TOOL_DESCRIPTIONS.md` (merge-conflict risk) and `routing.md`; every target has one author, so the bus factor is high (`git shortlog`; `git-fame` was not needed).
- **Operational**: no port, database, or dependency is involved; `pip-audit` and lock checks do not apply. The persisted-schema check does not apply.
- **Decision 1, `--file` arity**: make `--file` take one or more paths. Alternative: a new `--files` flag. Rejected because the checker id (derived from the first flag) would change, which forces a new routing row and a mapping change; `nargs="+"` keeps the id `check_workitem_structure:--file`, keeps the routing row valid, and lets pre-commit append filenames.
- **Decision 2, gate and hook**: add both. The gate serves the commit skill's pre-commit run; the hook serves a raw `git commit`. This resolves the issue's open question; the precedent is `workitem-traceability`. The hook `files` regular expression is `^(issues|plans|implementations)/[^/]+\.md$`, and the gate patterns are the matching single-segment globs, so `done/` never matches.
- **Decision 3, where the gate change lives**: the issue named `tools/run_validation_gates.py`. Reading it showed that `run_gate` already expands `__CHANGED_FILES__` and that the gate rows live in `tools/_validation_gate_defs.py`. The orchestrator stays unchanged. The gate-row edit adds roughly 25 bytes to a module with 329 bytes of headroom; REQ-007 verifies it.
- **Decision 4, leftover rule scope**: the rule is the 25 non-bullet instruction lines plus the 5 template bullets that hold a `{...}` placeholder plus the title line, matched verbatim. Measured on the repository: no open issue hits it and one archived issue hits it. The same verbatim rule is not usable for a plan (81 candidate lines; a filled archived plan keeps about 22 to 48 of them verbatim) or a procedure (13 candidates; a filled archived procedure keeps 9), so REQ-002 is limited to issues and UNK-01 records the rest.
- **Decision 5, braces**: generic brace detection stays manual, because open issues contain legitimate braces in their own content; only the template's own placeholder lines are detected.
- **Baseline**: `radon` reports `find_release_unit_findings` (grade C) in the checker and `_checker_id_from_command` (grade C) in the gate module, both pre-existing and untouched; the new leftover function must stay below grade C. `vulture` and `bandit` findings under `scripts/` are pre-existing and outside the targets. `diff-cover` has no baseline: the tree equals `master`, so the diff is empty; the 90% threshold applies at implementation.

## Implementation steps
Each step description MUST cite the exact file path(s) it touches by referencing rows
of `Implementation Target Files` above — do not restate file-level detail
independently of that frozen table. A step is a top-level numbered item (a Phase); its
checklist items are sub-tasks, and the Execution Status table has one row per step.

1. **Phase 1: Checker changes**
   - [ ] Make `--file` accept one or more paths and aggregate the findings (REQ-001; `tools/check_workitem_structure.py`)
   - [ ] Add the leftover detection for issues, derived from the template fence, in a function that stays below complexity grade C (REQ-002, REQ-007; `tools/check_workitem_structure.py`)
   - [ ] Add tests that fail first: multi-path, unfilled scaffold, filled issue, brace content, title line, and clean plan and procedure skeletons (REQ-001, REQ-002; `tests/tools/test_check_workitem_structure.py`)
2. **Phase 2: Gate table change** (applies after Phase 1, because the gate passes several paths to `--file`)
   - [ ] Replace the placeholder with `__CHANGED_FILES__` and narrow the patterns to single-segment globs (REQ-003, REQ-007; `tools/_validation_gate_defs.py`)
   - [ ] Add selection, `requires_context`, expansion, and `Fail` tests (REQ-003; `tests/tools/test_run_validation_gates.py`)
3. **Phase 3: Pre-commit hook**
   - [ ] Add the `workitem-structure` hook with the `--file` entry and the top-level `files` filter (REQ-004; `.pre-commit-config.yaml`)
   - [ ] Add the hook-id parity assertion and extend `_PARITY_GATES` and the trigger table (REQ-004; `tests/tools/test_run_validation_gates.py`)
4. **Phase 4: Documentation**
   - [ ] Replace the Step 10.4 snippet with the checker invocation and keep the manual brace judgment (REQ-005; `skills/issue-creator/workflow.md`)
   - [ ] Update the routing row note (REQ-005; `routing.md`)
   - [ ] Update the `check_workitem_structure.py` entries (REQ-006; `tools/TOOL_DESCRIPTIONS.md`)
5. **Phase 5: Verification** (no deploy step: no `scripts/` or `config/` file changes, and `deploy/deploy.sh` references `tools/` only for `manage_binaries.py`)
   - [ ] Run the validation sequence of `rules/toolchain.md` for the changed tools, both `tools/check_module_size.py` scopes, `run_validation_gates.py drift`, the skills reference checkers, and `tools/check_tool_descriptions_sync.py`; smoke-run the checker over the open work items and a throwaway scaffold (REQ-007; all target files)

### Release units
N/A: no release unit; each phase passes validation alone when applied in order 1 to 4.

## Validation plan
| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| `tools/check_workitem_structure.py` | Unit tests; smoke run on live work items | `uv run pytest tests/tools/test_check_workitem_structure.py -v`; `uv run python tools/check_workitem_structure.py` | New tests pass; the live scan reports no finding |
| `tools/_validation_gate_defs.py` | Unit tests; drift and size gates | `uv run pytest tests/tools/test_run_validation_gates.py -v`; `uv run python tools/run_validation_gates.py drift`; `uv run python tools/check_module_size.py --scripts-dir tools --baseline tools/check_module_size_tools_baseline.txt` | Tests pass, drift reports parity, size gate passes |
| `.pre-commit-config.yaml` | Integration: run the hook on a staged top-level issue | `uv run pre-commit run workitem-structure --files <an issue path>` | The hook passes on a filled issue and fails on an unfilled scaffold |
| `routing.md` | Doc consistency | `uv run python tools/check_skills_references.py`; `uv run python tools/check_skills_heading_cycles.py` | No finding |
| `skills/issue-creator/workflow.md` | Doc consistency | `uv run python tools/check_skills_references.py`; `uv run python tools/check_skills_heading_cycles.py` | No finding |
| `tools/TOOL_DESCRIPTIONS.md` | Doc consistency | `uv run python tools/check_tool_descriptions_sync.py` | No finding |
| `tests/tools/test_check_workitem_structure.py` | Self | `uv run mypy --no-namespace-packages scripts/ tests/eventbus tools`; ruff; bandit on the changed tools | Clean |
| `tests/tools/test_run_validation_gates.py` | Self | `uv run pytest tests/tools -n logical -q` | Pass |

## Risks
- **Risk**: `tools/_validation_gate_defs.py` is 329 B below the size limit → **Mitigation**: the edit is about 25 B; verify with the size gate before and after, and extract rows into a new module only if it fails.
- **Risk**: The hook blocks a commit that touches a legacy open work item shaped like an old template → **Mitigation**: the baseline scan reports no finding on the open items; run it again before the hook lands.
- **Risk**: `--file` arity change breaks `tools/amend_plan.py`, which passes one path → **Mitigation**: `nargs="+"` keeps single-path behavior; a test pins it and `tests/tools/test_amend_plan.py` runs in Phase 5.
- **Risk**: A legitimate issue reuses a template instruction line verbatim and is reported → **Mitigation**: the measured rate is one archived issue in 1650 and none of the open ones; the report names the line so the author can reword it.
- **Risk**: `tools/TOOL_DESCRIPTIONS.md` has the highest churn of the targets, so edits conflict → **Mitigation**: change one table row, rebase through the commit skill, and settle the order per UNK-02.
- **Risk**: The gate misses an untracked new issue file → **Mitigation**: the commit skill stages before the gate, and the hook sees staged files; the author still runs `--file` explicitly in Step 10.4.

## Execution Status

Table structure, status/type vocabulary, and general guidance: see
`templates/execution-status.md`. Default rows for a freshly generated Plan (replace
with the Plan's actual steps once Implementation steps are broken down):

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Checker: multi-path `--file` and issue leftover detection, with tests | Pending | — | — | |
| 2 | Gate table: auto-runnable top-level structure gate, with tests | Pending | — | — | |
| 3 | Pre-commit hook and parity tests | Pending | — | — | |
| 4 | Documentation: issue-creator step, routing row, tool description | Pending | — | — | |
| 5 | Verification: validation sequence, size and drift gates, smoke runs | Pending | — | — | |

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
- **Source issue**: issues/20261117-123330_wftool001_gate-workitem-structure.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: this document is the generated plan
- **Source implementation procedure**: N/A: not applicable in this phase
- **Generated at**: 20261117-124139
- **Related target files**: `tools/check_workitem_structure.py`; `tools/_validation_gate_defs.py`; `.pre-commit-config.yaml`; `routing.md`; `skills/issue-creator/workflow.md`; `tools/TOOL_DESCRIPTIONS.md`; `tests/tools/test_check_workitem_structure.py`; `tests/tools/test_run_validation_gates.py`

### Requirement Traceability
| Requirement ID | Source Issue section or evidence | Target file | Implementation step | Acceptance criterion | Test or validation item | Status |
|---|---|---|---|---|---|---|
| REQ-001 | Required Changes (several files per call) | `tools/check_workitem_structure.py` | Phase 1 | AC-1 | `uv run pytest tests/tools/test_check_workitem_structure.py` | Derived from confirmed evidence |
| REQ-001 | Required Changes (several files per call) | `tests/tools/test_check_workitem_structure.py` | Phase 1 | AC-1 | multi-path test | Derived from confirmed evidence |
| REQ-002 | Required Changes (leftover detection); measured rule in Step 3 | `tools/check_workitem_structure.py` | Phase 1 | AC-2, AC-3 | leftover tests | Derived from confirmed evidence |
| REQ-002 | Required Changes (fixtures) | `tests/tools/test_check_workitem_structure.py` | Phase 1 | AC-2, AC-3 | scaffold, filled, brace, skeleton tests | Derived from confirmed evidence |
| REQ-003 | Problem (gate row carries a placeholder) | `tools/_validation_gate_defs.py` | Phase 2 | AC-4, AC-5 | selection and expansion tests | Confirmed by repository evidence |
| REQ-003 | Required Changes (gate runs the check) | `tests/tools/test_run_validation_gates.py` | Phase 2 | AC-4, AC-5 | gate tests | Confirmed by repository evidence |
| REQ-004 | Unresolved Questions (hook versus gate) | `.pre-commit-config.yaml` | Phase 3 | AC-6 | `uv run pre-commit run workitem-structure --files <an issue path>` | Derived from confirmed evidence |
| REQ-004 | Required Changes (hook plus drift mapping) | `tests/tools/test_run_validation_gates.py` | Phase 3 | AC-6 | parity and id tests | Derived from confirmed evidence |
| REQ-005 | Required Changes (replace the snippet, update the row) | `skills/issue-creator/workflow.md` | Phase 4 | AC-7 | `tools/check_skills_references.py` | Explicit in issue |
| REQ-005 | Required Changes (update the routing row) | `routing.md` | Phase 4 | AC-7 | `tools/check_skills_heading_cycles.py` | Explicit in issue |
| REQ-006 | Documentation Impact | `tools/TOOL_DESCRIPTIONS.md` | Phase 4 | AC-8 | `tools/check_tool_descriptions_sync.py` | Explicit in issue |
| REQ-007 | Constraints (size gate, tool conventions) | `tools/check_workitem_structure.py` | Phase 5 | AC-9 | size gates, ruff, mypy, bandit, radon | Confirmed by repository evidence |
| REQ-007 | Constraints (size gate; the gate table is near the limit) | `tools/_validation_gate_defs.py` | Phase 5 | AC-9 | `tools/check_module_size.py` (tools scope) | Confirmed by repository evidence |
