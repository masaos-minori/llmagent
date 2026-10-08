## Goal

REQ-001: Modify authorization logic for scripts/eventbus/auth.py

## Scope

- Modify only `scripts/eventbus/auth.py` per the plan Implementation Target Files table
- Related Requirements: REQ-001
- Implementation Phase: Phase 1: Core Logic

## Assumptions

- The plan frozen inventory (Implementation Target Files section) accurately reflects current source state
- REQ-REQ-001 acceptance criteria are sufficient for validation
- No additional target files are required beyond those listed in the plan

## Design decisions

- Reject `consumer_token` without `consumer_authorization` at startup config validation (fail-closed)
- Unify allow-list semantics: empty frozenset consistently means deny all
- All-role tokens (`auth_token`, `admin_token`) remain operator-only; documented as such
- `_principal` must be passed through app.py wrappers to ACK/NACK handlers

## Alternatives considered

- **Alternative**: Accept `consumer_token` without `consumer_authorization` with a warning
  - **Reason for rejection**: Violates fail-closed principle (ADR-013 INV-02); a token without an explicit allow-list must be rejected, not warned
- **Alternative**: Use a different mechanism for consumer-ID binding (e.g., subscription-bound)
  - **Reason for rejection**: Token-to-consumer-ID binding is the correct approach since ACK can arrive after a subscription disconnects

## Implementation

### Target file

`scripts/eventbus/auth.py`

### Procedure

Modify `_populate_token_maps()` to validate that `consumer_token` requires `consumer_authorization`

### Method

- Read the current source file to confirm the plan claims before making changes
- Apply the modification described in the Procedure section
- Verify the change does not introduce lint/type errors

### Details

**For `scripts/eventbus/auth.py` (REQ-001)**:
- In `_populate_token_maps()`, add validation: if `consumer_token` is set but `consumer_authorization` is not, raise `ValueError` at startup
- Current code at line 124-128 shows `consumer_allowed_ids` defaults to `None` when `consumer_authorization` is absent -- this is the gap being fixed

## Compatibility considerations

- **Backward compatibility**: Rejecting `consumer_token` without `consumer_authorization` is a breaking change for deployments using a shared consumer token without allow-list restrictions. Operators must configure `consumer_authorization` before upgrading.
- **Config format**: The `consumer_authorization` field already exists on `EventBusConfig` (confirmed in `config.py` line 104).
- **Documentation drift**: Updating ADR-013 and eventbus_02 must stay consistent with the implementation change.

## Security considerations

- Fail-closed: rejecting `consumer_token` without `consumer_authorization` prevents unauthorized access to any consumer ID.
- Removing the debug WARNING log eliminates information leakage of principal identity at WARNING level.
- The operator-only constraint for `auth_token`/`admin_token` must be enforced by deployment practice, not code.

## Rollback considerations

- Reverting the `consumer_token` validation change would restore the fail-open behavior for unrestricted CONSUMER tokens.
- Reverting the allow-list semantics change would restore the inverted empty-allow-list behavior between ACK and subscribe paths.
- Reverting the `_principal` forwarding would break NACK authorization enforcement.
- Documentation changes are low-risk to revert.

## Validation plan

| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| scripts/eventbus/auth.py | Unit: mock config without consumer_authorization, verify rejection | pytest | Config validation test passes |
| scripts/eventbus/ack_route.py | Unit: mock allow-list with empty frozenset, verify deny-all | pytest | Allow-list semantics test passes |
| scripts/eventbus/app.py | Integration: verify `_principal` passed to nack_route | pytest | NACK authorization test passes |
| scripts/eventbus/ack_route.py | Lint/type: ruff, mypy | ruff, mypy | No lint/type errors |
| docs/10_adr/ADR-013-eventbus-authentication-authorization.md | Documentation review | Manual | INV-07 documented |
| docs/10_adr/ADR-006-eventbus-sqlite-persistence-and-sse-delivery.md | Documentation review | Manual | INV-10 revised |

## Completion criteria

- [ ] `consumer_token` without `consumer_authorization` is rejected at startup (REQ-001).
- [ ] Empty allow-list (`frozenset()`) consistently means deny all in both ACK and NACK (REQ-002).
- [ ] `_principal` is forwarded to NACK handler (REQ-003).
- [ ] Debug WARNING log removed from `_do_ack()` (REQ-004).
- [ ] ADR-013 documents operator-only constraint for `auth_token`/`admin_token` (REQ-005).
- [ ] ADR-006 INV-10 revised (REQ-006).
- [ ] Unit tests cover all four decision matrix outcomes: `consumer_token` without `consumer_authorization`, empty allow-list, `_principal` missing, debug log removal.
- [ ] Integration test verifies NACK authorization enforcement.
- [ ] ruff and mypy pass with no errors.

## Out of scope

- ACK/NACK state management (separate issue)
- DLQ model changes
- Health endpoint changes of unrelated servers
- Circuit-breaker behavior
- Creating new configuration fields beyond existing `consumer_authorization`

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | — | 20261008-224128 |  |
| 2 | Add or update tests per Validation plan | Completed | — | 20261008-224128 |  |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | — | 20261008-224128 |  |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Completed | — | 20261008-224128 |  |

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
- **Source issue**: N/A: no standalone issue document generated
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261008-155840_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261008-182050
- **Related target files**: scripts/eventbus/auth.py