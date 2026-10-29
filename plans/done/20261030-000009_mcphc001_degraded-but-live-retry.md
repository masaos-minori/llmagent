## Goal
Align the post-startup health-check retry path with the spawn-phase readiness gate: `_verify_single_health` must treat a non-200 `/health` response whose body indicates `liveness == true` as degraded-but-live (tolerated) rather than fatal, matching the `is_degraded_but_live` predicate used by `poll_until_ready`.

## Priority
Medium

## Scope
- **In-Scope**:
  - Make `_verify_single_health` in `scripts/agent/startup_mcp_starter.py` consult the `liveness`-based degraded-but-live predicate before treating a non-200 as fatal.
  - Add unit tests covering both branches of the non-200 + `liveness` decision in `tests/agent/test_startup_mcp_starter.py`.
- **Out-of-Scope**:
  - Changing the retry loop, delays, or retry count in `verify_health`.
  - Altering the spawn-phase `poll_until_ready` behavior.
  - Consolidating `verify_health`'s inline degraded-but-live block into `is_degraded_but_live` (documented as a follow-up only).
  - Any non-MCP health checks.
- **Dependencies**: N/A: none.

## Background
Startup has two HTTP health/readiness gates over the same `/health` signal:
- Spawn readiness: `poll_until_ready` (in `scripts/agent/http_lifecycle_health_checker.py`) treats a non-200 response with `liveness == true` as degraded-but-live and keeps the server ready, via the shared static predicate `HealthChecker.is_degraded_but_live`.
- Post-startup health: `verify_health` in `scripts/agent/startup_mcp_starter.py` polls each subprocess server once, then delegates failures to the shared `retry_once_with_delay(_verify_single_health)` helper.

The codebase has been refactored since this asymmetry was first noted: `verify_health` now performs a single inline degraded-but-live check and drives retries through `retry_once_with_delay` rather than an inline bounded loop, and both paths raise `RuntimeError` on a genuinely dead endpoint (there is no `MCPServerHealthError` anywhere in the codebase). The remaining divergence is confined to `_verify_single_health`, the function actually executed on the retry path.

## Problem
`_verify_single_health` raises `RuntimeError` on every non-200 response without consulting `liveness`. On the direct path, `verify_health` tolerates a degraded-but-live (HTTP 503, `liveness: true`) server and moves on. But when the first attempt throws (connection error / timeout), the retry executes `_verify_single_health`, which re-raises on the same 503 + `liveness: true` body instead of tolerating it. The two phases therefore disagree on the one signal (`liveness`) that both already agree is meaningful, and the divergence is untested — no test exercises a non-200 + `liveness: true` body through `_verify_single_health`.

## Reason for Change
Latent correctness bug: the post-startup retry gate contradicts the spawn gate on the `liveness` signal, so a server that recovers to degraded-but-live after a transient connection failure is aborted instead of tolerated. Also untested, so the divergence has never been caught.

## Implementation Intent
Branch on the parsed body's `liveness` field inside `_verify_single_health` before deciding a non-200 is fatal. Reuse the exact `is_degraded_but_live` predicate from `http_lifecycle_health_checker.py` (call it rather than duplicating it) so the two phases cannot drift. A non-200 with `liveness == true` returns normally (degraded-but-live, i.e. ready); a non-200 with `liveness == false`, a non-JSON body, or a non-503 status raises `RuntimeError` as before. Keep `verify_health`'s retry semantics and exception type intact.

## Requirements
- `REQ-001`: `_verify_single_health` treats a non-200 response whose body indicates `liveness == true` as degraded-but-live (returns normally, not raised), using the same predicate as `poll_until_ready`.
- `REQ-002`: Unit tests assert both branches of the non-200 + `liveness` decision in `tests/agent/test_startup_mcp_starter.py`.
- `REQ-003`: A non-200 with `liveness == false`, a non-JSON body, or a non-503 status still raises `RuntimeError`; `verify_health` retry parameters and spawn-phase behavior are unchanged.

