## Goal
- Describe batch mode for a declared release unit, with explicit exceptions to the per-cycle gate and per-file archival, and keep the per-cycle gate for Plans without a unit (`REQ-003`).

## Scope
- In scope: a new `### Batch mode (release unit)` subsection in Multi-file processing, a one-sentence exception in Step 4's full-suite bullet, and a one-sentence pointer at the start of Step 7. Out of scope: Step 1, Step 2, the Toolchain table, the scope rules, and Step 7's close-command and Plan-update text (other Plans edit them).

## Assumptions
- Step 3a: Step 4 says "Run the repository-defined full test suite exactly once per cycle" and already lists two exceptions (a failing-run re-run, and a conflict-detected earlier file); Multi-file processing applies `rules/ai-execution.md` Sequential Target Processing (Base); Step 7 archives each file with `close-implementation --stage-only` in a batch; Rollback on Failure reverts only files recorded in Step 3d's Notes (all checked against the current file).
- `rules/workflow-lifecycle.md` states it applies to the document-generation workflows, so it does not bind this workflow; the rule being excepted is `rules/ai-execution.md` Sequential Target Processing (Base), which `rules/ai-execution.md` Instruction Precedence > Explicit exceptions allows a workflow to except only by an explicit statement referencing it. No `rules/` edit is needed.
- Overlap (Step 2): this file is also targeted by the Plans filed from `flowimp003` (Step 1), `flowimp007` (Step 2), `flowimp008` (Toolchain table and Step 7 Plan-update call), `flowimp009` (Step 2, Step 3d, Step 7 mapping), and `flowimp011` (scope rules). Judged compatible (plan Assumption A7 and the other Plans' own Assumptions): this row adds a subsection, a sentence in Step 4, and a pointer sentence at the top of Step 7, touching none of their paragraphs. Whichever lands later rebases; the Step 7 pointer sits near the paragraphs `flowimp008` and `flowimp009` edit.
- Member order is the `seq` order already given by "Dependency order"; after the order view of `flowimp003` lands it becomes the order source (plan Assumption A4). Whether a failure is attributable to a later member is the executor's judgment, recorded in the Failure Log with the reason (plan Assumption A3).
- Depends on rows 02 and 04: a member is a procedure whose `Release unit` line in `## Scope` names a unit.

## Design decisions
- Batch mode applies only when procedures of one `Source plan` carry the same unit name and every member is in the batch; otherwise stop and ask (Question policy) rather than running a half unit in ordinary mode.
- Per member, Steps 1 to 3e, 5, and 6 run as usual, and Step 4's impact-selected targeted tests still run; only the full-suite and diff-cover run and Step 7 are deferred to after the last member.
- Allowed red states: (a) a targeted test failure, or (b) a Step 3e finding (type, import), that the executor attributes to a symbol or schema a later member creates, each recorded in the Failure Log with the reason; every other failure stops the cycle under the existing Attempt Limit.

## Alternatives considered
- A mechanical attribution test was rejected (plan Assumption A3); a per-unit Execution Status was rejected (A2).

## Implementation
### Target file
`skills/code-implementation/workflow.md`

### Procedure
- Under Multi-file processing, after the "Dependency order" paragraph, add `### Batch mode (release unit)` stating: applicability and the stop-and-ask rule above; the explicit exceptions (Step 4 "exactly once per cycle" becomes once per unit, after the last member; `rules/ai-execution.md` Sequential Target Processing (Base) "complete required gates before the next target" is excepted for the full suite, diff-cover, and Step 7 only), each by file path and heading per Instruction Precedence; the allowed red states; what stays mandatory (Step 3e validators, impact-selected tests, the Attempt Limit, the Failure Log, Step 3d baseline and single-path rollback limited to files recorded in the members' Notes); and the end-of-unit sequence (full suite with coverage and diff-cover once, then each member's Step 7 with `--stage-only` and the Plan Execution Status update).
- In Step 4's full-suite bullet, add one sentence: for a declared unit the single run is the end-of-unit run (see Batch mode); this is a third exception to "exactly once per cycle", scoped to a unit.
- At the start of Step 7, add one sentence: in batch mode this Step runs for all members after the end-of-unit run passes.
- State that a Plan without a unit keeps the per-cycle gate unchanged.

### Method
- Use the file's existing "MUST" style. Reference `rules/ai-execution.md` only by path plus the headings "Sequential Target Processing (Base)" and "Instruction Precedence", which exist.
- If the end-of-unit run fails and a fix would touch a member already finished, the fix is a normal Attempt Limit attempt and its file joins the Notes list so rollback stays single-path.

### Details
- Row 3 of each member's own Execution Status stays `In Progress` until the end-of-unit run passes; rows 1, 2, and 4 follow the existing Row mapping.

## Compatibility considerations
- Procedures without a unit follow the existing text unchanged. The new subsection adds a heading below an existing `##`; `tools/check_skills_heading_cycles.py` must stay clean.

## Security considerations
N/A: documentation only; no new command is introduced and rollback stays limited to single recorded paths.

## Rollback considerations
N/A: revert the commit.

## Validation plan
- `uv run python tools/check_skills_references.py`; `uv run python tools/check_skills_heading_cycles.py` report no findings (AC-6).
- Walk-through on a copy of the archived `wfrecovery001` Plan with a declaration added: the batch-mode text reproduces the by-hand run, recorded in the implementing change (AC-5). The copy is kept outside `plans/`.

## Completion criteria
- Batch mode exists with the exceptions named by path and heading, the allowed red states, the end-of-unit sequence, and the per-cycle default stated (AC-2); both checkers pass (AC-6); the walk-through is recorded (AC-5).

## Out of Scope
- Any change to the full suite, the coverage threshold, the Attempt Limit, or rollback limits.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Write the Batch mode subsection and the Step 4 and Step 7 sentences | Completed | 20261102-125222 | 20261102-125222 | Stale clean; 3a anchors confirmed (Step 4 exceptions at line 378-392, Sequential Target Processing exists); subsection placed after Multi-file processing preamble, before Progress recording. Changed: skills/code-implementation/workflow.md |
| 2 | Walk-through on a copy of the archived `wfrecovery001` Plan | Completed | 20261102-125222 | 20261102-125222 | Recorded in the implementing change; not a code test AC-5 walk-through on copy scratchpad/wfrecovery001_with_unit.md (unit phases 2,3): Phase 1/4 ordinary per-cycle; Phase 2 schema member runs 3e plus targeted tests, attempt-insert failures from attempt_number NOT NULL are allowed red (a), attributed to Phase 3 write path; Phase 3 members land; one full suite plus diff-cover at end; all members archived --stage-only after pass. Matches by-hand run. |
| 3 | Run `check_skills_references.py` and `check_skills_heading_cycles.py` | Completed | 20261102-125222 | 20261102-125222 | check_skills_references and check_skills_heading_cycles: no findings; full suite deferred to plan end |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| — | — | — | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| — | — | — | — | — | — |

## Traceability
- **Workflow phase**: plan-to-implementation-procedure
- **Requirement ID**: `REQ-003`
- **Source issue**: issues/20261030-191057_flowimp002_plan-release-units.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261102-080336_flowimp002_plan-release-units.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261102-085047
- **Related target files**: skills/code-implementation/workflow.md