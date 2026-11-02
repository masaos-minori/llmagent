## Goal
- Make closing executed implementation procedures discoverable and complete: point `code-implementation` at the existing row and archive tools, and add one verified batch command that archives procedures with renames staged, updates the Plan's `Work Items Created` table, and sets Plan steps `Completed` only on verified evidence, without the all-rows-`Completed` shortcut that `close-batch` takes.

## Priority
Medium

## Scope
- **In-Scope**:
  - A new tool, `tools/close_procedures_batch.py`, that verifies before it changes anything, supports a dry run, archives the named procedures with renames staged, updates matching `Work Items Created` rows, and marks the Plan steps the caller names `Completed` only when every file the step cites has an archived procedure.
  - Referencing `tools/set_execution_status.py` and `tools/close_procedure.sh` in the `code-implementation` Toolchain table.
  - Replacing the manual Plan-update text in `code-implementation` Step 7 with a call to the command, keeping the mapping rule as the command's documented behavior, and updating the `Work Items Created` statement in `plan-to-implementation-procedure` Step 4.
  - Registering the tool in `tools/TOOL_DESCRIPTIONS.md`.
- **Out-of-Scope**:
  - Changing `close-batch`'s own behavior, `set_execution_status.py`, or `close_procedure.sh` (they stay working and referenced).
  - Generating procedure documents or deciding execution order.
  - Committing the result (`git-commit-and-sync`).
- **Dependencies**: Sequencing only, in either order, with `plans/20261102-080336_flowimp002_plan-release-units.md` and `plans/20261102-080134_flowimp003_plan-dependency-gate.md`: all three change `skills/code-implementation/workflow.md`, so whichever lands later rebases. This Plan adds a new tool file instead of editing `tools/manage_workitem_stage.py`, so it does not conflict with their edits to that file (Assumption A2). Overlap judgments are in Assumptions A5 to A7.

## Background
- `Operationally observed` (2026-10-30, from the Issue): closing 41 procedure documents across three Plans took repeated `set-step-status` calls, a custom Python loop, and hand edits of each Plan's `Work Items Created` table and step statuses; the executor did not use `tools/set_execution_status.py` or `tools/close_procedure.sh` because nothing in the workflow named them.
- `Explicit in code` (checked in Step 3): `tools/TOOL_DESCRIPTIONS.md` lists `set_execution_status.py` (marks selected rows of one document `Completed`) and `close_procedure.sh` (marks every row `Completed` for a date, then archives). A search of `skills/`, `routing.md`, `rules/`, `AGENTS.md`, and `prompts/` finds no reference to either. The `skills/code-implementation/workflow.md` Toolchain table names only `close-implementation` and `set-step-status`.
- `Explicit in code` (checked in Step 3): `skills/code-implementation/workflow.md` Step 7 forbids `close-batch` because it sets every row of every procedure and of the owning Plan to `Completed` and overwrites timestamps, and describes the Plan update (map by step number; mark `Completed` only when every file the step modifies has its procedure archived) as manual `set-step-status plan` calls. `skills/plan-to-implementation-procedure/workflow.md` Step 4 states that the `Work Items Created` table has no tool and is edited directly.
- `Explicit in code` (checked in Step 3): `close-implementation` refuses a procedure whose `### Execution Status` table has a `Pending` row. `tools/manage_workitem_stage.py` provides the reusable pieces `parse_execution_status_rows`, `update_execution_status`, `move_to_done`, and `_find_owning_plan`.
- Measured in Step 2 and Step 5 (2026-11-02): `tools/manage_workitem_stage.py` is 50,614 bytes, two of its functions (`update_execution_status`, `cmd_close_batch`) are rated D by `radon cc`, and `tools/check_module_size.py` gates `scripts/` only, so no size gate applies to the file. Two sibling Plans also edit it.
- `Explicit in code` (checked in Step 3): a Plan's verification step cites checks and may cite changed files (for example the "Phase 2: Verification" step of `plans/20261101-165600_idemaudit001_audit-idempotency-key-mismatch.md` names a file it confirms), so "every cited file is archived" alone cannot distinguish a file-modifying step from a check-only step.

## Problem
The closing sequence is a fixed series of operations repeated for every batch, an existing tool pair covers half of it, the skill text does not point to it, and the half that remains (Plan step mapping, `Work Items Created` table) is manual and error-prone.

## Reason for Change
Each release batch closes dozens of documents. Manual closing is slow and, because the existing batch command would overwrite true statuses, the safe path is the most laborious one. `AGENTS.md` Global Rule 7 asks for a tool once an operation repeats three or more times.

