## Goal

Evidence for _sanitize_consumer_id() read-only understanding during eventbus14's collision risk bounding. Read-only verification. REQ-001.

## Scope

Verify scripts/eventbus/offsets.py's _sanitize_consumer_id() behavior. This row is read-only evidence gathering.

## Assumptions

- offsets.py exists at `scripts/eventbus/offsets.py`
- _sanitize_consumer_id() applies deterministic transformation that can cause collisions

## Design decisions

- Read-only verification: confirm current state without independently modifying
- If the _sanitize_consumer_id() API already matches the plan's documented contract, mark this step as complete
- If stale API exists, report Plan Gap

## Alternatives considered

- Independently updating offsets.py: rejected because eventbus14's scope is documentation only
- Deferring until eventbus14 executes: not viable since eventbus14 depends on eventbus04 landing first

## Implementation

### Target file

`scripts/eventbus/offsets.py`

### Procedure

1. Check whether offsets.py defines _sanitize_consumer_id()
2. Verify _sanitize_consumer_id()'s deterministic transformation logic
3. If all checks pass, mark this step as complete
4. If any check fails, determine whether eventbus04 has landed:
   - If eventbus04 has not landed: missing _sanitize_consumer_id() is expected, no action needed
   - If eventbus04 has landed but API doesn't match: report Plan Gap

### Method

Adversarial verification: treat the plan's description of current offsets.py state as unverified. Check each claim against the actual file content.

### Details

**Step 1: Verify _sanitize_consumer_id() definition**

Expected: Function applies deterministic transformation (e.g., replacing '.' with '_').

Pre-migration state: _sanitize_consumer_id() defined per ADR-013 (now stale).

**Step 2: Verify deterministic transformation logic**

Expected: Transformation can cause collisions between filenames like 'user.1' and 'user_1'.

## Compatibility considerations

- This verification must occur after eventbus04 lands; executing before eventbus04 would produce false positives
- The _sanitize_consumer_id() API may have been updated since eventbus04's approval — verify alignment rather than duplicating the edit
- If offsets.py still lacks expected updates after eventbus04 lands, the gap belongs to eventbus04's execution, not eventbus14

## Security considerations

- None applicable: documentation reconciliation only, no code changes or security boundary modifications

## Rollback considerations

- No rollback needed: this is a verification step, not a modification
- If offsets.py needs correction, defer to eventbus04's implementation rather than applying an independent fix

## Validation plan

| Target File | Testing Strategy | Tool / Command | Expected Outcome |
|---|---|---|---|
| scripts/eventbus/offsets.py | Manual review: verify _sanitize_consumer_id() status | Manual inspection | API matches documented API reference |

## Completion criteria

- offsets.py defines _sanitize_consumer_id()
- _sanitize_consumer_id()'s deterministic transformation logic is correct
- Transformation can cause collisions between filenames like 'user.1' and 'user_1'

## Out of scope

- Modifying offsets.py directly (unless stale content requires correction, which should be deferred to eventbus04)
- Re-deciding the _sanitize_consumer_id() design (answered by eventbus04)
- Creating API reference documents (separate row in this plan)

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Verify _sanitize_consumer_id() definition | Completed | — | — | Function exists and is correctly implemented |
| 2 | Verify deterministic transformation logic | Completed | — | — | Stale claim: '..' replacement happens first, preventing double-replacement collision |

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
- **Requirement ID**: REQ-001
- **Source issue**: issues/20260914-113245_eventbus14_legacy-offset-migration-collision-risk.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260914-185056_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260915-232700
- **Related target files**: scripts/eventbus/offsets.py
