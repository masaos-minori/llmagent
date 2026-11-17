## Goal
- Make the default output of `tools/run_validation_gates.py` show only rows that carry information: hide gates that cannot run because they need a runtime argument and print their count instead, keep every other `Not available` row visible, add a flag that shows all rows, and print the real base ref in the header.

## Priority
Low

## Scope
- **In-Scope**: (1) a classification of `Not available` results in the result model; (2) a renderer in a new module with the hide-by-default behavior, the count line, and the actual base ref in the header; (3) a `--verbose` flag; (4) tests for the renderer and the classification; (5) the Phase 4 note of the git workflow and the runner's description rows.
- **Out-of-Scope**: changing which gates are selected; changing exit code rules; changing the gate tables, the mappings, or the `drift` subcommand; correcting other drift in the runner's description rows (UNK-02).
- **Dependencies**: this Plan edits the import block of `tools/run_validation_gates.py`, which `plans/20261117-125207_wftool004_orphan-tool-routing.md` also edits, so it follows that Plan's phase 1. The Frozen Plan `plans/20261117-124139_wftool001_gate-workitem-structure.md` removes the structure check from the placeholder rows; no test here depends on that count, so the order against it is free. `tools/TOOL_DESCRIPTIONS.md` is also edited by the other tooling issues of this batch, the Frozen Plans for them, and the open procedure `implementations/20261117-110514_04_tools_TOOL_DESCRIPTIONS.md.md` (see Assumptions, UNK-01).
  - **Depends on**: plans/20261117-125207_wftool004_orphan-tool-routing.md | phase 1 | both Plans edit the import block of `tools/run_validation_gates.py`

## Background
Filed from the investigation of the issue -> plan -> implementation toolchain. A gate whose command carries a runtime placeholder is reported `Not available` on every run, and a gate whose local tool is missing is reported with the same status. The commit workflow tells the reader that `Not available` rows are not failures.

## Problem
The default output prints every gate whose command needs a runtime argument, so rows that can never run sit among rows that matter, and a genuinely missing local tool looks the same (`Explicit in code`: both go through `GateResult` with status `Not available` and differ only in a detail string). Eight of the routing gates that carry a placeholder are selected automatically by path patterns (`Explicit in code`, the gate table): three for any `docs/` change, and four or five for a change under `plans/`, `implementations/`, or `issues/`. The header prints `base: master` for every run, including a run with `--base ORIG_HEAD` (`Explicit in code` and `Operationally observed`). No test calls `main` or checks the printed summary (`Explicit in code`, `rg`).

## Reason for Change
The gate runs on every commit and sync, so the noise is paid each time, and the commit skill compensates with prose instead of the tool separating the two cases. The wrong header base can mislead a reader about what was compared. The severity is low and nothing makes the change urgent.

## Implementation Intent
The result model records why a gate was `Not available`, and the renderer, not the runner, decides what to show. Only the runtime-argument rows are hidden, because a missing-tool row is a check that did not run and must stay visible. The renderer lives in a new module because the runner is close to the size limit; moving it out makes the runner smaller. Gate selection, mappings, the `drift` subcommand, and exit codes do not change.

## Requirements
- `REQ-001`: `GateResult` carries a `reason` that is empty for `Pass` and `Fail` and, for `Not available`, one of `runtime-argument`, `missing-tool`, or `os-error`; `run_gate` sets it from the existing branches; the field has a default so existing constructors keep working.
- `REQ-002`: The default output omits the rows whose reason is `runtime-argument` and prints one line with their count and the flag that shows them; `Pass`, `Fail`, `Partial`, `Blocked`, and the other `Not available` rows stay visible; a run with no hidden rows prints no count line.
- `REQ-003`: `--verbose` prints every row, including the runtime-argument rows with their detail; selection, exit codes, and the `drift` subcommand are unchanged.
- `REQ-004`: The header prints the base ref that the run used.
- `REQ-005`: The renderer lives in `tools/_validation_gate_report.py`; `tools/run_validation_gates.py` imports it and ends smaller than today; no function in the new module reaches complexity grade C.
- `REQ-006`: The Phase 4 note of `skills/git-commit-and-sync/workflow.md` and the runner's description rows state the new default and the flag; `tools/TOOL_DESCRIPTIONS.md` has a row for the new module.

## Implementation Target Files
**Freeze status**: Frozen

This table is the canonical, frozen source of implementation scope for this Plan. Once
`Frozen`, `Implementation steps`, `Acceptance criteria`, and every downstream
`plan-to-implementation-procedure` document MUST reference file paths only from this
table — no other file may be treated as a modification target.

