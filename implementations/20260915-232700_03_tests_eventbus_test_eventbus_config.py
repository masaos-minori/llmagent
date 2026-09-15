## Goal

Evidence for EventBus config test updates during eventbus13's ConfigLoader migration. REQ-004.

## Scope

Verify tests/eventbus/test_eventbus_config.py's test updates for ConfigLoader-based loading. This row is read-only evidence gathering.

## Assumptions

- test_eventbus_config.py exists at `tests/eventbus/test_eventbus_config.py`
- Tests mock get_config_path() to inject test config files

## Design decisions

- Read-only verification: confirm current state without independently modifying
- If the tests already match the plan's documented contract, mark this step as complete
- If stale tests exist, report Plan Gap

## Alternatives considered

- Independently updating tests: rejected because eventbus13's scope is documentation only
- Deferring until eventbus13 executes: not viable since eventbus13 depends on eventbus09 landing first

## Implementation

### Target file

`tests/eventbus/test_eventbus_config.py`

### Procedure

1. Check whether test_eventbus_config.py still mocks get_config_path()
2. Verify tests work with ConfigLoader-based loading
3. Verify all existing validation error cases still produce the same errors
4. If all checks pass, mark this step as complete
5. If any check fails, determine whether eventbus09 has landed:
   - If eventbus09 has not landed: missing test updates are expected, no action needed
   - If eventbus09 has landed but tests don't match: report Plan Gap

### Method

Adversarial verification: treat the plan's description of current test_eventbus_config.py state as unverified. Check each claim against the actual file content.

### Details

**Step 1: Verify get_config_path() mocking**

Expected: Tests still mock get_config_path() where needed.

Pre-migration state: get_config_path() mocked per ADR-013 (now stale).

**Step 2: Verify ConfigLoader compatibility**

Expected: Tests work with ConfigLoader-based loading.

**Step 3: Verify validation error case coverage**

Expected: All existing validation error cases still produce the same errors.

## Compatibility considerations

- This verification must occur after eventbus09 lands; executing before eventbus09 would produce false positives
- The tests may have been updated since eventbus09's approval — verify alignment rather than duplicating the edit
- If test_eventbus_config.py still lacks expected updates after eventbus09 lands, the gap belongs to eventbus09's execution, not eventbus13

## Security considerations

- None applicable: documentation reconciliation only, no code changes or security boundary modifications

## Rollback considerations

- No rollback needed: this is a verification step, not a modification
- If test_eventbus_config.py needs correction, defer to eventbus09's implementation rather than applying an independent fix

## Validation plan

| Target File | Testing Strategy | Tool / Command | Expected Outcome |
|---|---|---|---|
| tests/eventbus/test_eventbus_config.py | Manual review: verify test updates status | Manual inspection | Tests match documented API reference |

## Completion criteria

- test_eventbus_config.py works with ConfigLoader-based loading
- All existing validation error cases still produce the same errors
- Tests confirm ConfigLoader permission enforcement for EventBus

## Out of scope

- Modifying test_eventbus_config.py directly (unless stale content requires correction, which should be deferred to eventbus09)
- Re-deciding the test design (answered by eventbus09)
- Creating API reference documents (separate row in this plan)

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Verify get_config_path() mocking | Pending | — | — | |
| 2 | Verify ConfigLoader compatibility | Pending | — | — | |
| 3 | Verify validation error case coverage | Pending | — | — | |

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
- **Source issue**: issues/20260914-104425_eventbus13_config-loader-migration.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260914-184302_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260915-232700
- **Related target files**: tests/eventbus/test_eventbus_config.py
