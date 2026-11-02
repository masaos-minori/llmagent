## Goal
- Add one narrow case to the shared Progress Reporting rule: a command expected to run longer than a stated threshold, or any command started in the background, is announced in one line before the wait starts, stating what is awaited and the expected duration, and no polling messages are added while waiting.

## Priority
Low

## Scope
- **In-Scope**:
  - One rule in `rules/ai-execution.md` Progress Reporting (Base): the before-a-long-wait line with a stated threshold and its content, the statement that polling messages are not added, and the one-line result report when a background command's completion is delivered by the platform.
- **Out-of-Scope**:
  - Changing the platform's own "has not heard" notice or how background completion is delivered.
  - Changing which steps run the full suite (`plans/20261102-080336_flowimp002_plan-release-units.md` covers batching).
  - Restating the rule in any workflow file, and any change to `skills/code-implementation/workflow.md` (Assumption A2).
- **Dependencies**: N/A: none. Re-verified in Step 2 (2026-11-02): no Issue or Frozen Plan lists `rules/ai-execution.md` as a target; `tools/check_plan_target_overlaps.py` reports no overlap for this Plan. Open Plans mention the file only as a referenced rule.

## Background
- `Explicit in code` (checked in Step 3): `rules/ai-execution.md` Progress Reporting (Base) says to report once per step, in one line, after the step completes, and to omit the report when the step finished as expected. It has no case for a step that runs for minutes inside a single step; the sections Tool Usage and Command Results do not mention waits either.
- `Operationally observed` (2026-10-30, from the Issue): the session ran the full test suite about eight times (427 to 493 seconds each) and other long commands, often in the background; during those waits the interface repeatedly reported that the user had not heard from the assistant for a while, and an ad hoc status line had to be added each time.
- `Explicit in code` (checked in Step 3): `skills/code-implementation/workflow.md` Step 4 requires the full-suite run in every cycle, and its Multi-file processing section applies `rules/ai-execution.md` Progress Reporting (Base) by name. The rule therefore reaches `code-implementation` through the existing reference. The other workflows that cite Progress Reporting (Base) are `prompts/01_issue-to-plan.md`, `prompts/02_plan-to-implementation-procedure.md`, `prompts/03_implementation.md`, `prompts/04_refactor.md`, `prompts/07_test-audit.md`, `prompts/08_document-sync.md`, `skills/issue-to-plan/workflow.md`, `skills/plan-to-implementation-procedure/workflow.md`, and `skills/python-refactoring/workflow.md`.

## Problem
The reporting rule is built around step boundaries. A long wait inside a step produces no output, which reads as a stall to the user and invites unplanned status messages that repeat information or interrupt the work.

