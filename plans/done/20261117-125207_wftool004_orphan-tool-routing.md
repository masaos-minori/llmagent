## Goal
- Make the Plan path audit and the Plan row reconciliation discoverable at the step where each applies: run the audit in `issue-to-plan` Step 8b before the freeze, and list both tools in the `routing.md` table with their trigger, while keeping the gate-table size gate and the routing drift check passing.

## Priority
Low

## Scope
- **In-Scope**: (1) move the toolchain gate table and its bare-except rule out of the near-limit gate-definition module into a new module, unchanged; (2) add manual routing mappings for the audit and the reconciliation tool; (3) two `routing.md` rows; (4) Step 8b and the Toolchain paragraph of `skills/issue-to-plan/workflow.md`; (5) the tool description rows (correcting the audit entry, adding the new module); (6) tests for the move and the new mappings.
- **Out-of-Scope**: changing the behavior of either tool; making the audit a blocking gate; changing `skills/code-implementation/workflow.md` (it already names the reconciliation tool, see Design); changing which gates the runner selects.
- **Dependencies**: N/A: nothing must be done first. The Frozen Plans of the structure-gate, status-vocabulary, and new-marker issues (wftool001, wftool002, wftool003), the archived procedure `implementations/done/20261117-110514_04_tools_TOOL_DESCRIPTIONS.md.md` (all rows `Completed`; its edits are already in the tree), and the other tooling issues edit some of the same files; the edits are in different regions (see Assumptions), and the order is settled at implementation time (UNK-01). The gate-output-noise work (wftool006) edits the runner's output and follows this Plan's first phase; it does not depend on this Plan's mappings, because manual mappings are never selected and never print a row.

## Background
Filed from the investigation of the issue -> plan -> implementation toolchain. `tools/audit_plan_target_paths.py` is called only by `tools/amend_plan.py` after a Plan is frozen. `tools/sync_plan_workitem_status.py` is named once, in the `Superseded` branch of the `code-implementation` workflow, and not in `routing.md`. Every checker row of the `routing.md` table needs a gate mapping, which the drift check enforces.

## Problem
A Plan can be frozen without an automated check that its target paths exist, because Step 8b relies on a manual existence check and the audit runs only after a freeze (`Explicit in code`). An operator scanning `routing.md` does not find the Plan row reconciliation tool (`Explicit in code`). The `tools/TOOL_DESCRIPTIONS.md` entry for the audit says it also reports cross-plan overlaps and path references in plan bodies, which the tool does not do: it audits only the `Implementation Target Files` paths (`Explicit in code`).

## Reason for Change
The audit would catch the existence criterion of the Freeze check one step earlier, and the reconciliation tool is easy to miss when a procedure is archived outside the batch close. A routing row is not free: it needs a gate mapping, and `tools/_validation_gate_defs.py` has 50 bytes below the size limit while two mappings need about 600, so the change must free space first. Nothing makes it time-sensitive.

## Implementation Intent
Move only the toolchain table (and the one constant only it uses) into a new module with identical content, so the routing table, the first Plan's edited row, and the module's helpers stay where they are. The two new mappings are manual (no path patterns), so the runner never selects or prints them; they exist for the drift check and for `routing.md` readers. Step 8b gains one read-only command with a fallback; no behavior of either tool changes.

## Requirements
- `REQ-001`: `TOOLCHAIN_GATES` and `_BARE_EXCEPT_RULE` move unchanged (same gates, order, commands, and modes) into `tools/_validation_gate_toolchain.py`; `tools/_validation_gate_defs.py` keeps the `Gate` type, helpers, constants, and `ROUTING_GATES`; the orchestrator imports `TOOLCHAIN_GATES` from the new module; the identity test and the gate-location message point at the right modules.
- `REQ-002`: `ROUTING_GATES` gains one mapping for the audit and one for the reconciliation tool; each has a placeholder command, no patterns, and an id equal to the id derived from its `routing.md` row.
- `REQ-003`: `routing.md` has a row for each tool with its triggering situation, and `uv run python tools/run_validation_gates.py drift` passes.
- `REQ-004`: `skills/issue-to-plan/workflow.md` Step 8b runs `tools/audit_plan_target_paths.py` on the Plan before marking `Frozen`, states that a missing path must say create or new in its `Change Responsibility`, and names the fallback (the manual existence check); the Toolchain paragraph lists the tool.
- `REQ-005`: `tools/TOOL_DESCRIPTIONS.md` describes the audit as the tool behaves, states the routing trigger for both tools, adds a row for the new module, and updates the row of the definition module.
- `REQ-006`: Both gate modules and the orchestrator stay below the `tools/` size limit with the definition module at least 2 KB lower than today; the module-size gates pass.

