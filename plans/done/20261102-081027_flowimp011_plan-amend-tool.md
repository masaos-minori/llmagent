## Goal
- Add a tool that appends a target file to a Frozen Plan consistently and re-runs the Plan checks, and propose in `rules/workflow-lifecycle.md` which amendments the executor may make and report afterwards and which need approval first, so a post-freeze amendment is cheap, uniform, and checkable.

## Priority
Medium

## Scope
- **In-Scope**:
  - A new tool, `tools/amend_plan.py`, with a dry run, an append-only guarantee for the target table, refusal when the file is already a target or reference file, a dated amendment line, and a run of the structure, path-audit, and overlap checks whose results it prints.
  - Proposed text in `rules/workflow-lifecycle.md` for the two approval classes (fallout the executor may make and report afterwards; scope or behavior changes that need approval first), marked as pending the owner's decision.
  - Updates to `skills/plan-to-implementation-procedure/workflow.md` (Step 3c additional target file discovery) and `skills/code-implementation/workflow.md` (a stop rule that calls the tool and follows the classes).
  - Registration in `tools/TOOL_DESCRIPTIONS.md`, `routing.md`, and the gate runner mapping.
- **Out-of-Scope**:
  - Preventing the discoveries (`plans/20261102-080004_flowimp001_consumer-impact-scan.md`).
  - Removing or reordering rows, or changing requirements through the tool.
  - Generating the new row's procedure document, and editing any real Plan outside tests.
- **Dependencies**: Sequencing only, in either order, with `plans/20261102-080336_flowimp002_plan-release-units.md`, `plans/20261102-080134_flowimp003_plan-dependency-gate.md`, and `plans/20261102-080828_flowimp009_test-row-grouping.md`: they share `skills/plan-to-implementation-procedure/workflow.md` and `skills/code-implementation/workflow.md`; whichever lands later rebases. Overlap judgments are in Assumptions A6 to A8. The policy itself is the owner's decision (Unknown UNK-01); the tool works under either answer.

## Background
- `Operationally observed` (2026-10-30, from the Issue): three Plans were amended six times after freeze (a path correction and a table-ownership inventory row for `dbmig001`; two rows each for `wftaskapi001` and `wfrecovery001`). Each amendment was a hand-written script that edited about seven places in the Plan; one replaced a path at the first occurrence in the file, which was in an unrelated table row, and the error was found by reading the diff. Four of the six amendments were approved by the user before being made; two were made and reported afterward. None changed the Plan's behavior or scope.
- `Explicit in code` (checked in Step 3): `rules/workflow-lifecycle.md` Implementation Target Files Validation (Revalidation) says that after an additional target file discovery the Plan must be amended (new row, evidence, requirement link) and re-validated and re-marked `Frozen`. `skills/plan-to-implementation-procedure/workflow.md` Step 3c adds that the new row is "appended after the last existing row — never inserted earlier, so no existing row's `seq` changes" and ends the cycle `Blocked: additional target file discovered` until then.
- Corrected in Step 2 (2026-11-02): the Issue says `skills/code-implementation/workflow.md` also ends the cycle `Blocked`. It has no explicit additional-target-file stop; it says only that it MUST NOT modify files outside the scope specified in the plan or procedure. The stop rule there is therefore new text.
- `Explicit in code` (checked in Step 3): no tool amends a Plan. `tools/check_workitem_structure.py` checks `## ` headings, `tools/audit_plan_target_paths.py` checks that target paths exist, and `tools/check_plan_target_overlaps.py` lists Frozen Plans sharing a target file.
- `Explicit in code` (checked in Step 3): a Plan places the information of one target file in several sections: the `Implementation Target Files` row, the `Freeze status` note, the `Related target files` line and the Requirement Traceability table in `Traceability`, an `Affected areas` row, the `Implementation steps` text, and (once a procedure exists) a `Work Items Created` row (`templates/plan.md`, `skills/issue-to-plan/workflow.md` Step 5 and Step 8a).

## Problem
An amendment touches many places by hand, with no check that it was applied consistently and no rule for which amendments need a decision. The result is slow, error-prone, and either asks a question each time or leaves the executor to guess whether one is needed.