## Implementation Target Files
**Freeze status**: Frozen (was `Draft`; set to `Frozen` only once `issue-to-plan`
Step 8's Implementation Target Files Validation passes — see
`rules/workflow-lifecycle.md` Implementation Target Files Validation (Plan Freeze)).

This table is the canonical, frozen source of implementation scope for this Plan. Once
`Frozen`, `Implementation steps`, `Acceptance criteria`, and every downstream
`plan-to-implementation-procedure` document MUST reference file paths only from this
table — no other file may be treated as a modification target.

| File Path | Change Responsibility | Reason for Modification | Related Requirement / Acceptance Criterion | Repository Evidence | Related Tests | Validation Status |
|---|---|---|---|---|---|---|
| `scripts/agent/startup_mcp_starter.py` | Modify | Align `_verify_single_health` non-200 handling with the degraded-but-live predicate | REQ-001, REQ-003; AC1, AC3 | `_verify_single_health` raises `RuntimeError` on any non-200 without consulting `liveness`; `is_degraded_but_live` exists and is used by `poll_until_ready` (checked in Step 2) | `_verify_single_health` | Verified |
| `tests/agent/test_startup_mcp_starter.py` | Modify | Add coverage for the non-200 + `liveness` decision | REQ-002; AC2, AC4 | File exists with existing `verify_health` / `_verify_single_health` tests driven by `respx` (checked in Step 2) | `test_verify_single_health_fails_with_wrong_token`, `test_verify_health_passes_with_correct_token` | Verified |

Rules (see `rules/workflow-lifecycle.md` Implementation Target Files Validation (Plan
Freeze) for the full validation procedure):
- One row per file. A directory, glob pattern (`*`, `**`), component/module name, file
  group, or a vague phrase (e.g. "related files", "as necessary", "etc.") MUST NOT
  appear as a row — list each file individually by its exact repository-relative path.
- Record a test, configuration, schema, migration, deployment, or documentation file as
  its own row when it requires modification — do not fold it into the row for the
  source file it accompanies.
- `Validation Status` is `Verified` or `Needs confirmation` per row; every row must be
  `Verified` before this section may be marked `Frozen`.

## Reference Files
Files that must be read to implement the targets above, but MUST NOT be modified. Same
one-file-per-row discipline as `Implementation Target Files` above — no directories,
glob patterns, components, file groups, or vague phrases.

| File Path | Why It Must Be Read | Related Target File or Requirement |
|---|---|---|
| `scripts/agent/http_lifecycle_health_checker.py` | Source of the `is_degraded_but_live` predicate mirrored by `_verify_single_health`; read to copy the exact status / content-type / JSON / `liveness` logic | `scripts/agent/startup_mcp_starter.py`; REQ-001 |

## Acceptance Criteria
- A server returning HTTP 503 with `liveness: true` is treated as degraded but live by `_verify_single_health` and not raised as fatal (REQ-001, AC1).
- A server returning HTTP 503 with `liveness: false` still raises `RuntimeError` (REQ-003, AC2).
- A non-503 non-200 response still raises `RuntimeError` (REQ-003, AC3).
- Existing tests in `tests/agent/test_startup_mcp_starter.py` still pass, including the pre-existing wrong-token `RuntimeError` assertion (REQ-002, AC4).

## Tests
- Unit test: `_verify_single_health` with a mocked 503 + `{"liveness": true}` JSON body does not raise (REQ-001).
- Unit test: `_verify_single_health` with a mocked 503 + `{"liveness": false}` JSON body raises `RuntimeError` (REQ-003).
- Unit test: `_verify_single_health` with a mocked non-503 non-200 body, e.g. 401, raises `RuntimeError` (REQ-003).

## Documentation Impact
Update the docstring on `_verify_single_health` to describe the `liveness`-based degradation path. No external `docs/*.md` update required (REQ-001).

