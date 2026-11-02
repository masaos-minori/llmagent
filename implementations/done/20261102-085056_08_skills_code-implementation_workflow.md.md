## Goal
- Make `code-implementation` Step 1 recompute readiness with the tool and report gated procedures instead of starting them (`REQ-006`).

## Scope
- In scope: one new bullet in Step 1 and one Toolchain row.
- Out of scope: Step 2 stale detection, Step 4, Step 7, and Multi-file processing (edited by flowimp002, flowimp007, flowimp008, flowimp009, flowimp011).

## Assumptions
- Plan A2 and A9. Step 3a verified (2026-11-02): Step 1 holds the all-steps-completed check and the partial-completion resume bullets; the Toolchain table lists `close-implementation`, `set-step-status`, and the checkers; `close-implementation` refuses a Pending row, which a gated procedure keeps.
- Overlap (Step 2): `flowimp002`, `flowimp007`, `flowimp008`, `flowimp009`, and `flowimp011` also edit this file at other steps. Judged compatible: this change adds a Step 1 bullet and a Toolchain row; sequencing rebase of adjacent text only.
- The skill never clears a `Gated:` marker itself; the owner does.

## Design decisions
- Step 1 reads the procedure's `Source plan`, runs `uv run python tools/plan_dependency_order.py --plan {plan_path}`, and if the Plan is `gated`, or any pending row carries a `Gated:` Notes prefix, reports `Gated: {file} - {blocking item}` and does not start the procedure (the cycle ends for this file, reported, not `Blocked`).
- Readiness comes from the tool, not from the marker alone: a stale marker with a `ready` result is reported and the owner decides.

## Alternatives considered
- Auto-clearing the marker when the tool says `ready`: rejected, the owner decides.

## Implementation
### Target file
`skills/code-implementation/workflow.md`

### Procedure
- Add a bullet "Gated check" after the Partial-completion resume bullet in Step 1.
- Add the tool to the Toolchain table with Step `1`.

### Method
- Keep the bullet to a few sentences: how readiness is computed, what is reported, and that the owner decides the order and clears the marker.
- If the Source plan is already in `plans/done/`, pass that path to `--plan`; the tool accepts both locations.

### Details
- A procedure whose Plan is not found: report `Needs confirmation` and continue as before.

## Compatibility considerations
- Procedures of a Plan without dependencies behave exactly as before; Status vocabulary unchanged.

## Security considerations
- N/A: skill text.

## Rollback considerations
- N/A: revert the commit.

## Validation plan
- `uv run python tools/check_skills_references.py`; `uv run python tools/check_skills_heading_cycles.py`.
- Read-through of one gated cycle: a procedure with a `Gated:` row is reported and not started.

## Completion criteria
- Step 1 reports gated procedures instead of starting them, recomputes readiness with the tool, and states that the owner decides the order; both checkers pass.

## Out of Scope
- The planning-side marking (row 07) and the other steps of this workflow.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 20261102-102152 | 20261102-102152 | Stale check clean. Procedure claim that the tool accepts plans/done/ was false against row 01; fixed in tools/plan_dependency_order.py (--plan reports an archived Plan own readiness, test added, 36 passed). Files: skills/code-implementation/workflow.md (Toolchain row, Step 1 Gated check) |
| 2 | Run the documentation checkers named in `routing.md` Tools "When to run which tool" | Completed | 20261102-102152 | 20261102-102152 | Documentation checkers named in `routing.md`, plus the one-cycle read-through check_skills_references and check_skills_heading_cycles: no issues; read-through of an archived Plan (flowimp005) via --plan reports ready. Full suite deferred to plan end |

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
- **Requirement ID**: REQ-006 (Step 1 reports gated procedures instead of starting them)
- **Source issue**: issues/20261030-191144_flowimp003_plan-dependency-gate.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261102-080134_flowimp003_plan-dependency-gate.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261102-085056
- **Related target files**: skills/code-implementation/workflow.md