| File Path | Change Responsibility | Reason for Modification | Related Requirement / Acceptance Criterion | Repository Evidence | Related Tests | Validation Status |
|---|---|---|---|---|---|---|
| `tools/_validation_gate_report.py` | Create the renderer module | The summary printer must move out of the near-limit runner and gain the hide-by-default behavior | REQ-002, REQ-003, REQ-004, REQ-005 / AC-2, AC-3, AC-4, AC-5 | New file; `tools/` exists; the current printer is a private function of the runner and prints a fixed `master` base (checked in Step 3) | `tests/tools/test_run_validation_gates.py` | Verified |
| `tools/run_validation_gates.py` | Add the `reason` field, set it in `run_gate`, add `--verbose`, call the renderer | `GateResult` has no classification and the printer is inline | REQ-001, REQ-003, REQ-005 / AC-1, AC-3, AC-5 | `GateResult` has `name`, `status`, `command`, and `detail`; `run_gate` builds the three `Not available` results; 23988 B of 24576 B (checked in Step 3) | `tests/tools/test_run_validation_gates.py` | Verified |
| `tests/tools/test_run_validation_gates.py` | Add classification and renderer tests | No test covers the printed summary or the `Not available` reasons | REQ-001 to REQ-004 / AC-1 to AC-4 | The module tests `classify`, `run_gate`, and selection but never `main` or the summary (checked in Step 3) | The file itself | Verified |
| `skills/git-commit-and-sync/workflow.md` | Update the Phase 4 note | The note explains `Not available` rows as runtime-argument rows | REQ-006 / AC-6 | Phase 4 states that only `Fail` and `Blocked` rows matter and that `Not available` rows are not failures (checked in Step 3) | `tools/check_skills_references.py` | Verified |
| `tools/TOOL_DESCRIPTIONS.md` | Update the runner rows and add the module row | The rows describe neither the hidden rows nor the flag, and the new module has no row | REQ-006 / AC-6 | Two rows describe the runner; the sync checker requires a row for each `tools/*.py` (checked in Step 3) | `tools/check_tool_descriptions_sync.py` | Verified |

## Reference Files
Files that must be read to implement the targets above, but MUST NOT be modified. Same
one-file-per-row discipline as `Implementation Target Files` above — no directories,
glob patterns, components, file groups, or vague phrases.

| File Path | Why It Must Be Read | Related Target File or Requirement |
|---|---|---|
| `tools/_validation_gate_defs.py` | Defines `Gate.requires_context` and the placeholder rule that sets the reason | `tools/run_validation_gates.py` / REQ-001 |
| `rules/ai-execution.md` | Item 12: an unavailable check must never be reported as passed | `tools/_validation_gate_report.py` / REQ-002 |
| `tools/check_module_size_tools_baseline.txt` | Neither touched tool is listed, so both must stay under the limit | `tools/run_validation_gates.py` / REQ-005 |

## Acceptance Criteria
- AC-1 (REQ-001): `run_gate` returns reason `runtime-argument` for a gate with a placeholder, `missing-tool` when the command is not found, `os-error` for another `OSError`, and an empty reason for `Pass` and `Fail` (tests); existing tests that build `GateResult` without a reason still pass.
- AC-2 (REQ-002): With one hidden row among visible ones, the default output has no runtime-argument row and one count line; a missing-tool `Not available` row and a `Fail` row are still printed (tests); with none hidden, no count line appears (test).
- AC-3 (REQ-003): With `--verbose`, every row is printed, and the exit code and the selected gates equal those of a run without it (tests).
- AC-4 (REQ-004): A run with `--base <ref>` prints that ref in the header (test).
- AC-5 (REQ-005): `tools/run_validation_gates.py` is smaller than 23988 B, the new module is below the limit with no function of grade C or worse, and both `tools/check_module_size.py` scopes pass.
- AC-6 (REQ-006): The Phase 4 note and the runner rows describe the default and the flag; `tools/check_tool_descriptions_sync.py` and `tools/check_skills_references.py` pass.

## Tests
- `tests/tools/test_run_validation_gates.py`: reason classification of `run_gate`; renderer cases for hidden, visible, missing-tool, and `Fail` rows; the count line and its absence; `--verbose`; the header base; and unchanged exit codes (REQ-001 to REQ-004).
- `uv run python tools/run_validation_gates.py drift` and a smoke run on the real diff, with and without `--verbose` (REQ-003).
- Reference checkers for the two documentation edits (REQ-006).

