## Goal

Understand how EventBus config is loaded and middleware attached at startup. Read-only evidence gathering for eventbus10's reconciliation. REQ-005.

## Scope

Verify app.py's startup/lifespan wiring for config loading and authentication middleware attachment. This row is read-only evidence gathering.

## Assumptions

- app.py exists at `scripts/eventbus/app.py`
- The lifespan handler calls `load_config()` and attaches auth middleware
- Pre-migration state: `load_config(get_config_path())` using tomllib path
- Post-migration state: `ConfigLoader.restrict_to("eventbus.toml")` + `load_config("eventbus")`

## Design decisions

- Read-only verification: confirm current state without independently modifying
- If the wiring already reflects eventbus13's outcome, mark this step as complete
- If stale wiring remains, report Plan Gap and do not apply eventbus13's fix here

## Alternatives considered

- Independently updating app.py's lifespan handler: rejected because eventbus13 owns this change via REQ-003
- Deferring until eventbus10 executes: not viable since eventbus10 depends on eventbus13 landing first

## Implementation

### Target file

`scripts/eventbus/app.py`

### Procedure

1. Check whether app.py's lifespan handler calls `ConfigLoader.restrict_to("eventbus.toml")` before config loading
2. Check whether app.py's lifespan handler calls `load_config("eventbus")` instead of `load_config(get_config_path())`
3. Check whether auth middleware (`attach_auth_middleware(app)`) is properly wired
4. If all checks pass, mark this step as complete
5. If any check fails, determine whether eventbus13 has landed:
   - If eventbus13 has not landed: stale wiring is expected, no action needed
   - If eventbus13 has landed but stale wiring persists: report Plan Gap

### Method

Adversarial verification: treat the plan's description of current app.py state as unverified. Check each claim against the actual file content.

### Details

**Step 1: Verify restrict_to call in lifespan handler**

Expected: `ConfigLoader.restrict_to("eventbus.toml")` called before `load_config()` invocation.

Pre-migration state: No `restrict_to()` call existed in the lifespan handler.

**Step 2: Verify load_config invocation**

Expected: `load_config("eventbus")` replaces `load_config(get_config_path())`.

Pre-migration state: `config = load_config(get_config_path())` in the lifespan handler.

**Step 3: Verify auth middleware wiring**

Expected: `attach_auth_middleware(app)` is called and every route requires `Depends(require_role(...))`.

Pre-migration state: auth middleware was pending per ADR-013's Problem section (now stale).

## Compatibility considerations

- This verification must occur after eventbus13 lands; executing before eventbus13 would produce false positives
- The lifespan handler may have been updated by eventbus13's REQ-003 — verify alignment rather than duplicating the edit
- If app.py still shows stale wiring after eventbus13 lands, the gap belongs to eventbus13's execution, not eventbus10

## Security considerations

- None applicable: documentation reconciliation only, no code changes or security boundary modifications

## Rollback considerations

- No rollback needed: this is a verification step, not a modification
- If app.py needs correction, defer to eventbus13's REQ-003 rather than applying an independent fix

## Validation plan

| Target File | Testing Strategy | Tool / Command | Expected Outcome |
|---|---|---|---|
| scripts/eventbus/app.py | Manual review: verify lifespan handler wiring | Manual inspection of lifespan handler | Config loading uses ConfigLoader, auth middleware is attached |

## Completion criteria

- `ConfigLoader.restrict_to("eventbus.toml")` is called in the lifespan handler before config loading
- `load_config("eventbus")` replaces `load_config(get_config_path())`
- `attach_auth_middleware(app)` is properly wired

## Out of scope

- Modifying app.py directly (unless stale content requires correction, which should be deferred to eventbus13)
- Re-deciding the ConfigLoader migration approach (answered by eventbus13)
- Updating ADR-002 or ADR-013 (separate rows in this plan)

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Verify restrict_to() call in lifespan handler | Pending | — | — | |
| 2 | Verify load_config() invocation uses ConfigLoader name | Pending | — | — | |
| 3 | Verify auth middleware wiring | Pending | — | — | |

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
- **Related target files**: scripts/eventbus/app.py
