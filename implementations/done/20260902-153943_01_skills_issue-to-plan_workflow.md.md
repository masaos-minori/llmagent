## Goal
Satisfy `REQ-001` (itp009): add a post-success file-existence/structure check to
`skills/issue-to-plan/workflow.md` Step 5's and Step 6's `tools/generate_workitem.py`
integration text.

## Scope
Modify exactly two locations in `skills/issue-to-plan/workflow.md`: Step 5's tool-integration
sentence (current lines 250-255) and Step 6's tool-integration sentence (current lines 282-287).
No other line in this file is touched.

## Assumptions
- Re-verified 2026-09-02: both target sentences match the Plan's Background quotes exactly at
  current lines 250-255 and 280-287 — no drift.

## Design decisions
A lightweight post-success check (existence + a quick structural glance, e.g. `##` heading
count), mirroring `rules/workflow-lifecycle.md` Archival Move's existing verification pattern
(Plan `Design`, corrected 2026-09-02 after this session found the Plan's original Design
section was boilerplate copied from an unrelated sibling plan, not describing this Plan's own
content) — not `tests/tools/test_generate_workitem.py`'s full field-order assertion.

## Alternatives considered
Duplicating the test suite's full field-order assertion inside the workflow document —
rejected: Plan Implementation steps explicitly call for a lightweight check only, to avoid
maintaining two copies of the same structural assertion (one in the test, one in the workflow
doc) that could drift apart.

## Implementation
### Target file
skills/issue-to-plan/workflow.md

### Procedure
Append a post-success verification sentence to both Step 5's and Step 6's tool-integration
text.

### Method
1. Locate Step 5's sentence (current lines 250-255):
   ```
   - Optionally scaffold the empty file first with `uv run python
     tools/generate_workitem.py --kind plan` — it reproduces `templates/plan.md`'s
     current field order exactly, removing manual timestamp/field-order transcription
     as an error source. The tool refuses (non-zero exit, no write) on a path
     collision rather than auto-incrementing; treat that refusal as the trigger for
     the zero-padded sequence rule above, not as a workflow failure.
   ```
   Append:
   ```
     After a `0` exit, independently verify the reported output path exists and contains
     the expected `## ` section headings before proceeding to fill in its content — per
     `rules/ai-execution.md` Repository Tool Usage item 8, a `0` exit alone MUST NOT be
     treated as proof the file was written correctly.
   ```
2. Locate Step 6's sentence (current lines 282-287):
   ```
   - Write any generated `issues/{timestamp}_unknowns.md` / `issues/{timestamp}_risks.md`
     file in English (see `SKILL.md` Core Execution Rules), same as the Plan. Optionally
     scaffold the empty file first with `uv run python tools/generate_workitem.py --kind
     unknowns` / `--kind risks` — it reproduces `templates/unknowns-issue.md` /
     `templates/risks-issue.md`'s current field order exactly. The tool refuses
     (non-zero exit, no write) on a base-path collision rather than auto-incrementing;
     on that refusal, retry once with `--seq {NN}` matching the zero-padded sequence
     rule below, rather than treating the refusal as a workflow failure.
   ```
   Append:
   ```
     After a `0` exit, independently verify the reported output path(s) exist and contain
     the expected `## ` section headings before proceeding to fill in their content — same
     verification as Step 5, per `rules/ai-execution.md` Repository Tool Usage item 8.
   ```

### Details
Both additions reference `rules/ai-execution.md` Repository Tool Usage item 8 by name rather
than restating its full text, consistent with this repository's cross-reference convention.

## Compatibility considerations
Documentation-only change to a skill's own procedure text; no code, schema, or runtime
behavior affected. Does not change `tools/generate_workitem.py`'s own output or exit-code
behavior (Plan Scope Out-of-Scope).

## Security considerations
N/A: no security-relevant content in a post-success verification clarification.

## Rollback considerations
Trivially revertable via `git revert`/`git checkout` of this single file.

## Validation plan
- Manual review: confirm the added instruction is consistent with `rules/ai-execution.md` Repository Tool Usage #8 and `rules/workflow-lifecycle.md` Archival Move's existing verification pattern (Plan `Tests`).

## Completion criteria
Step 5 and Step 6 each state that a `0` exit from `tools/generate_workitem.py` is followed by
an independent check that the output file exists and has the expected structure, before its
content is edited.

## Out of scope
Changing `tools/generate_workitem.py`'s own output or exit-code behavior (Plan Scope
Out-of-Scope). The equivalent gap in `plan-to-implementation-procedure/workflow.md`'s own tool
integration text, if confirmed there (Plan Scope Out-of-Scope — file separately).

## Documentation
Not a `docs/*.md` file; no `docs/00_index.md` task-scope mapping applies.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Add post-success check to Step 5 per Method | Completed | 2026-09-02 | 2026-09-02 | Verified lines 269-273 matched exactly |
| 2 | Add post-success check to Step 6 per Method | Completed | 2026-09-02 | 2026-09-02 | Verified lines 298-304 matched exactly |
| 3 | N/A: no test to add (doc-only change) | Completed | 2026-09-02 | 2026-09-02 | N/A |
| 4 | Manual review validation | Completed | 2026-09-02 | 2026-09-02 | Confirmed consistent with rules/ai-execution.md Repository Tool Usage item 8 and rules/workflow-lifecycle.md Archival Move's verification pattern |

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
- **Requirement ID**: REQ-001 (post-success verification for Step 5/6 tool scaffolding)
- **Source issue**: `issues/20260901-170327_itp009_tool_success_judged_by_exit_code_only.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20260901-220027_plan.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260902-153943
- **Related target files**: `skills/issue-to-plan/workflow.md`