## Documentation Impact
N/A for `docs/*.md`: no file under `docs/` changes. The Phase 4 note of the commit workflow and the tool description rows change (REQ-006).

## Assumptions
- Only the `runtime-argument` reason is hidden by default; `missing-tool` and `os-error` stay visible because they mean a check did not run.
- `--verbose` is the chosen flag name because it is the conventional name for showing everything and the runner has no flag of that name; an existing `--fast` is not a parser option (UNK-02).
- The routing mappings added by `plans/20261117-125207_wftool004_orphan-tool-routing.md` have no path patterns, so the runner never selects or prints them; the issue's statement that they add placeholder rows does not hold for that Plan's design, and this Plan has no dependency on them.
- Order against `plans/20261117-124139_wftool001_gate-workitem-structure.md` is free: it removes one placeholder row from the default output, and no test here pins the number of placeholder rows.
- Overlap with `plans/20261117-124139_wftool001_gate-workitem-structure.md`, `plans/20261117-124614_wftool002_status-vocabulary-unify.md`, `plans/20261117-124834_wftool003_new-marker-tools-merge.md`, `plans/20261117-125207_wftool004_orphan-tool-routing.md`, and `plans/20261117-125502_wftool005_workitem-batch-generate.md` on `tools/TOOL_DESCRIPTIONS.md` is compatible: this Plan edits the two runner rows and adds one module row; the others edit other rows.
- Overlap with `plans/20261117-124139_wftool001_gate-workitem-structure.md` on `tests/tools/test_run_validation_gates.py` is compatible: that Plan adds gate-selection and hook-parity tests, and this Plan adds classification and renderer tests.
- Overlap with `plans/20261117-125207_wftool004_orphan-tool-routing.md` on `tools/run_validation_gates.py` and `tests/tools/test_run_validation_gates.py` is a sequencing dependency on the import block (recorded in Scope); the remaining regions differ.

## Unknowns
| ID | Unknown Description | Evidence Missing | Resolution Path | Blocking? (True/False) |
|---|---|---|---|---|
| UNK-01 | Order against the open procedure `implementations/20261117-110514_04_tools_TOOL_DESCRIPTIONS.md.md` and the sibling tooling issues that edit `tools/TOOL_DESCRIPTIONS.md` | The procedure's target rows were not read | Read its target rows at implementation time; the edits are row-level, so land the earlier one first if rows coincide | False |
| UNK-02 | The runner's description rows state options and behavior the parser does not have: a `--fast` flag (the parser has `--base`, `--full`, and `--jobs`) and stopping non-zero on the first `Fail` (the runner runs every gate and exits `1` if any failed) | Whether the rows or the code reflect the intended behavior | File a follow-up issue; this Plan edits only the sentences about the default output and the new flag | False |

## Affected areas
`skills/DESIGN.md` Change-impact table, extended with `Churn (30d)` and `Bus Factor`
columns. The `File` column here MUST be a subset of `Implementation Target Files`'
rows — this table analyzes change-impact risk for those same files; it is not a
separate scope-of-record.

| File | Change | Blast Radius | Churn (30d) | Bus Factor | deploy.sh Impact |
|---|---|---|---|---|---|
| `tools/_validation_gate_report.py` | Create | Low: imported by the runner only | N/A: new file | N/A: new file | not applicable (rsynced) |
| `tools/run_validation_gates.py` | Modify | Medium: the commit skill, the drift hook, and the tests run it | 14 | High: single author | not applicable (rsynced) |
| `tests/tools/test_run_validation_gates.py` | Modify | Low | 10 | High: single author | not applicable (rsynced) |
| `skills/git-commit-and-sync/workflow.md` | Modify | Medium: read on every commit and sync | 6 | High: single author | not applicable (rsynced) |
| `tools/TOOL_DESCRIPTIONS.md` | Modify | Low: documentation rows read by the sync checker | 74 | High: single author | not applicable (rsynced) |

