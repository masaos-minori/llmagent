## Goal
- State one rule for ordering notes in a Plan's `Scope` the same way in `templates/plan.md`, the issue-to-plan workflow, and the tool description (a real ordering is a structured `Depends on` bullet; the prose `Dependencies` line never names another Plan or Issue by path), and pin the tool's prose-fallback behavior with tests, so a sequencing note can no longer gate a Plan by accident.

## Priority
Medium

## Scope
- **In-Scope**: (1) the template note for the `Dependencies` line and the `Depends on` bullet; (2) the issue-to-plan workflow, where the Plan's Scope Dependencies are written (Step 5) and where overlaps are judged (Step 8b); (3) the tool description row; (4) tests that pin the prose fallback in `--plan` mode and the by-title case.
- **Out-of-Scope**: changing `tools/plan_dependency_order.py` (its behavior, docstring, and warning text stay); the structured `Depends on` semantics and the closed and open rules; how overlaps are reported (report-only, never ordering edges); new dependency kinds; the issue template's own `Dependencies` guidance.
- **Dependencies**: the work that adds the overlap audit to the same workflow section edits Step 8b and the Toolchain paragraph, so this Plan lands after its phase 3 (structured line below). The template and the description file are also edited by other tooling Plans of this batch in other regions (see Assumptions).
  - **Depends on**: plans/20261117-125207_wftool004_orphan-tool-routing.md | phase 3 | edits Step 8b and the Toolchain paragraph of `skills/issue-to-plan/workflow.md`, which this Plan also edits in the same section

## Background
Found while generating the Plans of the workflow tooling issues: two of the six Plans written in one session (the status-vocabulary Plan and the orphan-tool-routing Plan) were reported `gated (prose)` behind sibling Plans, because the overlap notes in their `Dependencies` line named those Plans by path although the overlaps had been judged compatible. The text was reworded before the Plans were committed.

## Problem
`tools/plan_dependency_order.py` reads the structured `- **Depends on**: {path} | phase {N or all} | {reason}` bullets of a Plan's `## Scope`; when none exists it reads every `plans/` or `issues/` path of the free-text `- **Dependencies**:` bullet as a dependency with phase `all`, labels the Plan `gated (prose)` when such a dependency is open, and emits a `prose-dependency` warning (`Explicit in code`, module docstring, `parse_dependencies`, `readiness`). The `templates/plan.md` line for the Dependencies bullet tells the author to copy "the Issue's Dependencies, including fix order against sibling issues or plans" into the prose line, and its `Depends on` note says sequencing-only notes stay in the prose line (`Explicit in code`). An issue's Dependencies name Plans by path (the five issues of this batch do), so the copy itself triggers the fallback. `skills/issue-to-plan/workflow.md` never mentions the structured line: Step 4 maps Dependencies to "Scope (Dependencies)", and Step 8b says to "add the other Plan to `Scope` Dependencies" for a sequencing dependency (`Explicit in code`; no `Depends on` text in the workflow). A prose mention written to say "no ordering" therefore becomes a hard gate (`Operationally observed`: two of six Plans in one session).

The issue's open question is answered (`Operationally observed`, reproduced in this cycle on a temporary Plan set): the default text report shows both the `gated (prose)` label and a `Warnings:` entry `{plan}: prose-dependency: {path}`, and `--plan {path}` shows them too. The warning therefore reaches the default output; nothing needs to be made visible. What is missing is the rule at the point where authors write the line. Existing tests pin the fallback in `parse_dependencies`, the label, and the full-run warning, but none pins `--plan` mode with an open prose dependency, and none pins that a prose line naming a Plan without its path leaves the Plan `ready` (`Explicit in code`, `tests/tools/test_plan_dependency_order.py`).

## Reason for Change
- A false gate marks the Plan's procedures `Gated:` and makes `code-implementation` report the Plan as gated, which stalls work that has no real prerequisite.
- The template, the workflow, and the tool each give a different rule, so any author following the template can trigger it.
- It was caught here only because the order was inspected by hand. The cost of a wrong gate is a stalled implementation, not data loss.

