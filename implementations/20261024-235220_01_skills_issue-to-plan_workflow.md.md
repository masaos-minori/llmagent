## Goal
- Bound verification cost in `skills/issue-to-plan/workflow.md`: a same-cycle dedup rule (`REQ-001`), a depth ceiling with two expansion triggers (`REQ-002`), and a per-row `(checked in Step N)` evidence tag consumed by Step 8b (`REQ-003`), with no verification criterion weakened.

## Scope
- Edit Step 2 (line 130 onward), Step 3 (line 182 onward), Step 5's `Repository Evidence` bullet (line 350), and Step 8b (line 505 onward) at time of writing.
- No change to `rules/`, `templates/plan.md`, or any Plan table column.

## Assumptions
- Anchors confirmed 2026-10-24: Step 2 stop-rule bullet (line 143), Step 5 bullet ending "MUST NOT infer it." (line 350), Step 8b opening paragraph (line 508).
- Overlap judged in the Plan Assumptions: Plan `plans/20261024-232610_lightweight-path-a-plan-template.md` edits Step 4, Step 5 generation bullets, and Step 8a; the archived perf001 Plan edits `## Multi-file processing`. These are sequencing dependencies, compatible. Re-read the file and re-anchor immediately before editing.
- Step 6 performs no per-row verification (Plan Assumptions); the dedup applies to Steps 2-3 versus Step 8b.

## Design decisions
- The evidence tag lives in the existing `Repository Evidence` column as a `(checked in Step N)` suffix; no template column is added.
- Base investigation order is referenced by section name (`rules/ai-execution.md` Adversarial Verification (Base)), never copied.

## Alternatives considered
- A new `Verified by step` column and a separate verification log were rejected in the Plan Design (template and parser blast radius).

## Implementation
### Target file
`skills/issue-to-plan/workflow.md`

### Procedure
1. Step 2: add a dedup bullet. A claim, target file, or row already verified this cycle MUST NOT be verified again unless (a) a command in this cycle modified the file, (b) path-scoped `git status --short -- <path>` or `git log -1 --format=%H -- <path>` shows a change since the check, or (c) the earlier check was inconclusive (`Needs confirmation`).
2. Step 2 and Step 3: add the depth ceiling. Investigation stays within the base order; it MAY expand only when (a) a disconfirming finding inside the order points outside it, or (b) a target row cannot meet a Freeze criterion inside the order; any other unsettled item is `Needs confirmation`.
3. Step 5: extend the `Repository Evidence` bullet so each entry also carries the step that performed the check, for example `(checked in Step 3)`.
4. Step 8b: state that a row whose existence and evidence were recorded this cycle is validated from that record while all four Freeze criteria still apply; a row without a tag falls back to the existing check.

### Method
- Reference `rules/ai-execution.md` and `rules/workflow-lifecycle.md` by section name; add no heading that creates a cross-file heading cycle.

### Details
- Keep the existing Step 2 stop rule and the Correction-and-Recheck Cycle Bound reference unchanged.
- Do not edit the Step 8b overlap-check paragraph.

## Compatibility considerations
- Existing Plans stay valid: the tag is additive text and no checker parses it.
- `tools/generate_workitem.py` and `tools/check_plan_target_overlaps.py` parse the table by heading and separator row; their input shape is unchanged.

## Security considerations
N/A: instruction text only.

## Rollback considerations
N/A: revert the commit.

## Validation plan
- `uv run python tools/check_skills_references.py` and `uv run python tools/check_skills_heading_cycles.py` exit 0.
- `rg` for the base-order wording shows it is not copied into the workflow.
- `git diff --stat` shows no change under `rules/` or `templates/`; no Step 8 check removed.
- A generated Plan passes `uv run python tools/check_workitem_structure.py --file <plan>`.

## Completion criteria
- Steps 2, 3, 5, and 8b state `REQ-001` to `REQ-003` as above, the four Freeze criteria and the correction bound are unchanged, and both checkers exit 0.

## Out of Scope
- `rules/` text, `templates/plan.md`, the Step 0 load set, and perf001/perf003 edits.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Add the dedup rule and depth ceiling to Steps 2-3 | Pending | — | — | |
| 2 | Add the evidence tag to Step 5 and make Step 8b consume it | Pending | — | — | |
| 3 | Run both skills checkers and the `rg` and `git diff` checks | Pending | — | — | |

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
- **Requirement ID**: `REQ-001` (same-cycle dedup), `REQ-002` (depth ceiling), `REQ-003` (evidence tag consumed by Step 8b)
- **Source issue**: issues/20261024-185557_perf002_bound-adversarial-verification-cost.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261024-220231_bound-adversarial-verification-cost.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261024-235220
- **Related target files**: `skills/issue-to-plan/workflow.md`
