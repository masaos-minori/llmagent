## Goal

- Replace the line-number reference in the `ALL_SIDE_EFFECTING_TOOLS` comment with a reference to the module docstring (`REQ-004`).

## Scope
**Release unit**: N/A: not part of a release unit

- Plan step 4. A comment-only change.

## Assumptions

- Lines 4-21 of the file are the module docstring that states that the sets are not a routing source (checked in the plan-to-implementation-procedure cycle).

## Design decisions

- Name the section (the module docstring), not a line range.

## Alternatives considered

N/A: a text edit; the Plan fixes the change.

## Implementation
### Target file
`scripts/shared/tool_constants.py`
### Procedure
1. Replace `Routing authority remains this module's header (lines 4-21)` with `Routing authority remains this module's docstring`.
### Method
- Direct comment edit.
### Details
- No code change.

## Compatibility considerations

N/A: comment only.

## Security considerations

N/A: comment only; no behavior change.

## Rollback considerations

N/A: revert the commit.

## Validation plan

- `uv run ruff format scripts/shared/tool_constants.py` and `uv run ruff check scripts/shared/tool_constants.py`.
- `uv run pytest tests/shared -q`.

## Completion criteria

- The comment contains no line number (AC-2).

## Out of Scope

- The tool sets themselves.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Replace the line-number reference (Plan step 4) | Pending | — | — |  |
| 2 | Run the validation sequence for this row (Validation plan) | Pending | — | — | |

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
- **Requirement ID**: `REQ-004` (script comment)
- **Source issue**: issues/20261117-123012_adrchk012_traceability-id-uniqueness.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261120-124329_adrchk012_traceability-id-uniqueness.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261120-125111
- **Related target files**: `scripts/shared/tool_constants.py`
