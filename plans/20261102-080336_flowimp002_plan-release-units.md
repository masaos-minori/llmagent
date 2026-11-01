## Goal
- Let a Plan declare which phases must land together (a release unit), and give `code-implementation` a bounded batch mode for such a unit: cycles run in order, the full test suite and coverage gate run once at the end of the unit, and all members are archived together after it passes, while ordinary Plans keep the per-cycle gate.

## Priority
High

## Scope
- **In-Scope**:
  - A release-unit declaration in `templates/plan.md` (unit name, member phases, and the stated reason the members cannot be validated alone), written in the `Implementation steps` section without adding a `##` heading.
  - Carrying the unit name into each generated procedure document (`templates/implementation-procedure.md`, `skills/plan-to-implementation-procedure/workflow.md`).
  - Batch mode in `skills/code-implementation/workflow.md` with an explicit, referenced exception to the "exactly once per cycle" full-suite rule and to per-file archival, the allowed red states, and end-of-unit validation and archival.
  - Format validation of the declaration in `tools/check_workitem_structure.py`.
  - Unit grouping in `manage_workitem_stage.py list` and `show`.
  - A line in `skills/issue-to-plan/workflow.md` where phases are written, telling the author to declare a unit for coupled phases.
- **Out-of-Scope**:
  - Removing the per-cycle gate for ordinary Plans.
  - Changing what the full suite is, the coverage threshold, the Attempt Limit, or rollback limits.
  - Dependency ordering between Plans (`plans/20261102-080134_flowimp003_plan-dependency-gate.md`) and consumer discovery (`plans/20261102-080004_flowimp001_consumer-impact-scan.md`).
- **Dependencies**: Sequencing only, in either order, with `plans/20261102-080134_flowimp003_plan-dependency-gate.md`: both change `templates/plan.md`, `skills/plan-to-implementation-procedure/workflow.md`, `skills/code-implementation/workflow.md`, `tools/manage_workitem_stage.py`, and `tests/tools/test_manage_workitem_stage.py`; the `list` subcommand is edited by both (that Plan adds an order view, this Plan adds unit grouping), so whichever lands second rebases. Overlap judgments are in Assumptions A5 to A7.

## Background
- `Operationally observed` (2026-10-30, from the Issue): in `wfrecovery001`, the schema phase added `attempts.attempt_number NOT NULL` with a unique index, which breaks every existing attempt insert, so neither the schema phase nor the write-path phase could pass the suite alone. The work was finished only after the executor proposed, and the user approved, a single batch with one full-suite run at the end. `wftaskapi001` states the same coupling in prose only (Phase 3 title, "one release unit", checked in Step 2).
- `Explicit in code` (checked in Step 3): `skills/code-implementation/workflow.md` Step 4 says "Run the repository-defined full test suite exactly once per cycle" and already carries two stated exceptions (a failing-run re-run under the Attempt Limit, and a conflict-detected earlier file). Step 3c stops on a cross-file conflict. Multi-file processing applies `rules/ai-execution.md` Sequential Target Processing (Base), which completes each file's cycle and gates before the next target. There is no provision for cycles that are red by design until a later cycle lands.
- `Explicit in code` (checked in Step 3): `templates/plan.md` has no release-unit field. `templates/implementation-procedure.md` has `## Scope` and no unit field.
- `Explicit in code` (checked in Step 3): `tools/check_metadata_field_policy.py` compares only top-level `## ` sections of workitems with the template's canonical sections, and `tools/check_workitem_structure.py` checks only the presence of `## ` headings. A declaration written as a `###` block or a field line adds no `##` section, so neither checker rejects it; format validation of the declaration is new logic in `check_workitem_structure.py`.
- `Explicit in code` (checked in Step 3): `tools/generate_workitem.py` writes each template's fenced skeleton verbatim, so a new declaration line in a template appears in every generated document.
- Scope of the lifecycle rules (checked in Step 3): `rules/workflow-lifecycle.md` states it applies to the document-generation workflows (issue-to-plan, plan-to-implementation-procedure), so its Validation Reporting and Archival Move sections do not bind `code-implementation`. The rule the batch mode overrides is `rules/ai-execution.md` Sequential Target Processing (Base), which `rules/ai-execution.md` Instruction Precedence allows a narrower layer to except only by an explicit statement that references it.
- `Operationally observed` (from the Issue): the session ran the full suite about eight times (427 to 493 seconds each); several runs existed only to satisfy the per-cycle rule.