## Assumptions
- Only HTTP 503 counts as degraded-but-live, mirroring `is_degraded_but_live` (which returns `False` for any other status). Other non-200 statuses stay fatal.
- Returning normally from `_verify_single_health` on a degraded-but-live body makes `retry_once_with_delay` treat the retry as success, consistent with `verify_health`'s direct-path `continue`.
- Importing `HealthChecker` from `agent.http_lifecycle_health_checker` into `scripts/agent/startup_mcp_starter.py` introduces no import cycle: the health checker depends only on `shared.mcp_config` and `agent.secrets_masker`, neither of which imports the starter.

## Unknowns
| ID | Unknown Description | Evidence Missing | Resolution Path | Blocking? (True/False) |
|---|---|---|---|---|
| UNK-01 | Should a degraded-but-live response count toward / reset the retry budget, or short-circuit to "ok"? | None — resolved by design. | Mirror `poll_until_ready` / `is_degraded_but_live`: treat degraded-but-live as ready (return normally). | False |
| UNK-02 | Could a non-200 return a non-JSON body that should be fatal outright? | None — resolved by design. | `is_degraded_but_live` returns `False` on non-JSON, so non-JSON non-200 stays fatal. | False |

## Affected areas
`skills/DESIGN.md` Change-impact table, extended with `Churn (30d)` and `Bus Factor`
columns. The `File` column here MUST be a subset of `Implementation Target Files`'
rows — this table analyzes change-impact risk for those same files; it is not a
separate scope-of-record.

| File | Change | Blast Radius | Churn (30d) | Bus Factor | deploy.sh Impact |
|---|---|---|---|---|---|
| `scripts/agent/startup_mcp_starter.py` | Modify | Low | N/A | N/A | not applicable (rsynced) |
| `tests/agent/test_startup_mcp_starter.py` | Modify | Low | N/A | N/A | not applicable (rsynced) |

## Design
Path A (≤3 files, no public/runtime interface change, no schema change). Analysis limited to direct verification of the target files and their immediate dependency (`is_degraded_but_live`).

Fix location: `_verify_single_health` is the sole remaining divergence point. `verify_health` already tolerates degraded-but-live on its direct path and drives retries through `retry_once_with_delay`; the fix touches only the function executed on the retry path.

Predicate reuse: call `HealthChecker.is_degraded_but_live(resp)` rather than re-implementing the status / content-type / JSON / `liveness` check, so the two phases share one source of truth. The predicate returns `True` only for HTTP 503 + JSON body with `liveness == true`; every other non-200 (other status, non-JSON, `liveness == false`) returns `False` and stays fatal.

Exception type: keep `RuntimeError` for genuinely dead / non-degraded endpoints. There is no `MCPServerHealthError` in the codebase; the issue's reference to it is stale.

Existing test compatibility: the current `test_verify_single_health_fails_with_wrong_token` asserts a 401 raises `RuntimeError` matching `"HTTP 401"`. A 401 is not 503, so it remains fatal and the assertion still holds after this change.

Optional follow-up (out of scope): `verify_health` contains an inline copy of the degraded-but-live check that duplicates `is_degraded_but_live`; consolidating it would remove a second drift site. Not required by the acceptance criteria and left as a separate change.

## Implementation steps
1. **Phase 1: Align `_verify_single_health` with the degraded-but-live predicate**
   - [ ] Import `HealthChecker` from `agent.http_lifecycle_health_checker` at the top of `scripts/agent/startup_mcp_starter.py` (REQ-001; verify no import cycle via the existing test-suite import).
   - [ ] In `_verify_single_health`, on a non-200 response, call `HealthChecker.is_degraded_but_live(resp)`; if `True`, log the degraded-but-live condition and return normally; otherwise raise `RuntimeError(f"HTTP {resp.status_code}")` as before (REQ-001, REQ-003).
   - [ ] Update the `_verify_single_health` docstring to describe the `liveness`-based degradation path (REQ-001).
2. **Phase 2: Add branch coverage**
   - [ ] Add a test asserting `_verify_single_health` does not raise on a mocked 503 + `{"liveness": true}` JSON body (REQ-001).
   - [ ] Add a test asserting `_verify_single_health` raises `RuntimeError` on a mocked 503 + `{"liveness": false}` JSON body (REQ-003).
   - [ ] Add a test asserting `_verify_single_health` raises `RuntimeError` on a mocked non-503 non-200 body, e.g. 401 (REQ-003).
