## Goal

`REQ-004`: correct `maintenance.py`'s module docstring, which still describes
`rotate_all_dbs()` as archiving only three databases after REQ-001/REQ-002 extend it to
four.

## Scope

- **In-Scope**: edit the module docstring's "Typical maintenance schedule" line
  (`scripts/db/maintenance.py:16`) from `rotate_all_dbs()  # archives rag, session, and
  workflow` to reflect the 4DB structure.
- **Out-of-Scope**: any other line in the docstring or any function body in this file
  — this Requirement is a comment-only correction.

## Assumptions

- Confirmed via Read (`scripts/db/maintenance.py:1-18`) that line 16 is the only
  reference to `rotate_all_dbs()`'s DB count in this file (`rg "rotate_all_dbs"
  scripts/db/maintenance.py` — this file only imports/calls other maintenance
  functions, not `rotate_all_dbs()` itself; the reference is comment-only, inside the
  module docstring's schedule table).
- Depends on `scripts/db/rotation.py`'s `rotate_all_dbs()` extension (REQ-001/REQ-002)
  — apply this edit consistently with (though not strictly after) that change, since
  this is a documentation-only correction with no runtime dependency.

## Design decisions

- Replace `rotate_all_dbs()  # archives rag, session, and workflow` with
  `rotate_all_dbs()  # archives rag, session, workflow, and eventbus` — minimal wording
  change, same inline-comment style.

## Alternatives considered

- N/A — single-line comment correction with no design choice beyond matching the new
  4DB reality.

## Implementation

### Target file
`scripts/db/maintenance.py`

### Procedure
1. Edit line 16's inline comment per Design decisions.

### Method
Single-line comment text replacement inside the module docstring; no code change.

### Details
- Do not alter any other line of the "Typical maintenance schedule" table or any other
  part of the docstring.

## Compatibility considerations

N/A: comment-only change, no behavior affected.

## Security considerations

N/A: documentation correction only.

## Rollback considerations

- Revert the comment to "archives rag, session, and workflow".

## Validation plan

| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| `scripts/db/maintenance.py` | N/A: comment-only | `rg "archives rag, session, and workflow" scripts/db/maintenance.py` | No match after the edit |

## Completion criteria

- Line 16's comment reflects the 4DB (rag, session, workflow, eventbus) structure.

## Out of scope

- `scripts/db/rotation.py`'s implementation — see the companion implementation
  procedure document for REQ-001/REQ-002.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Correct the docstring's `rotate_all_dbs()` schedule-line comment | Pending | — | — | |
| 2 | Documentation update | Completed by Step 1 | — | — | This document's entire purpose is the documentation update itself |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| Assumption | scripts/db/rotation.py's rotate_all_dbs() currently archives only 3 databases (rag, session, workflow). eventbus not added. Procedure assumption conflicts with actual code. | No | 2026-08-25 |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| — | — | — | — | — | — |

## Traceability
- **Workflow phase**: plan-to-implementation-procedure
- **Requirement ID**: `REQ-004` — correct the `rotate_all_dbs()` schedule-comment DB count
- **Source issue**: `issues/20260823_adr008_eventbus_rotation_exclusion_issue.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20260825-133745_plan.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260825-181135
- **Related target files**: `scripts/db/maintenance.py`