## Implementation Target Files
**Freeze status**: Frozen

This table is the canonical, frozen source of implementation scope for this Plan. Once
`Frozen`, `Implementation steps`, `Acceptance criteria`, and every downstream
`plan-to-implementation-procedure` document MUST reference file paths only from this
table — no other file may be treated as a modification target.

| File Path | Change Responsibility | Reason for Modification | Related Requirement / Acceptance Criterion | Repository Evidence | Related Tests | Validation Status |
|---|---|---|---|---|---|---|
| `tools/_validation_gate_toolchain.py` | Create the module that holds the toolchain table | The definition module cannot hold two more mappings; the toolchain block and its rule are about 4.7 KB (measured 20261118: 3377 B table plus 1363 B rule) | REQ-001, REQ-006 / AC-1, AC-6 | New file; `tools/` exists; the toolchain block uses only `Gate`, `MODE_FULL`, `SOURCE_TOOLCHAIN`, and `_BARE_EXCEPT_RULE` (checked in Step 3) | `tests/tools/test_run_validation_gates.py` | Verified |
| `tools/_validation_gate_defs.py` | Remove the toolchain block; add the two manual mappings | Holds the toolchain table and is 24526 B of 24576 B (re-measured 20261118) | REQ-001, REQ-002, REQ-006 / AC-1, AC-2, AC-6 | `_BARE_EXCEPT_RULE` is defined here and used only inside the module; `TOOLCHAIN_GATES` is imported only by `tools/run_validation_gates.py`; `ROUTING_GATES` is the routing table (re-measured 20261118) | `tests/tools/test_run_validation_gates.py` | Verified |
| `tools/run_validation_gates.py` | Import the toolchain table from its new module | It imports `TOOLCHAIN_GATES` from the definition module | REQ-001, REQ-006 / AC-1, AC-6 | The first import block lists `TOOLCHAIN_GATES` among names of the definition module; 23696 B of 24576 B (re-measured 20261118) | `tests/tools/test_run_validation_gates.py` | Verified |
| `tests/tools/test_run_validation_gates.py` | Update the identity test and message; add mapping and parity tests | One test asserts that the orchestrator's `TOOLCHAIN_GATES` is the definition module's object, and a message names the definition module | REQ-001, REQ-002 / AC-1, AC-2 | `test_reexported_gate_definitions_are_the_same_objects` and the CI-lint-parity assertion message (checked in Step 3) | The file itself | Verified |
| `routing.md` | Add the two rows | Neither tool has a row | REQ-003 / AC-3 | The "When to run which tool" table has no row naming either tool (checked in Step 3) | `tools/check_skills_references.py`; `uv run python tools/run_validation_gates.py drift` | Verified |
| `skills/issue-to-plan/workflow.md` | Add the audit to Step 8b and the Toolchain paragraph | Step 8b freezes the table with a manual existence check and names no audit | REQ-004 / AC-4 | Step 8b and the Toolchain paragraph mention only `tools/check_plan_target_overlaps.py` (checked in Step 3) | `tools/check_skills_references.py`; `tools/check_skills_heading_cycles.py` | Verified |
| `tools/TOOL_DESCRIPTIONS.md` | Correct the audit entry; add the new module; update the definition module row | The audit entry claims overlap and body-path reporting that the tool lacks; the module rows are stale after the move | REQ-005 / AC-5 | The audit row says it reports cross-plan overlaps; the tool source audits target paths only; the definition module row names both tables (checked in Step 3) | `tools/check_tool_descriptions_sync.py` | Verified |

Revalidation (20261118, `plan-to-implementation-procedure` Step 2/3a): the cited sizes were re-measured and corrected — the definition module is 24526 B (50 B headroom, not 329 B), the runner is 23696 B (880 B headroom, not 588 B), and the toolchain block plus its rule measure about 4.7 KB (not about 3.9 KB). Row 2's evidence was corrected: `TOOLCHAIN_GATES` is imported by `tools/run_validation_gates.py`, so "used by no other module" was false. The UNK-01 procedure was found archived in `implementations/done/` with all rows `Completed`. All seven rows were re-checked against current source (audit and reconciliation tools' behavior, `routing.md` rows, Step 8b and Toolchain paragraphs, description rows, the identity test, and the gate-location message) and stay `Verified`; the section was re-frozen after this single correction cycle.

