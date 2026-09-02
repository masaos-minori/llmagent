## Goal
Satisfy `REQ-001`/`REQ-002` (ptip009): cross-reference `rules/workflow-lifecycle.md`'s shared
Rollback-Directive-applicability clarification from
`skills/plan-to-implementation-procedure/workflow.md`, and additionally state that a Plan-file
revert during an active Step 3 pass must preserve the `generate_workitem.py` timestamp marker.

## Scope
Modify exactly two locations in `skills/plan-to-implementation-procedure/workflow.md`: the
Plan-correction paragraph in Step 3 (current lines 143-151) gets a short cross-reference; the
shared-timestamp paragraph in Step 3 (current lines 160-169) gets the marker-preservation
requirement. No other line in this file is touched.

## Assumptions
- Depends on `itp004`'s `rules/workflow-lifecycle.md` `## Plan-Document Correction Handling`
  section (generated this cycle as a separate implementation procedure document) landing in the
  same cycle, so this cross-reference points to real content.
- Re-verified 2026-09-02: `tools/generate_workitem.py` lines 75-81 confirm the marker format:
  `<!-- tools/generate_workitem.py implementation-procedure-pass timestamp: {timestamp} -->`
  (`_PASS_TIMESTAMP_MARKER_RE`/`_PASS_TIMESTAMP_MARKER_TEMPLATE`).
- **Corrected 2026-09-02**: the Plan's originally-cited "line 32-35" (Allowed file operations)
  is confirmed accurate for the marker's *existence*, but the correct insertion point for the
  *preservation requirement* is the shared-timestamp paragraph in Step 3 (current lines
  160-169), which is where an agent mid-pass actually reasons about the marker.

## Design decisions
Resolve REQ-001 by cross-referencing `itp004`'s shared clarification rather than duplicating it
(Plan `Design`, corrected 2026-09-02 after this session found the Plan's original Design
section was copy-pasted from an unrelated sibling plan, itp004's Multi-file-processing text).
Resolve REQ-002 (the workflow-specific addition `itp004` does not need, since `issue-to-plan`
has no equivalent marker mechanism) by stating the preservation requirement directly in this
file, next to the existing marker-sharing explanation.

## Alternatives considered
Placing the marker-preservation requirement in `rules/workflow-lifecycle.md` alongside the
Rollback Directive clarification — rejected: the timestamp-marker mechanism is specific to
`tools/generate_workitem.py` and this workflow's Step 3, not a cross-workflow concern like
Rollback Directive applicability itself, so it belongs in this file next to the existing
marker-sharing explanation.

## Implementation
### Target file
skills/plan-to-implementation-procedure/workflow.md

### Procedure
Add a cross-reference to the Plan-correction paragraph, and a marker-preservation requirement
to the shared-timestamp paragraph.

### Method
1. Locate the Plan-correction paragraph (current lines 143-151, ending "...do not report a row
   `Completed` while a Plan-level inconsistency it surfaced remains unresolved."). Append:
   ```
   If this correction requires reverting a prior edit to `plans/{filename}_plan.md`, see
   `rules/workflow-lifecycle.md` Plan-Document Correction Handling for whether `AGENTS.md`
   Rollback Directive applies (it does not) — and, if a revert is nonetheless performed,
   see the timestamp-marker preservation requirement below.
   ```
2. Locate the shared-timestamp paragraph (current lines 160-169, ending "...so every
   invocation against the same `--source-plan` reuses the same value regardless of invocation
   order or a resumed session."). Append:
   ```
   If `plans/{filename}_plan.md` is reverted (in whole or in part) during an active Step 3
   pass for any reason, the existing `_PASS_TIMESTAMP_MARKER_RE` marker line (format:
   `<!-- tools/generate_workitem.py implementation-procedure-pass timestamp: {timestamp}
   -->`) MUST be preserved — re-add it if a full-file revert removed it. Do not let it
   silently regenerate with a new value: a still-pending row's later
   `generate_workitem.py` call would then mint a different timestamp than earlier rows in
   the same pass, breaking the "one shared timestamp per pass" guarantee this Step
   otherwise depends on.
   ```

### Details
This does not change `tools/generate_workitem.py`'s own marker-writing behavior (Plan Scope
Out-of-Scope) — only what the workflow requires an agent to do if a revert happens to remove
the marker.

## Compatibility considerations
Documentation-only change to a skill's own procedure text; no code, schema, or runtime
behavior affected.

## Security considerations
N/A: no security-relevant content in a workflow-procedure clarification.

## Rollback considerations
Trivially revertable via `git revert`/`git checkout` of this single file — should be reverted
together with `itp004`'s `rules/workflow-lifecycle.md` section if that is rolled back, to avoid
a dangling cross-reference.

## Validation plan
- Manual review: confirm the resolution is consistent with `itp004`'s resolution for the sibling workflow, and that the timestamp-marker preservation requirement does not contradict `tools/generate_workitem.py`'s documented behavior (Plan `Tests`).

## Completion criteria
Step 3 cross-references the shared Rollback-Directive clarification, and states the
timestamp-marker preservation requirement for any Plan-file revert during an active pass.

## Out of scope
`AGENTS.md`'s Rollback Directive itself (Plan Scope Out-of-Scope). `tools/generate_workitem.py`'s
marker-writing behavior (Plan Scope Out-of-Scope) — not modified.

## Documentation
Not a `docs/*.md` file; no `docs/00_index.md` task-scope mapping applies.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Add Rollback-Directive cross-reference per Method | Completed | 2026-09-02 | 2026-09-02 | itp004's rules/workflow-lifecycle.md section had already landed in a prior batch; cross-reference resolves correctly |
| 2 | Add timestamp-marker preservation requirement per Method | Completed | 2026-09-02 | 2026-09-02 | Verified `_PASS_TIMESTAMP_MARKER_RE`/`_PASS_TIMESTAMP_MARKER_TEMPLATE` at tools/generate_workitem.py:75,79 |
| 3 | N/A: no test to add (doc-only change) | Completed | 2026-09-02 | 2026-09-02 | N/A |
| 4 | Manual review validation | Completed | 2026-09-02 | 2026-09-02 | Confirmed consistent with itp004's resolution and generate_workitem.py's documented marker behavior |

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
- **Requirement ID**: REQ-001, REQ-002 (Rollback Directive cross-reference + timestamp-marker preservation)
- **Source issue**: `issues/20260901-171500_ptip009_rollback_directive_undefined_for_plan_documents.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20260901-214209_plan.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260902-153722
- **Related target files**: `skills/plan-to-implementation-procedure/workflow.md`