## Problem
Plans describe phases as independent, while some phases can only be validated together. The executor must either break the per-cycle rule without a sanctioned procedure or split a coupled change into states that cannot be tested, and the Plan's phase status cannot express a group.

## Reason for Change
Persisted-schema changes couple the schema row to its write path, so the situation recurs with every such Plan. An explicit unit makes the exception reviewable, bounded, and cheaper than repeated full runs.

## Implementation Intent
Make the coupling a declared, checkable fact rather than an ad hoc decision. The Plan names the unit and states why its members cannot be green alone; procedure documents carry the unit name. Batch mode keeps every safeguard that matters: cycles still run in order, static validators and impact-selected tests still run per cycle, a failure not attributable to a later member still stops the cycle, the Attempt Limit and Failure Log still apply, and the full suite and coverage gate run once at the end. Archival and Plan status updates happen for the whole unit after it passes.

## Requirements
- `REQ-001`: `templates/plan.md` MUST define a release-unit declaration (unit name, member phases, stated reason the members cannot be validated alone) inside `Implementation steps`, without adding a `##` heading, and the Plan skill text MUST tell the author to declare a unit for coupled phases.
- `REQ-002`: Each generated procedure document MUST carry its unit name through `templates/implementation-procedure.md` and the `plan-to-implementation-procedure` workflow.
- `REQ-003`: `skills/code-implementation/workflow.md` MUST describe batch mode for a declared unit, MUST state the exception to the "exactly once per cycle" rule and to per-file archival explicitly with a reference to `rules/ai-execution.md` Sequential Target Processing (Base), MUST list the allowed red states, MUST keep static validators, impact-selected tests, the Attempt Limit, the Failure Log, and rollback (limited to files recorded for the unit), and MUST keep the per-cycle gate for Plans without a unit.
- `REQ-004`: `tools/check_workitem_structure.py` MUST validate the declaration format: a valid declaration passes, a malformed one (missing name, member phases, or reason) fails, and a Plan without a unit is unaffected.
- `REQ-005`: `tools/manage_workitem_stage.py list` and `show` MUST group procedures by unit and keep the existing output for procedures without a unit.

## Implementation Target Files
**Freeze status**: Frozen (validated in Step 8b, 2026-11-02; all rows `Verified`)

This table is the canonical, frozen source of implementation scope for this Plan. Once `Frozen`, `Implementation steps`, `Acceptance criteria`, and every downstream `plan-to-implementation-procedure` document MUST reference file paths only from this table — no other file may be treated as a modification target.

| File Path | Change Responsibility | Reason for Modification | Related Requirement / Acceptance Criterion | Repository Evidence | Related Tests | Validation Status |
|---|---|---|---|---|---|---|
| `templates/plan.md` | Release-unit declaration in `Implementation steps` | The template has no unit field; phases are listed as independent | REQ-001 / AC-1 | "Implementation steps" block of the template (checked in Step 3) | `check_workitem_structure.py` on a fixture Plan | Verified |
| `templates/implementation-procedure.md` | Unit name line in `## Scope` | The template has no unit field | REQ-002 / AC-1 | `## Scope` heading of the template (checked in Step 3) | `check_workitem_structure.py` on a fixture procedure | Verified |
| `skills/issue-to-plan/workflow.md` | Tell the author to declare a unit where phases are written | Step 5 writes phases with no unit rule | REQ-001 / AC-1 | "Implementation steps MUST be small enough to be independently revertable" in Step 5 (checked in Step 3) | `check_skills_references.py`, `check_skills_heading_cycles.py` | Verified |
| `skills/plan-to-implementation-procedure/workflow.md` | Copy the unit name into each procedure | The generation steps carry no unit | REQ-002 / AC-1 | Step 3c and Step 4 text on generated documents (checked in Step 3) | `check_skills_references.py`, `check_skills_heading_cycles.py` | Verified |
| `skills/code-implementation/workflow.md` | Batch mode and its explicit exceptions | Step 4 and Multi-file processing allow only the per-cycle gate | REQ-003 / AC-2 | Step 4 "exactly once per cycle"; Multi-file processing; Step 7 (checked in Step 3) | `check_skills_references.py`, `check_skills_heading_cycles.py` | Verified |
| `tools/check_workitem_structure.py` | Validate the declaration format | The checker validates headings only | REQ-004 / AC-3 | `find_missing_sections`, `collect_single_file_findings` (checked in Step 3) | `tests/tools/test_check_workitem_structure.py` | Verified |
| `tests/tools/test_check_workitem_structure.py` | Tests for valid, malformed, and absent declarations | Existing tests cover headings only | REQ-004 / AC-3 | existing test module (checked in Step 3) | itself | Verified |
| `tools/manage_workitem_stage.py` | Unit grouping in `list` and `show` | `list` and `show` print workitems ungrouped | REQ-005 / AC-4 | `list_parser`, `show_parser`, `parse_execution_status_table` (checked in Step 3) | `tests/tools/test_manage_workitem_stage.py` | Verified |
| `tests/tools/test_manage_workitem_stage.py` | Tests for grouped display and the no-unit case | Existing tests cover ungrouped output | REQ-005 / AC-4 | existing `list` and `show` tests (checked in Step 3) | itself | Verified |

