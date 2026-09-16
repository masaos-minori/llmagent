## Goal

Evidence for authentication existence claim during eventbus10's reconciliation. Read-only verification — confirm auth.py exists and implements bearer authentication. REQ-005.

## Scope

Verify that `scripts/eventbus/auth.py` exists and contains the role-based authentication implementation referenced by eventbus10's reconciliation. This row is read-only evidence gathering.

## Assumptions

- auth.py exists at `scripts/eventbus/auth.py`
- auth.py defines Role enum (_ROUTE_ROLE_MAP), token maps, and require_role dependency factory
- Pre-migration state: auth.py was pending per ADR-013's Problem section (now stale)
- Post-migration state: auth.py exists with bearer authentication + role-based authorization

## Design decisions

- Read-only verification: confirm auth.py's existence and content without independently modifying
- If auth.py already implements the expected authentication model, mark this step as complete
- If auth.py does not exist or lacks expected functionality, report Plan Gap

## Alternatives considered

- Independently implementing auth.py: rejected because eventbus02 owns this implementation (ADR-013 Status: Accepted)
- Deferring until eventbus10 executes: not viable since eventbus10 depends on eventbus13 landing first

## Implementation

### Target file

`scripts/eventbus/auth.py`

### Procedure

1. Verify auth.py exists at `scripts/eventbus/auth.py`
2. Check whether auth.py defines the Role enum
3. Check whether auth.py defines _ROUTE_ROLE_MAP
4. Check whether auth.py defines _populate_token_maps()
5. Check whether auth.py defines require_role() dependency factory
6. If all checks pass, mark this step as complete
7. If any check fails, determine whether eventbus02 has landed:
   - If eventbus02 has not landed: missing auth.py is expected, no action needed
   - If eventbus02 has landed but auth.py is incomplete: report Plan Gap

### Method

Adversarial verification: treat the plan's description of current auth.py state as unverified. Check each claim against the actual file content.

### Details

**Step 1: Verify auth.py exists**

Expected: `scripts/eventbus/auth.py` exists on disk.

Pre-migration state: auth.py did not exist (pending per ADR-013).

**Step 2: Verify Role enum**

Expected: `auth.py:21-25` defines Role enum.

**Step 3: Verify _ROUTE_ROLE_MAP**

Expected: `auth.py:29-39` defines _ROUTE_ROLE_MAP mapping routes to required roles.

**Step 4: Verify _populate_token_maps()**

Expected: `auth.py:63-88` defines _populate_token_maps().

**Step 5: Verify require_role() dependency factory**

Expected: `auth.py:128-172` defines require_role() dependency factory.

## Compatibility considerations

- This verification must occur after eventbus02 lands; executing before eventbus02 would produce false positives
- auth.py may have been updated since eventbus02's approval — verify alignment rather than duplicating the edit
- If auth.py still lacks expected functionality after eventbus02 lands, the gap belongs to eventbus02's execution, not eventbus10

## Security considerations

- None applicable: documentation reconciliation only, no code changes or security boundary modifications

## Rollback considerations

- No rollback needed: this is a verification step, not a modification
- If auth.py needs correction, defer to eventbus02's implementation rather than applying an independent fix

## Validation plan

| Target File | Testing Strategy | Tool / Command | Expected Outcome |
|---|---|---|---|
| scripts/eventbus/auth.py | Manual review: verify authentication implementation | Manual inspection of Role enum, _ROUTE_ROLE_MAP, require_role() | Authentication exists and matches documented contract |

## Completion criteria

- auth.py exists at `scripts/eventbus/auth.py`
- Role enum is defined
- _ROUTE_ROLE_MAP is defined
- _populate_token_maps() is defined
- require_role() dependency factory is defined

## Out of scope

- Modifying auth.py directly (unless stale content requires correction, which should be deferred to eventbus02)
- Re-deciding the authentication architecture (answered by eventbus02)
- Updating ADR-002 or ADR-013 (separate rows in this plan)

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Verify auth.py exists | Passed | — | — | scripts/eventbus/auth.pyが存在 |
| 2 | Verify Role enum definition | Passed | — | — | Role enum定義済み（auth.py:26） |
| 3 | Verify _ROUTE_ROLE_MAP definition | Passed | — | — | _ROUTE_ROLE_MAP定義済み（auth.py:45） |
| 4 | Verify _populate_token_maps() definition | Passed | — | — | _populate_token_maps()定義済み（auth.py:92） |
| 5 | Verify require_role() dependency factory | Passed | — | — | require_role()依存関係ファクトリ定義済み（auth.py:212） |

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
- **Requirement ID**: REQ-005
- **Source issue**: issues/20260914-102602_eventbus10_reconcile-adrs-known-issues.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260914-180730_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260915-232643
- **Related target files**: scripts/eventbus/auth.py
