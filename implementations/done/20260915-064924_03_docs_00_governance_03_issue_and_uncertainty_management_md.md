# Implementation Procedure: Correct EVENTBUS-001 Governance Entry

## Goal

Correct EVENTBUS-001 in `docs/00_governance_03_issue-and-uncertainty-management.md` to describe the actual current risk (limited to `migrate_legacy_offsets()`'s no-`.map`-companion fallback), remove the stale `Related: EVENTBUS-003, EVENTBUS-008` references (both already resolved and removed from the active inventory), and lower its severity to reflect a one-time-migration-only risk rather than a continuously-exploitable one.

## Scope

- Modify `docs/00_governance_03_issue-and-uncertainty-management.md`: correct EVENTBUS-001 entry
- No modifications to other documentation files

## Assumptions

- The collision detection fix has been implemented and verified by tests before this step is executed
- EVENTBUS-003 and EVENTBUS-008 have been resolved and removed from the active inventory
- The current EVENTBUS-001 entry describes the collision risk as applying to the live, ongoing ACK path ("silent overwriting of offsets"), which is inaccurate

## Design decisions

### Decision A: Lower severity to Medium

**Reason:** The risk is limited to a one-time migration step, not a continuously-exploitable defect. Medium severity accurately reflects the reduced frequency and impact.

### Alternative A: Keep severity as High

**Reason for rejection:** Would misrepresent the risk. High severity implies continuous exploitation risk, which no longer applies after the migration-path fix.

### Decision B: Remove stale Related references

**Reason:** EVENTBUS-003 and EVENTBUS-008 have been resolved and removed from the active inventory. Keeping stale references creates confusion for future readers.

## Implementation

### Target file

`docs/00_governance_03_issue-and-uncertainty-management.md`

### Procedure

#### Step 1: Locate EVENTBUS-001 entry

Find the EVENTBUS-001 section in the document. Look for:
- The title "EVENTBUS-001"
- References to "Consumer ID Collision Detection"
- Severity level (currently High)
- Related references (EVENTBUS-003, EVENTBUS-008)

#### Step 2: Update severity from High to Medium

Change the severity line from:
```markdown
Severity: High
```
to:
```markdown
Severity: Medium
```

#### Step 3: Narrow the risk description

Update the risk description to reflect the actual, narrower current risk:
- Remove references to the live ACK path
- Emphasize that the risk is limited to `migrate_legacy_offsets()`'s no-`.map`-companion fallback
- Clarify that the risk is a one-time migration concern, not a continuously-exploitable defect

Example updated text:
```markdown
EVENTBUS-001 ("Consumer ID Collision Detection") was partially resolved and narrowed in scope 2026-09-15. The original claim that `_sanitize_consumer_id()` causes silent offset overwriting between colliding consumer_ids applied to the live ACK path (`ack_event_for_consumer()`), but this path no longer uses `_sanitize_consumer_id()` — it writes to `consumer_delivery`/`consumer_offsets` using the caller's `consumer_id` verbatim with no call to `_sanitize_consumer_id()`. Two distinct IDs like `user.1` and `user_1` are stored as distinct rows and cannot collide here.

The verified, current risk is narrower: a one-time migration step, only triggered for legacy offset files lacking a `.map` companion. In `migrate_legacy_offsets()`, when a `.map` companion file is missing, the function falls back to `_sanitize_consumer_id()` on the raw filename — at which point the original EVENTBUS-001 collision risk (`user.1` vs `user_1` both sanitizing to the same filename) can still silently merge two legacy consumers' offsets during a one-time migration. This risk is bounded by the finite set of legacy offset files and does not affect the live ACK path.
```

#### Step 4: Remove stale Related references

Remove or comment out the `Related: EVENTBUS-003, EVENTBUS-008` references, since both have been resolved and removed from the active inventory.

#### Step 5: Verify the update

Read the updated document to confirm:
- [ ] Severity is Medium
- [ ] Risk description accurately reflects the narrower scope
- [ ] Stale Related references removed
- [ ] Document structure preserved (no formatting changes)

### Method

Surgical edit of the EVENTBUS-001 section in the governance document.

### Details

#### Verification checklist

- [ ] Severity updated to Medium
- [ ] Risk description narrowed to migration-only scope
- [ ] Stale Related references removed
- [ ] Document structure preserved

## Compatibility considerations

- No compatibility impact — documentation-only change
- Other processes may reference EVENTBUS-001; ensure the corrected description is clear enough for downstream consumers

## Security considerations

- No security impact — documentation-only change
- Accurate severity assessment helps prioritize future work correctly

## Rollback considerations

- Revert to original EVENTBUS-001 entry if the correction was premature or incorrect

## Validation plan

1. **Manual review**: Confirm EVENTBUS-001 entry accurately reflects the corrected, narrower risk description
2. **Acceptance criteria verification**:
   - [ ] REQ-003: EVENTBUS-001's entry accurately describes the current, narrower risk and its actual severity, with stale Related references removed

## Completion criteria

- [ ] Severity updated to Medium
- [ ] Risk description narrowed to migration-only scope
- [ ] Stale Related references removed
- [ ] Document structure preserved

## Out of scope

- Modifying other Known Issues entries
- Changing the governance document's structure or format
- Adding new Known Issues beyond what currently exists

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Locate EVENTBUS-001 entry | Completed | 20260915-230000 | 20260915-230000 |  |
| 2 | Update severity from High to Medium | Completed | 20260915-230000 | 20260915-230000 |  |
| 3 | Narrow risk description | Completed | 20260915-230000 | 20260915-230000 |  |
| 4 | Remove stale Related references | Completed | 20260915-230000 | 20260915-230000 |  |
| 5 | Verify the update | Completed | 20260915-230000 | 20260915-230000 |  |

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
- **Requirement ID**: REQ-003 (correct EVENTBUS-001 entry: narrow risk description, lower severity, remove stale Related references)
- **Source issue**: issues/20260914-102632_eventbus11_api-reference-endpoint-contracts.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260914-185056_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260915-064924
- **Related target files**: docs/00_governance_03_issue-and-uncertainty-management.md