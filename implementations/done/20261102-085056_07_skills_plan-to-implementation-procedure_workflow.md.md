## Goal
- Make Step 2 call `tools/plan_dependency_order.py` and report its result without deciding the order, and make the generation and Step 4 text mark procedures of a gated Plan with the `Gated:` marker (`REQ-005`).

## Scope
- In scope: the Plan-level start conditions bullet on Dependencies, the Toolchain list, one marking instruction near Step 3c or Step 4, and the final report line.
- Out of scope: Step 3c classification, the Step 4 pre-move checklist, the `Work Items Created` paragraph, and `Step 3c` stale-detector text, which flowimp007, flowimp008, flowimp009, and flowimp011 edit.

## Assumptions
- Plan A2, A9. Step 3a verified (2026-11-02): the Dependency bullet is at lines 119 to 121 ("Report it and ask whether to proceed; do not decide the order here"); the Toolchain list names `check_plan_target_overlaps.py` for Step 2; the final report lists the Plan outcome, documents, caveats, and Step 3a edits.
- Overlap (Step 2): `plans/20261102-080336_flowimp002_plan-release-units.md` (copies the unit name into each procedure, Step 3c and Step 4), `flowimp007` (Step 3c item 2), `flowimp008` (Step 4 `Work Items Created` statement), `flowimp009` (companion conditions, Step 3c, Step 4 checklist), and `flowimp011` (Step 3c additional-target discovery) also edit this file. Judged compatible: this change edits Step 2's Dependency bullet, the Toolchain list, and adds a marking instruction; the textual neighbours in Step 4 are rebased by whichever Plan lands second.
- The rule that the owner decides the order stays; the start-condition stop (`Blocked`, report and ask) for a dependency stays, and the tool only supplies the answer to what is open.

## Design decisions
- Step 2: run `uv run python tools/plan_dependency_order.py --plan {plan_path}` after the overlap check; report each blocking item and any `Needs confirmation` or `prose-dependency` warning; a `gated` result still ends the cycle `Blocked` unless the owner says to proceed, in which case every procedure generated carries the marker.
- The marker is written while authoring each procedure (Notes of its pending rows start with `Gated: {blocking path} phase {N} - {reason}`), or with `set-step-status implementation-procedure {path} --step N Pending --notes "Gated: ..."` when the row's Notes is empty.

## Alternatives considered
- Letting the tool block the cycle: rejected, the tool recommends and never decides.

## Implementation
### Target file
`skills/plan-to-implementation-procedure/workflow.md`

### Procedure
- Replace the Dependency bullet text with a version that calls the tool, reports, and keeps "do not decide the order here".
- Add the tool to the Toolchain list (Step 2).
- Add a short marking paragraph at the end of Step 3c (after the Lightweight-fill bullet) and a final-report bullet: "each gated procedure and its blocking item".

### Method
- Keep every existing sentence that is not part of the Dependency bullet; use references to `templates/execution-status.md` for the marker definition (a section reference, not a restated rule).
- Avoid a new cross-file section cycle: reference `templates/execution-status.md` by file name only (`check_skills_heading_cycles.py` checks section references).

### Details
- State `Needs confirmation` for an unresolvable dependency, matching UNK-02.

## Compatibility considerations
- No change to document naming, classification, or the move gate; existing behavior without a structured line is the fallback warning.

## Security considerations
- N/A: skill text.

## Rollback considerations
- N/A: revert the commit.

## Validation plan
- `uv run python tools/check_skills_references.py`; `uv run python tools/check_skills_heading_cycles.py`.
- Read-through of one gated cycle: generate a procedure for a Plan with an open dependency and confirm the marker and the report.

## Completion criteria
- Step 2 calls the tool and reports without deciding; the marking instruction and final-report line exist; the skill states that the owner decides the order; both checkers pass.

## Out of Scope
- `code-implementation` Step 1 (row 08), the template definition (row 06), and the sibling Plans' edits.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 20261102-102117 | 20261102-102117 | Stale check clean. No correction. Files: skills/plan-to-implementation-procedure/workflow.md (Toolchain, Step 2 Dependency bullet, Step 3c marking bullet, Final report bullet) |
| 2 | Run the documentation checkers named in `routing.md` Tools "When to run which tool" | Completed | 20261102-102117 | 20261102-102117 | Documentation checkers named in `routing.md`, plus the one-cycle read-through check_skills_references and check_skills_heading_cycles: no issues; read-through of a gated cycle against live plan diagmask001 (tool reports gated (prose), blocking secmask001). Full suite deferred to plan end |

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
- **Requirement ID**: REQ-005 (Step 2 calls the tool and reports without deciding; Step 4 marks gated procedures)
- **Source issue**: issues/20261030-191144_flowimp003_plan-dependency-gate.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261102-080134_flowimp003_plan-dependency-gate.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261102-085056
- **Related target files**: skills/plan-to-implementation-procedure/workflow.md