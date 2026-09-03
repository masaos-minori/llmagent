## Goal

Confirm `build_agent_config()`'s `security_profile_val` branch ambiguity is closed as a consequence of REQ-001's fix — with `agent.toml` missing, the process aborts before `security_profile_val` is computed.

## Scope

Verify the consequence of REQ-001 on `scripts/agent/config_builders.py`. No separate code change is required here; the fix is a downstream effect of making `load_all()` strict by default.

## Assumptions

- REQ-001's fix (making `load_all()` strict by default) is applied first.
- `build_agent_config()` calls `ConfigLoader().load_all()` at line 60 without passing `strict`, so it inherits the new default.
- `security_profile_val = SecurityProfile(cfg.get("security_profile", "local"))` at line 447 becomes unreachable on missing file as a consequence.

## Design decisions

- No code change is needed here. The fix is achieved through REQ-001's change alone.
- A regression test should be added to confirm the consequence (REQ-002).

## Alternatives considered

- Adding an explicit `strict=True` call at line 60. Rejected because REQ-001's default change makes this redundant.
- Adding a defensive check for missing `security_profile` key. Rejected because the root cause (missing file) is fixed upstream.

## Implementation

### Target file

`scripts/agent/config_builders.py`

### Procedure

No code modification required. Confirm the consequence of REQ-001's fix by verifying that `build_agent_config()` aborts before `security_profile_val` is computed when `agent.toml` is missing.

### Method

1. After applying REQ-001's fix, verify that `ConfigLoader().load_all()` at line 60 raises `ConfigMissingError` when `agent.toml` is missing.
2. Confirm that execution never reaches `security_profile_val = SecurityProfile(cfg.get("security_profile", "local"))` at line 447.
3. Add a regression test in `tests/agent/test_startup.py` to assert this behavior.

### Details

1. Read `scripts/agent/config_builders.py` lines 55-65 to confirm `load_all()` call site.
2. Read `scripts/agent/config_builders.py` lines 440-450 to confirm `security_profile_val` computation location.
3. After REQ-001 is applied, add a test in `tests/agent/test_startup.py` that verifies `build_agent_config()` raises `ConfigMissingError` when `agent.toml` is missing.

## Compatibility considerations

- No compatibility impact beyond REQ-001's change. The consequence is automatic.

## Security considerations

- This is a critical security consequence: with `agent.toml` missing, `ProductionConfigValidator`'s checks are not reachable at all (REQ-002), preventing the same misconfiguration from being silently routed onto its non-fatal branch.

## Rollback considerations

- No rollback needed for this file specifically. Only REQ-001's rollback applies.

## Validation plan

Run `uv run pytest tests/agent/test_startup.py -v` after adding the regression test.

## Completion criteria

- Confirmed that `build_agent_config()` aborts before `security_profile_val` is computed when `agent.toml` is missing
- Regression test added and passing

## Out of scope

- Any separate fix to `ProductionConfigValidator` itself (REQ-002 is verified as a consequence, not a separate code change)
- Unknown-key rejection (REQ-004, handled separately)

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 2026-09-03 | 2026-09-03 | No code change required; consequence of REQ-001 |
| 2 | Add or update tests per Validation plan | Completed | 2026-09-03 | 2026-09-03 | Added regression test for REQ-002 |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 2026-09-03 | 2026-09-03 | All 41 tests pass, lint/typecheck/bandit clean |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Completed | 2026-09-03 | 2026-09-03 | Out of scope |

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
- **Source issue**: issues/20260902-101452_h02_config_loader_fail_closed_gap.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260902-191443_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260902-220059
- **Related target files**: scripts/agent/config_builders.py
