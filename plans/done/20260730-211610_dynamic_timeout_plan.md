# Work Plan: Dynamic Health Check Timeout Based on Startup Timeout Configuration

## Goal

Make the health check request timeout configurable and proportional to the overall startup timeout, eliminating the hardcoded 5-second value that causes false failures for slow-starting servers.

## Scope

**In-Scope:**
- Replace hardcoded `timeout=5.0` in health check client creation with a computed value
- Compute timeout as a fraction of `cfg.startup_timeout_sec` capped at a maximum

**Out-of-Scope:**
- Changing the health check polling interval (0.5 seconds)
- Changing the re-check interval for ongoing health monitoring
- Adding jitter or exponential backoff to the timeout calculation

## Assumptions

1. A fraction of 1/10 of the startup timeout provides reasonable per-request timeout while allowing retries within the overall window
2. Maximum timeout of 15 seconds prevents unreasonably long individual requests
3. Minimum timeout of 3 seconds ensures the timeout isn't too aggressive for fast-starting servers

## Unknowns

| ID | Unknown Description | Evidence Missing | Resolution Path | Blocking? (True/False) |
|---|---|---|---|---|
| UNK-01 | What is the typical range of startup_timeout_sec values across deployments? | Config audit | Review TOML configs for startup_timeout_sec values | False |
| UNK-02 | Is there a minimum timeout below which health checks fail even for healthy servers? | Empirical testing | Test with various timeout values | False |

## Affected Areas & Tool Evidence

- **Affected Files:**
  - `scripts/agent/http_lifecycle.py` — replace hardcoded `timeout=5.0` with computed value in two locations (lines 177-178 and line 329)
- **Blast Radius:** Health check timing behavior changes; servers that previously timed out may now succeed
- **Risk Metrics:** Moderate — affects health check reliability which impacts startup success rate
- **Deploy Impact:** No deploy.sh changes required

## Implementation Steps

1. **Phase 1: Preparation**
   - [ ] Audit TOML configs to understand current startup_timeout_sec values

2. **Phase 2: Core Logic Implementation**
   - [ ] In `verify_running_async()`, compute timeout: `hc_timeout = min(max(cfg.startup_timeout_sec // 10, 3.0), 15.0)`
   - [ ] Replace `timeout=httpx.Timeout(timeout=self._HEALTH_RECHECK_TIMEOUT_SEC)` with `timeout=httpx.Timeout(timeout=hc_timeout)`
   - [ ] In `start()`, compute timeout similarly before creating httpx.AsyncClient on line 329
   - [ ] Consider whether the re-check timeout (`_HEALTH_RECHECK_TIMEOUT_SEC`) should also be dynamic

3. **Phase 3: Deployment & Verification**
   - [ ] Run `ruff check scripts/agent/http_lifecycle.py` to verify lint passes
   - [ ] Run `pytest tests/test_lifecycle*.py -v` to verify existing tests pass
   - [ ] Verify no new mypy errors introduced

## Validation Plan

| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| `scripts/agent/http_lifecycle.py` | Integration test verifying health check succeeds when server responds within startup timeout but after 5 seconds | Manual verification via code review | Correct timeout computation |
| `scripts/agent/http_lifecycle.py` | Unit test verifying timeout calculation logic | `pytest tests/test_lifecycle*.py -v -k timeout` | Computation correct |

## Risks & Mitigations

- **Risk:** Proportional timeout could be too short for very fast-starting servers if startup_timeout_sec is small → **Mitigation:** Enforce minimum timeout of 3 seconds
- **Risk:** Proportional timeout could be too long for servers that respond quickly → **Mitigation:** Cap at 15 seconds maximum
- **Risk:** Existing tests assume 5-second timeout → **Mitigation:** Update test assertions to use computed timeout values

## Traceability

- Workflow phase: requirement-to-plan
- Source issue: N/A
- Source requirement: requires/20260730-204332_require.md
- Source plan: N/A
- Source implementation procedure: N/A
- Generated at: 20260730-211610
- Related target files: scripts/agent/http_lifecycle.py