## Reason for Change
Additional target discoveries are a known recurring event (`plans/20261102-080004_flowimp001_consumer-impact-scan.md` covers prevention). Until prevention is complete, the remedy should be cheap, uniform, and checkable.

## Implementation Intent
Separate the mechanics from the decision. The tool does the mechanics: given the Plan, the new file, its responsibility and reason, the linked requirement, the evidence, the related tests, the step, and the class the caller states, it appends the row after the last existing row and edits the other places, then runs the checks and prints their results. A dry run prints the edits first. The decision part is a proposed rule: an amendment that only adds a file needed to keep existing behavior, tests, inventories, or checkers working (fallout) may be made by the executor and reported afterward; an amendment that changes scope or behavior, adds a requirement, or removes a row needs approval before it is made. The policy is the owner's to confirm.

## Requirements
- `REQ-001`: `tools/amend_plan.py` MUST support a dry run that prints every intended edit and changes nothing; MUST append the new `Implementation Target Files` row after the last existing row and never insert before it; MUST refuse, with the reason, when the file is already a target row or a reference row; and MUST edit only the named Plan.
- `REQ-002`: The tool MUST apply the amendment consistently to the `Freeze status` note (dated line with the class and reason), the Requirement Traceability table, the `Related target files` line, the `Affected areas` table, the named step's text, and the `Work Items Created` table when the procedure path is given; each edit MUST be scoped to its own section so a similar path appearing earlier in the file is not touched.
- `REQ-003`: The tool MUST re-check the four Plan Freeze criteria for the new row (exists or declared new with an existing directory, a stated modification reason, evidence, a requirement link that exists in the Plan); MUST keep `Frozen` only when all four pass and otherwise set `Draft` and say so; and MUST run `check_workitem_structure.py`, `audit_plan_target_paths.py`, and `check_plan_target_overlaps.py` and print their results.
- `REQ-004`: `rules/workflow-lifecycle.md` MUST state the two approval classes and the report the executor owes for the first class as proposed text marked pending the owner's decision, without changing the Plan Freeze validation rules.
- `REQ-005`: `skills/plan-to-implementation-procedure/workflow.md` Step 3c MUST call the tool and follow the classes, and `skills/code-implementation/workflow.md` MUST add a stop rule for a file outside the procedure scope that calls the tool and follows the classes.
- `REQ-006`: The tool MUST be registered in `tools/TOOL_DESCRIPTIONS.md`, `routing.md`, and the gate runner mapping so the drift check passes.

## Implementation Target Files
**Freeze status**: Frozen (validated in Step 8b, 2026-11-02; all rows `Verified`)

This table is the canonical, frozen source of implementation scope for this Plan. Once `Frozen`, `Implementation steps`, `Acceptance criteria`, and every downstream `plan-to-implementation-procedure` document MUST reference file paths only from this table — no other file may be treated as a modification target.

