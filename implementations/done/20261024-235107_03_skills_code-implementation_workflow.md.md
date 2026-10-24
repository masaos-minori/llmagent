## Goal
- Point the code-implementation cycle at the strengthened Context Reading and Tool Usage rules without restating them (`REQ-003`: reference from `code-implementation` execution rules).

## Scope
- One reference sentence in `## Multi-file processing` of `skills/code-implementation/workflow.md` (line 81 area at time of writing).

## Assumptions
- Line 81 currently reads `Apply rules/ai-execution.md Progress Reporting (Base) for the per-step report cadence`; Context Reading is cited separately at line 150 (read 2026-10-24).
- Overlap: `skills/code-implementation/workflow.md` is also a target of `plans/20261024-233036_bound-verification-sequence-cost.md` and `plans/20261024-233356_cut-blocking-question-waits.md`; this is a sequencing dependency (different sections, compatible). Re-read and re-anchor immediately before editing.
- Row `01` is applied first so the referenced wording exists.

## Design decisions
- Add one sentence applying `rules/ai-execution.md` Context Reading and Tool Usage to the per-cycle load and call discipline; add no MUST sentences here.

## Alternatives considered
N/A: single-sentence edit; placement decided in the Plan Design.

## Implementation
### Target file
`skills/code-implementation/workflow.md`

### Procedure
1. In `## Multi-file processing`, add or extend a sentence so it applies `rules/ai-execution.md` Context Reading and Tool Usage alongside the existing Progress Reporting reference.

### Method
- Reference by section name only.

### Details
- `Step 3d`'s single `git status --short` baseline (line 288) stays unchanged.

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
- The section references Context Reading and Tool Usage by name with no copied rule text; both checkers exit 0.

## Out of Scope
- Validation-sequence and question-wait changes owned by sibling Plans.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Add the reference sentence in `## Multi-file processing` | Completed | — | 20261025-001709 |  |
| 2 | Run both skills checkers and the `rg` no-restatement check | Completed | — | 20261025-001709 |  |

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
- **Requirement ID**: `REQ-003` (reference from `code-implementation` execution rules)
- **Source issue**: issues/20261024-185427_perf001_cut-redundant-rereads-and-turn-overhead.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261024-215858_cut-redundant-rereads-and-turn-overhead.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261024-235107
- **Related target files**: `skills/code-implementation/workflow.md`