## Reason for Change
The wait is predictable (the suite's duration is known to within a minute), the fix is a few sentences of rule, and it applies to every workflow that cites the shared Progress Reporting text.

## Implementation Intent
Keep the existing cadence and add one narrow case. Before a command expected to take longer than the threshold, or any command started in the background, emit a single line saying what is waited on and the expected duration. Do not add periodic polling messages; when a background command's completion is delivered by the platform, report its result in one line. The threshold and wording live in the shared rule, so each workflow inherits them through its existing reference.

## Requirements
- `REQ-001`: `rules/ai-execution.md` Progress Reporting (Base) MUST state that a command expected to take longer than a stated threshold, and any command started in the background, is announced in one line before the wait, naming what is awaited and the expected duration.
- `REQ-002`: The rule MUST state that polling or periodic messages are not added while waiting and that a background command's delivered completion is reported in one line.
- `REQ-003`: The rule MUST NOT increase the number of messages for ordinary short steps, MUST NOT contradict the Output section ("Do not repeat the same content as a \"summary\", \"detail\", and \"conclusion\"") or the existing Progress Reporting (Base) cadence, and MUST NOT be restated in any workflow file.

## Implementation Target Files
**Freeze status**: Frozen (validated in Step 8b, 2026-11-02; all rows `Verified`)

This table is the canonical, frozen source of implementation scope for this Plan. Once `Frozen`, `Implementation steps`, `Acceptance criteria`, and every downstream `plan-to-implementation-procedure` document MUST reference file paths only from this table — no other file may be treated as a modification target.

| File Path | Change Responsibility | Reason for Modification | Related Requirement / Acceptance Criterion | Repository Evidence | Related Tests | Validation Status |
|---|---|---|---|---|---|---|
| `rules/ai-execution.md` | Add the before-a-long-wait rule to Progress Reporting (Base) | The section covers step boundaries only and has no long-wait case | REQ-001, REQ-002, REQ-003 / AC-1, AC-2, AC-3 | "Progress Reporting (Base)" section with the once-per-step bullets (checked in Step 3) | `check_skills_references.py`, `check_skills_heading_cycles.py` | Verified |

## Reference Files
| File Path | Why It Must Be Read | Related Target File or Requirement |
|---|---|---|
| `skills/code-implementation/workflow.md` | Confirms Step 4's full-suite run and its by-name reference to Progress Reporting (Base), so no edit is needed there | REQ-003 |
| `prompts/03_implementation.md` | Confirms the implementation entry point also references Progress Reporting (Base) | REQ-003 |

## Acceptance Criteria
- AC-1 (`REQ-001`, `REQ-002`): `rules/ai-execution.md` contains the rule with a stated threshold, the one-line announcement content, the no-polling statement, and the one-line result report.
- AC-2 (`REQ-003`): No workflow, prompt, or skill file restates the rule, and `skills/code-implementation/workflow.md` is unchanged.
- AC-3 (`REQ-003`): A review of the rule against `rules/ai-execution.md` Output and Progress Reporting (Base) finds no contradiction, and `check_skills_references.py` and `check_skills_heading_cycles.py` pass.
- AC-4 (`REQ-001`, `REQ-002`): A read-through of one `code-implementation` cycle with a full-suite run yields one announcement line before the wait and one result line after it.

## Tests
- `REQ-001`, `REQ-002`, `REQ-003`: the skill and rules checkers named in `routing.md` for a changed `rules/*.md` file; a read-through of one `code-implementation` cycle (no code test).

## Documentation Impact
- N/A: the change is limited to the shared rule `rules/ai-execution.md` (REQ-001 to REQ-003); no `docs/*.md` requires updating.

## Assumptions
- A1: A threshold of one minute is a proposal, not a measurement (from the Issue). The rule states it as the default and workflows MAY NOT override it. Falsifiable by a different threshold giving fewer unplanned messages.
- A2: Decision (Issue: "reference it from `code-implementation` Step 4 only if needed"): no reference is added, because `skills/code-implementation/workflow.md` already applies Progress Reporting (Base) by name. Falsifiable by a read-through showing the rule is not reached.
- A3: The announcement may ride on the description of the command's tool call or be a separate line; the rule requires only that exactly one announcement line exists before the wait (Unresolved Question in the Issue).
- A4: The interface's "has not heard" notice is triggered by elapsed silence, so one line before the wait prevents most of them (from the Issue). Falsifiable by notices still appearing after the rule is followed.
- A5: Path A classification: one target file, no runtime interface, no schema; the validation quality baseline is `N/A: no Python target`.
- A6: `git-fame` is not used; Bus Factor is `N/A` (single-owner repository).

## Unknowns
| ID | Unknown Description | Evidence Missing | Resolution Path | Blocking? (True/False) |
|---|---|---|---|---|
| UNK-01 | The right threshold | One minute is a proposal; no measurement of when the notice appears | Use one minute as the stated default (A1); revisit if notices still appear | False |
| UNK-02 | Whether the announcement should be a separate message or ride on the preceding tool call description | The interface behavior is not specified in the repository | Allow either (A3) | False |

## Affected areas
| File | Change | Blast Radius | Churn (30d) | Bus Factor | deploy.sh Impact |
|---|---|---|---|---|---|
| `rules/ai-execution.md` | Modify | Medium (cited by nine workflow files and prompts through Progress Reporting (Base)) | 1 | N/A | not applicable (rsynced) |

## Design
- Placement: new bullets in Progress Reporting (Base), after the once-per-step bullets, so the section keeps one cadence plus one narrow case.
- Content: one bullet for the announcement (threshold of one minute, or any background command; one line naming what is awaited and the expected duration); one bullet that polling or periodic messages are not added while waiting and that a delivered background completion is reported in one line.
- Constraint: the new bullets add no message for steps under the threshold and do not restate Output's rules; no workflow file is edited.
- Classification: Path A (one target file, no runtime-facing interface, no schema change), so architecture, dependency, historical, and operational analyses were skipped and the validation quality baseline is `N/A: no Python target`.
- Compatibility: existing citations of Progress Reporting (Base) are unchanged; workflows inherit the case automatically.

## Implementation steps
1. **Phase 1: Add the rule**
   - [ ] Add the announcement and no-polling bullets to Progress Reporting (Base) (`REQ-001`, `REQ-002`, `REQ-003`; `rules/ai-execution.md`)
2. **Phase 2: Verification** (no `scripts/` or `config/` change, so no deploy step is required)
   - [ ] Run `check_skills_references.py` and `check_skills_heading_cycles.py`, confirm with `rg -n -i "announc" skills prompts` that no workflow file restates the rule, and read one `code-implementation` cycle against the rule (`REQ-001`, `REQ-002`, `REQ-003`; `rules/ai-execution.md`)

## Validation plan
| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| `rules/ai-execution.md` | Reference and heading checks | `uv run python tools/check_skills_references.py`; `uv run python tools/check_skills_heading_cycles.py` | no findings |
| `rules/ai-execution.md` | No restatement elsewhere | `rg -n -i "announc" skills prompts` before and after the change | no new match in `skills/` or `prompts/` |
| `rules/ai-execution.md` | Read-through against Output and Progress Reporting (Base) | read the section and one `code-implementation` full-suite cycle | one announcement line and one result line |

## Risks
- **Risk**: The new bullet conflicts with the Output section or the once-per-step cadence. → **Mitigation**: REQ-003 and AC-3 require a read-through against both; the bullet adds a pre-wait line only for long or background commands.
- **Risk**: The rule increases messages for short steps. → **Mitigation**: the threshold excludes them (A1) and the rule states it adds no message for ordinary short steps.
- **Risk**: The one-minute threshold is wrong. → **Mitigation**: stated as a proposal (UNK-01); changing it is a one-line edit.
- **Risk**: A workflow later restates the rule and drifts. → **Mitigation**: AC-2 and the `rg` check confirm a single location; workflows inherit by reference.

## Execution Status

Table structure, status/type vocabulary, and general guidance: see `templates/execution-status.md`.

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Add the rule: `rules/ai-execution.md` | In Progress | — | — |  |
| 2 | Verification: checkers, no-restatement check, read-through of `rules/ai-execution.md` | Pending | — | — |  |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| — | — | — | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| implementations/20261102-084602_01_rules_ai-execution.md.md | 1 | Procedure | Pending | — | — |

## Traceability
- **Workflow phase**: issue-to-plan
- **Source issue**: issues/20261030-191820_flowimp012_long-wait-reporting.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: this document is the generated plan
- **Source implementation procedure**: N/A: not applicable in this phase
- **Generated at**: 20261102-081426
- **Related target files**: `rules/ai-execution.md` — the full list of `File Path` values from `Implementation Target Files` above, once `Frozen`

### Requirement Traceability
See `templates/requirement-traceability.md` for the canonical column format.

| Requirement ID | Source Issue section or evidence | Target file | Implementation step | Acceptance criterion | Test or validation item | Status |
|---|---|---|---|---|---|---|
| REQ-001 | Required Changes (before-a-long-wait line with a stated threshold) | `rules/ai-execution.md` | Phase 1 | AC-1, AC-4 | checkers; read-through | Explicit in issue |
| REQ-002 | Required Changes (no polling messages); Implementation Intent (one-line result report) | `rules/ai-execution.md` | Phase 1 | AC-1, AC-4 | checkers; read-through | Explicit in issue |
| REQ-003 | Constraints (no extra messages for short steps; no conflict with Output); Acceptance Criteria (no workflow restates it) | `rules/ai-execution.md` | Phase 1 | AC-2, AC-3 | `rg` single-location check; read-through | Confirmed by repository evidence |

<!-- tools/generate_workitem.py implementation-procedure-pass timestamp: 20261102-084602 -->