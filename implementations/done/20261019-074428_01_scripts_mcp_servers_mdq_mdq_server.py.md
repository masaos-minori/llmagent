## Goal

Bring `mdq-mcp` (`scripts/mcp_servers/mdq/mdq_server.py`) in line with every sibling MCP server by
adding a pre-bind, fail-closed security-posture gate: build the MDQ security posture once at module
import via `build_mdq_posture()` / `validate_mdq_security()`, expose it as a module-level
`_security_posture`, add `_enforce_posture_gate()` that reads `.validated` and raises
`SystemExit(1)` when invalid, and call the gate in `__main__` before `server.run_http()`. This
closes the bind-before-detect window described by ADR-003 (Static Availability) and ADR-004
(fail-closed).

## Scope

- **In-Scope**:
  - Build the MDQ security posture once at module import, reusing `build_mdq_posture()` /
    `validate_mdq_security()` and the dependency-collection helper extracted into
    `scripts/mcp_servers/mdq/health_check.py`.
  - Expose the posture as a module-level `_security_posture` readable as `.validated`.
  - Add `_enforce_posture_gate()` that raises `SystemExit(1)` when the posture is not validated, and
    call it in `__main__` before `server.run_http()`.
- **Out-of-Scope**:
  - Changing how MDQ computes or publishes its security posture on `/health`.
  - Modifying any other MCP server's `_enforce_posture_gate()`.
  - Changing `MCPServer.run_http()`.
  - Altering the module-level empty-token guard or the per-request `allowed_dirs` authorization.
  - Any `docs/*.md` change.

## Assumptions

- `build_mdq_posture()` / `validate_mdq_security()` never raise (per `run_startup_validation()`'s
  contract in `scripts/shared/security/startup_flow.py`), so building the posture at import cannot
  crash module import.
- Building the posture at import introduces no new DB side effect: `MdqService` already connects to
  the DB and creates tables at import (`_service = MdqService()` in `mdq_service.py`).
- The empty-token guard stays at module import; the posture gate is additive and runs only in
  `__main__`, so importing the module in tests never triggers `SystemExit`.
- The dependency-collection helper lives in `health_check.py` (not moved to `mdq_security_validation.py`)
  to respect the `mcp_servers → db, shared` import layer; `mdq_server.py` imports it from there.
- A fresh install with an empty DB yields a validated posture: `_index_check` returns OK when
  documents and FTS rows are both zero.

## Design decisions

- Mirror the sibling `web_search_server.py` shape exactly: a module-level `_security_posture` built
  once at import, plus `_enforce_posture_gate()` that reads `.validated` and raises `SystemExit(1)`.
- Fail fast at the process boundary (`__main__`) rather than adding per-request or `/health`-based
  detection; this restores contract parity with all siblings.
- The gate reads only `.validated`; the `ready` payload is derived elsewhere from dependencies plus
  `.validated`, so this module never invents its own `Ready` rule.

## Alternatives considered

- Adding a `/health`-based startup check on the Agent side only — rejected: it leaves the
  bind-before-first-probe window open locally and deviates from the shared sibling contract.
- Coercing the posture build into `MCPServer.run_http()` — rejected: the gate must run *before*
  binding, i.e. in `__main__`, not inside the HTTP runner.

## Implementation

### Target file

`scripts/mcp_servers/mdq/mdq_server.py`

### Procedure

1. Confirm via grep that `mdq_server.py` currently has no `_enforce_posture_gate` /
   `_security_posture` symbol and that its `__main__` (line ~454) calls only `server.run_http()`.
   Record the current `__main__` block. (AC-005 baseline)
2. Import the shared dependency-collection helper and posture builders at the top of
   `mdq_server.py`:
   ```python
       from mcp_servers.mdq.health_check import _collect_dependencies
       from mcp_servers.mdq.mdq_security_validation import build_mdq_posture
   ```
   Verify there is no circular import (`health_check.py` must not import `mdq_server`); if it does,
   resolve per the import-layer rule before proceeding.