| File Path | Change Responsibility | Reason for Modification | Related Requirement / Acceptance Criterion | Repository Evidence | Related Tests | Validation Status |
|---|---|---|---|---|---|---|
| `tools/amend_plan.py` | New file: the amendment tool | New file; no tool amends a Plan (`tools/` exists) | REQ-001, REQ-002, REQ-003 / AC-1, AC-2, AC-3, AC-4 | `TOOL_DESCRIPTIONS.md` lists no amendment tool; `check_workitem_structure.py` and `audit_plan_target_paths.py` are check-only (checked in Step 3) | `tests/tools/test_amend_plan.py` | Verified |
| `tests/tools/test_amend_plan.py` | New file: unit tests over fixture Plans | New file for the new tool (`tests/tools/` exists) | REQ-001, REQ-002, REQ-003 / AC-1 to AC-4 | one test module per tool in `tests/tools/` (checked in Step 3) | itself | Verified |
| `rules/workflow-lifecycle.md` | Proposed approval classes and the report owed | The rules state the amendment requirement but no approval classes | REQ-004 / AC-5 | "Implementation Target Files Validation (Plan Freeze)", Revalidation paragraph on additional target file discovery (checked in Step 3) | `check_skills_references.py`, `check_skills_heading_cycles.py` | Verified |
| `skills/plan-to-implementation-procedure/workflow.md` | Step 3c calls the tool and follows the classes | Step 3c describes the amendment as a manual edit | REQ-005 / AC-6 | "additional target file discovery" text in Step 3c (checked in Step 3) | `check_skills_references.py`, `check_skills_heading_cycles.py` | Verified |
| `skills/code-implementation/workflow.md` | Add the out-of-scope file stop rule | The workflow has only the scope statement and no explicit stop for a file outside the procedure | REQ-005 / AC-6 | scope rules ("MUST NOT modify files outside the scope specified in the plan/procedure") (checked in Step 3) | `check_skills_references.py`, `check_skills_heading_cycles.py` | Verified |
| `tools/TOOL_DESCRIPTIONS.md` | Register the tool | Every `tools/*.py` needs a row | REQ-006 / AC-7 | `check_tool_descriptions_sync.py` hook (checked in Step 3) | `tools/check_tool_descriptions_sync.py` | Verified |
| `routing.md` | Row in "When to run which tool" | The tool has no routing entry | REQ-006 / AC-7 | table "When to run which tool" (checked in Step 3) | `tools/run_validation_gates.py drift` | Verified |
| `tools/run_validation_gates.py` | Gate mapping entry for the new routing row | `drift_report()` fails for a routing checker without a mapping | REQ-006 / AC-7 | `drift_report`, `ROUTING_GATES` (checked in Step 3) | `tests/tools/test_run_validation_gates.py` | Verified |

## Reference Files
| File Path | Why It Must Be Read | Related Target File or Requirement |
|---|---|---|
| `templates/plan.md` | Section shapes the tool edits: target table, `Freeze status`, `Affected areas`, `Traceability` | REQ-001, REQ-002 |
| `templates/requirement-traceability.md` | Row format the tool appends | REQ-002 |
| `tools/check_workitem_structure.py` | Check the tool runs and prints | REQ-003 |
| `tools/audit_plan_target_paths.py` | Check the tool runs and prints | REQ-003 |
| `tools/check_plan_target_overlaps.py` | Check the tool runs and prints | REQ-003 |
| `plans/done/20261030-114041_wfrecovery001_workflow-recovery-state-machine.md` | Archived amended Plan used as a before and after reference | REQ-002 |
| `plans/done/20261030-113553_wftaskapi001_consolidate-task-persistence.md` | Archived amended Plan used as a before and after reference | REQ-002 |
| `plans/done/20261029-214108_dbmig001_forward-only-db-migrations.md` | Archived amended Plan used as a before and after reference | REQ-002 |
| `skills/plan-to-implementation-procedure/SKILL.md` | Core rules the Step 3c change must stay consistent with | REQ-005 |

## Acceptance Criteria
- AC-1 (`REQ-001`): On a fixture Plan, a dry run prints all intended edits and changes nothing; a real run applies them and prints the three checks' results.
- AC-2 (`REQ-001`): A file that is already a target row, or a reference row, is refused with the reason and the Plan is unchanged.
- AC-3 (`REQ-002`): A fixture Plan with a similar path appearing earlier in the file is edited in the intended section only, and the new row is appended after the last existing row.
- AC-4 (`REQ-003`): A row that fails one of the four criteria leaves the Plan `Draft` and the tool says which criterion failed; a row that passes keeps `Frozen`.
- AC-5 (`REQ-004`): `rules/workflow-lifecycle.md` states the two approval classes and the report owed for the first class, marked pending the owner's decision, and the Plan Freeze validation text is unchanged.
- AC-6 (`REQ-005`): The two skills call the tool and follow the classes, and `check_skills_references.py` and `check_skills_heading_cycles.py` pass.
- AC-7 (`REQ-006`): `check_tool_descriptions_sync.py` and `tools/run_validation_gates.py drift` pass with the tool registered.
- AC-8 (`REQ-002`): A dry run against copies of the three amended Plans, reconstructed from their before state in git history, is compared with the hand-made result and recorded in the implementing change.

## Tests
- `REQ-001`: unit tests for the dry run, the append-only rule, and each refusal.
- `REQ-002`: unit tests for each edit location and the repeated-path case.
- `REQ-003`: unit tests for each of the four criteria failing and for all passing, and for the check results being printed.
- `REQ-004`, `REQ-005`: skill and rules checkers named in `routing.md` for the changed files.
- `REQ-002`: the dry-run comparison against the three reconstructed Plans.