## Reference Files
Files that must be read to implement the targets above, but MUST NOT be modified. Same
one-file-per-row discipline as `Implementation Target Files` above — no directories,
glob patterns, components, file groups, or vague phrases.

| File Path | Why It Must Be Read | Related Target File or Requirement |
|---|---|---|
| `tools/audit_plan_target_paths.py` | Its read-only behavior, exit codes, and the `Change Responsibility` create hints that Step 8b must state | `skills/issue-to-plan/workflow.md` / REQ-004 |
| `tools/sync_plan_workitem_status.py` | Its trigger, `--dry-run`, and skip rule for the routing row | `routing.md` / REQ-003 |
| `skills/code-implementation/workflow.md` | It already names the reconciliation tool in the `Superseded` branch, so it needs no change | `routing.md` / REQ-003 |
| `tools/amend_plan.py` | The only caller of the audit today | `skills/issue-to-plan/workflow.md` / REQ-004 |
| `tools/check_module_size_tools_baseline.txt` | None of the touched modules is listed, so all must stay under the limit | `tools/_validation_gate_defs.py` / REQ-006 |

## Acceptance Criteria
- AC-1 (REQ-001): The moved table is identical: the ordered list of gate names, commands, modes, and patterns equals the one captured before the move (check recorded in Phase 1); `entry.TOOLCHAIN_GATES is toolchain_module.TOOLCHAIN_GATES` and the existing parity tests pass.
- AC-2 (REQ-002): Both new mappings exist with `patterns == ()`, `requires_context` true, and ids equal to the ids derived from their `routing.md` rows (tests); neither is selected for any changed path.
- AC-3 (REQ-003): `uv run python tools/run_validation_gates.py drift` passes with both rows present.
- AC-4 (REQ-004): Step 8b names the audit, the create-or-new rule, and the fallback; `tools/check_skills_references.py` and `tools/check_skills_heading_cycles.py` pass.
- AC-5 (REQ-005): `tools/check_tool_descriptions_sync.py` passes and the audit entry matches the tool.
- AC-6 (REQ-006): `uv run python tools/check_module_size.py --scripts-dir tools --baseline tools/check_module_size_tools_baseline.txt` passes, and the definition module is at least 2 KB smaller than 24526 B, its re-measured size on 20261118.

## Tests
- `tests/tools/test_run_validation_gates.py`: the updated identity test, the toolchain parity tests that already exist, and new tests for the two manual mappings (ids, patterns, `requires_context`, never selected) (REQ-001, REQ-002).
- Characterization: capture the toolchain table before the move and compare it after (REQ-001).
- Drift check and reference checkers for the documentation edits (REQ-003, REQ-004).

## Documentation Impact
N/A for `docs/*.md`: no file under `docs/` changes. `routing.md`, the issue-to-plan workflow, and the tool descriptions change (REQ-003 to REQ-005).

## Assumptions
- A routing row needs a mapping and the mapping must not auto-run the audit, because making it a blocking gate is out of scope; a manual mapping (no patterns) satisfies the drift check and is never selected or printed.
- Moving the toolchain table is behavior-neutral because the runner reads `_ALL_GATES` as `(*ROUTING_GATES, *TOOLCHAIN_GATES)` and the move keeps the contents and order.
- Overlap with `plans/20261117-124139_wftool001_gate-workitem-structure.md` is compatible: it edits the `check_workitem_structure` routing gate row, one `routing.md` row note, other tests, and other description rows; this Plan removes the toolchain block, adds mappings after the routing table, and adds other rows.
- Overlap with `plans/20261117-124614_wftool002_status-vocabulary-unify.md` and `plans/20261117-124834_wftool003_new-marker-tools-merge.md` is compatible: they edit other description rows and the convention paragraph; this Plan edits the audit row, the definition-module row, and one new row.
- `skills/code-implementation/workflow.md` needs no change: it names the reconciliation tool with its command at the point where a procedure is superseded.

## Unknowns
| ID | Unknown Description | Evidence Missing | Resolution Path | Blocking? (True/False) |
|---|---|---|---|---|
| UNK-01 | Order against the archived procedure `implementations/done/20261117-110514_04_tools_TOOL_DESCRIPTIONS.md.md` (found archived 20261118 with all rows `Completed`, so no pending edit from it), the sibling Plans, and the other tooling issues that edit the same files | The sibling Plans' procedure docs and their regions were not read | Read their target rows at implementation time; the edits are row-level and region-level, so land the earlier one first if regions coincide | False |

