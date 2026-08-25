## Goal

`REQ-001`/`REQ-003` (partial): make `discover_all()`'s unreachable-server status
decision consult `cfg.failure_policy`, so a `required=True` server configured with
`failure_policy=disable-tool`/`degraded` warns and excludes tools instead of aborting
startup with `FATAL`, implementing ADR-004 Decision #8 via the existing
`unavailable_servers` mechanism.

## Scope

- **In-Scope**: change `discover_all()`'s `new_status` decision (`scripts/agent/
  services/mcp_tool_discovery.py:138-142`) from `FATAL if is_required else WARNING` to
  `FATAL if (is_required and cfg.failure_policy == FailurePolicy.FAIL_FAST) else
  WARNING`; add three regression tests to `tests/agent/services/
  test_mcp_tool_discovery.py`'s `TestDiscoverAllUnreachableServers` class.
- **Out-of-Scope**: `scripts/shared/mcp_config.py`'s `FailurePolicy` enum/field
  (already defined, default `fail-fast` confirmed backward-compatible); distinguishing
  `disable-tool` from `degraded` in execution result (both produce the same
  WARNING+exclude outcome per the source Plan's Assumptions — this remains a documented
  simplification pending ADR-004's Accepted status); `startup.py`'s log-line extension —
  covered by its own companion implementation procedure document (REQ-002).

## Assumptions

- Confirmed via Read (`scripts/agent/services/mcp_tool_discovery.py:118-173`,
  `discover_all()`) that the current decision (lines 138-142) is a plain `FATAL if
  is_required else WARNING`, never consulting `cfg.failure_policy` — confirmed via `rg
  "failure_policy|FailurePolicy" scripts/ -g '*.py'` that outside
  `scripts/shared/mcp_config.py`'s definition/parsing (lines 27, 98, 300), no consumer
  exists anywhere in `scripts/`.
- Confirmed via Read (`scripts/shared/mcp_config.py:96-98`) that
  `required_in_production`/`required_in_local` both default to `True` and
  `failure_policy` defaults to `FailurePolicy.FAIL_FAST` — so any existing
  `config/*_mcp_server.toml` without an explicit `failure_policy` key continues to
  produce `is_required and cfg.failure_policy == FAIL_FAST` == `is_required`, identical
  to the current unconditional `FATAL if is_required` behavior. No existing
  configuration's runtime behavior changes.
- Confirmed via Read (`tests/agent/services/test_mcp_tool_discovery.py:61-63,65-77`)
  that the `_server()` test helper builds `McpServerConfig(transport=TransportType.HTTP,
  url=url)` with no explicit `required_in_production`/`required_in_local`/
  `failure_policy` override, so it inherits the `True`/`True`/`FAIL_FAST` defaults —
  confirming that all eight existing tests in `TestDiscoverAllUnreachableServers`
  (lines 560-693), which all assert `FATAL`, continue to pass unmodified under the new
  decision formula (since `is_required=True` and `failure_policy=FAIL_FAST` for all of
  them).
- Confirmed via Read (`scripts/agent/services/mcp_tool_discovery.py:154-155`) that
  `unreachable.append(key)` already runs unconditionally whenever `is_unreachable` is
  true, regardless of `is_required`/`new_status` — no change needed here; the
  `RuntimeToolRegistry(unavailable_servers=...)` exclusion mechanism (lines 164-168)
  already applies uniformly.

## Design decisions

- Single-expression change to the `new_status` ternary (lines 138-142): `new_status =
  (StartupCheckStatus.FATAL if (is_required and cfg.failure_policy ==
  FailurePolicy.FAIL_FAST) else StartupCheckStatus.WARNING)`.
- Import `FailurePolicy` from `shared.mcp_config` (confirm via `rg "^from shared.mcp_config
  import" scripts/agent/services/mcp_tool_discovery.py` whether other names from that
  module are already imported, to add to the same import statement rather than a new
  one).
- Add three new test methods to the existing `TestDiscoverAllUnreachableServers` class
  (not a new class), reusing the `_server()`/`_make_ctx()` helper pattern with explicit
  `required_in_production`/`failure_policy` overrides passed via
  `dataclasses.replace(_server(url), ...)` or an equivalent explicit-construction
  pattern (confirm `McpServerConfig`'s exact construction style already used elsewhere
  in the file before choosing).

## Alternatives considered

- Changing `is_required` itself to fold in the `failure_policy` check (e.g. `is_required
  = (...) and cfg.failure_policy == FAIL_FAST`) instead of changing the `new_status`
  ternary: rejected — `is_required` is also implicitly documented by its name as "is
  this server load-bearing," a semantically distinct question from "should an
  unreachable load-bearing server abort startup," which is what `new_status` actually
  decides; keeping the two separate is clearer for a future reader.

## Implementation

### Target file
`scripts/agent/services/mcp_tool_discovery.py`

### Procedure
1. Add `FailurePolicy` to the existing `from shared.mcp_config import (...)` statement
   (or add a new import line if no such statement currently exists in this file).
2. Replace the `new_status` ternary (lines 138-142) per Design decisions.
3. In `tests/agent/services/test_mcp_tool_discovery.py`'s `TestDiscoverAllUnreachableServers`
   class, add:
   - `test_required_production_fail_fast_unreachable_stays_fatal` — `required_in_production=True`,
     `failure_policy=FailurePolicy.FAIL_FAST` (default), unreachable → assert `FATAL` in
     findings (regression confirmation of unchanged default behavior).
   - `test_required_production_disable_tool_unreachable_becomes_warning` —
     `required_in_production=True`, `failure_policy=FailurePolicy.DISABLE_TOOL`,
     unreachable → assert no `FATAL` finding, and `"srv"` appears in `result.unreachable`.
   - `test_required_production_degraded_unreachable_becomes_warning` — identical to the
     above with `failure_policy=FailurePolicy.DEGRADED`.
   - Use `security_profile=SecurityProfile.PRODUCTION` in `_make_ctx()` for all three
     new tests, since `required_in_production` (not `required_in_local`) is the field
     under test.

### Method
One ternary-expression change plus three new test methods added to an existing test
class, following its established helper-usage pattern exactly.

### Details
- Do not change `unreachable.append(key)`'s unconditional placement (line 154-155) —
  it already covers both the `FATAL` and `WARNING` cases correctly for this
  Requirement's purposes.

## Compatibility considerations

- No behavior change for any server configured without an explicit `failure_policy`
  (defaults to `FAIL_FAST`, identical to current behavior) — see Assumptions.
- A server explicitly configured `failure_policy=disable-tool`/`degraded` and
  `required_in_production=True`/`required_in_local=True` changes from aborting startup
  (`FATAL`) to warning and excluding its tools (`WARNING`) — this is the intended new
  capability, not an unintended behavior change, and requires an explicit config
  opt-in.

## Security considerations

- A misconfigured `required=True` server set to `disable-tool`/`degraded` could mask a
  genuinely load-bearing server's unavailability behind a warning instead of a hard
  startup failure — mitigated by the companion `startup.py` document's REQ-002 log
  visibility (ADR-004 Decision #5).

## Rollback considerations

- Revert the `new_status` ternary to `FATAL if is_required else WARNING` and remove the
  `FailurePolicy` import if unused elsewhere; remove the three new test methods.

## Validation plan

| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| `scripts/agent/services/mcp_tool_discovery.py` | Integration | `PYTHONPATH=scripts uv run pytest tests/agent/services/test_mcp_tool_discovery.py -v` | All 8 existing `TestDiscoverAllUnreachableServers` tests still pass (FATAL, default `fail-fast`); 3 new tests pass (fail-fast stays FATAL, disable-tool/degraded become WARNING) |
| Repository-wide | Full suite | `PYTHONPATH=scripts uv run pytest` | No new failures |

## Completion criteria

- `discover_all()`'s unreachable-server decision consults `cfg.failure_policy`.
- A `required=True` server with `failure_policy=fail-fast` (default or explicit) still
  produces `FATAL` when unreachable (AC-02, regression-safe).
- A `required=True` server with `failure_policy=disable-tool`/`degraded` produces
  `WARNING` and appears in `result.unreachable` when unreachable (AC-01).
- All 8 pre-existing tests in `TestDiscoverAllUnreachableServers` pass unmodified.

## Out of scope

- `scripts/agent/startup.py`'s log-line extension — see the companion implementation
  procedure document for REQ-002.
- Distinguishing `disable-tool` from `degraded` in execution result (see Assumptions).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Re-confirm `discover_all()`'s current branch and import structure | Pending | — | — | |
| 2 | Change the `new_status` decision to consult `cfg.failure_policy` | Pending | — | — | |
| 3 | Add 3 regression tests to `TestDiscoverAllUnreachableServers` | Pending | — | — | |
| 4 | Run the validation sequence (`rules/toolchain.md`) scoped to this file and its tests | Pending | — | — | |
| 5 | Documentation update | N/A | — | — | Not in scope for this file |

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
- **Requirement ID**: `REQ-001`, `REQ-003` (partial) — consult `failure_policy` in unreachable-server decision
- **Source issue**: `issues/20260823_adr004_failure_policy_unused_issue.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20260825-133610_plan.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260825-180630
- **Related target files**: `scripts/agent/services/mcp_tool_discovery.py`
