# Procedure: skills/issue-to-plan/workflow.md - the Dependencies rule in Step 5 and Step 8b

## Goal

State the one ordering rule where the Plan's Scope Dependencies are actually written (Step 5) and where overlaps are judged into Dependencies (Step 8b), so the workflow can no longer produce a prose line that gates a Plan by accident.

## Scope
**Release unit**: N/A: not part of a release unit

- Add the rule to Step 5's plan-writing guidance (the section that fills `templates/plan.md`'s Scope from the Issue). (REQ-002)
- Rewrite Step 8b's `sequencing dependency` branch: a sequencing dependency becomes a structured `Depends on` bullet, and the compatible-overlap recording names the other Plan by title or id in the Scope. (REQ-002)
- Keep the Step 4 mapping row (`| Dependencies | Scope (Dependencies), Risks ... |`) consistent with the new wording if it instructs prose copying; it maps, it does not instruct — re-read and confirm rather than edit by default.

## Assumptions

- This edit executes after the prerequisite Plan's Step 3 procedure executes (its Step 8b audit rewrite is already merged into the current section text; the prerequisite Plan is archived with Step 3 `In Progress`, re-verified 20261118): re-read the whole Step 8b section before editing (Plan Assumption and UNK-02).
- Guidance-only option is chosen; UNK-01 maintainer confirmation gates Phase 2 execution of this Plan's phases (the template edit first, then this one). (Plan Assumption)
- `skills/plan-to-implementation-procedure/workflow.md` Step 2 already reports each `prose-dependency` warning and asks the user (reference file, unchanged); this workflow must stay consistent with it.

## Design decisions

- Copy the canonical wording from `implementations/20261118-073315_01_templates_plan.md.md` verbatim into both steps (Plan Implementation Intent, one rule; AC-3 reviews that the three texts agree). AC-2 requires the template's wording in the workflow.
- In Step 8b, keep the three judgment branches (compatible / sequencing dependency / conflict) exactly as they are; only the recording target changes: `sequencing dependency` records `Assumptions` plus a `Depends on` bullet (not the prose line), and `compatible` names the other Plan by title or id where the Scope mentions it at all.
- Step 5 gains the rule as a bullet in the plan-writing list next to the template/scaffold guidance, because that is the moment the Scope is filled; the Step 4 mapping table row stays a mapping, not an instruction.

## Alternatives considered

- Put the rule only in `templates/plan.md`. Rejected: Step 8b is where the workflow actively instructs "add the other Plan to `Scope` Dependencies" — the exact instruction the Plan's incident shows producing false gates (Plan Problem).
- Add a mechanical check that a Scope prose line contains no paths. Rejected: the Plan chose guidance-only (Design, Option 1); the tool's fallback already reports such a line as a visible gate plus warning.

## Implementation

### Target file

`skills/issue-to-plan/workflow.md` (exists)

### Procedure

1. Re-read the Step 5 "Generate the Plan" bullets and the full Step 8b section (the prerequisite Plan's audit text is already in it).
2. In Step 5, add one bullet carrying the canonical wording, placed with the guidance that fills the template's Scope (after the scaffold bullet), stating that when the Issue's own Dependencies are copied, each ordering dependency becomes a `Depends on` bullet and each non-ordering mention is written by title or id.
3. In Step 8b, change the `sequencing dependency` branch from "record it in `Assumptions` and add the other Plan to `Scope` Dependencies" to "record it in `Assumptions` and add a structured `Depends on` bullet for the other Plan in `Scope`", and add to the `compatible` branch the clause that a Scope mention names the other Plan by title or id, never by path (the fallback reads every `plans/` or `issues/` `.md` path in that line as a phase `all` dependency).
4. Leave the `conflict` branch, the overlap-tooling sentences, and the freeze criteria untouched.
5. Confirm the Step 4 mapping row still reads as a mapping (no instruction to copy paths); if its wording contradicts the new rule, adjust only that cell's wording minimally.

### Method

Targeted edits inside the two step sections; no heading changes (the skills reference and heading-cycle checkers read this file's structure).

### Details

- The `Depends on` grammar referenced here is `templates/plan.md`'s bullet (the sibling template document defines the wording); the workflow cites it, it does not redefine it.

## Compatibility considerations

- Every future issue-to-plan run sees the new instruction; existing Plans' Scope text is untouched.
- The other files in the fallback chain (`skills/plan-to-implementation-procedure/workflow.md`, `skills/code-implementation/workflow.md`) are reference-only (Plan Reference Files); the tool's output they consume is unchanged.

## Security considerations

- None; documentation edit.

## Rollback considerations

- Reverting this file restores the previous step texts; no state involved. If the prerequisite Plan's Step 3 text must survive, revert only this Plan's edits (targeted re-edit) rather than the whole file.

## Validation plan

- `uv run python tools/check_skills_references.py` and `uv run python tools/check_skills_heading_cycles.py` pass (AC-6).
- Review against AC-2: Step 5 and Step 8b carry the template's wording and Step 8b names the `Depends on` bullet.
- Cross-text review (AC-3): template, workflow, and tool-row wording match (sibling documents).

## Completion criteria

- AC-2: Step 5 and Step 8b state the rule in the template's wording; the sequencing branch records a `Depends on` bullet.
- AC-6: the skills checkers pass.

## Out of Scope

- `tools/plan_dependency_order.py` and its docstring/warning text (unchanged, REQ-005).
- `skills/plan-to-implementation-procedure/workflow.md` and `skills/code-implementation/workflow.md` (reference only).
- How overlaps are reported (report-only) and new dependency kinds.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | |
| 2 | Add or update tests per Validation plan | Pending | — | — | |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Pending | — | — | |

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
- **Requirement ID**: REQ-002, REQ-006
- **Source issue**: issues/20261117-132205_wftoolfu005_plan-prose-dependency-gating.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261117-134609_wftoolfu005_plan-prose-dependency-gating.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261118-073315
- **Related target files**: `skills/issue-to-plan/workflow.md`