## Design
**Classification**: Path B (five target rows, one a new module). The four analyses ran once for this cycle.
- **Architecture**: the new module needs only result objects and the mode and base strings; it imports no tool module, and the runner imports it, so no cycle exists. Nothing under `scripts/` is involved, so the import-linter contracts are unaffected.
- **Dependency graphing**: the printed header and summary have no consumer in the repository (no script parses them), so changing the default output affects only a reader; `GateResult` is read by tests only through its `status` and `detail`.
- **Historical**: the runner is high-churn; the commit workflow changes moderately; every target has one author. The runner has four functions of grade C that this change does not touch.
- **Operational**: no port, database, dependency, or lock is involved; the persisted-schema check does not apply.
- **Decision 1, classification carrier**: a `reason` field on `GateResult`. Alternative: match the existing detail text, rejected because a reworded message would silently change what is hidden.
- **Decision 2, what to hide**: only `runtime-argument`. Alternative: hide every `Not available`, rejected because a missing local tool is a check that did not run (`rules/ai-execution.md` item 12).
- **Decision 3, flag name**: `--verbose`. Alternative: a dedicated `--show-unrunnable`, rejected as narrower than the need and unlike other tools' flags.
- **Decision 4, where the renderer lives**: a new module that the runner calls; the runner shrinks because the inline printer leaves it. `GateResult` stays in the runner so that its importers and the re-export test are untouched.
- **Decision 5, header**: pass the run's base into the renderer. The fixed `master` text is a defect in the code being moved, and tests that pin the header would otherwise pin the wrong text.
- **Baseline**: `vulture` and `bandit` findings under `scripts/` are pre-existing and outside the targets; `diff-cover` has no baseline because the tree equals `master`, and the 90% threshold applies at implementation.

## Implementation steps
Each step description MUST cite the exact file path(s) it touches by referencing rows
of `Implementation Target Files` above — do not restate file-level detail
independently of that frozen table. A step is a top-level numbered item (a Phase); its
checklist items are sub-tasks, and the Execution Status table has one row per step.

1. **Phase 1: Tests first**
   - [ ] Add tests for the reason classification, the renderer cases, `--verbose`, and the header base; they fail first (REQ-001 to REQ-004; `tests/tools/test_run_validation_gates.py`)
2. **Phase 2: Classification and renderer**
   - [ ] Add the `reason` field with a default and set it in `run_gate` (REQ-001; `tools/run_validation_gates.py`)
   - [ ] Create the renderer with the hide rule, the count line, the verbose form, and the real base (REQ-002, REQ-003, REQ-004, REQ-005; `tools/_validation_gate_report.py`)
3. **Phase 3: Wire the flag**
   - [ ] Add `--verbose`, call the renderer, and remove the inline printer (REQ-003, REQ-005; `tools/run_validation_gates.py`)
4. **Phase 4: Documentation**
   - [ ] Update the Phase 4 note (REQ-006; `skills/git-commit-and-sync/workflow.md`)
   - [ ] Update the two runner rows and add the module row (REQ-006; `tools/TOOL_DESCRIPTIONS.md`)
5. **Phase 5: Verification** (no deploy step: no `scripts/` or `config/` file changes)
   - [ ] Run the validation sequence of `rules/toolchain.md` for the changed tools, `run_validation_gates.py drift`, both size gates, the description and skills checkers, and smoke runs on a real diff with and without `--verbose` (REQ-001 to REQ-006; all target files)

### Release units
N/A: no release unit; each phase passes validation alone when applied in order.

## Validation plan
| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| `tools/_validation_gate_report.py` | Unit tests; complexity; security | `uv run pytest tests/tools/test_run_validation_gates.py -v`; `uv run radon cc tools/_validation_gate_report.py -s -n C`; `uv run bandit tools/_validation_gate_report.py` | Tests pass; radon reports nothing; bandit clean |
| `tools/run_validation_gates.py` | Drift, size, smoke | `uv run python tools/run_validation_gates.py drift`; `uv run python tools/check_module_size.py --scripts-dir tools --baseline tools/check_module_size_tools_baseline.txt`; `uv run python tools/run_validation_gates.py` and the same with `--verbose` | Drift reports parity; size gate passes; the default output hides runtime-argument rows and `--verbose` shows them |
| `tests/tools/test_run_validation_gates.py` | Self; lint and types | `uv run ruff format tools tests/tools`; `uv run ruff check tools tests/tools`; `uv run mypy --no-namespace-packages scripts/ tests/eventbus tools` | Clean |
| `skills/git-commit-and-sync/workflow.md` | Doc consistency | `uv run python tools/check_skills_references.py`; `uv run python tools/check_skills_heading_cycles.py` | No finding |
| `tools/TOOL_DESCRIPTIONS.md` | Doc consistency | `uv run python tools/check_tool_descriptions_sync.py` | No finding |