## Implementation Intent
- Decision (guidance-only): keep the tool as it is and change the guidance. The fallback is the fail-safe for a Plan that states an ordering only in prose: an extra gate is visible (label, warning, and a question to the user in `plan-to-implementation-procedure` Step 2) and costs a stop, while dropping a real ordering would allow an out-of-order implementation silently. No open Plan relies on the fallback today (the run over the live Plans prints no `prose-dependency` warning), so removing it would buy nothing.
- One rule, worded identically in the three places: a Plan that must wait for another Plan or Issue records it as a structured `Depends on` bullet; the prose `Dependencies` line never names another Plan or Issue by path; a compatible overlap or a sequencing-only note names the other Plan by title or id, because the tool reads every `plans/` or `issues/` `.md` path in that line as a dependency on phase `all`.
- When the Issue's own Dependencies are copied into the Plan, each ordering dependency becomes a `Depends on` bullet and each non-ordering mention is written by title or id.

## Requirements
- `REQ-001`: `templates/plan.md` states the rule at the `Dependencies` line and at the `Depends on` bullet, and no longer tells the author to copy path-bearing text into the prose line.
- `REQ-002`: `skills/issue-to-plan/workflow.md` states the rule in Step 5 (populating the Scope) and in Step 8b (a sequencing dependency becomes a `Depends on` bullet; a compatible overlap is recorded in `Assumptions` and, in the Scope, only by title or id).
- `REQ-003`: The `plan_dependency_order.py` row of `tools/TOOL_DESCRIPTIONS.md` states the same rule and that the fallback gates and warns.
- `REQ-004`: Tests pin (a) `--plan` mode on a Plan with an open prose-only dependency: `gated (prose)` and the warning are printed; (b) a Plan whose prose line names another Plan by title or id without a path is `ready` with no warning; the existing structured-line and fallback tests stay green.
- `REQ-005`: `tools/plan_dependency_order.py` is unchanged, and the structured-line, closed, and open semantics are untouched.
- `REQ-006`: `tools/check_skills_references.py`, `tools/check_skills_heading_cycles.py`, and `tools/check_tool_descriptions_sync.py` pass.

## Implementation Target Files
**Freeze status**: Frozen

This table is the canonical, frozen source of implementation scope for this Plan. Once
`Frozen`, `Implementation steps`, `Acceptance criteria`, and every downstream
`plan-to-implementation-procedure` document MUST reference file paths only from this
table — no other file may be treated as a modification target.

| File Path | Change Responsibility | Reason for Modification | Related Requirement / Acceptance Criterion | Repository Evidence | Related Tests | Validation Status |
|---|---|---|---|---|---|---|
| `templates/plan.md` | State the rule at the `Dependencies` line and the `Depends on` bullet | Line 19 tells the author to copy the Issue's Dependencies into the prose line and line 20 says sequencing notes stay in the prose line | REQ-001 / AC-1 | Lines 19 and 20 of the template fence (checked in Step 3) | `tools/check_skills_references.py`, `tools/check_workitem_structure.py` | Verified |
| `skills/issue-to-plan/workflow.md` | State the rule in Step 5 and Step 8b | No `Depends on` text exists in the workflow; Step 8b says to add the other Plan to Scope Dependencies | REQ-002 / AC-2 | Step 4 mapping row `Dependencies`, Step 5 "Generate the Plan" bullets, and Step 8b lines 561 and 562 (checked in Step 3) | `tools/check_skills_references.py`, `tools/check_skills_heading_cycles.py` | Verified |
| `tools/TOOL_DESCRIPTIONS.md` | State the rule in the `plan_dependency_order.py` row | The row describes the fallback but gives no authoring rule | REQ-003 / AC-3 | Line 251 describes the fallback and the `prose-dependency` warning (checked in Step 3) | `tools/check_tool_descriptions_sync.py` | Verified |
| `tests/tools/test_plan_dependency_order.py` | Add the `--plan` prose test and the by-title test | No test pins `--plan` mode with an open prose dependency or a by-title prose line | REQ-004 / AC-4 | `test_plan_option_limits_the_report` uses a prose line whose path is unresolvable; the fallback tests cover `parse_dependencies` and the label (checked in Step 3) | The file itself | Verified |

## Reference Files
Files that must be read to implement the targets above, but MUST NOT be modified. Same
one-file-per-row discipline as `Implementation Target Files` above — no directories,
glob patterns, components, file groups, or vague phrases.

