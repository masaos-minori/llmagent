## Goal

Evidence for legacy offset migration collision detection during eventbus14's collision risk bounding. REQ-001, REQ-004.

## Scope

Verify scripts/eventbus/db.py's collision detection logic in migrate_legacy_offsets(). This row is read-only evidence gathering.

## Assumptions

- db.py exists at `scripts/eventbus/db.py`
- db.py has migrate_legacy_offsets() function
- _sanitize_consumer_id() applies deterministic transformation that can cause collisions

## Design decisions

- Read-only verification: confirm current state without independently modifying
- If the collision detection has already been implemented, mark this step as complete
- If stale migration behavior exists, report Plan Gap

## Alternatives considered

- Independently adding collision detection: rejected because eventbus14's scope is documentation only
- Deferring until eventbus14 executes: not viable since eventbus14 depends on eventbus04 landing first

## Implementation

### Target file

`scripts/eventbus/db.py`

### Procedure

1. Check whether db.py still lacks collision detection in migrate_legacy_offsets()
2. Verify db.py doesn't modify ack_event_for_consumer()
3. If all checks pass, mark this step as complete
4. If any check fails, determine whether eventbus04 has landed:
   - If eventbus04 has not landed: missing collision detection is expected, no action needed
   - If eventbus04 has landed but migration doesn't match: report Plan Gap

### Method

Adversarial verification: treat the plan's description of current db.py state as unverified. Check each claim against the actual file content.

### Details

**Step 1: Verify collision detection status**

Expected: migrate_legacy_offsets() lacks collision detection for no-.map-companion fallback.

Pre-migration state: Collision detection pending per ADR-013 (now stale).

**Step 2: Verify ack_event_for_consumer() unchanged**

Expected: ack_event_for_consumer() not modified by this change.

## Compatibility considerations

- This verification must occur after eventbus04 lands; executing before eventbus04 would produce false positives
- The migration may have been updated since eventbus04's approval — verify alignment rather than duplicating the edit
- If db.py still lacks expected updates after eventbus04 lands, the gap belongs to eventbus04's execution, not eventbus14

## Security considerations

- None applicable: documentation reconciliation only, no code changes or security boundary modifications

## Rollback considerations

- No rollback needed: this is a verification step, not a modification
- If db.py needs correction, defer to eventbus04's implementation rather than applying an independent fix

## Validation plan

| Target File | Testing Strategy | Tool / Command | Expected Outcome |
|---|---|---|---|
| scripts/eventbus/db.py | Manual review: verify collision detection status | Manual inspection | Collision detection matches documented API reference |

## Completion criteria

- migrate_legacy_offsets() detects and flags ambiguous cases when no `.map` companion exists
- ack_event_for_consumer() remains unchanged
- Collision detection does not introduce performance regressions in normal case

## Out of scope

- Modifying db.py directly (unless stale content requires correction, which should be deferred to eventbus04)
- Re-deciding the collision detection design (answered by eventbus04)
- Creating API reference documents (separate row in this plan)

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Verify collision detection status | Pending | — | — | |
| 2 | Verify ack_event_for_consumer() unchanged | Pending | — | — | |

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
- **Requirement ID**: REQ-001, REQ-004
- **Source issue**: issues/20260914-113245_eventbus14_legacy-offset-migration-collision-risk.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260914-185056_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260915-232700
- **Related target files**: scripts/eventbus/db.py
