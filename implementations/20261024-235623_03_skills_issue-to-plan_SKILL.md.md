## Goal
- Reword "MUST NOT omit any section" in `skills/issue-to-plan/SKILL.md` Output format so every heading stays but a Path A Plan may collapse listed sections, and add the Path A sizing rule to Routing (`REQ-003`: Output format wording; `REQ-004`: sizing rule).

## Scope
- Output format sentence (line 136 at time of writing) and the `### [Path A] Small Task` criteria block in Routing (lines 73-83).
- Phase overview rows are not touched here.

## Assumptions
- Confirmed 2026-10-24: line 136 contains `MUST NOT omit any section.`; Path A criteria start with `- [ ] Affects ≤ 3 files`.
- Overlap: `plans/20261024-220231_bound-adversarial-verification-cost.md` edits only the Phase overview rows 2, 5, 8 of this file (procedure `implementations/20261024-235220_02_skills_issue-to-plan_SKILL.md.md`); compatible. Re-anchor before editing.
- Row `01` (`templates/plan.md`) and row `02` (`skills/issue-to-plan/workflow.md`) are applied first so the referenced note and rule exist.
- Caveat (non-blocking `Needs confirmation`, Plan REQ-004 and UNK-05): the sizing threshold is the existing Path A boundary (at most 3 files); no new number.

## Design decisions
- Replace the absolute sentence with: every `##` heading of `templates/plan.md` MUST be present; a Path A Plan MAY collapse the sections the template's Path A collapse note lists to `N/A: {short reason}` under the condition in `workflow.md` Step 4.
- Routing states that a Plan classified Path A with more than 3 target rows is reclassified to Path B or split.

## Alternatives considered
N/A: wording-only edit; mechanism decided in the Plan Design.

## Implementation
### Target file
`skills/issue-to-plan/SKILL.md`

### Procedure
1. Replace `MUST NOT omit any section.` in Output format with the reworded sentence above.
2. In Routing under `[Path A] Small Task`, add one line stating the sizing rule and the reclassify-or-split outcome.

### Method
- Reference `templates/plan.md` and `workflow.md` Step 4 by name only.

### Details
- Keep "update it as scope changes" and the rest of the Output format paragraph unchanged.

## Compatibility considerations
N/A: wording only; Path B text unchanged.

## Security considerations
N/A: instruction text only.

## Rollback considerations
N/A: revert the commit.

## Validation plan
- `uv run python tools/check_skills_references.py` and `uv run python tools/check_skills_heading_cycles.py` exit 0.

## Completion criteria
- `SKILL.md` no longer says every section must be filled, states that every heading stays, and carries the sizing rule in Routing.

## Out of Scope
- Phase overview rows, `workflow.md`, and `templates/plan.md`.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Reword the Output format sentence | Pending | — | — | |
| 2 | Add the sizing rule to Routing | Pending | — | — | |
| 3 | Run both skills checkers | Pending | — | — | |

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
- **Requirement ID**: `REQ-003` (Output format wording), `REQ-004` (Path A sizing rule)
- **Source issue**: issues/20261024-185701_perf003_lightweight-path-a-plan-template.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261024-232610_lightweight-path-a-plan-template.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261024-235623
- **Related target files**: `skills/issue-to-plan/SKILL.md`