## Implementation Intent
First make the existing tools discoverable from the skill. Then add one batch command that verifies before it changes anything: every named procedure has only `Completed` or explicit `N/A` rows (rows are completed only when the caller passes an explicit option and a note), the archive destination is free, and the Plan can be found. It then archives the procedures with renames staged, updates matching `Work Items Created` rows, and marks the Plan steps the caller names `Completed` after verifying that every file those steps cite has an archived procedure. A dry run prints the planned changes. No status is invented.

## Requirements
- `REQ-001`: `skills/code-implementation/workflow.md` MUST reference `tools/set_execution_status.py` and `tools/close_procedure.sh` in its Toolchain table, stating what each does and that `close_procedure.sh` completes every row.
- `REQ-002`: `tools/close_procedures_batch.py` MUST, before any change, verify that every named procedure has only `Completed` or `N/A` rows (a `Pending` or `Blocked` row refuses the procedure and names the row, changing no file), that the archive destination is free, and that the Plan can be found; it MUST complete rows only when the caller passes an explicit option and a note; it MUST provide a dry run that prints every intended change and changes nothing.
- `REQ-003`: The tool MUST archive each verified procedure with the rename staged and MUST NOT commit; a failed archive of one document MUST be reported and MUST NOT stop the others.
- `REQ-004`: The tool MUST mark a Plan step `Completed` only when the caller names it and every file the step cites has its procedure archived (this batch's included); otherwise it MUST leave the step unchanged and report why; it MUST list the steps whose cited files are all archived as candidates when none is named.
- `REQ-005`: The tool MUST update the matching `Work Items Created` rows (the row whose Item ID is the procedure's path), MUST keep working on a Plan with no row for a document, and MUST never touch a document it did not verify.
- `REQ-006`: `skills/code-implementation/workflow.md` Step 7 MUST call the tool in place of the manual Plan update and keep the mapping rule as documented behavior; `skills/plan-to-implementation-procedure/workflow.md` Step 4 MUST state the command for the `Work Items Created` update; `tools/TOOL_DESCRIPTIONS.md` MUST register the tool.

## Implementation Target Files
**Freeze status**: Frozen (validated in Step 8b, 2026-11-02; all rows `Verified`)

This table is the canonical, frozen source of implementation scope for this Plan. Once `Frozen`, `Implementation steps`, `Acceptance criteria`, and every downstream `plan-to-implementation-procedure` document MUST reference file paths only from this table — no other file may be treated as a modification target.

| File Path | Change Responsibility | Reason for Modification | Related Requirement / Acceptance Criterion | Repository Evidence | Related Tests | Validation Status |
|---|---|---|---|---|---|---|
| `tools/close_procedures_batch.py` | New file: verified batch close | New file; no tool covers the Plan step mapping and `Work Items Created` update (`tools/` exists) | REQ-002, REQ-003, REQ-004, REQ-005 / AC-1, AC-2, AC-3, AC-4 | `close-batch` is ruled out by Step 7; `TOOL_DESCRIPTIONS.md` lists no such tool (checked in Step 3) | `tests/tools/test_close_procedures_batch.py` | Verified |
| `tests/tools/test_close_procedures_batch.py` | New file: unit tests | New file for the new tool (`tests/tools/` exists) | REQ-002 to REQ-005 / AC-1 to AC-4 | one test module per tool in `tests/tools/` (checked in Step 3) | itself | Verified |
| `skills/code-implementation/workflow.md` | Toolchain references and Step 7 call | The Toolchain table omits the two tools; Step 7 describes the Plan update as manual calls | REQ-001, REQ-006 / AC-5 | "Toolchain" table and "Plan Execution Status update (after the move)" (checked in Step 3) | `check_skills_references.py`, `check_skills_heading_cycles.py` | Verified |
| `skills/plan-to-implementation-procedure/workflow.md` | `Work Items Created` statement | Step 4 says the table has no tool and is edited directly | REQ-006 / AC-5 | "Record the generated documents in the Plan" paragraph (checked in Step 3) | `check_skills_references.py`, `check_skills_heading_cycles.py` | Verified |
| `tools/TOOL_DESCRIPTIONS.md` | Register the tool | Every `tools/*.py` needs a row | REQ-006 / AC-6 | `check_tool_descriptions_sync.py` hook (checked in Step 3) | `tools/check_tool_descriptions_sync.py` | Verified |

## Reference Files
| File Path | Why It Must Be Read | Related Target File or Requirement |
|---|---|---|
| `tools/manage_workitem_stage.py` | Reusable parsing, status update, and archival helpers; refusal rules of `close-implementation` and `close-batch` | REQ-002, REQ-003 |
| `tools/set_execution_status.py` | Existing row-completion tool to reference and, where fitting, reuse | REQ-001, REQ-002 |
| `tools/close_procedure.sh` | Existing all-rows close to reference | REQ-001 |
| `tests/tools/test_manage_workitem_stage.py` | Fixture patterns for Plans and procedures | REQ-002 to REQ-005 |
| `tests/tools/test_set_execution_status.py` | Fixture patterns for row completion | REQ-002 |
| `templates/execution-status.md` | Table structure and vocabulary the tool reads and writes | REQ-002, REQ-005 |
| `templates/plan.md` | `Implementation steps` and `Work Items Created` shapes | REQ-004, REQ-005 |

## Acceptance Criteria
- AC-1 (`REQ-002`): On fixture Plans and procedures, a dry run prints the intended row changes, archives, step mappings, and `Work Items Created` updates and changes nothing; a real run applies exactly those.
- AC-2 (`REQ-002`): A procedure with a `Pending` or `Blocked` row is refused with the row named, without changing any file; rows are completed only with the explicit option and a note.
- AC-3 (`REQ-003`): Renames are staged and nothing is committed; a failed archive of one document is reported and the others still complete.
- AC-4 (`REQ-004`, `REQ-005`): A Plan step is marked `Completed` only when named and all cited files have archived procedures (a step citing two files with one archived is left unchanged and reported); a Plan with no `Work Items Created` row for a document is handled; with no step named, candidates are listed and no step is changed.
- AC-5 (`REQ-001`, `REQ-006`): The two skill texts reference the command and the two tools, and `check_skills_references.py` and `check_skills_heading_cycles.py` pass.
- AC-6 (`REQ-006`): `check_tool_descriptions_sync.py` passes with the tool registered.

## Tests
- `REQ-002`: unit tests for each refusal (Pending row, Blocked row, destination exists, Plan not found) and the explicit completion option.
- `REQ-003`: tests for staged-only renames and a partial archive failure.
- `REQ-004`: tests for a step citing two files with one archived, a named step, an unnamed step, and candidate listing.
- `REQ-005`: tests for a matching row, a missing row, and an untouched unverified document.
- `REQ-002` to `REQ-005`: one dry run on the live repository's `plans/` and `implementations/done/` for a recently closed batch, reviewed against the manual result.

## Documentation Impact
- Yes. The two skills state the command, its verification, and that rows are never completed implicitly (REQ-001, REQ-006); `tools/TOOL_DESCRIPTIONS.md` registers the tool. No `docs/*.md` change: workflow tooling.

## Assumptions
- A1: A Plan step's cited files can be read reliably from its checkbox lines (from the Issue). The tool refuses to map a step it cannot parse and reports it. Falsifiable by a Plan whose steps do not cite paths in backticks.
- A2: Decision (Unresolved Question): the command is a new sibling tool, not a subcommand of `tools/manage_workitem_stage.py`, because that file is 50,614 bytes with two D-rated functions (Step 5) and two sibling Plans edit it; the new tool imports its helpers. Falsifiable by the owner preferring a subcommand, which would add that file and its test to this Plan.
- A3: Decision (Unresolved Question): `close_procedure.sh` keeps its all-rows behavior and stays referenced; folding it into the new command is out of scope. Falsifiable by the owner asking for removal.
- A4: Decision: Plan steps are marked only when the caller names them. Reason (Step 3 evidence): a check-only verification step can cite the same files, so "all cited files archived" is necessary but not sufficient; the caller keeps the judgment the existing Step 7 rule gives the executor, and the tool verifies the mechanical condition. Falsifiable by a Plan format in which file-modifying steps are machine-distinguishable, which would allow automatic marking in a later change.
- A5: Overlap judgment (Step 8b): `skills/code-implementation/workflow.md` is also a target of `plans/20261102-080134_flowimp003_plan-dependency-gate.md`, `plans/20261102-080336_flowimp002_plan-release-units.md`, and `plans/20261102-080513_flowimp007_stale-sibling-new.md`. Judged compatible: this Plan edits the Toolchain table and Step 7; the others edit Step 1, Step 2, Step 4, and Multi-file processing.
- A6: Overlap judgment (Step 8b): `skills/plan-to-implementation-procedure/workflow.md` is also a target of the same three Plans. Judged compatible: this Plan edits the `Work Items Created` paragraph in Step 4; the others edit Step 2, Step 3c item (2), and the unit and gated-marker text. The `Work Items Created` paragraph sits next to the gated-marker text of `plans/20261102-080134_flowimp003_plan-dependency-gate.md`, so whichever lands later rebases.
- A7: Overlap judgment (Step 8b): `tools/TOOL_DESCRIPTIONS.md` is also a target of several Plans. Judged compatible: each adds or updates its own row.
- A8: `git-fame` is not used; Bus Factor is `N/A` (single-owner repository).
- A9: Overlap judgment (plan-to-implementation-procedure Step 2, `check_plan_target_overlaps.py`, 2026-11-02): `skills/code-implementation/workflow.md` and `skills/plan-to-implementation-procedure/workflow.md` are also targets of `plans/20261102-080828_flowimp009_test-row-grouping.md` and `plans/20261102-081027_flowimp011_plan-amend-tool.md`, and `tools/TOOL_DESCRIPTIONS.md` of `plans/20261102-081027_flowimp011_plan-amend-tool.md` and `plans/20261102-081312_flowimp010_artifact-commit-split.md`. Judged compatible for the TOOL_DESCRIPTIONS rows and for the `plan-to-implementation-procedure` Step 4 paragraph. Sequencing dependency, not a conflict: `plans/20261102-080828_flowimp009_test-row-grouping.md` also edits the Step 7 "Plan Execution Status update" mapping text of `code-implementation` (companion test files counted in a procedure's archive); this Plan replaces that same subsection with a call to the command, so whichever lands later rebases, and the command reads a procedure's `Related target files` as a comma-separated list (Design, Matching) so it is already compatible with that Plan.
- A10: Step 3a finding (2026-11-02): `tools/set_execution_status.py` `apply_updates` marks every selected row `Completed` whatever its current status (a `Blocked` or `N/A` row would be overwritten). The command therefore selects only the step numbers of `Pending` rows when `--complete-rows` is given. `N/A` is not in the status vocabulary of `templates/execution-status.md` or `tools/manage_workitem_stage.py` (`Pending`, `In Progress`, `Blocked`, `Completed`) but appears in older archived procedures (for example `implementations/done/20260903-122926_06_docs_00_governance_03_issue-and-uncertainty-management.md.md`), so the command accepts it as a terminal status and never writes it.

## Unknowns
| ID | Unknown Description | Evidence Missing | Resolution Path | Blocking? (True/False) |
|---|---|---|---|---|
| UNK-01 | Whether the owner wants Plan steps marked automatically when all cited files are archived | The Issue states the all-files rule as sufficient; Step 3 shows check-only steps can satisfy it | Ship explicit `--plan-steps` with candidate listing (A4); revisit on owner feedback | False |
| UNK-02 | The exact `Work Items Created` row format used by older Plans | Rows use the path as Item ID in recent Plans; older Plans are unchecked | Match rows by the procedure path substring; report unmatched documents without failing | False |

## Affected areas
| File | Change | Blast Radius | Churn (30d) | Bus Factor | deploy.sh Impact |
|---|---|---|---|---|---|
| `tools/close_procedures_batch.py` | Create | Low (new; called only from the skill) | 0 | N/A | not applicable (rsynced) |
| `tests/tools/test_close_procedures_batch.py` | Create | Low | 0 | N/A | not applicable (rsynced) |
| `skills/code-implementation/workflow.md` | Modify | High (executes every procedure) | 13 | N/A | not applicable (rsynced) |
| `skills/plan-to-implementation-procedure/workflow.md` | Modify | Medium | 8 | N/A | not applicable (rsynced) |
| `tools/TOOL_DESCRIPTIONS.md` | Modify | Low | 82 | N/A | not applicable (rsynced) |

## Design
- Interface: `uv run python tools/close_procedures_batch.py {procedure paths...} [--plan {plan_path}] [--plan-steps N,M] [--complete-rows --note {text}] [--dry-run]`. The Plan defaults to the procedures' common `Source plan`.
- Verify first (no change until every check passes for a procedure): the file exists; its Execution Status table parses; every row is `Completed` or `N/A` (`Pending` and `Blocked` rows refuse the procedure unless `--complete-rows` with `--note` is given, which completes only `Pending` rows and records the note); the archive destination is free; the Plan is found in `plans/` or `plans/done/`. A refused procedure is reported with its reason and left untouched; verified procedures proceed.
- Apply per verified procedure: archive with the rename staged through the existing `move_to_done` path (staging only, never committing); a failure is recorded and the loop continues.
- Plan updates: for each archived procedure, update the `Work Items Created` row whose Item ID is its path to `Completed`, if present. For `--plan-steps`, verify each named step cites at least one file and that every cited `Implementation Target Files` path has a procedure in `implementations/done/` with that Plan as `Source plan`; mark the step through the existing status-update helper; otherwise leave it and report. With no steps named, list candidate steps and change none.
- Matching: the tool reads a procedure's Traceability `Related target files` as a comma-separated list of paths, because the Plan filed from `issues/20261030-191615_flowimp009_test-row-grouping.md` lets a procedure list companion test files after its primary target.
- Output: a plan-of-changes table in dry run and an applied-changes table otherwise, ending with counts of verified, refused, archived, failed, steps marked, and steps left.
- Alternatives rejected: a `manage_workitem_stage.py` subcommand (A2); automatic step marking (A4); folding in `close_procedure.sh` (A3).
- Compatibility: `close-batch`, `close-implementation`, `set-step-status`, `set_execution_status.py`, and `close_procedure.sh` are unchanged.

## Implementation steps
1. **Phase 1: Tool and tests**
   - [ ] Implement `tools/close_procedures_batch.py` with verification, dry run, staged archival, `Work Items Created` update, and the explicit Plan step marking (`REQ-002`, `REQ-003`, `REQ-004`, `REQ-005`; `tools/close_procedures_batch.py`)
   - [ ] Write unit tests for each refusal, partial failure, step mapping, and row update case (`REQ-002` to `REQ-005`; `tests/tools/test_close_procedures_batch.py`)
2. **Phase 2: Skill text and registration**
   - [ ] Reference the two existing tools in the Toolchain table and replace the manual Plan update in Step 7 with the command (`REQ-001`, `REQ-006`; `skills/code-implementation/workflow.md`)
   - [ ] Update the `Work Items Created` statement (`REQ-006`; `skills/plan-to-implementation-procedure/workflow.md`)
   - [ ] Register the tool (`REQ-006`; `tools/TOOL_DESCRIPTIONS.md`)
3. **Phase 3: Verification** (no `scripts/` or `config/` change, so no deploy step is required)
   - [ ] Run the tool lint sequence on the new tool, one live dry run, and the checkers named in the Validation plan (`REQ-001` to `REQ-006`; all rows)

## Validation plan
| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| `tools/close_procedures_batch.py` | Unit over temporary Plans and procedures | `uv run pytest tests/tools/test_close_procedures_batch.py -v` | all pass |
| `tools/close_procedures_batch.py` | Lint, type, security | `uv run ruff format tools/close_procedures_batch.py`; `uv run ruff check tools/close_procedures_batch.py`; `uv run mypy tools/close_procedures_batch.py`; `uv run bandit tools/close_procedures_batch.py` | clean |
| `tools/close_procedures_batch.py` | Live dry run | `uv run python tools/close_procedures_batch.py {procedures} --dry-run` on a recently closed batch | prints intended changes; changes nothing |
| `tools/TOOL_DESCRIPTIONS.md` | Sync check | `uv run python tools/check_tool_descriptions_sync.py` | passes |
| The two skills | Reference and heading checks | `uv run python tools/check_skills_references.py`; `uv run python tools/check_skills_heading_cycles.py` | no findings |

## Risks
- **Risk**: The command archives or marks something that was not verified. → **Mitigation**: verify-before-change per procedure, explicit options for completing rows and marking steps, a dry run, and tests for each refusal; the tool never touches a document it did not verify.
- **Risk**: A named Plan step is wrongly closed. → **Mitigation**: the tool verifies the all-cited-files-archived condition and refuses otherwise; the caller names the steps (A4).
- **Risk**: Shared `skills/code-implementation/workflow.md` and `skills/plan-to-implementation-procedure/workflow.md` are edited by sibling Plans. → **Mitigation**: A5 and A6 record that the edits target different sections; the later Plan rebases.
- **Risk**: Staging renames while another session has staged files confuses the next commit. → **Mitigation**: staging only the moved paths (the existing `--stage-only` behavior); `git-commit-and-sync` Phase 2 already handles pre-staged archival renames.
- **Risk**: Pre-existing `vulture` and `bandit` findings in `scripts/` (Step 5) are mistaken for regressions. → **Mitigation**: baseline recorded in the sibling Plans; only findings on the new tool count.

## Execution Status

Table structure, status/type vocabulary, and general guidance: see `templates/execution-status.md`.

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Tool and tests: `tools/close_procedures_batch.py`, `tests/tools/test_close_procedures_batch.py` | In Progress | — | — |  |
| 2 | Skill text and registration: `skills/code-implementation/workflow.md`, `skills/plan-to-implementation-procedure/workflow.md`, `tools/TOOL_DESCRIPTIONS.md` | In Progress | — | — |  |
| 3 | Verification: lint sequence, live dry run, checkers | Pending | — | — |  |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| — | — | — | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| `implementations/20261102-085613_01_tools_close_procedures_batch.py.md` | 1 | Procedure | Pending | — | — |
| `implementations/20261102-085613_02_tests_tools_test_close_procedures_batch.py.md` | 1 | Procedure | Pending | — | — |
| `implementations/20261102-085613_03_skills_code-implementation_workflow.md.md` | 2 | Procedure | Pending | — | — |
| `implementations/20261102-085613_04_skills_plan-to-implementation-procedure_workflow.md.md` | 2 | Procedure | Pending | — | — |
| `implementations/20261102-085613_05_tools_TOOL_DESCRIPTIONS.md.md` | 2 | Procedure | Pending | — | — |

## Traceability
- **Workflow phase**: issue-to-plan
- **Source issue**: issues/20261030-191530_flowimp008_workitem-bulk-close.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: this document is the generated plan
- **Source implementation procedure**: N/A: not applicable in this phase
- **Generated at**: 20261102-080631
- **Related target files**: `tools/close_procedures_batch.py`, `tests/tools/test_close_procedures_batch.py`, `skills/code-implementation/workflow.md`, `skills/plan-to-implementation-procedure/workflow.md`, `tools/TOOL_DESCRIPTIONS.md` — the full list of `File Path` values from `Implementation Target Files` above, once `Frozen`

### Requirement Traceability
See `templates/requirement-traceability.md` for the canonical column format.

| Requirement ID | Source Issue section or evidence | Target file | Implementation step | Acceptance criterion | Test or validation item | Status |
|---|---|---|---|---|---|---|
| REQ-001 | Required Changes (reference the two tools in the Toolchain table); Background | `skills/code-implementation/workflow.md` | Phase 2 | AC-5 | reference and heading checkers | Confirmed by repository evidence |
| REQ-002 | Required Changes (verified batch command, dry run, explicit completion) | `tools/close_procedures_batch.py` | Phase 1 | AC-1, AC-2 | refusal and dry-run tests | Explicit in issue |
| REQ-002 | Testing Expectations (unit tests for each refusal) | `tests/tools/test_close_procedures_batch.py` | Phase 1 | AC-1, AC-2 | refusal and dry-run tests | Explicit in issue |
| REQ-003 | Constraints (stage only; per-file failure does not stop others) | `tools/close_procedures_batch.py` | Phase 1 | AC-3 | staged-only and partial-failure tests | Explicit in issue |
| REQ-004 | Required Changes (Plan step mapping); Step 3 (check-only steps cite files) | `tools/close_procedures_batch.py` | Phase 1 | AC-4 | step mapping tests | Derived from confirmed evidence |
| REQ-005 | Required Changes (`Work Items Created` updates); Constraints (Plans without rows) | `tools/close_procedures_batch.py` | Phase 1 | AC-4 | row update tests | Explicit in issue |
| REQ-005 | Testing Expectations (Plan whose step cites two files with one archived) | `tests/tools/test_close_procedures_batch.py` | Phase 1 | AC-4 | step and row tests | Explicit in issue |
| REQ-006 | Required Changes (replace manual Step 7 text with the command) | `skills/code-implementation/workflow.md` | Phase 2 | AC-5 | reference and heading checkers | Explicit in issue |
| REQ-006 | Required Changes (update the `Work Items Created` statement) | `skills/plan-to-implementation-procedure/workflow.md` | Phase 2 | AC-5 | reference and heading checkers | Explicit in issue |
| REQ-006 | Acceptance Criteria (tool registered) | `tools/TOOL_DESCRIPTIONS.md` | Phase 2 | AC-6 | `check_tool_descriptions_sync.py` | Explicit in issue |

<!-- tools/generate_workitem.py implementation-procedure-pass timestamp: 20261102-085613 -->