## Risks
- **Risk**: A missing-tool row is hidden by mistake → **Mitigation**: only the `runtime-argument` reason is hidden, and a test asserts that a missing-tool row stays visible.
- **Risk**: A reader loses sight of the hidden gates → **Mitigation**: the count line and the flag name are printed in the default output, and `--verbose` shows them.
- **Risk**: Both Plans that edit the runner's import block conflict → **Mitigation**: this Plan follows the other's phase 1, and plan-order tooling reports it as gated.
- **Risk**: Adding a field to `GateResult` breaks a constructor → **Mitigation**: the field has a default, and the existing tests run in Phase 5.
- **Risk**: The runner's rows have other drift that this edit leaves in place → **Mitigation**: recorded as UNK-02 with a follow-up issue as the resolution path.
- **Risk**: `tools/TOOL_DESCRIPTIONS.md` has very high churn → **Mitigation**: change two rows and add one; rebase through the commit skill and settle the order per UNK-01.

## Execution Status

Table structure, status/type vocabulary, and general guidance: see
`templates/execution-status.md`. Default rows for a freshly generated Plan (replace
with the Plan's actual steps once Implementation steps are broken down):

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Tests first: classification, renderer, flag, header | Pending | — | — | |
| 2 | Classification field and renderer module | Pending | — | — | |
| 3 | Wire the flag and remove the inline printer | Pending | — | — | |
| 4 | Documentation: Phase 4 note and tool rows | Pending | — | — | |
| 5 | Verification: validation sequence, drift, size gates, smoke runs | Pending | — | — | |

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
- **Source issue**: issues/20261117-123335_wftool006_gate-output-noise.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: this document is the generated plan
- **Source implementation procedure**: N/A: not applicable in this phase
- **Generated at**: 20261117-125737
- **Related target files**: `tools/_validation_gate_report.py`; `tools/run_validation_gates.py`; `tests/tools/test_run_validation_gates.py`; `skills/git-commit-and-sync/workflow.md`; `tools/TOOL_DESCRIPTIONS.md`

### Requirement Traceability
| Requirement ID | Source Issue section or evidence | Target file | Implementation step | Acceptance criterion | Test or validation item | Status |
|---|---|---|---|---|---|---|
| REQ-001 | Required Changes (classify `Not available` rows in the result model) | `tools/run_validation_gates.py` | Phase 2 | AC-1 | reason classification tests | Explicit in issue |
| REQ-001 | Required Changes (classify rows) | `tests/tools/test_run_validation_gates.py` | Phase 1 | AC-1 | reason classification tests | Explicit in issue |
| REQ-002 | Required Changes (hide runtime-argument rows, print a count) | `tools/_validation_gate_report.py` | Phase 2 | AC-2 | renderer tests | Explicit in issue |
| REQ-002 | Acceptance Criteria (default output has no runtime-argument rows) | `tests/tools/test_run_validation_gates.py` | Phase 1 | AC-2 | renderer tests | Explicit in issue |
| REQ-003 | Required Changes (a flag that shows them) | `tools/run_validation_gates.py` | Phase 3 | AC-3 | `--verbose` tests; smoke run | Explicit in issue |
| REQ-003 | Acceptance Criteria (the flag prints them) | `tests/tools/test_run_validation_gates.py` | Phase 1 | AC-3 | `--verbose` tests | Explicit in issue |
| REQ-004 | Header printed `base: master` for a `--base ORIG_HEAD` run, found in Step 3 | `tools/_validation_gate_report.py` | Phase 2 | AC-4 | header test | Confirmed by repository evidence |
| REQ-004 | Header defect found in Step 3 | `tests/tools/test_run_validation_gates.py` | Phase 1 | AC-4 | header test | Confirmed by repository evidence |
| REQ-005 | Implementation Intent (new module for the output logic); Constraints (size gate) | `tools/_validation_gate_report.py` | Phase 5 | AC-5 | `radon cc -n C`; size gate | Explicit in issue |
| REQ-005 | Constraints (size gate; the runner is near the limit) | `tools/run_validation_gates.py` | Phase 5 | AC-5 | `tools/check_module_size.py` (tools scope) | Confirmed by repository evidence |
| REQ-006 | Required Changes (update the Phase 4 note and the tool description) | `skills/git-commit-and-sync/workflow.md` | Phase 4 | AC-6 | `tools/check_skills_references.py` | Explicit in issue |
| REQ-006 | Required Changes (update the tool description) | `tools/TOOL_DESCRIPTIONS.md` | Phase 4 | AC-6 | `tools/check_tool_descriptions_sync.py` | Explicit in issue |
