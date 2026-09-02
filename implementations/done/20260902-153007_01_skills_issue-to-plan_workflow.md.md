## Goal
Satisfy `REQ-001`/`REQ-002` (itp003): add an explicit 3-attempt retry limit and stop-and-report
behavior to `skills/issue-to-plan/workflow.md` Step 5 and Step 6's zero-padded-sequence
collision-retry procedures.

## Scope
Modify exactly two locations in `skills/issue-to-plan/workflow.md`: Step 5's sequence-retry
sentence (current lines 247-249) and Step 6's sequence-retry sentence (current lines 307-309).
No other line in this file is touched.

## Assumptions
- Re-verified 2026-09-02: both target sentences match the Plan's evidence content exactly. Line
  numbers have drifted from the Plan's originally-cited "line 248-249"/"line 286-287" to
  current 247-249/307-309 (a ~20-line shift for Step 6, likely from an unrelated addition
  elsewhere in the file) — content is unchanged, only line position shifted; no Plan correction
  needed beyond noting the current line numbers here.

## Design decisions
Treat this retry loop as an instance of `AGENTS.md`'s general Attempt Limit (3 attempts), not a
separate workflow-specific bound (Plan `Design`, corrected 2026-09-02 after this session found
the Plan's original Design section was copy-pasted from an unrelated sibling plan, itp007, and
resolving UNK-01) — a filesystem naming collision retried with an incrementing sequence is the
same class of repeated-failure-on-the-same-operation the Attempt Limit rule already covers.

## Alternatives considered
Defining a workflow-specific bound different from 3 — rejected: no distinct justification for a
different number was found; reusing `AGENTS.md`'s existing precedent avoids an arbitrary new
constant and keeps the two rules easy to reason about together.

## Implementation
### Target file
skills/issue-to-plan/workflow.md

### Procedure
Append a retry-bound and stop-and-report clause to both Step 5's and Step 6's sequence-retry
sentences.

### Method
1. Locate Step 5's sentence (current lines 247-249):
   ```
   - Save as `plans/{timestamp}_plan.md`. If that path already exists, use the lowest
     available zero-padded sequence (`plans/{timestamp}_01_plan.md`,
     `plans/{timestamp}_02_plan.md`, ...). An existing file MUST NOT be overwritten.
   ```
   Append:
   ```
     Retry up to 3 times (per `AGENTS.md` Loop Prevention > Attempt Limit — this collision
     retry is an instance of that rule, not a separate bound). After 3 collisions, stop and
     report `Blocked: repeated filename collision — plans/{timestamp}_plan.md` rather than
     continuing to increment.
   ```
2. Locate Step 6's sentence (current lines 307-309):
   ```
   - If either path already exists, apply the same lowest-available zero-padded sequence
     rule as Step 5 (`issues/{timestamp}_01_unknowns.md`, `issues/{timestamp}_01_risks.md`,
     ...). An existing file MUST NOT be overwritten.
   ```
   Append:
   ```
     The same 3-attempt bound and stop-and-report behavior from Step 5 apply here: after 3
     collisions on either path, stop and report `Blocked: repeated filename collision —
     {path}` for the colliding path.
   ```

### Details
Both edits cite `AGENTS.md` Attempt Limit explicitly and use the workflow's existing `Blocked`
reporting convention (`templates/execution-status.md`), rather than inventing a new reporting
format.

## Compatibility considerations
Documentation-only change to a skill's own procedure text; no code, schema, or runtime
behavior affected. Does not change `tools/generate_workitem.py`'s own reject-only collision
behavior (Plan Scope Out-of-Scope).

## Security considerations
N/A: no security-relevant content in a workflow-procedure retry-bound clarification.

## Rollback considerations
Trivially revertable via `git revert`/`git checkout` of this single file.

## Validation plan
- Manual review: confirm the added bound is internally consistent with `AGENTS.md` Attempt Limit and does not contradict the existing tool-refusal-handling text (Plan `Tests`).

## Completion criteria
Step 5 and Step 6 each state a concrete maximum (3) sequence-retry attempts and the
stop-and-report behavior once that maximum is reached.

## Out of scope
`tools/generate_workitem.py`'s own reject-only collision behavior (Plan Scope Out-of-Scope).
Retry-limit logic for other skills' analogous collision-handling steps, e.g.
`plan-to-implementation-procedure`'s own sequence rules (Plan Scope Out-of-Scope — file
separately if the same gap is confirmed there).

## Documentation
Not a `docs/*.md` file; no `docs/00_index.md` task-scope mapping applies.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Add retry bound + stop-and-report to Step 5 per Method | Completed | 2026-09-02 | 2026-09-02 | Verified lines 257-259 matched exactly |
| 2 | Add retry bound + stop-and-report to Step 6 per Method | Completed | 2026-09-02 | 2026-09-02 | Verified lines 317-319 matched exactly |
| 3 | N/A: no test to add (doc-only change) | Completed | 2026-09-02 | 2026-09-02 | N/A |
| 4 | Manual review validation | Completed | 2026-09-02 | 2026-09-02 | Confirmed consistent with AGENTS.md Attempt Limit wording (line 41-43) |

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
- **Requirement ID**: REQ-001, REQ-002 (3-attempt retry bound + stop-and-report for Step 5/6)
- **Source issue**: `issues/20260901-170327_itp003_sequence_retry_lacks_attempt_limit.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20260901-214951_plan.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260902-153007
- **Related target files**: `skills/issue-to-plan/workflow.md`
