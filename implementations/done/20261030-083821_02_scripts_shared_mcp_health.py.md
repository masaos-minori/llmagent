# Implementation Procedure: mcp_health.py reason codes and retry_after derivation

## Goal

Add the normalized health reason codes and a pure `retry_after_seconds` (new) derivation to
`scripts/shared/mcp_health.py` (REQ-001; plan AC-2).

## Scope

**In scope:**
- `scripts/shared/mcp_health.py`: reason-code constants and
  `cooldown_remaining()`/`retry_after_seconds()` derivation on `McpServerHealthRegistry`.

**Out of scope:**
- The `DynamicAvailabilityHint` (new) DTO shape (row 01 owns it). Attaching hints to results
  (row 03). No change to circuit thresholds, cooldown values, or state-transition
  semantics (plan Out-of-Scope: "Changing circuit-breaker thresholds or the half-open
  policy").

## Assumptions
- Verified at HEAD `124e340b4`: `McpServerHealthRegistry` (`mcp_health.py:21`) holds
  `_failure_threshold=3`, `_half_open_cooldown_sec=30.0`, `_unavailable_since`, and the
  states `HEALTHY/DEGRADED/UNAVAILABLE/HALF_OPEN/UNKNOWN` (`:11-18`); `is_unavailable()`
  is **not pure** — it performs the UNAVAILABLE→HALF_OPEN transition and trial acquire as
  side effects (`:81-102`).
- The derivation method must never call `is_unavailable()`; it reads `_states`,
  `_unavailable_since`, and `_half_open_cooldown_sec` directly.

## Design decisions
- Closed reason set as module constants (plan Assumption: small closed enum):
  `HEALTH_REASON_SERVER_UNAVAILABLE = "server_unavailable"`,
  `HEALTH_REASON_HALF_OPEN_TRIAL_IN_PROGRESS = "half_open_trial_in_progress"`. They match
  the `Literal` in row 01; this module is the canonical owner of the strings.
- `cooldown_remaining(server_key) -> float`: for `UNAVAILABLE`,
  `max(0.0, _half_open_cooldown_sec - (time.monotonic() - _unavailable_since[key]))`;
  `0.0` for every other state or unknown key. Pure read-only method.
- `retry_after_seconds(server_key) -> int | None`: `math.ceil(cooldown_remaining(...))`
  when state is `UNAVAILABLE`; `None` for `HALF_OPEN` (the trial window is already open —
  no timing to convey, plan Assumption "optional `retry_after_seconds` (new)") and `None` for
  all other states. `int`, never negative (plan Design: `max(0, cooldown_remaining)`).
- No new stored state: both methods are computed from existing fields at call time.

## Alternatives considered
- Storing `retry_after_seconds` (new) per server at failure time: rejected — drifts against
  cooldown reconfiguration and duplicates `_unavailable_since` (plan Implementation
  Intent: "computed, not stored in new state").
- Reusing `is_unavailable()` for the check: rejected — its state-transition side effect
  would change dispatch behavior from a diagnostics/derivation call.

## Implementation
### Target file
`scripts/shared/mcp_health.py`

### Procedure
1. Add the two reason constants at module level.
2. Add `cooldown_remaining()` and `retry_after_seconds()` methods to
   `McpServerHealthRegistry` after `get_state`.
3. Import `math` (module already imports `time`).

### Method
- Additive-only edit; no existing method body changes.

### Details
- `retry_after_seconds` (new) is `int` (ceil) so hints render whole seconds to operators;
  sub-second precision is not surfaced.
- Do not export the reason constants from `transport_dto` (row 01 imports only
  `McpServerHealthState`); the invoker (row 03) imports the reason constants from here.

## Compatibility considerations
- Health consumers (`tool_transport_invoker`, `mcp_status`, `startup_reporter`,
  `cmd_mcp`) see no behavior change from this row; new methods are additive.
- `tests/shared/test_mcp_health.py` characterization: existing state-machine tests must
  stay green untouched.

## Security considerations
- Reason codes are closed constants; no server-controlled strings enter them (plan Risk:
  prompt-injection surface).

## Rollback considerations
- Reverting removes constants + two methods; row 03 (the only consumer of the constants
  at this phase) must be reverted together.

## Validation plan
- Row 08 (`tests/shared/test_mcp_health.py`): derivation at cooldown boundary
  (just-before/after expiry), `UNAVAILABLE` → positive int, `HEALTHY`/`DEGRADED`/
  `HALF_OPEN`/unknown key → `None`/0.0, purity assertion (state and trial sets unchanged
  after calls).
- `uv run pytest tests/shared/test_mcp_health.py`; `uv run mypy
  --no-namespace-packages scripts/`.

## Completion criteria
- Two reason constants and two pure derivation methods exist with the stated semantics;
  all pre-existing registry tests pass unchanged.

## Out of Scope
- Hint DTO (row 01), invoker attachment (row 03), guard counters (row 04), docs (row 14).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Add reason constants, `cooldown_remaining()`, `retry_after_seconds()` | Completed | 20261030-202734 | 20261030-202759 | row 03 follow-up: reason constants annotated as Literal so they type-check against the hint field |
| 2 | Confirm existing registry tests pass unchanged (`uv run pytest tests/shared/test_mcp_health.py`) | Completed | — | 20261030-202759 |  |
| 3 | Run `uv run mypy --no-namespace-packages scripts/` and `lint-imports` | Completed | — | 20261030-202759 |  |

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
- **Requirement ID**: `REQ-001`
- **Source issue**: `issues/20261029-104507_toolhint001_dynamic-tool-health-hints.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/done/20261029-215111_toolhint001_dynamic-tool-health-hints.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261030-083821
- **Related target files**: `scripts/shared/mcp_health.py`