3. Build the MDQ posture once at module import, immediately after the existing module-level
   `_service = MdqService()` construction, exposing it as a module-level `_security_posture`:
   ```python
       _mdq_cfg, _db_file_present, _schema_error, _schema_checked, _index_stats = _collect_dependencies()
       _security_posture = build_mdq_posture(
           _mdq_cfg, _db_file_present, _schema_error, _schema_checked, _index_stats
       )
   ```
   Keep this defensive (never raise at import); if `_collect_dependencies()` could raise, wrap the
   build so an unparseable config yields an unvalidated posture rather than a crashed import. (REQ-002, AC-002)
4. Add `_enforce_posture_gate()` mirroring the sibling implementation:
   ```python
       def _enforce_posture_gate() -> None:
           \"\"\"Refuse HTTP bind when the MDQ posture is not validated (fail-closed).

           Reads only `_security_posture.validated`; logs failed check ids and reason
           codes and raises SystemExit(1) when not validated. Runs in __main__ only,
           so importing this module in tests never triggers SystemExit.
           \"\"\"
           if _security_posture.validated:
               return
           failed = ", ".join(
               f"{check.check_id}:{check.reason_code}"
               for check in _security_posture.checks
               if check.status is SecurityCheckStatus.FAILED
           )
           logger.error(
               "mdq-mcp: security posture FAILED (%s) — refusing to bind", failed
           )
           raise SystemExit(1)
   ```
   Use the same `SecurityCheckStatus` enum member the sibling references; confirm the exact member
   name from `mdq_security_validation.py` / the posture contract before coding. (REQ-001, AC-001)
5. In `__main__`, call `_enforce_posture_gate()` before `server.run_http()`:
   ```python
       if __name__ == "__main__":
           _enforce_posture_gate()
           server = ...  # existing construction
           server.run_http()
   ```
   Preserve the existing server construction unchanged. (REQ-001)
6. Run the affected MDQ test targets and static checks; confirm clean. (AC-001..005)

### Method

- **Build once at import (REQ-002).** Place the posture build next to the existing module-level
  service construction so it runs exactly once per process import, like the siblings. Expose the
  result as the module-level `_security_posture`.
- **Gate reads only `.validated` (REQ-001).** Do not derive `ready` here; the gate is a pure
  fail-closed switch. Log failed check ids and reason codes (no auth tokens or `allowed_dirs`
  entries) so the failure is actionable.
- **Run in `__main__` only.** The gate must not execute at import (tests import the module), so it
  lives in the `if __name__ == "__main__":` block before `run_http()`.
- **Preserve behavior (AC-005).** Leave the empty-token guard, the per-request `allowed_dirs`
  authorization, and `MCPServer.run_http()` untouched.

### Details

- `REQ-001`: the MDQ entry point validates its security posture as a fail-closed gate before binding
  HTTP and exits non-zero (`SystemExit(1)`) when the posture is not validated.
- `REQ-002`: the MDQ security posture is computed once at module import via `build_mdq_posture()` /
  `validate_mdq_security()`, exposed as a module-level `_security_posture` readable as `.validated`.
- **UNK-01:** the Agent-side `startup_validation.py` also relies on `/health`, so the local gate
  still closes the bind-to-first-probe window and restores contract parity. Not blocking.
- **UNK-02:** an empty `allowed_dirs` only logs a warning at import and does not fail closed; the
  gate fails that check, so the gate adds coverage the model lacks. Not blocking.

> **Plan Gap (scope decision for the Plan, not applied here):** building the posture at import calls
> `_collect_dependencies()`, which loads config and opens the DB. If that helper can raise during
> import (e.g. a malformed config), the module import would fail. The plan's risk mitigation states
> the posture build "never raises"; if evidence shows otherwise, wrap the import-time build so a
> bad config yields an unvalidated posture (gate fails closed at startup) rather than crashing
> import. This is an implementation-phase decision outside the frozen file scope.

## Compatibility considerations

Behavior-preserving for valid configs; adds a pre-bind fail-closed gate that every sibling already
has. No public/runtime interface change; `MCPServer.run_http()` is unchanged. The gate runs only in
`__main__`, so importing the module in tests never triggers `SystemExit`. No `docs/*.md` change.

## Security considerations

Adds a fail-closed bind gate (positive security impact): misconfiguration now refuses to listen
instead of accepting connections. Does not weaken the existing empty-token guard or
`allowed_dirs` authorization.

## Rollback considerations

N/A: revert the commit.

## Validation plan

