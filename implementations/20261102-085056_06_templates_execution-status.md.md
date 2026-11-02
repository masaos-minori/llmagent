## Goal
- Define the `Gated:` Notes prefix for a procedure of a gated Plan without adding a Status value (`REQ-003`).

## Scope
- In scope: one bullet in `## Notes` and, optionally, one sentence after the `Status options` line.
- Out of scope: the Status vocabulary, `_VALID_STATUSES`, and the parsers.

## Assumptions
- Plan A2 and A9. Step 3a verified (2026-11-02): the template line reads `Status options: Pending / In Progress / Blocked / Completed`; `_VALID_STATUSES` in `tools/manage_workitem_stage.py` is the same four values.
- Step 3a correction recorded in the Plan: `set-step-status --notes` appends to the Notes cell with a space (`update_execution_status`), so a prefix results only when the row's Notes is empty; the template states the rule as "the Notes cell starts with `Gated:`".
- Overlap (Step 2): no other Plan targets this file.

## Design decisions
- Marker format: `Gated: {blocking path} phase {N or all} - {reason}`, Status stays `Pending`; `Blocked` is for a started row that hit a blocker and does not fit a row that never started.
- The marker is informational: removing it is the owner's act, never `code-implementation`'s.

## Alternatives considered
- A fifth Status value: rejected, every parser of the four values would change.

## Implementation
### Target file
`templates/execution-status.md`

### Procedure
- Add one bullet to `## Notes` defining the `Gated:` prefix: when it is written (by `plan-to-implementation-procedure` for procedures of a gated Plan), its format, that Status stays `Pending`, that the Notes cell starts with the prefix, and that only the owner clears it.
- Leave the fenced template and `Status options` line unchanged.

### Method
- Place the bullet after the Resolved-column bullet; no code fence is changed.

### Details
- State that readiness is recomputed by `tools/plan_dependency_order.py`, so a stale marker never overrides the tool.

## Compatibility considerations
- Status vocabulary unchanged; existing documents without the prefix are valid.

## Security considerations
- N/A: template text.

## Rollback considerations
- N/A: revert the commit.

## Validation plan
- `uv run python tools/check_skills_references.py`; `uv run python tools/check_skills_heading_cycles.py`; `uv run python tools/check_workitem_structure.py --file {a Plan or procedure carrying a Gated: Notes cell}`.

## Completion criteria
- The template defines `Gated:` as a Notes prefix with Status `Pending`, states who writes and clears it, and adds no Status value.

## Out of Scope
- The tool (row 01), the skill steps that write the marker (rows 07, 08).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — |  |
| 2 | Run the documentation checkers named in `routing.md` Tools "When to run which tool" | Pending | — | — | Documentation checkers named in `routing.md` |

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
- **Requirement ID**: REQ-003 (gated marker defined as a `Notes` prefix, no new Status value)
- **Source issue**: issues/20261030-191144_flowimp003_plan-dependency-gate.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261102-080134_flowimp003_plan-dependency-gate.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261102-085056
- **Related target files**: templates/execution-status.md