## Affected areas
`skills/DESIGN.md` Change-impact table, extended with `Churn (30d)` and `Bus Factor`
columns. The `File` column here MUST be a subset of `Implementation Target Files`'
rows — this table analyzes change-impact risk for those same files; it is not a
separate scope-of-record.

| File | Change | Blast Radius | Churn (30d) | Bus Factor | deploy.sh Impact |
|---|---|---|---|---|---|
| `tools/_validation_gate_toolchain.py` | Create | Low: imported by the orchestrator only | N/A: new file | N/A: new file | not applicable (rsynced) |
| `tools/_validation_gate_defs.py` | Modify | Medium: the orchestrator and its tests import it, and the move changes its contents | 5 | High: single author | not applicable (rsynced) |
| `tools/run_validation_gates.py` | Modify | Medium: the commit skill, the drift hook, and the tests run it; the change is one import | 14 | High: single author | not applicable (rsynced) |
| `tests/tools/test_run_validation_gates.py` | Modify | Low | 10 | High: single author | not applicable (rsynced) |
| `routing.md` | Modify | Low: two table rows; the drift check reads the Run cells | 20 | High: single author | not applicable (rsynced) |
| `skills/issue-to-plan/workflow.md` | Modify | Medium: read on every planning cycle | 10 | High: single author | not applicable (rsynced) |
| `tools/TOOL_DESCRIPTIONS.md` | Modify | Low: documentation read by the sync checker | 74 | High: single author | not applicable (rsynced) |

## Design
**Classification**: Path B (seven target rows, one of them a new module). The four analyses ran once for this cycle.
- **Architecture**: the new module imports `Gate`, `MODE_FULL`, and `SOURCE_TOOLCHAIN` from the definition module, and the orchestrator imports from both, so no import cycle exists (the definition module must not import the new one). Nothing under `scripts/` is involved, so the import-linter contracts are unaffected.
- **Dependency graphing**: the definition module is imported by `tools/run_validation_gates.py` and the test module (one test uses it directly); `rules/toolchain.md`, `routing.md`, and `prompts/08_document-sync.md` name the runner only as a command. The bare-except rule is used only by the toolchain block.
- **Historical**: `routing.md` and `skills/issue-to-plan/workflow.md` change often, so the edits are two rows and two sentences; every target has one author.
- **Operational**: no port, database, dependency, or lock is involved; the persisted-schema check does not apply.
- **Decision 1, how to make room**: the issue's constraint forbids growing the runner and the definition module has 50 B of headroom (re-measured 20261118), while two mappings need about 600 B. Alternatives: (a) skip the routing rows and name the tools only in workflow steps, which fails the issue's Required Changes; (b) put the mappings in the runner, which has 880 B of headroom (re-measured 20261118) and should not hold tables; (c) move the routing table out, which also relocates the row that `plans/20261117-124139_wftool001_gate-workitem-structure.md` edits and creates an ordering conflict. Chosen: move the toolchain table, which is independent of both Plans.
- **Decision 2, mapping kind**: manual (no patterns, placeholder arguments), because blocking on the audit is out of scope and a patternless mapping is never selected, so it adds no gate-output row.
- **Decision 3, Step 8b**: the audit runs before `Frozen`, read-only, and a not-yet-existing file must say create or new in its `Change Responsibility`, the column the tool reads. Fallback: the manual existence check that Step 8b already requires.
- **Decision 4, `code-implementation`**: no edit; the workflow already carries the trigger and command, and the routing row cites it.
- **Decision 5, description fix**: the audit entry is rewritten to match the tool because the current text claims overlap and body-path reporting that the source does not implement.
- **Baseline**: `radon` reports grade C functions in the runner and one in the definition module, all pre-existing and untouched; `vulture` and `bandit` findings under `scripts/` are pre-existing and outside the targets; `diff-cover` has no baseline because the tree equals `master`, and the 90% threshold applies at implementation.

## Implementation steps
Each step description MUST cite the exact file path(s) it touches by referencing rows
of `Implementation Target Files` above — do not restate file-level detail
independently of that frozen table. A step is a top-level numbered item (a Phase); its
checklist items are sub-tasks, and the Execution Status table has one row per step.

