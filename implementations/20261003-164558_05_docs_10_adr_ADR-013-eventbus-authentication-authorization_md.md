## Goal

Remove dangling clause for EVENTBUS-008 from `ADR-013-eventbus-authentication-authorization.md`, so `check_known_deviation_sync.py` reports no warning for this ID (REQ-001, REQ-002).

## Scope

- Remove the dangling `EVENTBUS-008` clause from the ADR's `### Known Issues` pointer bullet.
- Preserve surrounding text and other references in the same bullet.

## Assumptions

- EVENTBUS-008 is confirmed resolved (per the ADR's own statement that it was resolved 2026-09-14), making the reference stale.
- Removing a dangling clause from an ADR's `### Known Issues` section does not affect the ADR's decision or invariant.

## Design decisions

- Only remove the specific `ID (...)` clause; preserve surrounding text and other references in the same bullet.
- Never hide IDs behind full-width punctuation or reformat them to evade `_ID_LOOKAHEAD_RE`.

## Alternatives considered

- Update the EVENTBUS-008 entry in `governance_03` to reflect its resolved status — rejected because the ADR already states it is resolved, so the reference should be removed rather than kept.
- Leave the dangling clause and update the checker — rejected because the checker correctly identifies the problem.

## Implementation

### Target file

`docs/10_adr/ADR-013-eventbus-authentication-authorization.md`

### Procedure

1. Confirm EVENTBUS-008 is resolved (the ADR itself states this at line 281).
2. Delete the whole dangling `EVENTBUS-008 (...)` clause from the ADR's `### Known Issues` pointer bullet.
3. Verify the checker passes after changes.

### Method

- Locate line 317 in the ADR where the EVENTBUS-008 known issue is referenced.
- Delete only the `EVENTBUS-008 (...)` clause portion, preserving the rest of the bullet.

### Details

Current state:
- Line 317: `- [Issue and Uncertainty Management](../00_governance/governance_03_issue-and-uncertainty-management.md) — EVENTBUS-008 (No Production Authentication Model) and CI-001 (ConfigLoader migration) addressed by this ADR.`

EVENTBUS-008 is explicitly stated as resolved in the ADR body (line 281). The reference at line 317 should be removed since the issue is no longer open.

Note: CI-001 is also mentioned but is out of scope for this cycle per the Plan's Out-of-Scope section.

## Compatibility considerations

N/A: documentation-only change.

## Security considerations

N/A: documentation-only change.

## Rollback considerations

Re-adding the dangling clause is straightforward if EVENTBUS-008 was incorrectly classified as resolved. Document the reason for re-addition in a comment.

## Validation plan

| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| docs/10_adr/ADR-013-eventbus-authentication-authorization.md | Checker validation | `uv run python tools/check_known_deviation_sync.py` | No `[WARNING]` for EVENTBUS-008 |

## Completion criteria

- Dangling EVENTBUS-008 clause removed from the ADR's `### Known Issues` section.
- `uv run python tools/check_known_deviation_sync.py` reports no `[WARNING]` for EVENTBUS-008.

## Out of scope

- Adding canonical entries for still-tracked IDs (covered by Row 1).
- Adding `**Status**: ...` field to `EVENTBUS-001` in `eventbus_01_system-overview.md` (covered by another row).
- The two pre-existing `[ERROR]` status-mismatch findings (`CI-001`, `CI-016`).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Confirm EVENTBUS-008 resolution status | Pending | — | — | |
| 2 | Remove dangling clause for EVENTBUS-008 | Pending | — | — | |
| 3 | Validate with check_known_deviation_sync.py | Pending | — | — | |

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
- **Requirement ID**: REQ-001, REQ-002
- **Source issue**: issues/20261003-080956_kd003_dangling_and_unparsed_known_issue_references.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/done/20261003-150043_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261003-164558
- **Related target files**: docs/10_adr/ADR-013-eventbus-authentication-authorization.md