## Reference Files
| File Path | Why It Must Be Read | Related Target File or Requirement |
|---|---|---|
| `rules/ai-execution.md` | Sequential Target Processing (Base) and Instruction Precedence that the exception must reference | REQ-003 |
| `rules/workflow-lifecycle.md` | Confirms its scope excludes `code-implementation`; Attempt Limit framing | REQ-003 |
| `rules/toolchain.md` | Completion checklist and diff-cover rule the unit's single end gate must still satisfy | REQ-003 |
| `skills/code-implementation/SKILL.md` | Core rules the batch mode must not weaken | REQ-003 |
| `tools/check_metadata_field_policy.py` | Confirms a `###` block or field line adds no new `##` section | REQ-001, REQ-002 |
| `tools/generate_workitem.py` | Writes the template skeleton verbatim, so the new lines reach generated documents | REQ-001, REQ-002 |
| `plans/done/20261030-114041_wfrecovery001_workflow-recovery-state-machine.md` | Archived Plan used for the walk-through on a copy | REQ-003 |
| `plans/done/20261030-113553_wftaskapi001_consolidate-task-persistence.md` | Prose-only unit statement to express as a declaration | REQ-001 |

## Acceptance Criteria
- AC-1 (`REQ-001`, `REQ-002`): `templates/plan.md` and `templates/implementation-procedure.md` carry the declaration and the unit line, and a fixture Plan and procedure using them pass `check_workitem_structure.py`.
- AC-2 (`REQ-003`): `skills/code-implementation/workflow.md` describes batch mode, names `rules/ai-execution.md` Sequential Target Processing (Base) and Step 4's "exactly once per cycle" as the rules it excepts, lists allowed red states, and keeps the per-cycle gate for Plans without a unit.
- AC-3 (`REQ-004`): A fixture Plan with a valid declaration passes; one missing a name, member phases, or reason fails; a Plan without a unit passes unchanged.
- AC-4 (`REQ-005`): `manage_workitem_stage.py list` groups procedures by unit; `show` prints the unit; procedures without a unit print as before.
- AC-5 (`REQ-003`): A walk-through on a copy of the archived `wfrecovery001` Plan with the declaration added shows the described batch mode reproduces the run that was done by hand (recorded in the implementing change).
- AC-6 (`REQ-001` to `REQ-005`): `check_skills_references.py` and `check_skills_heading_cycles.py` pass.

## Tests
- `REQ-004`: unit tests for valid, malformed (each missing field), and absent declarations.
- `REQ-005`: unit tests for grouped `list` and `show`, including procedures without a unit.
- `REQ-003`: a documented walk-through on a copy of the archived `wfrecovery001` Plan (no code test).
- `REQ-001`, `REQ-002`: structure checks on fixture documents; skill checkers for the changed `skills/*.md` files.

## Documentation Impact
- Yes. The templates and skills state the declaration, batch mode, and safeguards (intent, boundaries, failure behavior) (REQ-001 to REQ-003). No `docs/*.md` change: workflow rules, not system design.