1. **Phase 1: Move the toolchain table**
   - [ ] Capture the ordered gate names, commands, modes, and patterns of both tables before any edit (REQ-001; `tools/_validation_gate_defs.py`)
   - [ ] Create the new module with the toolchain table and the bare-except rule, unchanged (REQ-001; `tools/_validation_gate_toolchain.py`)
   - [ ] Remove them from the definition module and update its docstring (REQ-001, REQ-006; `tools/_validation_gate_defs.py`)
   - [ ] Import `TOOLCHAIN_GATES` from the new module (REQ-001; `tools/run_validation_gates.py`)
   - [ ] Update the identity test and the gate-location message, then compare the captured tables with the live ones (REQ-001; `tests/tools/test_run_validation_gates.py`)
2. **Phase 2: Routing rows and manual mappings**
   - [ ] Add the two manual mappings after the last routing gate (REQ-002; `tools/_validation_gate_defs.py`)
   - [ ] Add the two `routing.md` rows with their triggers (REQ-003; `routing.md`)
   - [ ] Add tests for the ids, patterns, `requires_context`, and non-selection (REQ-002; `tests/tools/test_run_validation_gates.py`)
3. **Phase 3: Step 8b**
   - [ ] Add the audit, the create-or-new rule, and the fallback to Step 8b and the Toolchain paragraph (REQ-004; `skills/issue-to-plan/workflow.md`)
4. **Phase 4: Tool descriptions**
   - [ ] Correct the audit entry, add the trigger mentions, add the new module row, and update the definition module row (REQ-005; `tools/TOOL_DESCRIPTIONS.md`)
5. **Phase 5: Verification** (no deploy step: no `scripts/` or `config/` file changes)
   - [ ] Run the validation sequence of `rules/toolchain.md` for the changed tools, `run_validation_gates.py drift`, both size gates, the skills reference checkers, and `tools/check_tool_descriptions_sync.py` (REQ-001 to REQ-006; all target files)

### Release units
N/A: no release unit; each phase passes validation alone when applied in order.

## Validation plan
| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| `tools/_validation_gate_toolchain.py` and `tools/_validation_gate_defs.py` | Unit tests; before and after table comparison | `uv run pytest tests/tools/test_run_validation_gates.py -v`; a throwaway comparison of the captured and live tables | Tests pass; the tables are identical |
| `tools/run_validation_gates.py` | Drift and size | `uv run python tools/run_validation_gates.py drift`; `uv run python tools/check_module_size.py --scripts-dir tools --baseline tools/check_module_size_tools_baseline.txt` | Drift reports parity; size gate passes |
| `tests/tools/test_run_validation_gates.py` | Self; lint and types | `uv run ruff format tools tests/tools`; `uv run ruff check tools tests/tools`; `uv run mypy --no-namespace-packages scripts/ tests/eventbus tools`; `uv run bandit -r tools/_validation_gate_toolchain.py` | Clean |
| `routing.md` | Doc consistency | `uv run python tools/check_skills_references.py`; `uv run python tools/check_skills_heading_cycles.py` | No finding |
| `skills/issue-to-plan/workflow.md` | Doc consistency | `uv run python tools/check_skills_references.py`; `uv run python tools/check_skills_heading_cycles.py` | No finding |
| `tools/TOOL_DESCRIPTIONS.md` | Doc consistency | `uv run python tools/check_tool_descriptions_sync.py` | No finding |

## Risks
- **Risk**: The moved table differs from the original (a lost gate or a changed order) → **Mitigation**: capture the tables first and compare after the move; the existing parity tests also cover the toolchain commands.
- **Risk**: An import cycle between the two gate modules → **Mitigation**: the new module imports from the definition module only, and a test imports both in a fresh interpreter.
- **Risk**: A routing row without a mapping, or the reverse, fails the drift check and the pre-commit parity hook → **Mitigation**: both land in one phase, and a test compares the ids.
- **Risk**: The audit becomes a blocking gate by accident → **Mitigation**: the mapping has no patterns, and a test asserts that no changed path selects it.
- **Risk**: Step 8b grows a long procedure inside a high-churn workflow → **Mitigation**: one sentence with the trigger, the command, and the fallback.
- **Risk**: Several Plans and a procedure edit the same documentation and gate files → **Mitigation**: the regions are disjoint (see Assumptions); rebase through the commit skill and settle the order per UNK-01.

## Execution Status

