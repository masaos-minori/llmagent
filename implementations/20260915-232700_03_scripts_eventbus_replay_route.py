## Goal

Evidence for replay route parameter cleanup during eventbus12's security parameter removal. REQ-002.

## Scope

Verify replay_route.py's unused `_role` parameter removal from `replay()`. This row is read-only evidence gathering.

## Assumptions

- replay_route.py exists at `scripts/eventbus/replay_route.py`
- replay_route.py currently has `_role` parameter in `replay()`
- This parameter is unused in function body

## Design decisions

- Read-only verification: confirm current state without independently modifying
- If the `_role` parameter has already been removed, mark this step as complete
- If stale parameter exists, report Plan Gap

## Alternatives considered

- Independently removing `_role` parameter: rejected because eventbus12's scope is documentation only
- Deferring until eventbus12 executes: not viable since eventbus12 depends on eventbus02/eventbus03 landing first

## Implementation

### Target file

`scripts/eventbus/replay_route.py`

### Procedure

1. Check whether replay_route.py still has `_role` parameter in `replay()`
2. Verify this parameter is unused in function body
3. If all checks pass, mark this step as complete
4. If any check fails, determine whether eventbus02 has landed:
   - If eventbus02 has not landed: missing `_role` parameter is expected, no action needed
   - If eventbus02 has landed but parameter remains: report Plan Gap

### Method

Adversarial verification: treat the plan's description of current replay_route.py state as unverified. Check each claim against the actual file content.

### Details

**Step 1: Verify `_role` parameter in `replay()`**

Expected: `_role: Role | None = None` parameter present and unused.

Pre-migration state: `_role` parameter exists per ADR-013 (now stale).

**Step 2: Verify parameter usage**

Expected: Parameter not used in function body.

## Compatibility considerations

- This verification must occur after eventbus02 lands; executing before eventbus02 would produce false positives
- The `_role` parameter may have been updated since eventbus02's approval — verify alignment rather than duplicating the edit
- If replay_route.py still has expected parameter after eventbus02 lands, the gap belongs to eventbus02's execution, not eventbus12

## Security considerations

- None applicable: documentation reconciliation only, no code changes or security boundary modifications

## Rollback considerations

- No rollback needed: this is a verification step, not a modification
- If replay_route.py needs correction, defer to eventbus02's implementation rather than applying an independent fix

## Validation plan

| Target File | Testing Strategy | Tool / Command | Expected Outcome |
|---|---|---|---|
| scripts/eventbus/replay_route.py | Manual review: verify `_role` parameter status | Manual inspection | Parameters match documented API reference |

## Completion criteria

- replay_route.py does not have unused `_role` parameter in `replay()`
- Function relies exclusively on endpoint-level authorization

## Out of scope

- Modifying replay_route.py directly (unless stale content requires correction, which should be deferred to eventbus02)
- Re-deciding the parameter design (answered by eventbus02)
- Creating API reference documents (separate row in this plan)

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Verify `_role` parameter in `replay()` | Pending | — | — | |
| 2 | Verify parameter usage status | Pending | — | — | |

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
- **Requirement ID**: REQ-002
- **Source issue**: issues/20260914-102654_eventbus12_remove-misleading-security-parameters.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260914-183834_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260915-232700
- **Related target files**: scripts/eventbus/replay_route.py
