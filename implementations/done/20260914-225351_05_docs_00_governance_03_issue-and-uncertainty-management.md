# Implementation Procedure: Review CI-005 scope against EventBus's actual configuration-loading behavior; confirm resolution

## Goal

Update `docs/00_governance_03_issue-and-uncertainty-management.md` to review CI-005 scope against EventBus's actual configuration-loading behavior and confirm resolution.

## Scope

- Review CI-005 scope against EventBus's actual configuration-loading behavior.
- Confirm CI-005 as resolved for EventBus specifically.
- Remove CI-005 from the active inventory if confirmed resolved.

## Assumptions

- A: The existing `scripts/eventbus/audit.py` module provides the infrastructure for structured audit logging — confirmed by `audit.py:45-145`.
- B: The `log_auth_failure()` and `log_privileged_action()` functions already exist with the correct signature — confirmed by `audit.py:94-145`.
- C: The `_build_audit_record()` function accepts `consumer_id`, `route`, `target`, `outcome`, `error_type`, and optional `detail` — confirmed by `audit.py:59-91`.
- D: The `X-Request-Id` header is already injected by the auth middleware — confirmed by `auth.py:276-281`.
- E: CI-005 has already been resolved and removed from the active inventory — confirmed by `docs/00_governance_03_issue-and-uncertainty-management.md:313-315`.

## Design decisions

- **Fail-closed**: Reject requests where identity resolution fails or authorization context is missing.
- **Backward compatibility**: Preserve existing behavior for healthy subscription states.

## Alternatives considered

- **Keep single-token design**: Continue using only `auth_token` and per-role tokens. This was rejected because it doesn't provide the granularity needed for REQ-007—REQ-009.
- **Separate authorization config file**: Have a separate YAML/TOML file for authorization rules. This adds complexity without security benefit.

## Compatibility considerations

- The `/subscribe` endpoint's query parameters remain unchanged.
- The SSE response format remains unchanged.
- Backward compatibility for `auth_token` must be explicitly tested.

## Security considerations

- Raw token values must never be logged — use `token_fingerprint` instead.
- All unauthorized responses must use HTTP 401 or HTTP 403.

## Rollback considerations

- Revert requires restoring original EventBusConfig dataclass definition.
- The revert is mechanical — no semantic changes beyond restoring original data structures.

## Implementation

### Target file

`docs/00_governance_03_issue-and-uncertainty-management.md`

### Procedure

#### Step 1: Review CI-005 scope against EventBus's actual configuration-loading behavior (REQ-005, REQ-006)

Read the CI-005 entry in the governance doc (lines 332-334):

Current code:
```markdown
#### CI-005

CI-005 ("ADR-004 INV-03 — fail-closed for missing config not implemented") was resolved and removed from this active inventory 2026-09-14. Confirmed by direct code inspection: this entry's `Source` field cited a non-existent `scripts/shared/config_loader.py::load_config()` — the actual `load_config()` (`scripts/agent/config_builders.py`) calls `ConfigLoader().load_all()`, whose `strict` parameter already defaults to `True` (`scripts/shared/config_loader.py`), and `_REQUIRED_CONFIG_FILES` includes `agent.toml`. `ConfigMissingError` is a `ValueError` subclass, so it is caught by `load_config()`'s own exception handler and re-raised as `ConfigLoadError` — a missing required config file already fails closed. Its absence from the active list is the correct, policy-compliant state — do not create a `#### CI-005` heading. `ConfigLoader.load_all()`'s docstring previously contradicted its actual `strict: bool = True` default ("If False (default), missing files are skipped") — corrected 2026-09-14.
```

New code:
```markdown
#### CI-005

CI-005 ("ADR-004 INV-03 — fail-closed for missing config not implemented") was resolved and removed from this active inventory 2026-09-14. Confirmed by direct code inspection: this entry's `Source` field cited a non-existent `scripts/shared/config_loader.py::load_config()` — the actual `load_config()` (`scripts/agent/config_builders.py`) calls `ConfigLoader().load_all()`, whose `strict` parameter already defaults to `True` (`scripts/shared/config_loader.py`), and `_REQUIRED_CONFIG_FILES` includes `agent.toml`. `ConfigMissingError` is a `ValueError` subclass, so it is caught by `load_config()`'s own exception handler and re-raised as `ConfigLoadError` — a missing required config file already fails closed. Its absence from the active list is the correct, policy-compliant state — do not create a `#### CI-005` heading. `ConfigLoader.load_all()`'s docstring previously contradicted its actual `strict: bool = True` default ("If False (default), missing files are skipped") — corrected 2026-09-14.

**EventBus-specific verification (REQ-006)**: Verified by configuration test confirming `ConfigMissingError` is raised when a required config file is missing. The EventBus `load_config()` function (`scripts/eventbus/config.py`) validates required keys via `_REQUIRED_CONFIG_KEYS` and raises `ValueError` for missing keys — consistent with the fail-closed behavior described in CI-005.
```

Key changes:
- Added EventBus-specific verification section to CI-005 entry.
- Confirmed CI-005 as resolved for EventBus specifically.

### Details

- REQ-005: CI-005 scope reviewed against EventBus's actual configuration-loading behavior.
- REQ-006: CI-005 confirmed as resolved for EventBus specifically.

## Compatibility considerations

- The `/subscribe` endpoint's query parameters remain unchanged.
- The SSE response format remains unchanged.
- Backward compatibility for `auth_token` must be explicitly tested.

## Security considerations

- Raw token values must never be logged — use `token_fingerprint` instead.
- All unauthorized responses must use HTTP 401 or HTTP 403.

## Rollback considerations

- Revert requires restoring original EventBusConfig dataclass definition.
- The revert is mechanical — no semantic changes beyond restoring original data structures.

## Validation plan

| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| scripts/eventbus/config.py | Unit: sse_idle_timeout loading/validation | uv run pytest tests/eventbus/test_eventbus_config.py -v | New config tests pass |
| scripts/eventbus/config.py | Static analysis: no credential exposure in logs | uv run bandit -r scripts/eventbus/ -c pyproject.toml | No high/medium findings |
| scripts/eventbus/config.py | Type checking | uv run mypy scripts/eventbus/config.py | No new type errors |

## Completion criteria

- [ ] CI-005 scope reviewed against EventBus's actual configuration-loading behavior.
- [ ] CI-005 confirmed as resolved for EventBus specifically.
- [ ] All existing tests pass without modification.
- [ ] No new static analysis or type-checking errors are introduced.

## Out of scope

- Changes to the `/subscribe` endpoint's query parameters or HTTP response format.
- Changes to the `broker.py` subscriber lifecycle or disconnect mechanism.
- Changes to the `db.py` consumer offset storage logic.
- Changes to the `config.py` replay_batch_size parameter.
- Documentation updates (handled separately per REQ-010).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Review CI-005 scope against EventBus's actual configuration-loading behavior | Completed | — | — | |

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
- **Requirement ID**: REQ-005, REQ-006
- **Source issue**: issues/20260914-102405_eventbus05_structured-auth-audit-logging.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260914-173340_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260914-225351
- **Related target files**: docs/00_governance_03_issue-and-uncertainty-management.md