## Assumptions
- A1: One unit per set of phases is enough; nested or overlapping units are not needed (from the Issue). Falsifiable by a Plan needing overlapping units.
- A2: Decision (Unresolved Question): the Plan's phase status stays per-phase with a unit marker in the declaration; Execution Status rows are not regrouped, because `tools/manage_workitem_stage.py` and `code-implementation` Step 7 map Plan steps to procedures by row. Falsifiable by the owner preferring per-unit status.
- A3: Decision (Unresolved Question): whether a failure is "attributable to a later member" is the executor's judgment in the first version, recorded in the Failure Log with the reason; no mechanical test is added. Falsifiable by a repeated misjudgment.
- A4: The members of a unit run in the order the existing Dependency order rule of `code-implementation` Multi-file processing gives (`seq`); after the order view of `plans/20261102-080134_flowimp003_plan-dependency-gate.md` lands, that view is the order source. Falsifiable by `seq` order differing from the declared member phases.
- A5: Overlap judgment (Step 8b): `templates/plan.md` is also a target of `plans/20261102-080004_flowimp001_consumer-impact-scan.md` and `plans/20261102-080134_flowimp003_plan-dependency-gate.md`. Judged compatible: this Plan edits the `Implementation steps` block, the others edit a notes section and the `Scope` block.
- A6: Overlap judgment (Step 8b): `skills/issue-to-plan/workflow.md` is also a target of `plans/20261102-080004_flowimp001_consumer-impact-scan.md`. Judged compatible: that Plan adds a step in Step 3; this Plan adds a line in Step 5.
- A7: Overlap judgment (Step 8b): `skills/plan-to-implementation-procedure/workflow.md`, `skills/code-implementation/workflow.md`, `tools/manage_workitem_stage.py`, and `tests/tools/test_manage_workitem_stage.py` are also targets of `plans/20261102-080134_flowimp003_plan-dependency-gate.md`. Judged a sequencing dependency, not a conflict: the skill edits touch different steps (Step 1 and Step 2 versus Step 4, Step 7, and Multi-file processing), and both Plans edit the `list` subcommand, so whichever lands second rebases onto the other.
- A8: `git-fame` is not used; Bus Factor is `N/A` (single-owner repository).

## Unknowns
| ID | Unknown Description | Evidence Missing | Resolution Path | Blocking? (True/False) |
|---|---|---|---|---|
| UNK-01 | Whether batch mode needs a mechanical check that a failing test belongs to a later member | No data on how often the judgment is wrong | Start with executor judgment in the Failure Log (A3); revisit after the first unit | False |
| UNK-02 | Whether the unit grouping needs a unit key beyond the name when two Plans use the same unit name | Not designed in the Issue | Group by Plan path plus unit name; confirm in the order-view tests | False |

## Affected areas
| File | Change | Blast Radius | Churn (30d) | Bus Factor | deploy.sh Impact |
|---|---|---|---|---|---|
| `templates/plan.md` | Modify | Medium (every Plan follows it; the generator copies it) | 5 | N/A | not applicable (rsynced) |
| `templates/implementation-procedure.md` | Modify | Medium (every procedure follows it) | 4 | N/A | not applicable (rsynced) |
| `skills/issue-to-plan/workflow.md` | Modify | Medium | 12 | N/A | not applicable (rsynced) |
| `skills/plan-to-implementation-procedure/workflow.md` | Modify | Medium | 8 | N/A | not applicable (rsynced) |
| `skills/code-implementation/workflow.md` | Modify | High (executes every procedure; carries the gate rules) | 13 | N/A | not applicable (rsynced) |
| `tools/check_workitem_structure.py` | Modify | Low (pre-commit hook and gate) | 1 | N/A | not applicable (rsynced) |
| `tests/tools/test_check_workitem_structure.py` | Modify | Low | 1 | N/A | not applicable (rsynced) |
| `tools/manage_workitem_stage.py` | Modify | Medium (status updates and archival moves use it) | 4 | N/A | not applicable (rsynced) |
| `tests/tools/test_manage_workitem_stage.py` | Modify | Low | 4 | N/A | not applicable (rsynced) |