| Target File/Module | Testing Strategy | Tool / Command | Expected Outcome |
|---|---|---|---|
| `scripts/mcp_servers/mdq/mdq_server.py` | Unit: gate fails closed on invalid posture, passes on valid posture | `uv run pytest tests/mcp_servers/mdq/test_mdq_health_posture.py` | gate raises `SystemExit(1)` on invalid posture, passes on validated posture |
| `scripts/mcp_servers/mdq/mdq_server.py` | Static — lint and type check | `uv run ruff check`, `uv run mypy --no-namespace-packages scripts/` | Clean (no new findings) |
| `scripts/mcp_servers/mdq/mdq_server.py` | Security | `uv run bandit` | No new high/medium findings |

## Completion criteria

- The MDQ posture is built once at import and readable as `.validated` (AC-002).
- `_enforce_posture_gate()` fails closed (`SystemExit(1)`) before `run_http()` when the posture is
  not validated (AC-001).
- The empty-token guard, per-request `allowed_dirs` authorization, and other servers' gates are
  unchanged (AC-005).

## Out of scope

Changing how MDQ computes or publishes its security posture on `/health`, modifying any other MCP
server's `_enforce_posture_gate()`, changing `MCPServer.run_http()`, altering the module-level
empty-token guard or the per-request `allowed_dirs` authorization, and any `docs/*.md` change.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Phase 1: Extract dependency-collection helper from `check_health()` | Completed | — | 20261019-185700 | REQ-003; `scripts/mcp_servers/mdq/health_check.py` Build MDQ posture once at import via build_mdq_posture() over the five trailing values of _collect_dependencies(); added _enforce_posture_gate() reading .validated and raising SystemExit(1) in __main__ before run_http(), mirroring web_search_server. Uses the module's shared Logger (propagate=False) so the refusal logs to file/stderr. 415 MDQ tests pass; static checks clean. |
| 2 | Phase 2a: Build MDQ posture once at import | Completed | — | 20261019-185700 | REQ-002; `scripts/mcp_servers/mdq/mdq_server.py` Build MDQ posture once at import via build_mdq_posture() over the five trailing values of _collect_dependencies(); added _enforce_posture_gate() reading .validated and raising SystemExit(1) in __main__ before run_http(), mirroring web_search_server. Uses the module's shared Logger (propagate=False) so the refusal logs to file/stderr. 415 MDQ tests pass; static checks clean. |
| 3 | Phase 2b: Add `_enforce_posture_gate()` and call it in `__main__` | Completed | — | 20261019-185700 | REQ-001; `scripts/mcp_servers/mdq/mdq_server.py` Build MDQ posture once at import via build_mdq_posture() over the five trailing values of _collect_dependencies(); added _enforce_posture_gate() reading .validated and raising SystemExit(1) in __main__ before run_http(), mirroring web_search_server. Uses the module's shared Logger (propagate=False) so the refusal logs to file/stderr. 415 MDQ tests pass; static checks clean. |
| 4 | Phase 3: Add `test_mdq_health_posture.py` | Completed | — | 20261019-185700 | REQ-004; `tests/mcp_servers/mdq/test_mdq_health_posture.py` Build MDQ posture once at import via build_mdq_posture() over the five trailing values of _collect_dependencies(); added _enforce_posture_gate() reading .validated and raising SystemExit(1) in __main__ before run_http(), mirroring web_search_server. Uses the module's shared Logger (propagate=False) so the refusal logs to file/stderr. 415 MDQ tests pass; static checks clean. |
| 5 | Phase 4: Static checks, MDQ test suite, deploy confirmation | Completed | — | 20261019-185700 | REQ-001..REQ-005 Build MDQ posture once at import via build_mdq_posture() over the five trailing values of _collect_dependencies(); added _enforce_posture_gate() reading .validated and raising SystemExit(1) in __main__ before run_http(), mirroring web_search_server. Uses the module's shared Logger (propagate=False) so the refusal logs to file/stderr. 415 MDQ tests pass; static checks clean. |

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
- **Requirement ID**: `REQ-001`, `REQ-002`
- **Source issue**: issues/20261018-191517_mcp002_mdq-mcp-server-lacks-pre-bind-fail-closed-security-posture-gate.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261018-222300_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261019-074428
- **Related target files**: scripts/mcp_servers/mdq/mdq_server.py