| File Path | Why It Must Be Read | Related Target File or Requirement |
|---|---|---|
| `tools/plan_dependency_order.py` | The fallback behavior the guidance describes (`parse_dependencies`, `readiness`, `render_text`); unchanged | `tools/TOOL_DESCRIPTIONS.md` / REQ-003, REQ-005 |
| `skills/plan-to-implementation-procedure/workflow.md` | Step 2 already reports each `prose-dependency` warning and asks the user; it must stay consistent | `skills/issue-to-plan/workflow.md` / REQ-002 |
| `skills/code-implementation/workflow.md` | Its gated check reads the tool's result; unchanged | `tools/TOOL_DESCRIPTIONS.md` / REQ-003 |
| `templates/issue.md` | Describes the Issue's Dependencies that are copied into the Plan | `templates/plan.md` / REQ-001 |

## Acceptance Criteria
- AC-1 (REQ-001): The template's `Dependencies` line and `Depends on` note carry the rule and no longer instruct copying path-bearing text into the prose line (review).
- AC-2 (REQ-002): Step 5 and Step 8b carry the rule in the same wording as the template, and Step 8b names the `Depends on` bullet for a sequencing dependency (review).
- AC-3 (REQ-003): The tool row carries the same rule, and the three texts state one rule (review).
- AC-4 (REQ-004): A Plan that names another Plan only in prose is `gated (prose)` with a visible warning in `--plan` mode when that Plan is open, and `ready` with no warning when it names the Plan by title or id (tests); a structured `Depends on` line still gates the Plan (existing tests).
- AC-5 (REQ-005): `git diff` shows no change to `tools/plan_dependency_order.py`.
- AC-6 (REQ-006): `tools/check_skills_references.py`, `tools/check_skills_heading_cycles.py`, and `tools/check_tool_descriptions_sync.py` pass.

## Tests
- `tests/tools/test_plan_dependency_order.py`: `--plan` mode with an open prose-only dependency prints the label and the warning; a prose line naming a Plan by title or id is `ready` with no warning (REQ-004). The tests describe current behavior, so they pass before any guidance edit.
- A run of `tools/plan_dependency_order.py` over the live Plans before and after the edits shows the same result (REQ-005).

## Documentation Impact
N/A for `docs/*.md`: no file under `docs/` changes. `templates/plan.md`, `skills/issue-to-plan/workflow.md`, and the tool description row change (REQ-001 to REQ-003).

## Assumptions
- Guidance-only is chosen (Decision above); the tool-change alternative (prose paths warn but do not gate) is recorded in Design and as UNK-01 for maintainer confirmation before Phase 2.
- Only the Scope's `Dependencies` bullet is read by the fallback; `Assumptions` and other sections may name Plans by path, as the Plans of this batch do.
- The tool needs no change because the warning already reaches the default output and `--plan` output, as reproduced in this cycle.
- Overlap with the orphan-tool-routing Plan on `skills/issue-to-plan/workflow.md` is a sequencing dependency, declared above. Overlap with the other tooling Plans on `templates/plan.md` is region-level: the structure-gate and status Plans edit other templates and other files; `tools/TOOL_DESCRIPTIONS.md` edits are row-level.

## Unknowns
| ID | Unknown Description | Evidence Missing | Resolution Path | Blocking? (True/False) |
|---|---|---|---|---|
| UNK-01 | Whether the maintainer prefers guidance-only or the tool change | A maintainer decision; the evidence (no open Plan relies on the fallback, the gate is visible, the fail-safe direction) favors guidance-only | The maintainer confirms before Phase 2; if the tool change is chosen, `tools/plan_dependency_order.py` and its docstring join the targets and this Plan is amended first | False |
| UNK-02 | Order against the other Plans that edit `tools/TOOL_DESCRIPTIONS.md` and `templates/plan.md` | The other Plans' final text of the shared files | Re-read the shared rows and the template fence at implementation time | False |

## Affected areas
`skills/DESIGN.md` Change-impact table, extended with `Churn (30d)` and `Bus Factor`
columns. The `File` column here MUST be a subset of `Implementation Target Files`'
rows — this table analyzes change-impact risk for those same files; it is not a
separate scope-of-record.

