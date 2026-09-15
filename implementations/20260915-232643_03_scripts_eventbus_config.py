## Goal

Confirm `eventbus13`'s ConfigLoader migration has landed in EventBus config loading. Read-only verification — no modification required unless stale content is discovered. REQ-004.

## Scope

Verify that `scripts/eventbus/config.py` uses `ConfigLoader`-based loading instead of direct `tomllib.load()`. This row is read-only evidence gathering for eventbus10's reconciliation.

## Assumptions

- `eventbus13` (`plans/20260914-184302_plan.md`) migrates EventBus to `ConfigLoader`
- Pre-migration state: `config.py:163-230` used `load_config()` with `tomllib.load()` directly
- Post-migration state: `ConfigLoader.load()` replaces `tomllib.load()`, `ConfigLoader.restrict_to("eventbus.toml")` called in lifespan handler

## Design decisions

- Read-only verification: confirm eventbus13's migration outcome without independently re-editing
- If ConfigLoader-based loading is already in place, mark this step as complete
- If stale tomllib-based loading remains, report Plan Gap and do not apply eventbus13's fix here

## Alternatives considered

- Independently migrating to ConfigLoader: rejected because eventbus13 owns this change via REQ-001/REQ-002
- Deferring until eventbus10 executes: not viable since eventbus10 depends on eventbus13 landing first

## Implementation

### Target file

`scripts/eventbus/config.py`

### Procedure

1. Check whether `config.py` imports `ConfigLoader` from `shared.config_loader`
2. Check whether `load_config()` uses `ConfigLoader.load()` instead of `tomllib.load()`
3. If both checks pass, mark this step as complete
4. If either check fails, determine whether eventbus13 has landed:
   - If eventbus13 has not landed: stale content is expected, no action needed
   - If eventbus13 has landed but stale content persists: report Plan Gap

### Method

Adversarial verification: treat the plan's description of current config.py state as unverified. Check each claim against the actual file content.

### Details

**Step 1: Verify ConfigLoader import**

Expected: `from shared.config_loader import ConfigLoader` (may require `.importlinter` relaxation per eventbus13's REQ-003).

Pre-migration state: `config.py:6` had `import tomllib` with no ConfigLoader import.

**Step 2: Verify load_config() uses ConfigLoader**

Expected: `ConfigLoader.restrict_to("eventbus.toml")` called before `loader.load(config_name)` in the lifespan handler.

Pre-migration state: `config.py:166` had `data = tomllib.load(f)` with local validation logic preserved.

**Step 3: Verify validation logic preservation**

Expected: All existing validation logic (per-key type validation, auth token non-empty check, per-role token combination rule, cross-field validation in `__post_init__`) is preserved exactly as-is.

## Compatibility considerations

- This verification must occur after eventbus13 lands; executing before eventbus13 would produce false positives
- The `.importlinter` contract may need relaxation for the ConfigLoader import — verify alignment with eventbus13's REQ-003
- If config.py still shows stale content after eventbus13 lands, the gap belongs to eventbus13's execution, not eventbus10

## Security considerations

- None applicable: documentation reconciliation only, no code changes or security boundary modifications

## Rollback considerations

- No rollback needed: this is a verification step, not a modification
- If config.py needs correction, defer to eventbus13's REQ-001/REQ-002 rather than applying an independent fix

## Validation plan

| Target File | Testing Strategy | Tool / Command | Expected Outcome |
|---|---|---|---|
| scripts/eventbus/config.py | Manual review: verify ConfigLoader-based loading | Manual inspection of imports and load_config() body | No stale tomllib.load() references remain |

## Completion criteria

- `config.py` imports `ConfigLoader` from `shared.config_loader`
- `load_config()` uses `ConfigLoader.load()` instead of `tomllib.load()` directly
- `ConfigLoader.restrict_to("eventbus.toml")` is called in the lifespan handler before config loading
- All existing validation behavior is preserved

## Out of scope

- Modifying config.py directly (unless stale content requires correction, which should be deferred to eventbus13)
- Re-deciding the ConfigLoader migration approach (answered by eventbus13)
- Updating ADR-002 or ADR-013 (separate rows in this plan)

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Verify ConfigLoader import exists in config.py | Pending | — | — | |
| 2 | Verify load_config() uses ConfigLoader.load() | Pending | — | — | |
| 3 | Verify validation logic preservation | Pending | — | — | |

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
- **Requirement ID**: REQ-004
- **Source issue**: issues/20260914-102602_eventbus10_reconcile-adrs-known-issues.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260914-180730_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260915-232643
- **Related target files**: scripts/eventbus/config.py
