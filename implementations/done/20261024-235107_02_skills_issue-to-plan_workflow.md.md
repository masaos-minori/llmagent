## Goal
- Point the issue-to-plan cycle at the strengthened Context Reading and Tool Usage rules without restating them (`REQ-002`: reference from `issue-to-plan` execution rules).

## Scope
- One reference sentence in `## Multi-file processing` of `skills/issue-to-plan/workflow.md` (line 63 area at time of writing).

## Assumptions
- Line 63 currently reads `Apply rules/ai-execution.md Context Reading and Progress Reporting (Base) ...`; Tool Usage is cited only in the cycle-isolation bullet (lines 59-61) (read 2026-10-24).
- Overlap: `skills/issue-to-plan/workflow.md` is also a target of the Plans `plans/20261024-220231_bound-adversarial-verification-cost.md` and `plans/20261024-232610_lightweight-path-a-plan-template.md`; this is a sequencing dependency (compatible edits, different sections). Re-read the file and re-anchor immediately before editing.
- Row `01` (`rules/ai-execution.md`) is applied first so the referenced wording exists.

## Design decisions
- Extend the existing `Apply rules/ai-execution.md Context Reading ...` sentence to name `Tool Usage`; add no MUST sentences here.

## Alternatives considered
N/A: single-sentence edit; placement decided in the Plan Design.

## Implementation
### Target file
`skills/issue-to-plan/workflow.md`

### Procedure
1. Edit the sentence at `## Multi-file processing` so it applies `rules/ai-execution.md` Context Reading and Tool Usage (not only Progress Reporting) to the per-cycle load and call discipline.

### Method
- Reference by section name only; do not copy the new MUST wording.

### Details
- The cycle-isolation bullet (lines 59-61) stays unchanged: conclusions are still not carried between cycles.

## Compatibility considerations
N/A: wording-only reference.

## Security considerations
N/A: instruction text only.

## Rollback considerations
N/A: revert the commit.

## Validation plan
- `uv run python tools/check_skills_references.py`
- `uv run python tools/check_skills_heading_cycles.py`
- `rg` for the new MUST sentences from row `01` matches only `rules/ai-execution.md`.

## Completion criteria
- The Multi-file processing section references Context Reading and Tool Usage by name with no copied rule text; both checkers exit 0; no Step 0 load set changed.

## Out of Scope
- Step 0 load sets, other sections, and the sibling Plans' edits.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Add the reference sentence in `## Multi-file processing` | Completed | — | 20261025-001708 |  |
| 2 | Run both skills checkers and the `rg` no-restatement check | Completed | — | 20261025-001708 |  |

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
- **Requirement ID**: `REQ-002` (reference from `issue-to-plan` execution rules)
- **Source issue**: issues/20261024-185427_perf001_cut-redundant-rereads-and-turn-overhead.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261024-215858_cut-redundant-rereads-and-turn-overhead.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261024-235107
- **Related target files**: `skills/issue-to-plan/workflow.md`