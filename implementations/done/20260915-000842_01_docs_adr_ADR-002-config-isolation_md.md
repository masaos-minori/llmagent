# Implementation Procedure: Reconcile ADR-002 Claim on Config Isolation Boundary

## Goal

Update ADR-002-config-isolation.md to reconcile the stale claim that "All processes MUST load config through ConfigLoader.restrict_to()" against the current reality where EventBus uses tomllib directly, and confirm the Known Deviation CI-001 entry accurately reflects the resolved state.

## Scope

- Modify only `docs/adr/ADR-002-config-isolation.md`
- Verify Claims section accuracy against current implementation
- Update any stale claims or Known Deviations entries

## Assumptions

- CI-001 resolution (2026-08-25) is valid and complete
- EventBus config loading via tomllib is intentional and documented
- No other processes violate the ConfigLoader.restrict_to() invariant

## Design decisions

- Preserve existing Known Deviation format; update status fields only
- Do not change Decision #9 text (it states the design intent, not current reality)
- Add a note to Decision #9 clarifying the EventBus exception

## Alternatives considered

### Alternative A: Rewrite Decision #9 to reflect current reality

**Reason for rejection:** Decision statements should express design intent, not implementation status. Changing them would conflate policy with observation.

### Alternative B: Remove Known Deviation CI-001 entirely

**Reason for rejection:** CI-001 documents an important architectural deviation that operators need visibility into. Removing it would lose audit trail.

## Implementation

### Target file

`docs/adr/ADR-002-config-isolation.md`

### Procedure

1. Read current CI-001 Known Deviation entry (lines 363-375)
2. Verify CI-001 status matches actual resolution date (2026-08-25)
3. Check if any new Known Deviations have emerged since CI-001 was created
4. Update CI-001 entry if needed (status, notes, owner)
5. Add a clarification note to Decision #9 about the EventBus exception
6. Run `tools/check_adr_reference.py --file docs/adr/ADR-002-config-isolation.md` to validate ADR structure

### Method

Direct file modification with targeted edits.

### Details

#### Step 1: Verify CI-001 entry

Current CI-001 entry (lines 363-375):
```markdown
### CI-001: EventBus does NOT use ConfigLoader at all

- **Known Issue**: CI-001
- **Type**: Design Deviation
- **Summary**: EventBus uses tomllib directly for config loading, bypassing ConfigLoader.restrict_to() permission checks
- **Conflicting Source**: docs/adr/ADR-002-config-isolation.md:Decision #9, scripts/eventbus/config.py (load_config()), scripts/eventbus/app.py
- **Expected Design**: All processes MUST load config through ConfigLoader.restrict_to() to enforce process-level config ownership boundaries
- **Observed Implementation**: EventBus config.py loads its own config via tomllib without calling restrict_to(), allowing it to access configs outside its declared scope
- **Impact**: Config isolation invariant violated for EventBus; could read/write configs belonging to other processes
- **Recommended Action**: EventBus cannot import ConfigLoader (.importlinter eventbus-is-isolated contract). Resolved via a local invariant instead: load_config()'s docstring states callers must pass get_config_path()'s return value, and a regression test in tests/eventbus/test_eventbus_config.py locks both call sites in app.py to that invariant. Agent-side, ConfigLoader.restrict_to("agent.toml") was added to AgentContext.__init__ (scripts/agent/context.py).
- **Owner**: TBD
- **Status**: Resolved (2026-08-25)
- **Resolution Target**: Before ADR-002 moves from Proposed to Accepted status
```

Verify:
- Status field shows "Resovled (2026-08-25)" — confirmed correct
- Recommended Action describes the resolution mechanism — confirmed accurate
- Owner is "TBD" — needs assignment

#### Step 2: Add clarification to Decision #9

Add after Decision #9:
```markdown
9. 共通Config Loaderの利用は許可するが、プロセスごとに許可ファイルを限定し、許可外ファイルの読込をRuntime Errorとする。
   *Note: EventBus is an exception — it loads config via tomllib directly (see CI-001).*
```

#### Step 3: Assign CI-001 Owner

Change `**Owner**: TBD` to `**Owner**: <assignee>` based on current team structure.

#### Step 4: Validate ADR structure

Run:
```bash
python tools/check_adr_reference.py --file docs/adr/ADR-002-config-isolation.md
```

## Compatibility considerations

- Existing consumers of this ADR rely on Decision #9 as design intent; adding a note does not change the decision
- CI-001 resolution is already implemented; updating the ADR entry is documentation-only

## Security considerations

- CI-001 represents a known security gap (EventBus can potentially access configs outside its scope)
- The resolution (local invariant + regression test) mitigates but does not fully eliminate the risk
- Operators should be aware of this limitation during deployment

## Rollback considerations

- Changes are documentation-only; no code rollback needed
- If CI-001 resolution is later found insufficient, revert the Status field to "Open"

## Validation plan

1. Manual review of CI-001 entry against current implementation
2. Confirm EventBus config.py still uses tomllib (no regression back to ConfigLoader)
3. Confirm regression test in `tests/eventbus/test_eventbus_config.py` still passes
4. Run `tools/check_adr_reference.py` to validate ADR structure

## Completion criteria

- [ ] CI-001 entry verified as accurate and up-to-date
- [ ] Clarification note added to Decision #9
- [ ] CI-001 Owner assigned
- [ ] ADR structure validation passes
- [ ] No unintended changes to Decision statements

## Out of scope

- Modifying Decision #9 text (design intent remains unchanged)
- Adding new Known Deviations unless discovered during verification
- Changing EventBus config loading mechanism
- Updating other ADRs or governance documents

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Verify CI-001 Known Deviation entry accuracy | Pending | — | — | |
| 2 | Add clarification note to Decision #9 | Pending | — | — | |
| 3 | Assign CI-001 Owner | Pending | — | — | |
| 4 | Run ADR structure validation | Pending | — | — | |

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
- **Requirement ID**: REQ-002 (config isolation enforcement)
- **Source issue**: N/A
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260914-180730_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260915-000842
- **Related target files**: docs/adr/ADR-002-config-isolation.md