## Documentation Impact
- Yes. `rules/workflow-lifecycle.md` and the two skills state the amendment procedure and the proposed approval classes (REQ-004, REQ-005); `tools/TOOL_DESCRIPTIONS.md` and `routing.md` list the tool (REQ-006). No `docs/*.md` change: workflow rules and tooling.

## Assumptions
- A1: The six amendments of 2026-10-30 are representative of the common case (from the Issue). Falsifiable by an amendment that touches a section the tool does not edit.
- A2: Decision (Unresolved Question): the amendment log is the dated line in the `Freeze status` note, not a new Plan section, because a new `##` section would change `templates/plan.md`, `tools/check_workitem_structure.py`, and `tools/check_metadata_field_policy.py`. Falsifiable by the owner preferring a dedicated section.
- A3: Decision: the tool also adds an `Affected areas` row (`skills/issue-to-plan/workflow.md` Step 5 requires one per target row) with caller-given or default columns, although the Issue's list of edited places does not name it. Falsifiable by a Plan whose `Affected areas` table is not one row per target.
- A4: Decision: the `Work Items Created` row is added only when the caller gives the new procedure's path, because the procedure does not exist at amendment time; otherwise the tool reports it as skipped.
- A5: The class (fallout or scope change) is stated by the caller and recorded; the tool does not decide it, so it works under either owner answer (from the Issue). The rule text is written as proposed and marked pending the owner's decision.
- A6: Overlap judgment (Step 8b): `skills/plan-to-implementation-procedure/workflow.md` and `skills/code-implementation/workflow.md` are also targets of Plans 002, 003, 007, 008, and 009. Judged compatible: this Plan edits Step 3c's additional-discovery paragraph and adds a stop rule in the scope rules; the others edit different steps.
- A7: Overlap judgment (Step 8b): `routing.md`, `tools/TOOL_DESCRIPTIONS.md`, and `tools/run_validation_gates.py` are also targets of the Plans filed from `flowimp001`, `flowimp003`, `flowimp004`, and `flowimp005`. Judged compatible: each adds its own row or mapping entry.
- A7a: Overlap re-check (plan-to-implementation-procedure Step 2, 2026-11-02, `check_plan_target_overlaps.py`): `routing.md`, `tools/TOOL_DESCRIPTIONS.md`, and `tools/run_validation_gates.py` are also targets of `plans/20261102-081312_flowimp010_artifact-commit-split.md`, and `tools/TOOL_DESCRIPTIONS.md` of `plans/20261102-080631_flowimp008_workitem-bulk-close.md`. Judged compatible: each adds its own row or mapping entry; whichever lands later rebases. A7 did not name these two Plans.
- A10: Step 3a correction: `tools/audit_plan_target_paths.py` decides whether a missing target path is a creation from the second table cell (`Change Responsibility`), not the third (`Reason for Modification`), so the tool MUST write `New file:` into the new row's `Change Responsibility` cell when the path does not exist, or the path audit it runs reports the row as missing. The same audit exits 1 on any finding and takes plan paths as arguments.
- A11: Step 3a correction: `tools/check_plan_target_overlaps.py` reads the Freeze status as the first non-space token after `**Freeze status**:` (`_FREEZE_STATUS_RE`), so the tool MUST change only that first token (`Frozen` to `Draft`) and keep the dated amendment text on separate lines after the existing note, never before the token. It takes no plan argument and prints repository-wide findings, so the tool filters its printed overlap lines to those naming the amended Plan.
- A8: Overlap judgment (Step 8b): no other Frozen Plan targets `rules/workflow-lifecycle.md`.
- A9: `git-fame` is not used; Bus Factor is `N/A` (single-owner repository).

## Unknowns
| ID | Unknown Description | Evidence Missing | Resolution Path | Blocking? (True/False) |
|---|---|---|---|---|
| UNK-01 | Whether the owner accepts executor-made "fallout" amendments with an after-the-fact report | No owner statement | The rule text is written as proposed and marked pending; the tool does not depend on the answer (A5) | False |
| UNK-02 | Whether the before-state of the three amended Plans can be reconstructed from git history | Not attempted | Try `git log` on the archived Plans at implementation; if a before-state cannot be recovered, record the limit and use synthetic fixtures for AC-8 | False |