| File | Change | Blast Radius | Churn (30d) | Bus Factor | deploy.sh Impact |
|---|---|---|---|---|---|
| `templates/plan.md` | Modify | Medium: the canonical Plan shape read by the generator, the checker, and the workflow | 7 | High: single author | not applicable (rsynced) |
| `skills/issue-to-plan/workflow.md` | Modify | Medium: loaded by every issue-to-plan run | 10 | High: single author | not applicable (rsynced) |
| `tools/TOOL_DESCRIPTIONS.md` | Modify | Low: documentation rows read by the sync checker | 74 | High: single author | not applicable (rsynced) |
| `tests/tools/test_plan_dependency_order.py` | Modify | Low | 2 | High: single author | not applicable (rsynced) |

## Design
**Classification**: Path B (four target rows; the template is read by the generator and the structure checker). The four analyses ran once for this cycle.
- **Architecture**: no code module changes. `tools/generate_workitem.py` reproduces the Plan template's skeleton (its dry run printed the template text in this cycle), so a template edit changes every new skeleton; `tools/check_workitem_structure.py` reads the fence headings only.
- **Dependency graphing**: the template fence is read by the generator and the checker; `skills/issue-to-plan/workflow.md` is referenced by the routing and the other skills; the tool description is read by the sync checker. The fallback consumers are `plan-to-implementation-procedure` Step 2 and `code-implementation`'s gated check, both through the tool's output.
- **Historical**: churn is high for the workflow, the template, and the description file; every target has one author.
- **Operational**: no port, database, dependency, or lock is involved; the persisted-schema check does not apply.
- **Option 1 (guidance-only, chosen)**: states the rule where authors write the line; no behavior change; the fail-safe gate remains. Residual risk: an author who ignores the rule still gets a visible gate, not a silent one.
- **Option 2 (tool change: prose paths warn, do not gate)**: removes the false gate but also drops a real ordering that a Plan states only in prose, silently apart from a warning; changes what `plan-to-implementation-procedure` and `code-implementation` report for such Plans. Rejected because no open Plan needs it and the cost it removes is already visible.
- **Observed behavior (reproduced)**: a Plan with a prose line naming an open Plan by path is `gated (prose)`, with a warning, in both the full and `--plan` reports; with a structured bullet present the prose paths are ignored.
- **Baseline**: `radon` is not run on the test file (a test module, not a tool or script target); `vulture` and `bandit` findings under `scripts/` are pre-existing and outside the targets; `diff-cover` has no baseline because the tree equals `master`.

## Implementation steps
Each step description MUST cite the exact file path(s) it touches by referencing rows
of `Implementation Target Files` above — do not restate file-level detail
independently of that frozen table. A step is a top-level numbered item (a Phase); its
checklist items are sub-tasks, and the Execution Status table has one row per step.

1. **Phase 1: Pin the behavior**
   - [ ] Add the `--plan` prose test and the by-title test; they pass against the unchanged tool (REQ-004; `tests/tools/test_plan_dependency_order.py`)
2. **Phase 2: Template** (starts after UNK-01 is confirmed)
   - [ ] State the rule at the `Dependencies` line and the `Depends on` note (REQ-001; `templates/plan.md`)