Table structure, status/type vocabulary, and general guidance: see
`templates/execution-status.md`. Default rows for a freshly generated Plan (replace
with the Plan's actual steps once Implementation steps are broken down):

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Move the toolchain gate table into a new module | In Progress | — | — |  |
| 2 | Routing rows, manual mappings, and tests | In Progress | — | — |  |
| 3 | Step 8b audit in the issue-to-plan workflow | In Progress | — | — |  |
| 4 | Tool description rows | In Progress | — | — |  |
| 5 | Verification: validation sequence, drift, size gates, checkers | Pending | — | — |  |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| — | — | — | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| implementations/20261118-043152_01_tools__validation_gate_toolchain.py.md | 1 | Procedure | Pending | — | — |
| implementations/20261118-043152_02_tools__validation_gate_defs.py.md | 1, 2 | Procedure | Pending | — | — |
| implementations/20261118-043152_03_tools_run_validation_gates.py.md | 1 | Procedure | Pending | — | — |
| implementations/20261118-043152_04_tests_tools_test_run_validation_gates.py.md | 1, 2 | Procedure | Pending | — | — |
| implementations/20261118-043152_05_routing.md.md | 2 | Procedure | Pending | — | — |
| implementations/20261118-043152_06_skills_issue-to-plan_workflow.md.md | 3 | Procedure | Pending | — | — |
| implementations/20261118-043152_07_tools_TOOL_DESCRIPTIONS.md.md | 4 | Procedure | Pending | — | — |

## Traceability
- **Workflow phase**: issue-to-plan
- **Source issue**: issues/20261117-123333_wftool004_orphan-tool-routing.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: this document is the generated plan
- **Source implementation procedure**: N/A: not applicable in this phase
- **Generated at**: 20261117-125207
- **Related target files**: `tools/_validation_gate_toolchain.py`; `tools/_validation_gate_defs.py`; `tools/run_validation_gates.py`; `tests/tools/test_run_validation_gates.py`; `routing.md`; `skills/issue-to-plan/workflow.md`; `tools/TOOL_DESCRIPTIONS.md`

### Requirement Traceability
| Requirement ID | Source Issue section or evidence | Target file | Implementation step | Acceptance criterion | Test or validation item | Status |
|---|---|---|---|---|---|---|
| REQ-001 | Constraints (size gate; new logic in a new module); gate-module size measured in Step 3 | `tools/_validation_gate_toolchain.py` | Phase 1 | AC-1 | table comparison; parity tests | Derived from confirmed evidence |
| REQ-001 | Constraints (size gate) | `tools/_validation_gate_defs.py` | Phase 1 | AC-1 | table comparison | Derived from confirmed evidence |
| REQ-001 | Constraints (size gate) | `tools/run_validation_gates.py` | Phase 1 | AC-1 | drift check | Derived from confirmed evidence |
| REQ-001 | Constraints (size gate) | `tests/tools/test_run_validation_gates.py` | Phase 1 | AC-1 | identity test | Derived from confirmed evidence |
| REQ-002 | Required Changes (routing rows for both tools; drift passes) | `tools/_validation_gate_defs.py` | Phase 2 | AC-2 | mapping tests | Derived from confirmed evidence |
| REQ-002 | Required Changes (drift passes) | `tests/tools/test_run_validation_gates.py` | Phase 2 | AC-2 | mapping tests | Derived from confirmed evidence |
| REQ-003 | Required Changes (add routing rows) | `routing.md` | Phase 2 | AC-3 | `run_validation_gates.py drift` | Explicit in issue |
| REQ-004 | Required Changes (audit in Step 8b with a fallback) | `skills/issue-to-plan/workflow.md` | Phase 3 | AC-4 | `tools/check_skills_references.py` | Explicit in issue |
| REQ-005 | Target Files (`tools/TOOL_DESCRIPTIONS.md`); description mismatch found in Step 3 | `tools/TOOL_DESCRIPTIONS.md` | Phase 4 | AC-5 | `tools/check_tool_descriptions_sync.py` | Confirmed by repository evidence |
| REQ-006 | Constraints (module-size gate) | `tools/_validation_gate_defs.py` | Phase 5 | AC-6 | `tools/check_module_size.py` (tools scope) | Confirmed by repository evidence |
| REQ-006 | Constraints (module-size gate) | `tools/_validation_gate_toolchain.py` | Phase 5 | AC-6 | `tools/check_module_size.py` (tools scope) | Confirmed by repository evidence |

<!-- tools/generate_workitem.py implementation-procedure-pass timestamp: 20261118-043152 -->