## Affected areas
| File | Change | Blast Radius | Churn (30d) | Bus Factor | deploy.sh Impact |
|---|---|---|---|---|---|
| `tools/amend_plan.py` | Create | Low (new; edits only a named Plan on request) | 0 | N/A | not applicable (rsynced) |
| `tests/tools/test_amend_plan.py` | Create | Low | 0 | N/A | not applicable (rsynced) |
| `rules/workflow-lifecycle.md` | Modify | Medium (shared by two workflows) | 3 | N/A | not applicable (rsynced) |
| `skills/plan-to-implementation-procedure/workflow.md` | Modify | Medium | 8 | N/A | not applicable (rsynced) |
| `skills/code-implementation/workflow.md` | Modify | High (executes every procedure) | 13 | N/A | not applicable (rsynced) |
| `tools/TOOL_DESCRIPTIONS.md` | Modify | Low | 82 | N/A | not applicable (rsynced) |
| `routing.md` | Modify | Medium (loaded by every task) | 28 | N/A | not applicable (rsynced) |
| `tools/run_validation_gates.py` | Modify | Medium | 8 | N/A | not applicable (rsynced) |

## Design
- Interface: `uv run python tools/amend_plan.py {plan_path} --file {path} --responsibility {text} --reason {text} --requirement {REQ-ID} --evidence {text} --tests {text} --step {N} --class fallout|scope [--procedure {path}] [--dry-run]`. The Plan path is `plans/` only; archived Plans are refused.
- Mechanics, each scoped to its own section: append the row after the last row of `Implementation Target Files`; extend the `Freeze status` note with `Amended {date} ({class}): added {path} — {reason}`; add a Requirement Traceability row for the linked requirement; append the path to `Related target files`; add an `Affected areas` row; append a checkbox naming the file to step N (extending the step text); add a `Work Items Created` row when `--procedure` is given.
- Freeze re-check: mechanically verify the four criteria for the new row (path exists or declared `New file` with an existing directory; reason non-empty; evidence non-empty; the requirement ID exists in the Plan's `Requirements`). All pass: `Freeze status` stays `Frozen` and the row is `Verified`. Otherwise the row is `Needs confirmation` and `Freeze status` becomes `Draft` with the failed criterion named.
- Checks: after a real run, run `check_workitem_structure.py`, `audit_plan_target_paths.py`, and `check_plan_target_overlaps.py` and print their results; a dry run prints the edits and the checks it would run.
- Refusals: the file already a target row or a reference row; the Plan not found, archived, or lacking a required section; a duplicate amendment line. A refusal changes nothing.
- Approval classes (proposed text in `rules/workflow-lifecycle.md`): fallout is a file added only to keep existing behavior, tests, inventories, or checkers working; the executor may amend and owes a report after the fact naming the file, the class, and the reason. A change to scope or behavior, a new requirement, or a removed row needs approval before it is made. The text is marked pending the owner's decision and leaves Plan Freeze validation unchanged.
- Skills: `plan-to-implementation-procedure` Step 3c calls the tool in place of the manual edit and follows the classes; `code-implementation` gains a stop rule: a file outside the procedure scope ends the cycle `Blocked` until the Plan is amended through the tool under the classes.
- Registration: the routing row carries placeholder arguments, so the gate mapping is reported `Not available` at run time but keeps its mapping.
- Alternatives rejected: a dedicated Plan section for the amendment log (A2); the tool deciding the class (A5).

## Implementation steps
1. **Phase 1: Tool and tests**
   - [ ] Implement `tools/amend_plan.py` with the dry run, append-only row, section-scoped edits, refusals, freeze re-check, and the printed checks (`REQ-001`, `REQ-002`, `REQ-003`; `tools/amend_plan.py`)
   - [ ] Write unit tests for each edit location, the append-only rule, the refusals, the repeated-path case, and the four criteria (`REQ-001`, `REQ-002`, `REQ-003`; `tests/tools/test_amend_plan.py`)
2. **Phase 2: Rule and skills**
   - [ ] Write the proposed approval classes marked pending the owner's decision (`REQ-004`; `rules/workflow-lifecycle.md`)
   - [ ] Update Step 3c (`REQ-005`; `skills/plan-to-implementation-procedure/workflow.md`)
   - [ ] Add the out-of-scope file stop rule (`REQ-005`; `skills/code-implementation/workflow.md`)
3. **Phase 3: Registration**
   - [ ] Add the tool row, routing row, and gate mapping entry (`REQ-006`; `tools/TOOL_DESCRIPTIONS.md`, `routing.md`, `tools/run_validation_gates.py`)
4. **Phase 4: Verification** (no `scripts/` or `config/` change, so no deploy step is required)
   - [ ] Run the tool lint sequence, the dry-run comparison against the three reconstructed Plans, and the checkers in the Validation plan (`REQ-001` to `REQ-006`; all rows)

## Validation plan
| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| `tools/amend_plan.py` | Unit over fixture Plans | `uv run pytest tests/tools/test_amend_plan.py -v` | all pass |
| `tools/amend_plan.py`, `tools/run_validation_gates.py` | Lint, type, security | `uv run ruff format <file>`; `uv run ruff check <file>`; `uv run mypy <file>`; `uv run bandit <file>` per file | clean |
| `tools/amend_plan.py` | Dry run on reconstructed Plan copies (AC-8) | `uv run python tools/amend_plan.py {copy} ... --dry-run` | edits match the hand-made result |
| `tools/TOOL_DESCRIPTIONS.md`, `routing.md`, `tools/run_validation_gates.py` | Registration and drift | `uv run python tools/check_tool_descriptions_sync.py`; `uv run python tools/run_validation_gates.py drift`; `uv run pytest tests/tools/test_run_validation_gates.py -v` | pass |
| `rules/workflow-lifecycle.md`, the two skills | Reference and heading checks | `uv run python tools/check_skills_references.py`; `uv run python tools/check_skills_heading_cycles.py` | no findings |

## Risks
- **Risk**: The tool corrupts a Plan by editing the wrong place. → **Mitigation**: every edit is scoped to its section, a dry run prints the edits first, tests include the repeated-path case, and the tool runs the structure, path-audit, and overlap checks afterward.
- **Risk**: The proposed fallout class lets scope creep pass as fallout. → **Mitigation**: the classes are written as proposed and marked pending the owner's decision (UNK-01); the class is recorded in the dated line so the history is visible; scope or behavior changes still need approval.
- **Risk**: The Plan Freeze rules are weakened by an easy amendment path. → **Mitigation**: the tool re-checks the four criteria and sets `Draft` on failure; the freeze rules in `rules/workflow-lifecycle.md` are unchanged.
- **Risk**: `skills/code-implementation/workflow.md` (churn 13) and the planning skill are shared with other Plans. → **Mitigation**: A6 records that the edits target different steps; the later Plan rebases.
- **Risk**: The three amended Plans' before-states cannot be reconstructed. → **Mitigation**: UNK-02; synthetic fixtures replace them for AC-8 and the limit is recorded.
- **Risk**: Shared registration files are edited by sibling Plans. → **Mitigation**: A7; row-additive edits.

## Execution Status

Table structure, status/type vocabulary, and general guidance: see `templates/execution-status.md`.

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Tool and tests: `tools/amend_plan.py`, `tests/tools/test_amend_plan.py` | In Progress | — | — |  |
| 2 | Rule and skills: `rules/workflow-lifecycle.md`, `skills/plan-to-implementation-procedure/workflow.md`, `skills/code-implementation/workflow.md` | In Progress | — | — |  |
| 3 | Registration: `tools/TOOL_DESCRIPTIONS.md`, `routing.md`, `tools/run_validation_gates.py` | In Progress | — | — |  |
| 4 | Verification: lint sequence, dry-run comparison, checkers | Pending | — | — |  |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| — | — | — | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| implementations/20261102-085611_01_tools_amend_plan.py.md | 1 | Procedure | Pending | — | — |
| implementations/20261102-085611_02_tests_tools_test_amend_plan.py.md | 1 | Procedure | Pending | — | — |
| implementations/20261102-085611_03_rules_workflow-lifecycle.md.md | 2 | Procedure | Pending | — | — |
| implementations/20261102-085611_04_skills_plan-to-implementation-procedure_workflow.md.md | 2 | Procedure | Pending | — | — |
| implementations/20261102-085611_05_skills_code-implementation_workflow.md.md | 2 | Procedure | Pending | — | — |
| implementations/20261102-085611_06_tools_TOOL_DESCRIPTIONS.md.md | 3 | Procedure | Pending | — | — |
| implementations/20261102-085611_07_routing.md.md | 3 | Procedure | Pending | — | — |
| implementations/20261102-085611_08_tools_run_validation_gates.py.md | 3 | Procedure | Pending | — | — |

## Traceability
- **Workflow phase**: issue-to-plan
- **Source issue**: issues/20261030-191737_flowimp011_plan-amend-tool.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: this document is the generated plan
- **Source implementation procedure**: N/A: not applicable in this phase
- **Generated at**: 20261102-081027
- **Related target files**: `tools/amend_plan.py`, `tests/tools/test_amend_plan.py`, `rules/workflow-lifecycle.md`, `skills/plan-to-implementation-procedure/workflow.md`, `skills/code-implementation/workflow.md`, `tools/TOOL_DESCRIPTIONS.md`, `routing.md`, `tools/run_validation_gates.py` — the full list of `File Path` values from `Implementation Target Files` above, once `Frozen`

### Requirement Traceability
See `templates/requirement-traceability.md` for the canonical column format.

| Requirement ID | Source Issue section or evidence | Target file | Implementation step | Acceptance criterion | Test or validation item | Status |
|---|---|---|---|---|---|---|
| REQ-001 | Required Changes (dry run, append-only, refusal) | `tools/amend_plan.py` | Phase 1 | AC-1, AC-2 | dry-run and refusal tests | Explicit in issue |
| REQ-001 | Testing Expectations (each edit location, append-only, refusals) | `tests/tools/test_amend_plan.py` | Phase 1 | AC-1, AC-2 | unit tests | Explicit in issue |
| REQ-002 | Implementation Intent (edit the places consistently); Acceptance Criteria (repeated path) | `tools/amend_plan.py` | Phase 1 | AC-3, AC-8 | edit-location and repeated-path tests | Explicit in issue |
| REQ-002 | Testing Expectations (repeated-path case) | `tests/tools/test_amend_plan.py` | Phase 1 | AC-3 | repeated-path test | Explicit in issue |
| REQ-003 | Constraints (the new row passes the four Freeze checks); Implementation Intent (run the checks) | `tools/amend_plan.py` | Phase 1 | AC-4 | criteria tests | Explicit in issue |
| REQ-003 | Acceptance Criteria (check results printed) | `tests/tools/test_amend_plan.py` | Phase 1 | AC-1, AC-4 | criteria and printed-check tests | Explicit in issue |
| REQ-004 | Required Changes (approval classes in `rules/workflow-lifecycle.md`) | `rules/workflow-lifecycle.md` | Phase 2 | AC-5 | reference and heading checkers | Explicit in issue |
| REQ-005 | Required Changes (update the two skills); Step 2 (no existing code-implementation stop) | `skills/plan-to-implementation-procedure/workflow.md` | Phase 2 | AC-6 | reference and heading checkers | Confirmed by repository evidence |
| REQ-005 | Required Changes; Step 2 correction | `skills/code-implementation/workflow.md` | Phase 2 | AC-6 | reference and heading checkers | Confirmed by repository evidence |
| REQ-006 | Required Changes (register the tool) | `tools/TOOL_DESCRIPTIONS.md` | Phase 3 | AC-7 | `check_tool_descriptions_sync.py` | Explicit in issue |
| REQ-006 | Target Files (`routing.md`) | `routing.md` | Phase 3 | AC-7 | drift check | Explicit in issue |
| REQ-006 | Step 3 (drift needs a gate mapping for a routing row) | `tools/run_validation_gates.py` | Phase 3 | AC-7 | drift check | Confirmed by repository evidence |

<!-- tools/generate_workitem.py implementation-procedure-pass timestamp: 20261102-085611 -->