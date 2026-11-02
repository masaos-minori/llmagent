## Goal
- Make Plan-to-Plan dependencies machine-readable, add a read-only tool that computes the dependency order and the ready or gated state of open Plans, and make `plan-to-implementation-procedure` and `code-implementation` use it, so procedures that cannot run yet are marked and reported as gated instead of being discovered when execution starts.

## Priority
High

## Scope
- **In-Scope**:
  - A structured dependency line in the Plan template (depended-on Plan or Issue path, phase, reason), with the existing prose form still read as a fallback with a warning.
  - A new read-only tool, `tools/plan_dependency_order.py`, that builds the graph from the dependency lines and from shared target files, detects cycles, prints a recommended order, and reports each open Plan as `ready` or `gated` with the blocking item.
  - A gated marker for procedures of a gated Plan, defined in `templates/execution-status.md`.
  - An order view in `manage_workitem_stage.py list` (Plan phase order, grouped by Plan).
  - Updates to `plan-to-implementation-procedure` Step 2 and Step 4 and `code-implementation` Step 1 to call the tool and report, never decide.
  - Registration in `tools/TOOL_DESCRIPTIONS.md`, `routing.md`, and the gate runner mapping.
- **Out-of-Scope**:
  - Deciding or changing the real order of any open Plan, and reordering, regenerating, or editing any existing Plan or procedure.
  - Release-unit batching within a Plan (a separate Plan).
  - Consumer discovery (`plans/20261102-080004_flowimp001_consumer-impact-scan.md`).
- **Dependencies**: Sequencing only, in either order, with the Plan `plans/20261102-080336_flowimp002_plan-release-units.md` (filed from `issues/20261030-191057_flowimp002_plan-release-units.md`; its Plan exists as of Step 3a, 2026-11-02): both change `templates/plan.md`, `skills/plan-to-implementation-procedure/workflow.md`, `skills/code-implementation/workflow.md`, and `tools/manage_workitem_stage.py`; whichever lands second rebases. This Plan is created first because `issues/20261030-191457_flowimp007_stale-sibling-new.md` needs the Plan phase order view this Plan adds. Overlap judgments with Frozen Plans are in Assumptions A5 to A7 and A9.

## Background
- `Operationally observed` (2026-10-30, from the Issue): procedure documents for the schema-dependent rows of `wfrecovery001` and `wftaskapi001` were generated while the `dbmig001` Plan they depended on had no procedures; seven sat `Pending` with a prose "Gated" note until `dbmig001` was implemented, found only when execution began, and the executor asked the user about the order three times.
- `Explicit in code` (checked in Step 3): `skills/plan-to-implementation-procedure/workflow.md` Step 2 "Plan-level start conditions" says a Dependency on another open Plan or Issue must be reported with a question and the order must not be decided there. The rule is prose; nothing evaluates it and nothing is recorded on the generated documents.
- `Explicit in code` (checked in Step 3): `tools/check_plan_target_overlaps.py` lists Plans that share a target file (`discover_plan_documents`, `find_cross_plan_target_overlaps`) and gives candidates only. `tools/manage_workitem_stage.py list` filters by `--kind` and `--status` and has no order view.
- `Explicit in code` (checked in Step 3): `tools/manage_workitem_stage.py` accepts only the Status values `Pending`, `In Progress`, `Blocked`, and `Completed` (`_VALID_STATUSES`), and `skills/code-implementation/workflow.md` Step 1 and Step 7 parse those values. A new Status value would change every parser; a `Notes` prefix would not.
- Verified in Step 2 (2026-11-02): `dbmig001`, `wftaskapi001`, and `wfrecovery001` are archived in `plans/done/`, so the Issue's live-order check (dbmig001, wftaskapi001, wfrecovery001, then the others) is no longer possible on `plans/`. The smoke run is reviewed against the open Plans' stated dependencies instead.
- `Explicit in code` (checked in Step 3): `templates/plan.md` `Scope` template line reads "Dependencies: [The Issue's Dependencies, including fix order against sibling issues or plans; `N/A: none` if there are none]", free text only.