3. **Phase 3: Deployment & Verification**
   - [ ] Run `uv run pytest tests/agent/test_startup_mcp_starter.py` and confirm all tests pass, including the pre-existing wrong-token assertion (REQ-002, REQ-003).

## Validation plan
| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| `scripts/agent/startup_mcp_starter.py::_verify_single_health` | Unit: mock httpx response via respx for 503+liveness:true, 503+liveness:false, 401 | `uv run pytest tests/agent/test_startup_mcp_starter.py` | 503+liveness:true does not raise; 503+liveness:false and 401 raise `RuntimeError` |
| `tests/agent/test_startup_mcp_starter.py` | Regression: pre-existing wrong-token assertion still holds | `uv run pytest tests/agent/test_startup_mcp_starter.py` | All tests pass |

## Risks
- **Risk**: Importing `HealthChecker` into `startup_mcp_starter.py` could introduce an import cycle if the health checker (or its dependencies) imports the starter. → **Mitigation**: The health checker depends only on `shared.mcp_config` and `agent.secrets_masker`, neither of which imports the starter; verified by importing the module and running the existing test suite, which imports `startup_mcp_starter`.
- **Risk**: Over-broadening the non-200 handling could mask genuinely dead servers. → **Mitigation**: Restrict degraded-but-live to exactly what `is_degraded_but_live` returns (HTTP 503 + JSON `liveness: true`); all other non-200 statuses remain fatal.
- **Risk**: Changing `_verify_single_health` could alter `verify_health` retry behavior. → **Mitigation**: Scope is confined to the non-200 branch inside `_verify_single_health`; the retry loop, delays, and exception propagation in `verify_health` are untouched.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Align `_verify_single_health` with the degraded-but-live predicate | In Progress | — | — | Touches `scripts/agent/startup_mcp_starter.py` |
| 2 | Add branch coverage for non-200 + liveness decision | In Progress | — | — | Touches `tests/agent/test_startup_mcp_starter.py` |
| 3 | Deployment & Verification | Pending | — | — | Runs `pytest tests/agent/test_startup_mcp_starter.py` |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| — | — | — | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| implementations/20261030-071421_01_scripts_agent_startup_mcp_starter.py.md | 1 | Procedure | Pending | — | — |
| implementations/20261030-071421_02_tests_agent_test_startup_mcp_starter.py.md | 2 | Procedure | Pending | — | — |

## Traceability
- **Workflow phase**: issue-to-plan
- **Source issue**: issues/20261029-220520_mcphc001_degraded-but-live-retry.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: this document is the generated plan
- **Source implementation procedure**: N/A: not applicable in this phase
- **Generated at**: 20261030-000009
- **Related target files**: scripts/agent/startup_mcp_starter.py, tests/agent/test_startup_mcp_starter.py

### Requirement Traceability
| Requirement ID | Source Issue section or evidence | Target file | Implementation step | Acceptance criterion | Test or validation item | Status |
|---|---|---|---|---|---|---|
| REQ-001 | Implementation Intent / Required Changes; `_verify_single_health` ignores `liveness` (Step 2) | `scripts/agent/startup_mcp_starter.py` | Step 1 | AC1 | 503+liveness:true tolerated (Step 2) | Confirmed by repository evidence |
| REQ-002 | Testing Expectations | `tests/agent/test_startup_mcp_starter.py` | Step 2 | AC2, AC4 | New branch tests (Step 2) | Explicit in issue |
| REQ-003 | Constraints / Acceptance Criteria; current `RuntimeError` on non-200 (Step 2) | `scripts/agent/startup_mcp_starter.py` | Step 1 | AC2, AC3 | 503+liveness:false and 401 raise (Step 2) | Confirmed by repository evidence |

<!-- tools/generate_workitem.py implementation-procedure-pass timestamp: 20261030-071421 -->