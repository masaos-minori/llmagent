## Goal
- State the Path A collapse condition (Steps 4 and 5), the Step 8a acceptance of a compliant `N/A` section, and the Path A sizing rule (Steps 5 and 8a) in `skills/issue-to-plan/workflow.md` (`REQ-002`: collapse condition and 8a acceptance; `REQ-004`: sizing rule).

## Scope
- Step 4 (after "No requirement information may remain unmapped", line 264 at time of writing), Step 5 generation bullets, and Step 8a (line 475 onward).
- No change to the four Freeze criteria, Step 0, or Step 8b.

## Assumptions
- Anchors confirmed 2026-10-24: Step 4 sentence at line 264; Step 8a "Verify the Plan preserves: ..." at line 477 and its `Completed when` paragraph.
- Overlap: also edited by `plans/20261024-220231_bound-adversarial-verification-cost.md` (Steps 2, 3, 5 evidence bullet, 8b; procedures `implementations/20261024-235220_01_skills_issue-to-plan_workflow.md.md`) and the archived perf001 Plan (`## Multi-file processing`). Sequencing dependency, compatible; re-read the file and re-anchor immediately before editing, and place the new Step 5 bullets after the evidence bullet rather than inside it.
- This row depends on the `templates/plan.md` note (row `01`), which it references by section name.
- Caveat (non-blocking `Needs confirmation`, Plan REQ-004 and UNK-05): the sizing threshold reuses the existing Path A boundary (at most 3 target files); owner confirmation is pending and the wording MUST NOT introduce a new number.

## Design decisions
- Collapse condition stated once in Step 4 (mapping) and referenced from Step 5 and Step 8a.
- Step 8a accepts an `N/A: {reason}` section only when the condition holds; the existing preserved-information list is unchanged.

## Alternatives considered
N/A: mechanism decided in the Plan Design.

## Implementation
### Target file
`skills/issue-to-plan/workflow.md`

### Procedure
1. Step 4: after the "No requirement information may remain unmapped" paragraph, add that for Path A a Plan section listed as collapsible in `templates/plan.md` may be written as `N/A: {short reason}` only if the Issue has no content for it or its content is carried in a named other section, and the collapsed line keeps any statement this workflow requires of the section.
2. Step 5: add one bullet referencing that condition for generation, and one bullet with the sizing rule: a Plan classified Path A whose `Implementation Target Files` has more than 3 rows, or which meets a Path B criterion in `SKILL.md` Routing, is reclassified to Path B or split into separate Issues before freezing.
3. Step 8a: state that a compliant `N/A: {reason}` section satisfies the preserved-information check, a non-compliant one fails it, and repeat the sizing check once.

### Method
- Reference `templates/plan.md` and `SKILL.md` Routing by name; copy no list of sections.

### Details
- Keep the `Affected areas` six-column check and the `Risks` check unchanged (those sections stay filled).

## Compatibility considerations
- Path B behavior and every existing Plan remain valid; only Path A gains the option to collapse.

## Security considerations
N/A: instruction text only.

## Rollback considerations
N/A: revert the commit.

## Validation plan
- `uv run python tools/check_skills_references.py` and `uv run python tools/check_skills_heading_cycles.py` exit 0.
- `git diff` shows no change under `rules/` and no removed Step 8a check.

## Completion criteria
- Steps 4, 5, and 8a state the collapse condition, the 8a acceptance, and the sizing rule with the existing 3-file threshold; both checkers exit 0.

## Out of Scope
- Steps 2, 3, 8b, template content, and `SKILL.md` wording (separate row).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Add the collapse condition to Step 4 and Step 5 | Completed | 20261025-003317 | 20261025-003334 |  |
| 2 | Add the sizing rule to Step 5 and the `N/A` acceptance and sizing check to Step 8a | Completed | — | 20261025-003334 |  |
| 3 | Run both skills checkers and review `git diff` | Completed | — | 20261025-003334 |  |

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
- **Requirement ID**: `REQ-002` (collapse condition, 8a acceptance), `REQ-004` (Path A sizing rule)
- **Source issue**: issues/20261024-185701_perf003_lightweight-path-a-plan-template.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261024-232610_lightweight-path-a-plan-template.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261024-235623
- **Related target files**: `skills/issue-to-plan/workflow.md`