## Design
- Declaration: a `### Release units` block inside `## Implementation steps`, one entry per unit: `**Unit**: {name} | **Phases**: {N, N} | **Reason**: {why the members cannot be validated alone}`; the default text is `N/A: no release unit`. No `##` heading is added, so `check_workitem_structure.py`'s heading check and `check_metadata_field_policy.py` are unaffected. The Plan skill text says to declare a unit when a phase breaks existing callers or tests until another lands (the schema `NOT NULL` case).
- Carry-over: each procedure's `## Scope` has a `**Release unit**` line with the unit name or `N/A: not part of a release unit`; the generation workflow copies it from the Plan.
- Batch mode (in `code-implementation`): applies only to procedures that carry a unit name. Members run in order. Per member: Steps 1 to 3 as usual; Step 3e static validators and the impact-selected targeted tests of Step 4 still run and must pass except for failures the executor attributes to a later member and records in the Failure Log. The full suite and the diff-cover gate run once, after the last member. Step 7 archival and the Plan Execution Status update run for all members after that run passes. A failure not attributable to a later member stops the cycle; the Attempt Limit applies; rollback is limited to the files recorded in the members' Notes.
- Explicit exceptions: written in `skills/code-implementation/workflow.md` Step 4 and Multi-file processing, each naming the overridden rule (Step 4's "exactly once per cycle"; `rules/ai-execution.md` Sequential Target Processing (Base)), per `rules/ai-execution.md` Instruction Precedence. `rules/workflow-lifecycle.md` does not bind this workflow (its stated scope is the document-generation workflows), so no edit to the rules files is needed.
- Tools: `check_workitem_structure.py` gains a declaration check (name, phases, reason present; phases cite existing phase numbers); `manage_workitem_stage.py list` groups by unit and `show` prints the unit; absent declarations leave output unchanged.
- Alternatives rejected: per-unit Plan status (A2); a mechanical attribution test (A3).
- Compatibility: Plans and procedures without a declaration are unchanged; the per-cycle gate stays the default.

## Implementation steps
1. **Phase 1: Templates and authoring text**
   - [ ] Add the `### Release units` declaration (`REQ-001`; `templates/plan.md`)
   - [ ] Add the `Release unit` line to `## Scope` (`REQ-002`; `templates/implementation-procedure.md`)
   - [ ] Add the "declare a unit for coupled phases" line where phases are written (`REQ-001`; `skills/issue-to-plan/workflow.md`)
   - [ ] Add the copy-the-unit-name instruction (`REQ-002`; `skills/plan-to-implementation-procedure/workflow.md`)
2. **Phase 2: Declaration check**
   - [ ] Implement the declaration check (`REQ-004`; `tools/check_workitem_structure.py`)
   - [ ] Add tests for valid, malformed, and absent declarations (`REQ-004`; `tests/tools/test_check_workitem_structure.py`)
3. **Phase 3: Grouped display**
   - [ ] Add unit grouping to `list` and `show` (`REQ-005`; `tools/manage_workitem_stage.py`)
   - [ ] Add tests for grouping and the no-unit case (`REQ-005`; `tests/tools/test_manage_workitem_stage.py`)
4. **Phase 4: Batch mode**
   - [ ] Write batch mode, the explicit exceptions, the allowed red states, and the per-cycle default (`REQ-003`; `skills/code-implementation/workflow.md`)
5. **Phase 5: Verification** (no `scripts/` or `config/` change, so no deploy step is required)
   - [ ] Run the tool lint sequence on the two changed tools, the walk-through on a copy of the archived `wfrecovery001` Plan, and the checkers in the Validation plan (`REQ-001` to `REQ-005`; all rows)

## Validation plan
| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| `tools/check_workitem_structure.py` | Unit | `uv run pytest tests/tools/test_check_workitem_structure.py -v` | all pass |
| `tools/manage_workitem_stage.py` | Unit and regression | `uv run pytest tests/tools/test_manage_workitem_stage.py tests/tools/test_manage_workitem_stage_new.py -v` | all pass |
| `tools/check_workitem_structure.py`, `tools/manage_workitem_stage.py` | Lint, type, security | `uv run ruff format <file>`; `uv run ruff check <file>`; `uv run mypy <file>`; `uv run bandit <file>` per file | clean |
| `templates/*.md`, the three skills | Reference, heading, and structure checks | `uv run python tools/check_skills_references.py`; `uv run python tools/check_skills_heading_cycles.py`; `uv run python tools/check_workitem_structure.py --file <fixture>` | no findings |
| Archived `wfrecovery001` Plan copy | Walk-through (AC-5) | read the copy with the declaration added against the batch-mode text | batch mode reproduces the manual run |

## Risks
- **Risk**: Batch mode is used to hide a real regression behind "red by design". → **Mitigation**: a unit needs a stated, checked reason; static validators and impact-selected tests still run per member; only failures attributed to a later member are tolerated, each recorded in the Failure Log; the full suite and coverage gate run at the end.
- **Risk**: The exception conflicts with `rules/ai-execution.md` Sequential Target Processing (Base). → **Mitigation**: the exception is stated explicitly in the narrower workflow file with a reference to that rule, as `rules/ai-execution.md` Instruction Precedence requires; the per-cycle gate stays the default.
- **Risk**: A new line in the shared templates reaches every generated Plan and procedure (the generator copies the skeleton). → **Mitigation**: the default text is `N/A`; only structure checks read it; `tests/tools/test_generate_workitem.py` runs in verification.
- **Risk**: `skills/code-implementation/workflow.md` (churn 13 in 30 days) and `tools/manage_workitem_stage.py` are shared with `plans/20261102-080134_flowimp003_plan-dependency-gate.md`. → **Mitigation**: A7 records the sequencing dependency; edits target different steps; the later Plan rebases.
- **Risk**: Rollback of a failed unit reverts files from a member that already passed. → **Mitigation**: rollback is limited to files recorded in the members' Notes, and the Attempt Limit applies; no bulk command is introduced.

## Execution Status

Table structure, status/type vocabulary, and general guidance: see `templates/execution-status.md`.

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Templates and authoring text: `templates/plan.md`, `templates/implementation-procedure.md`, `skills/issue-to-plan/workflow.md`, `skills/plan-to-implementation-procedure/workflow.md` | Pending | — | — | |
| 2 | Declaration check: `tools/check_workitem_structure.py`, `tests/tools/test_check_workitem_structure.py` | Pending | — | — | |
| 3 | Grouped display: `tools/manage_workitem_stage.py`, `tests/tools/test_manage_workitem_stage.py` | Pending | — | — | |
| 4 | Batch mode: `skills/code-implementation/workflow.md` | Pending | — | — | |
| 5 | Verification: lint sequence, walk-through, checkers | Pending | — | — | |

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
- **Source issue**: issues/20261030-191057_flowimp002_plan-release-units.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: this document is the generated plan
- **Source implementation procedure**: N/A: not applicable in this phase
- **Generated at**: 20261102-080336
- **Related target files**: `templates/plan.md`, `templates/implementation-procedure.md`, `skills/issue-to-plan/workflow.md`, `skills/plan-to-implementation-procedure/workflow.md`, `skills/code-implementation/workflow.md`, `tools/check_workitem_structure.py`, `tests/tools/test_check_workitem_structure.py`, `tools/manage_workitem_stage.py`, `tests/tools/test_manage_workitem_stage.py` — the full list of `File Path` values from `Implementation Target Files` above, once `Frozen`

### Requirement Traceability
See `templates/requirement-traceability.md` for the canonical column format.

| Requirement ID | Source Issue section or evidence | Target file | Implementation step | Acceptance criterion | Test or validation item | Status |
|---|---|---|---|---|---|---|
| REQ-001 | Required Changes (declaration in the Plan template) | `templates/plan.md` | Phase 1 | AC-1 | `check_workitem_structure.py` on a fixture Plan | Explicit in issue |
| REQ-001 | Target Files (`issue-to-plan` where phases are written) | `skills/issue-to-plan/workflow.md` | Phase 1 | AC-1, AC-6 | reference and heading checkers | Explicit in issue |
| REQ-002 | Required Changes (carry the unit name into each procedure) | `templates/implementation-procedure.md` | Phase 1 | AC-1 | `check_workitem_structure.py` on a fixture procedure | Explicit in issue |
| REQ-002 | Target Files (`plan-to-implementation-procedure` copies the unit) | `skills/plan-to-implementation-procedure/workflow.md` | Phase 1 | AC-1, AC-6 | reference and heading checkers | Explicit in issue |
| REQ-003 | Required Changes (batch mode with explicit exception); Step 3 (rule scope) | `skills/code-implementation/workflow.md` | Phase 4 | AC-2, AC-5 | walk-through; reference and heading checkers | Confirmed by repository evidence |
| REQ-004 | Required Changes (validate the declaration format) | `tools/check_workitem_structure.py` | Phase 2 | AC-3 | declaration unit tests | Explicit in issue |
| REQ-004 | Testing Expectations (declaration checker tests) | `tests/tools/test_check_workitem_structure.py` | Phase 2 | AC-3 | declaration unit tests | Explicit in issue |
| REQ-005 | Required Changes (unit grouping in `list` and `show`) | `tools/manage_workitem_stage.py` | Phase 3 | AC-4 | grouped display tests | Explicit in issue |
| REQ-005 | Testing Expectations (grouped display tests, Plan without a unit) | `tests/tools/test_manage_workitem_stage.py` | Phase 3 | AC-4 | grouped display tests | Explicit in issue |