3. **Phase 3: Workflow** (starts after the prerequisite Plan's phase 3)
   - [ ] State the rule in Step 5 and Step 8b in the template's wording (REQ-002; `skills/issue-to-plan/workflow.md`)
4. **Phase 4: Tool description**
   - [ ] State the rule in the `plan_dependency_order.py` row (REQ-003; `tools/TOOL_DESCRIPTIONS.md`)
5. **Phase 5: Verification** (no deploy step: no `scripts/` or `config/` file changes)
   - [ ] Run the tool tests, the three checkers, and the live-Plan run before and after; confirm `tools/plan_dependency_order.py` is unchanged (REQ-004 to REQ-006; all target files)

### Release units
N/A: no release unit; each phase passes validation alone when applied in order.

## Validation plan
| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| `tests/tools/test_plan_dependency_order.py` | Unit tests; before-and-after run on live Plans | `uv run pytest tests/tools/test_plan_dependency_order.py -v`; `uv run python tools/plan_dependency_order.py` | Pass; identical report before and after the guidance edits |
| `tests/tools/test_plan_dependency_order.py` | Lint and types | `uv run ruff format tests/tools`; `uv run ruff check tests/tools`; `uv run mypy --no-namespace-packages scripts/ tests/eventbus tools` | Clean |
| `templates/plan.md`, `skills/issue-to-plan/workflow.md`, `tools/TOOL_DESCRIPTIONS.md` | Reference and sync checkers | `uv run python tools/check_skills_references.py`; `uv run python tools/check_skills_heading_cycles.py`; `uv run python tools/check_tool_descriptions_sync.py` | No finding |
| `tools/plan_dependency_order.py` (unchanged) | Diff evidence | `git diff --stat -- tools/plan_dependency_order.py` | Empty |

## Risks
- **Risk**: The guidance is ignored and a prose path still gates a Plan → **Mitigation**: the gate stays visible (label, warning, a question to the user), and the rule sits where the line is written.
- **Risk**: The template edit changes every generated Plan skeleton and breaks a checker that compares text → **Mitigation**: the structure checker reads headings only; Phase 5 generates a skeleton and runs the checker on it.
- **Risk**: Three texts drift apart again → **Mitigation**: one wording, copied, with a review criterion (AC-3); a mechanical check is not added because the wording lives in prose.
- **Risk**: The prerequisite Plan's edit of Step 8b conflicts with this edit → **Mitigation**: the Plan depends on that Plan's phase 3 and re-reads the section at implementation time.
- **Risk**: `tools/TOOL_DESCRIPTIONS.md` and the workflow have high churn → **Mitigation**: change only the named row and steps, and rebase through the commit skill.

## Execution Status

Table structure, status/type vocabulary, and general guidance: see
`templates/execution-status.md`. Default rows for a freshly generated Plan (replace
with the Plan's actual steps once Implementation steps are broken down):

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Pin the prose fallback behavior with tests | Pending | — | — | |
| 2 | Template: state the rule at the Dependencies line and the Depends on note | Pending | — | — | |
| 3 | Workflow: state the rule in Step 5 and Step 8b | Pending | — | — | |
| 4 | Tool description row | Pending | — | — | |
| 5 | Verification: tests, checkers, live-Plan run, unchanged tool | Pending | — | — | |

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
- **Source issue**: issues/20261117-132205_wftoolfu005_plan-prose-dependency-gating.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: this document is the generated plan
- **Source implementation procedure**: N/A: not applicable in this phase
- **Generated at**: 20261117-134609
- **Related target files**: `templates/plan.md`; `skills/issue-to-plan/workflow.md`; `tools/TOOL_DESCRIPTIONS.md`; `tests/tools/test_plan_dependency_order.py`

### Requirement Traceability
| Requirement ID | Source Issue section or evidence | Target file | Implementation step | Acceptance criterion | Test or validation item | Status |
|---|---|---|---|---|---|---|
| REQ-001 | Implementation Intent (one rule in the template); Required Changes | `templates/plan.md` | Phase 2 | AC-1 | review; skeleton check | Explicit in issue |
| REQ-002 | Implementation Intent (one rule in the workflow); Required Changes | `skills/issue-to-plan/workflow.md` | Phase 3 | AC-2 | review; skills reference checkers | Explicit in issue |
| REQ-003 | Implementation Intent (one rule in the tool description); Required Changes | `tools/TOOL_DESCRIPTIONS.md` | Phase 4 | AC-3 | review; `tools/check_tool_descriptions_sync.py` | Explicit in issue |
| REQ-004 | Required Changes (tests with a prose-only Plan); Acceptance Criteria | `tests/tools/test_plan_dependency_order.py` | Phase 1 | AC-4 | the added tests | Explicit in issue |
| REQ-005 | Constraints (structured semantics unchanged); Required Changes (guidance-only option) | `tools/TOOL_DESCRIPTIONS.md` | Phase 5 | AC-5 | `git diff --stat` on the tool | Derived from confirmed evidence |
| REQ-006 | Acceptance Criteria (the three checkers pass) | `skills/issue-to-plan/workflow.md` | Phase 5 | AC-6 | the three checkers | Explicit in issue |
