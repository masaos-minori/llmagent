## Goal
Satisfy `REQ-001`/`REQ-002` (ptip008): add post-success verification instructions to both
Step 3's `generate_workitem.py` integration and Step 4's `manage_workitem_stage.py close-plan`
integration in `skills/plan-to-implementation-procedure/workflow.md`.

## Scope
Modify exactly two locations in `skills/plan-to-implementation-procedure/workflow.md`: Step 3's
`generate_workitem.py --kind implementation-procedure` tool-call text (current lines 209-215)
and Step 4's `manage_workitem_stage.py close-plan` tool-call text (current lines 301-305). No
other line in this file is touched.

## Assumptions
- **Corrected 2026-09-02** (during this cycle's adversarial verification): the Plan's
  originally-cited evidence line numbers ("line 164-169" for Step 3, "line 27-33" for Step 4)
  did not match the actual tool-call text — re-verified against current source and corrected to
  lines 209-215 (Step 3) and 301-305 (Step 4); content and gap description are otherwise
  unchanged.

## Design decisions
Mirror `itp009`'s proposal (the same fix for `issue-to-plan`'s own tool integration) applied to
this workflow's two tool calls (Plan `Design`, corrected 2026-09-02 after this session found
the Plan's original Design section was copy-pasted from an unrelated sibling plan, ptip005).
For Step 4, explicitly restate the same post-move checklist `rules/workflow-lifecycle.md`
Archival Move already requires for the manual `git mv` fallback, rather than leaving it implied
only for that fallback path.

## Alternatives considered
Relying on `rules/ai-execution.md` Repository Tool Usage #8's general verification rule alone
(without a Step-specific restatement) — rejected: the Plan's Problem notes this general rule
does not stop an agent from treating a `0` exit as sufficient for these two specific tool calls,
since neither Step's own text currently prompts the independent check.

## Implementation
### Target file
skills/plan-to-implementation-procedure/workflow.md

### Procedure
Append a post-success verification instruction to both tool-call texts.

### Method
1. Locate Step 3's tool-call text (current lines 209-215):
   ```
   - Optionally scaffold the empty file first with `uv run python
     tools/generate_workitem.py --kind implementation-procedure --source-plan
     {plan_path} --target-file-path {target_file_path} --seq {seq}` — it reproduces
     `templates/implementation-procedure.md`'s current field order exactly, computes
     `target_file_slug` per the naming rule above, and shares this pass's timestamp
     automatically across every row's invocation (see Allowed file operations) rather
     than requiring the manual shared-timestamp step above.
   ```
   Append:
   ```
     After a `0` exit, independently verify the expected file exists at
     `implementations/{timestamp}_{seq}_{target_file_slug}.md` before proceeding — a `0`
     exit alone is not sufficient evidence per `rules/ai-execution.md` Repository Tool
     Usage #8.
   ```
2. Locate Step 4's tool-call text (current lines 301-305):
   ```
   Prefer `uv run python tools/manage_workitem_stage.py close-plan
   plans/{filename}_plan.md` over a direct `git mv` — it performs the same move and
   refuses (non-zero exit, no move) if the source is missing, the destination already
   exists, or the source has uncommitted changes. Fall back to the direct `git mv`
   command only if the tool is unavailable.
   ```
   Append:
   ```
   After a `0` exit, independently verify the same checklist `rules/workflow-lifecycle.md`
   Archival Move already requires for the manual `git mv` fallback: destination file
   exists, source file no longer exists, and the move is recorded as a Git rename — a `0`
   exit alone is not sufficient evidence per `rules/ai-execution.md` Repository Tool Usage
   #8, regardless of which path (tool call or manual fallback) performed the move.
   ```

### Details
Neither edit changes either tool's own output or exit-code behavior (Plan Scope
Out-of-Scope) — only what the workflow independently verifies afterward.

## Compatibility considerations
Documentation-only change to a skill's own procedure text; no code, schema, or runtime
behavior affected.

## Security considerations
N/A: no security-relevant content in a workflow-procedure verification clarification.

## Rollback considerations
Trivially revertable via `git revert`/`git checkout` of this single file.

## Validation plan
- Manual review: confirm the added instructions are consistent with `itp009`'s phrasing and with `rules/workflow-lifecycle.md` Archival Move (Plan `Tests`).

## Completion criteria
Step 3 states that a `0` exit is followed by an independent file-existence check; Step 4
states that the tool-call path is followed by the same post-move verification checklist the
manual `git mv` path already requires.

## Out of scope
Changing either tool's own output or exit-code behavior (Plan Scope Out-of-Scope).

## Documentation
Not a `docs/*.md` file; no `docs/00_index.md` task-scope mapping applies.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Add Step 3 post-success verification per Method | Pending | — | — | |
| 2 | Add Step 4 post-success verification per Method | Pending | — | — | |
| 3 | N/A: no test to add (doc-only change) | Pending | — | — | N/A |
| 4 | Manual review validation | Pending | — | — | |

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
- **Requirement ID**: REQ-001, REQ-002 (post-success verification for Step 3/Step 4 tool calls)
- **Source issue**: `issues/20260901-171500_ptip008_tool_success_judged_by_exit_code_only.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20260901-213910_plan.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260902-153539
- **Related target files**: `skills/plan-to-implementation-procedure/workflow.md`
