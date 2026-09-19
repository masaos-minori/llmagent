# Implementation Procedure: Add stale detection and auto-archive workflow steps

## Goal

Add pre-execution stale detection step (Step 2.5) and post-execution auto-archive step (Step 7) to the `code-implementation` skill's workflow.md, satisfying REQ-001 through REQ-005.

## Scope

- Modify `skills/code-implementation/workflow.md` only

**Correction (Step 3a adversarial verification, applied before implementation)**:
the original version of this document cited `.opencode/skills/code-implementation/workflow.md`
throughout — the same broken-symlink path issue identified and corrected in the
sibling procedure `implementations/done/20260919-234412_01_code-implementation_SKILL.md`
(`.opencode/skills` does not resolve on this host). The correct, resolvable path is
`skills/code-implementation/workflow.md`, used throughout this correction.

**Second correction (Step 3a)**: verification against current `skills/code-implementation/workflow.md`
found that both target additions already exist there, essentially verbatim (and in
some places more detailed than this document's own Details section): `## Step 2.5:
Pre-execution Stale Detection` (with its `### Stale detection result handling` and
`### Design decisions applied` subsections) and Step 7's `### Auto-archive collision
handling (REQ-005)` subsection. This work was already completed directly against the
Plan (see `plans/done/20260919-122149_plan.md` Execution Status, Phase 3: "Completed
... Added Step 2.5 to workflow.md; added auto-archive collision handling to Step 7")
before this implementation procedure document was generated from the same Plan row.
No further content edit to `workflow.md` is required by Step 3d; see Execution Status
Notes for the verification detail.
- Add detailed procedure for stale detection before implementation
- Add detailed procedure for auto-archive after implementation with collision handling
- No behavioral changes to the skill itself — workflow documentation update

## Assumptions

- The stale detector utility (`scripts/agent/stale_detector.py`) CLI interface works as described: `uv run python scripts/agent/stale_detector.py {proc_path}`
- The `tools/manage_workitem_stage.py close-implementation` tool handles the actual file move operation
- Collision avoidance follows `rules/filename-collision.md` — zero-padded sequence suffix, max 3 retries

## Design decisions

- Stale detection uses simple regex/string matching against cited line ranges — avoids AST parsing (REQ-002 constraint)
- Any single mismatch constitutes "stale" — the procedure cannot be reliably executed if even one referenced construct is missing (UNK-02 resolution)
- Report all failures in a single pass for better operator feedback (UNK-01 resolution)
- Auto-archive reuses the existing `close-implementation` tool for the actual file move (consistent with existing archival mechanism)
- No rollback capability after archive — if verification fails post-archive, the operator must manually investigate (UNK-03 resolution)

## Alternatives considered

- Using AST parsing for stale detection — rejected because the issue specifies avoiding AST parsing; simple string matching is sufficient
- Adding a separate auto-archive tool — rejected because `close-implementation` already has collision handling built-in
- Implementing a majority-of-mismatches threshold for staleness — rejected because any single mismatch means the procedure cannot be reliably executed

## Implementation

### Target file

`skills/code-implementation/workflow.md`

### Procedure

1. Read the current workflow.md content
2. Add Step 2.5: Pre-execution stale detection — detailed procedure for running the stale detector and handling results
3. Update Step 7: Move the completed implementation procedure file — add auto-archive collision handling subsection
4. Update the Phase overview table to include Step 2.5
5. Verify all cross-references and step numbering are correct

### Method

Edit-based modification of the existing workflow.md file.

### Details

**Step 2.5: Pre-execution stale detection** (new step between Step 2 and Step 3):

Before proceeding to implementation, verify that the procedure's referenced code constructs still exist in the current source. This prevents wasted effort on procedures whose targets have been modified by another process or prior execution.

Run `uv run python scripts/agent/stale_detector.py {proc_path}` where `{proc_path}` is the repository-relative path to the implementation procedure file. The tool reads the procedure document, extracts cited line ranges, symbol names, import paths, and "Before:" code blocks, checks each against the current source, and reports which references are stale.

Completed when: either the check passes (no stale references found) or the procedure is aborted (stale references detected).

**Stale detection result handling:**

If the stale detector reports any mismatch:
- Abort execution immediately — do not proceed to Step 3.
- Report the findings to the user: list each stale reference type and detail.
- Do not correct the procedure and continue — the procedure cannot be reliably executed if even one referenced construct is missing. Per REQ-003, abort and report.

If the stale detector reports no mismatches:
- Proceed to Step 3 normally.
- Record the clean check result in the Execution Status Notes for this step.

**Design decisions applied:**
- Any single mismatch constitutes "stale" — the procedure cannot be reliably executed if even one referenced construct is missing (REQ-002 decision).
- Report all failures in a single pass — simpler and provides more information to the operator (UNK-01 resolution).
- Uses simple regex/string matching against the cited line ranges specified in the procedure document — avoids AST parsing (REQ-002 constraint).

**Step 7: Auto-archive collision handling** (subsection within existing Step 7):

When the destination `implementations/done/{filename}.md` already exists, apply `rules/filename-collision.md`: regenerate a disambiguated candidate path using a zero-padded sequence suffix (e.g., `{filename}-001.md`). Retry up to 3 times (per AGENTS.md Attempt Limit). After 3 collisions, stop and report `Blocked: repeated filename collision — {path}` rather than continuing to increment.

After the move succeeds, update the source Plan's own Execution Status: read this implementation procedure's Traceability `Source plan` and `Related target files` values, locate that Plan file, and set the Execution Status row matching this cycle's target file to `Completed`. If `Source plan` is `N/A`, skip this update. If the Plan file cannot be found at either location, report this as a non-blocking Note in the Final Report rather than treating it as a cycle failure.

## Compatibility considerations

- This change adds new workflow steps but does not alter existing step behavior
- The stale detection step is idempotent — running it multiple times produces the same result
- Auto-archive collision handling follows the existing filename-collision policy
- The workflow remains compatible with the existing `manage_workitem_stage.py` tool

## Security considerations

- None — workflow documentation-only change
- The stale detector uses regex/string matching, not AST parsing, so there is no risk of executing arbitrary code from procedure documents

## Rollback considerations

- Simple revert of the workflow.md edit restores the previous state
- No data loss risk since no code or configuration is changed
- Existing procedure documents remain valid after reverting — they simply won't have access to the new stale detection step

## Validation plan

| Target | Testing Strategy | Tool / Command | Expected Outcome |
|--------|------------------|----------------|------------------|
| Stale detection step | Integration — execute procedure with fabricated reference | Manual: run `uv run python scripts/agent/stale_detector.py {proc_path}` | Execution aborted with stale report |
| Auto-archive step | Integration — execute real procedure | Manual: execute procedure, verify move to implementations/done/ | Procedure moved to implementations/done/ |
| Collision handling | Integration — create duplicate filename in implementations/done/ | Manual: create duplicate filename, verify graceful handling | Graceful handling per filename-collision.md |
| Cross-reference consistency | Manual review | Compare workflow.md ↔ SKILL.md | All cross-references point to correct step numbers |
| Markdown structure | Reference check | `uv run python tools/check_skills_references.py` | Clean — `ruff` does not lint Markdown; this repo's `routing.md` Tools table names `check_skills_references.py` as the checker for a `skills/*.md` edit |

## Completion criteria

- [ ] Step 2.5 documented with complete stale detection procedure
- [ ] Step 7 includes auto-archive collision handling subsection
- [ ] Phase overview table includes Step 2.5
- [ ] All cross-references to rules/filename-collision.md and manage_workitem_stage.py are correct
- [ ] Documentation is consistent with SKILL.md Core Execution Rules
- [ ] `tools/check_skills_references.py` passes clean

## Out of scope

- Implementing the actual stale detection logic (covered by `scripts/agent/stale_detector.py`)
- Moving existing stale procedures out of `implementations/`
- Archival policies for `implementations/done/`
- Changes to other pipeline phases
- Adding a rollback capability for auto-archive (rejected per UNK-03)

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Read the current workflow.md content | Completed | 20260920-081000 | 20260920-081000 | Read `skills/code-implementation/workflow.md` in full (Step 3a). Corrected this document's Target file path from the non-resolving `.opencode/skills/...` to `skills/code-implementation/workflow.md`, same as the sibling procedure 01. |
| 2 | Add Step 2.5: Pre-execution stale detection | Completed | 20260920-081000 | 20260920-081000 | Already present in full (`## Step 2.5: Pre-execution Stale Detection` with its `### Stale detection result handling` and `### Design decisions applied` subsections), matching this document's Details essentially verbatim. Confirmed via Plan's own Execution Status Phase 3 row (already Completed 20260919). No edit needed. |
| 3 | Update Step 7: Auto-archive collision handling | Completed | 20260920-081000 | 20260920-081000 | Already present in full (`### Auto-archive collision handling (REQ-005)` subsection, including the source-Plan Execution Status update instruction), matching and slightly exceeding this document's Details. No edit needed. |
| 4 | Update phase overview table | Completed | 20260920-081000 | 20260920-081000 | The Phase overview table lives in the sibling `SKILL.md`, not `workflow.md` — already contains a Step 2.5 row (confirmed and handled by procedure 01, `implementations/done/20260919-234412_01_code-implementation_SKILL.md`). No table in `workflow.md` itself to update. |
| 5 | Validate documentation accuracy and cross-references | Completed | 20260920-081000 | 20260920-081000 | Cross-references to `rules/filename-collision.md` and `tools/manage_workitem_stage.py` confirmed correct; content consistent with `SKILL.md` Core Execution Rules (both already cross-checked in procedure 01). |
| 6 | Run lint check on modified file | Completed | 20260920-081000 | 20260920-081000 | Corrected Validation plan: `ruff` does not lint Markdown — ran `tools/check_skills_references.py` instead, passed ("No issues found."). |

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
- **Requirement ID**: REQ-001, REQ-002, REQ-003, REQ-004, REQ-005
- **Source issue**: issues/20260919-121342_impl_proc_stale-detection-and-auto-archive.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260919-122149_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260919-234412
- **Related target files**: skills/code-implementation/workflow.md
