## Goal
Satisfy `REQ-001`/`REQ-002` (itp010): add an explicit batch-continuation policy to
`rules/workflow-lifecycle.md` Archival Move for a move failure, and align Completion Criteria
with the resulting per-file framing.

## Scope
Modify exactly two locations in `rules/workflow-lifecycle.md`: the Archival Move section's
"If you cannot move the file, stop and report the error" bullet (current line 136), and the
Completion Criteria section (current lines 139-144). No other section in this file is touched.

## Assumptions
- Re-verified 2026-09-02: Archival Move (current lines 113-137) already states, per-skill, "If
  `git mv` fails, report `Blocked` — do not fall back to another method" (added since this
  Plan's Background was written — a partial overlap, not a contradiction: it already covers
  *reporting* `Blocked`, but not yet the *batch-continuation* question this Plan targets). The
  generic closing bullet ("If you cannot move the file, stop and report the error... Do not
  proceed without completing this step") is unchanged and still ambiguous between per-file and
  whole-batch scope, which is this row's actual target.

## Design decisions
State that a move failure is immediately terminal for that file only (no automatic retry —
resolves UNK-02) and reports `Blocked` for that file, leaving its output document generated but
unarchived; the batch continues to the next target file (Plan `Design`, corrected 2026-09-02
after this session found the Plan's original Design section was boilerplate copied from an
unrelated sibling plan, not describing this Plan's own content).

## Alternatives considered
Adding one automatic retry before `Blocked` — rejected (UNK-02): `git mv`'s refusal reasons
(destination exists, source missing, uncommitted changes) are deterministic, not transient; a
blind retry would not change the outcome without an agent or human first resolving the
underlying condition. This is distinct from `itp003`'s filename-collision retry, where
incrementing to the next available sequence number is itself a different operation, not a
repeat of the identical one.

## Implementation
### Target file
rules/workflow-lifecycle.md

### Procedure
Add a batch-continuation clause to Archival Move's "stop and report" bullet; add a
per-file-scope clarification to Completion Criteria.

### Method
1. Locate current line 136:
   ```
   - **If you cannot move the file, stop and report the error.** Do not proceed without completing this step.
   ```
   Replace with:
   ```
   - **If you cannot move the file, report `Blocked` for that specific file — this is
     immediately terminal for that file, with no automatic retry (see `Archival Move`'s
     per-skill `Blocked` bullets above). Do not proceed without completing this step for
     *that file*.** In a Multi-file-processing batch, this halts only the blocked file's
     own cycle — its output document remains generated but unarchived — and the batch
     continues to the next target file, since Completion Criteria (below) already tracks
     completion per file, not as an all-or-nothing batch property. This continuation is
     strictly sequential (the next file's cycle starts only after the blocked file's cycle
     has fully stopped), not parallel recovery, per `rules/ai-execution.md` Global Safety
     Restrictions (Base).
   ```
2. Locate the Completion Criteria section (current lines 139-144):
   ```
   ## Completion Criteria

   The cycle is complete only when:
   - output document generated and validated
   - source file moved to archive and verified
   - no unresolved blocking items remain
   ```
   Append a clarifying sentence after the bulleted list:
   ```
   These criteria apply per file, per `Sequential Target Processing (Base)`'s per-file gating —
   a batch containing one `Blocked` file alongside otherwise-`Completed` files is a valid,
   partially-complete outcome, not a batch-wide failure.
   ```

### Details
This does not build actual retry-on-failure logic (Plan Scope Out-of-Scope) — it only states
that no retry occurs, consistent with `git mv`'s deterministic refusal reasons.

## Compatibility considerations
Documentation-only change to a shared rules file; no code, schema, or runtime behavior
affected.

## Security considerations
N/A: no security-relevant content in a batch-continuation policy clarification.

## Rollback considerations
Trivially revertable via `git revert`/`git checkout` of this single file.

## Validation plan
- Manual review: confirm the added policy is internally consistent and does not contradict Sequential Target Processing (Base) or Global Safety Restrictions (Base) (Plan `Tests`).

## Completion criteria
Archival Move states explicitly that a move failure is terminal for that file only (no retry)
and that the batch continues to the next file; Completion Criteria states its per-file
applicability explicitly.

## Out of scope
Building actual retry-on-failure logic (Plan Scope Out-of-Scope) — this issue only requires the
policy to be stated, not a new mechanism implemented.

## Documentation
Not a `docs/*.md` file; no `docs/00_index.md` task-scope mapping applies.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Add batch-continuation clause to Archival Move per Method | Completed | 2026-09-02 | 2026-09-02 | Verified lines 153-154 matched exactly (17-line shift from cited 136, from an earlier itp004 edit to this same file) |
| 2 | Add per-file-scope clarification to Completion Criteria per Method | Completed | 2026-09-02 | 2026-09-02 | Verified lines 156-161 matched exactly |
| 3 | N/A: no test to add (doc-only change) | Completed | 2026-09-02 | 2026-09-02 | N/A |
| 4 | Manual review validation | Completed | 2026-09-02 | 2026-09-02 | Confirmed consistent with rules/ai-execution.md Sequential Target Processing (Base) and Global Safety Restrictions (Base) — no parallel recovery implied |

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
- **Requirement ID**: REQ-001, REQ-002 (batch-continuation policy for Archival Move failure)
- **Source issue**: `issues/20260901-170327_itp010_no_continuation_policy_after_archival_move_failure.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20260901-220358_plan.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260902-154117
- **Related target files**: `rules/workflow-lifecycle.md`
