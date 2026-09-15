## Goal

Evidence for EventBus config loading migration during eventbus13's ConfigLoader migration. REQ-001, REQ-002.

## Scope

Verify scripts/eventbus/config.py's migration from tomllib.load() to ConfigLoader-based loading while preserving all validation behavior. This row is read-only evidence gathering.

## Assumptions

- config.py exists at `scripts/eventbus/config.py`
- config.py currently uses tomllib.load() directly
- EventBus has validation logic in __post_init__ and load_config()

## Design decisions

- Read-only verification: confirm current state without independently modifying
- If the migration has already occurred, mark this step as complete
- If stale loading mechanism exists, report Plan Gap

## Alternatives considered

- Independently migrating config.py: rejected because eventbus13's scope is documentation only
- Deferring until eventbus13 executes: not viable since eventbus13 depends on eventbus09 landing first

## Implementation

### Target file

`scripts/eventbus/config.py`

### Procedure

1. Check whether config.py still uses tomllib.load() directly
2. Verify EventBus validation logic in __post_init__ and load_config()
3. If all checks pass, mark this step as complete
4. If any check fails, determine whether eventbus09 has landed:
   - If eventbus09 has not landed: missing ConfigLoader migration is expected, no action needed
   - If eventbus09 has landed but migration doesn't match: report Plan Gap

### Method

Adversarial verification: treat the plan's description of current config.py state as unverified. Check each claim against the actual file content.

### Details

**Step 1: Verify tomllib.load() usage**

Expected: tomllib.load() used directly in load_config().

Pre-migration state: tomllib.load() used per ADR-013 (now stale).

**Step 2: Verify validation logic**

Expected: Per-key type validation (lines 184-192), auth token non-empty check (lines 194-196), per-role token combination rule (lines 198-206), cross-field validation in __post_init__ (lines 73-80), single-value validation in __post_init__ (lines 62-94).

## Compatibility considerations

- This verification must occur after eventbus09 lands; executing before eventbus09 would produce false positives
- The config loading may have been updated since eventbus09's approval — verify alignment rather than duplicating the edit
- If config.py still lacks expected migration after eventbus09 lands, the gap belongs to eventbus09's execution, not eventbus13

## Security considerations

- None applicable: documentation reconciliation only, no code changes or security boundary modifications

## Rollback considerations

- No rollback needed: this is a verification step, not a modification
- If config.py needs correction, defer to eventbus09's implementation rather than applying an independent fix

## Validation plan

| Target File | Testing Strategy | Tool / Command | Expected Outcome |
|---|---|---|---|
| scripts/eventbus/config.py | Manual review: verify config loading migration status | Manual inspection | Migration matches documented API reference |

## Completion criteria

- config.py loads configuration via ConfigLoader, not tomllib.load() directly
- Every existing EventBus configuration validation error case still produces an equivalent error after migration
- EventBus configuration loading is covered by the same process-isolation guarantee (restrict_to()) as other processes

## Out of scope

- Modifying config.py directly (unless stale content requires correction, which should be deferred to eventbus09)
- Re-deciding the config loading design (answered by eventbus09)
- Creating API reference documents (separate row in this plan)

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Verify tomllib.load() usage status | Pending | — | — | |
| 2 | Verify validation logic preservation | Pending | — | — | |

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
- **Source issue**: issues/20260914-104425_eventbus13_config-loader-migration.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260914-184302_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260915-232700
- **Related target files**: scripts/eventbus/config.py