## Problem
A dependency between Plans exists only as prose. The executor learns that a procedure cannot run when it tries to run it, the generated documents do not say whether they are runnable, and the real execution order is reconstructed by hand for every batch.

## Reason for Change
Persisted-state work is ordered by design (migration framework, key rename, recovery state machine, lease and retry), and more such Plans are open. Every unrecorded dependency costs a blocked cycle and a question.

## Implementation Intent
Record the dependency in a structured line in the Plan, compute order and readiness with a tool, and let the skills consume the result. The tool recommends and never decides: the rule that the owner decides the order stays, and the tool only makes the question answerable (what depends on what, what is ready, what is gated and by which open item). Procedures of a gated Plan carry an explicit gated marker with a reason and are listed separately.

## Requirements
- `REQ-001`: `templates/plan.md` MUST define a structured dependency line in `Scope` (depended-on Plan or Issue path, phase, reason), and the tool MUST still read the existing prose form as a fallback and emit a warning for it.
- `REQ-002`: `tools/plan_dependency_order.py` MUST be read-only with no network access; MUST build the graph from the dependency lines and from shared target files (reusing the overlap tool's data); MUST detect cycles; MUST print a recommended order; and MUST report each open Plan as `ready` or `gated`, naming the blocking item.
- `REQ-003`: `templates/execution-status.md` MUST define the gated marker for a procedure of a gated Plan as a `Notes` prefix, without adding a Status value.
- `REQ-004`: `manage_workitem_stage.py list` MUST gain an order view that lists procedures in Plan phase order for a given Plan, grouped by Plan.
- `REQ-005`: `skills/plan-to-implementation-procedure/workflow.md` MUST call the tool in Step 2, report the result without deciding the order, and mark procedures of a gated Plan with the gated marker and reason.
- `REQ-006`: `skills/code-implementation/workflow.md` Step 1 MUST report gated procedures instead of starting them.
- `REQ-007`: The tool MUST be registered in `tools/TOOL_DESCRIPTIONS.md`, `routing.md`, and the gate runner mapping so the drift check passes.

## Implementation Target Files
**Freeze status**: Frozen (validated in Step 8b, 2026-11-02; all rows `Verified`)

This table is the canonical, frozen source of implementation scope for this Plan. Once `Frozen`, `Implementation steps`, `Acceptance criteria`, and every downstream `plan-to-implementation-procedure` document MUST reference file paths only from this table — no other file may be treated as a modification target.

| File Path | Change Responsibility | Reason for Modification | Related Requirement / Acceptance Criterion | Repository Evidence | Related Tests | Validation Status |
|---|---|---|---|---|---|---|
| `tools/plan_dependency_order.py` | New file: dependency graph, order, readiness | New file; no tool computes Plan order or readiness (`tools/` exists) | REQ-001, REQ-002 / AC-1, AC-2 | no such tool in `tools/TOOL_DESCRIPTIONS.md`; `check_plan_target_overlaps.py` is overlap-only (checked in Step 3) | `tests/tools/test_plan_dependency_order.py` | Verified |
| `tests/tools/test_plan_dependency_order.py` | New file: unit tests | New file for the new tool (`tests/tools/` exists) | REQ-001, REQ-002 / AC-1, AC-2 | one test module per tool in `tests/tools/` (checked in Step 3) | itself | Verified |
| `tools/manage_workitem_stage.py` | Order view in `list` | `list` has `--kind` and `--status` only | REQ-004 / AC-3 | `list_parser` with `--kind` and `--status`, `show` subcommand, `parse_execution_status_table` (checked in Step 3) | `tests/tools/test_manage_workitem_stage.py` | Verified |
| `tests/tools/test_manage_workitem_stage.py` | Tests for the order view | Existing tests cover `list` filters only | REQ-004 / AC-3 | existing `list` and `show` tests in the module (checked in Step 3) | itself | Verified |
| `templates/plan.md` | Structured dependency line in the `Scope` template | The `Dependencies` line is free text | REQ-001 / AC-4 | `Scope` block of the template (checked in Step 3) | `check_workitem_structure.py` on a generated Plan | Verified |
| `templates/execution-status.md` | Gated marker definition | The vocabulary has no gated state; `_VALID_STATUSES` fixes four Status values | REQ-003 / AC-4 | "Status options: Pending / In Progress / Blocked / Completed" (checked in Step 3) | `check_skills_references.py` | Verified |
| `skills/plan-to-implementation-procedure/workflow.md` | Step 2 calls the tool; Step 4 marks gated procedures | Step 2 only says to report a dependency and ask | REQ-005 / AC-5 | "Plan-level start conditions" (checked in Step 3) | `check_skills_references.py`, `check_skills_heading_cycles.py` | Verified |
| `skills/code-implementation/workflow.md` | Step 1 reports gated procedures | Step 1 has no gated check | REQ-006 / AC-5 | "Step 1: Identify the Target Implementation Procedure File(s)" (checked in Step 3) | `check_skills_references.py`, `check_skills_heading_cycles.py` | Verified |
| `tools/TOOL_DESCRIPTIONS.md` | Register the tool; note the new `list` option | Every `tools/*.py` needs a row | REQ-007 / AC-6 | `check_tool_descriptions_sync.py` hook (checked in Step 3) | `tools/check_tool_descriptions_sync.py` | Verified |
| `routing.md` | Row in "When to run which tool" | The new tool has no routing entry | REQ-007 / AC-6 | table "When to run which tool" (checked in Step 3) | `tools/run_validation_gates.py drift` | Verified |
| `tools/run_validation_gates.py` | Gate mapping entry for the new routing row | `drift_report()` fails for a routing checker without a mapping | REQ-007 / AC-6 | `drift_report`, `ROUTING_GATES` (checked in Step 3) | `tests/tools/test_run_validation_gates.py` | Verified |

## Reference Files
| File Path | Why It Must Be Read | Related Target File or Requirement |
|---|---|---|
| `tools/check_plan_target_overlaps.py` | Source of shared-target-file data to reuse | REQ-002 |
| `tools/set_execution_status.py` | Existing status writer; the marker is written through the existing `set-step-status --notes` path, unchanged, which appends to the Notes cell (`update_execution_status`), so it yields a prefix only on a row whose Notes is empty | REQ-003, REQ-005 |
| `templates/implementation-procedure.md` | Execution Status table that carries the marker | REQ-003 |
| `skills/plan-to-implementation-procedure/SKILL.md` | Core rule that the owner decides the order | REQ-005 |
| `rules/workflow-lifecycle.md` | Plan Freeze rules the marker must not contradict | REQ-003 |

## Acceptance Criteria
- AC-1 (`REQ-001`, `REQ-002`): On fixture Plans, the tool prints the expected order, reports a cycle, and marks a Plan whose dependency is open as `gated` with the blocking path; a Plan with only a prose dependency is read through the fallback with a warning.
- AC-2 (`REQ-002`): The tool writes nothing and makes no network access; a smoke run on the live `plans/` completes without error and its output is reviewed against the open Plans' stated dependencies.
- AC-3 (`REQ-004`): `manage_workitem_stage.py list` has an order view that lists procedures in Plan phase order for a given Plan, with a Plan without matching procedures handled.
- AC-4 (`REQ-001`, `REQ-003`): `templates/plan.md` carries the structured line and `templates/execution-status.md` defines the `Gated:` Notes prefix without a new Status value; `check_workitem_structure.py` passes on a Plan using them.
- AC-5 (`REQ-005`, `REQ-006`): A procedure generated for a gated Plan carries the marker and reason, and `code-implementation` Step 1 reports gated procedures instead of starting them; both skills state that the owner decides the order.
- AC-6 (`REQ-007`): `check_tool_descriptions_sync.py`, `tools/run_validation_gates.py drift`, `check_skills_references.py`, and `check_skills_heading_cycles.py` pass.

## Tests
- `REQ-001`, `REQ-002`: unit tests for graph building, cycle detection, readiness (open Issue, open Plan phase, closed, missing), and the prose fallback.
- `REQ-004`: tests for the order view, including a Plan with no procedures.
- `REQ-003`, `REQ-005`, `REQ-006`: structure and reference checks; a read-through of one gated cycle in each skill.
- `REQ-002`: one smoke run on the live `plans/` directory.

## Documentation Impact
- Yes. The two skills, `templates/plan.md`, and `templates/execution-status.md` state the structured dependency, the gated marker, and that the owner decides the order (REQ-001, REQ-003, REQ-005, REQ-006). `tools/TOOL_DESCRIPTIONS.md` and `routing.md` list the tool (REQ-007). No `docs/*.md` change: workflow tooling, not system design.

## Assumptions
- A1: A Plan's dependency can always be expressed as a Plan or Issue path plus a phase (from the Issue). Falsifiable by a dependency on something that is neither.
- A2: Decision (Unresolved Question in the Issue): the gated state is a `Notes` prefix `Gated:` with Status `Pending`, not a new Status value, because `_VALID_STATUSES` and the Step 1 and Step 7 parsers fix four values. A gated row never started, so `Blocked` (a started row that hit a blocker) does not fit. Falsifiable by the owner preferring a new Status value, which would add `tools/manage_workitem_stage.py` parser changes to this Plan.
- A3: Decision: the existing open Plans' prose dependencies are not converted by this Plan (the Issue forbids editing existing Plans); the prose fallback with a warning keeps them working.
- A4: The order view derives a procedure's phase from the Plan's `Implementation steps`: the first top-level step whose text cites the procedure's target file; a procedure that matches no step is listed last with a warning. Falsifiable by a Plan whose step text does not cite file paths.
- A5: Overlap judgment (Step 8b): `routing.md` is also a target of `plans/20261102-075445_flowimp005_gates-hook-parity.md`, `plans/20261102-075753_flowimp004_schema-change-checklist.md`, and `plans/20261102-080004_flowimp001_consumer-impact-scan.md`. Judged compatible: this Plan adds one row to the "When to run which tool" table; the other edits add rows or a different section.
- A6: Overlap judgment (Step 8b): `tools/TOOL_DESCRIPTIONS.md` and `tools/run_validation_gates.py` are also targets of `plans/20261102-075445_flowimp005_gates-hook-parity.md` and `plans/20261102-080004_flowimp001_consumer-impact-scan.md`. Judged compatible: this Plan adds a new tool row and one mapping entry; the others add their own rows and entries.
- A7: Overlap judgment (Step 8b): `templates/plan.md` is also a target of `plans/20261102-080004_flowimp001_consumer-impact-scan.md`. Judged compatible: this Plan edits the `Scope` template block, that Plan adds a note under "Notes on filling Implementation Target Files and Reference Files", so the edits touch different sections. No other Frozen Plan targets the skills, `templates/execution-status.md`, or `tools/manage_workitem_stage.py` rows of this Plan.
- A8: `git-fame` is not used; Bus Factor is `N/A` (single-owner repository).
- A9: Step 3a correction and overlap judgments (2026-11-02, `plan-to-implementation-procedure` Step 2): `check_plan_target_overlaps.py` now also reports overlaps not listed in A5 to A7. `plans/20261102-080336_flowimp002_plan-release-units.md` shares `templates/plan.md` (it edits `Implementation steps`, this Plan edits `Scope`), `skills/plan-to-implementation-procedure/workflow.md`, `skills/code-implementation/workflow.md`, `tools/manage_workitem_stage.py` (it groups `list` and `show` by unit, this Plan adds `list --plan --order`), and `tests/tools/test_manage_workitem_stage.py`: sequencing dependency, whichever lands second rebases (Scope Dependencies). `plans/20261102-080513_flowimp007_stale-sibling-new.md`, `plans/20261102-080631_flowimp008_workitem-bulk-close.md`, `plans/20261102-080828_flowimp009_test-row-grouping.md`, and `plans/20261102-081027_flowimp011_plan-amend-tool.md` share the two skill workflows (Step 3c and Step 4 text, Step 2, Step 7, Toolchain), and flowimp007, flowimp008, flowimp011, and flowimp010 share `tools/TOOL_DESCRIPTIONS.md`; flowimp010 and flowimp011 also share `routing.md` and `tools/run_validation_gates.py`: judged compatible, different steps and row-additive entries, with a textual rebase where Step 4 paragraphs are adjacent. `plans/20261102-075445_flowimp005_gates-hook-parity.md` and `plans/20261102-075753_flowimp004_schema-change-checklist.md` are archived with procedures in `implementations/`; flowimp005 changes `drift_report()` to compare tool-backed pre-commit hooks, and this Plan's tool has no hook, so the added routing row only needs its mapping entry. Also corrected: the Gated marker is a Notes prefix only when the row's Notes is empty (`set-step-status --notes` appends), see Design.

## Unknowns
| ID | Unknown Description | Evidence Missing | Resolution Path | Blocking? (True/False) |
|---|---|---|---|---|
| UNK-01 | Whether the open Plans' prose dependency statements are common enough that the fallback needs more than path detection | The fallback is untested on the live open Plans | Run the smoke run (AC-2) and report the warnings it produces; refine the fallback only for shapes that appear | False |
| UNK-02 | Whether a dependency on a phase of another Plan can always be resolved from that Plan's Execution Status | Open Plans use phase rows of varying wording | Resolve by step number; report `Needs confirmation` for a phase the tool cannot match | False |

## Affected areas
| File | Change | Blast Radius | Churn (30d) | Bus Factor | deploy.sh Impact |
|---|---|---|---|---|---|
| `tools/plan_dependency_order.py` | Create | Low (new, read-only) | 0 | N/A | not applicable (rsynced) |
| `tests/tools/test_plan_dependency_order.py` | Create | Low | 0 | N/A | not applicable (rsynced) |
| `tools/manage_workitem_stage.py` | Modify | Medium (status updates and archival moves use it) | 4 | N/A | not applicable (rsynced) |
| `tests/tools/test_manage_workitem_stage.py` | Modify | Low | 4 | N/A | not applicable (rsynced) |
| `templates/plan.md` | Modify | Medium (every Plan follows it) | 5 | N/A | not applicable (rsynced) |
| `templates/execution-status.md` | Modify | Medium (shared by Plans and procedures) | 1 | N/A | not applicable (rsynced) |
| `skills/plan-to-implementation-procedure/workflow.md` | Modify | Medium | 8 | N/A | not applicable (rsynced) |
| `skills/code-implementation/workflow.md` | Modify | Medium | 13 | N/A | not applicable (rsynced) |
| `tools/TOOL_DESCRIPTIONS.md` | Modify | Low | 82 | N/A | not applicable (rsynced) |
| `routing.md` | Modify | Medium (loaded by every task) | 28 | N/A | not applicable (rsynced) |
| `tools/run_validation_gates.py` | Modify | Medium | 8 | N/A | not applicable (rsynced) |

## Design
- Dependency line: in `Scope`, one bullet per dependency: `**Depends on**: {path} | phase {N or all} | {reason}`. The tool also reads the old free text: any `plans/` or `issues/` path in the `Dependencies` text becomes a dependency with phase `all` and a `prose-dependency` warning.
- Graph: nodes are open Plans (`plans/*.md`, `Frozen` or `Draft`); edges are declared dependencies. Shared target files come from `check_plan_target_overlaps.py` data and are shown as undirected `overlap` notes, not ordering edges, because the tool may not infer an order the owner has not stated. Cycles among declared edges are reported with the cycle path.
- Readiness: a dependency is closed when its Issue is in `issues/done/`, its Plan is in `plans/done/`, or the named phase row of the depended-on Plan is `Completed`; open when its Issue is still in `issues/` or the phase row is not `Completed`; unresolvable when the path cannot be found (`Needs confirmation`). A Plan with any open dependency is `gated`, naming the blocking path and phase.
- Output: recommended order (topological over declared edges, ties by Plan filename timestamp), then `ready` and `gated` lists, then warnings. The header states that the order is a recommendation and the owner decides.
- Gated marker: a procedure of a gated Plan has `Notes` starting with `Gated: {blocking path} — {reason}` on its pending rows, written with the existing `set-step-status --notes` call while the row's Notes is empty (the call appends with a space, so it cannot prepend to existing text); when a generated procedure already carries Notes on that row, the author writes `Gated: ...` as the first text of the Notes cell when authoring the document in Step 3c instead; Status stays `Pending`. `code-implementation` Step 1 recomputes readiness with the tool, reports gated procedures instead of starting them, and does not clear a marker itself.
- Order view: `manage_workitem_stage.py list --plan {plan_path} --order` lists the procedures whose `Source plan` is that Plan, ordered by the Plan phase that first cites the procedure's target file, then by `seq`.
- Registration: the routing row carries placeholder arguments, so the gate runner mapping is reported `Not available` at run time but keeps its mapping, as existing placeholder gates do.
- Compatibility: Status vocabulary unchanged; existing Plans without the structured line keep working; no existing Plan or procedure is edited.

## Implementation steps
1. **Phase 1: Tool and its tests**
   - [ ] Implement `tools/plan_dependency_order.py` with the structured line, the prose fallback, graph, cycles, order, and readiness (`REQ-001`, `REQ-002`; `tools/plan_dependency_order.py`)
   - [ ] Write unit tests for graph, cycle, readiness, and fallback (`REQ-001`, `REQ-002`; `tests/tools/test_plan_dependency_order.py`)
2. **Phase 2: Order view**
   - [ ] Add the `--plan` and `--order` view to `list` (`REQ-004`; `tools/manage_workitem_stage.py`)
   - [ ] Add tests including a Plan with no procedures (`REQ-004`; `tests/tools/test_manage_workitem_stage.py`)
3. **Phase 3: Template and vocabulary**
   - [ ] Add the structured dependency line to the `Scope` template (`REQ-001`; `templates/plan.md`)
   - [ ] Define the `Gated:` Notes prefix (`REQ-003`; `templates/execution-status.md`)
4. **Phase 4: Skills**
   - [ ] Update Step 2 and Step 4 to call the tool, report without deciding, and mark gated procedures (`REQ-005`; `skills/plan-to-implementation-procedure/workflow.md`)
   - [ ] Update Step 1 to report gated procedures instead of starting them (`REQ-006`; `skills/code-implementation/workflow.md`)
5. **Phase 5: Registration**
   - [ ] Add the tool row, routing row, and gate mapping entry (`REQ-007`; `tools/TOOL_DESCRIPTIONS.md`, `routing.md`, `tools/run_validation_gates.py`)
6. **Phase 6: Verification** (no `scripts/` or `config/` change, so no deploy step is required)
   - [ ] Run the tool lint sequence on the changed tools, the live smoke run, and the checkers named in the Validation plan (`REQ-001` to `REQ-007`; all rows)

## Validation plan
| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| `tools/plan_dependency_order.py` | Unit over fixture Plans | `uv run pytest tests/tools/test_plan_dependency_order.py -v` | all pass |
| `tools/manage_workitem_stage.py` | Unit and regression | `uv run pytest tests/tools/test_manage_workitem_stage.py tests/tools/test_manage_workitem_stage_new.py -v` | all pass |
| `tools/plan_dependency_order.py`, `tools/manage_workitem_stage.py`, `tools/run_validation_gates.py` | Lint, type, security | `uv run ruff format <file>`; `uv run ruff check <file>`; `uv run mypy <file>`; `uv run bandit <file>` per file | clean |
| `tools/plan_dependency_order.py` | Live smoke run | `uv run python tools/plan_dependency_order.py` | completes; output reviewed against open Plans' dependencies |
| `templates/*.md`, the two skills | Structure, reference, heading checks | `uv run python tools/check_skills_references.py`; `uv run python tools/check_skills_heading_cycles.py`; `uv run python tools/check_workitem_structure.py --file <Plan>` | no findings |
| `tools/TOOL_DESCRIPTIONS.md`, `routing.md`, `tools/run_validation_gates.py` | Registration and drift | `uv run python tools/check_tool_descriptions_sync.py`; `uv run python tools/run_validation_gates.py drift` | pass |

## Risks
- **Risk**: The prose fallback misreads a path mentioned in a Dependencies sentence as a dependency. → **Mitigation**: fallback dependencies are flagged with a warning and never silently gate a Plan beyond a `gated (prose)` label the owner can read; UNK-01 refines it only for shapes that appear.
- **Risk**: The tool is read as deciding the order. → **Mitigation**: the header and both skills state the owner decides; the tool never reorders or edits a document.
- **Risk**: `tools/manage_workitem_stage.py` is shared with the release-unit Plan and has complex functions (`update_execution_status`, `cmd_close_batch` rated D by `radon cc`, Step 5). → **Mitigation**: the order view is a new, separate function and subcommand option; no existing function is edited; the later Plan rebases (Scope Dependencies).
- **Risk**: `set-step-status --notes` appends and cannot prepend, so a marker could land after existing Notes text and fail a prefix check. → **Mitigation**: the author writes the marker first in the Notes cell when generating; the tool recognizes `Gated:` at the start of the Notes cell only, and reports a row that carries it elsewhere as a warning.
- **Risk**: The gated marker is lost when a procedure is regenerated. → **Mitigation**: marker writing is a skill step run after generation; `code-implementation` Step 1 recomputes readiness from the tool, not from the marker alone.
- **Risk**: Shared files (`routing.md`, `tools/TOOL_DESCRIPTIONS.md`, `tools/run_validation_gates.py`) are edited by sibling Plans. → **Mitigation**: row-additive edits; judgments in Assumptions A5 and A6.

## Execution Status

Table structure, status/type vocabulary, and general guidance: see `templates/execution-status.md`.

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Tool and tests: `tools/plan_dependency_order.py`, `tests/tools/test_plan_dependency_order.py` | Completed | — | 20261102-101710 |  |
| 2 | Order view: `tools/manage_workitem_stage.py`, `tests/tools/test_manage_workitem_stage.py` | Completed | — | 20261102-101947 |  |
| 3 | Template and vocabulary: `templates/plan.md`, `templates/execution-status.md` | Completed | — | 20261102-102056 |  |
| 4 | Skills: `skills/plan-to-implementation-procedure/workflow.md`, `skills/code-implementation/workflow.md` | Completed | — | 20261102-102157 |  |
| 5 | Registration: `tools/TOOL_DESCRIPTIONS.md`, `routing.md`, `tools/run_validation_gates.py` | Completed | — | 20261102-102315 |  |
| 6 | Verification: lint sequence, live smoke run, checkers | Completed | — | 20261102-103259 | Lint sequence, live smoke run, checkers pass; full suite 11052 passed, 1 known pre-existing failure (mdq bind gate) |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| — | — | — | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| implementations/20261102-085056_01_tools_plan_dependency_order.py.md | 1 | Procedure | Pending | — | — |
| implementations/20261102-085056_02_tests_tools_test_plan_dependency_order.py.md | 1 | Procedure | Pending | — | — |
| implementations/20261102-085056_03_tools_manage_workitem_stage.py.md | 2 | Procedure | Pending | — | — |
| implementations/20261102-085056_04_tests_tools_test_manage_workitem_stage.py.md | 2 | Procedure | Pending | — | — |
| implementations/20261102-085056_05_templates_plan.md.md | 3 | Procedure | Pending | — | — |
| implementations/20261102-085056_06_templates_execution-status.md.md | 3 | Procedure | Pending | — | — |
| implementations/20261102-085056_07_skills_plan-to-implementation-procedure_workflow.md.md | 4 | Procedure | Pending | — | — |
| implementations/20261102-085056_08_skills_code-implementation_workflow.md.md | 4 | Procedure | Pending | — | — |
| implementations/20261102-085056_09_tools_TOOL_DESCRIPTIONS.md.md | 5 | Procedure | Pending | — | — |
| implementations/20261102-085056_10_routing.md.md | 5 | Procedure | Pending | — | — |
| implementations/20261102-085056_11_tools_run_validation_gates.py.md | 5 | Procedure | Pending | — | — |

## Traceability
- **Workflow phase**: issue-to-plan
- **Source issue**: issues/20261030-191144_flowimp003_plan-dependency-gate.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: this document is the generated plan
- **Source implementation procedure**: N/A: not applicable in this phase
- **Generated at**: 20261102-080134
- **Related target files**: `tools/plan_dependency_order.py`, `tests/tools/test_plan_dependency_order.py`, `tools/manage_workitem_stage.py`, `tests/tools/test_manage_workitem_stage.py`, `templates/plan.md`, `templates/execution-status.md`, `skills/plan-to-implementation-procedure/workflow.md`, `skills/code-implementation/workflow.md`, `tools/TOOL_DESCRIPTIONS.md`, `routing.md`, `tools/run_validation_gates.py` — the full list of `File Path` values from `Implementation Target Files` above, once `Frozen`

### Requirement Traceability
See `templates/requirement-traceability.md` for the canonical column format.

| Requirement ID | Source Issue section or evidence | Target file | Implementation step | Acceptance criterion | Test or validation item | Status |
|---|---|---|---|---|---|---|
| REQ-001 | Required Changes (structured dependency line, prose fallback) | `tools/plan_dependency_order.py` | Phase 1 | AC-1 | fallback unit test | Explicit in issue |
| REQ-001 | Required Changes (define the line in the Plan template) | `templates/plan.md` | Phase 3 | AC-4 | `check_workitem_structure.py` | Explicit in issue |
| REQ-002 | Required Changes (graph, cycles, order, ready or gated) | `tools/plan_dependency_order.py` | Phase 1 | AC-1, AC-2 | graph, cycle, readiness tests; smoke run | Explicit in issue |
| REQ-002 | Testing Expectations (unit tests) | `tests/tools/test_plan_dependency_order.py` | Phase 1 | AC-1 | unit tests | Explicit in issue |
| REQ-003 | Required Changes (marker with a vocabulary entry); Step 3 (`_VALID_STATUSES`) | `templates/execution-status.md` | Phase 3 | AC-4 | structure and reference checks | Confirmed by repository evidence |
| REQ-004 | Required Changes (order view in `list`) | `tools/manage_workitem_stage.py` | Phase 2 | AC-3 | order view tests | Explicit in issue |
| REQ-004 | Testing Expectations (order view tests) | `tests/tools/test_manage_workitem_stage.py` | Phase 2 | AC-3 | order view tests | Explicit in issue |
| REQ-005 | Required Changes (update the two skills; report, not decide) | `skills/plan-to-implementation-procedure/workflow.md` | Phase 4 | AC-5 | reference and heading checks | Explicit in issue |
| REQ-006 | Acceptance Criteria (`code-implementation` Step 1 reports gated procedures) | `skills/code-implementation/workflow.md` | Phase 4 | AC-5 | reference and heading checks | Explicit in issue |
| REQ-007 | Required Changes (register the tool) | `tools/TOOL_DESCRIPTIONS.md` | Phase 5 | AC-6 | `check_tool_descriptions_sync.py` | Explicit in issue |
| REQ-007 | Target Files (`routing.md`) | `routing.md` | Phase 5 | AC-6 | drift check | Explicit in issue |
| REQ-007 | Step 3 (drift needs a gate mapping for a routing row) | `tools/run_validation_gates.py` | Phase 5 | AC-6 | drift check | Confirmed by repository evidence |

<!-- tools/generate_workitem.py implementation-procedure-pass timestamp: 20261102-085056 -->